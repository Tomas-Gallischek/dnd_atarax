import json
import random
from functools import wraps
from django.http import JsonResponse
from django.utils import functional
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Locations, Npc, Monsters_All_db, Monsters_Active
from player_site_app.models import Player, Char_info, Logs
from player_site_app.achivements import zbohatlik_ach, smrtici_stroj_ach
from dnd_atarax.terminal import (
    log_dm, log_arena, log_hp, log_mob, log_player,
    log_gold, log_success, log_warning, log_error, log_info
)
from .loot import loot_gold, loot_items, loot_temna_esence

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
            log_warning("Neautorizovaný přístup do DM sekce", f"Nepřihlášený požadavek na '{request.path}'")
            return redirect('player_site_app:index')

        # 2. Kontrola administrátorských práv
        if not request.user.is_staff:
            log_warning("Nedostatečná oprávnění", f"Uživatel '{request.user.username}' nemá staff práva pro '{request.path}'")
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
                zbohatlik_ach(char_id, plus_total_golds)  # kontrola achievementu
                log_gold(f"+{gold or 0} gp, +{silver or 0} sp", f"Postava: {char.name} (Hráč: {char.player.nickname}) -> Nový stav: {char.gold} gp, {char.silver} sp")
            elif action == 'minus':
                char.gold -= int(gold or 0)
                char.silver -= int(silver or 0)
                log_gold(f"-{gold or 0} gp, -{silver or 0} sp", f"Postava: {char.name} (Hráč: {char.player.nickname}) -> Nový stav: {char.gold} gp, {char.silver} sp")
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
        mob_lvl = int(request.POST.get('mob_lvl')) # 1-30 (v databázi 0-29)
        mob_dificulty = int(request.POST.get('mob_dificulty')) # Obtížnost v rámci daného levelu

        final_dificulty = int(mob_dificulty - 3) # 1-2 = menší lvl než hráči, 3 = stejný lvl jak hráčí, 4-5 = větší lvl než hráčí
        final_lvl = float(mob_lvl + final_dificulty)
        final_lvl_min = max(0.0, final_lvl - 0.5)
        final_lvl_max = min(30.0, final_lvl + 0.5)

        # Vyhledá všechny monstra které mají CR v daném rozsahu
        monsters = Monsters_All_db.objects.filter(challenge_rating__gte=final_lvl_min, challenge_rating__lte=final_lvl_max)
        count = monsters.count()

        # Vybere náhodné monstrum
        if count > 0:
            random_mob = random.choice(monsters)
            active_mob = active_mob_db_save(random_mob.id)
            log_mob("Náhodný výběr monstra", f"CR {final_lvl_min}–{final_lvl_max} (nalezeno {count}x) -> Vybrán: {random_mob.name_cz or random_mob.name_en} (CR {random_mob.formatted_cr})")
            return redirect('dm_site_app:monster_gen_page') # Znova načte stránku s novým mobem
        else:
            log_warning("Náhodný výběr monstra", f"Žádné monstrum v databázi pro CR {final_lvl_min}–{final_lvl_max}")
            messages.error(request, "Nenalezeno na daný level")
            return redirect('dm_site_app:monster_gen_page')

@dm_required
def specific_monster_gen(request):
    if request.method == 'POST':
        monster_id = request.POST.get('monster_id')
        active_mob = active_mob_db_save(monster_id)
        if active_mob:
            log_mob("Výběr konkrétního monstra", f"Přidán: {active_mob.name_cz or active_mob.name_en} (CR {active_mob.formatted_cr})")
        return redirect('dm_site_app:monster_gen_page')
    else:
        log_warning("Výběr specifického monstra", "Neplatná metoda (očekáván POST)")
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
    log_arena("Načtena aréna", f"{all_active_mobs.count()} monster vs {all_players.count()} hráčů v boji")

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
                old_hp = mob.current_hp
                mob.current_hp = new_hp
                mob.save(update_fields=['current_hp'])
                saved_records.append({'entity_type': 'mob', 'id': mob.id, 'current_hp': mob.current_hp})
                log_hp("Změna HP monstra", f"{mob.name_cz or mob.name_en}: {old_hp} -> {new_hp}/{mob.hit_points} HP")
            elif entity_type == 'player':
                player = Char_info.objects.get(id=entity_id)
                old_hp = player.hit_points_current
                player.hit_points_current = new_hp
                player.save(update_fields=['hit_points_current'])
                saved_records.append({'entity_type': 'player', 'id': player.id, 'current_hp': player.hit_points_current})
                log_hp("Změna HP hráče", f"{player.name}: {old_hp} -> {new_hp}/{player.hit_points_max} HP")

        return JsonResponse({'success': True, 'saved': saved_records})
    except Exception as e:
        log_error("Chyba při aktualizaci HP", str(e))
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
            action_desc = "VSTUPUJE DO BOJE ⚔️" if mob.in_fight else "ODCHÁZÍ Z BOJE 🏳️"
            log_arena(f"Monstrum: {action_desc}", f"{mob.name_cz or mob.name_en} [ID: {mob.id}]")
            return redirect('dm_site_app:pvp_pre')
        elif source == "player":
            player = Char_info.objects.get(id=source_id)
            player.in_fight = (action == 'True') # Musí být takto, jinak to python vždycky zapíše jako "True"
            player.save()
            action_desc = "VSTUPUJE DO BOJE ⚔️" if player.in_fight else "ODCHÁZÍ Z BOJE 🏳️"
            log_arena(f"Hráč: {action_desc}", f"{player.name} (Hráč: {player.player.nickname}) [ID: {player.id}]")
            return redirect('dm_site_app:pvp_pre')
    else:
        log_warning("Přepnutí stavu v boji", "Neplatná metoda požadavku (očekáván POST)")
        messages.error(request, "Chyba při vybirani monstra")
        return redirect('dm_site_app:pvp_pre') 

def active_mob_db_save(mob_id):
    mob = Monsters_All_db.objects.get(id=mob_id)

    if mob.monster_type == 'humanoid' or mob.monster_type == 'Humanoid':
        gold_base = 2
        silver_base = 6
        chance = 80
    elif mob.monster_type == 'undead' or mob.monster_type == 'Undead':
        gold_base = 2
        silver_base = 2
        chance = 10
    elif mob.monster_type == 'monstrosity' or mob.monster_type == 'Monstrosity':
        gold_base = 2
        silver_base = 2
        chance = 10
    else:
        gold_base = 0
        silver_base = 0
        chance = 0
        plus_gold = 0
        plus_silver = 0
        loot_able_switch = False

# spustí se jen pokud může mít mobka u sebe goldy
    print("--- GENERACE ZLATA U MONSTER --- ")
    print(f"Šance: {chance}%")
    print(f"Gold base: {gold_base}")
    print(f"Silver base: {silver_base}")
    if chance > 0:
        random_multi = int(round(mob.challenge_rating))
        if random_multi < 2:
            random_multi = 2
        random_bonus = random.uniform(1, random_multi)
        
        actual_gold = random.randint(1,gold_base)
        actual_silver = random.randint(1,silver_base)

        plus_gold = int(round(actual_gold * random_bonus))
        plus_silver = int(round(actual_silver * random_bonus))
        loot_able_switch = True

        while plus_silver >= 10:
            plus_gold += 1
            plus_silver -= 10

    # vytvoření nové mobky v aktivní databázi:
    new_mob = Monsters_Active.objects.create(
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
        raw_data=mob.raw_data,
        loot_gold=plus_gold,
        loot_silver=plus_silver,
        loot_able=loot_able_switch, 
    )
    log_success("Monstrum připraveno do hry", f"{new_mob.name_cz or new_mob.name_en} (CR {new_mob.formatted_cr}, {new_mob.hit_points} HP, AC {new_mob.armor_class}) [ID: {new_mob.id}]")
    return new_mob

@dm_required
def remove_mob(request, mob_id):
    mob = Monsters_Active.objects.filter(id=mob_id).first()
    if mob:
        name = mob.name_cz or mob.name_en
        mob.delete()
        log_mob("Monstrum odstraněno ze hry", f"{name} [ID: {mob_id}]")
    else:
        log_warning("Pokus o smazání neexistujícího monstra", f"ID: {mob_id}")
    return redirect('dm_site_app:monster_gen_page')

@dm_required
def mob_dead(request):

    if request.method == 'POST':
        mob_id = request.POST.get('mob_id')
        killer_id = request.POST.get('killer')

        mob = Monsters_Active.objects.filter(id=mob_id).first()
        killer = Char_info.objects.filter(id=killer_id).first()
        mob_name = (mob.name_cz or mob.name_en) if mob else f"ID {mob_id}"
        killer_name = killer.name if killer else f"ID {killer_id}"

        log_arena("Smrtící úder zaznamenán! 💀", f"Monstrum '{mob_name}' skoleno postavou '{killer_name}'")

# ACHIVEMENT
        smrtici_stroj_ach(char_id=killer_id, amount=1)
# LOOT
        #loot_gold(mob_id, killer_id) <--- Vypadá to, že není zájem
        #loot_items(mob_id, killer_id) <--- Vypadá to, že není zájem
        loot_temna_esence(mob_id, killer_id)
# LOG
        log = Logs(
            player=killer.player,
            character=killer,
            message=f"Postava {killer_name} porazila monstrum {mob_name}",
            value=None
        )
        log.save()

# ODEBRÁNÍ MONSTRA (MUSÍ BÝT NAKONEC!)

        mob.is_dead = True
        mob.in_fight = False
        mob.save()
        log_mob("Monstrum zabito", f"{mob_name} [ID: {mob_id}]")

        return redirect('dm_site_app:pvp_arena')
    return redirect('dm_site_app:pvp_arena')

@dm_required
def loot_management(request):

    all_chars = Char_info.objects.all()

    all_lootable_monsters = Monsters_Active.objects.filter(loot_able=True)
    alive_monsters = all_lootable_monsters.filter(is_dead=False)
    dead_monsters = all_lootable_monsters.filter(is_dead=True)

    all_lootable_npc = Npc.objects.filter(loot_able=True)
    alive_npc = all_lootable_npc.filter(is_dead=False)
    dead_npc = all_lootable_npc.filter(is_dead=True)
    
    context = {
        'all_chars': all_chars,
        'alive_monsters': alive_monsters,
        'dead_monsters': dead_monsters,
        'alive_npc': alive_npc,
        'dead_npc': dead_npc,
        'current_page': 'loot_management',
    }
    
    return render(request, 'dm_site_app/loot_management.html', context)


def plus_loot_gold(request):
    if request.method == 'POST':
        mob_id = int(request.POST.get('mob_id'))
        character_id = int(request.POST.get('character_id'))
    else:
        return redirect('dm_site_app:loot_management') 

# IDENTIFIKACE A PŘEPOČET
    mob = Monsters_Active.objects.filter(id=mob_id).first()
    character = Char_info.objects.filter(id=character_id).first()
    plus_gold = int(mob.loot_gold)
    plus_silver = int(mob.loot_silver)
    plus_total_gold = float(plus_gold + (plus_silver / 10))

# PŘIPSÁNÍ POSTAVĚ
    character.gold += plus_gold
    character.silver += plus_silver
    character.total_golds += plus_total_gold
    character.save()

# ACHIVEMENT
    zbohatlik_ach(char_id=character_id, amount=plus_total_gold)

# Log
    log = Logs(
        player=character.player,
        character=character,
        message=f"Postava {character.name} získala {plus_gold} zlata a {plus_silver} stříbra od monstra {mob.name_cz or mob.name_en}",
        value=plus_total_gold,
    )
    log.save()
    log_gold(f"{character_id}, {plus_gold}, {plus_silver}")

# Odebrání
    mob.loot_able = False
    mob.save()

    return redirect('dm_site_app:loot_management')
