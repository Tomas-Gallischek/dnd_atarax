from django.urls import path
from . import views

app_name = 'dm_site_app'

urlpatterns = [
    # 1. index_dashboard.html
    path('', views.index, name='index'),
    path('dashboard/', views.index, name='index_dashboard'),

    # 2. tools.html
    path('tools/', views.tools, name='tools'),

    # 3. npc.html
    path('npc/', views.npc, name='npc'),
    path('npcs/', views.npc, name='npcs'),

    # 4. locations.html
    path('locations/', views.locations, name='locations'),

    # 5. notes.html
    path('notes/', views.notes, name='notes'),

    # 6. lore.html
    path('lore/', views.lore, name='lore'),

    # Správa zlaťáků
    path('golds-management/', views.golds_management, name='golds-management'),
    path('add_gold/', views.add_gold, name='add_gold'),
]
