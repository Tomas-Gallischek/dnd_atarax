from dnd_atarax import terminal
from asgiref import current_thread_executor
from .models import Achivements_database, Achivements_players, Player, Char_info, Logs
from dnd_atarax.terminal import log_gold


def zbohatlik_ach(char_id, amount):
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
    
def smrtici_stroj_ach(char_id, amount):
    this_achivement = Achivements_database.objects.get(name="Smrtící stroj")
    this_char = Char_info.objects.get(id=char_id)
    current_achivement = Achivements_players.objects.filter(char=this_char, Achivement=this_achivement)
    if current_achivement.exists():
        current_achivement = current_achivement.first()
    else:
        current_achivement = Achivements_players.objects.create(player=this_char.player, char=this_char, Achivement=this_achivement, current_value=0) #Nula, protože to pak přidávám znova

    
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
    

# ==============================================================================
# POZNÁMKA K TEMNÉ ESENCI A ZACYKLENÍ:
# Temná esence získaná jako odměna za povýšení hodnosti v jakémkoliv jiném
# achievementu se do achievementu "Esencionik" započítává automaticky přímo
# v modelu Achivements_players (metoda update_achivement_status), kde je
# implementována ochrana proti zacyklení (Esencionik sám sebe nepovyšuje).
# Tato funkce esencionik_ach slouží výhradně pro započtení esence získané
# z jiných herních zdrojů (např. kořist z monster, rozebrání předmětů v shopu apod.).
# ==============================================================================
def esencionik_ach(char_id, amount):
    this_achivement = Achivements_database.objects.filter(name__iexact="Esencionik").first()
    this_char = Char_info.objects.filter(id=char_id).first()
    if not this_achivement or not this_char:
        return "NOT_FOUND"

    current_achivement = Achivements_players.objects.filter(char=this_char, Achivement=this_achivement)
    if current_achivement.exists():
        current_achivement = current_achivement.first()
    else:
        current_achivement = Achivements_players.objects.create(player=this_char.player, char=this_char, Achivement=this_achivement, current_value=0)

    # Zápis a kontrola
    old_value = current_achivement.current_value
    current_achivement.current_value += amount
    current_achivement.save()  

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


def gambler_ach(char_id, amount=1):
    this_achivement = Achivements_database.objects.filter(name__iexact="Gambler").first()
    this_char = Char_info.objects.filter(id=char_id).first()
    if not this_achivement or not this_char:
        return "NOT_FOUND"

    current_achivement = Achivements_players.objects.filter(char=this_char, Achivement=this_achivement)
    if current_achivement.exists():
        current_achivement = current_achivement.first()
    else:
        current_achivement = Achivements_players.objects.create(player=this_char.player, char=this_char, Achivement=this_achivement, current_value=0) 

    # Zápis a kontrola
    old_value = current_achivement.current_value
    current_achivement.current_value += amount
    current_achivement.save()  

    # Zápis Logu
    log = Logs(
        player=this_char.player,
        character=this_char,
        message=f"AKTUALIZACE ACHIVEMENTU 'Gambler'. Postava {this_char.name} otevřela truhlu ({amount}x). Změna z: {old_value} na: {current_achivement.current_value}",
        value=current_achivement.current_value
    )
    log.save()

    log_gold("AKTUALIZACE ACHIVEMENTU 'Gambler'", f"{this_char.name} otevřel truhlu v Dungeon Shopu ({amount}x). Celkem otevřeno: {current_achivement.current_value} truhel")

    return "OK"
    
    

    


    
    

    