from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import (
    Player, Char_info, Achivements_players, Achivements_database,
    Esence_Items_Shop, Esence_Items_Owners, CharNotes, CharBackstory
)
from .forms import PlayerLoginForm, PlayerRegistrationForm
from dnd_atarax.terminal import log_player, log_warning, log_info
from dm_site_app.models import (
    Items_Active, OverAllSettings, Kronika, Spells_All_db, Spells_Active
)
import random
import time


def get_player_and_character(request, char_id=None):
    """
    Pomocná funkce pro bezpečné získání profilu hráče a aktivní postavy.
    Zaručuje striktní izolaci dat: hráč se nikdy nedostane k datům jiného hráče.
    """
    player, _ = Player.objects.get_or_create(user=request.user, defaults={'nickname': request.user.username})

    if char_id:
        character = get_object_or_404(Char_info, id=char_id, player=player)
        request.session['active_char_id'] = character.id
        return player, character

    session_char_id = request.session.get('active_char_id')
    if session_char_id:
        character = Char_info.objects.filter(id=session_char_id, player=player).first()
        if character:
            return player, character

    first_char = player.characters.first()
    if first_char:
        request.session['active_char_id'] = first_char.id
        return player, first_char

    return player, None



def index(request):
    """
    Úvodní stránka hráčské sekce:
    - Pokud je hráč přihlášen, přesměruje ho na přehled postav (nebo staff na dm:index).
    - Zjišťuje nastavení OverAllSettings.loging_active.
    - Pokud je loging_active vypnutý (False), zobrazí uvítací obrazovku 'Vítejte'.
    - Pokud je loging_active zapnutý (True), zobrazí formulář pro zadání PIN kódu.
    - Omezuje počet pokusů na max 3.
    """
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('dm_site_app:index')
        return redirect('player_site_app:prehled_postav')

    settings_obj = OverAllSettings.objects.first()
    loging_active = settings_obj.loging_active if settings_obj else True

    # Sledování pokusů v session (max 3 pokusy)
    now_ts = int(time.time())
    lockout_until = request.session.get('pin_lockout_until', 0)
    is_locked_out = (lockout_until > now_ts)

    # Pokud lockout vypršel, resetujeme pokusy
    if not is_locked_out and lockout_until > 0:
        request.session['pin_attempts'] = 0
        request.session['pin_lockout_until'] = 0

    attempts_used = request.session.get('pin_attempts', 0)
    attempts_left = max(0, 3 - attempts_used)

    if request.method == 'POST':
        if not loging_active:
            messages.error(request, "Přihlašování je v tuto chvíli pozastaveno Pánem jeskyně.")
            return render(request, 'player_site_app/login_index.html', {
                'loging_active': False,
                'attempts_left': attempts_left,
                'is_locked_out': False,
            })

        if is_locked_out:
            mins_left = max(1, ((lockout_until - now_ts) // 60) + 1)
            messages.error(request, f"Byl vyčerpán maximální počet pokusů (3/3). Přihlášení je zablokováno, zkuste to znovu za {mins_left} min.")
            return render(request, 'player_site_app/login_index.html', {
                'loging_active': True,
                'attempts_left': 0,
                'is_locked_out': True,
                'lockout_remaining_sec': max(0, lockout_until - now_ts),
            })

        pin = request.POST.get('pin', '').strip()

        # Validace formátu: celé číslo do 100 znaků
        if not pin or not pin.isdigit() or len(pin) > 100:
            attempts_used += 1
            request.session['pin_attempts'] = attempts_used
            attempts_left = max(0, 3 - attempts_used)

            if attempts_used >= 3:
                request.session['pin_lockout_until'] = now_ts + 300
                is_locked_out = True
                log_warning("Vyčerpány pokusy o PIN", "Session překročila 3 pokusy. Lockout na 5 minut.")
                messages.error(request, "Vyčerpali jste maximální počet 3 pokusů. Přihlášení bylo zablokováno na 5 minut.")
            else:
                log_warning("Neplatný formát PINu", f"Zadáno: '{pin[:20]}...'")
                messages.error(request, f"PIN musí být celé číslo o délce do 100 číslic. Zbývající pokusy: {attempts_left} z 3.")

            return render(request, 'player_site_app/login_index.html', {
                'loging_active': True,
                'attempts_left': attempts_left,
                'is_locked_out': is_locked_out,
                'lockout_remaining_sec': 300 if is_locked_out else 0,
            })

        # Vyhledání hráče podle unikátního PINu
        player = Player.objects.filter(pin_code=pin).first()

        if player:
            # Úspěšné přihlášení -> reset pokusů
            request.session['pin_attempts'] = 0
            request.session['pin_lockout_until'] = 0

            # Zajištění vazby na User
            if not player.user:
                player.save()
            user = player.user

            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            role = "DM / Staff 🛡️" if user.is_staff else "Hráč 🧙"
            log_player("Přihlášení hráče přes PIN", f"'{player.nickname or user.username}' [{role}]")
            messages.success(request, f"Vítej ve hře, {player.nickname or user.username}!")

            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            if user.is_staff:
                return redirect('dm_site_app:index')
            return redirect('player_site_app:prehled_postav')

        else:
            # Neplatný PIN
            attempts_used += 1
            request.session['pin_attempts'] = attempts_used
            attempts_left = max(0, 3 - attempts_used)

            if attempts_used >= 3:
                request.session['pin_lockout_until'] = now_ts + 300
                is_locked_out = True
                log_warning("Vyčerpány pokusy o PIN", "Chybný PIN 3x za sebou. Lockout na 5 minut.")
                messages.error(request, "Nesprávný PIN. Vyčerpali jste všechny 3 pokusy. Přihlášení bylo zablokováno na 5 minut.")
            else:
                log_warning("Neúspěšné přihlášení PINem", f"Zbývá pokusů: {attempts_left}")
                messages.error(request, f"Nesprávný PIN kód! Zbývající pokusy: {attempts_left} z 3.")

            return render(request, 'player_site_app/login_index.html', {
                'loging_active': True,
                'attempts_left': attempts_left,
                'is_locked_out': is_locked_out,
                'lockout_remaining_sec': 300 if is_locked_out else 0,
            })

    return render(request, 'player_site_app/login_index.html', {
        'loging_active': loging_active,
        'attempts_left': attempts_left,
        'is_locked_out': is_locked_out,
        'lockout_remaining_sec': max(0, lockout_until - now_ts) if is_locked_out else 0,
    })


def logout_view(request):
    """Odhlásí hráče a přesměruje na login."""
    user_name = request.user.username if request.user.is_authenticated else "Neznámý"
    logout(request)
    log_player("Odhlášení uživatele", f"'{user_name}'")
    messages.info(request, "Byl jsi úspěšně odhlášen.")
    return redirect('player_site_app:index')


# ---------------------------------------------------------
# Chráněné stránky hráče (přístupné POUZE přihlášenému)
# ---------------------------------------------------------

@login_required(login_url='player_site_app:index')
def prehled_postav(request):
    """8. Přehled postav - seznam postav patřících pouze přihlášenému hráči."""
    player, _ = Player.objects.get_or_create(user=request.user, defaults={'nickname': request.user.username})
    characters = player.characters.all()

    return render(request, 'player_site_app/prehled_postav.html', {
        'player': player,
        'characters': characters,
        'active_character': characters.first() if characters.exists() else None,
        'current_page': 'prehled_postav',
    })


@login_required(login_url='player_site_app:index')
def char_overview(request, char_id=None):
    """1. Přehled postavy - detail zvolené nebo aktivní postavy a její poznámky."""
    player, character = get_player_and_character(request, char_id)
    notes = character.char_notes.all() if character else []

    return render(request, 'player_site_app/char_over_view..html', {
        'player': player,
        'character': character,
        'active_character': character,
        'current_page': 'char_overview',
        'notes': notes,
    })


@login_required(login_url='player_site_app:index')
def add_char_note(request):
    """Vytvoří novou soukromou poznámku k postavě."""
    if request.method == 'POST':
        char_id = request.POST.get('char_id')
        player = get_object_or_404(Player, user=request.user)
        character = get_object_or_404(Char_info, id=char_id, player=player)

        title = request.POST.get('title', '').strip() or 'Nová poznámka'
        note_text = request.POST.get('note', '').strip()

        if not note_text:
            messages.error(request, "Text poznámky nesmí být prázdný.")
        else:
            CharNotes.objects.create(
                player=player,
                character=character,
                title=title,
                note=note_text,
                is_favorite=False
            )
            messages.success(request, f"Poznámka '{title}' byla uložena.")

        return redirect('player_site_app:char_overview', char_id=character.id)
    return redirect('player_site_app:char_overview_active')


@login_required(login_url='player_site_app:index')
def delete_char_note(request, note_id):
    """Smaže soukromou poznámku hráče."""
    player = get_object_or_404(Player, user=request.user)
    note_obj = get_object_or_404(CharNotes, id=note_id, player=player)
    char_id = note_obj.character.id
    title = note_obj.title
    note_obj.delete()
    messages.info(request, f"Poznámka '{title}' byla smazána.")
    return redirect('player_site_app:char_overview', char_id=char_id)


@login_required(login_url='player_site_app:index')
def toggle_favorite_note(request, note_id):
    """Přepne stav oblíbené poznámky (hvězdička)."""
    player = get_object_or_404(Player, user=request.user)
    note_obj = get_object_or_404(CharNotes, id=note_id, player=player)
    note_obj.is_favorite = not note_obj.is_favorite
    note_obj.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax'):
        return JsonResponse({'status': 'ok', 'is_favorite': note_obj.is_favorite})

    return redirect('player_site_app:char_overview', char_id=note_obj.character.id)


@login_required(login_url='player_site_app:index')
def inv_view(request, char_id=None):
    """2. Inventář aktivní postavy."""
    player, character = get_player_and_character(request, char_id)

    categories = []
    total_weight = 0.0
    if character:
        inv_all_items = Items_Active.objects.filter(char_own=character).order_by('name_cz', 'name_en')
        categories = sorted(list(set(item.category for item in inv_all_items if item.category)))
        total_weight = sum((item.weight or 0.0) for item in inv_all_items)
    else:
        inv_all_items = Items_Active.objects.none()

    return render(request, 'player_site_app/inv.html', {
        'player': player,
        'character': character,
        'active_character': character,
        'current_page': 'inv',
        'inv_all_items': inv_all_items,
        'categories': categories,
        'total_weight': round(total_weight, 2),
    })


def get_max_spell_level_for_character(character):
    """Vypočítá nejvyšší úroveň kouzel (1-9), kterou postava může sesílat podle úrovně a povolání."""
    if not character:
        return 0
    lvl = max(1, character.level)
    char_class = (character.character_class or "").lower().strip()

    full_casters = [
        "kouzelník", "čaroděj", "klerik", "druid", "bard", "černokněžník",
        "wizard", "sorcerer", "cleric", "druid", "bard", "warlock"
    ]
    half_casters = ["paladin", "hraničář", "ranger"]
    third_casters = ["bojovník", "tulák", "fighter", "rogue"]

    if any(fc in char_class for fc in full_casters):
        return min(9, (lvl + 1) // 2)
    elif any(hc in char_class for hc in half_casters):
        if lvl < 2:
            return 0
        return min(5, (lvl - 1) // 4 + 1)
    elif any(tc in char_class for tc in third_casters):
        if lvl < 3:
            return 0
        elif lvl < 7:
            return 1
        elif lvl < 13:
            return 2
        elif lvl < 19:
            return 3
        return 4
    else:
        return min(9, max(1, (lvl + 1) // 2))


@login_required(login_url='player_site_app:index')
def char_schopnosti_view(request, char_id=None):
    """3. Schopnosti, triky a kouzla aktivní postavy (RPG strom/stupnice)."""
    player, character = get_player_and_character(request, char_id)

    if not character:
        return render(request, 'player_site_app/char_schopnosti.html', {
            'player': player,
            'character': None,
            'active_character': None,
            'current_page': 'char_schopnosti',
            'level_tiers': [],
            'spell_items': [],
        })

    max_spell_level = get_max_spell_level_for_character(character)

    class_name = (character.character_class or "").strip()
    race_name = (character.race or "").strip()
    bg_name = (character.background or "").strip()

    # 1. Filtrování relevantních kouzel pro postavu
    q = Q()
    if class_name and class_name != "Ostatní":
        q |= Q(classes__icontains=class_name)
    if race_name and race_name != "Ostatní":
        q |= Q(races__icontains=race_name)
    if bg_name and bg_name != "Ostatní":
        q |= Q(backgrounds__icontains=bg_name)

    active_spells_qs = Spells_Active.objects.filter(char_own=character)
    active_map = {sa.template_spell_id: sa for sa in active_spells_qs if sa.template_spell_id}
    active_by_index = {sa.api_index: sa for sa in active_spells_qs if sa.api_index}

    # Zahrnout kouzla, která již postava v DB vlastní
    active_template_ids = [sa.template_spell_id for sa in active_spells_qs if sa.template_spell_id]
    if active_template_ids:
        q |= Q(id__in=active_template_ids)

    relevant_spells = Spells_All_db.objects.filter(q).distinct().order_by('level', 'name_cz')
    # Pokud pro zadané povolání/rasu v DB zatím nejsou žádná specifická kouzla, zobrazit všechna dostupná
    if not relevant_spells.exists():
        relevant_spells = Spells_All_db.objects.all().order_by('level', 'name_cz')

    # 2. Sestavení položek kouzel se stavem
    spell_items = []
    for sp in relevant_spells:
        active_inst = active_map.get(sp.id) or active_by_index.get(sp.api_index)
        is_learned = bool(active_inst and active_inst.nauceno)
        is_equipped = bool(active_inst and active_inst.vybaveno)
        can_learn = (sp.level == 0) or (sp.level <= max_spell_level)

        if is_equipped:
            state = 'equipped'
        elif is_learned:
            state = 'learned'
        elif can_learn:
            state = 'available'
        else:
            state = 'locked'

        spell_items.append({
            'id': sp.id,
            'api_index': sp.api_index,
            'name_cz': sp.name_cz,
            'name_en': sp.name_en,
            'level': sp.level,
            'is_cantrip': sp.is_trick,
            'school': sp.school or "Univerzální",
            'school_en': sp.school_en,
            'casting_time': sp.casting_time or "1 akce",
            'range': sp.range or "Dotyk",
            'components': sp.components or "V, S",
            'material': sp.material or "",
            'duration': sp.duration or "Ihned",
            'concentration': sp.concentration,
            'ritual': sp.ritual,
            'attack_type': sp.attack_type or "",
            'damage_type': sp.damage_type or "",
            'damage_dice': sp.damage_dice or "",
            'saving_throw': sp.saving_throw or "",
            'heal_dice': sp.heal_dice or "",
            'description': sp.description or "",
            'higher_levels': sp.higher_levels or "",
            'classes': sp.classes or "",
            'races': sp.races or "",
            'icon_url': sp.display_icon_url,
            'is_learned': is_learned,
            'is_equipped': is_equipped,
            'can_learn': can_learn,
            'state': state,
            'active_id': active_inst.id if active_inst else None,
        })

    # 3. Skupiny podle úrovní (0 až 9) pro levou stupnici levelů a pravý strom
    level_tiers = []
    for lvl in range(10):
        tier_spells = [s for s in spell_items if s['level'] == lvl]
        tier_unlocked = (lvl == 0) or (lvl <= max_spell_level)
        level_tiers.append({
            'level': lvl,
            'name': "Magické triky (Cantrips)" if lvl == 0 else f"{lvl}. Úroveň kouzel",
            'short_title': "Triky" if lvl == 0 else f"Úroveň {lvl}",
            'is_cantrip': (lvl == 0),
            'is_unlocked': tier_unlocked,
            'spells': tier_spells,
            'total_count': len(tier_spells),
            'learned_count': sum(1 for s in tier_spells if s['is_learned']),
            'equipped_count': sum(1 for s in tier_spells if s['is_equipped']),
        })

    total_learned = sum(1 for s in spell_items if s['is_learned'])
    total_equipped = sum(1 for s in spell_items if s['is_equipped'])
    total_cantrips_learned = sum(1 for s in spell_items if s['level'] == 0 and s['is_learned'])
    total_spells_learned = sum(1 for s in spell_items if s['level'] > 0 and s['is_learned'])

    return render(request, 'player_site_app/char_schopnosti.html', {
        'player': player,
        'character': character,
        'active_character': character,
        'current_page': 'char_schopnosti',
        'level_tiers': level_tiers,
        'spell_items': spell_items,
        'max_spell_level': max_spell_level,
        'total_learned': total_learned,
        'total_equipped': total_equipped,
        'total_cantrips_learned': total_cantrips_learned,
        'total_spells_learned': total_spells_learned,
    })


@login_required(login_url='player_site_app:index')
def toggle_learn_spell(request):
    """Přepne stav 'naučeno' pro kouzlo postavy."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Pouze POST metoda'}, status=405)

    char_id = request.POST.get('char_id')
    spell_id = request.POST.get('spell_id')
    action = request.POST.get('action', 'toggle')

    player = get_object_or_404(Player, user=request.user)
    character = get_object_or_404(Char_info, id=char_id, player=player)
    spell_template = get_object_or_404(Spells_All_db, id=spell_id)

    active_spell, created = Spells_Active.objects.get_or_create(
        char_own=character,
        template_spell=spell_template,
        defaults={
            'api_index': spell_template.api_index,
            'name_cz': spell_template.name_cz,
            'name_en': spell_template.name_en,
            'level': spell_template.level,
            'is_cantrip': spell_template.is_cantrip,
            'school': spell_template.school,
            'school_en': spell_template.school_en,
            'casting_time': spell_template.casting_time,
            'range': spell_template.range,
            'components': spell_template.components,
            'material': spell_template.material,
            'duration': spell_template.duration,
            'concentration': spell_template.concentration,
            'ritual': spell_template.ritual,
            'attack_type': spell_template.attack_type,
            'damage_type': spell_template.damage_type,
            'damage_dice': spell_template.damage_dice,
            'saving_throw': spell_template.saving_throw,
            'heal_dice': spell_template.heal_dice,
            'description': spell_template.description,
            'higher_levels': spell_template.higher_levels,
            'classes': spell_template.classes,
            'races': spell_template.races,
            'backgrounds': spell_template.backgrounds,
            'icon': spell_template.icon,
            'icon_url': spell_template.icon_url,
            'raw_data': spell_template.raw_data,
            'nauceno': True,
            'vybaveno': False,
        }
    )

    if not created:
        if action == 'learn':
            active_spell.nauceno = True
        elif action == 'unlearn':
            active_spell.nauceno = False
            active_spell.vybaveno = False
        else:
            active_spell.nauceno = not active_spell.nauceno
            if not active_spell.nauceno:
                active_spell.vybaveno = False
        active_spell.save()

    action_str = "Naučeno" if active_spell.nauceno else "Zapomenuto"
    log_info(f"Kouzlo '{spell_template.name_cz}' u postavy '{character.name}': {action_str}")

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == '1':
        return JsonResponse({
            'success': True,
            'spell_id': spell_template.id,
            'nauceno': active_spell.nauceno,
            'vybaveno': active_spell.vybaveno,
        })

    messages.success(request, f"Kouzlo {spell_template.name_cz} bylo aktualizováno.")
    return redirect('player_site_app:char_schopnosti_detail', char_id=character.id)


@login_required(login_url='player_site_app:index')
def toggle_equip_spell(request):
    """Přepne stav 'vybaveno' pro naučené kouzlo postavy."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Pouze POST metoda'}, status=405)

    char_id = request.POST.get('char_id')
    spell_id = request.POST.get('spell_id')

    player = get_object_or_404(Player, user=request.user)
    character = get_object_or_404(Char_info, id=char_id, player=player)
    spell_template = get_object_or_404(Spells_All_db, id=spell_id)

    active_spell, created = Spells_Active.objects.get_or_create(
        char_own=character,
        template_spell=spell_template,
        defaults={
            'api_index': spell_template.api_index,
            'name_cz': spell_template.name_cz,
            'name_en': spell_template.name_en,
            'level': spell_template.level,
            'is_cantrip': spell_template.is_cantrip,
            'school': spell_template.school,
            'school_en': spell_template.school_en,
            'casting_time': spell_template.casting_time,
            'range': spell_template.range,
            'components': spell_template.components,
            'material': spell_template.material,
            'duration': spell_template.duration,
            'concentration': spell_template.concentration,
            'ritual': spell_template.ritual,
            'attack_type': spell_template.attack_type,
            'damage_type': spell_template.damage_type,
            'damage_dice': spell_template.damage_dice,
            'saving_throw': spell_template.saving_throw,
            'heal_dice': spell_template.heal_dice,
            'description': spell_template.description,
            'higher_levels': spell_template.higher_levels,
            'classes': spell_template.classes,
            'races': spell_template.races,
            'backgrounds': spell_template.backgrounds,
            'icon': spell_template.icon,
            'icon_url': spell_template.icon_url,
            'raw_data': spell_template.raw_data,
            'nauceno': True,
            'vybaveno': True,
        }
    )

    if not created:
        active_spell.vybaveno = not active_spell.vybaveno
        if active_spell.vybaveno:
            active_spell.nauceno = True
        active_spell.save()

    status_str = "Vybaveno" if active_spell.vybaveno else "Uloženo do knihy"
    log_info(f"Kouzlo '{spell_template.name_cz}' u postavy '{character.name}': {status_str}")

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == '1':
        return JsonResponse({
            'success': True,
            'spell_id': spell_template.id,
            'nauceno': active_spell.nauceno,
            'vybaveno': active_spell.vybaveno,
        })

    messages.success(request, f"Kouzlo {spell_template.name_cz} bylo aktualizováno ({status_str}).")
    return redirect('player_site_app:char_schopnosti_detail', char_id=character.id)


@login_required(login_url='player_site_app:index')
def char_roleplay_view(request, char_id=None):
    """4. Roleplay informace a správa backstory aktivní postavy."""
    player, character = get_player_and_character(request, char_id)
    backstories = character.char_backstories.all() if character else []

    return render(request, 'player_site_app/char_roleplay.html', {
        'player': player,
        'character': character,
        'active_character': character,
        'current_page': 'char_roleplay',
        'backstories': backstories,
    })


@login_required(login_url='player_site_app:index')
def add_char_backstory(request):
    """Přidá novou kapitolu nebo záznam do backstory postavy."""
    if request.method == 'POST':
        char_id = request.POST.get('char_id')
        player = get_object_or_404(Player, user=request.user)
        character = get_object_or_404(Char_info, id=char_id, player=player)

        title = request.POST.get('title', '').strip() or 'Kapitola příběhu'
        backstory_text = request.POST.get('backstory', '').strip()
        is_public = (request.POST.get('public') == 'on' or request.POST.get('public') == 'true')

        if not backstory_text:
            messages.error(request, "Text příběhu nesmí být prázdný.")
        else:
            CharBackstory.objects.create(
                player=player,
                character=character,
                title=title,
                backstory=backstory_text,
                public=is_public
            )
            visibility_str = "veřejný pro družinu" if is_public else "soukromý"
            messages.success(request, f"Zápis '{title}' byl úspěšně uložen jako {visibility_str}.")

        return redirect('player_site_app:char_roleplay_detail', char_id=character.id)
    return redirect('player_site_app:char_roleplay')


@login_required(login_url='player_site_app:index')
def delete_char_backstory(request, backstory_id):
    """Smaže záznam backstory postavy."""
    player = get_object_or_404(Player, user=request.user)
    backstory_obj = get_object_or_404(CharBackstory, id=backstory_id, player=player)
    char_id = backstory_obj.character.id
    title = backstory_obj.title
    backstory_obj.delete()
    messages.info(request, f"Zápis '{title}' byl smazán.")
    return redirect('player_site_app:char_roleplay_detail', char_id=char_id)


@login_required(login_url='player_site_app:index')
def toggle_public_backstory(request, backstory_id):
    """Přepne viditelnost zápisu backstory (veřejný/soukromý)."""
    player = get_object_or_404(Player, user=request.user)
    backstory_obj = get_object_or_404(CharBackstory, id=backstory_id, player=player)
    backstory_obj.public = not backstory_obj.public
    backstory_obj.save()

    status_str = "veřejný pro družinu" if backstory_obj.public else "soukromý"
    messages.info(request, f"Zápis '{backstory_obj.title}' je nyní {status_str}.")
    return redirect('player_site_app:char_roleplay_detail', char_id=backstory_obj.character.id)


@login_required(login_url='player_site_app:index')
def char_achivements_view(request, char_id=None):
    """5. Úspěchy (Achievements) aktivní postavy a hráče."""
    player, character = get_player_and_character(request, char_id)

    if character:
        achivements = Achivements_players.objects.filter(char=character).select_related('Achivement')
    else:
        achivements = Achivements_players.objects.none()

    return render(request, 'player_site_app/char_achivements.html', {
        'player': player,
        'character': character,
        'active_character': character,
        'current_page': 'char_achivements',
        'achivements': achivements,
        'achivement': achivements,
    })


@login_required(login_url='player_site_app:index')
def char_stats_detail_view(request, char_id=None):
    """6. Detail statistik aktivní postavy."""
    player, character = get_player_and_character(request, char_id)

    return render(request, 'player_site_app/char_stats_detail.html', {
        'player': player,
        'character': character,
        'active_character': character,
        'current_page': 'char_stats_detail',
    })


@login_required(login_url='player_site_app:index')
def all_chars_view(request):
    """Zobrazí přehled postav všech hráčů (družiny) s možností přechodu na detail."""
    player, active_char = get_player_and_character(request)
    all_characters = Char_info.objects.select_related('player', 'player__user').order_by('name')

    return render(request, 'player_site_app/all_chars.html', {
        'player': player,
        'character': active_char,
        'active_character': active_char,
        'characters': all_characters,
        'current_page': 'all_chars',
    })


@login_required(login_url='player_site_app:index')
def all_chars_detail_view(request, char_id):
    """
    Zobrazí detail postavy cizího hráče:
    - Informace (Jméno, rasa, povolání, atributy, achivementy).
    - VEŘEJNÉ zápisy z backstory (soukromé poznámky NIKDY).
    - Žádné finance, temná esence, inventář ani editační tlačítka.
    """
    player, active_char = get_player_and_character(request)
    target_character = get_object_or_404(Char_info.objects.select_related('player'), id=char_id)
    public_backstories = target_character.char_backstories.filter(public=True).order_by('-created_at')
    achievements = Achivements_players.objects.filter(char=target_character, current_status=True).select_related('Achivement')

    return render(request, 'player_site_app/all_chars_detail.html', {
        'player': player,
        'character': active_char,
        'active_character': active_char,
        'target_char': target_character,
        'public_backstories': public_backstories,
        'achievements': achievements,
        'current_page': 'all_chars',
    })


@login_required(login_url='player_site_app:index')
def kronika_view(request):
    """7. Kronika kampaně a dobrodružství - rozdělená na Info a Příběh."""
    player, character = get_player_and_character(request)

    info_entries = Kronika.objects.filter(odkryto_hracum=True, category='info').order_by('datum_vytvoreni')
    lore_entries = Kronika.objects.filter(odkryto_hracum=True, category='lore').order_by('datum_vytvoreni')

    return render(request, 'player_site_app/kronika.html', {
        'player': player,
        'character': character,
        'active_character': character,
        'current_page': 'kronika',
        'info_entries': info_entries,
        'lore_entries': lore_entries,
    })


@login_required(login_url='player_site_app:index')
def kronika_detail_view(request, entry_id):
    """Detail konkrétního zápisu z kroniky kampaně."""
    player, character = get_player_and_character(request)
    entry = get_object_or_404(Kronika, id=entry_id, odkryto_hracum=True)

    return render(request, 'player_site_app/kronika_detail.html', {
        'player': player,
        'character': character,
        'active_character': character,
        'entry': entry,
        'current_page': 'kronika',
    })



@login_required(login_url='player_site_app:index')
def stream_view(request):
    """9. Stream - živé vysílání / stream sekce."""
    player, character = get_player_and_character(request)

    return render(request, 'player_site_app/stream.html', {
        'player': player,
        'character': character,
        'active_character': character,
        'current_page': 'stream',
    })


@login_required(login_url='player_site_app:index')
def dungeon_shop_view(request):
    """10. Dungeon Shop - obchod oddělený na konci nabídky."""
    player, character = get_player_and_character(request)
    treasures = Esence_Items_Shop.objects.filter(category='treasures')
    owned_count = Esence_Items_Owners.objects.filter(player=player).count()
    all_owned = Esence_Items_Owners.objects.all()

    return render(request, 'player_site_app/dungeon_shop.html', {
        'player': player,
        'character': character,
        'active_character': character,
        'current_page': 'dungeon_shop',
        'treasures': treasures,
        'shop_items': treasures,
        'owned_count': owned_count,
    })


@login_required(login_url='player_site_app:index')
def dungeon_shop_inv_view(request):
    """Inventář zakoupených předmětů a truhel z Dungeon Shopu."""
    player, character = get_player_and_character(request)
    owned_records = Esence_Items_Owners.objects.filter(player=player).select_related('item').order_by('-id')

    # Seskupení podle položek pro přehledné zobrazení s počtem kusů
    grouped = {}
    for record in owned_records:
        item = record.item
        if item.id not in grouped:
            grouped[item.id] = {
                'item': item,
                'count': 1,
                'first_record': record,
            }
        else:
            grouped[item.id]['count'] += 1

    grouped_items = list(grouped.values())

    return render(request, 'player_site_app/dungeon_shop_inv.html', {
        'player': player,
        'character': character,
        'active_character': character,
        'current_page': 'dungeon_shop_inv',
        'owned_items': owned_records,
        'grouped_items': grouped_items,
        'total_owned_count': owned_records.count(),
    })


@login_required(login_url='player_site_app:index')
def esence_buy(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        player_id = request.POST.get('player_id')

        try:
            item_id = int(item_id)
            player_id = int(player_id) if player_id else request.user.player.id
            player = get_object_or_404(Player, id=player_id)

            # Bezpečnostní kontrola vlastníka
            if hasattr(request.user, 'player') and request.user.player.id != player.id and not request.user.is_staff:
                messages.error(request, 'Neoprávněná akce!')
                return redirect('player_site_app:dungeon_shop')

            this_item = get_object_or_404(Esence_Items_Shop, id=item_id)
            cost = int(this_item.cost or 0)

            # Kosmetické předměty (rámečky, pozadí) stačí vlastnit jednou
            if this_item.category in ['borders', 'backgrounds'] and Esence_Items_Owners.objects.filter(player=player, item=this_item).exists():
                messages.warning(request, f'Předmět „{this_item.name}“ už ve své sbírce vlastníš!')
                return redirect('player_site_app:dungeon_shop')

            if player.temna_esence >= cost:
                player.temna_esence -= cost
                player.save()

                Esence_Items_Owners.objects.create(
                    player=player,
                    item=this_item,
                )
                messages.success(request, f'Předmět „{this_item.name}“ byl úspěšně zakoupen!')
            else:
                messages.error(request, 'Nemáš dostatek temné esence!')
        except Exception:
            messages.error(request, 'Chybně zadané hodnoty!')

        return redirect('player_site_app:dungeon_shop')
    else:
        messages.error(request, 'Chybně zadané hodnoty!')
        return redirect('player_site_app:dungeon_shop')

    
# ==============================================================================
# DROP RATES PRO TRUHLY (Šance v procentech na zisk rarity rámečku)
# ==============================================================================
# Každá truhla obsahuje přesně JEDEN rámeček.
#
# 1. BĚŽNÁ TRUHLA (basic):
#    - Běžný rámeček (basic):          80.0 % (800 / 1000)
#    - Vzácný rámeček (rare):           17.0 % (170 / 1000)
#    - Epický rámeček (epic):            2.8 % ( 28 / 1000)
#    - Legendární rámeček (legendary):   0.2 % (  2 / 1000)
#
# 2. VZÁCNÁ TRUHLA (rare):
#    - Běžný rámeček (basic):          50.0 % (500 / 1000)
#    - Vzácný rámeček (rare):           38.0 % (380 / 1000)
#    - Epický rámeček (epic):           10.0 % (100 / 1000)
#    - Legendární rámeček (legendary):   2.0 % ( 20 / 1000)
#
# 3. EPICKÁ TRUHLA (epic):
#    - Běžný rámeček (basic):          25.0 % (250 / 1000)
#    - Vzácný rámeček (rare):           45.0 % (450 / 1000)
#    - Epický rámeček (epic):           25.0 % (250 / 1000)
#    - Legendární rámeček (legendary):   5.0 % ( 50 / 1000)
#
# 4. LEGENDÁRNÍ TRUHLA (legendary):
#    - Běžný rámeček (basic):          10.0 % (100 / 1000)
#    - Vzácný rámeček (rare):           35.0 % (350 / 1000)
#    - Epický rámeček (epic):           40.0 % (400 / 1000)
#    - Legendární rámeček (legendary):  15.0 % (150 / 1000)
# ==============================================================================

CHEST_DROP_RATES = {
    'basic': {
        'basic': 800,       # 80.0 %
        'rare': 170,        # 17.0 %
        'epic': 28,         # 2.8 %
        'legendary': 2,     # 0.2 %
    },
    'rare': {
        'basic': 500,       # 50.0 %
        'rare': 380,        # 38.0 %
        'epic': 100,        # 10.0 %
        'legendary': 20,    # 2.0 %
    },
    'epic': {
        'basic': 250,       # 25.0 %
        'rare': 450,        # 45.0 %
        'epic': 250,        # 25.0 %
        'legendary': 50,    # 5.0 %
    },
    'legendary': {
        'basic': 100,       # 10.0 %
        'rare': 350,        # 35.0 %
        'epic': 400,        # 40.0 %
        'legendary': 150,   # 15.0 %
    },
}


def get_border_from_treasure(player_id, item_id, rarity, request=None):
    """
    Vylosuje právě JEDEN rámeček z truhly na základě její rarity
    a přidá jej do vlastnictví hráče.
    """
    player = get_object_or_404(Player, id=player_id)

    # Získání vah pravděpodobnosti pro danou raritu truhly (výchozí: basic)
    weights_dict = CHEST_DROP_RATES.get(rarity, CHEST_DROP_RATES['basic'])

    # 1. Losování rarity vyhraného rámečku podle definovaných vah
    target_rarity = random.choices(
        population=list(weights_dict.keys()),
        weights=list(weights_dict.values()),
        k=1
    )[0]

    # 2. Výběr rámečků dané vylosované rarity
    pool = list(Esence_Items_Shop.objects.filter(category="borders", rarity=target_rarity))

    # Záchranný fallback: pokud pro danou raritu není žádný rámeček, vybereme ze všech existujících
    if not pool:
        pool = list(Esence_Items_Shop.objects.filter(category="borders"))

    if not pool:
        return None

    # 3. Každá truhla obsahuje pouze 1 rámeček
    won_border = random.choice(pool)

    # Uložení do inventáře hráče
    Esence_Items_Owners.objects.create(
        player=player,
        item=won_border,
    )

    return won_border


@login_required(login_url='player_site_app:index')
def use_treasure(request):
    """
    Spotřebuje 1 truhlu z inventáře hráče, vylosuje rámeček
    a vrátí výsledek (buď jako JSON pro animaci Mimica, nebo přes redirect).
    """
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        player_id = request.POST.get('player_id')
        is_ajax = (
            request.headers.get('x-requested-with') == 'XMLHttpRequest' or
            'application/json' in request.headers.get('Accept', '') or
            request.POST.get('ajax') == '1'
        )

        try:
            item_id = int(item_id)
            player_id = int(player_id) if player_id else request.user.player.id
            player = get_object_or_404(Player, id=player_id)

            # Bezpečnostní kontrola vlastníka
            if hasattr(request.user, 'player') and request.user.player.id != player.id and not request.user.is_staff:
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Neoprávněná akce!'}, status=403)
                messages.error(request, 'Neoprávněná akce!')
                return redirect('player_site_app:dungeon_shop_inv')

            # Hledáme jeden kus tohoto předmětu pro daného hráče
            treasure_owner_record = Esence_Items_Owners.objects.filter(
                player=player,
                item_id=item_id
            ).first()

            if treasure_owner_record:
                treasure_name = treasure_owner_record.item.name
                rarity = treasure_owner_record.item.rarity
                chest_image_url = treasure_owner_record.item.image.url if treasure_owner_record.item.image else ''

                won_border = get_border_from_treasure(player.id, item_id, rarity, request=request)
                treasure_owner_record.delete()

                if won_border:
                    if is_ajax:
                        return JsonResponse({
                            'success': True,
                            'chest_name': treasure_name,
                            'chest_rarity': rarity,
                            'chest_image_url': chest_image_url,
                            'border': {
                                'id': won_border.id,
                                'name': won_border.name,
                                'rarity': won_border.rarity,
                                'rarity_display': won_border.get_rarity_display(),
                                'image_url': won_border.image.url if won_border.image else '',
                                'category': won_border.category,
                                'category_display': won_border.get_category_display(),
                            }
                        })
                    messages.success(request, f'Truhla „{treasure_name}“ byla otevřena! Získal jsi rámeček: {won_border.name}.')
                else:
                    if is_ajax:
                        return JsonResponse({'success': False, 'error': 'Z truhly se nepodařilo nic vylosovat.'}, status=400)
                    messages.success(request, f'Předmět „{treasure_name}“ byl úspěšně spotřebován!')
            else:
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Předmět nebyl ve tvém inventáři nalezen!'}, status=404)
                messages.error(request, 'Předmět nebyl ve tvém inventáři nalezen!')

        except Exception:
            if is_ajax:
                return JsonResponse({'success': False, 'error': 'Chyba při použití předmětu!'}, status=500)
            messages.error(request, 'Chyba při použití předmětu!')

        return redirect('player_site_app:dungeon_shop_inv')

    return redirect('player_site_app:dungeon_shop_inv')