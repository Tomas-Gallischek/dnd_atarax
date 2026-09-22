from django.shortcuts import render


def index(request):
    """Základní úvodní zobrazení pro hráčskou sekci."""
    return render(request, 'player_site_app/index.html')
