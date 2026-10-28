from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from dm_site_app.models import OverAllSettings, Items_Active
from .models import Player, Char_info, Esence_Items_Shop, Esence_Items_Owners, Logs, Achivements_database, Achivements_players


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

        res = self.client.post(reverse('player_site_app:index'), {
            'player_id': self.player1.id,
            'pin': long_pin
        })
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, reverse('player_site_app:prehled_postav'))

    def test_login_with_profile_dropdown_and_non_unique_pin(self):
        """Dva hráči mohou mít shodný PIN a úspěšně se přihlásit výběrem svého profilu."""
        # 1. Nastavíme oběma hráčům stejný PIN (ověření, že PIN již není unikátní v databázi)
        self.player1.pin_code = '7777'
        self.player1.save()
        self.player2.pin_code = '7777'
        self.player2.save()

        # Ověření, že login stránka obsahuje rozbalovací nabídku s oběma profily a žádné heslo
        get_res = self.client.get(reverse('player_site_app:index'))
        self.assertEqual(get_res.status_code, 200)
        self.assertContains(get_res, 'id="playerSelect"')
        self.assertContains(get_res, self.player1.nickname)
        self.assertContains(get_res, self.player2.nickname)
        self.assertNotContains(get_res, 'name="password"')

        # 2. Přihlášení Hráče 1 se sdíleným PINem '7777'
        res1 = self.client.post(reverse('player_site_app:index'), {
            'player_id': self.player1.id,
            'pin': '7777'
        })
        self.assertEqual(res1.status_code, 302)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user1.id)

        # Odhlášení
        self.client.logout()

        # 3. Přihlášení Hráče 2 se stejným PINem '7777'
        res2 = self.client.post(reverse('player_site_app:index'), {
            'player_id': self.player2.id,
            'pin': '7777'
        })
        self.assertEqual(res2.status_code, 302)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user2.id)

        # 4. Neúspěšný pokus: Vybrán Hráč 1, ale zadán chybný PIN
        self.client.logout()
        res_fail = self.client.post(reverse('player_site_app:index'), {
            'player_id': self.player1.id,
            'pin': '0000'
        })
        self.assertEqual(res_fail.status_code, 200)
        self.assertContains(res_fail, 'Nesprávný PIN kód pro hráče')

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
        # 9. stream (volitelné pokud bylo odebráno z menu)
        idx9 = content.find(reverse('player_site_app:stream'))
        # 10. dungeon_shop (oddělený čárou hr)
        idx10 = content.find(reverse('player_site_app:dungeon_shop'))
        # 11. logout (pod dungeon shopem)
        idx_logout = content.find(reverse('player_site_app:logout'))

        self.assertTrue(idx1 != -1 and idx2 != -1 and idx3 != -1 and idx4 != -1)
        self.assertTrue(idx5 != -1 and idx6 != -1 and idx7 != -1 and idx8 != -1)
        self.assertTrue(idx10 != -1 and idx_logout != -1)

        # Ověření přesného pořadí:
        hr_idx = content.find('<hr class="player-nav-divider">')
        self.assertTrue(hr_idx != -1)
        if idx9 != -1:
            self.assertTrue(idx1 < idx2 < idx3 < idx4 < idx5 < idx6 < idx7 < idx8 < idx9 < idx10 < idx_logout)
            self.assertTrue(idx9 < hr_idx < idx10)
        else:
            self.assertTrue(idx1 < idx2 < idx3 < idx4 < idx5 < idx6 < idx7 < idx8 < idx10 < idx_logout)
            self.assertTrue(idx8 < hr_idx < idx10)

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

    def test_kronika_detail_view(self):
        """Detail zápisu v kronice zobrazí celý text a tlačítko zpět, skryté zápisy vrátí 404."""
        from dm_site_app.models import Kronika

        entry_revealed = Kronika.objects.create(
            nazev='Dlouhý zápis z bitvy',
            category='lore',
            popis='Zde je velmi dlouhý popis celého sezení, které družina absolvovala.',
            odkryto_hracum=True
        )
        entry_hidden = Kronika.objects.create(
            nazev='Přísně tajný lore',
            category='lore',
            popis='DM příprava pro další sezení.',
            odkryto_hracum=False
        )

        self.client.login(username='hrac1', password='tajneheslo123')

        # 1. Odkrytý záznam se zobrazí se všemi detaily a tlačítkem zpět
        res = self.client.get(reverse('player_site_app:kronika_detail', kwargs={'entry_id': entry_revealed.id}))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'player_site_app/kronika_detail.html')
        self.assertContains(res, 'Dlouhý zápis z bitvy')
        self.assertContains(res, 'Zde je velmi dlouhý popis celého sezení, které družina absolvovala.')
        self.assertContains(res, reverse('player_site_app:kronika'))

        # 2. Skrytý záznam vrátí 404
        res_hidden = self.client.get(reverse('player_site_app:kronika_detail', kwargs={'entry_id': entry_hidden.id}))
        self.assertEqual(res_hidden.status_code, 404)

    def test_char_schopnosti_view_filtering_and_tiers(self):
        """Kniha kouzel filtruje podle povolání, řadí podle úrovně a správně určuje stav dostupné/zamčené."""
        from dm_site_app.models import Spells_All_db, Spells_Active

        # Vytvoření postavy: Kouzelník na 3. úrovni (může triky, 1. úroveň a 2. úroveň)
        char = Char_info.objects.create(
            player=self.player1,
            name='Geralt Magus',
            character_class='Kouzelník',
            level=3,
            race='Člověk'
        )

        cantrip = Spells_All_db.objects.create(
            api_index='fire-bolt',
            name_cz='Ohnivá střela',
            name_en='Fire Bolt',
            level=0,
            is_cantrip=True,
            school='Evokace',
            classes='Kouzelník, Čaroděj'
        )
        spell_lvl1 = Spells_All_db.objects.create(
            api_index='magic-missile',
            name_cz='Magická střela',
            name_en='Magic Missile',
            level=1,
            is_cantrip=False,
            school='Evokace',
            classes='Kouzelník, Čaroděj'
        )
        spell_lvl5 = Spells_All_db.objects.create(
            api_index='cone-of-cold',
            name_cz='Kužel mrazu',
            name_en='Cone of Cold',
            level=5,
            is_cantrip=False,
            school='Evokace',
            classes='Kouzelník'
        )

        self.client.login(username='hrac1', password='tajneheslo123')
        res = self.client.get(reverse('player_site_app:char_schopnosti_detail', kwargs={'char_id': char.id}))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'player_site_app/char_schopnosti.html')

        # V kontextu musí být správně vypočtena max. dosažitelná úroveň (pro kouzelníka L3 je to 2. úroveň)
        self.assertEqual(res.context['max_spell_level'], 2)

        # Karty v HTML
        self.assertContains(res, 'Ohnivá střela')
        self.assertContains(res, 'Magická střela')
        self.assertContains(res, 'Kužel mrazu')

    def test_toggle_learn_and_equip_spell(self):
        """Hráč se může naučit kouzlo, následně ho vybavit a odebrat z výbavy."""
        from dm_site_app.models import Spells_All_db, Spells_Active

        char = Char_info.objects.create(
            player=self.player1,
            name='Yennefer z Vengerbergu',
            character_class='Kouzelník',
            level=5
        )
        spell = Spells_All_db.objects.create(
            api_index='fireball',
            name_cz='Ohnivá koule',
            name_en='Fireball',
            level=3,
            is_cantrip=False,
            school='Evokace',
            classes='Kouzelník, Čaroděj'
        )

        self.client.login(username='hrac1', password='tajneheslo123')

        # 1. Naučit se kouzlo (AJAX POST)
        res_learn = self.client.post(reverse('player_site_app:toggle_learn_spell'), {
            'char_id': char.id,
            'spell_id': spell.id,
            'action': 'learn',
            'ajax': '1'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(res_learn.status_code, 200)
        data = res_learn.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['nauceno'])
        self.assertFalse(data['vybaveno'])

        active_spell = Spells_Active.objects.get(char_own=char, template_spell=spell)
        self.assertTrue(active_spell.nauceno)
        self.assertFalse(active_spell.vybaveno)

        # 2. Vybavit kouzlo
        res_equip = self.client.post(reverse('player_site_app:toggle_equip_spell'), {
            'char_id': char.id,
            'spell_id': spell.id,
            'ajax': '1'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(res_equip.status_code, 200)
        data_equip = res_equip.json()
        self.assertTrue(data_equip['success'])
        self.assertTrue(data_equip['vybaveno'])

        active_spell.refresh_from_db()
        self.assertTrue(active_spell.vybaveno)

        # 3. Odebrat z výbavy
        res_unequip = self.client.post(reverse('player_site_app:toggle_equip_spell'), {
            'char_id': char.id,
            'spell_id': spell.id,
            'ajax': '1'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(res_unequip.status_code, 200)
        active_spell.refresh_from_db()
        self.assertFalse(active_spell.vybaveno)

    def test_spell_isolation_between_players(self):
        """Hráč 2 nemůže manipulovat s kouzly postavy hráče 1."""
        from dm_site_app.models import Spells_All_db

        char1 = Char_info.objects.create(player=self.player1, name='Geralt', level=1)
        spell = Spells_All_db.objects.create(
            api_index='shield',
            name_cz='Štít',
            name_en='Shield',
            level=1
        )

        self.client.login(username='hrac2', password='tajneheslo123')
        res = self.client.post(reverse('player_site_app:toggle_learn_spell'), {
            'char_id': char1.id,
            'spell_id': spell.id,
        })
        self.assertEqual(res.status_code, 404)


class PlayerReforgeAndEquipTests(TestCase):
    def setUp(self):
        self.settings, _ = OverAllSettings.objects.get_or_create(
            id=1,
            defaults={'loging_active': True, 'editing_active': True}
        )
        self.user = User.objects.create_user(username='tester', password='heslo123')
        self.player = Player.objects.create(user=self.user, nickname='Tester', temna_esence=10, pin_code='4321')

        self.border_basic = Esence_Items_Shop.objects.create(
            name='Dřevěný rámeček',
            category='borders',
            rarity='basic',
            cost=10
        )
        self.border_rare = Esence_Items_Shop.objects.create(
            name='Stříbrný rámeček',
            category='borders',
            rarity='rare',
            cost=25
        )
        self.border_epic = Esence_Items_Shop.objects.create(
            name='Zlatý rámeček',
            category='borders',
            rarity='epic',
            cost=50
        )
        self.border_legendary = Esence_Items_Shop.objects.create(
            name='Dračí rámeček',
            category='borders',
            rarity='legendary',
            cost=100
        )
        self.chest = Esence_Items_Shop.objects.create(
            name='Tajemná truhla',
            category='treasures',
            rarity='basic',
            cost=10
        )

    def test_reforge_basic_item_success(self):
        """Hráč může rozebrat basic předmět a získá 5 temné esence."""
        owner_record = Esence_Items_Owners.objects.create(player=self.player, item=self.border_basic)
        self.client.login(username='tester', password='heslo123')

        res = self.client.post(reverse('player_site_app:reforge_tresure'), {
            'item_id': self.border_basic.id,
            'player_id': self.player.id,
            'ajax': '1',
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['value'], 5)
        self.assertEqual(data['new_essence'], 15)

        self.player.refresh_from_db()
        self.assertEqual(self.player.temna_esence, 15)
        self.assertFalse(Esence_Items_Owners.objects.filter(id=owner_record.id).exists())
        self.assertTrue(Esence_Items_Shop.objects.filter(id=self.border_basic.id).exists())

    def test_reforge_rarities_essence_values(self):
        """Ověření hodnot esence pro vzácnou, epickou a legendární raritu (25, 50, 100)."""
        Esence_Items_Owners.objects.create(player=self.player, item=self.border_rare)
        Esence_Items_Owners.objects.create(player=self.player, item=self.border_epic)
        Esence_Items_Owners.objects.create(player=self.player, item=self.border_legendary)
        self.client.login(username='tester', password='heslo123')

        # Rare -> +25 (10 + 25 = 35)
        self.client.post(reverse('player_site_app:reforge_tresure'), {'item_id': self.border_rare.id})
        self.player.refresh_from_db()
        self.assertEqual(self.player.temna_esence, 35)

        # Epic -> +50 (35 + 50 = 85)
        self.client.post(reverse('player_site_app:reforge_tresure'), {'item_id': self.border_epic.id})
        self.player.refresh_from_db()
        self.assertEqual(self.player.temna_esence, 85)

        # Legendary -> +100 (85 + 100 = 185)
        self.client.post(reverse('player_site_app:reforge_tresure'), {'item_id': self.border_legendary.id})
        self.player.refresh_from_db()
        self.assertEqual(self.player.temna_esence, 185)

    def test_cannot_reforge_treasure_chest(self):
        """Truhlu nelze rozebírat, pouze otevřít."""
        Esence_Items_Owners.objects.create(player=self.player, item=self.chest)
        self.client.login(username='tester', password='heslo123')

        res = self.client.post(reverse('player_site_app:reforge_tresure'), {
            'item_id': self.chest.id,
            'ajax': '1',
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(res.status_code, 400)
        data = res.json()
        self.assertFalse(data['success'])
        self.assertIn('Truhly nelze rozebírat', data['error'])

    def test_reforge_active_frame_clears_or_repoints(self):
        """Pokud hráč rozebere aktivní rámeček, active_ramecek se správně aktualizuje."""
        rec1 = Esence_Items_Owners.objects.create(player=self.player, item=self.border_basic)
        rec2 = Esence_Items_Owners.objects.create(player=self.player, item=self.border_basic)

        self.player.active_ramecek = rec1
        self.player.save()

        self.client.login(username='tester', password='heslo123')

        # 1. Rozebere 1. kus: active_ramecek se přepojí na 2. kus stejného rámečku
        self.client.post(reverse('player_site_app:reforge_tresure'), {'item_id': self.border_basic.id})
        self.player.refresh_from_db()
        self.assertEqual(self.player.active_ramecek, rec2)

        # 2. Rozebere 2. kus: active_ramecek se nastaví na None
        self.client.post(reverse('player_site_app:reforge_tresure'), {'item_id': self.border_basic.id})
        self.player.refresh_from_db()
        self.assertIsNone(self.player.active_ramecek)

    def test_equip_and_unequip_frame(self):
        """Hráč může nasadit vlastněný rámeček a následně jej sundat."""
        owner_record = Esence_Items_Owners.objects.create(player=self.player, item=self.border_rare)
        self.client.login(username='tester', password='heslo123')

        # 1. Nasadit
        res_equip = self.client.post(reverse('player_site_app:equip_frame'), {
            'item_id': self.border_rare.id,
            'action': 'equip',
            'ajax': '1',
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(res_equip.status_code, 200)
        self.player.refresh_from_db()
        self.assertEqual(self.player.active_ramecek, owner_record)

        # 2. Sundat
        res_unequip = self.client.post(reverse('player_site_app:equip_frame'), {
            'action': 'unequip',
            'ajax': '1',
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(res_unequip.status_code, 200)
        self.player.refresh_from_db()
        self.assertIsNone(self.player.active_ramecek)

    def test_cannot_equip_non_border_item(self):
        """Nelze nasadit předmět, který není rámeček (např. truhlu)."""
        Esence_Items_Owners.objects.create(player=self.player, item=self.chest)
        self.client.login(username='tester', password='heslo123')

        res = self.client.post(reverse('player_site_app:equip_frame'), {
            'item_id': self.chest.id,
            'action': 'equip',
            'ajax': '1',
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(res.status_code, 400)

    def test_dnd5e_spellcasting_rules_helpers(self):
        """Ověření výpočtu úrovní kouzel a přístupu k trikům podle D&D 5e pravidel."""
        from player_site_app.views import get_max_spell_level_for_character, can_character_cast_cantrips

        # Čaroděj (Plnohodnotný sesilatel)
        sorcerer_lvl1 = Char_info(character_class='Čaroděj', level=1)
        self.assertTrue(can_character_cast_cantrips(sorcerer_lvl1))
        self.assertEqual(get_max_spell_level_for_character(sorcerer_lvl1), 1)

        # Paladin (Polo-sesilatel: na 1. úrovni nemá kouzla ani triky)
        paladin_lvl1 = Char_info(character_class='Paladin', level=1)
        self.assertFalse(can_character_cast_cantrips(paladin_lvl1))
        self.assertEqual(get_max_spell_level_for_character(paladin_lvl1), 0)

        # Paladin na 2. úrovni získává 1. úroveň kouzel, ale triky v 5e nemá
        paladin_lvl2 = Char_info(character_class='Paladin', level=2)
        self.assertFalse(can_character_cast_cantrips(paladin_lvl2))
        self.assertEqual(get_max_spell_level_for_character(paladin_lvl2), 1)

        # Barbar (Nemagická třída)
        barbarian = Char_info(character_class='Barbar', level=5)
        self.assertFalse(can_character_cast_cantrips(barbarian))
        self.assertEqual(get_max_spell_level_for_character(barbarian), 0)

        # Bojovník (Třetinový sesilatel: do 2. úrovně 0, od 3. úrovně má triky a 1. level)
        fighter_lvl1 = Char_info(character_class='Bojovník', level=1)
        self.assertFalse(can_character_cast_cantrips(fighter_lvl1))
        self.assertEqual(get_max_spell_level_for_character(fighter_lvl1), 0)

        fighter_lvl3 = Char_info(character_class='Bojovník', level=3)
        self.assertTrue(can_character_cast_cantrips(fighter_lvl3))
        self.assertEqual(get_max_spell_level_for_character(fighter_lvl3), 1)

    def test_two_unified_spell_icons(self):
        """Triky a kouzla mají přesně 2 sjednocené RPG ikonky (cantrip_icon.svg a spell_icon.svg)."""
        from dm_site_app.models import Spells_All_db

        cantrip = Spells_All_db.objects.create(
            api_index='poison-spray-test',
            name_cz='Oblak jedu test',
            name_en='Poison Spray',
            level=0,
            is_cantrip=True
        )
        spell = Spells_All_db.objects.create(
            api_index='cloudkill-test',
            name_cz='Mrak smrti test',
            name_en='Cloudkill',
            level=5,
            is_cantrip=False
        )

        self.assertEqual(cantrip.display_icon_url, '/static/img/spells/cantrip_icon.svg')
        self.assertEqual(spell.display_icon_url, '/static/img/spells/spell_icon.svg')

    def test_non_caster_character_sees_no_spells_and_gets_notice(self):
        """Nemagické povolání (např. Barbar) nevidí cizí kouzla a zobrazí se mu informační box."""
        from dm_site_app.models import Spells_All_db

        Spells_All_db.objects.create(
            api_index='fireball-test2',
            name_cz='Ohnivá koule test',
            name_en='Fireball',
            level=3,
            classes='Kouzelník, Čaroděj'
        )

        barbarian_char = Char_info.objects.create(
            player=self.player,
            name='Conan',
            character_class='Barbar',
            level=1,
            race='Člověk'
        )

        self.client.login(username='tester', password='heslo123')
        res = self.client.get(reverse('player_site_app:char_schopnosti_detail', kwargs={'char_id': barbarian_char.id}))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['max_spell_level'], 0)
        self.assertFalse(res.context['has_spellcasting'])
        self.assertEqual(len(res.context['spell_items']), 0)
        self.assertContains(res, 'podle pravidel D&D 5e neovládá magická kouzla')

    def test_toggle_learn_spell_validation_dnd5e(self):
        """Systém odmítne naučení kouzla pro nepovolenou třídu nebo nepovolenou úroveň."""
        from dm_site_app.models import Spells_All_db

        sorcerer_char = Char_info.objects.create(
            player=self.player,
            name='Glem',
            character_class='Čaroděj',
            level=1,
            race='Tiefling'
        )
        cantrip = Spells_All_db.objects.create(
            api_index='poison-spray-val',
            name_cz='Oblak jedu',
            name_en='Poison Spray',
            level=0,
            is_cantrip=True,
            classes='Čaroděj, Černokněžník, Kouzelník'
        )
        high_level_spell = Spells_All_db.objects.create(
            api_index='cloudkill-val',
            name_cz='Mrak smrti',
            name_en='Cloudkill',
            level=5,
            is_cantrip=False,
            classes='Čaroděj, Kouzelník'
        )

        self.client.login(username='tester', password='heslo123')

        # 1. Čaroděj na 1. úrovni se MŮŽE naučit Oblak jedu (Poison Spray, Trik 0. úrovně)
        res_cantrip = self.client.post(reverse('player_site_app:toggle_learn_spell'), {
            'char_id': sorcerer_char.id,
            'spell_id': cantrip.id,
            'action': 'learn',
            'ajax': '1',
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(res_cantrip.status_code, 200)
        self.assertTrue(res_cantrip.json()['success'])

        # 2. Čaroděj na 1. úrovni se NEMŮŽE naučit Mrak smrti (Cloudkill, 5. úroveň) -> odmítnuto kódem 403
        res_locked = self.client.post(reverse('player_site_app:toggle_learn_spell'), {
            'char_id': sorcerer_char.id,
            'spell_id': high_level_spell.id,
            'action': 'learn',
            'ajax': '1',
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(res_locked.status_code, 403)
        self.assertFalse(res_locked.json()['success'])
        self.assertIn('maximálně 1. úrovně', res_locked.json()['error'])


class PlayerHiddenCharacterAndDmTests(TestCase):
    def setUp(self):
        self.settings, _ = OverAllSettings.objects.get_or_create(
            id=1,
            defaults={'loging_active': True, 'editing_active': True}
        )
        self.user1 = User.objects.create_user(username='hrac_bob', password='password123')
        self.player1 = Player.objects.create(user=self.user1, nickname='Bob')

        self.user2 = User.objects.create_user(username='hrac_alice', password='password123')
        self.player2 = Player.objects.create(user=self.user2, nickname='Alice')

        self.dm_user = User.objects.create_superuser(username='dm_dan', password='password123')
        self.dm_player = Player.objects.create(user=self.dm_user, nickname='DanDM', admin=True)

    def test_hidden_character_isolation_and_dm_visibility(self):
        """Běžní hráči nevidí skryté postavy v družině a nemají k nim přístup (404). DM je vidí a spravuje."""
        # Veřejná postava
        public_char = Char_info.objects.create(
            player=self.player1,
            name='Veřejný Hrdina',
            character_class='Bojovník',
            level=3,
            is_public=True
        )

        # Skrytá postava (pouze pro DM)
        secret_char = Char_info.objects.create(
            player=self.dm_player,
            name='Tajemný Inkvizitor',
            character_class='Paladin',
            level=10,
            is_public=False
        )

        # 1. Běžný hráč (Alice)
        self.client.login(username='hrac_alice', password='password123')

        # V all_chars vidí veřejnou, NEVIDÍ skrytou
        roster_res = self.client.get(reverse('player_site_app:all_chars'))
        self.assertEqual(roster_res.status_code, 200)
        self.assertContains(roster_res, 'Veřejný Hrdina')
        self.assertNotContains(roster_res, 'Tajemný Inkvizitor')

        # V all_chars_detail na skrytou postavu dostane 404
        secret_detail_res = self.client.get(reverse('player_site_app:all_chars_detail', kwargs={'char_id': secret_char.id}))
        self.assertEqual(secret_detail_res.status_code, 404)

        # Běžný hráč se nemůže pokusit přepnout viditelnost (403)
        toggle_forbidden = self.client.post(reverse('player_site_app:toggle_char_visibility'), {
            'char_id': secret_char.id,
            'ajax': '1',
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(toggle_forbidden.status_code, 403)

        # 2. Dungeon Master (DanDM)
        self.client.login(username='dm_dan', password='password123')

        # DM v all_chars VIDÍ skrytou postavu i s označením
        dm_roster = self.client.get(reverse('player_site_app:all_chars'))
        self.assertEqual(dm_roster.status_code, 200)
        self.assertContains(dm_roster, 'Tajemný Inkvizitor')
        self.assertContains(dm_roster, 'Skrytá')

        # DM může otevřít detail v all_chars_detail
        dm_detail = self.client.get(reverse('player_site_app:all_chars_detail', kwargs={'char_id': secret_char.id}))
        self.assertEqual(dm_detail.status_code, 200)
        self.assertContains(dm_detail, 'Tajemný Inkvizitor')
        self.assertContains(dm_detail, 'Skrytá před hráči')

        # DM může otevřít deník postavy (char_overview)
        dm_overview = self.client.get(reverse('player_site_app:char_overview', kwargs={'char_id': secret_char.id}))
        self.assertEqual(dm_overview.status_code, 200)
        self.assertContains(dm_overview, 'Tajemný Inkvizitor')
        self.assertContains(dm_overview, 'id="dmSecretBanner"')

        # DM přepne viditelnost na veřejnou
        toggle_res = self.client.post(reverse('player_site_app:toggle_char_visibility'), {
            'char_id': secret_char.id,
            'ajax': '1',
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(toggle_res.status_code, 200)
        self.assertTrue(toggle_res.json()['success'])
        self.assertTrue(toggle_res.json()['is_public'])

        secret_char.refresh_from_db()
        self.assertTrue(secret_char.is_public)

        # Nyní běžný hráč (Alice) postavu již vidí
        self.client.login(username='hrac_alice', password='password123')
        roster_now = self.client.get(reverse('player_site_app:all_chars'))
        self.assertContains(roster_now, 'Tajemný Inkvizitor')

        detail_now = self.client.get(reverse('player_site_app:all_chars_detail', kwargs={'char_id': secret_char.id}))
        self.assertEqual(detail_now.status_code, 200)

    def test_create_character_by_dm(self):
        """DM může vytvořit novou postavu (výchozí stav: skrytá). Běžný hráč nemá oprávnění."""
        # 1. Běžný hráč se pokusí vytvořit postavu -> zamítnuto a přesměrováno
        self.client.login(username='hrac_bob', password='password123')
        res_forbidden = self.client.post(reverse('player_site_app:create_character'), {
            'name': 'Hackerova postava',
            'character_class': 'Tulák',
            'race': 'Elf',
            'level': 1,
        })
        self.assertRedirects(res_forbidden, reverse('player_site_app:prehled_postav'))
        self.assertFalse(Char_info.objects.filter(name='Hackerova postava').exists())

        # 2. DM vytvoří novou skrytou postavu
        self.client.login(username='dm_dan', password='password123')
        res_dm = self.client.post(reverse('player_site_app:create_character'), {
            'name': 'Temný Černokněžník',
            'character_class': 'Černokněžník',
            'race': 'Tiefling',
            'level': 5,
            'player_id': self.dm_player.id,
            # is_public není zaškrtnuto -> defaultně False (skrytá)
        })
        created_char = Char_info.objects.filter(name='Temný Černokněžník').first()
        self.assertIsNotNone(created_char)
        self.assertFalse(created_char.is_public)
        self.assertEqual(created_char.level, 5)
        self.assertEqual(created_char.character_class, 'Černokněžník')
        # Přesměrováno přímo do deníku postavy
        self.assertRedirects(res_dm, reverse('player_site_app:char_overview', kwargs={'char_id': created_char.id}))


class PlayerCharacterAvatarTests(TestCase):
    def setUp(self):
        OverAllSettings.objects.get_or_create(id=1, defaults={'loging_active': True, 'editing_active': True})
        self.user_player = User.objects.create_user(username='hrac_avatar', password='password123')
        self.player = Player.objects.create(user=self.user_player, nickname='Aragorn', pin_code='9876')

        self.user_other = User.objects.create_user(username='hrac_cizi', password='password123')
        self.player_other = Player.objects.create(user=self.user_other, nickname='Gimli', pin_code='5432')

        self.user_dm = User.objects.create_user(username='dm_avatar', password='password123', is_staff=True)
        self.player_dm = Player.objects.create(user=self.user_dm, nickname='Gandalf', pin_code='1111', admin=True)

        self.char_barbar = Char_info.objects.create(
            player=self.player,
            name='Conan',
            character_class='Barbar',
            race='Člověk',
            level=3
        )

        self.char_kouzelnik = Char_info.objects.create(
            player=self.player,
            name='Raistlin',
            character_class='Kouzelník',
            race='Člověk',
            level=5
        )

    def test_default_class_avatars_mapped_correctly(self):
        """Postava bez nahraného obrázku automaticky používá unikátní SVG obrázek svého povolání."""
        self.assertFalse(self.char_barbar.has_custom_image)
        self.assertEqual(self.char_barbar.default_class_image_url, '/static/img/classes/barbar.svg')
        self.assertEqual(self.char_barbar.profile_image_url, '/static/img/classes/barbar.svg')

        self.assertFalse(self.char_kouzelnik.has_custom_image)
        self.assertEqual(self.char_kouzelnik.default_class_image_url, '/static/img/classes/kouzelnik.svg')
        self.assertEqual(self.char_kouzelnik.profile_image_url, '/static/img/classes/kouzelnik.svg')

    def test_all_classes_have_unique_svgs(self):
        """Všech 13 tříd má platnou cestu na SVG."""
        classes = [
            'Barbar', 'Bard', 'Bojovník', 'Čaroděj', 'Černokněžník',
            'Druid', 'Hraničář', 'Klerik', 'Kouzelník', 'Mnich',
            'Paladin', 'Tulák', 'Ostatní'
        ]
        urls = set()
        for cls_name in classes:
            char = Char_info(player=self.player, name='Test', character_class=cls_name)
            url = char.default_class_image_url
            self.assertTrue(url.startswith('/static/img/classes/'))
            self.assertTrue(url.endswith('.svg'))
            urls.add(url)
        # Všech 13 unikátních svg souborů
        self.assertEqual(len(urls), 13)

    def test_class_change_updates_default_avatar(self):
        """Při změně povolání u postavy bez vlastního obrázku se výchozí obrázek automaticky změní."""
        char = Char_info.objects.create(player=self.player, name='Měňavec', character_class='Tulák')
        self.assertEqual(char.profile_image_url, '/static/img/classes/tulak.svg')

        char.character_class = 'Paladin'
        char.save()
        self.assertEqual(char.profile_image_url, '/static/img/classes/paladin.svg')

    def test_upload_avatar_file_success(self):
        """Hráč může nahrát vlastní profilový obrázek."""
        self.client.login(username='hrac_avatar', password='password123')
        fake_image = SimpleUploadedFile(
            name='hrdina.png',
            content=b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4',
            content_type='image/png'
        )

        response = self.client.post(reverse('player_site_app:upload_char_avatar'), {
            'char_id': self.char_barbar.id,
            'action': 'upload',
            'image': fake_image,
            'ajax': '1',
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data['success'])
        self.assertTrue(json_data['has_custom_image'])

        self.char_barbar.refresh_from_db()
        self.assertTrue(self.char_barbar.has_custom_image)
        self.assertTrue(self.char_barbar.image.name.startswith('characters/'))
        self.assertIn('characters/', self.char_barbar.profile_image_url)

    def test_set_avatar_from_url_and_reset(self):
        """Hráč může nastavit obrázek z URL a následně jej resetovat zpět na výchozí obrázek povolání."""
        self.client.login(username='hrac_avatar', password='password123')

        # 1. Nastavení z URL
        url_resp = self.client.post(reverse('player_site_app:upload_char_avatar'), {
            'char_id': self.char_kouzelnik.id,
            'action': 'url',
            'image_url': 'https://example.com/kouzelnik_art.webp',
            'ajax': '1',
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(url_resp.status_code, 200)
        self.char_kouzelnik.refresh_from_db()
        self.assertTrue(self.char_kouzelnik.has_custom_image)
        self.assertEqual(self.char_kouzelnik.profile_image_url, 'https://example.com/kouzelnik_art.webp')

        # 2. Reset na výchozí obrázek povolání
        reset_resp = self.client.post(reverse('player_site_app:upload_char_avatar'), {
            'char_id': self.char_kouzelnik.id,
            'action': 'reset',
            'ajax': '1',
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(reset_resp.status_code, 200)
        reset_json = reset_resp.json()
        self.assertTrue(reset_json['success'])
        self.assertFalse(reset_json['has_custom_image'])
        self.assertEqual(reset_json['profile_image_url'], '/static/img/classes/kouzelnik.svg')

        self.char_kouzelnik.refresh_from_db()
        self.assertFalse(self.char_kouzelnik.has_custom_image)
        self.assertEqual(self.char_kouzelnik.profile_image_url, '/static/img/classes/kouzelnik.svg')

    def test_cannot_change_other_players_character_avatar(self):
        """Běžný hráč nemůže změnit profilový obrázek cizí postavy."""
        self.client.login(username='hrac_cizi', password='password123')
        fake_image = SimpleUploadedFile('hacked.jpg', b'fakejpgdata', content_type='image/jpeg')

        response = self.client.post(reverse('player_site_app:upload_char_avatar'), {
            'char_id': self.char_barbar.id,  # Vlastníkem je hrac_avatar
            'action': 'upload',
            'image': fake_image,
        })
        self.assertEqual(response.status_code, 404)

    def test_dm_can_change_any_character_avatar(self):
        """Dungeon Master může změnit profilový obrázek kterékoliv postavy."""
        self.client.login(username='dm_avatar', password='password123')

        resp = self.client.post(reverse('player_site_app:upload_char_avatar'), {
            'char_id': self.char_barbar.id,
            'action': 'url',
            'image_url': 'https://example.com/dm_custom_conan.png',
            'ajax': '1',
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        self.char_barbar.refresh_from_db()
        self.assertEqual(self.char_barbar.profile_image_url, 'https://example.com/dm_custom_conan.png')

    def test_overview_page_contains_clickable_avatar_and_modal(self):
        """Stránka s přehledem postavy obsahuje klikatelný avatar a modal pro změnu."""
        self.client.login(username='hrac_avatar', password='password123')
        resp = self.client.get(reverse('player_site_app:char_overview', kwargs={'char_id': self.char_barbar.id}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'char-avatar-clickable')
        self.assertContains(resp, 'openAvatarModal()')
        self.assertContains(resp, 'id="avatarModal"')
        self.assertContains(resp, 'id="avatarDropzone"')
        self.assertContains(resp, '/static/img/classes/barbar.svg')


class PlayerInventoryItemRemovalTests(TestCase):
    def setUp(self):
        OverAllSettings.objects.get_or_create(id=1, defaults={'loging_active': True, 'editing_active': True})

        # Hráč 1 a jeho postava
        self.user1 = User.objects.create_user(username='hrac_jan', password='password123')
        self.player1 = Player.objects.create(user=self.user1, nickname='Janek')
        self.char1 = Char_info.objects.create(player=self.player1, name='Galahad', level=3, character_class='Paladin')

        # Hráč 2 a jeho postava
        self.user2 = User.objects.create_user(username='hrac_petr', password='password123')
        self.player2 = Player.objects.create(user=self.user2, nickname='Petr')
        self.char2 = Char_info.objects.create(player=self.player2, name='Robin', level=2, character_class='Hraničář')

        # Předmět v batohu postavy 1
        self.item1 = Items_Active.objects.create(
            char_own=self.char1,
            name_cz='Obyčejné lano',
            name_en='Hemp Rope',
            category='Vybavení dobrodruha',
            cost_gold=1,
            weight=10.0
        )

        # Druhý předmět pro AJAX test
        self.item2 = Items_Active.objects.create(
            char_own=self.char1,
            name_cz='Pochodeň',
            name_en='Torch',
            category='Vybavení dobrodruha',
            cost_gold=0,
            cost_silver=1,
            weight=1.0
        )

    def test_player_can_remove_own_item(self):
        """Hráč může úspěšně smazat/vyřadit předmět ze svého vlastního inventáře."""
        self.client.login(username='hrac_jan', password='password123')
        delete_url = reverse('player_site_app:remove_inv_item', kwargs={'item_id': self.item1.id})

        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Items_Active.objects.filter(id=self.item1.id).exists())

        # Ověření zápisu do logu
        self.assertTrue(Logs.objects.filter(character=self.char1, message__contains='zahodil předmět').exists())

    def test_player_cannot_remove_other_players_item(self):
        """Hráč nemůže smazat předmět patřící jiné postavě jiného hráče (vrátí 403 Forbidden)."""
        self.client.login(username='hrac_petr', password='password123')
        delete_url = reverse('player_site_app:remove_inv_item', kwargs={'item_id': self.item1.id})

        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Items_Active.objects.filter(id=self.item1.id).exists())

    def test_player_ajax_item_removal(self):
        """Předmět lze smazat i přes asynchronní AJAX požadavek s vrácením JSON statusu."""
        self.client.login(username='hrac_jan', password='password123')
        delete_url = reverse('player_site_app:remove_inv_item', kwargs={'item_id': self.item2.id})

        response = self.client.post(delete_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data['status'], 'ok')
        self.assertEqual(json_data['deleted_id'], self.item2.id)
        self.assertFalse(Items_Active.objects.filter(id=self.item2.id).exists())

    def test_inv_page_renders_action_column_and_delete_form(self):
        """Stránka inventáře obsahuje sloupec Akce a formulář pro zahození předmětu."""
        self.client.login(username='hrac_jan', password='password123')
        response = self.client.get(reverse('player_site_app:inv'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Akce')
        self.assertContains(response, 'btn-item-drop')
        self.assertContains(response, reverse('player_site_app:remove_inv_item', kwargs={'item_id': self.item1.id}))

    def test_esencionik_achievement_essence_propagation_no_cycle(self):
        """Při zvýšení hodnosti v jiném úspěchu se temná esence připíše do Esencionika bez zacyklení."""
        u_ese = User.objects.create_user(username='u_ese', password='password123')
        player = Player.objects.create(user=u_ese, nickname='GeraltEse', temna_esence=0)
        char = Char_info.objects.create(player=player, name='GeraltEseChar', level=1)

        tmpl_zbohatlik, _ = Achivements_database.objects.get_or_create(
            name='Zbohatlík',
            defaults={
                'bronze_value': 10,
                'silver_value': 50,
                'gold_value': 100,
                'platinum_value': 500,
                'emerald_value': 1000,
                'diamond_value': 2000,
            }
        )
        tmpl_esencionik, _ = Achivements_database.objects.get_or_create(
            name='Esencionik',
            defaults={
                'bronze_value': 25,
                'silver_value': 50,
                'gold_value': 100,
                'platinum_value': 250,
                'emerald_value': 500,
                'diamond_value': 1000,
            }
        )

        # Zvýšíme Zbohatlíka na 100 (dosáhne bronze + silver + gold: odměny 25 + 50 + 100 = 175)
        ach_zbohatlik = Achivements_players.objects.create(
            player=player,
            char=char,
            Achivement=tmpl_zbohatlik,
            current_value=100
        )
        ach_zbohatlik.save()

        player.refresh_from_db()
        # Odměna ze Zbohatlíka (175) se propíše do Esencionika, čímž Esencionik dosáhne Gold (175 >= 100),
        # a Esencionik sám přidá hráči dalších 175 temné esence (25 + 50 + 100 = 175)!
        # Celková esence hráče: 175 + 175 = 350.
        es_ach = Achivements_players.objects.filter(char=char, Achivement=tmpl_esencionik).first()
        self.assertIsNotNone(es_ach)
        self.assertEqual(es_ach.current_value, 175.0)
        self.assertEqual(es_ach.current_status, 'gold')
        self.assertEqual(player.temna_esence, 350)

    def test_gambler_achievement_on_chest_open(self):
        """Při otevření truhly v dungeon shopu se započte +1 do úspěchu Gambler."""
        u_gam = User.objects.create_user(username='u_gam', password='password123')
        player = Player.objects.create(user=u_gam, nickname='GeraltGambler', temna_esence=50)
        char = Char_info.objects.create(player=player, name='GeraltGamblerChar', level=1)

        tmpl_gambler, _ = Achivements_database.objects.get_or_create(
            name='Gambler',
            defaults={
                'bronze_value': 10,
                'silver_value': 20,
                'gold_value': 40,
                'platinum_value': 80,
                'emerald_value': 200,
                'diamond_value': 500,
            }
        )

        chest_item = Esence_Items_Shop.objects.create(
            name='Truhla osudu',
            category='treasures',
            rarity='basic',
            cost=10
        )
        # Vytvoříme i rámeček, aby get_border_from_treasure měl co vylosovat
        Esence_Items_Shop.objects.create(
            name='Běžný rámeček z truhly',
            category='borders',
            rarity='basic',
            cost=5
        )
        owner_record = Esence_Items_Owners.objects.create(player=player, item=chest_item)

        self.client.login(username='u_gam', password='password123')
        # Nastavíme request session aktivní postavu
        session = self.client.session
        session['active_character_id'] = char.id
        session.save()

        res = self.client.post(reverse('player_site_app:use_treasure'), {
            'item_id': chest_item.id,
            'player_id': player.id,
            'char_id': char.id,
            'ajax': '1',
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(res.status_code, 200)
        gambler_record = Achivements_players.objects.filter(char=char, Achivement=tmpl_gambler).first()
        self.assertIsNotNone(gambler_record)
        self.assertEqual(gambler_record.current_value, 1.0)

    def test_achievement_display_icon_url_fallback(self):
        """Ověření URL ikony úspěchu: vrácení SVG ze static nebo nahraného obrázku."""
        tmpl = Achivements_database.objects.create(name='Cesta hrdiny', description='Zkouška')
        self.assertEqual(tmpl.display_icon_url, '/static/img/achievements/cesta_hrdiny.svg')

        tmpl_custom = Achivements_database.objects.create(name='Zcela Nový Úspěch')
        self.assertEqual(tmpl_custom.display_icon_url, '/static/img/achievements/default.svg')







