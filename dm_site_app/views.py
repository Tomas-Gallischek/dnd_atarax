from django.shortcuts import render


def index(request):
    return render(request, 'dm_site_app/index_dashboard.html')
