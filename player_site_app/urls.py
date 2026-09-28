from django.urls import path
from . import views

app_name = 'player_site_app'

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.index, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('prehled-postav/', views.prehled_postav, name='prehled_postav'),
    path('postava/<int:char_id>/', views.char_overview, name='char_overview'),
]
