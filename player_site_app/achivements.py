from asgiref import current_thread_executor
from .models import Achivements_database, Achivements_players, Player, Char_info, Logs
from dnd_atarax.terminal import log_gold



def add_temna_esence(char_id, old_rank, new_rank):
    this_char = Char_info.objects.get(id=char_id)
    player = Player.objects.get(id=this_char.player.id)
    if new_rank != old_rank:
        if new_rank == "bronze":
            temna_esence_reward = 100
        elif new_rank == "silver":
            temna_esence_reward = 200
        elif new_rank == "gold":
            temna_esence_reward = 300
        elif new_rank == "platinum":
            temna_esence_reward = 400
        elif new_rank == "emerald":
            temna_esence_reward = 500
        elif new_rank == "diamond":
            temna_esence_reward = 600

        player.temna_esence += temna_esence_reward
        player.save()

        log = Logs(
            player=this_char.player,
            character=this_char,
            message=f"Nová úroveň Achivementu:({old_rank} → {new_rank}) - {temna_esence_reward} TE",
            value=player.temna_esence
        )
        log.save()

        log_gold("Nová úroveň Achivementu", f"{this_char.name}: {player.temna_esence} temné esence celkem")

        return "OK"  
    else:
        return "OK"

def zbohatlik_ach(char_id, amount):
    # identifikace
    this_achivement = Achivements_database.objects.get(name="Zbohatlík")
    this_char = Char_info.objects.get(id=char_id)
    current_achivement = Achivements_players.objects.filter(char=this_char, Achivement=this_achivement)
    if current_achivement.exists():
        current_achivement = current_achivement.first()
    else:
        current_achivement = Achivements_players.objects.create(player=this_char.player, char=this_char, Achivement=this_achivement, current_value=amount)

    old_rank = current_achivement.current_status

    # Zápis a kontrola
    new_total_gold = this_char.total_golds + amount  # Nové celkové goldy
    current_achivement.current_value = new_total_gold 
    current_achivement.save()  # zapsání a uložení do databáze (kontrola se provede automaticky) 

    new_rank = current_achivement.current_status
    
    add_temna_esence(char_id, old_rank, new_rank)

# Zápis Logu
    log = Logs(
        player=this_char.player,
        character=this_char,
        message=f"Aktualizace GOLD achivementu",
        value=current_achivement.current_value
    )
    log.save()

    log_gold("Úspěch 'Zbohatlík' aktualizován", f"{this_char.name}: {current_achivement.current_value} gp celkem")

    return "OK"
    
def smrtici_stroj_ach(char_id, amount):
    this_achivement = Achivements_database.objects.get(name="Smrtící stroj")
    this_char = Char_info.objects.get(id=char_id)
    current_achivement = Achivements_players.objects.filter(char=this_char, Achivement=this_achivement)
    if current_achivement.exists():
        current_achivement = current_achivement.first()
    else:
        current_achivement = Achivements_players.objects.create(player=this_char.player, char=this_char, Achivement=this_achivement, current_value=0) #Nula, protože to pak přidávám znova

    old_rank = current_achivement.current_status
    
# Zápis a kontrola
    old_value = current_achivement.current_value
    current_achivement.current_value += amount
    current_achivement.save()  
    
    new_rank = current_achivement.current_status

    add_temna_esence(char_id, old_rank, new_rank)


# Zápis Logu
    log = Logs(
        player=this_char.player,
        character=this_char,
        message=f"AKTUALIZACE ACHIVEMENTU 'Smrtící stroj'. Postava {this_char.name} zabila {amount} monster. Změna z: {old_value} na: {current_achivement.current_value}",
        value=current_achivement.current_value
    )
    log.save()

    log_gold("AKTUALIZACE ACHIVEMENTU 'Smrtící stroj'", f"{this_char.name} zabil {amount} monster. Celkem: {current_achivement.current_value} monster")

    return "OK"
    

def esencionik_ach(char_id, amount):
    this_achivement = Achivements_database.objects.get(name="Esencionik")
    this_char = Char_info.objects.get(id=char_id)
    current_achivement = Achivements_players.objects.filter(char=this_char, Achivement=this_achivement)
    if current_achivement.exists():
        current_achivement = current_achivement.first()
    else:
        current_achivement = Achivements_players.objects.create(player=this_char.player, char=this_char, Achivement=this_achivement, current_value=0) #Nula, protože to pak přidávám znova

    old_rank = current_achivement.current_status

# Zápis a kontrola
    old_value = current_achivement.current_value
    current_achivement.current_value += amount
    current_achivement.save()  

    new_rank = current_achivement.current_status
    
    add_temna_esence(char_id, old_rank, new_rank)

# Zápis Logu
    log = Logs(
        player=this_char.player,
        character=this_char,
        message=f"AKTUALIZACE ACHIVEMENTU 'Esencionik'. Postava {this_char.name} sesbírala {amount} Temné esence. Změna z: {old_value} na: {current_achivement.current_value}",
        value=current_achivement.current_value
    )
    log.save()

    log_gold("AKTUALIZACE ACHIVEMENTU 'Esencionik'", f"{this_char.name} sesbíral {amount} Temné esence. Celkem: {current_achivement.current_value} Temné esence")

    return "OK"
    
    
    


    


    
    

    