from django.contrib import admin
from .models import Locations, Npc, NpcLoot

admin.site.register(Locations)


# 1. Definujeme vnořený formulář pro loot
class NpcLootInline(admin.TabularInline):
    model = NpcLoot
    extra = 1  # Kolik prázdných řádků pro přidání nového lootu se zobrazí rovnou
    
# 2. Zaregistrujeme NPC a vložíme do něj ten loot
@admin.register(Npc)
class NpcAdmin(admin.ModelAdmin):
    list_display = ('name', 'gender', 'location')
    list_filter = ('gender', 'location')
    search_fields = ('name',)
    
    # Zde připojíme tabulku s lootem přímo do detailu NPC
    inlines = [NpcLootInline]