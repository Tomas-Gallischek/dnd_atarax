from django.db import migrations, models

def clean_cantrips_equipped(apps, schema_editor):
    Spells_Active = apps.get_model('dm_site_app', 'Spells_Active')
    # Nastavíme vybaveno = False pro všechny triky (úroveň 0 nebo is_cantrip=True)
    Spells_Active.objects.filter(
        models.Q(level=0) | models.Q(is_cantrip=True) |
        models.Q(template_spell__level=0) | models.Q(template_spell__is_cantrip=True)
    ).update(vybaveno=False)

def reverse_noop(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('player_site_app', '0031_alter_char_info_combat_initiative_and_more'),
        ('dm_site_app', '0021_alter_items_active_options_items_active_equip_able_and_more'),
    ]

    operations = [
        migrations.RunPython(clean_cantrips_equipped, reverse_noop),
    ]

