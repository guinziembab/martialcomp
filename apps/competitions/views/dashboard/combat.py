from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.competitions.utils.decorators import federation_or_club_required
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Count, Q
from apps.competitions.models.combat import (
    CombatConfiguration, Equipe, Poule, Combat, ActionCombat, MembreEquipe
)
from apps.competitions.models import Competition
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

import logging
logger = logging.getLogger(__name__)

@login_required
def combat_dashboard(request):
    """
    Tableau de bord Combat filtré par club.
    Affiche uniquement les données relatives au club du manager :
    - Équipes du club
    - Combats impliquant au moins un membre du club
    - Statistiques filtrées par club
    """
    from django.contrib import messages
    from django.shortcuts import redirect
    from apps.competitions.models import Club, Federation

    has_access = False
    user_type = "unknown"
    club = None
    organization = None

    # 1. Vérifier si c'est un responsable de club (owner)
    club = Club.objects.filter(owner=request.user).first()
    if club:
        has_access = True
        user_type = "club"

    # 2. Vérifier via OrganizationMember (manager)
    if not club:
        try:
            from apps.organizations.models import OrganizationMember
            member = OrganizationMember.objects.filter(
                user=request.user,
                is_active=True,
                role__in=['manager', 'admin', 'owner']
            ).first()
            if member:
                club = Club.objects.filter(organization=member.organization).first()
                if club:
                    has_access = True
                    user_type = "club"
        except Exception as e:
            logger.debug(f"Erreur OrganizationMember combat: {e}")

    # 3. Vérifier si c'est un responsable de fédération
    if not has_access:
        fed = Federation.objects.filter(owner=request.user).first()
        if fed:
            has_access = True
            user_type = "federation"

    # 4. Fallback : utilisateur authentifié
    if not has_access and request.user.is_authenticated:
        has_access = True
        user_type = "external"

    if not has_access:
        messages.error(request, _("Vous n'avez pas accès au module Combat."))
        return redirect('competitions:dashboard:index')

    # Déterminer l'organisation du club pour filtrer les pratiquants
    if club:
        organization = club.organization

    # === FILTRAGE PAR CLUB ===
    if club:
        # Équipes du club (club principal ou partenaire)
        club_equipes = Equipe.objects.filter(
            Q(club=club) | Q(clubs_partenaires=club)
        ).distinct()

        # IDs des équipes du club
        club_equipe_ids = list(club_equipes.values_list('id', flat=True))

        # Combats impliquant au moins une équipe du club
        club_combats_filter = Q(equipe_rouge_id__in=club_equipe_ids) | Q(equipe_blanc_id__in=club_equipe_ids)

        # Si le club a une organisation, inclure aussi les combats
        # où un membre du club participe via MembreEquipe
        if organization:
            # IDs des équipes contenant au moins un pratiquant du club
            equipe_ids_via_membres = list(
                MembreEquipe.objects.filter(
                    pratiquant__organization=organization
                ).values_list('equipe_id', flat=True).distinct()
            )
            club_combats_filter = club_combats_filter | Q(
                equipe_rouge_id__in=equipe_ids_via_membres
            ) | Q(
                equipe_blanc_id__in=equipe_ids_via_membres
            )
            # Fusionner les IDs pour les stats
            all_related_equipe_ids = list(set(club_equipe_ids + equipe_ids_via_membres))
        else:
            all_related_equipe_ids = club_equipe_ids

        # Stats filtrées
        total_combats = Combat.objects.filter(club_combats_filter).distinct().count()
        total_equipes = len(all_related_equipe_ids)
        total_poules = Poule.objects.filter(
            equipes__id__in=all_related_equipe_ids
        ).distinct().count()
        total_actions = ActionCombat.objects.filter(
            combat__in=Combat.objects.filter(club_combats_filter).distinct()
        ).count()

        # Configurations : toutes (pas liées à un club)
        configurations = CombatConfiguration.objects.order_by('-id')[:5]

        # Équipes récentes du club
        equipes = Equipe.objects.filter(
            id__in=all_related_equipe_ids
        ).order_by('-created_at')[:5]

        # Combats en cours impliquant le club
        combats_en_cours = Combat.objects.filter(
            club_combats_filter,
            status='en_cours'
        ).distinct().order_by('-debut_combat')[:10]

        # Prochains combats impliquant le club
        prochains_combats = Combat.objects.filter(
            club_combats_filter,
            status='planifie',
        ).distinct().order_by('date_planifiee')[:10]

        # Résultats récents du club
        resultats_recents = Combat.objects.filter(
            club_combats_filter,
            status='termine'
        ).distinct().order_by('-fin_combat')[:10]

    else:
        # Pas de club : afficher tout (fédération ou external)
        total_combats = Combat.objects.count()
        total_equipes = Equipe.objects.count()
        total_poules = Poule.objects.count()
        total_actions = ActionCombat.objects.count()

        configurations = CombatConfiguration.objects.order_by('-id')[:5]
        equipes = Equipe.objects.order_by('-created_at')[:5]
        combats_en_cours = Combat.objects.filter(status='en_cours').order_by('-debut_combat')[:10]
        prochains_combats = Combat.objects.filter(
            status='planifie',
            date_planifiee__gte=timezone.now()
        ).order_by('date_planifiee')[:10]
        resultats_recents = Combat.objects.filter(
            status='termine'
        ).order_by('-fin_combat')[:10]

    context = {
        'title': _('Tableau de bord Combat'),
        'combat_configurations': configurations,
        'teams': equipes,
        'ongoing_combats': combats_en_cours,
        'upcoming_combats': prochains_combats,
        'recent_results': resultats_recents,
        'user_type': user_type,
        'club': club,
        'stats': {
            'total_combats': total_combats,
            'total_equipes': total_equipes,
            'total_poules': total_poules,
            'total_actions': total_actions,
            'ongoing_count': combats_en_cours.count() if hasattr(combats_en_cours, 'count') else len(combats_en_cours),
            'upcoming_count': prochains_combats.count() if hasattr(prochains_combats, 'count') else len(prochains_combats),
            'recent_count': resultats_recents.count() if hasattr(resultats_recents, 'count') else len(resultats_recents),
        }
    }

    return render(request, 'competitions/dashboard/combat.html', context)
