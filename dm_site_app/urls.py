from django.urls import path
from . import views

app_name = 'dm_site_app'

urlpatterns = [
    path('', views.index, name='index'),
    path('locations',views.locations,name='locations'),
    path('golds-management',views.golds_management,name='golds-management'),
    path('tools',views.tools,name='tools'),
    path('lore',views.lore,name='lore'),
    path('notes',views.notes,name='notes'),
    path('npcs',views.npcs,name='npcs'),
    
    
]
