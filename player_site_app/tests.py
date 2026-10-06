from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from dm_site_app.models import OverAllSettings
from .models import Player, Char_info


class PlayerAuthAndCharacterTests(TestCase):
    def setUp(self):
        # Nastavení OverAllSettings pro testy
        self.settings, _ = OverAllSettings.objects.get_or_create(
            id=1,
            defaults={'loging_active': True, 'editing_active': True}
        )
        self.settings.loging_active = True
        self.settings.save()

        # Vytvoření testovacího uživatele a hráče 1
        self.user1 = User.objects.create_user(username='hrac1', password='tajneheslo123')
        self.player1 = Player.objects.create(user=self.user1, nickname='Geralt', temna_esence=50, pin_code='1234')

        # Vytvoření testovacího uživatele a hráče 2
        self.user2 = User.objects.create_user(username='hrac2', password='tajneheslo123')
        self.player2 = Player.objects.create(user=self.user2, nickname='Dandelion', pin_code='5678')

    def test_login_index_renders(self):
        """Nepřihlášený uživatel vidí přihlášení s polem pro PIN, nevidí registraci ani hráčské menu."""
        response = self.client.get(reverse('player_site_app:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'player_site_app/login_index.html')
        self.assertContains(response, 'Vstup do hry')
        self.assertContains(response, 'Zadejte PIN')
        self.assertNotContains(response, 'Registrace nového dobrodruha')
        # Pro nepřihlášeného se menu nezobrazuje
        self.assertNotContains(response, 'id="playerNavContainer"')

    def test_registration_not_available(self):
        """Registrace byla z úvodní stránky odebrána."""
        post_data = {
            'action': 'register',
            'username': 'novy_hrac',
            'nickname': 'Legolas',
        }
        response = self.client.post(reverse('player_site_app:index'), post_data)
        self.assertFalse(User.objects.filter(username='novy_hrac').exists())

    def test_user_login_with_pin(self):
        """Platné přihlášení pomocí PIN kódu přesměruje na přehled postav."""
        post_data = {
            'pin': '1234',
        }
        response = self.client.post(reverse('player_site_app:index'), post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('player_site_app:prehled_postav'))
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user1.id)

    def test_login_when_loging_inactive(self):
        """Pokud je loging_active=False, zobrazí se pouze nápis 'Vítejte' a formulář je skrytý."""
        self.settings.loging_active = False
        self.settings.save()

        response = self.client.get(reverse('player_site_app:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Vítejte')
        self.assertNotContains(response, 'Zadejte PIN')

        # Pokus o POST při vypnutém přihlašování je zablokován
        post_res = self.client.post(reverse('player_site_app:index'), {'pin': '1234'})
        self.assertEqual(post_res.status_code, 200)
        self.assertContains(post_res, 'Přihlašování je v tuto chvíli pozastaveno')

    def test_pin_login_max_attempts_lockout(self):
        """Po 3 neúspěšných pokusech je přístup zablokován."""
        # Pokus 1
        res1 = self.client.post(reverse('player_site_app:index'), {'pin': '9999'})
        self.assertEqual(res1.status_code, 200)
        self.assertContains(res1, 'Zbývající pokusy: 2')

        # Pokus 2
        res2 = self.client.post(reverse('player_site_app:index'), {'pin': '9999'})
        self.assertEqual(res2.status_code, 200)
        self.assertContains(res2, 'Zbývající pokusy: 1')

        # Pokus 3
        res3 = self.client.post(reverse('player_site_app:index'), {'pin': '9999'})
        self.assertEqual(res3.status_code, 200)
        self.assertContains(res3, 'Vyčerpali jste všechny 3 pokusy')
        self.assertContains(res3, 'Přístup zablokován')

        # 4. pokus (i se správným PINem) je zablokován
        res4 = self.client.post(reverse('player_site_app:index'), {'pin': '1234'})
        self.assertEqual(res4.status_code, 200)
        self.assertContains(res4, 'Byl vyčerpán maximální počet pokusů')

    def test_long_pin_up_to_100_digits(self):
        """PIN může mít až 100 číslic."""
        long_pin = '9' * 100
        self.player1.pin_code = long_pin
        self.player1.save()

        res = self.client.post(reverse('player_site_app:index'), {'pin': long_pin})
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, reverse('player_site_app:prehled_postav'))

    def test_unauthenticated_redirect_all_pages(self):
        """Všech 10 stránek hráče vyžaduje přihlášení a přesměruje nepřihlášeného na login."""
        urls_to_test = [
            reverse('player_site_app:char_overview_active'),
            reverse('player_site_app:inv'),
            reverse('player_site_app:char_schopnosti'),
            reverse('player_site_app:char_roleplay'),
            reverse('player_site_app:char_achivements'),
            reverse('player_site_app:char_stats_detail'),
            reverse('player_site_app:kronika'),
            reverse('player_site_app:prehled_postav'),
            reverse('player_site_app:stream'),
            reverse('player_site_app:dungeon_shop'),
        ]
        for url in urls_to_test:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith(reverse('player_site_app:index')))

    def test_authenticated_user_redirect_from_login(self):
        """Přihlášený uživatel je z login stránky automaticky přesměrován na přehled postav."""
        self.client.login(username='hrac1', password='tajneheslo123')
        response = self.client.get(reverse('player_site_app:index'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('player_site_app:prehled_postav'))

    def test_prehled_postav_empty(self):
        """Pokud hráč nemá žádné postavy, zobrazí se text 'žádná postava'."""
        self.client.login(username='hrac1', password='tajneheslo123')
        response = self.client.get(reverse('player_site_app:prehled_postav'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'player_site_app/prehled_postav.html')
        self.assertContains(response, 'žádnou postavu')

    def test_prehled_postav_with_characters(self):
        """Vytvořená postava se zobrazí jako klikatelný odkaz vedoucí na char_overview."""
        char = Char_info.objects.create(
            player=self.player1,
            name='Ciri z Cintry',
            character_class='Bojovník',
            level=5,
            hit_points_max=44,
            hit_points_current=44,
            armor_class=16,
            strength=14,
            dexterity=18,
            constitution=14,
            intelligence=12,
            wisdom=13,
            charisma=16,
            gold=15,
            silver=5,
        )
        self.client.login(username='hrac1', password='tajneheslo123')
        response = self.client.get(reverse('player_site_app:prehled_postav'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'žádná postava')
        self.assertContains(response, 'Ciri z Cintry')

        detail_url = reverse('player_site_app:char_overview', kwargs={'char_id': char.id})
        self.assertContains(response, detail_url)

    def test_char_overview_detail(self):
        """Na stránce postavy se zobrazí všechny detailní informace."""
        char = Char_info.objects.create(
            player=self.player1,
            name='Yennefer',
            character_class='Kouzelník',
            level=10,
            race='Půlelf',
            background='Učenec',
            alignment='Neutrální',
            hit_points_max=52,
            hit_points_current=48,
            armor_class=13,
            speed=30,
            strength=8,
            dexterity=14,
            constitution=14,
            intelligence=20,
            wisdom=15,
            charisma=16,
            gold=100,
            silver=2,
        )
        self.client.login(username='hrac1', password='tajneheslo123')
        response = self.client.get(reverse('player_site_app:char_overview', kwargs={'char_id': char.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'player_site_app/char_over_view..html')
        self.assertContains(response, 'Yennefer')
        self.assertContains(response, 'Kouzelník (Úroveň 10)')
        self.assertContains(response, 'Půlelf')
        self.assertContains(response, '48 / 52')

    def test_isolation_between_players(self):
        """Hráč 2 nemůže vidět postavu hráče 1 ani v přehledu, ani v detailu."""
        char1 = Char_info.objects.create(
            player=self.player1,
            name='Ciri z Cintry',
            level=5,
        )

        # Přihlásíme se jako hráč 2
        self.client.login(username='hrac2', password='tajneheslo123')

        # V přehledu postav hráče 2 nesmí být postava hráče 1
        response = self.client.get(reverse('player_site_app:prehled_postav'))
        self.assertNotContains(response, 'Ciri z Cintry')
        self.assertContains(response, 'žádnou postavu')

        # Pokus o přímé zobrazení detailu postavy cizího hráče vrátí 404
        response_detail = self.client.get(reverse('player_site_app:char_overview', kwargs={'char_id': char1.id}))
        self.assertEqual(response_detail.status_code, 404)

    def test_dropdown_menu_order_and_elements(self):
        """Rozbalovací nabídka v levém horním rohu obsahuje všech 10 položek v přesném pořadí s oddělovačem a odhlášením."""
        self.client.login(username='hrac1', password='tajneheslo123')
        response = self.client.get(reverse('player_site_app:prehled_postav'))
        self.assertEqual(response.status_code, 200)

        # Nabídka je přítomna v levém horním rohu
        self.assertContains(response, 'id="playerNavContainer"')
        self.assertContains(response, 'id="playerNavToggleBtn"')
        self.assertContains(response, 'id="playerNavDropdown"')

        content = response.content.decode('utf-8')

        # Kontrola přesného pořadí v HTML:
        # 1. char_over_view
        idx1 = content.find(reverse('player_site_app:char_overview_active'))
        # 2. inv
        idx2 = content.find(reverse('player_site_app:inv'))
        # 3. char_schopnosti
        idx3 = content.find(reverse('player_site_app:char_schopnosti'))
        # 4. char_roleplay
        idx4 = content.find(reverse('player_site_app:char_roleplay'))
        # 5. char_achivements
        idx5 = content.find(reverse('player_site_app:char_achivements'))
        # 6. char_stats_detail
        idx6 = content.find(reverse('player_site_app:char_stats_detail'))
        # 7. kronika
        idx7 = content.find(reverse('player_site_app:kronika'))
        # 8. prehled_postav
        idx8 = content.find(reverse('player_site_app:prehled_postav'))
        # 9. stream
        idx9 = content.find(reverse('player_site_app:stream'))
        # 10. dungeon_shop (oddělený čárou hr)
        idx10 = content.find(reverse('player_site_app:dungeon_shop'))
        # 11. logout (pod dungeon shopem)
        idx_logout = content.find(reverse('player_site_app:logout'))

        self.assertTrue(idx1 != -1 and idx2 != -1 and idx3 != -1 and idx4 != -1)
        self.assertTrue(idx5 != -1 and idx6 != -1 and idx7 != -1 and idx8 != -1)
        self.assertTrue(idx9 != -1 and idx10 != -1 and idx_logout != -1)

        # Ověření přesného pořadí:
        self.assertTrue(idx1 < idx2 < idx3 < idx4 < idx5 < idx6 < idx7 < idx8 < idx9 < idx10 < idx_logout)

        # Ověření oddělovače (hr) před Dungeon Shopem
        hr_idx = content.find('<hr class="player-nav-divider">')
        self.assertTrue(hr_idx != -1)
        self.assertTrue(idx9 < hr_idx < idx10)

    def test_dm_site_does_not_contain_player_nav(self):
        """Aplikace dm_site_app nesmí obsahovat hráčské menu."""
        self.user1.is_staff = True
        self.user1.save()
        self.client.force_login(self.user1)
        response = self.client.get(reverse('dm_site_app:index'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'id="playerNavContainer"')
        self.assertNotContains(response, 'id="playerNavToggleBtn"')

    def test_notes_crud_and_favorite(self):
        """Hráč může přidat poznámku, označit ji jako oblíbenou a smazat ji."""
        char = Char_info.objects.create(player=self.player1, name='Geralt z Rivie', level=3)
        self.client.login(username='hrac1', password='tajneheslo123')

        # 1. Přidání poznámky
        add_res = self.client.post(reverse('player_site_app:add_char_note'), {
            'char_id': char.id,
            'title': 'Tajná mapa',
            'note': 'Mapa se nachází pod kamenným oltářem.',
        })
        self.assertEqual(add_res.status_code, 302)
        note = char.char_notes.first()
        self.assertIsNotNone(note)
        self.assertEqual(note.title, 'Tajná mapa')
        self.assertFalse(note.is_favorite)

        # 2. Zobrazení v char_overview
        view_res = self.client.get(reverse('player_site_app:char_overview', kwargs={'char_id': char.id}))
        self.assertEqual(view_res.status_code, 200)
        self.assertContains(view_res, 'Tajná mapa')
        self.assertContains(view_res, 'Mapa se nachází pod kamenným oltářem.')

        # 3. Přepnutí na oblíbené
        fav_res = self.client.post(reverse('player_site_app:toggle_favorite_note', kwargs={'note_id': note.id}))
        self.assertEqual(fav_res.status_code, 302)
        note.refresh_from_db()
        self.assertTrue(note.is_favorite)

        # 4. Smazání poznámky
        del_res = self.client.post(reverse('player_site_app:delete_char_note', kwargs={'note_id': note.id}))
        self.assertEqual(del_res.status_code, 302)
        self.assertEqual(char.char_notes.count(), 0)

    def test_backstory_crud_and_public_toggle(self):
        """Hráč může přidat backstory, přepínat veřejné/soukromé a smazat zápis."""
        char = Char_info.objects.create(player=self.player1, name='Geralt z Rivie', level=3)
        self.client.login(username='hrac1', password='tajneheslo123')

        # 1. Přidání soukromého zápisu
        add_res = self.client.post(reverse('player_site_app:add_char_backstory'), {
            'char_id': char.id,
            'title': 'Dětství v Kaer Morhen',
            'backstory': 'Těžký výcvik a mutace zaklínačů.',
        })
        self.assertEqual(add_res.status_code, 302)
        story = char.char_backstories.first()
        self.assertIsNotNone(story)
        self.assertFalse(story.public)

        # 2. Zobrazení v char_roleplay
        rp_res = self.client.get(reverse('player_site_app:char_roleplay_detail', kwargs={'char_id': char.id}))
        self.assertEqual(rp_res.status_code, 200)
        self.assertContains(rp_res, 'Dětství v Kaer Morhen')

        # 3. Zveřejnění zápisu
        pub_res = self.client.post(reverse('player_site_app:toggle_public_backstory', kwargs={'backstory_id': story.id}))
        self.assertEqual(pub_res.status_code, 302)
        story.refresh_from_db()
        self.assertTrue(story.public)

        # 4. Smazání
        del_res = self.client.post(reverse('player_site_app:delete_char_backstory', kwargs={'backstory_id': story.id}))
        self.assertEqual(del_res.status_code, 302)
        self.assertEqual(char.char_backstories.count(), 0)

    def test_all_chars_and_detail_view_isolation(self):
        """Hráč 2 může nahlížet na postavu hráče 1, vidí pouze VEŘEJNOU backstory, nevidí poznámky ani finance."""
        from .models import CharNotes, CharBackstory

        char1 = Char_info.objects.create(
            player=self.player1,
            name='Geralt z Rivie',
            character_class='Zaklínač',
            level=5,
            race='Člověk',
            gold=999,
            silver=50
        )
        # Veřejná kapitola
        CharBackstory.objects.create(
            player=self.player1,
            character=char1,
            title='Veřejná kapitola',
            backstory='Toto smí vidět celá družina.',
            public=True
        )
        # Soukromá kapitola
        CharBackstory.objects.create(
            player=self.player1,
            character=char1,
            title='Tajná kapitola',
            backstory='Toto je přísně tajné.',
            public=False
        )
        # Soukromá poznámka
        CharNotes.objects.create(
            player=self.player1,
            character=char1,
            title='Moje tajná poznámka',
            note='Tajné heslo do truhly.'
        )

        # Přihlášení jako hráč 2
        self.client.login(username='hrac2', password='tajneheslo123')

        # 1. Seznam all_chars
        roster_res = self.client.get(reverse('player_site_app:all_chars'))
        self.assertEqual(roster_res.status_code, 200)
        self.assertContains(roster_res, 'Geralt z Rivie')

        # 2. Detail postavy cizího hráče
        detail_res = self.client.get(reverse('player_site_app:all_chars_detail', kwargs={'char_id': char1.id}))
        self.assertEqual(detail_res.status_code, 200)
        self.assertContains(detail_res, 'Geralt z Rivie')
        self.assertContains(detail_res, 'Veřejná kapitola')
        self.assertContains(detail_res, 'Toto smí vidět celá družina.')

        # Striktní bezpečnost: nesmí obsahovat tajnou kapitolu, poznámky ani peníze
        self.assertNotContains(detail_res, 'Tajná kapitola')
        self.assertNotContains(detail_res, 'Toto je přísně tajné.')
        self.assertNotContains(detail_res, 'Moje tajná poznámka')
        self.assertNotContains(detail_res, 'Tajné heslo do truhly.')
        self.assertNotContains(detail_res, '999 zl')

    def test_kronika_view_filter_revealed(self):
        """Kronika zobrazuje pouze odkryté záznamy rozdělené na info a lore."""
        from dm_site_app.models import Kronika

        Kronika.objects.create(nazev='Pravidla cechu', category='info', popis='Nová pravidla cechu.', odkryto_hracum=True)
        Kronika.objects.create(nazev='Bitva o most', category='lore', popis='Epická bitva u řeky.', odkryto_hracum=True)
        Kronika.objects.create(nazev='Tajné spiknutí', category='lore', popis='Zatím skrytý děj.', odkryto_hracum=False)

        self.client.login(username='hrac1', password='tajneheslo123')
        res = self.client.get(reverse('player_site_app:kronika'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Pravidla cechu')
        self.assertContains(res, 'Bitva o most')
        self.assertNotContains(res, 'Tajné spiknutí')

