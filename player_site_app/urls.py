from django.urls import path
from . import views

app_name = 'player_site_app'

urlpatterns = [
    # Autentizace
    path('', views.index, name='index'),
    path('login/', views.index, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # 1. char_over_view..html a poznámky
    path('postava/', views.char_overview, name='char_overview_active'),
    path('postava/<int:char_id>/', views.char_overview, name='char_overview'),
    path('postava/poznamka/pridat/', views.add_char_note, name='add_char_note'),
    path('postava/poznamka/smazat/<int:note_id>/', views.delete_char_note, name='delete_char_note'),
    path('postava/poznamka/oblibene/<int:note_id>/', views.toggle_favorite_note, name='toggle_favorite_note'),

    # 2. inv.html
    path('inventar/', views.inv_view, name='inv'),
    path('inventar/<int:char_id>/', views.inv_view, name='inv_detail'),

    # 3. char_schopnosti.html
    path('schopnosti/', views.char_schopnosti_view, name='char_schopnosti'),
    path('schopnosti/<int:char_id>/', views.char_schopnosti_view, name='char_schopnosti_detail'),

    # 4. char_roleplay.html a backstory
    path('roleplay/', views.char_roleplay_view, name='char_roleplay'),
    path('roleplay/<int:char_id>/', views.char_roleplay_view, name='char_roleplay_detail'),
    path('roleplay/backstory/pridat/', views.add_char_backstory, name='add_char_backstory'),
    path('roleplay/backstory/smazat/<int:backstory_id>/', views.delete_char_backstory, name='delete_char_backstory'),
    path('roleplay/backstory/zverejnit/<int:backstory_id>/', views.toggle_public_backstory, name='toggle_public_backstory'),

    # 5. char_achivements.html
    path('achievements/', views.char_achivements_view, name='char_achivements'),
    path('achievements/<int:char_id>/', views.char_achivements_view, name='char_achivements_detail'),

    # 6. char_stats_detail.html
    path('statistiky/', views.char_stats_detail_view, name='char_stats_detail'),
    path('statistiky/<int:char_id>/', views.char_stats_detail_view, name='char_stats_detail_detail'),

    # 7. kronika.html
    path('kronika/', views.kronika_view, name='kronika'),

    # 8. prehled_postav.html & všechny postavy družiny (all_chars)
    path('prehled-postav/', views.prehled_postav, name='prehled_postav'),
    path('druzina/', views.all_chars_view, name='all_chars'),
    path('druzina/<int:char_id>/', views.all_chars_detail_view, name='all_chars_detail'),

    # 9. stream.html
    path('stream/', views.stream_view, name='stream'),

    # 10. dungeon_shop.html
    path('dungeon-shop/', views.dungeon_shop_view, name='dungeon_shop'),
    path('dungeon-shop/inventar/', views.dungeon_shop_inv_view, name='dungeon_shop_inv'),
    path('esence_buy/', views.esence_buy, name='esence_buy'),
    path('use_treasure/', views.use_treasure, name='use_treasure')
]
