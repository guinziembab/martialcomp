from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.contrib import messages
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset


@login_required
def technical_scoring_management(request, competition_id=None):
    """
    Interface de management centralisée pour les compétitions techniques.
    """
    from ..models import Competition, CompetitionCategory
    
    competition = None
    if competition_id:
        try:
            competition = Competition.objects.get(id=competition_id)
        except Competition.DoesNotExist:
            messages.error(request, _("Compétition non trouvée."))
            return redirect('competitions:technical_scoring:management')
    
    # Récupérer toutes les compétitions disponibles
    competitions = Competition.objects.filter(
        status__in=['published', 'ongoing', 'draft']
    ).order_by('-created_at')
    
    categories = []
    performances = []
    judge_assignments = []
    
    if competition:
        # Récupérer les catégories de la compétition
        categories = competition.categories.all()
        # TODO: Récupérer les performances et assignations
    
    context = {
        'competition': competition,
        'competitions': competitions,
        'categories': categories,
        'performances': performances,
        'judge_assignments': judge_assignments,
        'management_sections': [
            {
                'title': _('Configuration des catégories'),
                'description': _('Définir les critères de notation par catégorie'),
                'url': 'setup' if competition_id else None,
                'icon': 'fas fa-cogs',
                'color': 'primary'
            },
            {
                'title': _('Affectation des juges'),
                'description': _('Assigner les juges aux catégories'),
                'url': 'assign_judges' if competition_id else None,
                'icon': 'fas fa-user-tie',
                'color': 'info'
            },
            {
                'title': _('Gestion des performances'),
                'description': _('Organiser et suivre les performances'),
                'url': 'manage_performances' if competition_id else None,
                'icon': 'fas fa-play-circle',
                'color': 'success'
            },
            {
                'title': _('Suivi en temps réel'),
                'description': _('Monitor des performances en cours'),
                'url': None,  # URL dynamique selon performances actives
                'icon': 'fas fa-eye',
                'color': 'warning'
            },
            {
                'title': _('Résultats et classements'),
                'description': _('Consulter les résultats par catégorie'),
                'url': None,  # URL dynamique selon catégories
                'icon': 'fas fa-trophy',
                'color': 'danger'
            }
        ]
    }
    
    return render(request, 'competitions/technical_scoring/management_dashboard.html', context)


@login_required
def judge_dashboard(request):
    """
    Tableau de bord des juges pour la notation technique.
    """
    # TODO: Implémenter la logique pour récupérer les compétitions assignées au juge
    user = request.user
    assigned_competitions = []  # À remplacer par la vraie requête
    pending_scores = []  # Scores en attente
    completed_scores = []  # Scores terminés
    
    # Statistiques
    stats = {
        'total_competitions': 0,
        'pending_matches': 0,
        'completed_matches': 0,
        'average_score_time': '0 min',
    }
    
    context = {
        'user': user,
        'assigned_competitions': assigned_competitions,
        'pending_scores': pending_scores,
        'completed_scores': completed_scores,
        'stats': stats,
    }
    
    return render(request, 'competitions/technical_scoring/judge_dashboard.html', context)


@login_required
def scoring_interface(request, competition_id, category_id=None):
    """
    Interface de notation technique pour les juges.
    """
    # TODO: Implémenter la logique de notation
    # competition = get_object_or_404(Competition, id=competition_id)
    # category = get_object_or_404(Category, id=category_id) if category_id else None
    
    if request.method == 'POST':
        # Traitement des scores soumis
        # TODO: Implémenter la sauvegarde des scores
        messages.success(request, _("Scores enregistrés avec succès."))
        return JsonResponse({'status': 'success'})
    
    # Données pour l'interface de notation
    context = {
        'competition_id': competition_id,
        'category_id': category_id,
        # 'competition': competition,
        # 'category': category,
        'participants': [],  # Liste des participants à noter
        'scoring_criteria': [],  # Critères de notation
    }
    
    return render(request, 'competitions/technical_scoring/scoring_interface.html', context)


@login_required  
def scoring_history(request, competition_id=None):
    """
    Historique des notations effectuées par le juge.
    """
    user = request.user
    # TODO: Filtrer l'historique par utilisateur et optionnellement par compétition
    
    scoring_history = []  # Historique des notations
    
    context = {
        'user': user,
        'competition_id': competition_id,
        'scoring_history': scoring_history,
    }
    
    return render(request, 'competitions/technical_scoring/scoring_history.html', context)


@login_required
def scoring_categories(request, competition_id=None):
    """
    Gestion des catégories de notation pour une compétition.
    """
    # TODO: Récupérer les catégories de notation
    # competition = get_object_or_404(Competition, id=competition_id) if competition_id else None
    
    categories = []  # Liste des catégories de notation
    
    context = {
        'competition_id': competition_id,
        # 'competition': competition,
        'categories': categories,
    }
    
    return render(request, 'competitions/technical_scoring/categories.html', context)


# ===== VUES POUR LES MANAGERS =====

@login_required
def category_scoring_setup(request, competition_id=None):
    """
    Configuration des catégories de notation pour une compétition.
    """
    from ..models import Competition, CompetitionCategory
    
    if not competition_id:
        messages.error(request, _("ID de compétition requis."))
        return redirect('competitions:technical_scoring:management')
    
    try:
        competition = Competition.objects.get(id=competition_id)
    except Competition.DoesNotExist:
        messages.error(request, _("Compétition non trouvée."))
        return redirect('competitions:technical_scoring:management')
    
    # Get first category for this competition as an example
    # In a real implementation, this should be passed as a parameter
    category = competition.categories.first()
    if not category:
        messages.warning(request, _("Aucune catégorie trouvée pour cette compétition."))
        category = None
    
    # Mock data for now - in a real implementation, these would come from the database
    criteria = []
    config = None
    
    # Mock forms - in a real implementation, these would be proper Django forms
    criterion_form = None
    config_form = None
    
    if request.method == 'POST':
        if 'generate_default' in request.POST:
            messages.success(request, _("Critères par défaut générés (simulation)."))
        elif 'add_criterion' in request.POST:
            messages.success(request, _("Critère ajouté (simulation)."))
        elif 'update_config' in request.POST:
            messages.success(request, _("Configuration mise à jour (simulation)."))
    
    context = {
        'competition': competition,
        'category': category,
        'criteria': criteria,
        'config': config,
        'criterion_form': criterion_form,
        'config_form': config_form,
    }
    return render(request, 'competitions/technical_scoring/category_setup.html', context)


@login_required
def assign_judges(request, competition_id=None):
    """
    Assignation des juges aux compétitions et catégories.
    """
    from ..models import Competition, CompetitionCategory
    
    if not competition_id:
        messages.error(request, _("ID de compétition requis."))
        return redirect('competitions:technical_scoring:management')
    
    try:
        competition = Competition.objects.get(id=competition_id)
    except Competition.DoesNotExist:
        messages.error(request, _("Compétition non trouvée."))
        return redirect('competitions:technical_scoring:management')
    
    # Get first category for this competition as an example
    # In a real implementation, this should be passed as a parameter
    category = competition.categories.first()
    if not category:
        messages.warning(request, _("Aucune catégorie trouvée pour cette compétition."))
        # Create a mock category object for template compatibility
        class MockCategory:
            name = _("Aucune catégorie")
            id = None
        category = MockCategory()
    
    # Mock data for now - in a real implementation, these would come from the database
    available_judges = []
    assigned_judges = []
    
    if request.method == 'POST':
        if 'assign_judge' in request.POST:
            messages.success(request, _("Juge assigné (simulation)."))
        elif 'remove_judge' in request.POST:
            messages.success(request, _("Juge retiré (simulation)."))
    
    context = {
        'competition': competition,
        'category': category,
        'available_judges': available_judges,
        'assigned_judges': assigned_judges,
    }
    return render(request, 'competitions/technical_scoring/assign_judges.html', context)


@login_required
def manage_performances(request, competition_id=None):
    """
    Gestion des performances à noter.
    """
    from ..models import Competition, CompetitionCategory
    
    if not competition_id:
        messages.error(request, _("ID de compétition requis."))
        return redirect('competitions:technical_scoring:management')
    
    try:
        competition = Competition.objects.get(id=competition_id)
    except Competition.DoesNotExist:
        messages.error(request, _("Compétition non trouvée."))
        return redirect('competitions:technical_scoring:management')
    
    # Get first category for this competition as an example
    # In a real implementation, this should be passed as a parameter
    categories = competition.categories.all()
    category = categories.first()
    
    if not category:
        messages.warning(request, _("Aucune catégorie trouvée pour cette compétition. Veuillez créer des catégories d'abord."))
        # Create a mock category object for template compatibility
        class MockCategory:
            name = _("Aucune catégorie")
            id = None
        category = MockCategory()
    
    # Mock data for now - in a real implementation, these would come from the database
    performances = []
    practitioners = []
    context_categories = categories if categories.exists() else []
    
    if request.method == 'POST':
        if 'add_performance' in request.POST:
            messages.success(request, _("Performance ajoutée (simulation)."))
        elif 'remove_performance' in request.POST:
            messages.success(request, _("Performance supprimée (simulation)."))
        elif 'start_performance' in request.POST:
            messages.success(request, _("Performance démarrée (simulation)."))
    
    context = {
        'competition': competition,
        'category': category,
        'categories': context_categories,
        'performances': performances,
        'practitioners': practitioners,
    }
    return render(request, 'competitions/technical_scoring/manage_performances.html', context)


@login_required
def start_performance(request, performance_id):
    """
    Démarrage d'une performance pour notation.
    """
    # TODO: Implémenter le démarrage de performance
    context = {
        'performance_id': performance_id,
    }
    return render(request, 'competitions/technical_scoring/start_performance.html', context)


@login_required
def monitor_performance(request, performance_id):
    """
    Monitoring d'une performance en cours.
    """
    # TODO: Implémenter le monitoring
    context = {
        'performance_id': performance_id,
    }
    return render(request, 'competitions/technical_scoring/monitor_performance.html', context)


@login_required
def performance_results(request, performance_id):
    """
    Résultats d'une performance spécifique.
    """
    # TODO: Implémenter l'affichage des résultats
    context = {
        'performance_id': performance_id,
    }
    return render(request, 'competitions/technical_scoring/performance_results.html', context)


@login_required
def category_results(request, category_id):
    """
    Résultats d'une catégorie complète.
    """
    # TODO: Implémenter l'affichage des résultats de catégorie
    context = {
        'category_id': category_id,
    }
    return render(request, 'competitions/technical_scoring/category_results.html', context)


# ===== VUES SUPPLÉMENTAIRES POUR LES JUGES =====

@login_required
def judge_competition_list(request):
    """
    Liste des compétitions assignées au juge.
    """
    # TODO: Implémenter la liste des compétitions
    context = {
        'competitions': [],
    }
    return render(request, 'competitions/technical_scoring/judge_competition_list.html', context)


@login_required
def judge_competition_detail(request, competition_id):
    """
    Détail d'une compétition pour le juge.
    """
    # TODO: Implémenter le détail de compétition
    context = {
        'competition_id': competition_id,
    }
    return render(request, 'competitions/technical_scoring/judge_competition_detail.html', context)


@login_required
def judge_category_view(request, category_id):
    """
    Vue d'une catégorie spécifique pour le juge.
    """
    # TODO: Implémenter la vue de catégorie
    context = {
        'category_id': category_id,
    }
    return render(request, 'competitions/technical_scoring/judge_category_view.html', context)


@login_required
def score_performance(request, performance_id):
    """
    Interface de notation pour une performance spécifique.
    """
    # TODO: Implémenter la notation de performance
    context = {
        'performance_id': performance_id,
    }
    return render(request, 'competitions/technical_scoring/score_performance.html', context)


@login_required
def submit_score(request):
    """
    Soumission d'un score via AJAX.
    """
    if request.method == 'POST':
        # TODO: Traiter la soumission de score
        return JsonResponse({'status': 'success', 'message': 'Score soumis avec succès'})
    
    return JsonResponse({'status': 'error', 'message': 'Méthode non autorisée'})


@login_required
def judge_settings(request):
    """
    Paramètres du juge.
    """
    # TODO: Implémenter les paramètres
    context = {}
    return render(request, 'competitions/technical_scoring/judge_settings.html', context)


@login_required
def judge_help(request):
    """
    Aide pour les juges.
    """
    # TODO: Implémenter l'aide
    context = {}
    return render(request, 'competitions/technical_scoring/judge_help.html', context)


# ===== APIs =====

@login_required
def get_performance_scores(request, performance_id):
    """
    API pour récupérer les scores d'une performance.
    """
    # TODO: Implémenter l'API de récupération des scores
    scores = {
        'performance_id': performance_id,
        'scores': [],
        'total_score': 0,
    }
    return JsonResponse(scores)


@login_required
def get_category_results(request, category_id):
    """
    API pour récupérer les résultats d'une catégorie.
    """
    # TODO: Implémenter l'API de récupération des résultats
    results = {
        'category_id': category_id,
        'results': [],
        'ranking': [],
    }
    return JsonResponse(results)