from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.competitions.utils.decorators import federation_or_club_required
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Count, Q
from apps.competitions.models.combat import (
    CombatConfiguration, Equipe, Poule, Combat, ActionCombat
)
from apps.competitions.models import Competition
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

@login_required
def combat_dashboard(request):
    """
    View for displaying the combat dashboard.
    Shows combat-related information and management options.
    Available for: club owners, federation owners, and external organizers.
    """
    # Vérifier que l'utilisateur a accès au module combat
    has_access = False
    user_type = "unknown"
    
    # Import des modèles
    from apps.competitions.models import Club, Federation
    
    # Vérifier si c'est un responsable de club
    if Club.objects.filter(owner=request.user).exists():
        has_access = True
        user_type = "club"
        request.club = Club.objects.filter(owner=request.user).first()
    
    # Vérifier si c'est un responsable de fédération
    elif Federation.objects.filter(owner=request.user).exists():
        has_access = True
        user_type = "federation"
        request.federation = Federation.objects.filter(owner=request.user).first()
    
    # Vérifier si c'est un organisateur externe (utilisateur connecté sans club ni fédération)
    elif request.user.is_authenticated:
        # Un organisateur externe peut aussi utiliser le module combat
        has_access = True
        user_type = "external"
    
    # Si aucun accès n'est accordé
    if not has_access:
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, _("Vous n'avez pas accès au module Combat."))
        return redirect('competitions:dashboard:index')
    # Récupérer les statistiques réelles de la base de données
    total_combats = Combat.objects.count()
    total_equipes = Equipe.objects.count()
    total_poules = Poule.objects.count()
    total_actions = ActionCombat.objects.count()
    
    # Récupérer les configurations de combat récentes (5 dernières)
    # Note: CombatConfiguration n'a pas de champ organization, utiliser toutes les configurations pour maintenant
    configurations = CombatConfiguration.objects.order_by('-id')[:5]
    
    # Récupérer les équipes récentes (5 dernières) 
    # Filtrer par club si l'utilisateur appartient à un club
    if hasattr(request, 'club') and request.club:
        equipes = Equipe.objects.filter(club=request.club).order_by('-created_at')[:5]
    else:
        equipes = Equipe.objects.order_by('-created_at')[:5]
    
    # Récupérer les poules récentes (5 dernières)
    # Les poules sont liées aux compétitions, pour maintenant utiliser toutes les poules
    poules = Poule.objects.order_by('-id')[:5]
    
    # Récupérer les combats en cours
    combats_en_cours = Combat.objects.filter(status='en_cours').order_by('-debut_combat')[:10]
    
    # Récupérer les prochains combats (planifiés)
    prochains_combats = Combat.objects.filter(
        status='planifie',
        date_planifiee__gte=timezone.now()
    ).order_by('date_planifiee')[:10]
    
    # Récupérer les résultats récents (combats terminés)
    resultats_recents = Combat.objects.filter(
        status='termine'
    ).order_by('-fin_combat')[:10]
    
    # Préparer les données pour le nouveau template
    context = {
        'title': _('Tableau de bord Combat'),
        'combat_configurations': configurations,
        'teams': equipes,
        'poules': poules,
        'ongoing_combats': combats_en_cours,
        'upcoming_combats': prochains_combats,
        'recent_results': resultats_recents,
        'user_type': user_type,  # Ajouter le type d'utilisateur
        'stats': {
            'total_combats': total_combats,
            'total_equipes': total_equipes,
            'total_poules': total_poules,
            'total_actions': total_actions,
            'ongoing_count': combats_en_cours.count(),
            'upcoming_count': prochains_combats.count(),
            'recent_count': resultats_recents.count()
        }
    }
    
    return render(request, 'competitions/dashboard/combat.html', context)


