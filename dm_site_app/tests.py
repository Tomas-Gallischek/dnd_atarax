from django.test import SimpleTestCase
from django.urls import reverse


class DMSiteViewTests(SimpleTestCase):
    def test_dm_index_status_and_template(self):
        response = self.client.get(reverse('dm_site_app:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dm_site_app/index.html')
        self.assertTemplateUsed(response, 'base.html')

    def test_dm_index_links_to_player(self):
        response = self.client.get(reverse('dm_site_app:index'))
        player_url = reverse('player_site_app:index')
        self.assertContains(response, player_url)
