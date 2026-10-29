import json
import random
from functools import wraps
from django.http import JsonResponse
from django.utils import functional
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Locations, Npc, Monsters_All_db, Monsters_Active
from player_site_app.models import Player, Char_info, Logs, create_db_log
from player_site_app.achivements import zbohatlik_ach, smrtici_stroj_ach, esencionik_ach
from dnd_atarax.terminal import (
    log_dm, log_arena, log_hp, log_mob, log_player,
    log_gold, log_success, log_warning, log_error, log_info
)


def loot_temna_esence(mob_id, killer_id):
    try:
        mob = Monsters_Active.objects.get(id=mob_id)
    except Monsters_Active.DoesNotExist:
        log_error("Monstrum nenalezeno", f"ID: {mob_id}")
        return
    try:
        char = Char_info.objects.get(id=killer_id)
        player = char.player
    except (Player.DoesNotExist, Char_info.DoesNotExist):
        log_error("Hráč nenalezen", f"ID: {killer_id}")
        return

    cr = mob.challenge_rating or 0
    min_value = int(cr * 2)
    if min_value < 1:
        min_value = 1

    max_value = int(cr * 4)
    if max_value < 2:
        max_value = 2

    if min_value >= max_value:
        min_value = max_value
        max_value = min_value

    plus_temna_esence = random.randint(int(min_value), int(max_value))
    player.temna_esence = (player.temna_esence or 0) + plus_temna_esence
    player._skip_auto_log = True
    player.save()

    create_db_log(
        character=char,
        player=player,
        message=f"Postava {char.name} získala +{plus_temna_esence} Temné esence ze zabitého monstra '{mob.name_cz}' (celkem {player.temna_esence} TE)",
        value=float(plus_temna_esence)
    )

    # ACHIVEMENT
    esencionik_ach(char_id=killer_id, amount=plus_temna_esence)

    log_success("Temná esence", f"Postava: {char.name} | Hráč: {player.nickname} -> Přidáno: {plus_temna_esence} Temné esence")

    return


# Dodělat pokud bude zájem
def loot_gold(mob_id, killer_id):
    try:
        mob = Monsters_Active.objects.get(id=mob_id)
    except Monsters_Active.DoesNotExist:
        log_error("Monstrum nenalezeno", f"ID: {mob_id}")
        return
    try:
        player = Char_info.objects.get(id=killer_id)
    except Char_info.DoesNotExist:
        log_error("Hráč nenalezen", f"ID: {killer_id}")
        return


# Dodělat pokud bude zájem
def loot_items(mob_id, killer_id):
    try:
        mob = Monsters_Active.objects.get(id=mob_id)
    except Monsters_Active.DoesNotExist:
        log_error("Monstrum nenalezeno", f"ID: {mob_id}")
        return
    try:
        player = Char_info.objects.get(id=killer_id)
    except Char_info.DoesNotExist:
        log_error("Hráč nenalezen", f"ID: {killer_id}")
        return
