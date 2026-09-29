from django.contrib import admin
from .models import Player, Char_info, Achivements_database, Achivements_players, Logs


class CharInfoInline(admin.TabularInline):
    model = Char_info
    extra = 0
    fields = ('name', 'race', 'character_class', 'level', 'hit_points_current', 'hit_points_max', 'armor_class')
    show_change_link = True


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('user', 'nickname', 'characters_count', 'created_at')
    search_fields = ('user__username', 'user__email', 'nickname')
    inlines = [CharInfoInline]

    @admin.display(description='Počet postav')
    def characters_count(self, obj):
        return obj.characters.count()


@admin.register(Char_info)
class CharInfoAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'player',
        'character_class',
        'race',
        'level',
        'hit_points_current',
        'hit_points_max',
        'armor_class',
    )
    list_filter = ('character_class', 'race', 'level', 'player')
    search_fields = ('name', 'player__user__username', 'player__nickname', 'backstory')
    ordering = ('-level', 'name')

    fieldsets = (
        ('Hráč a identita postavy', {
            'fields': (
                'player',
                ('name', 'character_class', 'level'),
                ('race', 'background', 'alignment'),
                'experience_points',
            ),
        }),
        ('Bojové statistiky & Životy', {
            'fields': (
                ('hit_points_current', 'hit_points_max'),
                ('armor_class', 'speed'),
            ),
        }),
        ('Základní vlastnosti (Ability Scores)', {
            'fields': (
                ('strength', 'dexterity', 'constitution'),
                ('intelligence', 'wisdom', 'charisma'),
            ),
        }),
        ('Příběh a poznámky', {
            'fields': (
                'backstory',
                'notes',
            ),
        }),
    )

@admin.register(Achivements_database)
class AchivementsDatabaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'bronze_value', 'silver_value', 'gold_value', 'platinum_value', 'emerald_value', 'diamond_value')
    search_fields = ('name', 'description')
    ordering = ('name',)
    fieldsets = (
        ('Základní informace o achivementu', {
            'fields': (
                ('name', 'description'),
            ),
        }),
        ('Hodnoty pro získání achivementu', {
            'fields': (
                ('bronze_value', 'silver_value', 'gold_value'),
                ('platinum_value', 'emerald_value', 'diamond_value'),
            ),
        }),
    )

    def has_add_permission(self, request):
        return True

    def has_change_permission(self, request, obj=None):
        return True


@admin.register(Achivements_players)
class AchivementsPlayersAdmin(admin.ModelAdmin):
    list_display = ('player', 'Achivement', 'current_status', 'current_value', 'bronze_obtained_date', 'silver_obtained_date', 'gold_obtained_date', 'platinum_obtained_date', 'emerald_obtained_date', 'diamond_obtained_date')
    list_filter = ('current_status', 'Achivement', 'player')
    search_fields = ('player__user__username', 'player__nickname', 'Achivement__name')
    ordering = ('-current_value', 'Achivement')
    fieldsets = (
        ('Hráč a achivement', {
            'fields': (
                ('player', 'Achivement'),
            ),
        }),
        ('Aktuální status', {
            'fields': (
                ('current_status', 'current_value'),
            ),
        }),
        ('Datumy získání', {
            'fields': (
                ('bronze_obtained_date', 'silver_obtained_date', 'gold_obtained_date'),
                ('platinum_obtained_date', 'emerald_obtained_date', 'diamond_obtained_date'),
            ),
        }),
    )

    def has_add_permission(self, request):
        return True

    def has_change_permission(self, request, obj=None):
        return True

@admin.register(Logs)
class LogsAdmin(admin.ModelAdmin):
    list_display = ('player', 'message', 'value')
    search_fields = ('player__user__username', 'player__nickname', 'message')
    ordering = ('created_at',)
    fieldsets = (
        ('Základní informace o logu', {
            'fields': (
                ('player', 'message'),
            ),
        }),
    )