from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.urls import NoReverseMatch
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from ..models import UserProfile

@require_GET
def welcome(request):
    # Si l'utilisateur vient d'une page dashboard, ne pas rediriger
    referer = request.META.get('HTTP_REFERER', '')
    if 'dashboard' in referer:
        return render(request, 'competitions/welcome.html')
    
    # Si un paramètre no_redirect est présent, afficher simplement la page
    if request.GET.get('no_redirect'):
        return render(request, 'competitions/welcome.html')
    
    if request.user.is_authenticated:
        try:
            # Simplifiez cette partie - utilisez le rôle de l'utilisateur directement
            role = request.user.role  # Assurez-vous que votre modèle User a bien un champ role
            
            # Ajoutez no_redirect pour empêcher les boucles
            if role == 'club_manager':
                return redirect('/competitions/dashboard/club/?no_redirect=1')
            # Autres rôles...
            else:
                # Rôle par défaut avec no_redirect
                return redirect('/competitions/dashboard/spectator/?no_redirect=1')
        except Exception as e:
            # Log l'erreur et affiche la page d'accueil
            print(f"Erreur de redirection: {str(e)}")
            messages.error(request, _("Une erreur s'est produite. Veuillez réessayer."))
            return render(request, 'competitions/welcome.html')
    
    # Utilisateurs non connectés
    return render(request, 'competitions/welcome.html')