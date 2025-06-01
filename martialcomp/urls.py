from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('competitions/', include('competitions.urls', namespace='competitions')),
    path('accounts/', include('django.contrib.auth.urls')),
]