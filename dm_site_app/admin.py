from django.contrib import admin
from django.utils.html import format_html
from .models import Locations, Npc, Monsters_All_db, Items_All_db, Monsters_Active, Items_Active


@admin.register(Locations, Npc, Monsters_All_db, Items_All_db, Monsters_Active)
#všichni
class CommonAdmin(admin.ModelAdmin):
    pass

@admin.register(Items_Active)
class Items_ActiveAdmin(admin.ModelAdmin):
    list_display = ('name_cz', 'category', 'char_own', 'cost_gold', 'cost_silver', 'damage', 'armor_class')
    list_filter = ('category', 'char_own')
    search_fields = ('name_cz', 'name_en', 'char_own__name', 'category')
    autocomplete_fields = ('char_own',)

    

