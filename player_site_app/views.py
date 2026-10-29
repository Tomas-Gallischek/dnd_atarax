from player_site_app.achivements import esencionik_ach, gambler_ach
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import (
    Player, Char_info, Achivements_players, Achivements_database,
    Esence_Items_Shop, Esence_Items_Owners, CharNotes, CharBackstory, Logs
)
from .forms import PlayerLoginForm, PlayerRegistrationForm
from dnd_atarax.terminal import log_player, log_warning, log_info
from dm_site_app.models import (
    Items_Active, OverAllSettings, Kronika, Spells_All_db, Spells_Active
)
import os
import random
import time
import re


def get_player_and_character(request, char_id=None):
    """
    Pomocná funkce pro bezpečné získání profilu hráče a aktivní postavy.
    Zaručuje striktní izolaci dat pro běžné hráče, zatímco DM má možnost spravovat i skryté či cizí postavy.
    """
    player, _ = Player.objects.get_or_create(user=request.user, defaults={'nickname': request.user.username})
    is_dm = bool(request.user.is_staff or getattr(player, 'admin', False))

    if char_id:
        if is_dm:
            character = get_object_or_404(Char_info, id=char_id)
        else:
            character = get_object_or_404(Char_info, id=char_id, player=player)
        request.session['active_char_id'] = character.id
        return player, character

    session_char_id = request.session.get('active_char_id')
    if session_char_id:
        if is_dm:
            character = Char_info.objects.filter(id=session_char_id).first()
        else:
            character = Char_info.objects.filter(id=session_char_id, player=player).first()
        if character:
            return player, character

    first_char = player.characters.first()
    if first_char:
        request.session['active_char_id'] = first_char.id
        return player, first_char

    if is_dm:
        any_char = Char_info.objects.first()
        if any_char:
            request.session['active_char_id'] = any_char.id
            return player, any_char

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

    # Načtení profilů hráčů pro rozbalovací nabídku
    players = Player.objects.all().select_related('user').order_by('nickname', 'user__username')

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
                'players': players,
                'attempts_left': attempts_left,
                'is_locked_out': False,
            })

        if is_locked_out:
            mins_left = max(1, ((lockout_until - now_ts) // 60) + 1)
            messages.error(request, f"Byl vyčerpán maximální počet pokusů (3/3). Přihlášení je zablokováno, zkuste to znovu za {mins_left} min.")
            return render(request, 'player_site_app/login_index.html', {
                'loging_active': True,
                'players': players,
                'attempts_left': 0,
                'is_locked_out': True,
                'lockout_remaining_sec': max(0, lockout_until - now_ts),
            })

        player_id = request.POST.get('player_id', '').strip()
        pin = request.POST.get('pin', '').strip()

        # Vyhledání zvoleného hráče
        selected_player = None
        if player_id:
            if player_id.isdigit():
                selected_player = Player.objects.filter(id=int(player_id)).first()
            if not selected_player:
                selected_player = Player.objects.filter(Q(nickname=player_id) | Q(user__username=player_id)).first()
        elif pin:
            # Zpětná kompatibilita pro testy / starší volání bez player_id
            matching_players = list(Player.objects.filter(pin_code=pin))
            if len(matching_players) == 1:
                selected_player = matching_players[0]
            elif not matching_players:
                # Pokud nebyl vybrán player_id a zadaný PIN neodpovídá žádnému hráči:
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
                    'players': players,
                    'attempts_left': attempts_left,
                    'is_locked_out': is_locked_out,
                    'lockout_remaining_sec': 300 if is_locked_out else 0,
                })

        if not selected_player:
            messages.error(request, "Vyberte prosím svůj profil ze seznamu dobrodruhů.")
            return render(request, 'player_site_app/login_index.html', {
                'loging_active': True,
                'players': players,
                'selected_player_id': player_id,
                'attempts_left': attempts_left,
                'is_locked_out': is_locked_out,
                'lockout_remaining_sec': 300 if is_locked_out else 0,
            })

        # Validace PINu: nesmí být prázdný
        if not pin:
            attempts_used += 1
            request.session['pin_attempts'] = attempts_used
            attempts_left = max(0, 3 - attempts_used)

            if attempts_used >= 3:
                request.session['pin_lockout_until'] = now_ts + 300
                is_locked_out = True
                log_warning("Vyčerpány pokusy o PIN", "Session překročila 3 pokusy. Lockout na 5 minut.")
                messages.error(request, "Vyčerpali jste maximální počet 3 pokusů. Přihlášení bylo zablokováno na 5 minut.")
            else:
                log_warning("Prázdný PIN", "Nebyl zadán žádný PIN kód.")
                messages.error(request, f"Zadejte prosím svůj PIN kód. Zbývající pokusy: {attempts_left} z 3.")

            return render(request, 'player_site_app/login_index.html', {
                'loging_active': True,
                'players': players,
                'selected_player_id': selected_player.id,
                'attempts_left': attempts_left,
                'is_locked_out': is_locked_out,
                'lockout_remaining_sec': 300 if is_locked_out else 0,
            })

        # Kontrola PINu pro zvoleného hráče
        if selected_player.pin_code and selected_player.pin_code == pin:
            # Úspěšné přihlášení -> reset pokusů
            request.session['pin_attempts'] = 0
            request.session['pin_lockout_until'] = 0

            # Zajištění vazby na User
            if not selected_player.user:
                selected_player.save()
            user = selected_player.user

            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            role = "DM / Staff 🛡️" if user.is_staff else "Hráč 🧙"
            log_player("Přihlášení hráče přes profil a PIN", f"'{selected_player.nickname or user.username}' [{role}]")
            messages.success(request, f"Vítej ve hře, {selected_player.nickname or user.username}!")

            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            if user.is_staff:
                return redirect('dm_site_app:index')
            return redirect('player_site_app:prehled_postav')

        else:
            # Neplatný PIN pro zvolený profil
            attempts_used += 1
            request.session['pin_attempts'] = attempts_used
            attempts_left = max(0, 3 - attempts_used)

            player_name = selected_player.nickname or (selected_player.user.username if selected_player.user else "vybraného hráče")
            if attempts_used >= 3:
                request.session['pin_lockout_until'] = now_ts + 300
                is_locked_out = True
                log_warning("Vyčerpány pokusy o PIN", f"Chybný PIN 3x za sebou pro hráče '{player_name}'. Lockout na 5 minut.")
                messages.error(request, "Nesprávný PIN. Vyčerpali jste všechny 3 pokusy. Přihlášení bylo zablokováno na 5 minut.")
            else:
                log_warning("Neúspěšné přihlášení PINem", f"Hráč: '{player_name}', zbývá pokusů: {attempts_left}")
                messages.error(request, f"Nesprávný PIN kód pro hráče {player_name}! Zbývající pokusy: {attempts_left} z 3.")

            return render(request, 'player_site_app/login_index.html', {
                'loging_active': True,
                'players': players,
                'selected_player_id': selected_player.id,
                'attempts_left': attempts_left,
                'is_locked_out': is_locked_out,
                'lockout_remaining_sec': 300 if is_locked_out else 0,
            })

    return render(request, 'player_site_app/login_index.html', {
        'loging_active': loging_active,
        'players': players,
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
    """8. Přehled postav - seznam postav patřících přihlášenému hráči (a pro DM možnost vytvářet postavy a vidět stav skrytosti)."""
    player, _ = Player.objects.get_or_create(user=request.user, defaults={'nickname': request.user.username})
    is_dm = bool(request.user.is_staff or getattr(player, 'admin', False))
    characters = player.characters.all()
    all_players = Player.objects.select_related('user').order_by('nickname', 'user__username') if is_dm else None
    all_campaign_characters = Char_info.objects.select_related('player', 'player__user').order_by('name') if is_dm else None

    return render(request, 'player_site_app/prehled_postav.html', {
        'player': player,
        'characters': characters,
        'all_campaign_characters': all_campaign_characters,
        'active_character': characters.first() if characters.exists() else None,
        'current_page': 'prehled_postav',
        'is_dm': is_dm,
        'all_players': all_players,
        'class_choices': Char_info.class_choices,
        'race_choices': Char_info.race_choices,
    })


@login_required(login_url='player_site_app:index')
def char_overview(request, char_id=None):
    """1. Přehled postavy - detail zvolené nebo aktivní postavy a její poznámky."""
    player, character = get_player_and_character(request, char_id)
    is_dm = bool(request.user.is_staff or getattr(player, 'admin', False))
    notes = character.char_notes.all() if character else []

    return render(request, 'player_site_app/char_over_view..html', {
        'player': player,
        'character': character,
        'active_character': character,
        'current_page': 'char_overview',
        'notes': notes,
        'is_dm': is_dm,
    })


@login_required(login_url='player_site_app:index')
def upload_char_avatar(request):
    """
    Změní profilový obrázek postavy (nahráním souboru, zadáním URL, nebo resetem na výchozí podle povolání).
    Podporuje jak standardní POST odeslání s přesměrováním, tak moderní AJAX požadavek.
    """
    if request.method != 'POST':
        return redirect('player_site_app:char_overview_active')

    player, _ = Player.objects.get_or_create(user=request.user, defaults={'nickname': request.user.username})
    is_dm = bool(request.user.is_staff or getattr(player, 'admin', False))

    char_id = request.POST.get('char_id')
    if char_id:
        if is_dm:
            character = get_object_or_404(Char_info, id=char_id)
        else:
            character = get_object_or_404(Char_info, id=char_id, player=player)
    else:
        _, character = get_player_and_character(request)

    is_ajax = (
        request.headers.get('x-requested-with') == 'XMLHttpRequest' or
        'application/json' in request.headers.get('Accept', '') or
        request.POST.get('ajax') == '1'
    )

    if not character:
        if is_ajax:
            return JsonResponse({'success': False, 'error': 'Nebyla nalezena žádná postava k úpravě.'}, status=404)
        messages.error(request, "Nebyla nalezena žádná postava k úpravě.")
        return redirect('player_site_app:prehled_postav')

    action = request.POST.get('action', 'upload').strip()

    try:
        if action == 'reset':
            # Reset na výchozí obrázek povolání
            character.active_icon = None
            if character.image:
                try:
                    if character.image.name and 'default_avatar' not in character.image.name:
                        character.image.delete(save=False)
                except Exception:
                    pass
                character.image = None
            character.image_url = None
            character.save()

            msg = f"Profilový obrázek postavy '{character.name}' byl resetován na výchozí obrázek povolání ({character.character_class or 'Dobrodruh'})."
            log_info(f"Hráč '{player.nickname}' resetoval profilový obrázek postavy '{character.name}' na výchozí.")

            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'action': 'reset',
                    'message': msg,
                    'char_id': character.id,
                    'profile_image_url': character.profile_image_url,
                    'has_custom_image': character.has_custom_image,
                    'default_image_url': character.default_class_image_url,
                })

            messages.success(request, msg)

        elif action == 'url':
            # Nastavení profilového obrázku z externí URL
            new_url = request.POST.get('image_url', '').strip()
            if not new_url:
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Zadejte prosím platnou URL adresu obrázku.'}, status=400)
                messages.error(request, "Zadejte prosím platnou URL adresu obrázku.")
                return redirect('player_site_app:char_overview', char_id=character.id)

            if character.image:
                try:
                    if character.image.name and 'default_avatar' not in character.image.name:
                        character.image.delete(save=False)
                except Exception:
                    pass
                character.image = None

            character.image_url = new_url
            character.active_icon = None
            character.save()

            msg = f"Profilový obrázek postavy '{character.name}' byl úspěšně nastaven z URL adresy."
            log_info(f"Hráč '{player.nickname}' změnil profilový obrázek postavy '{character.name}' z URL.")

            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'action': 'url',
                    'message': msg,
                    'char_id': character.id,
                    'profile_image_url': character.profile_image_url,
                    'has_custom_image': character.has_custom_image,
                    'default_image_url': character.default_class_image_url,
                })

            messages.success(request, msg)

        elif action == 'icon':
            # Nastavení profilového obrázku z vlastněné ikonky z Dungeon Shopu
            item_id = request.POST.get('item_id') or request.POST.get('icon_id')
            owner_rec = Esence_Items_Owners.objects.filter(
                player=player,
                item_id=item_id,
                item__category='icons'
            ).first()

            if not owner_rec:
                err_msg = "Tuto ikonku nemáš ve svém inventáři!"
                if is_ajax:
                    return JsonResponse({'success': False, 'error': err_msg}, status=400)
                messages.error(request, err_msg)
                return redirect('player_site_app:char_overview', char_id=character.id)

            if character.image:
                try:
                    if character.image.name and 'default_avatar' not in character.image.name:
                        character.image.delete(save=False)
                except Exception:
                    pass
                character.image = None

            character.image_url = None
            character.active_icon = owner_rec
            character.save()

            player.active_icon = owner_rec
            player.save()

            msg = f"Profilový obrázek postavy '{character.name}' byl nastaven na ikonku '{owner_rec.item.name}'."
            log_info(f"Hráč '{player.nickname}' nastavil profilovou ikonku '{owner_rec.item.name}' pro postavu '{character.name}'.")

            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'action': 'icon',
                    'message': msg,
                    'char_id': character.id,
                    'profile_image_url': character.profile_image_url,
                    'has_custom_image': character.has_custom_image,
                    'default_image_url': character.default_class_image_url,
                    'active_icon_name': owner_rec.item.name,
                    'active_icon_id': owner_rec.item.id,
                })

            messages.success(request, msg)

        else:
            # Nahrání souboru ze zařízení hráče
            uploaded_file = request.FILES.get('image')
            if not uploaded_file:
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Nebyl vybrán žádný soubor s obrázkem.'}, status=400)
                messages.error(request, "Nebyl vybrán žádný soubor s obrázkem.")
                return redirect('player_site_app:char_overview', char_id=character.id)

            # Kontrola velikosti (max 5 MB)
            max_size_bytes = 5 * 1024 * 1024
            if uploaded_file.size > max_size_bytes:
                err_msg = "Soubor je příliš velký. Maximální povolená velikost je 5 MB."
                if is_ajax:
                    return JsonResponse({'success': False, 'error': err_msg}, status=400)
                messages.error(request, err_msg)
                return redirect('player_site_app:char_overview', char_id=character.id)

            # Kontrola přípony
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            allowed_exts = ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg']
            if ext not in allowed_exts:
                err_msg = f"Nepodporovaný formát souboru ({ext}). Povolené jsou: JPG, PNG, WEBP, GIF, SVG."
                if is_ajax:
                    return JsonResponse({'success': False, 'error': err_msg}, status=400)
                messages.error(request, err_msg)
                return redirect('player_site_app:char_overview', char_id=character.id)

            # Smazání starého vlastního souboru
            if character.image:
                try:
                    if character.image.name and 'default_avatar' not in character.image.name:
                        character.image.delete(save=False)
                except Exception:
                    pass

            character.image = uploaded_file
            character.image_url = None
            character.active_icon = None
            character.save()

            msg = f"Profilový obrázek postavy '{character.name}' byl úspěšně nahrán."
            log_info(f"Hráč '{player.nickname}' nahrál nový profilový obrázek pro postavu '{character.name}'.")

            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'action': 'upload',
                    'message': msg,
                    'char_id': character.id,
                    'profile_image_url': character.profile_image_url,
                    'has_custom_image': character.has_custom_image,
                    'default_image_url': character.default_class_image_url,
                })

            messages.success(request, msg)

    except Exception as e:
        err = "Došlo k neočekávané chybě při ukládání obrázku."
        if is_ajax:
            return JsonResponse({'success': False, 'error': err}, status=500)
        messages.error(request, err)

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
    if next_url:
        return redirect(next_url)
    return redirect('player_site_app:char_overview', char_id=character.id)


@login_required(login_url='player_site_app:index')
def add_char_note(request):
    """Vytvoří novou soukromou poznámku k postavě."""
    if request.method == 'POST':
        char_id = request.POST.get('char_id')
        player = get_object_or_404(Player, user=request.user)
        is_dm = bool(request.user.is_staff or getattr(player, 'admin', False))
        if is_dm:
            character = get_object_or_404(Char_info, id=char_id)
        else:
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
    is_dm = bool(request.user.is_staff or getattr(player, 'admin', False))
    if is_dm:
        note_obj = get_object_or_404(CharNotes, id=note_id)
    else:
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
    is_dm = bool(request.user.is_staff or getattr(player, 'admin', False))
    if is_dm:
        note_obj = get_object_or_404(CharNotes, id=note_id)
    else:
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


@login_required(login_url='player_site_app:index')
def remove_inv_item(request, item_id):
    """
    Umožňuje hráči odebrat (zahodit) předmět z inventáře své postavy.
    Striktně ověřuje, že předmět patří postavě přihlášeného hráče (nebo má uživatel DM práva).
    """
    if request.method != 'POST':
        messages.warning(request, "Předmět lze odebrat pouze potvrzením formuláře.")
        return redirect('player_site_app:inv')

    player, _ = Player.objects.get_or_create(user=request.user, defaults={'nickname': request.user.username})
    is_dm = bool(request.user.is_staff or getattr(player, 'admin', False))

    item = get_object_or_404(Items_Active, id=item_id)
    char = item.char_own

    # Striktní kontrola vlastnictví
    if not (is_dm or (char and char.player == player)):
        log_warning(
            "Neautorizovaný pokus o smazání předmětu",
            f"Uživatel '{request.user.username}' se pokusil smazat předmět #{item.id} patřící postavě '{char.name if char else 'bez vlastníka'}'"
        )
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax'):
            return JsonResponse({'status': 'error', 'message': 'Nemáte oprávnění odebrat tento předmět.'}, status=403)
        return HttpResponseForbidden("Nemáte oprávnění odebrat předmět z cizího inventáře.")

    item_name = item.name_cz or item.name_en or f"Předmět #{item.id}"
    char_name = char.name if char else "neznámá postava"
    char_id = char.id if char else None

    item.delete()

    if char:
        Logs.objects.create(
            player=char.player,
            character=char,
            message=f"Hráč {player.nickname} zahodil předmět '{item_name}' z inventáře postavy {char_name}",
            value=0.0
        )
    log_player(f"Hráč '{player.nickname}' zahodil předmět '{item_name}' (ID: {item_id}) z inventáře postavy '{char_name}'")

    success_msg = f"Předmět '{item_name}' byl vyřazen z tvého inventáře."
    messages.success(request, success_msg)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax'):
        return JsonResponse({
            'status': 'ok',
            'deleted_id': item_id,
            'item_name': item_name,
            'message': success_msg
        })

    if char_id:
        return redirect('player_site_app:inv_detail', char_id=char_id)
    return redirect('player_site_app:inv')


def can_character_cast_cantrips(character):
    """Určí, zda má postava podle pravidel D&D 5e přístup k magickým trikům (0. úroveň)."""
    if not character:
        return False
    char_class = (character.character_class or "").lower().strip()
    lvl = max(1, character.level)

    # Plnohodnotní sesilatelé mají triky od 1. úrovně
    full_casters = [
        "kouzelník", "čaroděj", "klerik", "druid", "bard", "černokněžník",
        "wizard", "sorcerer", "cleric", "druid", "bard", "warlock"
    ]
    if any(fc in char_class for fc in full_casters):
        return True

    # Třetinoví sesilatelé (Mystický rytíř, Mystický šejdíř) mají triky od 3. úrovně
    third_casters = ["bojovník", "tulák", "fighter", "rogue"]
    if any(tc in char_class for tc in third_casters) and lvl >= 3:
        return True

    # Polo-sesilatelé (Paladin, Hraničář) v 5e SRD triky nemají.
    # Nemagická povolání (Barbar, Mnich) v 5e SRD triky nemají.
    return False


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
        # Nemagická povolání (Barbar, Mnich atd.) nemají sloty pro kouzla
        return 0


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
    can_cast_cantrips_flag = can_character_cast_cantrips(character)

    class_name = (character.character_class or "").strip()
    char_class_lower = class_name.lower()
    race_name = (character.race or "").strip()
    race_name_lower = race_name.lower()
    bg_name = (character.background or "").strip()

    is_half_caster = any(hc in char_class_lower for hc in ["paladin", "hraničář", "ranger"])
    is_third_caster = any(tc in char_class_lower for tc in ["bojovník", "tulák", "fighter", "rogue"])
    is_full_caster = any(fc in char_class_lower for fc in [
        "kouzelník", "čaroděj", "klerik", "druid", "bard", "černokněžník",
        "wizard", "sorcerer", "cleric", "druid", "bard", "warlock"
    ])

    # 1. Filtrování relevantních kouzel striktně podle pravidel D&D 5e:
    q = Q()
    has_class_spells = False

    # A) Podle povolání postavy:
    if class_name and class_name != "Ostatní":
        if is_full_caster:
            q |= Q(classes__icontains=class_name)
            has_class_spells = True
        elif is_half_caster:
            # Paladin a Hraničář mají kouzla specifická pro svou třídu
            q |= Q(classes__icontains=class_name)
            has_class_spells = True
        elif is_third_caster and character.level >= 3:
            # Mystický rytíř (Bojovník) a Mystický šejdíř (Tulák) od 3. úrovně čerpají z kouzelnického seznamu
            q |= Q(classes__icontains="Kouzelník")
            has_class_spells = True

    # B) Podle rasy (vrozená rasová kouzla/triky např. Tiefling, Elf, Gnom):
    if race_name and race_name != "Ostatní":
        q |= Q(races__icontains=race_name)

    # C) Podle zázemí:
    if bg_name and bg_name != "Ostatní":
        q |= Q(backgrounds__icontains=bg_name)

    active_spells_qs = Spells_Active.objects.filter(char_own=character)
    active_map = {sa.template_spell_id: sa for sa in active_spells_qs if sa.template_spell_id}
    active_by_index = {sa.api_index: sa for sa in active_spells_qs if sa.api_index}

    # D) Zahrnout kouzla, která již postava v DB vlastní / má přidělena od DM
    active_template_ids = [sa.template_spell_id for sa in active_spells_qs if sa.template_spell_id]
    if active_template_ids:
        q |= Q(id__in=active_template_ids)

    # Pokud postava nemá žádné magické zaměření ani rasová kouzla (např. Barbar),
    # seznam je prázdný (žádný fallback na all()!)
    if not q:
        relevant_spells = Spells_All_db.objects.none()
    else:
        relevant_spells = Spells_All_db.objects.filter(q).distinct().order_by('level', 'name_cz')

    # 2. Sestavení položek kouzel se stavem podle D&D 5e pravidel
    spell_items = []
    for sp in relevant_spells:
        active_inst = active_map.get(sp.id) or active_by_index.get(sp.api_index)
        is_learned = bool(active_inst and active_inst.nauceno)
        is_equipped = bool(active_inst and active_inst.vybaveno)

        is_trick = sp.is_trick or sp.level == 0
        is_racial = bool(race_name_lower and race_name_lower in (sp.races or "").lower())
        is_already_owned = bool(active_inst)

        # Určení, zda se postava může kouzlo naučit
        if is_trick:
            # Triky: Plnohodnotný sesilatel, nebo rasový trik, nebo již vlastněný
            can_learn = can_cast_cantrips_flag or is_racial or is_already_owned
        else:
            # Kouzla: Musí mít dostatečný max_spell_level pro danou úroveň
            can_learn = (max_spell_level > 0 and sp.level <= max_spell_level) or (is_racial and sp.level <= max(1, max_spell_level))

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
            'is_cantrip': is_trick,
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
            'icon_url': '/static/img/spells/cantrip_icon.svg' if is_trick else '/static/img/spells/spell_icon.svg',
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
        if lvl == 0:
            tier_unlocked = can_cast_cantrips_flag or any(s['can_learn'] or s['is_learned'] for s in tier_spells)
        else:
            tier_unlocked = (max_spell_level > 0 and lvl <= max_spell_level)

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

    has_spellcasting = has_class_spells or can_cast_cantrips_flag or (max_spell_level > 0) or len(spell_items) > 0

    return render(request, 'player_site_app/char_schopnosti.html', {
        'player': player,
        'character': character,
        'active_character': character,
        'current_page': 'char_schopnosti',
        'level_tiers': level_tiers,
        'spell_items': spell_items,
        'max_spell_level': max_spell_level,
        'can_cast_cantrips': can_cast_cantrips_flag,
        'has_spellcasting': has_spellcasting,
        'is_half_caster': is_half_caster,
        'is_third_caster': is_third_caster,
        'total_learned': total_learned,
        'total_equipped': total_equipped,
        'total_cantrips_learned': total_cantrips_learned,
        'total_spells_learned': total_spells_learned,
    })


@login_required(login_url='player_site_app:index')
def toggle_learn_spell(request):
    """Přepne stav 'naučeno' pro kouzlo postavy s D&D 5e validací."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Pouze POST metoda'}, status=405)

    char_id = request.POST.get('char_id')
    spell_id = request.POST.get('spell_id')
    action = request.POST.get('action', 'toggle')

    player = get_object_or_404(Player, user=request.user)
    is_dm = bool(request.user.is_staff or getattr(player, 'admin', False))
    if is_dm:
        character = get_object_or_404(Char_info, id=char_id)
    else:
        character = get_object_or_404(Char_info, id=char_id, player=player)
    spell_template = get_object_or_404(Spells_All_db, id=spell_id)

    # Validace D&D 5e pravidel:
    max_spell_level = get_max_spell_level_for_character(character)
    can_cast_cantrips_flag = can_character_cast_cantrips(character)

    char_class = (character.character_class or "").lower().strip()
    race_name = (character.race or "").strip().lower()
    spell_classes = (spell_template.classes or "").lower()
    spell_races = (spell_template.races or "").lower()

    is_class_match = bool(char_class and char_class in spell_classes)
    if not is_class_match and character.level >= 3 and any(tc in char_class for tc in ["bojovník", "tulák", "fighter", "rogue"]):
        if "kouzelník" in spell_classes or "wizard" in spell_classes:
            is_class_match = True

    is_race_match = bool(race_name and race_name in spell_races)
    existing_active = Spells_Active.objects.filter(char_own=character, template_spell=spell_template).first()

    is_trying_to_learn = (action == 'learn') or (action == 'toggle' and (not existing_active or not existing_active.nauceno))

    if is_trying_to_learn:
        # 1. Musí mít na kouzlo nárok (třída, rasa nebo již vlastněné)
        if not (is_class_match or is_race_match or existing_active):
            return JsonResponse({
                'success': False,
                'error': f'Kouzlo "{spell_template.name_cz}" není určeno pro povolání {character.character_class}.'
            }, status=403)

        # 2. Úroveň kouzla
        if spell_template.is_trick or spell_template.level == 0:
            if not can_cast_cantrips_flag and not is_race_match and not existing_active:
                return JsonResponse({
                    'success': False,
                    'error': f'Povolání {character.character_class} nemá na {character.level}. úrovni přístup k magickým trikům.'
                }, status=403)
        else:
            if spell_template.level > max_spell_level:
                return JsonResponse({
                    'success': False,
                    'error': f'Postava na {character.level}. úrovni může sesílat kouzla maximálně {max_spell_level}. úrovně (toto kouzlo je {spell_template.level}. úrovně).'
                }, status=403)

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
    """Přepne stav 'vybaveno' pro naučené kouzlo postavy s D&D validací."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Pouze POST metoda'}, status=405)

    char_id = request.POST.get('char_id')
    spell_id = request.POST.get('spell_id')

    player = get_object_or_404(Player, user=request.user)
    is_dm = bool(request.user.is_staff or getattr(player, 'admin', False))
    if is_dm:
        character = get_object_or_404(Char_info, id=char_id)
    else:
        character = get_object_or_404(Char_info, id=char_id, player=player)
    spell_template = get_object_or_404(Spells_All_db, id=spell_id)

    # Validace D&D pravidel:
    max_spell_level = get_max_spell_level_for_character(character)
    can_cast_cantrips_flag = can_character_cast_cantrips(character)
    char_class = (character.character_class or "").lower().strip()
    race_name = (character.race or "").strip().lower()
    spell_classes = (spell_template.classes or "").lower()
    spell_races = (spell_template.races or "").lower()

    is_class_match = bool(char_class and char_class in spell_classes)
    if not is_class_match and character.level >= 3 and any(tc in char_class for tc in ["bojovník", "tulák", "fighter", "rogue"]):
        if "kouzelník" in spell_classes or "wizard" in spell_classes:
            is_class_match = True

    is_race_match = bool(race_name and race_name in spell_races)
    active_spell = Spells_Active.objects.filter(char_own=character, template_spell=spell_template).first()

    if not active_spell:
        if not (is_class_match or is_race_match):
            return JsonResponse({
                'success': False,
                'error': f'Kouzlo "{spell_template.name_cz}" není určeno pro povolání {character.character_class}.'
            }, status=403)
        if (spell_template.is_trick or spell_template.level == 0) and not can_cast_cantrips_flag and not is_race_match:
            return JsonResponse({
                'success': False,
                'error': f'Povolání {character.character_class} nemá přístup k magickým trikům.'
            }, status=403)
        if spell_template.level > 0 and spell_template.level > max_spell_level:
            return JsonResponse({
                'success': False,
                'error': f'Postava nemůže sesílat kouzlo {spell_template.level}. úrovně.'
            }, status=403)

        active_spell = Spells_Active.objects.create(
            char_own=character,
            template_spell=spell_template,
            api_index=spell_template.api_index,
            name_cz=spell_template.name_cz,
            name_en=spell_template.name_en,
            level=spell_template.level,
            is_cantrip=spell_template.is_cantrip,
            school=spell_template.school,
            school_en=spell_template.school_en,
            casting_time=spell_template.casting_time,
            range=spell_template.range,
            components=spell_template.components,
            material=spell_template.material,
            duration=spell_template.duration,
            concentration=spell_template.concentration,
            ritual=spell_template.ritual,
            attack_type=spell_template.attack_type,
            damage_type=spell_template.damage_type,
            damage_dice=spell_template.damage_dice,
            saving_throw=spell_template.saving_throw,
            heal_dice=spell_template.heal_dice,
            description=spell_template.description,
            higher_levels=spell_template.higher_levels,
            classes=spell_template.classes,
            races=spell_template.races,
            backgrounds=spell_template.backgrounds,
            icon=spell_template.icon,
            icon_url=spell_template.icon_url,
            raw_data=spell_template.raw_data,
            nauceno=True,
            vybaveno=True,
        )
    else:
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
        is_dm = bool(request.user.is_staff or getattr(player, 'admin', False))
        if is_dm:
            character = get_object_or_404(Char_info, id=char_id)
        else:
            character = get_object_or_404(Char_info, id=char_id, player=player)

        title = request.POST.get('title', '').strip() or 'Kapitola příběhu'
        backstory_text = request.POST.get('backstory', '').strip()
        is_public = (request.POST.get('public') == 'on' or request.POST.get('public') == 'true')

        if not backstory_text:
            messages.error(request, "Text příběhu nesmí být prázdný.")
        else:
            CharBackstory.objects.create(
                player=character.player,
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
    is_dm = bool(request.user.is_staff or getattr(player, 'admin', False))
    if is_dm:
        backstory_obj = get_object_or_404(CharBackstory, id=backstory_id)
    else:
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
    is_dm = bool(request.user.is_staff or getattr(player, 'admin', False))
    if is_dm:
        backstory_obj = get_object_or_404(CharBackstory, id=backstory_id)
    else:
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
    """Zobrazí přehled postav všech hráčů (družiny) s možností přechodu na detail. Běžní hráči vidí POUZE veřejné postavy."""
    player, active_char = get_player_and_character(request)
    is_dm = bool(request.user.is_staff or getattr(player, 'admin', False))

    if is_dm:
        all_characters = Char_info.objects.select_related('player', 'player__user').order_by('name')
    else:
        all_characters = Char_info.objects.filter(
            Q(is_public=True) | Q(player=player)
        ).select_related('player', 'player__user').order_by('name')

    all_players = Player.objects.select_related('user').order_by('nickname', 'user__username') if is_dm else None

    return render(request, 'player_site_app/all_chars.html', {
        'player': player,
        'character': active_char,
        'active_character': active_char,
        'characters': all_characters,
        'current_page': 'all_chars',
        'is_dm': is_dm,
        'all_players': all_players,
        'class_choices': Char_info.class_choices,
        'race_choices': Char_info.race_choices,
    })


@login_required(login_url='player_site_app:index')
def all_chars_detail_view(request, char_id):
    """
    Zobrazí detail postavy cizího hráče:
    - Informace (Jméno, rasa, povolání, atributy, achivementy).
    - VEŘEJNÉ zápisy z backstory (soukromé poznámky NIKDY).
    - Žádné finance, temná esence, inventář ani editační tlačítka.
    - Pro běžné hráče: Skrytá postava (is_public=False) cizího hráče vrátí striktně 404.
    """
    player, active_char = get_player_and_character(request)
    is_dm = bool(request.user.is_staff or getattr(player, 'admin', False))

    if is_dm:
        target_character = get_object_or_404(Char_info.objects.select_related('player'), id=char_id)
    else:
        target_character = get_object_or_404(
            Char_info.objects.select_related('player'),
            Q(id=char_id) & (Q(is_public=True) | Q(player=player))
        )

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
        'is_dm': is_dm,
    })


@login_required(login_url='player_site_app:index')
def toggle_char_visibility(request):
    """
    Přepne viditelnost postavy pro ostatní hráče (veřejná / skrytá).
    Tato pravomoc je vyhrazena POUZE Dungeon Masterovi (is_staff nebo player.admin).
    Běžní hráči o existenci skrytých postav vůbec nevědí.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Pouze POST metoda.'}, status=405)

    player, _ = Player.objects.get_or_create(user=request.user, defaults={'nickname': request.user.username})
    is_dm = bool(request.user.is_staff or getattr(player, 'admin', False))
    if not is_dm:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == '1':
            return JsonResponse({'error': 'Tato akce je vyhrazena pouze pro Dungeon Mastera.'}, status=403)
        messages.error(request, "Tato akce je vyhrazena pouze pro Dungeon Mastera.")
        return redirect('player_site_app:prehled_postav')

    char_id = request.POST.get('char_id')
    char = get_object_or_404(Char_info, id=char_id)
    char.is_public = not char.is_public
    char.save(update_fields=['is_public'])

    status_str = "veřejná pro celou družinu" if char.is_public else "skrytá před ostatními hráči (tajná)"
    log_info(f"DM '{request.user.username}' změnil viditelnost postavy '{char.name}' na: {status_str}")

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == '1':
        return JsonResponse({
            'success': True,
            'char_id': char.id,
            'is_public': char.is_public,
            'status_str': status_str,
            'badge_text': '🌐 Veřejná' if char.is_public else '🕵️ Skrytá',
            'button_text': 'Skrýt před hráči' if char.is_public else 'Zveřejnit pro hráče',
            'message': f"Postava '{char.name}' je nyní {status_str}."
        })

    messages.success(request, f"Postava '{char.name}' je nyní {status_str}.")
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
    if next_url:
        return redirect(next_url)
    return redirect('player_site_app:char_overview', char_id=char.id)


@login_required(login_url='player_site_app:index')
def create_character(request):
    """
    Umožní Dungeon Masterovi vytvořit novou postavu (výchozí stav: skrytá před ostatními hráči).
    Po vytvoření postavy přesměruje přímo do jejího deníku, kde DM může upravit její statistiky, inventář, kouzla atd.
    Tato akce je striktně vyhrazena pro DM.
    """
    if request.method != 'POST':
        return redirect('player_site_app:prehled_postav')

    player, _ = Player.objects.get_or_create(user=request.user, defaults={'nickname': request.user.username})
    is_dm = bool(request.user.is_staff or getattr(player, 'admin', False))
    if not is_dm:
        messages.error(request, "Vytvářet nové postavy může pouze Dungeon Master.")
        return redirect('player_site_app:prehled_postav')

    name = request.POST.get('name', '').strip()
    if not name:
        messages.error(request, "Jméno postavy nesmí být prázdné.")
        return redirect('player_site_app:prehled_postav')

    character_class = request.POST.get('character_class', 'Ostatní').strip() or 'Ostatní'
    race = request.POST.get('race', 'Ostatní').strip() or 'Ostatní'
    try:
        level = max(1, min(20, int(request.POST.get('level', 1))))
    except (ValueError, TypeError):
        level = 1

    target_player_id = request.POST.get('player_id')
    if target_player_id:
        target_player = get_object_or_404(Player, id=target_player_id)
    else:
        target_player = player

    # Viditelnost: defaultně SKRYTÁ (is_public=False) pokud DM explicitně nezaškrtl zveřejnění
    is_public = (request.POST.get('is_public') in ['true', '1', 'on'])

    # Výchozí D&D 5e statistiky
    try:
        strength = int(request.POST.get('strength', 10))
        dexterity = int(request.POST.get('dexterity', 10))
        constitution = int(request.POST.get('constitution', 10))
        intelligence = int(request.POST.get('intelligence', 10))
        wisdom = int(request.POST.get('wisdom', 10))
        charisma = int(request.POST.get('charisma', 10))
        armor_class = int(request.POST.get('armor_class', 10 + (dexterity - 10) // 2))
        hit_points = int(request.POST.get('hit_points', 10 + (constitution - 10) // 2))
        speed = int(request.POST.get('speed', 30))
    except (ValueError, TypeError):
        strength = dexterity = constitution = intelligence = wisdom = charisma = 10
        armor_class = 10
        hit_points = 10
        speed = 30

    new_char = Char_info.objects.create(
        player=target_player,
        name=name,
        character_class=character_class,
        race=race,
        level=level,
        is_public=is_public,
        strength=strength,
        dexterity=dexterity,
        constitution=constitution,
        intelligence=intelligence,
        wisdom=wisdom,
        charisma=charisma,
        armor_class=armor_class,
        hit_points_max=max(1, hit_points),
        hit_points_current=max(1, hit_points),
        speed=speed,
    )

    request.session['active_char_id'] = new_char.id

    if is_public:
        messages.success(request, f"Postava '{new_char.name}' byla úspěšně vytvořena jako VEŘEJNÁ pro celou družinu.")
    else:
        messages.success(
            request,
            f"Postava '{new_char.name}' byla úspěšně vytvořena jako SKRYTÁ (pouze pro DM). "
            f"Ostatní hráči o ní nevědí, dokud ji neodkliknete jako veřejnou."
        )

    return redirect('player_site_app:char_overview', char_id=new_char.id)


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
    Vylosuje právě JEDEN předmět (rámeček nebo profilovou ikonku) z truhly
    na základě její rarity a přidá jej do vlastnictví hráče.
    """
    player = get_object_or_404(Player, id=player_id)

    # Získání vah pravděpodobnosti pro danou raritu truhly (výchozí: basic)
    weights_dict = CHEST_DROP_RATES.get(rarity, CHEST_DROP_RATES['basic'])

    # 1. Losování rarity vyhraného předmětu podle definovaných vah
    target_rarity = random.choices(
        population=list(weights_dict.keys()),
        weights=list(weights_dict.values()),
        k=1
    )[0]

    # 2. Výběr předmětů (rámečky i profilové ikonky) dané vylosované rarity
    pool = list(Esence_Items_Shop.objects.filter(category__in=["borders", "icons"], rarity=target_rarity))

    # Záchranný fallback: pokud pro danou raritu není žádný předmět, vybereme ze všech existujících rámečků a ikonek
    if not pool:
        pool = list(Esence_Items_Shop.objects.filter(category__in=["borders", "icons"]))

    if not pool:
        return None

    # 3. Každá truhla obsahuje právě 1 náhodný předmět (rámeček nebo ikonku)
    won_item = random.choice(pool)

    # Uložení do inventáře hráče
    Esence_Items_Owners.objects.create(
        player=player,
        item=won_item,
    )

    return won_item


# Alias pro jednotné použití v kódu
get_item_from_treasure = get_border_from_treasure


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

                # Započtení úspěchu 'Gambler' (+1 otevřená truhla)
                char_id = request.POST.get('char_id')
                target_char_id = None
                if char_id:
                    try:
                        target_char_id = int(char_id)
                    except (ValueError, TypeError):
                        pass
                if not target_char_id:
                    _, active_char = get_player_and_character(request)
                    if active_char:
                        target_char_id = active_char.id
                    elif player.characters.exists():
                        target_char_id = player.characters.first().id

                if target_char_id:
                    try:
                        gambler_ach(target_char_id, 1)
                    except Exception:
                        pass

                if won_border:
                    category_label = won_border.get_category_display()
                    item_payload = {
                        'id': won_border.id,
                        'name': won_border.name,
                        'rarity': won_border.rarity,
                        'rarity_display': won_border.get_rarity_display(),
                        'image_url': won_border.image.url if won_border.image else '',
                        'category': won_border.category,
                        'category_display': category_label,
                    }
                    if is_ajax:
                        return JsonResponse({
                            'success': True,
                            'chest_name': treasure_name,
                            'chest_rarity': rarity,
                            'chest_image_url': chest_image_url,
                            'border': item_payload,
                            'item': item_payload,
                        })
                    messages.success(request, f'Truhla „{treasure_name}“ byla otevřena! Získal jsi {category_label.lower()}: {won_border.name}.')
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

@login_required(login_url='player_site_app:index')
def reforge_tresure(request):
    """
    Rozebere vlastněný předmět hráče (POUZE předměty, které NEJSOU truhla)
    na temnou esenci podle rarity a odstraní 1 kus z inventáře hráče.
    """
    if request.method == "POST":
        item_id = request.POST.get('item_id')
        player_id = request.POST.get('player_id')
        char_id = request.POST.get('char_id')
        is_ajax = (
            request.headers.get('x-requested-with') == 'XMLHttpRequest' or
            'application/json' in request.headers.get('Accept', '') or
            request.POST.get('ajax') == '1'
        )

        try:
            player_id = int(player_id) if player_id else request.user.player.id
            player = get_object_or_404(Player, id=player_id)

            # Bezpečnostní kontrola vlastníka
            if hasattr(request.user, 'player') and request.user.player.id != player.id and not request.user.is_staff:
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Nemáš oprávnění k této akci!'}, status=403)
                messages.error(request, "Nemáš oprávnění k této akci!")
                return redirect('player_site_app:dungeon_shop_inv')

            item = get_object_or_404(Esence_Items_Shop, id=item_id)

            # Kontrola: Truhly se nesmí rozebírat
            if item.category == 'treasures':
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Truhly nelze rozebírat, pouze otevřít!'}, status=400)
                messages.error(request, "Truhly nelze rozebírat, pouze otevřít!")
                return redirect('player_site_app:dungeon_shop_inv')

            # Hledáme 1 kus vlastněného záznamu hráče
            owner_record = Esence_Items_Owners.objects.filter(
                player=player,
                item=item
            ).first()

            if not owner_record:
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Tento předmět nemáš ve svém inventáři!'}, status=404)
                messages.error(request, "Tento předmět nemáš ve svém inventáři!")
                return redirect('player_site_app:dungeon_shop_inv')

            # Zisk esence podle rarity (basic: 5, rare: 25, epic: 50, legendary: 100)
            value = getattr(item, 'dismantle_value', 0)
            if not value:
                rarity_map = {'basic': 1, 'rare': 5, 'epic': 10, 'legendary': 20}
                value = rarity_map.get(item.rarity, 0)

            # Pokud byl tento předmět aktivní rámeček hráče, ošetříme ho
            active_frame_removed = False
            if player.active_ramecek_id == owner_record.id or (player.active_ramecek and player.active_ramecek.item_id == item.id):
                another_copy = Esence_Items_Owners.objects.filter(
                    player=player,
                    item=item
                ).exclude(id=owner_record.id).first()

                if another_copy:
                    player.active_ramecek = another_copy
                else:
                    player.active_ramecek = None
                    active_frame_removed = True

            # Pokud byl tento předmět aktivní ikonka hráče či některé postavy, ošetříme ji
            active_icon_removed = False
            if player.active_icon_id == owner_record.id or (player.active_icon and player.active_icon.item_id == item.id):
                another_copy_icon = Esence_Items_Owners.objects.filter(
                    player=player,
                    item=item
                ).exclude(id=owner_record.id).first()

                if another_copy_icon:
                    player.active_icon = another_copy_icon
                else:
                    player.active_icon = None
                    active_icon_removed = True

            for p_char in player.characters.all():
                if p_char.active_icon_id == owner_record.id or (p_char.active_icon and p_char.active_icon.item_id == item.id):
                    another_char_copy = Esence_Items_Owners.objects.filter(
                        player=player,
                        item=item
                    ).exclude(id=owner_record.id).first()
                    p_char.active_icon = another_char_copy
                    p_char.save()

            # Přidání esence hráči
            if player.temna_esence is None:
                player.temna_esence = 0
            player.temna_esence += value
            player.save()

            target_char_id = None
            if char_id:
                try:
                    target_char_id = int(char_id)
                except (ValueError, TypeError):
                    pass
            if not target_char_id:
                _, active_char = get_player_and_character(request)
                if active_char:
                    target_char_id = active_char.id
                elif player.characters.exists():
                    target_char_id = player.characters.first().id

            if target_char_id:
                try:
                    esencionik_ach(target_char_id, int(value))
                except Exception:
                    pass

            # Odstranění POUZE vlastněného záznamu hráče (nikoliv položky v obchodě)
            item_name = item.name
            owner_record.delete()

            remaining_count = Esence_Items_Owners.objects.filter(player=player, item=item).count()
            total_owned_count = Esence_Items_Owners.objects.filter(player=player).count()

            msg = f"Předmět „{item_name}“ byl úspěšně rozebrán na {value} temné esence!"
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': msg,
                    'item_id': item.id,
                    'item_name': item_name,
                    'value': value,
                    'new_essence': player.temna_esence,
                    'remaining_count': remaining_count,
                    'total_owned_count': total_owned_count,
                    'active_frame_removed': active_frame_removed,
                    'active_icon_removed': active_icon_removed,
                })

            messages.success(request, msg)
            return redirect('player_site_app:dungeon_shop_inv')

        except Exception as e:
            if is_ajax:
                return JsonResponse({'success': False, 'error': 'Nastala chyba při zpracovávání vašeho požadavku.'}, status=500)
            messages.error(request, "Nastala chyba při zpracovávání vašeho požadavku.")
            return redirect('player_site_app:dungeon_shop_inv')

    return redirect('player_site_app:dungeon_shop_inv')


# Alias pro správný pravopis
reforge_treasure = reforge_tresure


@login_required(login_url='player_site_app:index')
def equip_frame(request):
    """
    Nasadí nebo sundá rámeček profilu hráče (Player.active_ramecek).
    """
    if request.method == "POST":
        item_id = request.POST.get('item_id')
        player_id = request.POST.get('player_id')
        action = request.POST.get('action', 'equip')
        is_ajax = (
            request.headers.get('x-requested-with') == 'XMLHttpRequest' or
            'application/json' in request.headers.get('Accept', '') or
            request.POST.get('ajax') == '1'
        )

        try:
            player_id = int(player_id) if player_id else request.user.player.id
            player = get_object_or_404(Player, id=player_id)

            if hasattr(request.user, 'player') and request.user.player.id != player.id and not request.user.is_staff:
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Nemáš oprávnění k této akci!'}, status=403)
                messages.error(request, 'Nemáš oprávnění k této akci!')
                return redirect('player_site_app:dungeon_shop_inv')

            if action == 'unequip':
                player.active_ramecek = None
                player.save()
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'action': 'unequip',
                        'message': 'Rámeček byl úspěšně sundán z profilu.',
                        'active_item_id': None,
                        'active_frame_url': None,
                    })
                messages.success(request, 'Rámeček byl úspěšně sundán z profilu.')
                return redirect('player_site_app:dungeon_shop_inv')

            # Akce nasazení rámečku
            item = get_object_or_404(Esence_Items_Shop, id=item_id)
            if item.category != 'borders':
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Pouze rámečky lze nasadit na profil!'}, status=400)
                messages.error(request, 'Pouze rámečky lze nasadit na profil!')
                return redirect('player_site_app:dungeon_shop_inv')

            owner_record = Esence_Items_Owners.objects.filter(
                player=player,
                item=item
            ).first()

            if not owner_record:
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Tento rámeček nemáš ve svém inventáři!'}, status=404)
                messages.error(request, 'Tento rámeček nemáš ve svém inventáři!')
                return redirect('player_site_app:dungeon_shop_inv')

            player.active_ramecek = owner_record
            player.save()

            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'action': 'equip',
                    'message': f"Rámeček „{owner_record.item.name}“ byl úspěšně nasazen!",
                    'active_item_id': owner_record.item.id,
                    'active_frame_url': player.active_frame_url,
                })

            messages.success(request, f"Rámeček „{owner_record.item.name}“ byl úspěšně nasazen!")
            return redirect('player_site_app:dungeon_shop_inv')

        except Exception as e:
            if is_ajax:
                return JsonResponse({'success': False, 'error': 'Nastala chyba při zpracování rámečku.'}, status=500)
            messages.error(request, 'Nastala chyba při zpracování rámečku.')
            return redirect('player_site_app:dungeon_shop_inv')

    return redirect('player_site_app:dungeon_shop_inv')


@login_required(login_url='player_site_app:index')
def equip_icon(request):
    """
    Nasadí nebo sundá profilovou ikonku hráče a postavy (Player.active_icon a Char_info.active_icon).
    """
    if request.method == "POST":
        item_id = request.POST.get('item_id')
        player_id = request.POST.get('player_id')
        char_id = request.POST.get('char_id')
        action = request.POST.get('action', 'equip')
        is_ajax = (
            request.headers.get('x-requested-with') == 'XMLHttpRequest' or
            'application/json' in request.headers.get('Accept', '') or
            request.POST.get('ajax') == '1'
        )

        try:
            player_id = int(player_id) if player_id else request.user.player.id
            player = get_object_or_404(Player, id=player_id)

            if hasattr(request.user, 'player') and request.user.player.id != player.id and not request.user.is_staff:
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Nemáš oprávnění k této akci!'}, status=403)
                messages.error(request, 'Nemáš oprávnění k této akci!')
                return redirect('player_site_app:dungeon_shop_inv')

            target_character = None
            if char_id:
                try:
                    target_character = Char_info.objects.filter(id=int(char_id), player=player).first()
                except (ValueError, TypeError):
                    pass
            if not target_character:
                _, active_char = get_player_and_character(request)
                if active_char and active_char.player_id == player.id:
                    target_character = active_char
                elif player.characters.exists():
                    target_character = player.characters.first()

            if action == 'unequip':
                player.active_icon = None
                player.save()
                if target_character:
                    target_character.active_icon = None
                    target_character.save()
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'action': 'unequip',
                        'message': 'Ikonka byla úspěšně sundána z profilu.',
                        'active_item_id': None,
                        'active_icon_url': None,
                    })
                messages.success(request, 'Ikonka byla úspěšně sundána z profilu.')
                return redirect('player_site_app:dungeon_shop_inv')

            # Akce nasazení ikonky
            item = get_object_or_404(Esence_Items_Shop, id=item_id)
            if item.category != 'icons':
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Pouze ikonky lze nasadit jako profilový obrázek!'}, status=400)
                messages.error(request, 'Pouze ikonky lze nasadit jako profilový obrázek!')
                return redirect('player_site_app:dungeon_shop_inv')

            owner_record = Esence_Items_Owners.objects.filter(
                player=player,
                item=item
            ).first()

            if not owner_record:
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Tuto ikonku nemáš ve svém inventáři!'}, status=404)
                messages.error(request, 'Tuto ikonku nemáš ve svém inventáři!')
                return redirect('player_site_app:dungeon_shop_inv')

            player.active_icon = owner_record
            player.save()

            if target_character:
                target_character.active_icon = owner_record
                target_character.image_url = None
                target_character.save()

            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'action': 'equip',
                    'message': f"Ikonka „{owner_record.item.name}“ byla úspěšně nasazena!",
                    'active_item_id': owner_record.item.id,
                    'active_icon_url': player.active_icon_url,
                })

            messages.success(request, f"Ikonka „{owner_record.item.name}“ byla úspěšně nasazena!")
            return redirect('player_site_app:dungeon_shop_inv')

        except Exception as e:
            if is_ajax:
                return JsonResponse({'success': False, 'error': 'Nastala chyba při zpracování ikonky.'}, status=500)
            messages.error(request, 'Nastala chyba při zpracování ikonky.')
            return redirect('player_site_app:dungeon_shop_inv')

    return redirect('player_site_app:dungeon_shop_inv')


@login_required(login_url='player_site_app:index')
def nastaveni_view(request):
    """
    Záložka Nastavení pro hráče:
    1) Změna profilové ikonky (výběr z vlastněných ikonek, nahrání vlastní fotky, reset na defaultní ikonku)
    2) Změna profilového rámečku (výběr z vlastněných rámečků, odebrání rámečku úplně)
    3) Změna přihlašovacího PIN kódu (neomezené množství znaků)
    4) Změna přihlašovacího jména
    """
    player, _ = Player.objects.get_or_create(user=request.user, defaults={'nickname': request.user.username})

    # Podpora volby postavy pro hráče s více postavami
    char_id = request.GET.get('char_id') or request.POST.get('char_id')
    if char_id:
        try:
            char_id_int = int(char_id)
            if request.user.is_staff or getattr(player, 'admin', False):
                character = Char_info.objects.filter(id=char_id_int).first()
            else:
                character = Char_info.objects.filter(id=char_id_int, player=player).first()
            if character:
                request.session['active_char_id'] = character.id
        except (ValueError, TypeError):
            character = None
    else:
        _, character = get_player_and_character(request)

    is_ajax = (
        request.headers.get('x-requested-with') == 'XMLHttpRequest' or
        'application/json' in request.headers.get('Accept', '') or
        request.POST.get('ajax') == '1'
    )

    if request.method == 'POST':
        action = request.POST.get('action', '').strip()

        # ---------------------------------------------------------
        # 1. ZMĚNA PROFILOVÉ IKONKY POSTAVY
        # ---------------------------------------------------------
        if action == 'change_icon':
            icon_type = request.POST.get('icon_type', '').strip()

            if not character:
                err = "Nebyla nalezena žádná postava k úpravě profilové ikonky."
                if is_ajax:
                    return JsonResponse({'success': False, 'error': err}, status=404)
                messages.error(request, err)
                return redirect('player_site_app:nastaveni')

            if icon_type == 'owned_icon':
                # Výběr z vlastněných ikonek z Dungeon Shopu
                item_id = request.POST.get('item_id')
                owner_rec = Esence_Items_Owners.objects.filter(
                    player=player,
                    item_id=item_id,
                    item__category='icons'
                ).first()

                if not owner_rec:
                    err = "Tuto profilovou ikonku nemáte ve svém inventáři."
                    if is_ajax:
                        return JsonResponse({'success': False, 'error': err}, status=400)
                    messages.error(request, err)
                    return redirect('player_site_app:nastaveni')

                # Smazání starého vlastního souboru
                if character.image:
                    try:
                        if character.image.name and 'default_avatar' not in character.image.name:
                            character.image.delete(save=False)
                    except Exception:
                        pass
                    character.image = None

                character.image_url = None
                character.active_icon = owner_rec
                character.save()

                player.active_icon = owner_rec
                player.save()

                msg = f"Profilová ikonka postavy „{character.name}“ byla nastavena na „{owner_rec.item.name}“."
                log_info(f"Hráč '{player.nickname}' nastavil ikonku '{owner_rec.item.name}' pro postavu '{character.name}'.")

                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': msg,
                        'profile_image_url': character.profile_image_url,
                        'active_icon_id': owner_rec.item.id,
                        'active_icon_name': owner_rec.item.name,
                    })
                messages.success(request, msg)
                return redirect('player_site_app:nastaveni')

            elif icon_type == 'upload':
                # Nahrání vlastní fotky
                uploaded_file = request.FILES.get('image')
                if not uploaded_file:
                    err = "Vyberte prosím soubor s fotkou k nahrání."
                    if is_ajax:
                        return JsonResponse({'success': False, 'error': err}, status=400)
                    messages.error(request, err)
                    return redirect('player_site_app:nastaveni')

                # Kontrola velikosti (max 5 MB)
                if uploaded_file.size > 5 * 1024 * 1024:
                    err = "Soubor je příliš velký. Maximální povolená velikost je 5 MB."
                    if is_ajax:
                        return JsonResponse({'success': False, 'error': err}, status=400)
                    messages.error(request, err)
                    return redirect('player_site_app:nastaveni')

                # Kontrola formátu
                ext = os.path.splitext(uploaded_file.name)[1].lower()
                if ext not in ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg']:
                    err = f"Nepodporovaný formát souboru ({ext}). Povolené jsou: JPG, PNG, WEBP, GIF, SVG."
                    if is_ajax:
                        return JsonResponse({'success': False, 'error': err}, status=400)
                    messages.error(request, err)
                    return redirect('player_site_app:nastaveni')

                # Smazání starého vlastního souboru
                if character.image:
                    try:
                        if character.image.name and 'default_avatar' not in character.image.name:
                            character.image.delete(save=False)
                    except Exception:
                        pass

                character.image = uploaded_file
                character.active_icon = None
                character.image_url = None
                character.save()

                player.active_icon = None
                player.save()

                msg = f"Vlastní profilová fotka postavy „{character.name}“ byla úspěšně nahrána a uložena."
                log_info(f"Hráč '{player.nickname}' nahrál vlastní profilovou fotku pro postavu '{character.name}'.")

                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': msg,
                        'profile_image_url': character.profile_image_url,
                    })
                messages.success(request, msg)
                return redirect('player_site_app:nastaveni')

            elif icon_type == 'reset':
                # Reset na defaultní ikonku povolání
                if character.image:
                    try:
                        if character.image.name and 'default_avatar' not in character.image.name:
                            character.image.delete(save=False)
                    except Exception:
                        pass
                    character.image = None

                character.image_url = None
                character.active_icon = None
                character.save()

                player.active_icon = None
                player.save()

                msg = f"Profilová ikonka byla resetována na výchozí symbol povolání ({character.character_class or 'Dobrodruh'})."
                log_info(f"Hráč '{player.nickname}' resetoval ikonku postavy '{character.name}' na výchozí.")

                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': msg,
                        'profile_image_url': character.profile_image_url,
                    })
                messages.success(request, msg)
                return redirect('player_site_app:nastaveni')

            else:
                err = "Neplatný typ úpravy profilové ikonky."
                if is_ajax:
                    return JsonResponse({'success': False, 'error': err}, status=400)
                messages.error(request, err)
                return redirect('player_site_app:nastaveni')

        # ---------------------------------------------------------
        # 2. ZMĚNA PROFILOVÉHO RÁMEČKU HRÁČE
        # ---------------------------------------------------------
        elif action == 'change_frame':
            frame_action = request.POST.get('frame_action', '').strip()

            if frame_action == 'remove':
                # Odebrání rámečku úplně
                player.active_ramecek = None
                player.save()

                msg = "Profilový rámeček byl úspěšně odebrán z profilu."
                log_info(f"Hráč '{player.nickname}' odebral profilový rámeček.")

                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': msg,
                        'active_frame_url': None,
                    })
                messages.success(request, msg)
                return redirect('player_site_app:nastaveni')

            elif frame_action == 'equip':
                # Výběr z vlastněných rámečků
                item_id = request.POST.get('item_id')
                owner_rec = Esence_Items_Owners.objects.filter(
                    player=player,
                    item_id=item_id,
                    item__category='borders'
                ).first()

                if not owner_rec:
                    err = "Tento profilový rámeček nemáte ve svém inventáři."
                    if is_ajax:
                        return JsonResponse({'success': False, 'error': err}, status=400)
                    messages.error(request, err)
                    return redirect('player_site_app:nastaveni')

                player.active_ramecek = owner_rec
                player.save()

                msg = f"Profilový rámeček „{owner_rec.item.name}“ byl úspěšně nasazen."
                log_info(f"Hráč '{player.nickname}' nasadil rámeček '{owner_rec.item.name}'.")

                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': msg,
                        'active_frame_url': player.active_frame_url,
                        'active_frame_id': owner_rec.item.id,
                    })
                messages.success(request, msg)
                return redirect('player_site_app:nastaveni')

            else:
                err = "Neplatná akce pro profilový rámeček."
                if is_ajax:
                    return JsonResponse({'success': False, 'error': err}, status=400)
                messages.error(request, err)
                return redirect('player_site_app:nastaveni')

        # ---------------------------------------------------------
        # 3. ZMĚNA PŘIHLAŠOVACÍHO PIN KÓDU (neomezené množství znaků)
        # ---------------------------------------------------------
        elif action == 'change_pin':
            new_pin = request.POST.get('new_pin', '').strip()
            confirm_pin = request.POST.get('confirm_pin', '').strip()

            if not new_pin:
                err = "PIN kód nesmí být prázdný. Zadejte prosím nový PIN kód."
                if is_ajax:
                    return JsonResponse({'success': False, 'error': err}, status=400)
                messages.error(request, err)
                return redirect('player_site_app:nastaveni')

            if new_pin != confirm_pin:
                err = "Zadané PIN kódy se neshodují. Zkontrolujte prosím zadání a opakujte."
                if is_ajax:
                    return JsonResponse({'success': False, 'error': err}, status=400)
                messages.error(request, err)
                return redirect('player_site_app:nastaveni')

            player.pin_code = new_pin
            player.save()

            log_player("Změna PIN kódu", f"Hráč '{player.nickname}' si úspěšně změnil přihlašovací PIN kód.")
            msg = "Přihlašovací PIN kód byl úspěšně změněn."

            if is_ajax:
                return JsonResponse({'success': True, 'message': msg})
            messages.success(request, msg)
            return redirect('player_site_app:nastaveni')

        # ---------------------------------------------------------
        # 4. ZMĚNA PŘIHLAŠOVACÍHO JMÉNA
        # ---------------------------------------------------------
        elif action == 'change_username':
            new_username = request.POST.get('new_username', '').strip()

            if not new_username:
                err = "Přihlašovací jméno nesmí být prázdné."
                if is_ajax:
                    return JsonResponse({'success': False, 'error': err}, status=400)
                messages.error(request, err)
                return redirect('player_site_app:nastaveni')

            # Kontrola kolize s jiným hráčem (nickname nebo User.username)
            nickname_collision = Player.objects.filter(nickname__iexact=new_username).exclude(id=player.id).exists()
            user_collision = User.objects.filter(username__iexact=new_username).exclude(id=player.user.id).exists()

            if nickname_collision or user_collision:
                err = f"Přihlašovací jméno „{new_username}“ je již obsazené jiným hráčem. Zvolte prosím jiné."
                if is_ajax:
                    return JsonResponse({'success': False, 'error': err}, status=400)
                messages.error(request, err)
                return redirect('player_site_app:nastaveni')

            old_name = player.nickname or (player.user.username if player.user else "hrac")
            player.nickname = new_username

            # Synchronizace User.username pokud je validní pro Django User
            clean_username = re.sub(r'[^\w.@+-]', '_', new_username) or "hrac"
            if not User.objects.filter(username__iexact=clean_username).exclude(id=player.user.id).exists():
                player.user.username = clean_username
                player.user.save()

            player.save()

            log_player("Změna přihlašovacího jména", f"Hráč změnil přihlašovací jméno z '{old_name}' na '{new_username}'.")
            msg = f"Přihlašovací jméno bylo úspěšně změněno na „{new_username}“."

            if is_ajax:
                return JsonResponse({'success': True, 'message': msg, 'new_username': new_username})
            messages.success(request, msg)
            return redirect('player_site_app:nastaveni')

        else:
            err = "Neznámá akce nastavení."
            if is_ajax:
                return JsonResponse({'success': False, 'error': err}, status=400)
            messages.error(request, err)
            return redirect('player_site_app:nastaveni')

    # GET požadavek: zobrazení nastavení
    owned_icons = player.owned_avatar_icons
    owned_frames = player.owned_frames
    player_characters = player.characters.all() if player else []

    return render(request, 'player_site_app/nastaveni.html', {
        'current_page': 'nastaveni',
        'player': player,
        'character': character,
        'characters': player_characters,
        'owned_icons': owned_icons,
        'owned_frames': owned_frames,
        'active_frame': player.active_ramecek,
    })


