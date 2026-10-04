from django.contrib import admin
from django.utils.html import format_html
from .models import Locations, Npc, NpcLoot, Monsters_All_db, Items_All_db, Monsters_Active, Items_Active


@admin.register(Locations)
class LocationsAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'layer_up', 'layer_down', 'short_description')
    list_filter = ('type', 'layer_up')
    search_fields = ('name', 'description')
    ordering = ('name',)
    list_per_page = 25

    fieldsets = (
        ('Základní informace', {
            'fields': (
                ('name', 'type'),
                ('layer_up', 'layer_down'),
            ),
        }),
        ('Popis', {
            'fields': (
                'description',
            ),
        }),
    )

    @admin.display(description='Popis')
    def short_description(self, obj):
        if obj.description and len(obj.description) > 60:
            return f"{obj.description[:60]}..."
        return obj.description or "—"



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
@admin.register(Items_All_db)
class Items_All_dbAdmin(admin.ModelAdmin):
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


# 4. Zaregistrujeme nestvůry z kompendia s komplexním a přehledným rozhraním
@admin.register(Monsters_All_db)
class Monsters_All_dbAdmin(admin.ModelAdmin):
    list_display = (
        'name_cz',
        'name_en',
        'formatted_cr_display',
        'monster_type',
        'size',
        'armor_class',
        'hit_points',
        'alignment',
    )
    list_filter = ('challenge_rating', 'monster_type', 'size', 'alignment')
    search_fields = ('name_cz', 'name_en', 'api_index', 'monster_type', 'special_abilities', 'actions')
    ordering = ('challenge_rating', 'name_cz')
    list_per_page = 25

    readonly_fields = ('image_preview', 'formatted_ability_scores')

    fieldsets = (
        ('Základní identifikace a vzhled', {
            'fields': (
                ('name_cz', 'name_en'),
                'api_index',
                ('size', 'monster_type', 'subtype'),
                'alignment',
                ('image_url', 'image_preview'),
            ),
        }),
        ('Bojové statistiky a životy', {
            'fields': (
                ('armor_class', 'armor_desc'),
                ('hit_points', 'hit_dice'),
                'speed',
            ),
        }),
        ('Základní vlastnosti (Ability Scores)', {
            'fields': (
                ('strength', 'dexterity', 'constitution'),
                ('intelligence', 'wisdom', 'charisma'),
                'formatted_ability_scores',
            ),
        }),
        ('Obrana, dovednosti a smysly', {
            'fields': (
                'saving_throws',
                'skills',
                ('damage_vulnerabilities', 'damage_resistances'),
                ('damage_immunities', 'condition_immunities'),
                ('senses', 'languages'),
            ),
        }),
        ('Nebezpečnost a odměna', {
            'fields': (
                ('challenge_rating', 'xp', 'proficiency_bonus'),
            ),
        }),
        ('Bojové akce a schopnosti', {
            'fields': (
                'special_abilities',
                'actions',
                'legendary_actions',
                'reactions',
            ),
        }),
        ('Doplňující popis a surová data (API)', {
            'classes': ('collapse',),
            'fields': (
                'description',
                'raw_data',
            ),
        }),
    )

    @admin.display(description='CR', ordering='challenge_rating')
    def formatted_cr_display(self, obj):
        return obj.formatted_cr

    @admin.display(description='Náhled obrázku')
    def image_preview(self, obj):
        if obj.image_url:
            return format_html(
                '<img src="{}" style="max-height: 120px; max-width: 150px; border-radius: 8px; border: 1px solid #555; object-fit: contain;" />',
                obj.image_url
            )
        return "Bez obrázku"

    @admin.display(description='Přehled modifikátorů')
    def formatted_ability_scores(self, obj):
        return format_html(
            "<b>SIL:</b> {} ({}) &nbsp;|&nbsp; "
            "<b>OBR:</b> {} ({}) &nbsp;|&nbsp; "
            "<b>ODL:</b> {} ({}) &nbsp;|&nbsp; "
            "<b>INT:</b> {} ({}) &nbsp;|&nbsp; "
            "<b>MDR:</b> {} ({}) &nbsp;|&nbsp; "
            "<b>CHA:</b> {} ({})",
            obj.strength, obj.str_mod,
            obj.dexterity, obj.dex_mod,
            obj.constitution, obj.con_mod,
            obj.intelligence, obj.int_mod,
            obj.wisdom, obj.wis_mod,
            obj.charisma, obj.cha_mod,
        )


# 5. Zaregistrujeme aktivní položky (Items_Active)
@admin.register(Items_Active)
class Items_ActiveAdmin(Items_All_dbAdmin):
    pass


# 6. Zaregistrujeme aktivní nestvůry (Monsters_Active)
@admin.register(Monsters_Active)
class Monsters_ActiveAdmin(Monsters_All_dbAdmin):
    pass