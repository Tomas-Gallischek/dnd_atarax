from asgiref import current_thread_executor
from .models import Achivements_database, Achivements_players, Player, Char_info, Logs
from dnd_atarax.terminal import log_gold


def golds_achivement(char_id, amount):
    # identifikace
    this_achivement = Achivements_database.objects.get(name="Zbohatlík")
    this_char = Char_info.objects.get(id=char_id)
    current_achivement = Achivements_players.objects.filter(char=this_char, Achivement=this_achivement)
    if current_achivement.exists():
        current_achivement = current_achivement.first()
    else:
        current_achivement = Achivements_players.objects.create(player=this_char.player, char=this_char, Achivement=this_achivement, current_value=amount)

    # Zápis a kontrola
    new_total_gold = this_char.total_golds + amount  # Nové celkové goldy
    current_achivement.current_value = new_total_gold 
    current_achivement.save()  # zapsání a uložení do databáze (kontrola se provede automaticky) 

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
    
def killer_achivement(char_id, amount):
    this_achivement = Achivements_database.objects.get(name="Smrtící stroj")
    this_char = Char_info.objects.get(id=char_id)
    current_achivement = Achivements_players.objects.filter(char=this_char, Achivement=this_achivement)
    if current_achivement.exists():
        current_achivement = current_achivement.first()
    else:
        current_achivement = Achivements_players.objects.create(player=this_char.player, char=this_char, Achivement=this_achivement, current_value=amount)

# Zápis a kontrola
    old_value = current_achivement.current_value
    current_achivement.current_value += amount
    current_achivement.save()  

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
    
    
    
    


    


    
    

    