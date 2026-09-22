from django.shortcuts import render


def index(request):
    return render(request, 'player_site_app/index.html')
