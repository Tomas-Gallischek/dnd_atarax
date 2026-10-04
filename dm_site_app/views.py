from django.utils import functional
from dm_site_app.models import Monsters_All_db, Monsters_Active
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

    active_mobs = Monsters_Active.objects.all()
    
    if active_mobs:
        context = {
            'active_mobs_names': active_mobs.name_cz,
        }
    else:
        context = {
            'active_mobs_names': "Nic nenalezeno",
        }

    return render(request, 'dm_site_app/monster_gen_page.html', context)

@dm_required
def random_monster_gen(request):
    if request.method == 'POST':
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
        
        # Vybere náhodné monstrum
        if monsters:
            random_mob = random.choice(monsters) 
            active_mob_db_save(random_mob.id)

            return render(request, 'dm_site_app/monster_gen_page.html')
        else:
            messages.error(request, "Nenalezeno na daný level")
            return redirect('dm_site_app:monster_gen_page')

def active_mob_db_save(mob_id):
    mob = Monsters_All_db.objects.get(id=mob_id)
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
        damage_vulnerability=mob.damage_vulnerability,
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
    

    
    

    
    

    


    
    