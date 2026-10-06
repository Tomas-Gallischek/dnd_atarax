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

