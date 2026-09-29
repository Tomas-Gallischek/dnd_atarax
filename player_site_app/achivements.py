from .models import Achivements_database, Achivements_players, Player, Char_info, Logs


def golds_achivement(char_id, amount):
    
# identifikace
    this_achivement = Achivements_database.objects.get(name="Zbohatlík")
    this_char = Char_info.objects.get(id=char_id)
    current_achivement = this_char.achivements.get(Achivement=this_achivement)

# Zápis a kontrola
    new_total_gold = this_char.total_golds + amount # Nové celkové goldy
    current_achivement.current_value = new_total_gold 
    current_achivement.save() # zapsání a uložení do databáze (kontrola se provede automaticky) 

    log = Logs(
        player=this_char.player,
        character=this_char,
        message=f"Aktualizace GOLD achivementu",
        value=current_achivement.current_value
    )
    log.save()

    return "OK"

    
    
    
    
    


    


    
    

    