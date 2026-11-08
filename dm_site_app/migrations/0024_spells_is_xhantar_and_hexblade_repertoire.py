from django.db import migrations, models
from dm_site_app.spells_data import HEXBLADE_SPELLS_DATA


def seed_all_hexblade_spells(apps, schema_editor):
    Spells_All_db = apps.get_model('dm_site_app', 'Spells_All_db')
    Spells_Active = apps.get_model('dm_site_app', 'Spells_Active')
    valid_fields = {f.name for f in Spells_All_db._meta.fields}

    for spell_data in HEXBLADE_SPELLS_DATA:
        api_index = spell_data['api_index']
        defaults = {
            k: v for k, v in spell_data.items()
            if k != 'api_index' and k in valid_fields
        }
        defaults['is_xhantar'] = spell_data.get('is_xhantar', True)

        spell, _ = Spells_All_db.objects.update_or_create(
            api_index=api_index,
            defaults=defaults
        )

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


def reverse_seed_hexblade(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('dm_site_app', '0023_add_hexblade_spells'),
    ]

    operations = [
        migrations.AddField(
            model_name='spells_all_db',
            name='is_xhantar',
            field=models.BooleanField(default=False, verbose_name='Xanatharův průvodce (Rozšíření)'),
        ),
        migrations.AddField(
            model_name='spells_active',
            name='is_xhantar',
            field=models.BooleanField(default=False, verbose_name='Xanatharův průvodce (Rozšíření)'),
        ),
        migrations.RunPython(seed_all_hexblade_spells, reverse_code=reverse_seed_hexblade),
    ]

