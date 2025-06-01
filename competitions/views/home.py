from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET

@login_required
@require_GET
def home(request):
    """
    Vue pour la page d'accueil des utilisateurs authentifiés.
    Cette page peut afficher des informations personnalisées pour l'utilisateur connecté.
    """
    context = {
        'title': 'Accueil - MartialComp',
        'user': request.user,
    }
    
    return render(request, 'competitions/home.html', context)