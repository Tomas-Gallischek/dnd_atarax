from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Player, Char_info, Achivements_players, Achivements_database, Esence_Items_Shop, Esence_Items_Owners
from .forms import PlayerLoginForm, PlayerRegistrationForm
from dnd_atarax.terminal import log_player, log_warning, log_info
from dm_site_app.models import Items_Active
import random


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
    Pokud je hráč přihlášen, přesměruje ho na přehled postav.
    Pokud není přihlášen, nabídne přihlášení a registraci.
    """
    if request.user.is_authenticated:
        return redirect('player_site_app:prehled_postav')

    login_form = PlayerLoginForm()
    reg_form = PlayerRegistrationForm()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'register':
            reg_form = PlayerRegistrationForm(request.POST)
            if reg_form.is_valid():
                user = reg_form.save()
                login(request, user)
                log_player("Registrace nového hráče", f"Uživatel '{user.username}' ({user.player.nickname})")
                messages.success(request, f"Registrace proběhla úspěšně! Vítej, {user.player.nickname or user.username}.")
                return redirect('player_site_app:prehled_postav')
            else:
                log_warning("Chyba při registraci hráče", "Neplatná data ve formuláři")
                messages.error(request, "Opravte prosím chyby v registračním formuláři.")

        elif action == 'login':
            login_form = PlayerLoginForm(request, data=request.POST)
            if login_form.is_valid():
                user = login_form.get_user()
                login(request, user)
                Player.objects.get_or_create(user=user, defaults={'nickname': user.username})
                role = "DM / Staff 🛡️" if user.is_staff else "Hráč 🧙"
                log_player("Přihlášení uživatele", f"'{user.username}' [{role}]")
                messages.success(request, "Přihlášení proběhlo úspěšně. Vítej zpět!")
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                if request.user.is_staff:
                    return redirect('dm_site_app:index')
                else:
                    return redirect('player_site_app:prehled_postav')
            else:
                username_attempt = request.POST.get('username', 'neznámý')
                log_warning("Neúspěšné přihlášení", f"Neplatné jméno nebo heslo pro '{username_attempt}'")
                messages.error(request, "Neplatné uživatelské jméno nebo heslo.")

    return render(request, 'player_site_app/login_index.html', {
        'login_form': login_form,
        'reg_form': reg_form,
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
    """1. Přehled postavy - detail zvolené nebo aktivní postavy."""
    player, character = get_player_and_character(request, char_id)

    return render(request, 'player_site_app/char_over_view..html', {
        'player': player,
        'character': character,
        'active_character': character,
        'current_page': 'char_overview',
    })


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
def char_schopnosti_view(request, char_id=None):
    """3. Schopnosti a kouzla aktivní postavy."""
    player, character = get_player_and_character(request, char_id)

    return render(request, 'player_site_app/char_schopnosti.html', {
        'player': player,
        'character': character,
        'active_character': character,
        'current_page': 'char_schopnosti',
    })


@login_required(login_url='player_site_app:index')
def char_roleplay_view(request, char_id=None):
    """4. Roleplay informace aktivní postavy."""
    player, character = get_player_and_character(request, char_id)

    return render(request, 'player_site_app/char_roleplay.html', {
        'player': player,
        'character': character,
        'active_character': character,
        'current_page': 'char_roleplay',
    })


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
def kronika_view(request):
    """7. Kronika kampaně a dobrodružství."""
    player, character = get_player_and_character(request)

    return render(request, 'player_site_app/kronika.html', {
        'player': player,
        'character': character,
        'active_character': character,
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
    for i in treasures:
        i.objects.delete()

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

                won_border = get_border_from_treasure(player.id, item_id, rarity, request=request)
                treasure_owner_record.delete()

                if won_border:
                    if is_ajax:
                        return JsonResponse({
                            'success': True,
                            'chest_name': treasure_name,
                            'chest_rarity': rarity,
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