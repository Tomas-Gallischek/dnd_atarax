import json
import random
from functools import wraps
from django.http import JsonResponse
from django.utils import functional
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Locations, Npc, Monsters_All_db, Monsters_Active
from player_site_app.models import Player, Char_info, Logs
from player_site_app.achivements import golds_achivement


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
    all_active_mobs = Monsters_Active.objects.all()
    all_monsters = Monsters_All_db.objects.all()
    

    context = {
        'active_mobs_list': all_active_mobs,
        'all_monsters': all_monsters,

    }
    return render(request, 'dm_site_app/monster_gen_page.html', context)

@dm_required
def random_monster_gen(request):
    if request.method == 'POST':
        print("Supuštěn POST")
        mob_lvl = int(request.POST.get('mob_lvl')) # 1-30 (v databázi 0-29)
        mob_dificulty = int(request.POST.get('mob_dificulty')) # Obtížnost v rámci daného levelu

        final_dificulty = int(mob_dificulty - 3) # 1-2 = menší lvl než hráči, 3 = stejný lvl jak hráčí, 4-5 = větší lvl než hráčí
        final_lvl = float(mob_lvl + final_dificulty)
        final_lvl_min = final_lvl-0.5
        final_lvl_max=final_lvl+0.5

        if final_lvl_min <=0:
            final_lvl_min = 0
        if final_lvl_max >= 30:
            final_lvl_max = 30

# Vyhledá všechny monstra které mají CR o 0,5 menší nebo větší
        monsters = Monsters_All_db.objects.filter(challenge_rating__gte=final_lvl_min, challenge_rating__lte=final_lvl_max)
        print("Nalezeno monster: ", monsters)
        # Vybere náhodné monstrum
        if monsters:
            print("Vybral se random mob")
            random_mob = random.choice(monsters) 
            active_mob_db_save(random_mob.id)
            print("Uložil se do databáze")
            return redirect('dm_site_app:monster_gen_page') # Znova načte stránku s novým mobem
        else:
            print("Nenalezeno")
            messages.error(request, "Nenalezeno na daný level")
            return redirect('dm_site_app:monster_gen_page')
@dm_required
def specific_monster_gen(request):
    if request.method == 'POST':
        monster_id = request.POST.get('monster_id')
        print("Jdu na uložení do databáze")
        active_mob_db_save(monster_id)
        print("Uloženo do databáze")
        return redirect('dm_site_app:monster_gen_page')
    else:
        messages.error(request, "Chyba při vybirani monstra")
        return redirect('dm_site_app:monster_gen_page')
        
@dm_required
def pvp_pre(request):
    all_active_mobs = Monsters_Active.objects.all()
    all_players = Char_info.objects.all()

    return render(request, 'dm_site_app/pvp_pre.html', {
        'current_page': 'pvp_pre',
        'all_active_mobs': all_active_mobs,
        'all_players': all_players,
    })


@dm_required
def pvp_arena(request):
    all_active_mobs = Monsters_Active.objects.filter(in_fight=True)
    all_players = Char_info.objects.filter(in_fight=True)

    return render(request, 'dm_site_app/pvp_arena.html', {
        'current_page': 'pvp_arena',
        'all_active_mobs': all_active_mobs,
        'all_players': all_players,
    })


@dm_required
def api_update_hp(request):
    """
    API endpoint pro dávkový pozitivní update aktuálních životů (HP)
    pro monstra (Monsters_Active) i postavy hráčů (Char_info).
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Pouze metoda POST'}, status=405)

    try:
        data = json.loads(request.body)
        updates = data.get('updates')
        if updates is None:
            updates = [data]

        saved_records = []
        for item in updates:
            entity_type = item.get('entity_type')
            entity_id = item.get('entity_id')
            new_hp = int(item.get('current_hp'))

            if entity_type == 'mob':
                mob = Monsters_Active.objects.get(id=entity_id)
                mob.current_hp = new_hp
                mob.save(update_fields=['current_hp'])
                saved_records.append({'entity_type': 'mob', 'id': mob.id, 'current_hp': mob.current_hp})
            elif entity_type == 'player':
                player = Char_info.objects.get(id=entity_id)
                player.hit_points_current = new_hp
                player.save(update_fields=['hit_points_current'])
                saved_records.append({'entity_type': 'player', 'id': player.id, 'current_hp': player.hit_points_current})

        return JsonResponse({'success': True, 'saved': saved_records})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@dm_required
def in_fight_switch(request):
    if request.method == 'POST':
        source_id = request.POST.get('source_id') # ID
        action = request.POST.get('in_fight') # True / False
        source = request.POST.get('source') # mob/ player

        if source == "mob":
            mob = get_object_or_404(Monsters_Active, id=source_id)
            mob.in_fight = (action == 'True') # Musí být takto, jinak to python vždycky zapíše jako "True"
            mob.save()
            return redirect('dm_site_app:pvp_pre')
        elif source == "player":
            player = Char_info.objects.get(id=source_id)
            player.in_fight = (action == 'True') # Musí být takto, jinak to python vždycky zapíše jako "True"
            player.save()
            return redirect('dm_site_app:pvp_pre')
    else:
        messages.error(request, "Chyba při vybirani monstra")
        return redirect('dm_site_app:pvp_pre') 

@dm_required
def active_mob_db_save(mob_id):
    mob = Monsters_All_db.objects.get(id=mob_id)
    print("Ukládá se do databáze")
# vytvoření nové mobky v databázi:
    Monsters_Active.objects.create(
        api_index=mob.api_index,
        name_cz=mob.name_cz,
        name_en=mob.name_en,
        size=mob.size,
        monster_type=mob.monster_type,
        subtype=mob.subtype,
        alignment=mob.alignment,
        armor_class=mob.armor_class,
        armor_desc=mob.armor_desc,
        hit_points=mob.hit_points,
        current_hp=mob.hit_points,
        hit_dice=mob.hit_dice,
        speed=mob.speed,
        strength=mob.strength,
        dexterity=mob.dexterity,
        constitution=mob.constitution,
        intelligence=mob.intelligence,
        wisdom=mob.wisdom,
        charisma=mob.charisma,
        saving_throws=mob.saving_throws,
        skills=mob.skills,
        damage_vulnerabilities=mob.damage_vulnerabilities,
        damage_resistances=mob.damage_resistances,
        damage_immunities=mob.damage_immunities,
        condition_immunities=mob.condition_immunities,
        senses=mob.senses,
        languages=mob.languages,
        challenge_rating=mob.challenge_rating,
        xp=mob.xp,
        proficiency_bonus=mob.proficiency_bonus,
        special_abilities=mob.special_abilities,
        actions=mob.actions,
        legendary_actions=mob.legendary_actions,
        reactions=mob.reactions,
        description=mob.description,
        image_url=mob.image_url,
        raw_data=mob.raw_data
    )
    print("Uloženo do databáze")
    

@dm_required
def remove_mob(request, mob_id):
    Monsters_Active.objects.filter(id=mob_id).delete()
    return redirect('dm_site_app:monster_gen_page')    
    

    


    


    
    