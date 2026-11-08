import requests
from django.core.management.base import BaseCommand
from dm_site_app.models import Spells_All_db, Spells_Active
from dm_site_app.spells_data import HEXBLADE_SPELLS_DATA


class Command(BaseCommand):
    help = (
        "Implementuje všechna kouzla, triky, vzývání a schopnosti pro Hexblade Černokněžníka "
        "a Temného elfa z Xanatharova průvodce vším (XGtE) s příznakem is_xhantar=True."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--sync-active',
            action='store_true',
            default=True,
            help='Propsat příznak is_xhantar a parametry i do již přiřazených aktivních kouzel postav (Spells_Active).',
        )
        parser.add_argument(
            '--verify-api',
            action='store_true',
            help='Volitelně ověřit dostupnost doplňkových dat přes Open5e API (https://api.open5e.com/v1/spells/).',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE(
            "⚔️ Zahajuji import / aktualizaci kompletního repertoáru Hexblade & Xanathar kouzel do databáze..."
        ))
        created_count = 0
        updated_count = 0

        if options.get('verify_api'):
            try:
                resp = requests.get("https://api.open5e.com/v1/spells/?limit=5", timeout=8)
                if resp.status_code == 200:
                    self.stdout.write(self.style.SUCCESS("🌐 Spojení s Open5e API je aktivní a ověřené."))
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f"⚠️ Open5e API není dostupné ({exc}), pokračuji z vestavěné databáze."))

        for spell_data in HEXBLADE_SPELLS_DATA:
            api_index = spell_data['api_index']
            defaults = {k: v for k, v in spell_data.items() if k != 'api_index'}
            defaults['is_xhantar'] = spell_data.get('is_xhantar', True)

            spell, created = Spells_All_db.objects.update_or_create(
                api_index=api_index,
                defaults=defaults
            )

            # Propsání is_xhantar do již existujících aktivních instancí u postav
            if options.get('sync_active', True):
                Spells_Active.objects.filter(template_spell=spell).update(
                    is_xhantar=spell.is_xhantar,
                    classes=spell.classes,
                    races=spell.races,
                )
                Spells_Active.objects.filter(api_index=api_index, template_spell__isnull=True).update(
                    template_spell=spell,
                    is_xhantar=spell.is_xhantar,
                    classes=spell.classes,
                    races=spell.races,
                )

            typ_label = "Trik (0)" if spell.is_cantrip or spell.level == 0 else f"Level {spell.level}"
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f"  [+] VYTVOŘENO: {spell.name_cz} ({spell.name_en}) [{typ_label}, is_xhantar={spell.is_xhantar}]"
                ))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(
                    f"  [*] AKTUALIZOVÁNO: {spell.name_cz} ({spell.name_en}) [{typ_label}, is_xhantar={spell.is_xhantar}]"
                ))

        total_xhantar = Spells_All_db.objects.filter(is_xhantar=True).count()
        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Hotovo! Vytvořeno: {created_count}, aktualizováno: {updated_count}. "
            f"Celkem Xanathar/Hexblade kouzel v DB: {total_xhantar} (celkem všech kouzel: {Spells_All_db.objects.count()})."
        ))
