from django.shortcuts import render, redirect, get_object_or_404
from .models import Locations
from player_site_app.models import Player, Char_info, Logs

def index(request):
    if request.user.is_staff == False:
        return redirect('player_site_app:index')
    return render(request, 'dm_site_app/index_dashboard.html')

def locations(request):
    if request.user.is_staff == False:
        return redirect('player_site_app:index')

    all_locations = Locations.objects.all()

    context = {
        'locations': all_locations
    }

    return render(request, 'dm_site_app/locations.html', context)

def tools(request):
    if request.user.is_staff == False:
        return redirect('player_site_app:index')
    return render(request, 'dm_site_app/tools.html')

def golds_management(request):
    if request.user.is_staff == False:
        return redirect('player_site_app:index')
    all_chars = Char_info.objects.all()

    
    context = {
        'all_chars': all_chars
    }
    return render(request, 'dm_site_app/golds_management.html', context)

def lore(request):
    if request.user.is_staff == False:
        return redirect('player_site_app:index')
    return render(request, 'dm_site_app/lore.html')

def notes(request):
    if request.user.is_staff == False:
        return redirect('player_site_app:index')
    return render(request, 'dm_site_app/notes.html')

def npcs(request):
    if request.user.is_staff == False:
        return redirect('player_site_app:index')
    return render(request, 'dm_site_app/npcs.html')


def add_gold(request):
    if request.user.is_staff == False:
        return redirect('player_site_app:index')
    if request.method == 'POST':
        char_id = request.POST.get('char_id')
        gold = request.POST.get('gold')
        silver = request.POST.get('silver')
        action = request.POST.get('action')
        plus_total_golds = float(gold) + (float(silver) / 10)

        if char_id:
            char = get_object_or_404(Char_info, id=char_id)
            if action == 'plus':
                char.gold += int(gold or 0)
                char.silver += int(silver or 0)
                char.total_golds += plus_total_golds
            elif action == 'minus':
                char.gold -= int(gold or 0)
                char.silver -= int(silver or 0)
            else:
                return redirect('dm_site_app:golds-management')
                
            char.save()

            log = Logs(
                player=char.player,
                character=char,
                message=f"Přidáno: {gold} zlaťáků a {silver} stříbrňáků",
                value=plus_total_golds
            )
            log.save()

    return redirect('dm_site_app:golds-management')
    