from django.urls import path, include

from ..views.welcome import welcome
from ..views.auth import login_view, logout_view 

app_name = 'competitions'  # Définir le namespace racine

urlpatterns = [
    # Page d'accueil principale
    path('', welcome, name='welcome'),
    
    # URLs Onboarding
    path('onboarding/', include('competitions.urls.onboarding', namespace='onboarding')),
    
    # URLs Dashboard
    path('dashboard/', include('competitions.urls.dashboard', namespace='dashboard')),
    
    # URLs pour les compétitions
    path('competitions/', include('competitions.urls.competitions', namespace='competitions')),
    
    # URLs pour les clubs
    path('club/', include('competitions.urls.club', namespace='club')),
    
    # URLs pour les fédérations
    path('federations/', include('competitions.urls.federations', namespace='federations')),
    
    # URLs pour les catégories
    path('categories/', include('competitions.urls.categories', namespace='categories')),
       # URLs pour les grades
    # competitions/urls.py (ajouter dans le namespace 'federation')
    path('federation/<int:federation_id>/licences/', include('competitions.urls.federation.licences', namespace='licences')),
    path('grades/', include('competitions.urls.grades', namespace='grades')),
    # Nouvelles URLs pour la notation technique - CORRIGÉ avec namespace
    path('technical-scoring/', include('competitions.urls.technical_scoring', namespace='technical_scoring')),
    # URLs pour le module de combat
    path('combat/', include('competitions.urls.combat', namespace='combat')),
    # URLs pour le module de combat Taekwondo
    path('combat-taekwondo/', include('competitions.urls.combat_taekwondo', namespace='combat_taekwondo')),
    # URLs pour le système de notation standalone
    path('standalone-scoring/', include('competitions.urls.standalone_scoring', namespace='standalone_scoring')),
    # URLs pour le système de QR codes
    path('qr/', include('competitions.urls.qr_scanner', namespace='qr')),
    
    # URLs pour les pratiquants/membres
    path('practitioner/', include('competitions.urls.practitioner', namespace='practitioner')),
    
    # URLs pour les événements
    path('events/', include(('competitions.urls.events', 'competitions'), namespace='events')),
    
    # URLs pour la planification d'événements
    path('events/planning/', include('competitions.urls.event_planning', namespace='event_planning')),
    
    # URL de déconnexion
    path('logout/', logout_view, name='logout'),
]