from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Locations, Npc, Monsters_All_db, Items_All_db, Monsters_Active,
    Items_Active, OverAllSettings, Kronika, Spells_All_db, Spells_Active, DmNote
)


@admin.register(DmNote)
class DmNoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_current', 'updated_at', 'created_at')
    list_filter = ('is_current', 'category')
    search_fields = ('title', 'content', 'category')
    list_editable = ('is_current',)


@admin.register(Locations, Monsters_All_db, Monsters_Active)
#všichni
class CommonAdmin(admin.ModelAdmin):
    pass


@admin.register(Npc)
class NpcAdmin(admin.ModelAdmin):
    list_display = ('name', 'title', 'race', 'occupation', 'location', 'gender', 'is_dead', 'in_fight')
    list_filter = ('location', 'gender', 'race', 'occupation', 'is_dead', 'in_fight')
    search_fields = ('name', 'title', 'race', 'occupation', 'description', 'location__name')
    list_editable = ('title', 'race', 'occupation')


@admin.register(Items_All_db)
class Items_All_dbAdmin(admin.ModelAdmin):
    list_display = ('name_cz', 'name_en', 'category', 'equip_able', 'cost_gold', 'cost_silver', 'damage', 'armor_class', 'weight')
    list_editable = ('equip_able',)
    list_filter = ('equip_able', 'category')
    search_fields = ('name_cz', 'name_en', 'category', 'properties')


@admin.register(Items_Active)
class Items_ActiveAdmin(admin.ModelAdmin):
    list_display = ('name_cz', 'quantity', 'equip_able', 'is_equipped', 'category', 'char_own', 'cost_gold', 'cost_silver', 'damage', 'armor_class')
    list_editable = ('quantity', 'equip_able', 'is_equipped')
    list_filter = ('equip_able', 'is_equipped', 'category', 'char_own')
    search_fields = ('name_cz', 'name_en', 'char_own__name', 'category')
    autocomplete_fields = ('char_own',)


@admin.register(OverAllSettings)
class OverAllSettingsAdmin(admin.ModelAdmin):
    list_display = ('id', 'loging_active', 'editing_active')
    list_editable = ('loging_active', 'editing_active')


@admin.register(Kronika)
class KronikaAdmin(admin.ModelAdmin):
    list_display = ('nazev', 'category', 'odkryto_hracum', 'datum_vytvoreni')
    list_filter = ('category', 'odkryto_hracum')
    search_fields = ('nazev', 'popis')
    list_editable = ('odkryto_hracum',)


@admin.register(Spells_All_db)
class Spells_All_dbAdmin(admin.ModelAdmin):
    list_display = ('name_cz', 'name_en', 'level', 'is_cantrip', 'is_xhantar', 'school', 'classes', 'casting_time')
    list_filter = ('level', 'is_cantrip', 'is_xhantar', 'school')
    search_fields = ('name_cz', 'name_en', 'classes', 'description')


@admin.register(Spells_Active)
class Spells_ActiveAdmin(admin.ModelAdmin):
    list_display = ('name_cz', 'char_own', 'level', 'is_cantrip', 'is_xhantar', 'nauceno', 'vybaveno')
    list_filter = ('nauceno', 'vybaveno', 'is_xhantar', 'level', 'char_own')
    search_fields = ('name_cz', 'name_en', 'char_own__name')
    list_editable = ('nauceno', 'vybaveno')
