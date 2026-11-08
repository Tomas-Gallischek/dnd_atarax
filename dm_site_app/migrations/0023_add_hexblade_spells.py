from django.db import migrations
from dm_site_app.spells_data import HEXBLADE_SPELLS_DATA


def add_spells(apps, schema_editor):
    Spells_All_db = apps.get_model('dm_site_app', 'Spells_All_db')
    for spell_data in HEXBLADE_SPELLS_DATA:
        api_index = spell_data['api_index']
        defaults = {k: v for k, v in spell_data.items() if k != 'api_index'}
        Spells_All_db.objects.update_or_create(
            api_index=api_index,
            defaults=defaults
        )


def remove_spells(apps, schema_editor):
    Spells_All_db = apps.get_model('dm_site_app', 'Spells_All_db')
    indexes = [s['api_index'] for s in HEXBLADE_SPELLS_DATA]
    Spells_All_db.objects.filter(api_index__in=indexes).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('dm_site_app', '0022_npc_occupation_npc_race_npc_title'),
    ]

    operations = [
        migrations.RunPython(add_spells, reverse_code=remove_spells),
    ]
