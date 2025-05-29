# competitions/urls/grades.py - Module de transition
# Dans competitions/urls/grades.py
from django.urls import path, include


app_name = 'grades'  # Ajoutez cette ligne
# Ce module redirige simplement vers la nouvelle application grades
urlpatterns = [
    path('', include('grades.urls')),
]