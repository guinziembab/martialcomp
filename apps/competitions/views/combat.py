from django.core.exceptions import PermissionDenied
"""
Vues pour la gestion des combats.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.urls import reverse

# Importation de notre helper de permission personnalisé
from apps.competitions.utils.permission_helpers import manual_permission_check, get_user_club

import json
import random
import logging
from decimal import Decimal

from apps.competitions.models.combat import (
    CombatConfiguration, 
    Equipe, 
    MembreEquipe, 
    Poule, 
    Combat, 
    ActionCombat
)
from apps.competitions.forms.combat_forms import (
    CombatConfigurationForm,
    EquipeForm,
    MembreEquipeForm,
    PouleForm,
    CombatForm,
    ActionCombatForm,
    GenerationPoulesForm,
    AttributionPointForm
)
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

logger = logging.getLogger(__name__)

# Vues pour la configuration des combats
@login_required
def liste_configurations(request):
    """
    Affiche la liste des configurations de combat disponibles.
    """
    configurations = CombatConfiguration.objects.order_by('discipline__name', 'nom')
    return render(request, 'competitions/combat/liste_configurations.html', {
        'configurations': configurations
    })

@login_required
def creer_configuration(request):
    """Permet de créer une nouvelle configuration de combat."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.add_combatconfiguration'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    if request.method == 'POST':
        form = CombatConfigurationForm(request.POST)
        if form.is_valid():
            configuration = form.save()
            messages.success(request, _("La configuration de combat a été créée avec succès."))
            return redirect('competitions:combat:liste_configurations')
    else:
        form = CombatConfigurationForm()
    
    return render(request, 'competitions/combat/form_configuration.html', {
        'form': form,
        'title': _("Créer une configuration de combat")
    })

@login_required
def modifier_configuration(request, config_id):
    """Permet de modifier une configuration de combat existante."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.change_combatconfiguration'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    configuration = get_object_or_404(CombatConfiguration, id=config_id)
    
    if request.method == 'POST':
        form = CombatConfigurationForm(request.POST, instance=configuration)
        if form.is_valid():
            form.save()
            messages.success(request, _("La configuration de combat a été modifiée avec succès."))
            return redirect('competitions:combat:liste_configurations')
    else:
        form = CombatConfigurationForm(instance=configuration)
    
    return render(request, 'competitions/combat/form_configuration.html', {
        'form': form,
        'configuration': configuration,
        'title': _("Modifier une configuration de combat")
    })

@login_required
def supprimer_configuration(request, config_id):
    """Permet de supprimer une configuration de combat."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.delete_combatconfiguration'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    configuration = get_object_or_404(CombatConfiguration, id=config_id)
    
    if request.method == 'POST':
        configuration.delete()
        messages.success(request, _("La configuration de combat a été supprimée avec succès."))
        return redirect('competitions:combat:liste_configurations')
    
    return render(request, 'competitions/combat/confirmer_suppression.html', {
        'object': configuration,
        'title': _("Supprimer la configuration de combat"),
        'message': _("ÃŠtes-vous sÃ»r de vouloir supprimer cette configuration de combat ?"),
        'cancel_url': reverse('competitions:liste_configurations')
    })

# Vues pour la gestion des équipes
@login_required
def liste_equipes(request, competition_id=None):
    """
    Affiche la liste des équipes, filtrées par compétition.
    Ne montre que les équipes des catégories de type combat.
    Si aucune compétition n'est spécifiée, affiche la liste des compétitions disponibles.
    """
    from apps.competitions.models import Competition
    from django.db.models import Q

    if competition_id:
        competition = get_object_or_404(Competition, id=competition_id)
        # Filtrer les équipes pour ne montrer que celles des catégories combat
        # Une équipe est "combat" si sa catégorie a un competition_type avec scoring_system='combat'
        equipes = Equipe.objects.filter(
            competition=competition
        ).filter(
            Q(category__competition_type__scoring_system='combat') |
            Q(category__isnull=True)  # Inclure les équipes sans catégorie pour ne pas les perdre
        ).select_related('category', 'category__competition_type', 'club').order_by('nom')
        context = {
            'equipes': equipes,
            'competition': competition
        }
        return render(request, 'competitions/combat/liste_equipes.html', context)
    else:
        # Afficher la liste des compétitions avec équipes pour sélection
        # IMPORTANT: Filtrer par organisation de l'utilisateur pour l'isolation multi-tenant
        from apps.organizations.models import OrganizationMember
        from apps.competitions.models import Club

        user_org_ids = set()

        # Via OrganizationMember
        user_org_ids.update(
            OrganizationMember.objects.filter(user=request.user).values_list('organization_id', flat=True)
        )

        # Via Club owner
        user_org_ids.update(
            Club.objects.filter(owner=request.user).values_list('organization_id', flat=True)
        )

        # Filtrer les compétitions par organisation de l'utilisateur
        if user_org_ids:
            competitions = Competition.objects.filter(
                status__in=['draft', 'published', 'ongoing'],
                organizing_organization_id__in=user_org_ids
            ).prefetch_related('equipes_combat').order_by('-start_date')
        else:
            # Si l'utilisateur n'a pas d'organisation, ne montrer aucune compétition
            competitions = Competition.objects.none()

        context = {
            'competitions': competitions,
            'select_competition': True
        }
        return render(request, 'competitions/combat/select_competition_equipes.html', context)


@login_required
def liste_equipes_par_categorie(request, competition_id=None):
    """
    Affiche la liste des équipes ET des inscriptions individuelles groupées par catégorie.
    Permet de voir le nombre d'équipes/participants par catégorie et planifier les combats.
    Si aucune compétition n'est spécifiée, redirige vers la sélection de compétition.
    """
    from apps.competitions.models import Competition, CompetitionCategory, CompetitionRegistration
    from apps.organizations.models import OrganizationMember
    from apps.competitions.models import Club
    from django.db.models import Count, Prefetch

    if not competition_id:
        # Rediriger vers la page de sélection de compétition
        # IMPORTANT: Filtrer par organisation de l'utilisateur pour l'isolation multi-tenant
        user_org_ids = set()

        # Via OrganizationMember
        user_org_ids.update(
            OrganizationMember.objects.filter(user=request.user).values_list('organization_id', flat=True)
        )

        # Via Club owner
        user_org_ids.update(
            Club.objects.filter(owner=request.user).values_list('organization_id', flat=True)
        )

        # Filtrer les compétitions par organisation de l'utilisateur
        if user_org_ids:
            competitions = Competition.objects.filter(
                status__in=['draft', 'published', 'ongoing'],
                organizing_organization_id__in=user_org_ids
            ).prefetch_related('equipes_combat').order_by('-start_date')
        else:
            competitions = Competition.objects.none()

        context = {
            'competitions': competitions,
            'select_competition': True,
            'view_type': 'par_categorie'
        }
        return render(request, 'competitions/combat/select_competition_equipes.html', context)

    context = {}
    competition = get_object_or_404(Competition, id=competition_id)
    context['competition'] = competition

    # Récupérer les catégories avec le nombre d'équipes ET d'inscriptions individuelles
    categories = CompetitionCategory.objects.filter(
        competition=competition
    ).prefetch_related(
        Prefetch(
            'equipes_combat',
            queryset=Equipe.objects.select_related('club').prefetch_related('membres')
        ),
        Prefetch(
            'registrations',
            queryset=CompetitionRegistration.objects.select_related(
                'practitioner', 'practitioner__organization'
            ).filter(competition=competition)
        )
    ).annotate(
        nb_equipes=Count('equipes_combat', distinct=True),
        nb_registrations=Count('registrations', distinct=True)
    ).order_by('name')

    # Équipes sans catégorie assignée
    equipes_sans_categorie = Equipe.objects.filter(
        competition=competition,
        category__isnull=True
    ).select_related('club').prefetch_related('membres')

    # Inscriptions sans catégorie (pratiquants inscrits mais pas encore affectés à une catégorie)
    registrations_sans_categorie = CompetitionRegistration.objects.filter(
        competition=competition,
        categories__isnull=True
    ).select_related('practitioner', 'practitioner__organization').distinct()

    # Filtrer les participants individuels : exclure ceux déjà membres d'une équipe de la catégorie
    for cat in categories:
        team_practitioner_ids = set(
            MembreEquipe.objects.filter(
                equipe__category=cat, equipe__competition=competition
            ).values_list('pratiquant_id', flat=True)
        )
        cat.filtered_registrations = [
            r for r in cat.registrations.all()
            if r.practitioner_id not in team_practitioner_ids
        ]

    # Types de compétition distincts pour les filtres
    from apps.competitions.models import CompetitionType
    competition_types = CompetitionType.objects.filter(
        categories__competition=competition
    ).distinct().order_by('name')

    context['categories'] = categories
    context['competition_types'] = competition_types
    context['equipes_sans_categorie'] = equipes_sans_categorie
    context['registrations_sans_categorie'] = registrations_sans_categorie
    context['total_equipes'] = Equipe.objects.filter(competition=competition).count()
    context['total_registrations'] = CompetitionRegistration.objects.filter(competition=competition).count()

    return render(request, 'competitions/combat/liste_equipes_par_categorie.html', context)


@login_required
def creer_equipe(request, competition_id=None):
    """Permet de créer une nouvelle équipe, avec pré-sélection de la compétition si spécifiée."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.add_equipe'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    from apps.competitions.models import Competition
    
    # Vérifier s'il y a des compétitions disponibles
    available_competitions = Competition.objects.filter(
        status__in=['draft', 'published', 'ongoing']
    )
    
    if not available_competitions.exists():
        messages.warning(request, _("Aucune compétition disponible. Vous devez d'abord créer une compétition."))
    
    initial = {}
    if competition_id:
        competition = get_object_or_404(Competition, id=competition_id)
        initial['competition'] = competition
    category_id = request.GET.get('category')
    if category_id:
        from apps.competitions.models import CompetitionCategory
        try:
            initial['category'] = CompetitionCategory.objects.get(id=category_id)
        except CompetitionCategory.DoesNotExist:
            pass
    
    if request.method == 'POST':
        # Vérifier qu'il y a des compétitions disponibles avant de traiter le formulaire
        if not available_competitions.exists():
            messages.error(request, _("Impossible de créer une équipe : aucune compétition disponible."))
            form = EquipeForm(initial=initial)
        else:
            form = EquipeForm(request.POST)
            if form.is_valid():
                # Vérifier explicitement que la compétition est sélectionnée
                if not form.cleaned_data.get('competition'):
                    messages.error(request, _("Vous devez sélectionner une compétition."))
                else:
                    equipe = form.save()
                    messages.success(request, _("L'équipe a été créée avec succès."))
                    return redirect('competitions:combat:detail_equipe', equipe_id=equipe.id)
            else:
                # Afficher les erreurs du formulaire
                for field, errors in form.errors.items():
                    field_label = form.fields.get(field, {}).get('label', field) if hasattr(form.fields.get(field, {}), 'get') else field
                    for error in errors:
                        messages.error(request, f"{field_label}: {error}")
    else:
        form = EquipeForm(initial=initial)
    
    return render(request, 'competitions/combat/form_equipe.html', {
        'form': form,
        'title': _("Créer une équipe"),
        'has_competitions': available_competitions.exists()
    })

@login_required
def detail_equipe(request, equipe_id):
    """
    Affiche les détails d'une équipe, y compris ses membres.
    """
    equipe = get_object_or_404(Equipe, id=equipe_id)
    membres = MembreEquipe.objects.filter(equipe=equipe).order_by('ordre', '-est_remplacant')
    
    context = {
        'equipe': equipe,
        'membres': membres,
        'titulaires': membres.filter(est_remplacant=False).count(),
        'remplacants': membres.filter(est_remplacant=True).count()
    }
    
    return render(request, 'competitions/combat/detail_equipe.html', context)

@login_required
def modifier_equipe(request, equipe_id):
    """Permet de modifier une équipe existante."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.change_equipe'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    equipe = get_object_or_404(Equipe, id=equipe_id)
    
    if request.method == 'POST':
        form = EquipeForm(request.POST, instance=equipe)
        if form.is_valid():
            form.save()
            messages.success(request, _("L'équipe a été modifiée avec succès."))
            return redirect('competitions:combat:detail_equipe', equipe_id=equipe.id)
    else:
        form = EquipeForm(instance=equipe)
    
    return render(request, 'competitions/combat/form_equipe.html', {
        'form': form,
        'equipe': equipe,
        'title': _("Modifier l'équipe")
    })

@login_required
def supprimer_equipe(request, equipe_id):
    """Permet de supprimer une équipe."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.delete_equipe'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    equipe = get_object_or_404(Equipe, id=equipe_id)
    
    if request.method == 'POST':
        competition_id = equipe.competition.id
        equipe.delete()
        messages.success(request, _("L'équipe a été supprimée avec succès."))
        return redirect('competitions:combat:liste_equipes_competition', competition_id=competition_id)
    
    return render(request, 'competitions/combat/confirmer_suppression.html', {
        'object': equipe,
        'title': _("Supprimer l'équipe"),
        'message': _("ÃŠtes-vous sÃ»r de vouloir supprimer cette équipe ? Cette action supprimera également tous les membres associés."),
        'cancel_url': reverse('competitions:combat:detail_equipe', kwargs={'equipe_id': equipe.id})
    })

@login_required
@never_cache
def ajouter_membre_equipe(request, equipe_id):
    """Permet d'ajouter un membre Ã  une équipe."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.add_membreequipe'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    equipe = get_object_or_404(Equipe, id=equipe_id)

    if request.method == 'POST':
        form = MembreEquipeForm(request.POST, initial={'equipe': equipe})
        if form.is_valid():
            membre = form.save(commit=False)
            if MembreEquipe.objects.filter(equipe=equipe, pratiquant=membre.pratiquant).exists():
                form.add_error('pratiquant', _("Ce pratiquant est déjà membre de cette équipe."))
            else:
                membre.equipe = equipe
                membre.save()
                messages.success(request, _("Le membre a été ajouté à l'équipe avec succès."))
                return redirect('competitions:combat:detail_equipe', equipe_id=equipe.id)
    else:
        form = MembreEquipeForm(initial={'equipe': equipe})

    return render(request, 'competitions/combat/form_membre_equipe.html', {
        'form': form,
        'equipe': equipe,
        'title': _("Ajouter un membre à l'équipe")
    })

@login_required
def modifier_membre_equipe(request, membre_id):
    """Permet de modifier le statut d'un membre d'équipe (titulaire/remplaçant, ordre)."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.change_membreequipe'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    membre = get_object_or_404(MembreEquipe, id=membre_id)
    
    if request.method == 'POST':
        form = MembreEquipeForm(request.POST, instance=membre)
        if form.is_valid():
            form.save()
            messages.success(request, _("Le membre de l'équipe a été modifié avec succès."))
            return redirect('competitions:combat:detail_equipe', equipe_id=membre.equipe.id)
    else:
        form = MembreEquipeForm(instance=membre)
    
    return render(request, 'competitions/combat/form_membre_equipe.html', {
        'form': form,
        'membre': membre,
        'equipe': membre.equipe,
        'title': _("Modifier le membre de l'équipe")
    })

@login_required
def supprimer_membre_equipe(request, membre_id):
    """Permet de supprimer un membre d'une équipe."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.delete_membreequipe'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    membre = get_object_or_404(MembreEquipe, id=membre_id)
    equipe_id = membre.equipe.id
    
    if request.method == 'POST':
        membre.delete()
        messages.success(request, _("Le membre a été retiré de l'équipe avec succès."))
        return redirect('competitions:combat:detail_equipe', equipe_id=equipe_id)
    
    return render(request, 'competitions/combat/confirmer_suppression.html', {
        'object': membre,
        'title': _("Retirer le membre de l'équipe"),
        'message': _("ÃŠtes-vous sÃ»r de vouloir retirer ce membre de l'équipe ?"),
        'cancel_url': reverse('competitions:combat:detail_equipe', kwargs={'equipe_id': equipe_id})
    })

# Vues pour la gestion des poules

@login_required
def redirect_poule_legacy(request, id):
    """
    Gère les anciens URLs /poules/<id>/ en redirigeant vers le bon format.
    Vérifie si l'ID correspond à une poule existante ou une compétition.
    """
    # Essayer d'abord de trouver une poule avec cet ID
    poule = Poule.objects.filter(id=id).first()
    if poule:
        return redirect('competitions:combat:detail_poule', poule_id=id)

    # Sinon, vérifier si c'est une compétition
    from apps.competitions.models import Competition
    competition = Competition.objects.filter(id=id).first()
    if competition:
        return redirect('competitions:combat:liste_poules', competition_id=id)

    # Si aucun ne correspond, afficher une erreur 404
    from django.http import Http404
    raise Http404(_("Aucune poule ou compétition trouvée avec cet identifiant."))

@never_cache
@login_required
def liste_poules(request, competition_id):
    """
    Affiche la liste des poules pour une compétition, organisées par catégorie.
    Les poules sont organisées par phase: éliminatoires, demi-finales, finale.
    """
    from apps.competitions.models import Competition, CompetitionCategory, CompetitionType
    from django.db.models import Count, Prefetch

    competition = get_object_or_404(Competition, id=competition_id)

    # Récupérer les poules avec leurs relations
    poules = Poule.objects.filter(competition=competition).select_related(
        'category'
    ).prefetch_related(
        'equipes', 'pratiquants', 'combats'
    ).order_by('category__name', 'phase', 'numero')

    # Organiser les poules par catégorie ET par phase
    poules_par_categorie = {}
    poules_sans_categorie = []

    for poule in poules:
        if poule.category:
            cat_id = poule.category.id
            if cat_id not in poules_par_categorie:
                poules_par_categorie[cat_id] = {
                    'category': poule.category,
                    'poules': [],
                    'poules_eliminatoires': [],
                    'poules_demi': [],
                    'poules_finale': [],
                    'total_equipes': 0,
                    'total_pratiquants': 0,
                    'total_combats': 0,
                    'demi_terminees': False,
                    'finale_prete': False,
                }
            poules_par_categorie[cat_id]['poules'].append(poule)

            # Classer les poules par phase
            phase_lower = (poule.phase or 'eliminatoire').lower()
            if phase_lower == 'finale':
                poules_par_categorie[cat_id]['poules_finale'].append(poule)
                # Vérifier si la finale a des combats
                if poule.combats.exists():
                    poules_par_categorie[cat_id]['finale_prete'] = True
            elif phase_lower in ('demi', 'demi_finale'):
                poules_par_categorie[cat_id]['poules_demi'].append(poule)
                # Vérifier si les demi-finales sont terminées
                combats_demi = poule.combats.all()
                if combats_demi.count() >= 2 and all(c.status == 'termine' for c in combats_demi):
                    poules_par_categorie[cat_id]['demi_terminees'] = True
            elif phase_lower == 'quart':
                # Les quarts sont considérés comme éliminatoires avancés
                poules_par_categorie[cat_id]['poules_eliminatoires'].append(poule)
            else:
                # Phase éliminatoire par défaut
                poules_par_categorie[cat_id]['poules_eliminatoires'].append(poule)

            poules_par_categorie[cat_id]['total_equipes'] += poule.equipes.count()
            poules_par_categorie[cat_id]['total_pratiquants'] += poule.pratiquants.count()
            poules_par_categorie[cat_id]['total_combats'] += poule.combats.count()
        else:
            poules_sans_categorie.append(poule)

    # Calculer les stats globales
    total_poules = poules.count()
    total_combats = sum(p.combats.count() for p in poules)
    total_equipes = sum(p.equipes.count() for p in poules)
    total_pratiquants = sum(p.pratiquants.count() for p in poules)

    # Récupérer les types de compétition "combat" (scoring_system='combat' ou 'mixed')
    # Ce sont les seuls types qui ont besoin de poules
    combat_competition_types = CompetitionType.objects.filter(
        competitions=competition,
        scoring_system__in=['combat', 'mixed']
    ).distinct()

    # Prepare categories by type for per-category pool generation modal
    import json as _json
    categories_by_type = {}
    for _ct in combat_competition_types:
        _cats = CompetitionCategory.objects.filter(
            competition=competition,
            competition_type=_ct
        ).order_by('name').values('id', 'name')
        categories_by_type[str(_ct.id)] = {
            'type_name': _ct.name,
            'categories': list(_cats)
        }

    return render(request, 'competitions/combat/liste_poules.html', {
        'competition': competition,
        'poules': poules,
        'poules_par_categorie': list(poules_par_categorie.values()),
        'poules_sans_categorie': poules_sans_categorie,
        'total_poules': total_poules,
        'total_combats': total_combats,
        'total_equipes': total_equipes,
        'total_pratiquants': total_pratiquants,
        'combat_competition_types': combat_competition_types,
        'categories_by_type_json': _json.dumps(categories_by_type),
    })

@login_required
def creer_poule(request, competition_id):
    """Permet de créer une nouvelle poule pour une compétition."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.add_poule'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    from apps.competitions.models import Competition
    competition = get_object_or_404(Competition, id=competition_id)
    
    if request.method == 'POST':
        form = PouleForm(request.POST)
        if form.is_valid():
            poule = form.save(commit=False)
            poule.competition = competition
            poule.save()
            
            # Enregistrer les relations ManyToMany
            form.save_m2m()
            
            messages.success(request, _("La poule a été créée avec succès."))
            return redirect('competitions:combat:detail_poule', poule_id=poule.id)
    else:
        # Prérégler le numéro de poule au nombre actuel + 1
        next_num = Poule.objects.filter(competition=competition).count() + 1
        form = PouleForm(initial={
            'competition': competition,
            'numero': next_num,
            'nom': f"Poule {next_num}"
        })
    
    return render(request, 'competitions/combat/form_poule.html', {
        'form': form,
        'competition': competition,
        'title': _("Créer une poule")
    })

@login_required
def detail_poule(request, poule_id):
    """
    Affiche les détails d'une poule, y compris les équipes/participants et les combats.
    """
    poule = get_object_or_404(Poule, id=poule_id)
    combats = Combat.objects.filter(poule=poule).select_related(
        'equipe_rouge', 'equipe_rouge__club',
        'equipe_blanc', 'equipe_blanc__club',
        'pratiquant_rouge', 'pratiquant_rouge__organization',
        'pratiquant_blanc', 'pratiquant_blanc__organization',
    ).order_by('date_planifiee')
    
    # Calculer les statistiques
    total_combats = combats.count()
    combats_termines = combats.filter(status='termine').count()
    combats_en_cours = combats.filter(status='en_cours').count()
    combats_planifies = combats.filter(status='planifie').count()
    
    return render(request, 'competitions/combat/detail_poule.html', {
        'poule': poule,
        'combats': combats,
        'equipes': poule.equipes.all().prefetch_related('memberships__pratiquant'),
        'pratiquants': poule.pratiquants.all(),
        'total_combats': total_combats,
        'combats_termines': combats_termines,
        'combats_en_cours': combats_en_cours,
        'combats_planifies': combats_planifies,
    })

@login_required
def modifier_poule(request, poule_id):
    """Permet de modifier une poule existante."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.change_poule'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    poule = get_object_or_404(Poule, id=poule_id)
    
    if request.method == 'POST':
        form = PouleForm(request.POST, instance=poule)
        if form.is_valid():
            form.save()
            messages.success(request, _("La poule a été modifiée avec succès."))
            return redirect('competitions:combat:detail_poule', poule_id=poule.id)
    else:
        form = PouleForm(instance=poule)
    
    return render(request, 'competitions/combat/form_poule.html', {
        'form': form,
        'poule': poule,
        'competition': poule.competition,
        'title': _("Modifier la poule")
    })

@login_required
def supprimer_poule(request, poule_id):
    """Permet de supprimer une poule."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.delete_poule'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    poule = get_object_or_404(Poule, id=poule_id)
    competition_id = poule.competition.id
    
    if request.method == 'POST':
        poule.delete()
        messages.success(request, _("La poule a été supprimée avec succès."))
        return redirect('competitions:combat:liste_poules', competition_id=competition_id)
    
    return render(request, 'competitions/combat/confirmer_suppression.html', {
        'object': poule,
        'title': _("Supprimer la poule"),
        'message': _("ÃŠtes-vous sÃ»r de vouloir supprimer cette poule ? Cette action supprimera également tous les combats associés."),
        'cancel_url': reverse('competitions:combat:detail_poule', kwargs={'poule_id': poule.id})
    })

@login_required
def generer_poules(request, competition_id):
    """
    Génère automatiquement des poules pour chaque catégorie combat d'une compétition.

    DEUX MODES DISPONIBLES:
    - standard: Round-robin complet (chaque équipe contre toutes les autres)
    - qualificatif: Chaque équipe fait minimum 2 combats, puis demi-finales et finale

    FILTRAGE PAR TYPE DE COMPÉTITION:
    - Seuls les types 'combat' ou 'mixed' peuvent avoir des poules
    - Les types 'technical' ne génèrent pas de poules

    Analyse chaque catégorie et crée des poules en fonction du nombre d'équipes ou de participants.
    """
    # Verifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.add_poule'):
        messages.error(request, _("Vous n'avez pas les permissions necessaires pour cette action."))
        return redirect('competitions:dashboard:index')

    from apps.competitions.models import Competition, CompetitionCategory, CompetitionRegistration, CompetitionType
    competition = get_object_or_404(Competition, id=competition_id)

    # Récupérer le mode de génération (standard ou qualificatif)
    mode = request.GET.get('mode', 'standard')  # 'standard' ou 'qualificatif'
    combat_mode = request.GET.get('combat_mode', 'auto')  # mode global par défaut
    eviter_clubs = True  # Par défaut, éviter les clubs dans la même poule

    # Modes de combat par catégorie (prioritaire sur le mode global)
    category_modes = {}
    for key, value in request.GET.items():
        if key.startswith('cat_mode_'):
            cat_id = key[len('cat_mode_'):]
            if value in ('auto', 'equipe', 'individuel'):
                category_modes[cat_id] = value

    # Récupérer les types de compétition sélectionnés (paramètre 'types')
    # Si aucun type spécifié, utiliser tous les types 'combat' et 'mixed' de la compétition
    selected_type_ids = request.GET.getlist('types')

    if selected_type_ids:
        # Filtrer par les types sélectionnés par l'utilisateur
        selected_types = CompetitionType.objects.filter(
            id__in=selected_type_ids,
            competitions=competition,
            scoring_system__in=['combat', 'mixed']  # Sécurité: ne permettre que combat/mixed
        )
    else:
        # Par défaut: tous les types combat/mixed de cette compétition
        selected_types = CompetitionType.objects.filter(
            competitions=competition,
            scoring_system__in=['combat', 'mixed']
        )

    selected_type_ids_set = set(selected_types.values_list('id', flat=True))

    if not selected_type_ids_set:
        messages.warning(request, _("Aucun type de compétition 'Combat' trouvé. Les compétitions techniques ne nécessitent pas de poules."))
        return redirect('competitions:combat:liste_poules', competition_id=competition.id)

    # Supprimer uniquement les poules des catégories liées aux types sélectionnés
    Poule.objects.filter(
        competition=competition,
        category__competition_type__id__in=selected_type_ids_set
    ).delete()

    total_poules = 0
    total_combats = 0
    categories_traitees = 0

    # Récupérer uniquement les catégories liées aux types de compétition sélectionnés
    categories = CompetitionCategory.objects.filter(
        competition=competition,
        competition_type__id__in=selected_type_ids_set
    ).prefetch_related('equipes_combat', 'registrations').select_related('competition_type')

    for category in categories:
        # Compter les équipes dans cette catégorie (ou sans catégorie assignée)
        from django.db.models import Q
        equipes = list(Equipe.objects.filter(
            competition=competition,
            is_active=True
        ).filter(
            Q(category=category) | Q(category__isnull=True)
        ).select_related('club'))

        # Compter les participants individuels (inscriptions dans cette catégorie)
        participants = list(CompetitionRegistration.objects.filter(
            competition=competition,
            categories=category
        ).select_related('practitioner'))

        nb_equipes = len(equipes)
        nb_participants = len(participants)

        # Auto-assigner la catégorie aux équipes qui n'en ont pas
        for eq in equipes:
            if eq.category_id is None:
                eq.category = category
                eq.save(update_fields=['category'])

        # Si pas d'équipes ni de participants, passer à la catégorie suivante
        if nb_equipes == 0 and nb_participants == 0:
            continue

        categories_traitees += 1

        # Mode de combat pour cette catégorie (spécifique ou global)
        cat_combat_mode = category_modes.get(str(category.id), combat_mode)

        # Déterminer le mode de combat selon le choix de l'utilisateur
        if cat_combat_mode == 'equipe':
            # Mode équipe forcé : utiliser les équipes existantes
            if nb_equipes > 0:
                nb_elements = nb_equipes
                elements = equipes
                is_team_mode = True
            else:
                # Aucune équipe dans la compétition, impossible de générer en mode équipe
                continue
        elif cat_combat_mode == 'individuel':
            # Mode individuel forcé: utiliser les participants même si des équipes existent
            if nb_participants > 0:
                nb_elements = nb_participants
                elements = participants
                is_team_mode = False
            elif nb_equipes > 0:
                # Pas de participants individuels, fallback sur équipes
                nb_elements = nb_equipes
                elements = equipes
                is_team_mode = True
            else:
                continue
        else:
            # Mode auto: détecter automatiquement (comportement d'origine)
            if nb_equipes > 0:
                nb_elements = nb_equipes
                elements = equipes
                is_team_mode = True
            else:
                nb_elements = nb_participants
                elements = participants
                is_team_mode = False

        # === MODE QUALIFICATIF ===
        # Moins de combats: chaque équipe fait 2 combats minimum, puis demi/finale
        if mode == 'qualificatif':
            poules_count, combats_count = _generer_poules_mode_qualificatif(
                competition, category, elements, is_team_mode, eviter_clubs
            )
            total_poules += poules_count
            total_combats += combats_count
            continue

        # === MODE STANDARD (round-robin complet) ===
        # Algorithme de détermination du nombre de poules
        if nb_elements <= 4:
            nombre_poules = 1  # Une seule poule
        elif nb_elements <= 8:
            nombre_poules = 2  # 2 poules
        elif nb_elements <= 12:
            nombre_poules = 3  # 3 poules
        elif nb_elements <= 16:
            nombre_poules = 4  # 4 poules
        else:
            nombre_poules = max(4, nb_elements // 4)  # 4+ éléments par poule

        # Distribution intelligente pour éviter les clubs dans la même poule
        if eviter_clubs and is_team_mode:
            elements = _distribuer_equipes_intelligent(elements, nombre_poules, True, False)
        else:
            random.shuffle(elements)

        # Créer les poules pour cette catégorie
        poules_categorie = []
        for i in range(nombre_poules):
            poule = Poule.objects.create(
                competition=competition,
                category=category,
                nom=f"Poule {chr(65 + i)}",
                numero=i + 1,
                phase='eliminatoire',
                description=f"Catégorie: {category.name}"
            )
            poules_categorie.append(poule)
            total_poules += 1

        # Distribution round-robin des éléments dans les poules
        for idx, element in enumerate(elements):
            poule_index = idx % nombre_poules
            if is_team_mode:
                poules_categorie[poule_index].equipes.add(element)
            else:
                poules_categorie[poule_index].pratiquants.add(element.practitioner)

        # Générer les combats pour chaque poule
        for poule in poules_categorie:
            if is_team_mode:
                total_combats += _generer_combats_poule(poule)
            else:
                total_combats += _generer_combats_poule_individuel(poule)

    if categories_traitees > 0:
        mode_label = _("Mode Qualificatif (rapide)") if mode == 'qualificatif' else _("Mode Standard (round-robin)")
        combat_mode_label = _("Équipe") if combat_mode == 'equipe' else _("Individuel") if combat_mode == 'individuel' else _("Auto")
        types_names = ", ".join([t.name for t in selected_types])
        messages.success(
            request,
            _("{} poules créées dans {} catégories avec {} combats générés. {} - Combat: {} - Types: {}").format(
                total_poules, categories_traitees, total_combats, mode_label, combat_mode_label, types_names
            )
        )
    else:
        messages.warning(request, _("Aucune catégorie avec des équipes ou participants trouvée pour les types sélectionnés."))

    return redirect('competitions:combat:liste_poules', competition_id=competition.id)


def _generer_poules_mode_qualificatif(competition, category, elements, is_team_mode, eviter_clubs):
    """
    MODE QUALIFICATIF: Génère des poules avec moins de combats.

    Principe:
    - Chaque équipe fait MINIMUM 2 combats en phase éliminatoire
    - Les 2 meilleurs de chaque poule vont en demi-finale
    - Puis finale

    Algorithme:
    - 2-4 équipes: 1 poule, round-robin (tous contre tous)
    - 5-8 équipes: 2 poules de 3-4, chaque équipe fait 2-3 combats
    - 9-16 équipes: 4 poules de 3-4, chaque équipe fait 2-3 combats
    - 17+ équipes: N poules de 4 max

    Retourne (nombre_poules, nombre_combats)
    """
    nb_elements = len(elements)
    total_poules = 0
    total_combats = 0

    if nb_elements < 2:
        return 0, 0

    # Déterminer le nombre optimal de poules pour le mode qualificatif
    if nb_elements <= 4:
        nombre_poules = 1
    elif nb_elements <= 8:
        nombre_poules = 2
    elif nb_elements <= 16:
        nombre_poules = 4
    else:
        # Pour plus de 16, on fait des poules de 4 maximum
        nombre_poules = (nb_elements + 3) // 4

    # Distribution intelligente
    if eviter_clubs and is_team_mode:
        elements = _distribuer_equipes_intelligent(elements, nombre_poules, True, False)
    else:
        random.shuffle(elements)

    # Créer les poules éliminatoires
    poules_categorie = []
    for i in range(nombre_poules):
        poule = Poule.objects.create(
            competition=competition,
            category=category,
            nom=f"Poule {chr(65 + i)}",
            numero=i + 1,
            phase='eliminatoire',
            description=f"Catégorie: {category.name} - Mode Qualificatif"
        )
        poules_categorie.append(poule)
        total_poules += 1

    # Distribution des éléments dans les poules
    for idx, element in enumerate(elements):
        poule_index = idx % nombre_poules
        if is_team_mode:
            poules_categorie[poule_index].equipes.add(element)
        else:
            poules_categorie[poule_index].pratiquants.add(element.practitioner if hasattr(element, 'practitioner') else element)

    # Générer les combats en mode qualificatif (2 combats minimum par équipe)
    for poule in poules_categorie:
        if is_team_mode:
            total_combats += _generer_combats_qualificatif_equipe(poule)
        else:
            total_combats += _generer_combats_qualificatif_individuel(poule)

    return total_poules, total_combats


def _generer_combats_qualificatif_equipe(poule):
    """
    Génère les combats pour une poule en mode qualificatif (équipes).

    Règle: Chaque équipe doit faire MINIMUM 2 combats.

    Si 3 équipes: A vs B, B vs C, A vs C (3 combats, chacun fait 2)
    Si 4 équipes: A vs B, C vs D, A vs C, B vs D (4 combats, chacun fait 2)
    Si 5+ équipes: Round-robin limité pour garantir 2 combats minimum
    """
    equipes = list(poule.equipes.all())
    nb_equipes = len(equipes)
    combats_crees = 0

    if nb_equipes < 2:
        return 0

    if nb_equipes == 2:
        # 2 équipes: 1 seul combat
        Combat.objects.create(
            competition=poule.competition,
            poule=poule,
            equipe_rouge=equipes[0],
            equipe_blanc=equipes[1],
            status='planifie',
            type_combat='equipe',
            duree_combat=getattr(poule, 'category', None) and getattr(poule.category, 'combat_duration', 120) or 120,
                    duree_prolongation=getattr(poule, 'category', None) and getattr(poule.category, 'combat_extra_time', 0) or 0
        )
        return 1

    if nb_equipes == 3:
        # 3 équipes: round-robin complet (3 combats, chacun fait 2)
        matchups = [(0, 1), (1, 2), (0, 2)]
        for i, j in matchups:
            Combat.objects.create(
                competition=poule.competition,
                poule=poule,
                equipe_rouge=equipes[i],
                equipe_blanc=equipes[j],
                status='planifie',
                type_combat='equipe',
                duree_combat=getattr(poule, 'category', None) and getattr(poule.category, 'combat_duration', 120) or 120,
                    duree_prolongation=getattr(poule, 'category', None) and getattr(poule.category, 'combat_extra_time', 0) or 0
            )
            combats_crees += 1
        return combats_crees

    if nb_equipes == 4:
        # 4 équipes: système croisé (4 combats, chacun fait 2)
        # A vs B, C vs D, A vs C, B vs D
        matchups = [(0, 1), (2, 3), (0, 2), (1, 3)]
        for i, j in matchups:
            Combat.objects.create(
                competition=poule.competition,
                poule=poule,
                equipe_rouge=equipes[i],
                equipe_blanc=equipes[j],
                status='planifie',
                type_combat='equipe',
                duree_combat=getattr(poule, 'category', None) and getattr(poule.category, 'combat_duration', 120) or 120,
                    duree_prolongation=getattr(poule, 'category', None) and getattr(poule.category, 'combat_extra_time', 0) or 0
            )
            combats_crees += 1
        return combats_crees

    # 5+ équipes: système garantissant 2 combats minimum par équipe
    # On utilise un algorithme de tournoi circulaire limité
    combats_par_equipe = {e.id: 0 for e in equipes}
    combats_crees_set = set()

    # D'abord, assurer que chaque équipe a au moins 2 combats
    for i, equipe in enumerate(equipes):
        adversaires = [eq for eq in equipes if eq.id != equipe.id]
        for adversaire in adversaires:
            if combats_par_equipe[equipe.id] >= 2:
                break

            pair = tuple(sorted([equipe.id, adversaire.id]))
            if pair not in combats_crees_set:
                Combat.objects.create(
                    competition=poule.competition,
                    poule=poule,
                    equipe_rouge=equipe,
                    equipe_blanc=adversaire,
                    status='planifie',
                    type_combat='equipe',
                    duree_combat=getattr(poule, 'category', None) and getattr(poule.category, 'combat_duration', 120) or 120,
                    duree_prolongation=getattr(poule, 'category', None) and getattr(poule.category, 'combat_extra_time', 0) or 0
                )
                combats_crees_set.add(pair)
                combats_par_equipe[equipe.id] += 1
                combats_par_equipe[adversaire.id] += 1
                combats_crees += 1

    return combats_crees


def _generer_combats_qualificatif_individuel(poule):
    """
    Génère les combats pour une poule en mode qualificatif (individuel).
    Même logique que pour les équipes mais avec des pratiquants.
    """
    pratiquants = list(poule.pratiquants.all())
    nb_pratiquants = len(pratiquants)
    combats_crees = 0

    if nb_pratiquants < 2:
        return 0

    if nb_pratiquants == 2:
        Combat.objects.create(
            competition=poule.competition,
            poule=poule,
            pratiquant_rouge=pratiquants[0],
            pratiquant_blanc=pratiquants[1],
            status='planifie',
            type_combat='individuel',
            duree_combat=getattr(poule, 'category', None) and getattr(poule.category, 'combat_duration', 120) or 120,
                    duree_prolongation=getattr(poule, 'category', None) and getattr(poule.category, 'combat_extra_time', 0) or 0
        )
        return 1

    if nb_pratiquants == 3:
        matchups = [(0, 1), (1, 2), (0, 2)]
        for i, j in matchups:
            Combat.objects.create(
                competition=poule.competition,
                poule=poule,
                pratiquant_rouge=pratiquants[i],
                pratiquant_blanc=pratiquants[j],
                status='planifie',
                type_combat='individuel',
                duree_combat=getattr(poule, 'category', None) and getattr(poule.category, 'combat_duration', 120) or 120,
                    duree_prolongation=getattr(poule, 'category', None) and getattr(poule.category, 'combat_extra_time', 0) or 0
            )
            combats_crees += 1
        return combats_crees

    if nb_pratiquants == 4:
        matchups = [(0, 1), (2, 3), (0, 2), (1, 3)]
        for i, j in matchups:
            Combat.objects.create(
                competition=poule.competition,
                poule=poule,
                pratiquant_rouge=pratiquants[i],
                pratiquant_blanc=pratiquants[j],
                status='planifie',
                type_combat='individuel',
                duree_combat=getattr(poule, 'category', None) and getattr(poule.category, 'combat_duration', 120) or 120,
                    duree_prolongation=getattr(poule, 'category', None) and getattr(poule.category, 'combat_extra_time', 0) or 0
            )
            combats_crees += 1
        return combats_crees

    # 5+ pratiquants
    combats_par_prat = {p.id: 0 for p in pratiquants}
    combats_crees_set = set()

    for i, prat in enumerate(pratiquants):
        adversaires = [p for p in pratiquants if p.id != prat.id]
        for adversaire in adversaires:
            if combats_par_prat[prat.id] >= 2:
                break

            pair = tuple(sorted([prat.id, adversaire.id]))
            if pair not in combats_crees_set:
                Combat.objects.create(
                    competition=poule.competition,
                    poule=poule,
                    pratiquant_rouge=prat,
                    pratiquant_blanc=adversaire,
                    status='planifie',
                    type_combat='individuel',
                    duree_combat=getattr(poule, 'category', None) and getattr(poule.category, 'combat_duration', 120) or 120,
                    duree_prolongation=getattr(poule, 'category', None) and getattr(poule.category, 'combat_extra_time', 0) or 0
                )
                combats_crees_set.add(pair)
                combats_par_prat[prat.id] += 1
                combats_par_prat[adversaire.id] += 1
                combats_crees += 1

    return combats_crees


@login_required
def reset_poules(request, competition_id):
    """Supprime toutes les poules et combats associés d'une compétition."""
    if not manual_permission_check(request.user, 'competitions.delete_poule'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')

    from apps.competitions.models import Competition
    competition = get_object_or_404(Competition, id=competition_id)

    if request.method == 'POST':
        # Supprimer tous les combats associés aux poules
        Combat.objects.filter(poule__competition=competition).delete()
        # Supprimer toutes les poules
        nb_deleted = Poule.objects.filter(competition=competition).delete()[0]

        messages.success(request, _("{} poules et leurs combats ont été supprimés.").format(nb_deleted))
        return redirect('competitions:combat:liste_poules', competition_id=competition.id)

    # GET: Confirmation
    nb_poules = Poule.objects.filter(competition=competition).count()
    nb_combats = Combat.objects.filter(poule__competition=competition).count()

    return render(request, 'competitions/combat/confirm_reset_poules.html', {
        'competition': competition,
        'nb_poules': nb_poules,
        'nb_combats': nb_combats,
        'title': _("Réinitialiser les poules")
    })


@login_required
def supprimer_poules_categorie(request, competition_id, category_id):
    """Supprime toutes les poules et combats d'une catégorie spécifique."""
    if not manual_permission_check(request.user, 'competitions.delete_poule'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')

    from apps.competitions.models import Competition, CompetitionCategory
    competition = get_object_or_404(Competition, id=competition_id)
    category = get_object_or_404(CompetitionCategory, id=category_id)

    if request.method == 'POST':
        # Supprimer tous les combats associés aux poules de cette catégorie
        Combat.objects.filter(poule__competition=competition, poule__category=category).delete()
        # Supprimer toutes les poules de cette catégorie
        nb_deleted = Poule.objects.filter(competition=competition, category=category).delete()[0]

        messages.success(request, _("Les {} poule(s) de la catégorie '{}' et leurs combats ont été supprimés.").format(nb_deleted, category.name))
        return redirect('competitions:combat:liste_poules', competition_id=competition.id)

    # GET: Confirmation via AJAX ou simple redirect pour éviter une page supplémentaire
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        nb_poules = Poule.objects.filter(competition=competition, category=category).count()
        nb_combats = Combat.objects.filter(poule__competition=competition, poule__category=category).count()
        return JsonResponse({
            'category_name': category.name,
            'nb_poules': nb_poules,
            'nb_combats': nb_combats
        })

    # Si GET direct, rediriger vers la liste avec un message
    messages.warning(request, _("Utilisez le bouton de suppression pour retirer une catégorie."))
    return redirect('competitions:combat:liste_poules', competition_id=competition.id)


@login_required
def reorganiser_poules(request, competition_id):
    """
    Interface de réorganisation manuelle des poules.
    Permet de déplacer des équipes/participants entre les poules d'une même catégorie.
    """
    if not manual_permission_check(request.user, 'competitions.change_poule'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')

    from apps.competitions.models import Competition, CompetitionCategory
    competition = get_object_or_404(Competition, id=competition_id)

    if request.method == 'POST':
        # Traiter les modifications
        action = request.POST.get('action')

        if action == 'move_team':
            # Déplacer une équipe d'une poule à une autre
            equipe_id = request.POST.get('equipe_id')
            source_poule_id = request.POST.get('source_poule_id')
            target_poule_id = request.POST.get('target_poule_id')

            if equipe_id and source_poule_id and target_poule_id:
                try:
                    equipe = Equipe.objects.get(id=equipe_id)
                    source_poule = Poule.objects.get(id=source_poule_id)
                    target_poule = Poule.objects.get(id=target_poule_id)

                    # Vérifier que les poules sont de la même catégorie
                    if source_poule.category != target_poule.category:
                        return JsonResponse({
                            'success': False,
                            'error': _("Les poules doivent être de la même catégorie")
                        })

                    # Supprimer les combats impliquant cette équipe dans la poule source
                    Combat.objects.filter(
                        poule=source_poule
                    ).filter(
                        Q(equipe_rouge=equipe) | Q(equipe_blanc=equipe)
                    ).delete()

                    # Déplacer l'équipe
                    source_poule.equipes.remove(equipe)
                    target_poule.equipes.add(equipe)

                    # Générer les nouveaux combats pour l'équipe dans la poule cible
                    _regenerer_combats_pour_equipe(target_poule, equipe)

                    return JsonResponse({
                        'success': True,
                        'message': _("Équipe déplacée avec succès")
                    })
                except (Equipe.DoesNotExist, Poule.DoesNotExist) as e:
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    })

        elif action == 'move_practitioner':
            # Déplacer un pratiquant d'une poule à une autre
            practitioner_id = request.POST.get('practitioner_id')
            source_poule_id = request.POST.get('source_poule_id')
            target_poule_id = request.POST.get('target_poule_id')

            if practitioner_id and source_poule_id and target_poule_id:
                try:
                    from apps.competitions.models import Practitioner
                    practitioner = Practitioner.objects.get(id=practitioner_id)
                    source_poule = Poule.objects.get(id=source_poule_id)
                    target_poule = Poule.objects.get(id=target_poule_id)

                    # Vérifier que les poules sont de la même catégorie
                    if source_poule.category != target_poule.category:
                        return JsonResponse({
                            'success': False,
                            'error': _("Les poules doivent être de la même catégorie")
                        })

                    # Supprimer les combats impliquant ce pratiquant
                    Combat.objects.filter(
                        poule=source_poule
                    ).filter(
                        Q(pratiquant_rouge=practitioner) | Q(pratiquant_blanc=practitioner)
                    ).delete()

                    # Déplacer le pratiquant
                    source_poule.pratiquants.remove(practitioner)
                    target_poule.pratiquants.add(practitioner)

                    # Générer les nouveaux combats
                    _regenerer_combats_pour_pratiquant(target_poule, practitioner)

                    return JsonResponse({
                        'success': True,
                        'message': _("Pratiquant déplacé avec succès")
                    })
                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    })

        elif action == 'regenerate_combats':
            # Régénérer tous les combats d'une poule
            poule_id = request.POST.get('poule_id')
            if poule_id:
                try:
                    poule = Poule.objects.get(id=poule_id)
                    # Supprimer les combats existants
                    Combat.objects.filter(poule=poule).delete()
                    # Regénérer les combats
                    if poule.equipes.exists():
                        nb_combats = _generer_combats_poule(poule)
                    else:
                        nb_combats = _generer_combats_poule_individuel(poule)

                    return JsonResponse({
                        'success': True,
                        'message': _("{} combats générés").format(nb_combats)
                    })
                except Poule.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': _("Poule introuvable")
                    })

        return JsonResponse({'success': False, 'error': _("Action non reconnue")})

    # GET: Afficher l'interface de réorganisation
    # Organiser les poules par catégorie
    poules_par_categorie = []
    categories = CompetitionCategory.objects.filter(
        competition=competition
    ).distinct()

    for category in categories:
        poules = Poule.objects.filter(
            competition=competition,
            category=category
        ).prefetch_related('equipes', 'equipes__club', 'pratiquants')

        if poules.exists():
            poules_par_categorie.append({
                'category': category,
                'poules': poules,
                'is_team_mode': poules.first().equipes.exists()
            })

    return render(request, 'competitions/combat/reorganiser_poules.html', {
        'competition': competition,
        'poules_par_categorie': poules_par_categorie,
        'title': _("Réorganiser les poules")
    })


def _regenerer_combats_pour_equipe(poule, equipe):
    """
    Génère les combats pour une équipe nouvellement ajoutée à une poule.
    L'équipe affronte toutes les autres équipes de la poule.
    """
    autres_equipes = poule.equipes.exclude(id=equipe.id)

    for autre_equipe in autres_equipes:
        # Vérifier si le combat existe déjà
        combat_exists = Combat.objects.filter(
            poule=poule,
            equipe_rouge=equipe,
            equipe_blanc=autre_equipe
        ).exists() or Combat.objects.filter(
            poule=poule,
            equipe_rouge=autre_equipe,
            equipe_blanc=equipe
        ).exists()

        if not combat_exists:
            Combat.objects.create(
                competition=poule.competition,
                poule=poule,
                equipe_rouge=equipe,
                equipe_blanc=autre_equipe,
                status='planifie',
                type_combat='equipe',
                duree_combat=getattr(poule, 'category', None) and getattr(poule.category, 'combat_duration', 120) or 120,
                    duree_prolongation=getattr(poule, 'category', None) and getattr(poule.category, 'combat_extra_time', 0) or 0
            )


def _regenerer_combats_pour_pratiquant(poule, practitioner):
    """
    Génère les combats pour un pratiquant nouvellement ajouté à une poule.
    Le pratiquant affronte tous les autres pratiquants de la poule.
    """
    autres_pratiquants = poule.pratiquants.exclude(id=practitioner.id)

    for autre_prat in autres_pratiquants:
        # Vérifier si le combat existe déjà
        combat_exists = Combat.objects.filter(
            poule=poule,
            pratiquant_rouge=practitioner,
            pratiquant_blanc=autre_prat
        ).exists() or Combat.objects.filter(
            poule=poule,
            pratiquant_rouge=autre_prat,
            pratiquant_blanc=practitioner
        ).exists()

        if not combat_exists:
            Combat.objects.create(
                competition=poule.competition,
                poule=poule,
                pratiquant_rouge=practitioner,
                pratiquant_blanc=autre_prat,
                status='planifie',
                type_combat='individuel',
                duree_combat=getattr(poule, 'category', None) and getattr(poule.category, 'combat_duration', 120) or 120,
                    duree_prolongation=getattr(poule, 'category', None) and getattr(poule.category, 'combat_extra_time', 0) or 0
            )


def _generer_combats_poule_individuel(poule):
    """
    Génère tous les combats d'une poule en mode individuel.
    Chaque pratiquant affronte chaque autre pratiquant.
    """
    pratiquants = list(poule.pratiquants.all())
    combats_crees = 0

    if len(pratiquants) < 2:
        return 0

    for i, prat_rouge in enumerate(pratiquants):
        for prat_blanc in pratiquants[i + 1:]:
            # Vérifier si le combat existe déjà
            combat_exists = Combat.objects.filter(
                poule=poule,
                pratiquant_rouge=prat_rouge,
                pratiquant_blanc=prat_blanc
            ).exists() or Combat.objects.filter(
                poule=poule,
                pratiquant_rouge=prat_blanc,
                pratiquant_blanc=prat_rouge
            ).exists()

            if not combat_exists:
                Combat.objects.create(
                    competition=poule.competition,
                    poule=poule,
                    pratiquant_rouge=prat_rouge,
                    pratiquant_blanc=prat_blanc,
                    status='planifie',
                    type_combat='individuel',
                    duree_combat=getattr(poule, 'category', None) and getattr(poule.category, 'combat_duration', 120) or 120,
                    duree_prolongation=getattr(poule, 'category', None) and getattr(poule.category, 'combat_extra_time', 0) or 0
                )
                combats_crees += 1

    return combats_crees


def _distribuer_equipes_intelligent(equipes_list, nombre_poules, eviter_clubs, eviter_pays):
    """
    BUG #8 FIX: Algorithme intelligent de distribution des equipes.
    Essaie d'eviter de placer des equipes du meme club/pays dans la meme poule.
    """
    by_club = {}

    for equipe in equipes_list:
        club_id = getattr(equipe, 'club_id', None) or 'no_club'
        if club_id not in by_club:
            by_club[club_id] = []
        by_club[club_id].append(equipe)

    sorted_equipes = []

    if eviter_clubs:
        clubs_sorted = sorted(by_club.values(), key=len, reverse=True)
        max_len = max(len(club) for club in clubs_sorted) if clubs_sorted else 0

        for i in range(max_len):
            for club_equipes in clubs_sorted:
                if i < len(club_equipes):
                    sorted_equipes.append(club_equipes[i])
    else:
        sorted_equipes = equipes_list.copy()
        random.shuffle(sorted_equipes)

    return sorted_equipes


def _generer_combats_poule(poule):
    """
    BUG #8 FIX: Genere tous les combats d'une poule (chaque equipe contre chaque autre).
    Retourne le nombre de combats crees.
    """
    equipes = list(poule.equipes.all())
    combats_crees = 0

    if len(equipes) < 2:
        return 0

    for i, equipe_rouge in enumerate(equipes):
        for equipe_blanc in equipes[i + 1:]:
            combat_exists = Combat.objects.filter(
                poule=poule,
                equipe_rouge=equipe_rouge,
                equipe_blanc=equipe_blanc
            ).exists() or Combat.objects.filter(
                poule=poule,
                equipe_rouge=equipe_blanc,
                equipe_blanc=equipe_rouge
            ).exists()

            if not combat_exists:
                Combat.objects.create(
                    competition=poule.competition,
                    poule=poule,
                    equipe_rouge=equipe_rouge,
                    equipe_blanc=equipe_blanc,
                    status='planifie',
                    type_combat='equipe',
                    duree_combat=getattr(poule, 'category', None) and getattr(poule.category, 'combat_duration', 120) or 120,
                    duree_prolongation=getattr(poule, 'category', None) and getattr(poule.category, 'combat_extra_time', 0) or 0
                )
                combats_crees += 1

    return combats_crees
# Vues pour la gestion des combats
@login_required
def liste_combats(request, competition_id=None, poule_id=None):
    """
    Affiche la liste des combats, filtrés par compétition et/ou poule si spécifié.
    """
    from apps.competitions.models import Competition
    
    if poule_id:
        poule = get_object_or_404(Poule, id=poule_id)
        competition = poule.competition
        combats = Combat.objects.filter(poule=poule)
        context = {
            'combats': combats,
            'competition': competition,
            'poule': poule,
            'title': _("Combats de la poule {}").format(poule.nom)
        }
    elif competition_id:
        competition = get_object_or_404(Competition, id=competition_id)
        combats = Combat.objects.filter(competition=competition)
        context = {
            'combats': combats,
            'competition': competition,
            'title': _("Combats de la compétition")
        }
    else:
        combats = Combat.objects.order_by('-date_planifiee')
        context = {
            'combats': combats,
            'title': _("Tous les combats")
        }
    
    # Stats par statut
    context['combats_en_cours'] = combats.filter(status='en_cours').count()
    context['combats_termines'] = combats.filter(status='termine').count()
    context['combats_planifies'] = combats.filter(status='planifie').count()

    # Pagination
    paginator = Paginator(combats.order_by('-date_planifiee', 'status'), 20)
    page_number = request.GET.get('page')
    context['page_obj'] = paginator.get_page(page_number)

    return render(request, 'competitions/combat/liste_combats.html', context)

@login_required
def detail_combat(request, combat_id):
    """
    Affiche les détails d'un combat, y compris les actions et les scores.
    """
    combat = get_object_or_404(Combat, id=combat_id)
    actions = ActionCombat.objects.filter(combat=combat).order_by('temps')
    
    context = {
        'combat': combat,
        'actions': actions,
        'can_start': combat.status == 'planifie',
        'can_end': combat.status == 'en_cours',
        'configuration': combat.configuration,
        'point_form': AttributionPointForm(combat=combat) if combat.status == 'en_cours' else None
    }
    
    return render(request, 'competitions/combat/detail_combat.html', context)

@login_required
def creer_combat(request, competition_id=None, poule_id=None):
    """Configuration du combat — paramètres par catégorie/poule."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.add_combat'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    from apps.competitions.models import Competition, CompetitionCategory
    from apps.competitions.models.combat import CombatConfiguration

    # Récupérer la compétition
    competition_obj = None
    if not poule_id:
        poule_id = request.GET.get('poule') or request.POST.get('poule')
    if poule_id:
        poule = get_object_or_404(Poule, id=poule_id)
        competition_obj = poule.competition
        competition_id = competition_obj.id
    elif competition_id:
        competition_obj = get_object_or_404(Competition, id=competition_id)

    if not competition_obj:
        messages.error(request, _("Compétition non trouvée."))
        return redirect('competitions:dashboard:index')

    # Récupérer les catégories et poules
    categories = CompetitionCategory.objects.filter(
        competition=competition_obj
    ).prefetch_related('poules').order_by('name')

    # Configurations de combat disponibles
    configurations = CombatConfiguration.objects.filter(
        discipline=competition_obj.discipline
    ) if competition_obj.discipline else CombatConfiguration.objects.none()

    # Sauvegarde de la configuration (POST)
    if request.method == 'POST':
        category_id_post = request.POST.get('category', '')
        duree = request.POST.get('duree_combat', '120')
        extra_time = request.POST.get('duree_prolongation', '0')
        type_combat = request.POST.get('type_combat', 'individuel')

        try:
            duree = int(duree)
        except (ValueError, TypeError):
            duree = 120
        try:
            extra_time = int(extra_time) if extra_time else 0
        except (ValueError, TypeError):
            extra_time = 0

        if category_id_post:
            try:
                cat = CompetitionCategory.objects.get(id=category_id_post, competition=competition_obj)
                cat.combat_duration = duree
                cat.combat_extra_time = extra_time
                if type_combat in ('individuel', 'individual'):
                    cat.combat_mode = 'individual'
                else:
                    cat.combat_mode = 'team'
                cat.save(update_fields=['combat_duration', 'combat_extra_time', 'combat_mode'])
                messages.success(request, _("Configuration sauvegardée pour la catégorie '%(cat)s'.") % {'cat': cat.name})
            except CompetitionCategory.DoesNotExist:
                messages.error(request, _("Catégorie non trouvée."))
        else:
            messages.warning(request, _("Veuillez sélectionner une catégorie."))

        return redirect('competitions:combat:creer_combat_competition', competition_id=competition_id)

    # Charger les préférences sauvées
    saved_config = request.session.get('combat_config', {})

    return render(request, 'competitions/combat/form_combat.html', {
        'competition': competition_obj,
        'categories': categories,
        'configurations': configurations,
        'saved_config': saved_config,
        'title': _("Configuration du combat")
    })

@login_required
def modifier_combat(request, combat_id):
    """Permet de modifier un combat existant."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.change_combat'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    combat = get_object_or_404(Combat, id=combat_id)
    comp_id = combat.competition_id

    if request.method == 'POST':
        form = CombatForm(request.POST, instance=combat, competition_id=comp_id)
        if form.is_valid():
            form.save()
            messages.success(request, _("Le combat a été modifié avec succès."))
            return redirect('competitions:combat:detail_combat', combat_id=combat.id)
    else:
        form = CombatForm(instance=combat, competition_id=comp_id)

    return render(request, 'competitions/combat/form_combat.html', {
        'form': form,
        'combat': combat,
        'competition': combat.competition,
        'title': _("Configuration du combat")
    })

@login_required
def supprimer_combat(request, combat_id):
    """Permet de supprimer un combat."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.delete_combat'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    combat = get_object_or_404(Combat, id=combat_id)
    
    if request.method == 'POST':
        poule_id = combat.poule.id if combat.poule else None
        competition_id = combat.competition.id
        combat.delete()
        messages.success(request, _("Le combat a été supprimé avec succès."))
        
        if poule_id:
            return redirect('competitions:combat:detail_poule', poule_id=poule_id)
        else:
            return redirect('competitions:combat:liste_combats_competition', competition_id=competition_id)
    
    return render(request, 'competitions/combat/confirmer_suppression.html', {
        'object': combat,
        'title': _("Supprimer le combat"),
        'message': _("ÃŠtes-vous sÃ»r de vouloir supprimer ce combat ? Cette action supprimera également toutes les actions associées."),
        'cancel_url': reverse('competitions:combat:detail_combat', kwargs={'combat_id': combat.id})
    })

@login_required
def demarrer_combat(request, combat_id):
    """Permet de démarrer un combat planifié."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.change_combat'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    combat = get_object_or_404(Combat, id=combat_id)
    
    if combat.start_combat():
        messages.success(request, _("Le combat a été démarré."))
    else:
        messages.error(request, _("Impossible de démarrer ce combat."))
    
    return redirect('competitions:combat:detail_combat', combat_id=combat.id)

@login_required
def terminer_combat(request, combat_id):
    """Permet de terminer un combat en cours."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.change_combat'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    combat = get_object_or_404(Combat, id=combat_id)
    
    if combat.end_combat():
        # Déterminer le vainqueur automatiquement
        if combat.score_rouge > combat.score_blanc:
            messages.success(request, _("Combat terminé. Victoire de l'équipe/pratiquant rouge."))
        elif combat.score_blanc > combat.score_rouge:
            messages.success(request, _("Combat terminé. Victoire de l'équipe/pratiquant blanc."))
        else:
            messages.success(request, _("Combat terminé. Match nul."))
    else:
        messages.error(request, _("Impossible de terminer ce combat."))
    
    return redirect('competitions:combat:detail_combat', combat_id=combat.id)

@login_required
def annuler_combat(request, combat_id):
    """Permet d'annuler un combat."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.change_combat'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    combat = get_object_or_404(Combat, id=combat_id)
    
    if request.method == 'POST':
        motif = request.POST.get('motif', '')
        if combat.cancel_combat(motif):
            messages.success(request, _("Le combat a été annulé."))
        else:
            messages.error(request, _("Impossible d'annuler ce combat."))
        return redirect('competitions:combat:detail_combat', combat_id=combat.id)
    
    return render(request, 'competitions/combat/annuler_combat.html', {
        'combat': combat,
        'title': _("Annuler le combat")
    })

# Vues pour la gestion des actions de combat (API)
@login_required
@csrf_exempt
def ajouter_action(request, combat_id):
    """Permet d'ajouter une action Ã  un combat en cours (en AJAX ou formulaire standard)."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.add_actioncombat'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    combat = get_object_or_404(Combat, id=combat_id)

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if combat.status != 'en_cours':
        messages.error(request, _("Impossible d'ajouter une action Ã  un combat qui n'est pas en cours."))
        return JsonResponse({'success': False, 'error': "Combat non actif"}, status=400) if is_ajax else redirect('competitions:combat:detail_combat', combat_id=combat.id)
    
    if request.method == 'POST':
        try:
            if is_ajax:
                data = json.loads(request.body)
                type_action = data.get('type_action')
                couleur = data.get('couleur')
                valeur = Decimal(str(data.get('valeur', 0)))
                description = data.get('description', '')
                arbitre_id = data.get('arbitre_id')
            else:
                # Traiter les formulaires AttributionPointForm
                form = AttributionPointForm(request.POST, combat=combat)
                if form.is_valid():
                    type_action = form.cleaned_data['type_action']
                    couleur = form.cleaned_data['couleur']
                    
                    if type_action == 'point':
                        valeur = Decimal(str(form.cleaned_data['valeur_point']))
                    else:  # type_action == 'penalite'
                        valeur = Decimal(str(form.cleaned_data['valeur_penalite']))
                    
                    description = ""
                    arbitre_id = request.user.id if hasattr(request.user, 'judge') else None
                else:
                    messages.error(request, _("Formulaire invalide."))
                    return redirect('competitions:combat:detail_combat', combat_id=combat.id)
            
            # Créer l'action
            action = ActionCombat(
                combat=combat,
                type_action=type_action,
                couleur=couleur,
                valeur=valeur,
                description=description
            )
            
            if arbitre_id:
                from apps.competitions.models import Judge
                try:
                    action.arbitre = Judge.objects.get(id=arbitre_id)
                except Judge.DoesNotExist:
                    pass
            
            action.save()
            
            # Mettre à jour le combat (fait automatiquement par le modèle ActionCombat)
            combat.refresh_from_db()
            
            if is_ajax:
                return JsonResponse({
                    'success': True, 
                    'action_id': action.id,
                    'score_rouge': float(combat.score_rouge),
                    'score_blanc': float(combat.score_blanc)
                })
            else:
                messages.success(request, _("L'action a été enregistrée."))
                return redirect('competitions:combat:detail_combat', combat_id=combat.id)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur dans ajouter_action combat {combat_id}: {e}", exc_info=True)
            if is_ajax:
                return JsonResponse({'success': False, 'error': str(e)}, status=500)
            else:
                messages.error(request, _("Erreur lors de l'enregistrement de l'action."))
                return redirect('competitions:combat:detail_combat', combat_id=combat.id)
    
    messages.error(request, _("Méthode non autorisée."))
    return JsonResponse({'success': False, 'error': "Méthode non autorisée"}, status=405) if is_ajax else redirect('competitions:combat:detail_combat', combat_id=combat.id)

@login_required
def annuler_action(request, action_id):
    """Permet d'annuler une action de combat."""
    # Vérifier manuellement les permissions
    if not manual_permission_check(request.user, 'competitions.delete_actioncombat'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    action = get_object_or_404(ActionCombat, id=action_id)
    combat = action.combat
    
    if combat.status != 'en_cours':
        messages.error(request, _("Impossible d'annuler une action d'un combat qui n'est pas en cours."))
        return redirect('competitions:combat:detail_combat', combat_id=combat.id)
    
    # Inverser l'effet de l'action sur le score
    if action.type_action in ['point', 'penalite']:
        if action.couleur == 'rouge':
            combat.score_rouge -= action.valeur
        elif action.couleur == 'blanc':
            combat.score_blanc -= action.valeur
        
        combat.save()
    
    # Supprimer l'action
    action.delete()
    
    messages.success(request, _("L'action a été annulée."))
    return redirect('competitions:combat:detail_combat', combat_id=combat.id)

# Interface de combat en temps réel
@login_required
def interface_combat(request, combat_id):
    """
    Affiche l'interface de combat en temps réel, optimisée pour l'arbitrage.
    """
    combat = get_object_or_404(Combat, id=combat_id)
    actions = ActionCombat.objects.filter(combat=combat).order_by('-temps')[:30]

    context = {
        'combat': combat,
        'actions': actions,
        'is_judge': hasattr(request.user, 'judge'),
        'can_edit': request.user.is_staff or (hasattr(request.user, 'judge') and combat.arbitre_central and combat.arbitre_central.user == request.user),
    }

    if combat.configuration:
        context['valeurs_points'] = combat.configuration.valeurs_points
        context['valeurs_penalites'] = combat.configuration.valeurs_penalites

    # Mode équipe : charger tous les membres de chaque équipe (même logique que V2)
    if combat.type_combat == 'equipe' and combat.equipe_rouge and combat.equipe_blanc:
        titulaires_rouge = list(
            MembreEquipe.objects.filter(equipe=combat.equipe_rouge, est_remplacant=False)
            .select_related('pratiquant', 'pratiquant__organization')
            .order_by('ordre', 'id')
        )
        titulaires_blanc = list(
            MembreEquipe.objects.filter(equipe=combat.equipe_blanc, est_remplacant=False)
            .select_related('pratiquant', 'pratiquant__organization')
            .order_by('ordre', 'id')
        )
        remplacants_rouge = list(
            MembreEquipe.objects.filter(equipe=combat.equipe_rouge, est_remplacant=True)
            .select_related('pratiquant', 'pratiquant__organization')
            .order_by('ordre', 'id')
        )
        remplacants_blanc = list(
            MembreEquipe.objects.filter(equipe=combat.equipe_blanc, est_remplacant=True)
            .select_related('pratiquant', 'pratiquant__organization')
            .order_by('ordre', 'id')
        )
        all_membres_rouge = titulaires_rouge + remplacants_rouge
        all_membres_blanc = titulaires_blanc + remplacants_blanc

        nb_rounds = max(len(titulaires_rouge), len(titulaires_blanc), 1)
        rounds_data = []
        for i in range(nb_rounds):
            mr = titulaires_rouge[i] if i < len(titulaires_rouge) else None
            mb = titulaires_blanc[i] if i < len(titulaires_blanc) else None
            rounds_data.append({
                'numero': i + 1,
                'rouge_nom': mr.pratiquant.full_name if mr else str(_("Pas de combattant")),
                'rouge_id': mr.pratiquant.id if mr else 0,
                'rouge_photo': mr.pratiquant.photo.url if mr and mr.pratiquant.photo else '',
                'blanc_nom': mb.pratiquant.full_name if mb else str(_("Pas de combattant")),
                'blanc_id': mb.pratiquant.id if mb else 0,
                'blanc_photo': mb.pratiquant.photo.url if mb and mb.pratiquant.photo else '',
                'rouge_club': mr.pratiquant.organization.name if mr and mr.pratiquant.organization else '',
                'blanc_club': mb.pratiquant.organization.name if mb and mb.pratiquant.organization else '',
            })

        membres_rouge_data = []
        for m in all_membres_rouge:
            membres_rouge_data.append({
                'id': m.pratiquant.id,
                'nom': m.pratiquant.full_name,
                'photo': m.pratiquant.photo.url if m.pratiquant.photo else '',
                'est_remplacant': m.est_remplacant,
                'ordre': m.ordre,
            })
        membres_blanc_data = []
        for m in all_membres_blanc:
            membres_blanc_data.append({
                'id': m.pratiquant.id,
                'nom': m.pratiquant.full_name,
                'photo': m.pratiquant.photo.url if m.pratiquant.photo else '',
                'est_remplacant': m.est_remplacant,
                'ordre': m.ordre,
            })

        context['is_team_combat'] = True
        context['rounds_data'] = rounds_data
        context['nb_rounds'] = nb_rounds
        context['all_membres_rouge'] = all_membres_rouge
        context['all_membres_blanc'] = all_membres_blanc
        context['remplacants_rouge'] = remplacants_rouge
        context['remplacants_blanc'] = remplacants_blanc
        context['membres_rouge_data'] = json.dumps(membres_rouge_data)
        context['membres_blanc_data'] = json.dumps(membres_blanc_data)
    else:
        context['is_team_combat'] = False

    return render(request, 'competitions/combat/interface_combat.html', context)


@login_required
def monitor_match(request, combat_id):
    """
    Affiche l'interface de suivi en temps réel optimisée pour les juges et les coachs.
    Cette vue utilise JavaScript pour mettre Ã  jour les scores et actions en temps réel.
    """
    combat = get_object_or_404(Combat, id=combat_id)
    actions = ActionCombat.objects.filter(combat=combat).order_by('-temps')[:10]
    
    # Vérifier si l'utilisateur a le droit d'éditer (arbitre central ou staff)
    can_edit = request.user.is_staff
    if hasattr(request.user, 'judge'):
        can_edit = can_edit or (combat.arbitre_central and combat.arbitre_central.user == request.user)
    
    context = {
        'combat': combat,
        'actions': actions,
        'can_edit': can_edit
    }
    
    return render(request, 'competitions/combat/monitor_live.html', context)

def affichage_combat(request, combat_id):
    """
    Affiche le tableau de score grand écran pour le public.
    Pas de login requis — destiné à l'écran secondaire.
    """
    combat = get_object_or_404(Combat, id=combat_id)
    return render(request, 'competitions/combat/affichage_combat.html', {
        'combat': combat
    })


def vue_publique_live(request):
    """
    Vue publique persistante — pas de login requis.
    Affiche le combat en cours. Se rafraîchit automatiquement.
    Destinée à être ouverte une seule fois sur un écran secondaire.
    """
    from apps.competitions.models import Competition

    # Trouver le combat en cours (le plus récent)
    combat_actif = Combat.objects.filter(
        status='en_cours'
    ).select_related(
        'equipe_rouge', 'equipe_blanc',
        'pratiquant_rouge', 'pratiquant_blanc',
        'competition', 'poule'
    ).order_by('-updated_at').first()

    # Si pas de combat en cours, chercher le dernier combat planifié
    if not combat_actif:
        combat_actif = Combat.objects.filter(
            status='planifie'
        ).select_related(
            'equipe_rouge', 'equipe_blanc',
            'pratiquant_rouge', 'pratiquant_blanc',
            'competition', 'poule'
        ).order_by('-id').first()

    return render(request, 'competitions/combat/vue_publique_live.html', {
        'combat': combat_actif,
        'refresh_interval': 3,
    })

@login_required
def interface_combat_v2(request, combat_id):
    """
    Nouvelle interface de combat améliorée avec système double écran.
    Optimisée pour l'arbitrage professionnel avec support des raccourcis clavier.
    """
    # Debug: essayer de récupérer le combat de plusieurs façons
    try:
        combat = Combat.objects.get(id=combat_id)
    except Combat.DoesNotExist:
        # Si ça ne marche pas, essayer avec filter
        combat = Combat.objects.filter(id=combat_id).first()
        if not combat:
            # En dernier recours, lister tous les combats
            all_combats = list(Combat.objects.values_list('id', flat=True))
            raise Combat.DoesNotExist(
                f"Combat {combat_id} not found. Available IDs: {all_combats}"
            )
    
    actions = ActionCombat.objects.filter(combat=combat).order_by('-temps')[:20]
    
    # Mode simulation uniquement si explicitement demandé via paramètre GET
    # Le combat peut être en mode édition même s'il n'est pas encore démarré
    simulation_mode = request.GET.get('simulation') == '1'
    
    context = {
        'combat': combat,
        'actions': actions,
        'simulation_mode': simulation_mode,
        'is_judge': hasattr(request.user, 'judge'),
        'can_edit': request.user.is_staff or (hasattr(request.user, 'judge') and combat.arbitre_central and combat.arbitre_central.user == request.user)
    }

    # Hériter durée/extra-time de la catégorie si le combat n'en a pas
    if combat.poule and hasattr(combat.poule, 'category') and combat.poule.category:
        cat = combat.poule.category
        if not combat.duree_prolongation and cat.combat_extra_time:
            combat.duree_prolongation = cat.combat_extra_time
        if combat.duree_combat == 120 and cat.combat_duration != 120:
            combat.duree_combat = cat.combat_duration

    if combat.configuration:
        context['valeurs_points'] = combat.configuration.valeurs_points
        context['valeurs_penalites'] = combat.configuration.valeurs_penalites

    # Mode équipe : charger tous les membres de chaque équipe
    if combat.type_combat == 'equipe' and combat.equipe_rouge and combat.equipe_blanc:
        # Titulaires
        titulaires_rouge = list(
            MembreEquipe.objects.filter(equipe=combat.equipe_rouge, est_remplacant=False)
            .select_related('pratiquant', 'pratiquant__organization')
            .order_by('ordre', 'id')
        )
        titulaires_blanc = list(
            MembreEquipe.objects.filter(equipe=combat.equipe_blanc, est_remplacant=False)
            .select_related('pratiquant', 'pratiquant__organization')
            .order_by('ordre', 'id')
        )
        # Remplaçants
        remplacants_rouge = list(
            MembreEquipe.objects.filter(equipe=combat.equipe_rouge, est_remplacant=True)
            .select_related('pratiquant', 'pratiquant__organization')
            .order_by('ordre', 'id')
        )
        remplacants_blanc = list(
            MembreEquipe.objects.filter(equipe=combat.equipe_blanc, est_remplacant=True)
            .select_related('pratiquant', 'pratiquant__organization')
            .order_by('ordre', 'id')
        )
        # Tous les membres pour les panneaux de sélection
        all_membres_rouge = titulaires_rouge + remplacants_rouge
        all_membres_blanc = titulaires_blanc + remplacants_blanc

        # Construire les rounds : paire à paire (Fighter 1 vs Fighter 1, etc.)
        nb_rounds = max(len(titulaires_rouge), len(titulaires_blanc), 1)
        rounds_data = []
        for i in range(nb_rounds):
            mr = titulaires_rouge[i] if i < len(titulaires_rouge) else None
            mb = titulaires_blanc[i] if i < len(titulaires_blanc) else None
            rounds_data.append({
                'numero': i + 1,
                'rouge_nom': mr.pratiquant.full_name if mr else str(_("Pas de combattant")),
                'rouge_id': mr.pratiquant.id if mr else 0,
                'rouge_photo': mr.pratiquant.photo.url if mr and mr.pratiquant.photo else '',
                'blanc_nom': mb.pratiquant.full_name if mb else str(_("Pas de combattant")),
                'blanc_id': mb.pratiquant.id if mb else 0,
                'blanc_photo': mb.pratiquant.photo.url if mb and mb.pratiquant.photo else '',
                'rouge_club': mr.pratiquant.organization.name if mr and mr.pratiquant.organization else '',
                'blanc_club': mb.pratiquant.organization.name if mb and mb.pratiquant.organization else '',
            })

        # Préparer les données des membres pour le JS (sélection latérale)
        membres_rouge_data = []
        for m in all_membres_rouge:
            membres_rouge_data.append({
                'id': m.pratiquant.id,
                'nom': m.pratiquant.full_name,
                'photo': m.pratiquant.photo.url if m.pratiquant.photo else '',
                'est_remplacant': m.est_remplacant,
                'ordre': m.ordre,
            })
        membres_blanc_data = []
        for m in all_membres_blanc:
            membres_blanc_data.append({
                'id': m.pratiquant.id,
                'nom': m.pratiquant.full_name,
                'photo': m.pratiquant.photo.url if m.pratiquant.photo else '',
                'est_remplacant': m.est_remplacant,
                'ordre': m.ordre,
            })

        context['is_team_combat'] = True
        context['rounds_data'] = rounds_data
        context['nb_rounds'] = nb_rounds
        context['membres_rouge'] = titulaires_rouge
        context['membres_blanc'] = titulaires_blanc
        context['all_membres_rouge'] = all_membres_rouge
        context['all_membres_blanc'] = all_membres_blanc
        context['remplacants_rouge'] = remplacants_rouge
        context['remplacants_blanc'] = remplacants_blanc
        context['membres_rouge_data'] = json.dumps(membres_rouge_data)
        context['membres_blanc_data'] = json.dumps(membres_blanc_data)
    else:
        context['is_team_combat'] = False

    # Utiliser le nouveau template V3 si disponible, sinon V2
    return render(request, 'competitions/combat/interface_combat_v3.html', context)

# API pour l'interface temps réel
@login_required
def api_statut_combat(request, combat_id):
    """
    API JSON retournant le statut actuel d'un combat.
    Utilisé pour l'interface temps réel avec polling.
    """
    combat = get_object_or_404(Combat, id=combat_id)
    actions = ActionCombat.objects.filter(combat=combat).order_by('-temps')[:10]
    
    # Calculer le temps écoulé si le combat est en cours
    elapsed_time = None
    if combat.status == 'en_cours' and combat.debut_combat:
        elapsed_seconds = (timezone.now() - combat.debut_combat).total_seconds()
        elapsed_time = min(elapsed_seconds, combat.duree_combat)
    
    data = {
        'id': combat.id,
        'uuid': str(combat.uuid),
        'status': combat.status,
        'score_rouge': float(combat.score_rouge),
        'score_blanc': float(combat.score_blanc),
        'debut_combat': combat.debut_combat.isoformat() if combat.debut_combat else None,
        'fin_combat': combat.fin_combat.isoformat() if combat.fin_combat else None,
        'type_combat': combat.type_combat,
        'derniere_action': None,
        'elapsed_time': int(elapsed_time) if elapsed_time is not None else None,
        'total_time': combat.duree_combat,
        'vainqueur': combat.vainqueur,
        'est_nul': combat.est_nul,
        'actions': []
    }
    
    # Informations des participants
    if combat.type_combat == 'individuel':
        data['rouge'] = {
            'id': combat.pratiquant_rouge.id,
            'nom': combat.pratiquant_rouge.full_name
        } if combat.pratiquant_rouge else None
        
        data['blanc'] = {
            'id': combat.pratiquant_blanc.id,
            'nom': combat.pratiquant_blanc.full_name
        } if combat.pratiquant_blanc else None
    else:
        data['rouge'] = {
            'id': combat.equipe_rouge.id,
            'nom': combat.equipe_rouge.nom
        } if combat.equipe_rouge else None
        
        data['blanc'] = {
            'id': combat.equipe_blanc.id,
            'nom': combat.equipe_blanc.nom
        } if combat.equipe_blanc else None
    
    # Liste des actions récentes
    for action in actions:
        action_data = {
            'id': action.id,
            'action_type': action.type_action,
            'team': 'red' if action.couleur == 'rouge' else 'blue' if action.couleur == 'blanc' else 'neutral',
            'points': float(action.valeur),
            'description': action.description,
            'timestamp': action.temps.isoformat(),
            'judge': action.arbitre.user.get_full_name() if action.arbitre else None,
        }
        data['actions'].append(action_data)
        
        # Ã‰galement définir la dernière action pour compatibilité
        if not data['derniere_action'] and actions.exists():
            derniere = actions.first()
            data['derniere_action'] = {
                'id': derniere.id,
                'type': derniere.type_action,
                'couleur': derniere.couleur,
                'valeur': float(derniere.valeur),
                'temps': derniere.temps.isoformat(),
                'description': derniere.description
            }
    
    # Ajouter l'état du timer depuis le cache (synchronisé par l'arbitre)
    from django.core.cache import cache
    timer_state = cache.get(f'combat_timer_{combat_id}', {})
    data['timer'] = {
        'seconds': timer_state.get('seconds', data.get('elapsed_time') or 0),
        'is_running': timer_state.get('is_running', combat.status == 'en_cours'),
        'total_duration': timer_state.get('total_duration', combat.duree_combat),
        'mode': timer_state.get('mode', 'ascending'),
        'updated_at': timer_state.get('updated_at'),
    }

    # Ajouter les infos du combattant actuel (mode équipe)
    if combat.type_combat == 'equipe':
        fighters_state = cache.get(f'combat_fighters_{combat_id}', {})
        if fighters_state:
            data['current_fighters'] = fighters_state

    return JsonResponse(data)

@login_required
def api_liste_actions(request, combat_id):
    """
    API JSON retournant la liste des actions d'un combat.
    """
    combat = get_object_or_404(Combat, id=combat_id)
    actions = ActionCombat.objects.filter(combat=combat).order_by('-temps')
    
    data = {
        'id': combat.id,
        'actions': []
    }
    
    for action in actions:
        data['actions'].append({
            'id': action.id,
            'type': action.type_action,
            'couleur': action.couleur,
            'valeur': float(action.valeur),
            'temps': action.temps.isoformat(),
            'description': action.description
        })

    return JsonResponse(data)


@login_required
@csrf_exempt
def api_timer_sync(request, combat_id):
    """Synchronise l'état du timer depuis l'interface arbitre vers le cache serveur."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    combat = get_object_or_404(Combat, id=combat_id)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    from django.core.cache import cache
    # Ne mettre à jour le timer que si ce n'est pas un appel fighters_only
    if not data.get('fighters_only'):
        cache.set(f'combat_timer_{combat_id}', {
            'seconds': int(data.get('seconds', 0)),
            'is_running': bool(data.get('is_running', False)),
            'total_duration': int(data.get('total_duration', combat.duree_combat)),
            'mode': data.get('mode', 'ascending'),
            'updated_at': timezone.now().isoformat(),
        }, timeout=7200)

    # Stocker aussi les infos du combattant actuel (mode équipe)
    fighters = data.get('current_fighters')
    if fighters:
        cache.set(f'combat_fighters_{combat_id}', {
            'current_round': fighters.get('current_round', 1),
            'total_rounds': fighters.get('total_rounds', 1),
            'rouge_nom': fighters.get('rouge_nom', ''),
            'rouge_photo': fighters.get('rouge_photo', ''),
            'blanc_nom': fighters.get('blanc_nom', ''),
            'blanc_photo': fighters.get('blanc_photo', ''),
        }, timeout=7200)

    return JsonResponse({'success': True})


@login_required
def api_categories_competition(request, competition_id):
    """
    API JSON retournant la liste des catégories d'une compétition.
    Utilisé pour charger dynamiquement les catégories dans le formulaire d'équipe.
    """
    from apps.competitions.models import Competition, CompetitionCategory

    competition = get_object_or_404(Competition, id=competition_id)
    categories = CompetitionCategory.objects.filter(
        competition=competition
    ).order_by('name')

    data = {
        'competition_id': competition.id,
        'categories': []
    }

    for cat in categories:
        data['categories'].append({
            'id': cat.id,
            'name': cat.name,
            'gender': cat.get_gender_display() if cat.gender else None,
        })

    return JsonResponse(data)


# =============================================================================
# FEATURE #9: Génération de la phase finale après les poules
# =============================================================================
@login_required
def generer_phase_finale(request, competition_id):
    """
    Génère automatiquement la phase finale (quarts, demis, finale)
    à partir des résultats des poules éliminatoires.

    Logique:
    - Récupère les N premiers de chaque poule éliminatoire
    - Génère les combats de quart de finale (si >= 8 qualifiés)
    - Ou demi-finale directe (si 4 qualifiés)
    - Ou finale directe (si 2 qualifiés)
    """
    from apps.competitions.models import Competition
    from django.db.models import Sum, Count, Q

    if not manual_permission_check(request.user, 'competitions.change_competition'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires."))
        return redirect('competitions:dashboard:index')

    competition = get_object_or_404(Competition, id=competition_id)

    # Récupérer les poules éliminatoires
    poules_eliminatoires = Poule.objects.filter(
        competition=competition,
        phase='eliminatoire'
    ).order_by('numero')

    if not poules_eliminatoires.exists():
        messages.error(request, _("Aucune poule éliminatoire trouvée."))
        return redirect('competitions:combat:liste_poules', competition_id=competition_id)

    # Vérifier que toutes les poules sont terminées
    for poule in poules_eliminatoires:
        combats_non_termines = Combat.objects.filter(
            poule=poule
        ).exclude(status='termine').count()

        if combats_non_termines > 0:
            messages.warning(
                request,
                _("La poule {} a encore {} combat(s) non terminé(s).").format(
                    poule.nom, combats_non_termines
                )
            )
            return redirect('competitions:combat:liste_poules', competition_id=competition_id)

    if request.method == 'POST':
        qualifies_par_poule = int(request.POST.get('qualifies_par_poule', 2))

        # Calculer le classement de chaque poule et récupérer les qualifiés
        tous_qualifies = []

        for poule in poules_eliminatoires:
            classement_poule = _calculer_classement_poule(poule)
            qualifies = classement_poule[:qualifies_par_poule]

            for rang, entry in enumerate(qualifies, 1):
                tous_qualifies.append({
                    'entry': entry,
                    'poule': poule,
                    'rang_poule': rang
                })

        nb_qualifies = len(tous_qualifies)

        if nb_qualifies < 2:
            messages.error(request, _("Pas assez de qualifiés pour générer une phase finale."))
            return redirect('competitions:combat:liste_poules', competition_id=competition_id)

        # Déterminer la phase à créer
        if nb_qualifies >= 8:
            phase = 'quart'
            phase_label = _("Quart de finale")
        elif nb_qualifies >= 4:
            phase = 'demi'
            phase_label = _("Demi-finale")
        else:
            phase = 'finale'
            phase_label = _("Finale")

        # Supprimer les anciennes phases finales si elles existent
        Poule.objects.filter(
            competition=competition,
            phase__in=['quart', 'demi', 'finale']
        ).delete()

        # Créer la nouvelle poule de phase finale
        poule_finale = Poule.objects.create(
            competition=competition,
            nom=str(phase_label),
            numero=1,
            phase=phase
        )

        # Générer les combats selon le système de croisement
        # 1er Poule A vs 2ème Poule B, 1er Poule B vs 2ème Poule A, etc.
        combats_crees = _generer_combats_phase_finale(
            poule_finale,
            tous_qualifies,
            competition,
            nb_qualifies
        )

        messages.success(
            request,
            _("Phase finale générée: {} avec {} combats.").format(phase_label, combats_crees)
        )
        return redirect('competitions:combat:detail_poule', poule_id=poule_finale.id)

    # Afficher le formulaire de configuration
    context = {
        'competition': competition,
        'poules': poules_eliminatoires,
        'nb_poules': poules_eliminatoires.count(),
    }
    return render(request, 'competitions/combat/generer_phase_finale.html', context)


def _calculer_classement_poule(poule):
    """
    Calcule le classement d'une poule basé sur:
    1. Nombre de victoires
    2. Différence de points
    3. Points marqués
    """
    from django.db.models import Sum, Q

    classement = []

    # Déterminer si c'est une poule d'équipes ou de pratiquants
    if poule.equipes.exists():
        participants = list(poule.equipes.all())
        is_equipe = True
    else:
        participants = list(poule.pratiquants.all())
        is_equipe = False

    for participant in participants:
        if is_equipe:
            filter_rouge = Q(poule=poule, equipe_rouge=participant, status='termine')
            filter_blanc = Q(poule=poule, equipe_blanc=participant, status='termine')
            victoires_rouge = Combat.objects.filter(filter_rouge, vainqueur='rouge').count()
            victoires_blanc = Combat.objects.filter(filter_blanc, vainqueur='blanc').count()
        else:
            filter_rouge = Q(poule=poule, pratiquant_rouge=participant, status='termine')
            filter_blanc = Q(poule=poule, pratiquant_blanc=participant, status='termine')
            victoires_rouge = Combat.objects.filter(filter_rouge, vainqueur='rouge').count()
            victoires_blanc = Combat.objects.filter(filter_blanc, vainqueur='blanc').count()

        victoires = victoires_rouge + victoires_blanc

        # Calculer les points
        combats_rouge = Combat.objects.filter(
            Q(poule=poule, status='termine') &
            (Q(equipe_rouge=participant) if is_equipe else Q(pratiquant_rouge=participant))
        ).aggregate(
            pour=Sum('score_rouge', default=0),
            contre=Sum('score_blanc', default=0)
        )

        combats_blanc = Combat.objects.filter(
            Q(poule=poule, status='termine') &
            (Q(equipe_blanc=participant) if is_equipe else Q(pratiquant_blanc=participant))
        ).aggregate(
            pour=Sum('score_blanc', default=0),
            contre=Sum('score_rouge', default=0)
        )

        points_pour = float(combats_rouge['pour'] or 0) + float(combats_blanc['pour'] or 0)
        points_contre = float(combats_rouge['contre'] or 0) + float(combats_blanc['contre'] or 0)

        classement.append({
            'participant': participant,
            'is_equipe': is_equipe,
            'victoires': victoires,
            'points_pour': points_pour,
            'points_contre': points_contre,
            'diff': points_pour - points_contre
        })

    # Trier par victoires, puis diff, puis points pour
    classement.sort(key=lambda x: (-x['victoires'], -x['diff'], -x['points_pour']))

    return classement


def _generer_combats_phase_finale(poule, qualifies, competition, nb_qualifies):
    """
    Génère les combats de phase finale avec croisement des poules.
    """
    combats_crees = 0

    # Organiser les qualifiés par rang puis par poule
    # Pour un croisement optimal: 1er P1 vs 2ème P2, 1er P2 vs 2ème P1, etc.
    premiers = [q for q in qualifies if q['rang_poule'] == 1]
    seconds = [q for q in qualifies if q['rang_poule'] == 2]

    # Créer les paires avec croisement
    paires = []
    nb_premiers = len(premiers)

    for i in range(min(nb_premiers, len(seconds))):
        # Croiser: 1er de poule i vs 2ème de poule (i+1) % nb
        idx_second = (i + 1) % len(seconds) if len(seconds) > 1 else 0
        paires.append((premiers[i], seconds[idx_second]))

    # Gérer les qualifiés restants si nombre impair
    if len(premiers) > len(seconds):
        # Ajouter les premiers restants avec exemption ou entre eux
        for i in range(len(seconds), len(premiers)):
            if i + 1 < len(premiers):
                paires.append((premiers[i], premiers[i + 1]))

    # Créer les combats
    for paire in paires:
        q1, q2 = paire

        combat_data = {
            'competition': competition,
            'poule': poule,
            'status': 'planifie',
        }

        if q1['entry']['is_equipe']:
            combat_data['type_combat'] = 'equipe'
            combat_data['equipe_rouge'] = q1['entry']['participant']
            combat_data['equipe_blanc'] = q2['entry']['participant']
        else:
            combat_data['type_combat'] = 'individuel'
            combat_data['pratiquant_rouge'] = q1['entry']['participant']
            combat_data['pratiquant_blanc'] = q2['entry']['participant']

        Combat.objects.create(**combat_data)
        combats_crees += 1

    return combats_crees


# =============================================================================
# FEATURE #10: Génération de la phase finale PAR CATÉGORIE
# =============================================================================
@login_required
def generer_phase_finale_categorie(request, competition_id, category_id):
    """
    Génère automatiquement la phase finale (demi-finales, finale) pour UNE catégorie spécifique.

    Cette vue est appelée depuis la page liste_poules.html pour chaque catégorie
    qui a plusieurs poules éliminatoires avec tous les combats terminés.

    Logique:
    - Récupère les N premiers de chaque poule éliminatoire de cette catégorie
    - Génère les combats de demi-finale (croisement 1er PA vs 2ème PB)
    - Les vainqueurs des demis iront en finale
    """
    from apps.competitions.models import Competition, CompetitionCategory
    from django.db.models import Q

    if not manual_permission_check(request.user, 'competitions.change_competition'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires."))
        return redirect('competitions:dashboard:index')

    competition = get_object_or_404(Competition, id=competition_id)
    category = get_object_or_404(CompetitionCategory, id=category_id, competition=competition)

    # Récupérer les poules éliminatoires de CETTE catégorie uniquement
    poules_eliminatoires = Poule.objects.filter(
        competition=competition,
        category=category,
        phase='eliminatoire'
    ).order_by('numero')

    if poules_eliminatoires.count() < 2:
        messages.warning(request, _("Cette catégorie n'a qu'une seule poule. Pas de phase finale nécessaire."))
        return redirect('competitions:combat:liste_poules', competition_id=competition_id)

    # Vérifier que toutes les poules de la catégorie sont terminées
    combats_non_termines = Combat.objects.filter(
        poule__in=poules_eliminatoires
    ).exclude(status='termine').count()

    if combats_non_termines > 0:
        messages.warning(
            request,
            _("Il reste {} combat(s) non terminé(s) dans les poules éliminatoires de cette catégorie.").format(combats_non_termines)
        )
        return redirect('competitions:combat:liste_poules', competition_id=competition_id)

    # Calculer le classement de chaque poule et récupérer les qualifiés (2 premiers par poule)
    qualifies_par_poule = 2
    tous_qualifies = []

    for poule in poules_eliminatoires:
        classement_poule = _calculer_classement_poule(poule)
        qualifies = classement_poule[:qualifies_par_poule]

        for rang, entry in enumerate(qualifies, 1):
            tous_qualifies.append({
                'entry': entry,
                'poule': poule,
                'rang_poule': rang
            })

    nb_qualifies = len(tous_qualifies)

    if nb_qualifies < 2:
        messages.error(request, _("Pas assez de qualifiés pour générer une phase finale."))
        return redirect('competitions:combat:liste_poules', competition_id=competition_id)

    # Supprimer les anciennes phases finales de CETTE catégorie si elles existent
    Poule.objects.filter(
        competition=competition,
        category=category,
        phase__in=['quart', 'demi', 'finale']
    ).delete()

    combats_phase_finale = 0

    # Déterminer les phases à créer selon le nombre de qualifiés
    premiers = [q for q in tous_qualifies if q['rang_poule'] == 1]
    seconds = [q for q in tous_qualifies if q['rang_poule'] == 2]

    if nb_qualifies >= 4:
        # === CRÉER LES DEMI-FINALES ===
        poule_demi = Poule.objects.create(
            competition=competition,
            category=category,
            nom=f"Demi-finales - {category.name[:30]}",
            numero=100,
            phase='demi',
            description=f"Demi-finales de la catégorie {category.name}"
        )

        # Croisement: 1er Poule A vs 2ème Poule B, 1er Poule B vs 2ème Poule A
        # Demi 1: 1er PA vs 2ème PB
        # Demi 2: 1er PB vs 2ème PA
        if len(premiers) >= 2 and len(seconds) >= 2:
            is_equipe = premiers[0]['entry']['is_equipe']

            # Demi-finale 1: 1er Poule A vs 2ème Poule B
            combat_data_1 = {
                'competition': competition,
                'poule': poule_demi,
                'status': 'planifie',
            }
            if is_equipe:
                combat_data_1['type_combat'] = 'equipe'
                combat_data_1['equipe_rouge'] = premiers[0]['entry']['participant']
                combat_data_1['equipe_blanc'] = seconds[1]['entry']['participant']
            else:
                combat_data_1['type_combat'] = 'individuel'
                combat_data_1['pratiquant_rouge'] = premiers[0]['entry']['participant']
                combat_data_1['pratiquant_blanc'] = seconds[1]['entry']['participant']

            Combat.objects.create(**combat_data_1)
            combats_phase_finale += 1

            # Demi-finale 2: 1er Poule B vs 2ème Poule A
            combat_data_2 = {
                'competition': competition,
                'poule': poule_demi,
                'status': 'planifie',
            }
            if is_equipe:
                combat_data_2['type_combat'] = 'equipe'
                combat_data_2['equipe_rouge'] = premiers[1]['entry']['participant']
                combat_data_2['equipe_blanc'] = seconds[0]['entry']['participant']
            else:
                combat_data_2['type_combat'] = 'individuel'
                combat_data_2['pratiquant_rouge'] = premiers[1]['entry']['participant']
                combat_data_2['pratiquant_blanc'] = seconds[0]['entry']['participant']

            Combat.objects.create(**combat_data_2)
            combats_phase_finale += 1

        # === CRÉER LA FINALE (vide pour l'instant - sera remplie manuellement ou via bouton) ===
        poule_finale = Poule.objects.create(
            competition=competition,
            category=category,
            nom=f"Finale - {category.name[:30]}",
            numero=200,
            phase='finale',
            description=f"Finale de la catégorie {category.name}. Les vainqueurs des demi-finales s'affronteront ici."
        )

        messages.success(
            request,
            _("Phase finale générée pour '{}': 2 demi-finales créées. La finale sera automatiquement peuplée après les demi-finales.").format(category.name)
        )

    elif nb_qualifies == 2:
        # Seulement 2 qualifiés: finale directe
        poule_finale = Poule.objects.create(
            competition=competition,
            category=category,
            nom=f"Finale - {category.name[:30]}",
            numero=200,
            phase='finale',
            description=f"Finale directe de la catégorie {category.name}"
        )

        is_equipe = tous_qualifies[0]['entry']['is_equipe']
        combat_data = {
            'competition': competition,
            'poule': poule_finale,
            'status': 'planifie',
        }
        if is_equipe:
            combat_data['type_combat'] = 'equipe'
            combat_data['equipe_rouge'] = tous_qualifies[0]['entry']['participant']
            combat_data['equipe_blanc'] = tous_qualifies[1]['entry']['participant']
        else:
            combat_data['type_combat'] = 'individuel'
            combat_data['pratiquant_rouge'] = tous_qualifies[0]['entry']['participant']
            combat_data['pratiquant_blanc'] = tous_qualifies[1]['entry']['participant']

        Combat.objects.create(**combat_data)
        combats_phase_finale += 1

        messages.success(
            request,
            _("Finale directe générée pour '{}': 1 combat créé.").format(category.name)
        )

    return redirect('competitions:combat:liste_poules', competition_id=competition_id)


@login_required
def promouvoir_vainqueurs_finale(request, competition_id, category_id):
    """
    Promeut automatiquement les vainqueurs des demi-finales vers la finale.
    Appelé lorsque les 2 demi-finales sont terminées.
    """
    from apps.competitions.models import Competition, CompetitionCategory

    if not manual_permission_check(request.user, 'competitions.change_competition'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires."))
        return redirect('competitions:dashboard:index')

    competition = get_object_or_404(Competition, id=competition_id)
    category = get_object_or_404(CompetitionCategory, id=category_id, competition=competition)

    # Récupérer la poule demi-finale de cette catégorie
    poule_demi = Poule.objects.filter(
        competition=competition,
        category=category,
        phase='demi'
    ).first()

    if not poule_demi:
        messages.error(request, _("Aucune demi-finale trouvée pour cette catégorie."))
        return redirect('competitions:combat:liste_poules', competition_id=competition_id)

    # Vérifier que les 2 demi-finales sont terminées
    combats_demi = Combat.objects.filter(poule=poule_demi, status='termine')
    if combats_demi.count() < 2:
        messages.warning(request, _("Les demi-finales ne sont pas encore toutes terminées."))
        return redirect('competitions:combat:liste_poules', competition_id=competition_id)

    # Récupérer les vainqueurs
    vainqueurs = []
    for combat in combats_demi:
        if combat.vainqueur == 'rouge':
            if combat.type_combat == 'equipe':
                vainqueurs.append({'participant': combat.equipe_rouge, 'is_equipe': True})
            else:
                vainqueurs.append({'participant': combat.pratiquant_rouge, 'is_equipe': False})
        elif combat.vainqueur == 'blanc':
            if combat.type_combat == 'equipe':
                vainqueurs.append({'participant': combat.equipe_blanc, 'is_equipe': True})
            else:
                vainqueurs.append({'participant': combat.pratiquant_blanc, 'is_equipe': False})

    if len(vainqueurs) < 2:
        messages.error(request, _("Impossible de déterminer les 2 vainqueurs des demi-finales."))
        return redirect('competitions:combat:liste_poules', competition_id=competition_id)

    # Récupérer ou créer la poule finale
    poule_finale = Poule.objects.filter(
        competition=competition,
        category=category,
        phase='finale'
    ).first()

    if not poule_finale:
        poule_finale = Poule.objects.create(
            competition=competition,
            category=category,
            nom=f"Finale - {category.name[:30]}",
            numero=200,
            phase='finale',
            description=f"Finale de la catégorie {category.name}"
        )

    # Supprimer les anciens combats de finale
    Combat.objects.filter(poule=poule_finale).delete()

    # Créer le combat de finale
    combat_data = {
        'competition': competition,
        'poule': poule_finale,
        'status': 'planifie',
    }

    if vainqueurs[0]['is_equipe']:
        combat_data['type_combat'] = 'equipe'
        combat_data['equipe_rouge'] = vainqueurs[0]['participant']
        combat_data['equipe_blanc'] = vainqueurs[1]['participant']
    else:
        combat_data['type_combat'] = 'individuel'
        combat_data['pratiquant_rouge'] = vainqueurs[0]['participant']
        combat_data['pratiquant_blanc'] = vainqueurs[1]['participant']

    Combat.objects.create(**combat_data)

    messages.success(
        request,
        _("Combat de finale créé pour '{}': {} vs {}").format(
            category.name,
            vainqueurs[0]['participant'],
            vainqueurs[1]['participant']
        )
    )

    return redirect('competitions:combat:detail_poule', poule_id=poule_finale.id)


# =============================================================================
# SPRINT 1-3: Nouvelles vues pour équipes, ententes, fusions et podium
# =============================================================================

from apps.competitions.models.combat import (
    TeamConfiguration, Entente, TeamMerge, PhaseFinale, PodiumEquipe
)
from apps.competitions.services import (
    EntenteService, TeamMergeService, CompetitionModeService
)


@login_required
def team_configuration(request, competition_id):
    """
    Sprint 1: Configuration des équipes (N titulaires + M remplaçants).
    """
    from apps.competitions.models import Competition
    competition = get_object_or_404(Competition, id=competition_id)

    try:
        config = competition.team_configuration
    except TeamConfiguration.DoesNotExist:
        config = None

    if request.method == 'POST':
        format_preset = request.POST.get('format_preset', '3+1')

        if config:
            config.format_preset = format_preset
            # Appliquer les presets
            if format_preset == '2+1':
                config.min_titulaires = config.max_titulaires = 2
                config.max_remplacants = 1
            elif format_preset == '3+1':
                config.min_titulaires = config.max_titulaires = 3
                config.max_remplacants = 1
            elif format_preset == '3+2':
                config.min_titulaires = config.max_titulaires = 3
                config.max_remplacants = 2
            elif format_preset == '5+2':
                config.min_titulaires = config.max_titulaires = 5
                config.max_remplacants = 2
            config.save()
        else:
            config = CompetitionModeService.configurer_mode_equipe(
                competition, format_preset=format_preset
            )

        messages.success(request, _("Configuration des équipes mise à jour."))
        return redirect('competitions:combat:team_configuration', competition_id=competition_id)

    return render(request, 'competitions/combat/team_configuration.html', {
        'competition': competition,
        'config': config,
    })


@login_required
def liste_ententes(request, competition_id):
    """
    Sprint 2: Liste des ententes (prêts de joueurs) pour une compétition.
    """
    from apps.competitions.models import Competition
    competition = get_object_or_404(Competition, id=competition_id)

    status_filter = request.GET.get('status', '')
    ententes = EntenteService.get_ententes_competition(competition, status=status_filter or None)

    # Compter par status
    all_ententes = Entente.objects.filter(competition=competition)
    total_count = all_ententes.count()
    pending_count = all_ententes.filter(status='pending').count()
    approved_count = all_ententes.filter(status='approved').count()
    rejected_count = all_ententes.filter(status='rejected').count()

    return render(request, 'competitions/combat/liste_ententes.html', {
        'competition': competition,
        'ententes': ententes,
        'status_filter': status_filter,
        'total_count': total_count,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
    })


@login_required
def creer_entente(request, competition_id):
    """
    Sprint 2: Créer une nouvelle entente.
    """
    from apps.competitions.models import Competition, Club, Practitioner
    competition = get_object_or_404(Competition, id=competition_id)

    clubs = Club.objects.filter(is_active=True).select_related('organization')

    # Build a list of clubs with their practitioners (via organization)
    clubs_avec_pratiquants = []
    for club in clubs:
        if club.organization:
            practitioners = Practitioner.objects.filter(
                organization=club.organization,
                is_active=True
            ).order_by('last_name', 'first_name')
            if practitioners.exists():
                clubs_avec_pratiquants.append({
                    'id': club.id,
                    'nom': club.name,
                    'practitioners': practitioners
                })

    if request.method == 'POST':
        try:
            pratiquant = get_object_or_404(Practitioner, id=request.POST.get('pratiquant'))
            club_origine = get_object_or_404(Club, id=request.POST.get('club_origine'))
            club_accueil = get_object_or_404(Club, id=request.POST.get('club_accueil'))
            role = request.POST.get('role', 'titulaire')
            raison = request.POST.get('raison', '')

            entente = EntenteService.creer_demande_entente(
                competition=competition,
                pratiquant=pratiquant,
                club_origine=club_origine,
                club_accueil=club_accueil,
                demandeur=request.user,
                role=role,
                raison=raison
            )
            messages.success(request, _("Demande d'entente créée avec succès."))
            return redirect('competitions:combat:liste_ententes', competition_id=competition_id)
        except Exception as e:
            messages.error(request, str(e))

    return render(request, 'competitions/combat/form_entente.html', {
        'competition': competition,
        'clubs': clubs,
        'clubs_avec_pratiquants': clubs_avec_pratiquants,
    })


@login_required
def approuver_entente(request, entente_id):
    """Sprint 2: Approuver une entente."""
    entente = get_object_or_404(Entente, id=entente_id)
    if request.method == 'POST':
        try:
            EntenteService.approuver_entente(entente, request.user)
            messages.success(request, _("Entente approuvée."))
        except Exception as e:
            messages.error(request, str(e))
    return redirect('competitions:combat:liste_ententes', competition_id=entente.competition.id)


@login_required
def refuser_entente(request, entente_id):
    """Sprint 2: Refuser une entente."""
    entente = get_object_or_404(Entente, id=entente_id)
    if request.method == 'POST':
        try:
            EntenteService.refuser_entente(entente, request.user)
            messages.success(request, _("Entente refusée."))
        except Exception as e:
            messages.error(request, str(e))
    return redirect('competitions:combat:liste_ententes', competition_id=entente.competition.id)


@login_required
def annuler_entente(request, entente_id):
    """Sprint 2: Annuler une entente."""
    entente = get_object_or_404(Entente, id=entente_id)
    if request.method == 'POST':
        try:
            EntenteService.annuler_entente(entente)
            messages.success(request, _("Entente annulée."))
        except Exception as e:
            messages.error(request, str(e))
    return redirect('competitions:combat:liste_ententes', competition_id=entente.competition.id)


@login_required
def liste_fusions(request, competition_id):
    """
    Sprint 2: Liste des demandes de fusion d'équipes.
    """
    from apps.competitions.models import Competition
    competition = get_object_or_404(Competition, id=competition_id)

    fusions = TeamMergeService.get_fusions_competition(competition)
    equipes_insuffisantes = TeamMergeService.get_equipes_fusionnables(competition)

    return render(request, 'competitions/combat/liste_fusions.html', {
        'competition': competition,
        'fusions': fusions,
        'equipes_insuffisantes': equipes_insuffisantes,
    })


@login_required
def creer_fusion(request, competition_id):
    """
    Sprint 2: Proposer une fusion d'équipes.
    """
    from apps.competitions.models import Competition
    competition = get_object_or_404(Competition, id=competition_id)

    equipes = Equipe.objects.filter(
        competition=competition,
        is_active=True
    ).select_related('club')

    equipes_insuffisantes = TeamMergeService.get_equipes_fusionnables(competition)

    try:
        min_titulaires = competition.team_configuration.min_titulaires
    except:
        min_titulaires = 3

    if request.method == 'POST':
        try:
            equipe_demandeur = get_object_or_404(Equipe, id=request.POST.get('equipe_demandeur'))
            equipe_cible = get_object_or_404(Equipe, id=request.POST.get('equipe_cible'))
            raison = request.POST.get('raison', '')
            nom_propose = request.POST.get('nom_equipe_proposee', '')

            fusion = TeamMergeService.creer_demande_fusion(
                equipe_demandeur=equipe_demandeur,
                equipe_cible=equipe_cible,
                demandeur=request.user,
                raison=raison,
                nom_equipe_proposee=nom_propose
            )
            messages.success(request, _("Demande de fusion créée avec succès."))
            return redirect('competitions:combat:liste_fusions', competition_id=competition_id)
        except Exception as e:
            messages.error(request, str(e))

    return render(request, 'competitions/combat/form_fusion.html', {
        'competition': competition,
        'equipes': equipes,
        'equipes_insuffisantes': equipes_insuffisantes,
        'min_titulaires': min_titulaires,
    })


@login_required
def approuver_fusion(request, fusion_id):
    """Sprint 2: Approuver une demande de fusion."""
    fusion = get_object_or_404(TeamMerge, id=fusion_id)
    if request.method == 'POST':
        try:
            TeamMergeService.approuver_fusion(fusion, request.user)
            messages.success(request, _("Fusion approuvée. Vous pouvez maintenant l'exécuter."))
        except Exception as e:
            messages.error(request, str(e))
    return redirect('competitions:combat:liste_fusions', competition_id=fusion.competition.id)


@login_required
def refuser_fusion(request, fusion_id):
    """Sprint 2: Refuser une demande de fusion."""
    fusion = get_object_or_404(TeamMerge, id=fusion_id)
    if request.method == 'POST':
        try:
            TeamMergeService.refuser_fusion(fusion, request.user)
            messages.success(request, _("Fusion refusée."))
        except Exception as e:
            messages.error(request, str(e))
    return redirect('competitions:combat:liste_fusions', competition_id=fusion.competition.id)


@login_required
def executer_fusion(request, fusion_id):
    """Sprint 2: Exécuter une fusion approuvée."""
    fusion = get_object_or_404(TeamMerge, id=fusion_id)
    if request.method == 'POST':
        try:
            equipe_fusionnee = TeamMergeService.executer_fusion(fusion)
            messages.success(request, _("Fusion exécutée. Nouvelle équipe: {nom}").format(
                nom=equipe_fusionnee.nom
            ))
        except Exception as e:
            messages.error(request, str(e))
    return redirect('competitions:combat:liste_fusions', competition_id=fusion.competition.id)


@login_required
def annuler_fusion(request, fusion_id):
    """Sprint 2: Annuler une demande de fusion."""
    fusion = get_object_or_404(TeamMerge, id=fusion_id)
    if request.method == 'POST':
        try:
            TeamMergeService.annuler_fusion(fusion)
            messages.success(request, _("Demande de fusion annulée."))
        except Exception as e:
            messages.error(request, str(e))
    return redirect('competitions:combat:liste_fusions', competition_id=fusion.competition.id)


@login_required
def competition_mode_switch(request, competition_id):
    """
    Interface pour basculer entre mode équipe et individuel PAR CATÉGORIE.
    Chaque catégorie combat peut avoir son propre mode (équipe ou individuel).
    """
    from apps.competitions.models import Competition, CompetitionCategory
    from django.db.models import Count, Q

    competition = get_object_or_404(Competition, id=competition_id)

    # Récupérer toutes les catégories combat de cette compétition
    categories_combat = CompetitionCategory.objects.filter(
        competition=competition,
        competition_type__scoring_system='combat'
    ).select_related('competition_type').order_by('name')

    # Pour chaque catégorie, calculer les stats
    categories_stats = []
    for cat in categories_combat:
        # Compter les équipes dans cette catégorie
        nb_equipes = Equipe.objects.filter(
            competition=competition,
            category=cat,
            is_active=True
        ).count()

        # Compter les pratiquants inscrits individuellement dans cette catégorie
        nb_participants_individuels = cat.registrations.count() if hasattr(cat, 'registrations') else 0

        # Compter les combats liés à cette catégorie
        nb_combats = Combat.objects.filter(
            competition=competition,
            poule__category=cat
        ).count()

        nb_combats_termines = Combat.objects.filter(
            competition=competition,
            poule__category=cat,
            status='termine'
        ).count()

        # Déterminer si on peut basculer
        peut_basculer_equipe = nb_participants_individuels >= 2  # Au moins 2 participants pour former des équipes
        peut_basculer_individuel = nb_equipes >= 1  # Au moins 1 équipe avec des membres

        categories_stats.append({
            'category': cat,
            'combat_mode': cat.combat_mode,  # 'team' ou 'individual'
            'nb_equipes': nb_equipes,
            'nb_participants': nb_participants_individuels,
            'nb_combats': nb_combats,
            'nb_combats_termines': nb_combats_termines,
            'peut_basculer_equipe': peut_basculer_equipe,
            'peut_basculer_individuel': peut_basculer_individuel,
        })

    # Traitement POST: basculer le mode d'une catégorie spécifique
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        new_mode = request.POST.get('new_mode')

        if category_id and new_mode in ['team', 'individual']:
            try:
                cat = CompetitionCategory.objects.get(
                    id=category_id,
                    competition=competition,
                    competition_type__scoring_system='combat'
                )

                old_mode = cat.combat_mode
                cat.combat_mode = new_mode
                cat.save()

                mode_label = _("Équipe") if new_mode == 'team' else _("Individuel")
                messages.success(request, _(
                    "Mode de la catégorie '{category}' basculé vers {mode}."
                ).format(category=cat.name, mode=mode_label))

            except CompetitionCategory.DoesNotExist:
                messages.error(request, _("Catégorie non trouvée."))
            except Exception as e:
                messages.error(request, str(e))

        return redirect('competitions:combat:competition_mode_switch', competition_id=competition_id)

    # Statistiques globales
    total_equipes = sum(c['nb_equipes'] for c in categories_stats)
    total_combats = sum(c['nb_combats'] for c in categories_stats)
    total_combats_termines = sum(c['nb_combats_termines'] for c in categories_stats)
    nb_categories_equipe = sum(1 for c in categories_stats if c['combat_mode'] == 'team')
    nb_categories_individuel = sum(1 for c in categories_stats if c['combat_mode'] == 'individual')

    return render(request, 'competitions/combat/competition_mode_switch.html', {
        'competition': competition,
        'categories_stats': categories_stats,
        'total_equipes': total_equipes,
        'total_combats': total_combats,
        'total_combats_termines': total_combats_termines,
        'nb_categories_equipe': nb_categories_equipe,
        'nb_categories_individuel': nb_categories_individuel,
        'nb_categories': len(categories_stats),
    })


@login_required
def podium_equipes(request, competition_id):
    """
    Sprint 3: Affichage du podium des équipes.
    """
    from apps.competitions.models import Competition
    competition = get_object_or_404(Competition, id=competition_id)

    podiums = PodiumEquipe.objects.filter(
        competition=competition
    ).select_related('equipe', 'equipe__club').order_by('place')

    return render(request, 'competitions/combat/podium_equipes.html', {
        'competition': competition,
        'podiums': podiums,
    })


@login_required
def export_podium(request, competition_id):
    """
    Sprint 3: Export PDF du podium.
    """
    # TODO: Implémenter l'export PDF
    messages.info(request, _("Export PDF en cours de développement."))
    return redirect('competitions:combat:podium_equipes', competition_id=competition_id)


@login_required
def api_equipes_club(request, club_id):
    """
    API: Retourne les équipes d'un club pour une compétition.
    """
    competition_id = request.GET.get('competition')
    equipes = Equipe.objects.filter(club_id=club_id, is_active=True)

    if competition_id:
        equipes = equipes.filter(competition_id=competition_id)

    data = {
        'equipes': [
            {'id': e.id, 'nom': e.nom}
            for e in equipes
        ]
    }
    return JsonResponse(data)


@login_required
@require_POST
def api_add_member_to_team(request, equipe_id):
    """API pour ajouter un pratiquant à une équipe via drag & drop."""
    if not manual_permission_check(request.user, 'competitions.change_equipe'):
        return JsonResponse({'success': False, 'message': 'Permission refusée'}, status=403)

    equipe = get_object_or_404(Equipe, id=equipe_id)
    data = json.loads(request.body)
    practitioner_id = data.get('practitioner_id')

    from apps.competitions.models import Practitioner
    practitioner = get_object_or_404(Practitioner, id=practitioner_id)

    if MembreEquipe.objects.filter(equipe=equipe, pratiquant=practitioner).exists():
        return JsonResponse({'success': False, 'message': str(_("Ce pratiquant est déjà dans l'équipe."))})

    max_ordre = MembreEquipe.objects.filter(equipe=equipe).order_by('-ordre').values_list('ordre', flat=True).first() or 0
    MembreEquipe.objects.create(equipe=equipe, pratiquant=practitioner, ordre=max_ordre + 1)

    return JsonResponse({
        'success': True,
        'message': str(_("Membre ajouté à l'équipe.")),
        'member_count': equipe.membres.count()
    })


@login_required
def api_search_practitioners(request, competition_id):
    """Recherche de pratiquants pour ajout rapide à une catégorie."""
    from apps.competitions.models import Practitioner, Competition
    if not manual_permission_check(request.user, 'competitions.change_competitioncategory'):
        return JsonResponse({'results': []})

    q = request.GET.get('q', '').strip()
    category_id = request.GET.get('category_id')
    if len(q) < 2:
        return JsonResponse({'results': []})

    competition = get_object_or_404(Competition, id=competition_id)
    practitioners = Practitioner.objects.filter(
        Q(first_name__icontains=q) | Q(last_name__icontains=q)
    ).select_related('organization', 'grade')[:20]

    # IDs des pratiquants déjà dans cette catégorie spécifique
    from apps.competitions.models import CompetitionRegistration
    if category_id:
        already_in_category_ids = set(CompetitionRegistration.objects.filter(
            competition=competition, categories__id=category_id
        ).values_list('practitioner_id', flat=True))
    else:
        already_in_category_ids = set()

    results = []
    for p in practitioners:
        results.append({
            'id': p.id,
            'name': p.get_full_name(),
            'club': p.organization.name if p.organization else '-',
            'birth_date': p.birth_date.strftime('%d/%m/%Y') if p.birth_date else '-',
            'age': p.age if p.birth_date else None,
            'grade': str(p.grade) if p.grade else '-',
            'already_in_category': p.id in already_in_category_ids
        })
    return JsonResponse({'results': results})


@login_required
@require_POST
def api_quick_add_to_category(request, competition_id):
    """Ajout rapide d'un pratiquant à une compétition + catégorie."""
    from apps.competitions.models import Competition, CompetitionRegistration, CompetitionCategory
    if not manual_permission_check(request.user, 'competitions.change_competitioncategory'):
        return JsonResponse({'success': False, 'message': 'Permission refusée'}, status=403)

    data = json.loads(request.body)
    practitioner_id = data.get('practitioner_id')
    category_id = data.get('category_id')

    competition = get_object_or_404(Competition, id=competition_id)
    from apps.competitions.models import Practitioner
    practitioner = get_object_or_404(Practitioner, id=practitioner_id)
    category = get_object_or_404(CompetitionCategory, id=category_id, competition=competition)

    # Créer ou récupérer l'inscription
    registration, created = CompetitionRegistration.objects.get_or_create(
        competition=competition,
        practitioner=practitioner,
        defaults={'status': 'confirmed'}
    )
    # Assigner à la catégorie
    registration.categories.add(category)

    return JsonResponse({
        'success': True,
        'message': str(_("Pratiquant ajouté à la catégorie.")),
        'registration_id': registration.id,
        'practitioner_name': practitioner.get_full_name(),
        'practitioner_club': practitioner.organization.name if practitioner.organization else '-',
        'practitioner_birth_date': practitioner.birth_date.strftime('%d/%m/%Y') if practitioner.birth_date else '-',
        'practitioner_age': practitioner.age if practitioner.birth_date else None,
        'practitioner_grade': str(practitioner.grade) if practitioner.grade else '',
        'practitioner_id': practitioner.id
    })


@login_required
def ajouter_combat_poule(request, poule_id):
    """Ajouter un combat à une poule existante."""
    if not manual_permission_check(request.user, 'competitions.add_combat'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires."))
        return redirect('competitions:dashboard:index')

    poule = get_object_or_404(Poule, id=poule_id)
    competition = poule.competition

    # Déterminer les combattants disponibles
    from apps.competitions.models import CompetitionRegistration
    equipes = list(poule.equipes.all())
    participants = []
    if poule.category:
        participants = list(CompetitionRegistration.objects.filter(
            competition=competition, categories=poule.category
        ).select_related('practitioner'))

    if request.method == 'POST':
        rouge_id = request.POST.get('rouge')
        blanc_id = request.POST.get('blanc')
        mode = request.POST.get('mode', 'individuel')

        if not rouge_id or not blanc_id:
            messages.error(request, _("Sélectionnez les deux combattants."))
        elif rouge_id == blanc_id:
            messages.error(request, _("Un combattant ne peut pas se battre contre lui-même."))
        else:
            combat_data = {
                'competition': competition,
                'poule': poule,
                'type_combat': mode,
                'status': 'planifie',
                'duree_combat': 120,
            }
            if mode == 'equipe':
                combat_data['equipe_rouge_id'] = rouge_id
                combat_data['equipe_blanc_id'] = blanc_id
            else:
                combat_data['pratiquant_rouge_id'] = rouge_id
                combat_data['pratiquant_blanc_id'] = blanc_id

            Combat.objects.create(**combat_data)
            messages.success(request, _("Combat créé avec succès."))
            return redirect('competitions:combat:detail_poule', poule_id=poule.id)

    return render(request, 'competitions/combat/ajouter_combat_poule.html', {
        'poule': poule,
        'competition': competition,
        'equipes': equipes,
        'participants': participants,
    })

