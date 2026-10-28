from django.apps import AppConfig


class PlayerSiteAppConfig(AppConfig):
    name = 'player_site_app'

    def ready(self):
        try:
            from player_site_app.asset_definitions import ensure_all_media_assets
            ensure_all_media_assets()
        except Exception:
            pass
