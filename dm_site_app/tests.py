from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from dm_site_app.models import Locations, Npc, Items_Active, Items_All_db, DmNote
from player_site_app.models import Player, Char_info, Logs


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
            reverse('dm_site_app:player_inventory_management'),
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
            reverse('dm_site_app:player_inventory_management'),
        ]
        for url in urls_to_test:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, f"URL {url} by měla vrátit redirect 302")
            self.assertEqual(response.url, reverse('player_site_app:prehled_postav'))

    def test_staff_user_can_access_all_dm_pages(self):
        """Přihlášený uživatel s admin právy (is_staff=True) má přístup na všechny DM stránky."""
        self.client.force_login(self.dm_user)
        # index přesměrovává na sjednocené tools
        res_index = self.client.get(reverse('dm_site_app:index'))
        self.assertEqual(res_index.status_code, 302)
        self.assertEqual(res_index.url, reverse('dm_site_app:tools'))

        pages_and_templates = [
            (reverse('dm_site_app:tools'), 'dm_site_app/tools.html'),
            (reverse('dm_site_app:npc'), 'dm_site_app/npc.html'),
            (reverse('dm_site_app:locations'), 'dm_site_app/locations.html'),
            (reverse('dm_site_app:notes'), 'dm_site_app/notes.html'),
            (reverse('dm_site_app:lore'), 'dm_site_app/lore.html'),
            (reverse('dm_site_app:golds-management'), 'dm_site_app/golds_management.html'),
            (reverse('dm_site_app:player_inventory_management'), 'dm_site_app/player_inventory_management.html'),
            (reverse('dm_site_app:monster_gen_page'), 'dm_site_app/monster_gen_page.html'),
            (reverse('dm_site_app:create_custom_monster'), 'dm_site_app/create_custom_monster.html'),
        ]
        for url, template in pages_and_templates:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, f"URL {url} by měla vrátit status 200")
            self.assertTemplateUsed(response, template)
            self.assertTemplateUsed(response, 'dm_site_app/base_dm.html')
            self.assertTemplateUsed(response, 'base.html')

    def test_dm_dropdown_menu_elements_and_order(self):
        """Rozbalovací nabídka obsahuje sjednocené nástroje, NPC, lokace, poznámky, kroniku, arénu, přehled postav a odhlášení."""
        self.client.force_login(self.dm_user)
        response = self.client.get(reverse('dm_site_app:tools'))
        self.assertEqual(response.status_code, 200)

        # Kontrola přítomnosti DM navigace
        self.assertContains(response, 'id="dmNavContainer"')
        self.assertContains(response, 'id="dmNavToggleBtn"')
        self.assertContains(response, 'id="dmNavDropdown"')

        content = response.content.decode('utf-8')

        # Hledání indexů jednotlivých odkazů v HTML
        idx_tools = content.find(f'href="{reverse("dm_site_app:tools")}"')
        idx_npc = content.find(f'href="{reverse("dm_site_app:npc")}"')
        idx_locations = content.find(f'href="{reverse("dm_site_app:locations")}"')
        idx_notes = content.find(f'href="{reverse("dm_site_app:notes")}"')
        idx_kronika = content.find(f'href="{reverse("dm_site_app:kronika_edit")}"')
        idx_pvp = content.find(f'href="{reverse("dm_site_app:pvp_pre")}"')
        idx_player = content.find(f'href="{reverse("player_site_app:prehled_postav")}"')
        idx_logout = content.find(f'href="{reverse("player_site_app:logout")}"')

        # Všechny odkazy musí v menu existovat
        self.assertTrue(idx_tools != -1, "Odkaz na tools chybí")
        self.assertTrue(idx_npc != -1, "Odkaz na npc chybí")
        self.assertTrue(idx_locations != -1, "Odkaz na locations chybí")
        self.assertTrue(idx_notes != -1, "Odkaz na notes chybí")
        self.assertTrue(idx_kronika != -1, "Odkaz na kronika_edit chybí")
        self.assertTrue(idx_pvp != -1, "Odkaz na pvp_pre chybí")
        self.assertTrue(idx_player != -1, "Odkaz na player přehled postav chybí")
        self.assertTrue(idx_logout != -1, "Odkaz na odhlášení chybí")

        # Ověření přesného pořadí odkazů v sjednoceném menu:
        self.assertTrue(
            idx_tools < idx_npc < idx_locations < idx_notes < idx_kronika < idx_pvp < idx_player < idx_logout,
            "Pořadí odkazů v rozbalovací nabídce neodpovídá zadání!"
        )

    def test_dm_site_does_not_contain_player_navigation(self):
        """V DM sekci se nesmí zobrazovat hráčská navigace."""
        self.client.force_login(self.dm_user)
        response = self.client.get(reverse('dm_site_app:tools'))
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


class DMPlayerInventoryManagementTests(TestCase):
    def setUp(self):
        # DM uživatel
        self.dm_user = User.objects.create_user(username='dm_elminster', password='password123', is_staff=True)

        # Hráč a postava
        self.player_user = User.objects.create_user(username='hrac_conan', password='password123')
        self.player = Player.objects.create(user=self.player_user, nickname='Barbar')
        self.character = Char_info.objects.create(
            player=self.player,
            name='Conan Cimmerijec',
            level=5,
            character_class='Barbar',
            gold=42,
            silver=15
        )

        # Předměty v inventáři postavy
        self.item1 = Items_Active.objects.create(
            char_own=self.character,
            name_cz='Obouruční meč',
            name_en='Greatsword',
            category='Zbraně',
            cost_gold=50,
            weight=6.0,
            damage='2d6 sečné'
        )
        self.item2 = Items_Active.objects.create(
            char_own=self.character,
            name_cz='Léčivý lektvar',
            name_en='Potion of Healing',
            category='Lektvary',
            cost_gold=50,
            weight=0.5
        )
        self.item3 = Items_Active.objects.create(
            char_own=self.character,
            name_cz='Starý pergamen',
            name_en='Old Parchment',
            category='Ostatní',
            cost_gold=0,
            cost_silver=5,
            weight=0.1
        )

    def test_tools_page_contains_player_inventory_card(self):
        """V rozcestníku DM nástrojů (tools.html) je odkaz na správu inventářů postav."""
        self.client.force_login(self.dm_user)
        response = self.client.get(reverse('dm_site_app:tools'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('dm_site_app:player_inventory_management'))
        self.assertContains(response, 'Inventáře postav')

    def test_loot_management_page_contains_link_to_player_inventory(self):
        """Ve správě lootů je tlačítko směřující do správy inventářů postav."""
        self.client.force_login(self.dm_user)
        response = self.client.get(reverse('dm_site_app:loot_management'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('dm_site_app:player_inventory_management'))

    def test_dm_can_view_player_inventory_management(self):
        """DM si může zobrazit inventář postavy včetně detailů o předmětech."""
        self.client.force_login(self.dm_user)
        response = self.client.get(reverse('dm_site_app:player_inventory_management') + f'?char_id={self.character.id}')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dm_site_app/player_inventory_management.html')
        self.assertContains(response, 'Conan Cimmerijec')
        self.assertContains(response, 'Obouruční meč')
        self.assertContains(response, 'Léčivý lektvar')
        self.assertContains(response, 'Starý pergamen')

    def test_dm_can_delete_single_item(self):
        """DM může smazat předmět libovolné postavě a akce se zaloguje."""
        self.client.force_login(self.dm_user)
        del_url = reverse('dm_site_app:dm_delete_player_item', args=[self.item1.id])

        response = self.client.post(del_url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Items_Active.objects.filter(id=self.item1.id).exists())

        # Ověření zápisu v Logs
        self.assertTrue(Logs.objects.filter(character=self.character, message__contains='DM odebral předmět').exists())

    def test_dm_can_delete_item_via_ajax(self):
        """DM může smazat předmět přes AJAX s JSON odpovědí."""
        self.client.force_login(self.dm_user)
        del_url = reverse('dm_site_app:dm_delete_player_item', args=[self.item2.id])

        response = self.client.post(del_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data['status'], 'ok')
        self.assertEqual(json_data['deleted_id'], self.item2.id)
        self.assertFalse(Items_Active.objects.filter(id=self.item2.id).exists())

    def test_dm_can_bulk_delete_items(self):
        """DM může hromadně smazat vybrané předměty z inventáře postavy."""
        self.client.force_login(self.dm_user)
        bulk_url = reverse('dm_site_app:dm_bulk_delete_player_items')

        response = self.client.post(bulk_url, {
            'character_id': self.character.id,
            'item_ids': [self.item1.id, self.item3.id],
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Items_Active.objects.filter(id=self.item1.id).exists())
        self.assertFalse(Items_Active.objects.filter(id=self.item3.id).exists())
        self.assertTrue(Items_Active.objects.filter(id=self.item2.id).exists())

        # Ověření hromadného logu
        self.assertTrue(Logs.objects.filter(character=self.character, message__contains='DM hromadně odebral').exists())

    def test_dm_achievements_management_access(self):
        """DM má přístup k /dm/achievements/, běžný uživatel je odmítnut."""
        self.client.force_login(self.player_user)
        res_non_dm = self.client.get(reverse('dm_site_app:achievements_management'))
        self.assertEqual(res_non_dm.status_code, 302)

        self.client.force_login(self.dm_user)
        res_dm = self.client.get(reverse('dm_site_app:achievements_management'))
        self.assertEqual(res_dm.status_code, 200)
        self.assertContains(res_dm, 'Správa Úspěchů')

    def test_dm_assign_and_update_achievement(self):
        """DM může přiřadit libovolný úspěch jakékoliv postavě a upravit jeho hodnotu."""
        from player_site_app.models import Achivements_database, Achivements_players
        self.client.force_login(self.dm_user)

        tmpl = Achivements_database.objects.create(
            name='Testovací úspěch',
            description='Popis testu',
            bronze_value=5,
            silver_value=10,
            gold_value=20,
        )

        # 1. Přiřazení úspěchu postavě
        assign_url = reverse('dm_site_app:dm_assign_achievement')
        res_assign = self.client.post(assign_url, {
            'character_id': self.character.id,
            'template_id': tmpl.id,
            'current_value': '7',
            'mode': 'set'
        })
        self.assertEqual(res_assign.status_code, 302)

        p_ach = Achivements_players.objects.filter(char=self.character, Achivement=tmpl).first()
        self.assertIsNotNone(p_ach)
        self.assertEqual(p_ach.current_value, 7.0)
        self.assertEqual(p_ach.current_status, 'bronze')

        # 2. Úprava hodnoty úspěchu (přičtení +5 -> celkem 12, dosáhne silver)
        update_url = reverse('dm_site_app:dm_update_achievement_value', args=[p_ach.id])
        res_update = self.client.post(update_url, {
            'delta': '5'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(res_update.status_code, 200)
        json_data = res_update.json()
        self.assertEqual(json_data['status'], 'ok')
        self.assertEqual(json_data['current_value'], 12.0)
        self.assertEqual(json_data['current_status'], 'silver')

        p_ach.refresh_from_db()
        self.assertEqual(p_ach.current_value, 12.0)
        self.assertEqual(p_ach.current_status, 'silver')

        # 3. Smazání úspěchu
        del_url = reverse('dm_site_app:dm_delete_player_achievement', args=[p_ach.id])
        res_del = self.client.post(del_url)
        self.assertEqual(res_del.status_code, 302)
        self.assertFalse(Achivements_players.objects.filter(id=p_ach.id).exists())

    def test_dm_create_and_edit_achievement_template(self):
        """DM může vytvořit a upravit šablonu úspěchu."""
        from player_site_app.models import Achivements_database
        self.client.force_login(self.dm_user)

        # 1. Vytvoření šablony
        create_url = reverse('dm_site_app:dm_create_achievement_template')
        res_create = self.client.post(create_url, {
            'name': 'Lovec monster',
            'description': 'Skol 10 monster',
            'bronze_value': '1',
            'silver_value': '5',
            'gold_value': '10',
            'platinum_value': '20',
            'emerald_value': '50',
            'diamond_value': '100',
        })
        self.assertEqual(res_create.status_code, 302)

        tmpl = Achivements_database.objects.filter(name='Lovec monster').first()
        self.assertIsNotNone(tmpl)
        self.assertEqual(tmpl.gold_value, 10.0)

        # 2. Úprava šablony
        edit_url = reverse('dm_site_app:dm_edit_achievement_template', args=[tmpl.id])
        res_edit = self.client.post(edit_url, {
            'name': 'Lovec monster Elita',
            'description': 'Skol 50 monster',
            'bronze_value': '5',
            'silver_value': '15',
            'gold_value': '30',
            'platinum_value': '60',
            'emerald_value': '120',
            'diamond_value': '250',
        })
        self.assertEqual(res_edit.status_code, 302)

        tmpl.refresh_from_db()
        self.assertEqual(tmpl.name, 'Lovec monster Elita')
        self.assertEqual(tmpl.gold_value, 30.0)

    def test_create_custom_monster_success(self):
        """DM může vytvořit vlastní monstrum do bestiáře a volitelně ho aktivovat do hry."""
        from dm_site_app.models import Monsters_All_db, Monsters_Active
        self.client.force_login(self.dm_user)

        url = reverse('dm_site_app:create_custom_monster')
        get_res = self.client.get(url)
        self.assertEqual(get_res.status_code, 200)
        self.assertTemplateUsed(get_res, 'dm_site_app/create_custom_monster.html')

        post_data = {
            'name_cz': 'Stínový vlkodlak',
            'name_en': 'Shadow Werewolf',
            'size': 'Střední',
            'type': 'Monstrosita',
            'subtype': 'tvaroměnec',
            'alignment': 'chaoticky zlý',
            'armor_class': '14',
            'armor_desc': 'přirozená zbroj',
            'hit_points': '65',
            'hit_dice': '8d8 + 16',
            'speed': '12 m (40 ft)',
            'strength': '16',
            'dexterity': '14',
            'constitution': '14',
            'intelligence': '10',
            'wisdom': '12',
            'charisma': '8',
            'strength_save': '5',
            'dexterity_save': '4',
            'skills': 'Nenápadnost +4, Vnímání +5',
            'senses': 'Vidění ve tmě 18 m, Pasivní vnímání 15',
            'languages': 'Obecná řeč',
            'challenge_rating': '4',
            'cr_fraction': '4',
            'xp': '1100',
            'actions': 'Kousnutí: útok na blízko +5, zásah: 2d8+3 bodné poškození.',
            'description': 'Tvor zrozený ze stínů a měsíčního svitu.',
            'image_url': 'https://example.com/shadow_wolf.png',
            'auto_activate': 'on',
            'loot_gold': '12',
            'loot_silver': '30',
        }

        post_res = self.client.post(url, post_data)
        self.assertEqual(post_res.status_code, 302)
        self.assertEqual(post_res.url, reverse('dm_site_app:monster_gen_page'))

        # Ověření v Monsters_All_db
        db_mob = Monsters_All_db.objects.filter(name_cz='Stínový vlkodlak').first()
        self.assertIsNotNone(db_mob)
        self.assertEqual(db_mob.size, 'Střední')
        self.assertEqual(db_mob.armor_class, 14)
        self.assertEqual(db_mob.hit_points, 65)
        self.assertEqual(db_mob.strength, 16)
        self.assertEqual(db_mob.challenge_rating, 4.0)

        # Ověření v Monsters_Active
        active_mob = Monsters_Active.objects.filter(name_cz='Stínový vlkodlak').first()
        self.assertIsNotNone(active_mob)
        self.assertEqual(active_mob.current_hp, 65)
        self.assertEqual(active_mob.loot_gold, 12)
        self.assertEqual(active_mob.loot_silver, 30)

    def test_api_update_hp_batch_and_steps(self):
        """API api_update_hp dokáže dávkově aktualizovat HP monster i hráčů po ublížení či léčení."""
        import json
        from dm_site_app.models import Monsters_Active
        self.client.force_login(self.dm_user)

        # Příprava monstra a hráče
        active_mob = Monsters_Active.objects.create(
            name_cz='Skřet válečník',
            hit_points=30,
            current_hp=30,
            in_fight=True
        )
        self.character.in_fight = True
        self.character.hit_points_max = 45
        self.character.hit_points_current = 45
        self.character.save()

        # Dávková aktualizace HP (např. skřet dostal -12 dmg -> 18 HP, hráč vyléčen o +5 -> 50, oříznuto na max nebo uloženo)
        payload = {
            'updates': [
                {
                    'entity_type': 'mob',
                    'entity_id': active_mob.id,
                    'current_hp': 18
                },
                {
                    'entity_type': 'player',
                    'entity_id': self.character.id,
                    'current_hp': 40
                }
            ]
        }

        api_url = reverse('dm_site_app:api_update_hp')
        res = self.client.post(
            api_url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        res_data = res.json()
        self.assertTrue(res_data['success'])
        self.assertEqual(len(res_data['saved']), 2)

        # Kontrola v DB
        active_mob.refresh_from_db()
        self.assertEqual(active_mob.current_hp, 18)

        self.character.refresh_from_db()
        self.assertEqual(self.character.hit_points_current, 40)


class DMSpellSlotsManagementTests(TestCase):
    def setUp(self):
        self.player_user = User.objects.create_user(username='hrac_sloty', password='password123')
        self.player = Player.objects.create(user=self.player_user, nickname='KouzelnikHrac')
        self.dm_user = User.objects.create_user(username='dm_arcane', password='password123', is_staff=True)
        self.character = Char_info.objects.create(
            player=self.player,
            name='Kaelen',
            character_class='Kouzelník',
            level=5,
        )
        from player_site_app.models import CharacterSpellSlot
        self.slot1 = CharacterSpellSlot.objects.create(
            character=self.character,
            level=1,
            max_slots=4,
            current_slots=2
        )
        self.slot2 = CharacterSpellSlot.objects.create(
            character=self.character,
            level=2,
            max_slots=3,
            current_slots=3
        )

    def test_spell_slots_page_permissions(self):
        """Stránka správy pozic pro kouzla je dostupná pouze pro DM (staff)."""
        url = reverse('dm_site_app:spell_slots_management')

        # 1. Nepřihlášený -> redirect
        res_anon = self.client.get(url)
        self.assertEqual(res_anon.status_code, 302)

        # 2. Hráč bez staff -> redirect
        self.client.force_login(self.player_user)
        res_player = self.client.get(url)
        self.assertEqual(res_player.status_code, 302)

        # 3. DM -> 200 a správná šablona
        self.client.force_login(self.dm_user)
        res_dm = self.client.get(url)
        self.assertEqual(res_dm.status_code, 200)
        self.assertTemplateUsed(res_dm, 'dm_site_app/spell_slots_management.html')
        self.assertContains(res_dm, 'Správa pozic pro kouzla')
        self.assertContains(res_dm, 'Kaelen')

    def test_modify_spell_slots_actions_plus_and_minus(self):
        """DM může zvýšit a snížit počet aktuálních pozic pro kouzla (i přes AJAX)."""
        self.client.force_login(self.dm_user)
        url = reverse('dm_site_app:modify_spell_slots')

        # 1. Plus (2 -> 3)
        res_plus = self.client.post(url, {
            'action': 'plus',
            'slot_id': self.slot1.id,
            'ajax': '1',
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(res_plus.status_code, 200)
        data = res_plus.json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['current_slots'], 3)
        self.slot1.refresh_from_db()
        self.assertEqual(self.slot1.current_slots, 3)

        # 2. Minus (3 -> 2)
        res_minus = self.client.post(url, {
            'action': 'minus',
            'slot_id': self.slot1.id,
            'ajax': '1',
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(res_minus.status_code, 200)
        data_minus = res_minus.json()
        self.assertEqual(data_minus['status'], 'ok')
        self.assertEqual(data_minus['current_slots'], 2)
        self.slot1.refresh_from_db()
        self.assertEqual(self.slot1.current_slots, 2)

    def test_modify_spell_slots_restore_all_and_crud(self):
        """DM může obnovit všechny pozice na maximum, nastavit slot a smazat slot."""
        self.client.force_login(self.dm_user)
        url = reverse('dm_site_app:modify_spell_slots')

        # 1. Obnova všech pozic na maximum (Dlouhý odpočinek)
        res_restore = self.client.post(url, {
            'action': 'restore_all',
            'character_id': self.character.id,
        })
        self.assertEqual(res_restore.status_code, 302)
        self.slot1.refresh_from_db()
        self.assertEqual(self.slot1.current_slots, 4)

        # 2. Vytvoření/nastavení nového slotu (úroveň 3, max 2)
        res_set = self.client.post(url, {
            'action': 'set_slot',
            'character_id': self.character.id,
            'level': '3',
            'max_slots': '2',
            'current_slots': '2',
        })
        self.assertEqual(res_set.status_code, 302)
        from player_site_app.models import CharacterSpellSlot
        slot3 = CharacterSpellSlot.objects.filter(character=self.character, level=3).first()
        self.assertIsNotNone(slot3)
        self.assertEqual(slot3.max_slots, 2)
        self.assertEqual(slot3.current_slots, 2)

        # 3. Smazání slotu
        res_delete = self.client.post(url, {
            'action': 'delete_slot',
            'slot_id': slot3.id,
        })
        self.assertEqual(res_delete.status_code, 302)
        self.assertFalse(CharacterSpellSlot.objects.filter(id=slot3.id).exists())




