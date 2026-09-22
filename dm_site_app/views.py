from django.shortcuts import render


def index(request):
    """Základní úvodní zobrazení pro sekci Pána jeskyně."""
    return render(request, 'dm_site_app/index.html')
