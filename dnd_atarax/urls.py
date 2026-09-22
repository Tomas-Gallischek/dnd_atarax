from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('player/', include('player_site_app.urls')),
    path('dm/', include('dm_site_app.urls')),
    path('', RedirectView.as_view(pattern_name='player_site_app:index', permanent=False), name='home'),
]
