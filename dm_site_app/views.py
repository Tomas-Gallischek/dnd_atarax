from django.shortcuts import render
from models import Locations

def index(request):
    return render(request, 'dm_site_app/index_dashboard.html')

def locations(request):

    all_locations = Locations.objects.all()
    
    context = {
        'locations': all_locations
    }

    return render(request, 'dm_site_app/locations.html', context)