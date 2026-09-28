from django.urls import path
from . import views

app_name = 'dm_site_app'

urlpatterns = [
    path('', views.index, name='index'),
    path('locations',views.locations,name='locations'),
    path('api-test/', views.api_items_test, name='api_items_test'),
]
