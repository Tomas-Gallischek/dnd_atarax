from django.contrib import admin
from django.utils.html import format_html
from .models import Player, Char_info, Achivements_database, Achivements_players, Logs


class CharInfoInline(admin.TabularInline):
    model = Char_info
    extra = 0
    fields = ('name', 'race', 'character_class', 'level', 'hit_points_current', 'hit_points_max', 'armor_class')
    show_change_link = True


class AchivementsPlayersForPlayerInline(admin.TabularInline):
    model = Achivements_players
    extra = 0
    fields = ('Achivement', 'char', 'current_value', 'current_status')
    autocomplete_fields = ('Achivement', 'char')
    show_change_link = True
    verbose_name = "Úspěch hráče"
    verbose_name_plural = "Přiřazené úspěchy"


class AchivementsPlayersForDatabaseInline(admin.TabularInline):
    model = Achivements_players
    extra = 0
    fields = ('player', 'char', 'current_value', 'current_status')
    autocomplete_fields = ('player', 'char')
    show_change_link = True
    verbose_name = "Držitel úspěchu"
    verbose_name_plural = "Hráči s tímto úspěchem"


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('user', 'nickname', 'characters_count', 'achievements_count', 'created_at')
    search_fields = ('user__username', 'user__email', 'nickname')
    inlines = [CharInfoInline, AchivementsPlayersForPlayerInline]

    @admin.display(description='Počet postav')
    def characters_count(self, obj):
        return obj.characters.count()

    @admin.display(description='Počet úspěchů')
    def achievements_count(self, obj):
        return obj.achivements.count()


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
    list_display = (
        'name',
        'img_ozn',
        'description',
        'bronze_value',
        'silver_value',
        'gold_value',
        'platinum_value',
        'emerald_value',
        'diamond_value',
    )
    search_fields = ('name', 'description', 'img_ozn')
    ordering = ('name',)
    inlines = [AchivementsPlayersForDatabaseInline]
    fieldsets = (
        ('Základní informace o achivementu', {
            'fields': (
                ('name', 'img_ozn'),
                'description',
            ),
        }),
        ('Hodnoty pro získání achivementu', {
            'fields': (
                ('bronze_value', 'silver_value', 'gold_value'),
                ('platinum_value', 'emerald_value', 'diamond_value'),
            ),
        }),
    )


@admin.register(Achivements_players)
class AchivementsPlayersAdmin(admin.ModelAdmin):
    list_display = (
        'player',
        'char',
        'Achivement',
        'current_value',
        'status_badge',
        'tier_progress',
        'latest_obtained_milestone',
    )
    list_filter = ('current_status', 'Achivement', 'player')
    search_fields = (
        'player__nickname',
        'player__user__username',
        'char__name',
        'Achivement__name',
    )
    autocomplete_fields = ('player', 'char', 'Achivement')
    ordering = ('-current_value', 'Achivement')
    list_per_page = 25
    readonly_fields = ('status_badge', 'tier_progress')

    fieldsets = (
        ('Přiřazení hráče a postavy', {
            'fields': (
                ('player', 'char'),
            ),
        }),
        ('Úspěch a aktuální postup', {
            'fields': (
                'Achivement',
                ('current_value', 'current_status'),
                ('status_badge', 'tier_progress'),
            ),
        }),
        ('Historie milníků (data získání)', {
            'classes': ('collapse',),
            'description': 'Datumy jsou automaticky aktualizovány při dosažení dané hodnoty, lze je však v případě potřeby upravit i ručně.',
            'fields': (
                ('bronze_obtained_date', 'silver_obtained_date'),
                ('gold_obtained_date', 'platinum_obtained_date'),
                ('emerald_obtained_date', 'diamond_obtained_date'),
            ),
        }),
    )

    @admin.display(description='Aktuální status', ordering='current_status')
    def status_badge(self, obj):
        if not obj.current_status:
            return format_html(
                '<span style="background: #4b5563; color: #f3f4f6; padding: 3px 8px; border-radius: 10px; font-size: 11px; font-weight: 600;">{}</span>',
                'Zatím nezískáno'
            )

        styles = {
            'bronze': ('#cd7f32', '#ffffff', '🥉 Bronze'),
            'silver': ('#9ca3af', '#111827', '🥈 Silver'),
            'gold': ('#eab308', '#111827', '🥇 Gold'),
            'platinum': ('#06b6d4', '#ffffff', '💠 Platinum'),
            'emerald': ('#10b981', '#ffffff', '💚 Emerald'),
            'diamond': ('#8b5cf6', '#ffffff', '💎 Diamond'),
        }
        bg, fg, label = styles.get(obj.current_status, ('#6b7280', '#ffffff', obj.get_current_status_display()))
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 10px; border-radius: 10px; font-size: 11px; font-weight: 700; display: inline-block;">{}</span>',
            bg, fg, label
        )

    @admin.display(description='Cíl / Pokrok')
    def tier_progress(self, obj):
        if not obj.Achivement:
            return "—"

        def format_num(val):
            if val is None:
                return "0"
            try:
                f_val = float(val)
                if f_val.is_integer():
                    return str(int(f_val))
                return f"{f_val:g}"
            except (ValueError, TypeError):
                return str(val)

        ach = obj.Achivement
        tiers = [
            ('Bronze', ach.bronze_value),
            ('Silver', ach.silver_value),
            ('Gold', ach.gold_value),
            ('Platinum', ach.platinum_value),
            ('Emerald', ach.emerald_value),
            ('Diamond', ach.diamond_value),
        ]

        next_tier = None
        for name, val in tiers:
            if val is not None and val > 0 and obj.current_value < val:
                next_tier = (name, val)
                break

        if next_tier:
            pct = min(100, max(0, int((obj.current_value / next_tier[1]) * 100)))
            return format_html(
                '<div style="min-width: 130px;">'
                '<div style="font-size: 11px; margin-bottom: 2px; color: #ddd;">Další: <b>{}</b> ({} / {})</div>'
                '<div style="background: #374151; border-radius: 4px; height: 7px; overflow: hidden; border: 1px solid #4b5563;">'
                '<div style="background: linear-gradient(90deg, #3b82f6, #10b981); width: {}%; height: 100%;"></div>'
                '</div>'
                '</div>',
                next_tier[0], format_num(obj.current_value), format_num(next_tier[1]), pct
            )
        elif obj.current_status == 'diamond':
            return format_html(
                '<span style="color: #10b981; font-weight: bold; font-size: 11px;">{}</span>',
                '✓ Maximální úroveň'
            )
        return format_html('<span style="color: #9ca3af; font-size: 11px;">{} bodů</span>', format_num(obj.current_value))

    @admin.display(description='Poslední milník')
    def latest_obtained_milestone(self, obj):
        milestones = [
            (obj.diamond_obtained_date, '💎 Diamond'),
            (obj.emerald_obtained_date, '💚 Emerald'),
            (obj.platinum_obtained_date, '💠 Platinum'),
            (obj.gold_obtained_date, '🥇 Gold'),
            (obj.silver_obtained_date, '🥈 Silver'),
            (obj.bronze_obtained_date, '🥉 Bronze'),
        ]
        for dt, label in milestones:
            if dt:
                return format_html(
                    '<span style="font-size: 11px;"><b>{}</b><br><span style="color: #9ca3af;">{}</span></span>',
                    label, dt.strftime("%d.%m.%Y %H:%M")
                )
        return format_html('<span style="color: #6b7280; font-size: 11px;">{}</span>', '—')


@admin.register(Logs)
class LogsAdmin(admin.ModelAdmin):
    list_display = ('player', 'character', 'message', 'value', 'created_at')
    search_fields = ('player__user__username', 'player__nickname', 'character__name', 'message')
    list_filter = ('created_at', 'player')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Základní informace o logu', {
            'fields': (
                ('player', 'character'),
                ('message', 'value'),
                'created_at',
            ),
        }),
    )