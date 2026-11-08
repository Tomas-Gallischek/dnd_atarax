from django.core.management.base import BaseCommand
from dm_site_app.models import Spells_All_db
from dm_site_app.spells_data import HEXBLADE_SPELLS_DATA


class Command(BaseCommand):
    help = "Implementuje kouzla a schopnosti Hexblade (Kletba čepelníka, Prokletý válečník, Štít, Hněvivý úder) do databáze Spells_All_db."

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Vynutit přepsání existujících záznamů výchozími daty.',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("⚔️ Zahajuji import / aktualizaci Hexblade kouzel do databáze..."))
        created_count = 0
        updated_count = 0

        for spell_data in HEXBLADE_SPELLS_DATA:
            api_index = spell_data['api_index']
            defaults = {k: v for k, v in spell_data.items() if k != 'api_index'}

            spell, created = Spells_All_db.objects.update_or_create(
                api_index=api_index,
                defaults=defaults
            )

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f"  [+] VYTVOŘENO: {spell.name_cz} ({spell.name_en}) [Level {spell.level}, {spell.classes}]"
                ))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(
                    f"  [*] AKTUALIZOVÁNO: {spell.name_cz} ({spell.name_en}) [Level {spell.level}, {spell.classes}]"
                ))

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Hotovo! Vytvořeno: {created_count}, aktualizováno: {updated_count}. Celkem v DB: {Spells_All_db.objects.count()} kouzel."
        ))

