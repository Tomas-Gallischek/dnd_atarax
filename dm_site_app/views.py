from dm_site_app.models import Monsters_All_db
from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Locations, Npc
from player_site_app.models import Player, Char_info, Logs
from player_site_app.achivements import golds_achivement
import random


def dm_required(view_func):
    """
    Dekorátor pro DM sekci.
    Kontroluje:
    1) Zda je uživatel přihlášený (request.user.is_authenticated)
    2) Zda má administrátorská / staff práva (request.user.is_staff=True)
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # 1. Kontrola přihlášení
        if not request.user.is_authenticated:
            return redirect('player_site_app:index')

        # 2. Kontrola administrátorských práv
        if not request.user.is_staff:
            messages.error(request, "Pro přístup do DM sekce musíte mít administrátorská práva (is_staff).")
            return redirect('player_site_app:prehled_postav')

        return view_func(request, *args, **kwargs)
    return _wrapped_view


@dm_required
def index(request):
    """1. DM Dashboard"""
    return render(request, 'dm_site_app/index_dashboard.html', {
        'current_page': 'index_dashboard',
    })


@dm_required
def tools(request):
    """2. Nástroje DM"""
    return render(request, 'dm_site_app/tools.html', {
        'current_page': 'tools',
    })


@dm_required
def npc(request):
    """3. Seznam NPC"""
    all_npcs = Npc.objects.all()
    context = {
        'npcs': all_npcs,
        'current_page': 'npc',
    }
    return render(request, 'dm_site_app/npc.html', context)


# Zpětná kompatibilita pro název funkce npcs
npcs = npc


@dm_required
def locations(request):
    """4. Mapy a lokace"""
    all_locations = Locations.objects.all()
    context = {
        'locations': all_locations,
        'current_page': 'locations',
    }
    return render(request, 'dm_site_app/locations.html', context)


@dm_required
def notes(request):
    """5. Poznámky DM"""
    return render(request, 'dm_site_app/notes.html', {
        'current_page': 'notes',
    })


@dm_required
def lore(request):
    """6. Lore s možností sdílet hráčům"""
    return render(request, 'dm_site_app/lore.html', {
        'current_page': 'lore',
    })


@dm_required
def golds_management(request):
    """Správa zlaťáků postav"""
    all_chars = Char_info.objects.all()
    context = {
        'all_chars': all_chars,
        'current_page': 'golds_management',
    }
    return render(request, 'dm_site_app/golds_management.html', context)


@dm_required
def add_gold(request):
    """Přidání/odebrání zlaťáků postavě"""
    if request.method == 'POST':
        char_id = request.POST.get('char_id')
        gold = request.POST.get('gold')
        silver = request.POST.get('silver')
        action = request.POST.get('action')
        plus_total_golds = round(float(gold or 0) + (float(silver or 0) / 10), 1)

        # Zapsání goldů
        if char_id:
            char = get_object_or_404(Char_info, id=char_id)
            if action == 'plus':
                char.gold += int(gold or 0)
                char.silver += int(silver or 0)
                char.total_golds += plus_total_golds
                golds_achivement(char_id, plus_total_golds)  # kontrola achievementu
            elif action == 'minus':
                char.gold -= int(gold or 0)
                char.silver -= int(silver or 0)
            else:
                return redirect('dm_site_app:golds-management')

            char.save()

            # Zapsání do logu
            log = Logs(
                player=char.player,
                character=char,
                message=f"Přidáno: {gold} zlaťáků a {silver} stříbrňáků",
                value=plus_total_golds
            )
            log.save()

    return redirect('dm_site_app:golds-management')


@dm_required
def monster_gen_page(request):

    context = {
        'current_page': 'monster_gen',
    }

    return render(request, 'dm_site_app/monster_gen_page.html', context)

@dm_required
def random_monster_gen(request):
    if request == 'POST':
        mob_lvl = int(request.POST.get('mob_lvl')) # 1-30 (v databázi 0-29)
        mob_dificulty = int(request.POST.get('mob_dificulty')) # Obtížnost v rámci daného levelu

        final_dificulty = int(mob_dificulty - 3) # 1-2 = menší lvl než hráči, 3 = stejný lvl jak hráčí, 4-5 = větší lvl než hráčí
        final_lvl = float(mob_lvl + final_dificulty)

        if final_lvl >= 0:
            final_lvl = 1
        elif final_lvl >= 30:
            final_lvl = 30

# Vyhledá všechny monstra které mají CR o 0,5 menší nebo větší
        monsters = Monsters_All_db.objects.filter(challenge_rating__gte=final_lvl-0.5, challenge_rating__lte=final_lvl+0.5)
        
        # Vybere náhodné monstrum
        random_mob = random.choice(monsters)

        print(f"TEST: MOB LEVEL: {final_lvl}")
        print(f"TEST: MOB LISTA: {monsters}")
        print(f"TEST: MOB: {random_mob}")

        context = {
            'random_mob': random_mob,
        }
        
        return redirect('dm_site_app:monster_gen_page', context)


    else:
        print("TEST: NEJSEM POST")
        return redirect('dm_site_app:monster_gen_page')
    


    
    