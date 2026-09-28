from django.contrib import admin
from .models import Player, Char_info


class CharInfoInline(admin.TabularInline):
    model = Char_info
    extra = 0
    fields = ('name', 'race', 'character_class', 'level', 'hp_points_current', 'hp_points_max', 'armor_class')
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
        'hp_points_current',
        'hp_points_max',
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
                ('hp_points_current', 'hp_points_max'),
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
