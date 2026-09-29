from django.shortcuts import render, redirect, get_object_or_404
from .models import Locations
from player_site_app.models import Player, Char_info

def index(request):
    return render(request, 'dm_site_app/index_dashboard.html')

def locations(request):

    all_locations = Locations.objects.all()

    context = {
        'locations': all_locations
    }

    return render(request, 'dm_site_app/locations.html', context)

def tools(request):
    return render(request, 'dm_site_app/tools.html')

def golds_management(request):
    all_chars = Char_info.objects.all()

    
    context = {
        'all_chars': all_chars
    }
    return render(request, 'dm_site_app/golds_management.html', context)

def lore(request):
    return render(request, 'dm_site_app/lore.html')

def notes(request):
    return render(request, 'dm_site_app/notes.html')

def npcs(request):
    return render(request, 'dm_site_app/npcs.html')


def add_gold(request):
    if request.method == 'POST':
        char_id = request.POST.get('char_id')
        gold = request.POST.get('gold')
        silver = request.POST.get('silver')

        if char_id:
            char = get_object_or_404(Char_info, id=char_id)
            char.gold += int(gold or 0)
            char.silver += int(silver or 0)
            char.save()
            print(f"Přidáno: {gold} zlaťáků a {silver} stříbrňáků postavě {char.name}")

    return redirect('dm_site_app:golds-management')
    