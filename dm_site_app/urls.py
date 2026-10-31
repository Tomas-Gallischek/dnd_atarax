from django.urls import path
from . import views

app_name = 'dm_site_app'

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/', views.index, name='index_dashboard'),
    path('tools/', views.tools, name='tools'),
    # 3. NPC
    path('npc/', views.npc, name='npc'),
    path('npcs/', views.npc, name='npcs'),
    path('npc/create/', views.npc_create, name='npc_create'),
    path('npc/<int:npc_id>/', views.npc_detail, name='npc_detail'),
    path('npc/<int:npc_id>/edit/', views.npc_edit, name='npc_edit'),
    path('npc/<int:npc_id>/delete/', views.npc_delete, name='npc_delete'),

    # 4. Lokace
    path('locations/', views.locations, name='locations'),
    path('locations/create/', views.location_create, name='location_create'),
    path('locations/<int:loc_id>/', views.location_detail, name='location_detail'),
    path('locations/<int:loc_id>/edit/', views.location_edit, name='location_edit'),
    path('locations/<int:loc_id>/delete/', views.location_delete, name='location_delete'),

    # 5. Poznámky
    path('notes/', views.notes, name='notes'),
    path('notes/create/', views.note_create, name='note_create'),
    path('notes/<int:note_id>/', views.notes, name='note_detail'),
    path('notes/<int:note_id>/edit/', views.note_edit, name='note_edit'),
    path('notes/<int:note_id>/toggle_current/', views.note_toggle_current, name='note_toggle_current'),
    path('notes/<int:note_id>/delete/', views.note_delete, name='note_delete'),
    path('lore/', views.lore, name='lore'),
    path('kronika_edit/', views.kronika_edit, name='kronika_edit'),
    path('golds-management/', views.golds_management, name='golds-management'),
    path('add_gold/', views.add_gold, name='add_gold'),
    path('monster_gen_page/', views.monster_gen_page, name='monster_gen_page'),
    path('random_monster_gen/', views.random_monster_gen, name='random_monster_gen'),
    path('remove_mob/<int:mob_id>/', views.remove_mob, name='remove_mob'),
    path('specific_monster_gen/', views.specific_monster_gen, name='specific_monster_gen'),
    path('create_custom_monster/', views.create_custom_monster, name='create_custom_monster'),
    path('pvp_pre', views.pvp_pre, name='pvp_pre'),
    path('pvp_arena', views.pvp_arena, name='pvp_arena'),
    path('in_fight_switch', views.in_fight_switch, name='in_fight_switch'),
    path('api/update_hp/', views.api_update_hp, name='api_update_hp'),
    path('mob_dead/', views.mob_dead, name='mob_dead'),
    path('loot_management/', views.loot_management, name='loot_management'),
    path('plus_loot_gold/', views.plus_loot_gold, name='plus_loot_gold'),
    path('assign_loot_items/', views.assign_loot_items, name='assign_loot_items'),
    path('create_custom_item/', views.create_custom_item, name='create_custom_item'),
    path('player_inventory/', views.player_inventory_management, name='player_inventory_management'),
    path('player_inventory/delete/<int:item_id>/', views.dm_delete_player_item, name='dm_delete_player_item'),
    path('player_inventory/bulk_delete/', views.dm_bulk_delete_player_items, name='dm_bulk_delete_player_items'),

    # 7. Správa Úspěchů (Achievements)
    path('achievements/', views.achievements_management, name='achievements_management'),
    path('achievements/assign/', views.dm_assign_achievement, name='dm_assign_achievement'),
    path('achievements/update/<int:ach_player_id>/', views.dm_update_achievement_value, name='dm_update_achievement_value'),
    path('achievements/delete/<int:ach_player_id>/', views.dm_delete_player_achievement, name='dm_delete_player_achievement'),
    path('achievements/template/create/', views.dm_create_achievement_template, name='dm_create_achievement_template'),
    path('achievements/template/<int:template_id>/edit/', views.dm_edit_achievement_template, name='dm_edit_achievement_template'),

    # 8. Pozice pro kouzla (Spell Slots DM Tool)
    path('spell-slots/', views.spell_slots_management, name='spell_slots_management'),
    path('spell-slots/modify/', views.modify_spell_slots, name='modify_spell_slots'),

    # 9. Přehled aplikačních logů (DM Logs Tool)
    path('logs/', views.logs_view, name='logs_view'),

    # 10. Databáze a správa všech kouzel (DM Spells Tool)
    path('spells/', views.spells_management, name='spells_management'),
    path('spells/create/', views.dm_create_spell, name='dm_create_spell'),
    path('spells/<int:spell_id>/edit/', views.dm_edit_spell, name='dm_edit_spell'),
    path('spells/<int:spell_id>/delete/', views.dm_delete_spell, name='dm_delete_spell'),
]

