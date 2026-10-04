from django.contrib import admin
from django.utils.html import format_html
from .models import Locations, Npc, NpcLoot, Monsters_All_db, Items_All_db, Monsters_Active, Items_Active


@admin.register(Locations, Npc, NpcLoot, Monsters_All_db, Items_All_db, Monsters_Active, Items_Active )
#všichni
class CommonAdmin(admin.ModelAdmin):
    pass

#jednotlivý
class LocationAdmin(admin.ModelAdmin):
    pass
class NpcAdmin(admin.ModelAdmin):
    pass
class NpcLootAdmin(admin.ModelAdmin):
    pass
class Monster_All_dbAdmin(admin.ModelAdmin):
    pass
class Items_All_dbAdmin(admin.ModelAdmin):
    pass
class Monsters_ActiveAdmin(admin.ModelAdmin):
    pass
class Items_ActiveAdmin(admin.ModelAdmin):
    pass

    

