from django.test import SimpleTestCase
from django.urls import reverse


class PlayerSiteViewTests(SimpleTestCase):
    def test_player_index_status_and_template(self):
        """Ověření dostupnosti hráčské sekce a použitých šablon."""
        response = self.client.get(reverse('player_site_app:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'player_site_app/index.html')
        self.assertTemplateUsed(response, 'player_site_app/base.html')

    def test_player_index_links_to_dm(self):
        """Ověření, že stránka obsahuje odkaz na DM sekci."""
        response = self.client.get(reverse('player_site_app:index'))
        dm_url = reverse('dm_site_app:index')
        self.assertContains(response, dm_url)

    def test_root_redirects_to_player(self):
        """Ověření, že root URL přesměrovává na hráčskou sekci."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('player_site_app:index'))
