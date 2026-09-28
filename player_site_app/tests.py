from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Player, Char_info


class PlayerAuthAndCharacterTests(TestCase):
    def setUp(self):
        # Vytvoření testovacího uživatele a hráče 1
        self.user1 = User.objects.create_user(username='hrac1', password='tajneheslo123')
        self.player1 = Player.objects.create(user=self.user1, nickname='Geralt')

        # Vytvoření testovacího uživatele a hráče 2
        self.user2 = User.objects.create_user(username='hrac2', password='tajneheslo123')
        self.player2 = Player.objects.create(user=self.user2, nickname='Dandelion')

    def test_login_index_renders(self):
        """Nepřihlášený uživatel vidí přihlašovací a registrační formulář."""
        response = self.client.get(reverse('player_site_app:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'player_site_app/login_index.html')
        self.assertContains(response, 'Přihlášení')
        self.assertContains(response, 'Registrace nového hráče')

    def test_user_registration(self):
        """Registrace nového hráče vytvoří User i Player a přesměruje na přehled postav."""
        post_data = {
            'action': 'register',
            'username': 'novy_hrac',
            'nickname': 'Legolas',
            'password': 'mojebezpecneheslo',
            'password_confirm': 'mojebezpecneheslo',
        }
        response = self.client.post(reverse('player_site_app:index'), post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('player_site_app:prehled_postav'))
        
        # Ověření vytvoření v DB
        user = User.objects.get(username='novy_hrac')
        self.assertIsNotNone(user.player)
        self.assertEqual(user.player.nickname, 'Legolas')

    def test_user_login(self):
        """Platné přihlášení přesměruje na přehled postav."""
        post_data = {
            'action': 'login',
            'username': 'hrac1',
            'password': 'tajneheslo123',
        }
        response = self.client.post(reverse('player_site_app:index'), post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('player_site_app:prehled_postav'))

    def test_unauthenticated_redirect(self):
        """Nepřihlášený uživatel je z přehledu postav přesměrován na login."""
        response = self.client.get(reverse('player_site_app:prehled_postav'))
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
        self.assertContains(response, 'žádná postava')

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
            backstory='Mocná čarodějka z Vengerbergu.',
            notes='Kouzla: Ohnivá koule, Teleportace.',
        )
        self.client.login(username='hrac1', password='tajneheslo123')
        response = self.client.get(reverse('player_site_app:char_overview', kwargs={'char_id': char.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'player_site_app/char_over_view..html')
        self.assertContains(response, 'Yennefer')
        self.assertContains(response, 'Kouzelník (Úroveň 10)')
        self.assertContains(response, 'Půlelf')
        self.assertContains(response, '48 / 52')
        self.assertContains(response, 'Mocná čarodějka z Vengerbergu.')
        self.assertContains(response, 'Kouzla: Ohnivá koule, Teleportace.')

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
        self.assertContains(response, 'žádná postava')

        # Pokus o přímé zobrazení detailu postavy cizího hráče vrátí 404
        response_detail = self.client.get(reverse('player_site_app:char_overview', kwargs={'char_id': char1.id}))
        self.assertEqual(response_detail.status_code, 404)
