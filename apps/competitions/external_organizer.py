from django.urls import path
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

# Vues pour l'organisateur non-membre
@login_required
def participants_view(request):
    """Vue pour gérer les participants des compétitions organisées."""
    context = {
        'title': _('Gestion des Participants'),
        'participants': [],  # Ã€ remplir avec les vraies données
    }
    return render(request, 'competitions/external_organizer/participants.html', context)

@login_required
def results_view(request):
    """Vue pour afficher les résultats des compétitions."""
    context = {
        'title': _('Résultats des Compétitions'),
        'results': [],  # Ã€ remplir avec les vraies données
    }
    return render(request, 'competitions/external_organizer/results.html', context)

@login_required
def reports_view(request):
    """Vue pour les rapports et statistiques."""
    context = {
        'title': _('Rapports et Statistiques'),
        'reports': [],  # Ã€ remplir avec les vraies données
    }
    return render(request, 'competitions/external_organizer/reports.html', context)

@login_required
def profile_view(request):
    """Vue pour gérer le profil de l'organisateur."""
    context = {
        'title': _('Mon Profil'),
        'user': request.user,
    }
    return render(request, 'competitions/external_organizer/profile.html', context)

@login_required
def support_view(request):
    """Vue pour le support et l'aide."""
    context = {
        'title': _('Support et Aide'),
    }
    return render(request, 'competitions/external_organizer/support.html', context)

app_name = 'external_organizer'

urlpatterns = [
    path('participants/', participants_view, name='participants'),
    path('results/', results_view, name='results'),
    path('reports/', reports_view, name='reports'),
    path('profile/', profile_view, name='profile'),
    path('support/', support_view, name='support'),
] 
