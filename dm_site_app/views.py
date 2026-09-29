from django.shortcuts import render
from .models import Locations
from player_site_app.models import Player, Char_info
from django.shortcuts import redirect

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
        print(f"Přidíno: {gold} zlaťáků a {silver} stříbrňáků postavě {Char_info.objects.get(id=char_id).name}")
        
        char = Char_info.objects.get(id=char_id)
        char.gold += int(gold)
        char.silver += int(silver)
        char.save()
    
    return redirect('golds_management')
    