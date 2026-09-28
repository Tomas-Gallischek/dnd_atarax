from django.contrib import admin
from .models import Locations, Npc, NpcLoot, CompendiumItem

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


# 3. Zaregistrujeme položky z kompendia s přehledným rozhraním
@admin.register(CompendiumItem)
class CompendiumItemAdmin(admin.ModelAdmin):
    list_display = (
        'name_cz',
        'name_en',
        'category',
        'formatted_price',
        'formatted_weight',
        'damage',
        'armor_class',
    )
    list_filter = ('category',)
    search_fields = ('name_cz', 'name_en', 'api_index', 'properties', 'description')
    ordering = ('name_cz',)
    list_per_page = 25

    fieldsets = (
        ('Základní identifikace', {
            'fields': (
                ('name_cz', 'name_en'),
                'api_index',
            ),
        }),
        ('Kategorie a cena', {
            'fields': (
                'category',
                ('cost_gold', 'cost_silver'),
                'weight',
            ),
        }),
        ('Bojové statistiky a vlastnosti', {
            'fields': (
                ('damage', 'armor_class'),
                'properties',
            ),
        }),
        ('Popis předmětu', {
            'fields': ('description',),
        }),
    )

    @admin.display(description='Cena', ordering='cost_gold')
    def formatted_price(self, obj):
        parts = []
        if obj.cost_gold:
            parts.append(f"{obj.cost_gold} zl")
        if obj.cost_silver:
            parts.append(f"{obj.cost_silver} st")
        return ", ".join(parts) if parts else "0 st"

    @admin.display(description='Váha', ordering='weight')
    def formatted_weight(self, obj):
        return f"{obj.weight} lb" if obj.weight else "—"