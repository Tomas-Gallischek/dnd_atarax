from django.test import SimpleTestCase
from django.urls import reverse


class DMSiteViewTests(SimpleTestCase):
    def test_dm_index_status_and_template(self):
        """Ověření dostupnosti DM sekce a použitých šablon."""
        response = self.client.get(reverse('dm_site_app:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dm_site_app/index.html')
        self.assertTemplateUsed(response, 'dm_site_app/base.html')

    def test_dm_index_links_to_player(self):
        """Ověření, že stránka obsahuje odkaz na hráčskou sekci."""
        response = self.client.get(reverse('dm_site_app:index'))
        player_url = reverse('player_site_app:index')
        self.assertContains(response, player_url)
