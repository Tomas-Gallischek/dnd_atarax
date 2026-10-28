from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from dm_site_app.models import Locations, Npc


class DMSiteAuthAndNavigationTests(TestCase):
    def setUp(self):
        # Běžný hráč (bez admin práv)
        self.player_user = User.objects.create_user(username='hrac_bob', password='password123')

        # DM / Admin uživatel (is_staff=True)
        self.dm_user = User.objects.create_user(username='dm_gandalf', password='password123', is_staff=True)

        # Ukázková lokace a NPC
        self.location = Locations.objects.create(name='Phandalin', description='Hornické městečko', type='city')
        self.npc = Npc.objects.create(name='Sildar Hallwinter', location=self.location, gender='male')

    def test_unauthenticated_user_redirected(self):
        """Nepřihlášený uživatel je přesměrován při pokusu o přístup do DM sekce."""
        urls_to_test = [
            reverse('dm_site_app:index'),
            reverse('dm_site_app:tools'),
            reverse('dm_site_app:npc'),
            reverse('dm_site_app:locations'),
            reverse('dm_site_app:notes'),
            reverse('dm_site_app:lore'),
            reverse('dm_site_app:golds-management'),
        ]
        for url in urls_to_test:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, f"URL {url} by měla vrátit redirect 302")
            self.assertEqual(response.url, reverse('player_site_app:index'))

    def test_authenticated_non_staff_user_redirected(self):
        """Přihlášený hráč bez admin práv (is_staff=False) je přesměrován na přehled postav."""
        self.client.force_login(self.player_user)
        urls_to_test = [
            reverse('dm_site_app:index'),
            reverse('dm_site_app:tools'),
            reverse('dm_site_app:npc'),
            reverse('dm_site_app:locations'),
            reverse('dm_site_app:notes'),
            reverse('dm_site_app:lore'),
            reverse('dm_site_app:golds-management'),
        ]
        for url in urls_to_test:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, f"URL {url} by měla vrátit redirect 302")
            self.assertEqual(response.url, reverse('player_site_app:prehled_postav'))

    def test_staff_user_can_access_all_dm_pages(self):
        """Přihlášený uživatel s admin právy (is_staff=True) má přístup na všechny DM stránky."""
        self.client.force_login(self.dm_user)
        pages_and_templates = [
            (reverse('dm_site_app:index'), 'dm_site_app/index_dashboard.html'),
            (reverse('dm_site_app:tools'), 'dm_site_app/tools.html'),
            (reverse('dm_site_app:npc'), 'dm_site_app/npc.html'),
            (reverse('dm_site_app:locations'), 'dm_site_app/locations.html'),
            (reverse('dm_site_app:notes'), 'dm_site_app/notes.html'),
            (reverse('dm_site_app:lore'), 'dm_site_app/lore.html'),
            (reverse('dm_site_app:golds-management'), 'dm_site_app/golds_management.html'),
        ]
        for url, template in pages_and_templates:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, f"URL {url} by měla vrátit status 200")
            self.assertTemplateUsed(response, template)
            self.assertTemplateUsed(response, 'dm_site_app/base_dm.html')
            self.assertTemplateUsed(response, 'base.html')

    def test_dm_dropdown_menu_elements_and_order(self):
        """Rozbalovací nabídka obsahuje všech 6 podstránek v přesném pořadí, odkaz na přehled postav a odhlášení."""
        self.client.force_login(self.dm_user)
        response = self.client.get(reverse('dm_site_app:index'))
        self.assertEqual(response.status_code, 200)

        # Kontrola přítomnosti DM navigace
        self.assertContains(response, 'id="dmNavContainer"')
        self.assertContains(response, 'id="dmNavToggleBtn"')
        self.assertContains(response, 'id="dmNavDropdown"')

        content = response.content.decode('utf-8')

        # Hledání indexů jednotlivých odkazů v HTML
        idx_index = content.find(f'href="{reverse("dm_site_app:index")}"')
        idx_tools = content.find(f'href="{reverse("dm_site_app:tools")}"')
        idx_npc = content.find(f'href="{reverse("dm_site_app:npc")}"')
        idx_locations = content.find(f'href="{reverse("dm_site_app:locations")}"')
        idx_notes = content.find(f'href="{reverse("dm_site_app:notes")}"')
        idx_lore = content.find(f'href="{reverse("dm_site_app:lore")}"')
        idx_player = content.find(f'href="{reverse("player_site_app:prehled_postav")}"')
        idx_logout = content.find(f'href="{reverse("player_site_app:logout")}"')

        # Všechny odkazy musí v menu existovat
        self.assertTrue(idx_index != -1, "Odkaz na index_dashboard chybí")
        self.assertTrue(idx_tools != -1, "Odkaz na tools chybí")
        self.assertTrue(idx_npc != -1, "Odkaz na npc chybí")
        self.assertTrue(idx_locations != -1, "Odkaz na locations chybí")
        self.assertTrue(idx_notes != -1, "Odkaz na notes chybí")
        self.assertTrue(idx_lore != -1, "Odkaz na lore chybí")
        self.assertTrue(idx_player != -1, "Odkaz na player přehled postav chybí")
        self.assertTrue(idx_logout != -1, "Odkaz na odhlášení chybí")

        # Ověření zachování přesného pořadí požadovaného uživatelem:
        # 1. index_dashboard -> 2. tools -> 3. npc -> 4. locations -> 5. notes -> 6. lore -> prehled_postav -> logout
        self.assertTrue(
            idx_index < idx_tools < idx_npc < idx_locations < idx_notes < idx_lore < idx_player < idx_logout,
            "Pořadí odkazů v rozbalovací nabídce neodpovídá zadání!"
        )

    def test_dm_site_does_not_contain_player_navigation(self):
        """V DM sekci se nesmí zobrazovat hráčská navigace."""
        self.client.force_login(self.dm_user)
        response = self.client.get(reverse('dm_site_app:index'))
        self.assertNotContains(response, 'id="playerNavContainer"')
        self.assertNotContains(response, 'id="playerNavToggleBtn"')

    def test_kronika_edit_crud(self):
        """DM může přidat záznam do kroniky, přepnout stav odkrytí a smazat záznam."""
        from dm_site_app.models import Kronika

        self.client.force_login(self.dm_user)

        # 1. Zobrazení stránky
        page_res = self.client.get(reverse('dm_site_app:kronika_edit'))
        self.assertEqual(page_res.status_code, 200)
        self.assertTemplateUsed(page_res, 'dm_site_app/kronika_edit.html')

        # 2. Přidání záznamu
        add_res = self.client.post(reverse('dm_site_app:kronika_edit'), {
            'action': 'add',
            'nazev': 'Pád hradeb',
            'category': 'lore',
            'popis': 'Skřeti prorazili severní bránu.',
            'odkryto_hracum': 'on',
        })
        self.assertEqual(add_res.status_code, 302)
        entry = Kronika.objects.first()
        self.assertIsNotNone(entry)
        self.assertEqual(entry.nazev, 'Pád hradeb')
        self.assertEqual(entry.category, 'lore')
        self.assertTrue(entry.odkryto_hracum)

        # 3. Přepnutí odkrytí
        toggle_res = self.client.post(reverse('dm_site_app:kronika_edit'), {
            'action': 'toggle_reveal',
            'entry_id': entry.id,
        })
        self.assertEqual(toggle_res.status_code, 302)
        entry.refresh_from_db()
        self.assertFalse(entry.odkryto_hracum)

        # 4. Smazání
        del_res = self.client.post(reverse('dm_site_app:kronika_edit'), {
            'action': 'delete',
            'entry_id': entry.id,
        })
        self.assertEqual(del_res.status_code, 302)
        self.assertEqual(Kronika.objects.count(), 0)

    def test_create_custom_item_page_and_permissions(self):
        """Stránka pro vytvoření vlastního itemu vyžaduje DM práva."""
        url = reverse('dm_site_app:create_custom_item')

        # 1. Nepřihlášený uživatel
        res_anon = self.client.get(url)
        self.assertEqual(res_anon.status_code, 302)

        # 2. Běžný hráč bez DM práv
        self.client.force_login(self.player_user)
        res_player = self.client.get(url)
        self.assertEqual(res_player.status_code, 302)

        # 3. DM uživatel
        self.client.force_login(self.dm_user)
        res_dm = self.client.get(url)
        self.assertEqual(res_dm.status_code, 200)
        self.assertTemplateUsed(res_dm, 'dm_site_app/create_custom_item.html')
        self.assertContains(res_dm, 'Vytvořit vlastní item')

    def test_create_custom_item_minimal_fields(self):
        """Vytvoření jednoduchého předmětu (např. chléb) pouze se jménem a vlastníkem."""
        from player_site_app.models import Player, Char_info
        from dm_site_app.models import Items_All_db, Items_Active

        self.client.force_login(self.dm_user)
        player = Player.objects.create(user=self.player_user, nickname='TestHrac')
        char = Char_info.objects.create(player=player, name='Glem', level=1)

        url = reverse('dm_site_app:create_custom_item')
        post_data = {
            'character_id': str(char.id),
            'name_cz': 'Křupavý chléb',
            'quantity': '2',
            'category': 'Jídlo a pití',
            'cost_gold': '0',
            'cost_silver': '2',
            'description': 'Čerstvě upečený chléb z místní pekárny.',
        }

        res = self.client.post(url, post_data)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, reverse('dm_site_app:loot_management'))

        # Záznam v Items_All_db
        template = Items_All_db.objects.filter(name_cz='Křupavý chléb').first()
        self.assertIsNotNone(template)
        self.assertEqual(template.category, 'Jídlo a pití')
        self.assertEqual(template.cost_silver, 2)
        self.assertEqual(template.cost_gold, 0)
        self.assertIsNone(template.damage)
        self.assertIsNone(template.armor_class)

        # 2 záznamy v Items_Active pro postavu
        active_items = Items_Active.objects.filter(char_own=char, name_cz='Křupavý chléb')
        self.assertEqual(active_items.count(), 2)
        first_active = active_items.first()
        self.assertEqual(first_active.description, 'Čerstvě upečený chléb z místní pekárny.')
        self.assertEqual(first_active.cost_silver, 2)

    def test_npc_crud_and_images(self):
        """Test pro NPC: výchozí obrázek, vytvoření, detail, úprava a smazání."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.client.force_login(self.dm_user)

        # 1. Výchozí obrázek bez nahraného souboru
        npc_default = Npc.objects.create(name='Tajemný cizinec')
        self.assertFalse(npc_default.has_custom_image)
        self.assertEqual(npc_default.display_image_url, '/static/img/default_npc.svg')

        # 2. Vytvoření NPC přes formulář s externí URL
        create_res = self.client.post(reverse('dm_site_app:npc_create'), {
            'name': 'Hospodský Toblen',
            'location': str(self.location.id),
            'gender': 'male',
            'description': 'Majitel hostince U Kamenného krbu.',
            'image_url': 'https://example.com/toblen.png',
            'loot_gold': '15',
            'loot_silver': '40',
            'loot_able': 'on',
        })
        self.assertEqual(create_res.status_code, 302)
        toblen = Npc.objects.filter(name='Hospodský Toblen').first()
        self.assertIsNotNone(toblen)
        self.assertTrue(toblen.has_custom_image)
        self.assertEqual(toblen.display_image_url, 'https://example.com/toblen.png')
        self.assertEqual(toblen.location, self.location)
        self.assertEqual(toblen.loot_gold, 15)
        self.assertEqual(toblen.loot_silver, 40)
        self.assertTrue(toblen.loot_able)

        # 3. Zobrazení detailu
        detail_res = self.client.get(reverse('dm_site_app:npc_detail', args=[toblen.id]))
        self.assertEqual(detail_res.status_code, 200)
        self.assertTemplateUsed(detail_res, 'dm_site_app/npc_detail.html')
        self.assertContains(detail_res, 'Hospodský Toblen')
        self.assertContains(detail_res, '15 GP')

        # 4. Úprava NPC přes formulář
        fake_avatar = SimpleUploadedFile("avatar.png", b"file_content", content_type="image/png")
        edit_res = self.client.post(reverse('dm_site_app:npc_edit', args=[toblen.id]), {
            'name': 'Toblen Kamenný krb',
            'location': str(self.location.id),
            'gender': 'male',
            'description': 'Aktualizovaný popis.',
            'image': fake_avatar,
            'loot_gold': '20',
            'loot_silver': '0',
            'is_dead': 'on',
        })
        self.assertEqual(edit_res.status_code, 302)
        toblen.refresh_from_db()
        self.assertEqual(toblen.name, 'Toblen Kamenný krb')
        self.assertTrue(toblen.is_dead)
        self.assertTrue(toblen.has_custom_image)
        self.assertIn('npcs/', toblen.display_image_url)

        # 5. Smazání NPC
        del_res = self.client.post(reverse('dm_site_app:npc_delete', args=[toblen.id]))
        self.assertEqual(del_res.status_code, 302)
        self.assertFalse(Npc.objects.filter(id=toblen.id).exists())

    def test_locations_crud_and_maps(self):
        """Test pro Lokace: výchozí mapa, vytvoření, detail, úprava a smazání."""
        self.client.force_login(self.dm_user)

        # 1. Výchozí mapa lokace
        loc_default = Locations.objects.create(name='Zapomenuté údolí', description='Pustina')
        self.assertFalse(loc_default.has_custom_image)
        self.assertEqual(loc_default.display_image_url, '/static/img/default_location.svg')

        # 2. Vytvoření lokace přes formulář
        create_res = self.client.post(reverse('dm_site_app:location_create'), {
            'name': 'Hrad Cragmaw',
            'type': 'dungeon',
            'description': 'Zřícenina hradu ovládaná skřety.',
            'layer_up': str(self.location.id),
            'image_url': 'https://example.com/cragmaw_map.jpg',
        })
        self.assertEqual(create_res.status_code, 302)
        cragmaw = Locations.objects.filter(name='Hrad Cragmaw').first()
        self.assertIsNotNone(cragmaw)
        self.assertEqual(cragmaw.type, 'dungeon')
        self.assertEqual(cragmaw.layer_up, self.location)
        self.assertTrue(cragmaw.has_custom_image)
        self.assertEqual(cragmaw.display_image_url, 'https://example.com/cragmaw_map.jpg')

        # 3. Zobrazení detailu lokace
        detail_res = self.client.get(reverse('dm_site_app:location_detail', args=[cragmaw.id]))
        self.assertEqual(detail_res.status_code, 200)
        self.assertTemplateUsed(detail_res, 'dm_site_app/location_detail.html')
        self.assertContains(detail_res, 'Hrad Cragmaw')
        self.assertContains(detail_res, 'dm-detail-map-banner')

        # 4. Úprava lokace
        edit_res = self.client.post(reverse('dm_site_app:location_edit', args=[cragmaw.id]), {
            'name': 'Pevnost Cragmaw',
            'type': 'dungeon',
            'description': 'Opravená pevnost.',
            'remove_image': 'on',
        })
        self.assertEqual(edit_res.status_code, 302)
        cragmaw.refresh_from_db()
        self.assertEqual(cragmaw.name, 'Pevnost Cragmaw')
        self.assertFalse(cragmaw.has_custom_image)
        self.assertEqual(cragmaw.display_image_url, '/static/img/default_location.svg')

        # 5. Smazání lokace
        del_res = self.client.post(reverse('dm_site_app:location_delete', args=[cragmaw.id]))
        self.assertEqual(del_res.status_code, 302)
        self.assertFalse(Locations.objects.filter(id=cragmaw.id).exists())

    def test_notes_crud_and_current_pinning_order(self):
        """Test pro DM Poznámky: vytvoření, úprava, řazení aktuálních nahoře a smazání."""
        from dm_site_app.models import DmNote
        self.client.force_login(self.dm_user)

        # 1. Vytvoření běžné starší poznámky
        old_note = DmNote.objects.create(
            title='Staré zápletky',
            content='<p>Informace z minulého sezení.</p>',
            category='Zápletky',
            is_current=False
        )

        # 2. Vytvoření nové poznámky přes formulář s označením aktuální (is_current=True)
        create_res = self.client.post(reverse('dm_site_app:note_create'), {
            'title': 'Příprava na bitvu o Phandalin',
            'content': '<h2>Cíle sezení:</h2><ul><li>Bránit radnici</li><li>Najít mapu</li></ul>',
            'category': 'Příprava sezení',
            'is_current': 'on',
        })
        self.assertEqual(create_res.status_code, 302)
        active_note = DmNote.objects.filter(title='Příprava na bitvu o Phandalin').first()
        self.assertIsNotNone(active_note)
        self.assertTrue(active_note.is_current)

        # 3. Ověření řazení: aktuální poznámka MUSÍ být v querysetu na 1. místě!
        ordered_notes = list(DmNote.objects.all())
        self.assertEqual(ordered_notes[0].id, active_note.id, "Poznámka s is_current=True musí být první v pořadí!")

        # 4. Zobrazení stránky poznámek s reader view
        notes_res = self.client.get(reverse('dm_site_app:notes'))
        self.assertEqual(notes_res.status_code, 200)
        self.assertTemplateUsed(notes_res, 'dm_site_app/notes.html')
        self.assertContains(notes_res, 'Příprava na bitvu o Phandalin')
        self.assertContains(notes_res, 'Bránit radnici')
        self.assertContains(notes_res, 'Aktuální')

        # 5. Úprava poznámky
        edit_res = self.client.post(reverse('dm_site_app:note_edit', args=[active_note.id]), {
            'title': 'Příprava na bitvu o Phandalin - DOKONČENO',
            'content': '<p>Bitva proběhla úspěšně.</p>',
            'category': 'Kampaň',
            'is_current': 'on',
        })
        self.assertEqual(edit_res.status_code, 302)
        active_note.refresh_from_db()
        self.assertEqual(active_note.title, 'Příprava na bitvu o Phandalin - DOKONČENO')

        # 6. Přepnutí statusu aktuální (toggle_current)
        toggle_res = self.client.get(reverse('dm_site_app:note_toggle_current', args=[active_note.id]))
        self.assertEqual(toggle_res.status_code, 302)
        active_note.refresh_from_db()
        self.assertFalse(active_note.is_current)

        # 7. Smazání poznámky
        del_res = self.client.post(reverse('dm_site_app:note_delete', args=[active_note.id]))
        self.assertEqual(del_res.status_code, 302)
        self.assertFalse(DmNote.objects.filter(id=active_note.id).exists())


