"""
URLs competitions - Version minimale test
"""
from django.urls import path
from competitions.views import pages

app_name = 'competitions'

urlpatterns = [
    path('', pages.welcome, name='welcome'),
    path('dashboard/', pages.dashboard, name='dashboard'),
]
