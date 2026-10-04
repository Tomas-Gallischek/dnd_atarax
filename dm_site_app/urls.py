from django.urls import path
from . import views

app_name = 'dm_site_app'

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/', views.index, name='index_dashboard'),
    path('tools/', views.tools, name='tools'),
    path('npc/', views.npc, name='npc'),
    path('npcs/', views.npc, name='npcs'),
    path('locations/', views.locations, name='locations'),
    path('notes/', views.notes, name='notes'),
    path('lore/', views.lore, name='lore'),
    path('golds-management/', views.golds_management, name='golds-management'),
    path('add_gold/', views.add_gold, name='add_gold'),
    path('monster_gen_page/', views.monster_gen_page, name='monster_gen_page'),
    path('random_monster_gen/', views.random_monster_gen, name='random_monster_gen'),
    path('remove_mob/<int:mob_id>/', views.remove_mob, name='remove_mob'),
    path('specific_monster_gen/', views.specific_monster_gen, name='specific_monster_gen'),
    path('pvp_pre', views.pvp_pre, name='pvp_pre'),
    path('pvp_arena', views.pvp_arena, name='pvp_arena'),
]
