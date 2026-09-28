from django.shortcuts import render
from .models import Locations
import urllib.request
import json

def index(request):
    return render(request, 'dm_site_app/index_dashboard.html')

def locations(request):

    all_locations = Locations.objects.all()

    context = {
        'locations': all_locations
    }

    return render(request, 'dm_site_app/locations.html', context)



def api_items_test(request):
    # Konkrétní endpoint pro vybavení z dnd5eapi
    url = "https://www.dnd5eapi.co/api/equipment"
    
    try:
        # Vytvoření požadavku s hlavičkou, aby nás API neodmítlo
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            # Přečtení a dekódování JSON odpovědi
            data = json.loads(response.read().decode('utf-8'))
            # API vrací seznam předmětů v klíči 'results'
            items = data.get('results', [])
    except Exception as e:
        items = []
        print(f"Chyba při načítání API: {e}")

    return render(request, 'dm_site_app/api_test.html', {'items': items})