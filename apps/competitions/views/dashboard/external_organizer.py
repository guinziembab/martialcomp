from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset
import logging

logger = logging.getLogger(__name__)

@login_required
def dashboard_external_organizer(request):
    """Dashboard complet pour lâ€™organisateur non-membre."""
    user = request.user
    # Récupérer les compétitions organisées par cet utilisateur (Ã  adapter selon modèle)
    competitions = []  # Ã€ remplacer par la vraie requÃªte si besoin
    
    # Statistiques Combat pour organisateurs externes
    combat_stats = {}
    try:
        from ...models.combat import Combat, Equipe, Poule, ActionCombat
        combat_stats = {
            'total_combats': Combat.objects.count(),
            'ongoing_combats': Combat.objects.filter(status='en_cours').count(),
            'completed_combats': Combat.objects.filter(status='termine').count(),
            'total_equipes': Equipe.objects.count(),
            'total_poules': Poule.objects.count(),
        }
    except Exception:
        combat_stats = {'total_combats': 0}
    
    
    context = {
        'user': user,
        'competitions': competitions,
        'combat_stats': combat_stats,
    }
    
    return render(request, 'competitions/dashboard/external_organizer.html', context) 
