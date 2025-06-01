from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.db.models import Avg, Count, Sum, Q
from django.core.paginator import Paginator
from django.urls import reverse
from django.template.loader import render_to_string
import json
import csv
from django.views.decorators.http import require_POST

# Imports adaptés à la structure de votre projet
from competitions.models.technical_scoring import (
    ScoringCriterion,
    ScoringConfiguration,
    TechnicalPerformance,
    TechnicalScore,
    CompetitionRanking
)
from competitions.models import (
    Competition, 
    CompetitionCategory,
    Practitioner,
    Performance, 
    Score, 
    JudgeSubmissionStatus,
    JudgeSettings, 
    Notification,
    Discipline  # Discipline reste nécessaire pour d'autres fonctions
)
# Import des versions renommées dans scoring_results.py
from competitions.models.scoring_results import (
    TechnicalPerformanceResult,
    TechnicalScoreResult,
    JudgeSubmissionStatusResult
)
from django.contrib.auth.models import User
from competitions.forms.technical_scoring import (
    ScoringConfigurationForm,
    ScoringCriterionFormSet,
    TechnicalScoreForm,
    JudgeAssignmentForm,
    PerformanceOrderForm,
    StartPerformanceForm,
    PerformanceResultsForm,
    JudgeSettingsForm
    # JudgeApplicationForm a été supprimé, car maintenant dans judge.py
)
from competitions.utils.decorators import manager_required, judge_required

import logging
logger = logging.getLogger(__name__)

# ===== Vues pour les managers de compétition =====

@login_required
@manager_required
def category_scoring_setup(request, category_id):
    """Configuration du système de notation pour une catégorie"""
    category = get_object_or_404(CompetitionCategory, id=category_id)
    competition = category.competition
    
    # Vérifier que l'utilisateur a les permissions sur cette compétition
    if not request.user.has_perm('competitions.change_competition', competition):
        messages.error(request, _("Vous n'avez pas les permissions pour configurer cette catégorie."))
        return redirect('competitions:competitions:detail', pk=competition.id)
    
    # Récupérer ou créer la configuration
    config, created = ScoringConfiguration.objects.get_or_create(category=category)
    
    # Récupérer les critères existants
    criterion_formset = ScoringCriterionFormSet(
        request.POST or None,
        instance=category,
        prefix='criteria'
    )
    
    # Formulaire pour la configuration
    config_form = ScoringConfigurationForm(
        request.POST or None,
        instance=config,
        prefix='config'
    )
    
    if request.method == 'POST':
        if config_form.is_valid() and criterion_formset.is_valid():
            try:
                with transaction.atomic():
                    # Sauvegarder la configuration
                    config_form.save()
                    
                    # Sauvegarder les critères
                    criterion_formset.save()
                    
                    messages.success(request, _("Configuration de notation enregistrée avec succès."))
                    
                    # Rediriger vers la page de détail de la catégorie
                    return redirect('competitions:competitions:categories', competition_id=competition.id)
            except Exception as e:
                messages.error(request, _("Une erreur est survenue: {}").format(str(e)))
        else:
            # Afficher les erreurs
            for form in criterion_formset:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{form.prefix}-{field}: {error}")
    
    context = {
        'category': category,
        'competition': competition,
        'config_form': config_form,
        'criterion_formset': criterion_formset,
        'title': _("Configuration de la notation - {}").format(category.name)
    }
    
    return render(request, 'competitions/technical_scoring/setup.html', context)


@login_required
@manager_required
def assign_judges(request, category_id):
    """Assigner des juges à une catégorie"""
    category = get_object_or_404(CompetitionCategory, id=category_id)
    competition = category.competition
    
    # Vérifier que l'utilisateur a les permissions sur cette compétition
    if not request.user.has_perm('competitions.change_competition', competition):
        messages.error(request, _("Vous n'avez pas les permissions pour configurer cette catégorie."))
        return redirect('competitions:competitions:detail', pk=competition.id)
    
    # Préparer le formulaire d'assignation
    form = JudgeAssignmentForm(
        request.POST or None,
        competition=competition
    )
    
    # Récupérer les assignations actuelles
    current_assignments = {}
    chief_judge = None
    
    # Logique pour récupérer les assignations existantes
    # Cette partie dépend de la structure exacte de vos données
    
    if request.method == 'POST':
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Logique pour enregistrer les assignations
                    # Cette partie dépend de la structure exacte de vos données
                    
                    messages.success(request, _("Juges assignés avec succès."))
                    return redirect('competitions:competitions:categories', competition_id=competition.id)
            except Exception as e:
                messages.error(request, _("Une erreur est survenue: {}").format(str(e)))
    
    context = {
        'category': category,
        'competition': competition,
        'form': form,
        'title': _("Assignation des juges - {}").format(category.name)
    }
    
    return render(request, 'competitions/technical_scoring/assign_judges.html', context)

@login_required
def judge_competition_detail(request, competition_id):
    """
    Affiche les détails d'une compétition spécifique pour un juge,
    y compris les catégories et performances à évaluer.
    """
    competition = get_object_or_404(Competition, id=competition_id)
    
    # Vérifier que l'utilisateur est bien assigné comme juge pour cette compétition
    if not hasattr(request.user, 'judge') or not competition.judges.filter(id=request.user.id).exists():
        messages.error(request, _("Vous n'êtes pas autorisé à juger cette compétition."))
        return redirect('competitions:dashboard:referee')
    
    # Récupérer les catégories pour lesquelles l'utilisateur est juge
    judge_categories = competition.categories.filter(judge_assignments__registration__practitioner__user=request.user)
    
    # Récupérer les performances à juger (à venir et en cours)
    upcoming_performances = Performance.objects.filter(
        category__in=judge_categories,
        status__in=['scheduled', 'in_progress']
    ).order_by('scheduled_time')
    
    # Récupérer les performances déjà jugées
    judged_performances = Performance.objects.filter(
        category__in=judge_categories,
        status='completed',
        scores__judge=request.user.judge
    ).distinct().order_by('-completion_time')
    
    context = {
        'competition': competition,
        'judge_categories': judge_categories,
        'upcoming_performances': upcoming_performances,
        'judged_performances': judged_performances,
    }
    
    return render(request, 'competitions/technical_scoring/judge_competition_detail.html', context)

@login_required
@require_POST
def submit_score(request, performance_id):
    """
    Soumet les scores d'un juge pour une performance spécifique.
    """
    performance = get_object_or_404(Performance, id=performance_id)
    
    # Vérifier que l'utilisateur est bien assigné comme juge
    if not hasattr(request.user, 'judge'):
        messages.error(request, _("Vous n'êtes pas autorisé à soumettre des scores."))
        return redirect('competitions:dashboard:referee')
    
    # Vérifier que la performance est en cours
    if performance.status != 'in_progress':
        messages.error(request, _("Vous ne pouvez pas noter cette performance car elle n'est pas en cours."))
        return redirect('competitions:technical_scoring:judge_competition_detail', competition_id=performance.category.competition.id)
    
    try:
        with transaction.atomic():
            # Récupérer les critères et leurs scores
            criteria_ids = request.POST.getlist('criteria_id')
            scores = request.POST.getlist('score')
            
            # Supprimer les anciennes notes si existantes (en cas de modification)
            Score.objects.filter(performance=performance, judge=request.user.judge).delete()
            
            # Sauvegarder les nouvelles notes
            for i, criterion_id in enumerate(criteria_ids):
                criterion = get_object_or_404(ScoringCriterion, id=criterion_id)
                score_value = float(scores[i])
                
                # Vérifier que le score est dans la plage autorisée
                if score_value < criterion.min_score or score_value > criterion.max_score:
                    raise ValueError(f"Le score pour {criterion.name} doit être entre {criterion.min_score} et {criterion.max_score}")
                
                Score.objects.create(
                    performance=performance,
                    judge=request.user.judge,
                    criterion=criterion,
                    value=score_value
                )
            
            # Mettre à jour le statut de la soumission
            JudgeSubmissionStatus.objects.update_or_create(
                judge=request.user.judge,
                performance=performance,
                defaults={'submitted': True, 'submission_time': timezone.now()}
            )
            
            messages.success(request, _("Vos scores ont été soumis avec succès."))
            
            # Vérifier si tous les juges ont soumis leurs scores
            all_submitted = JudgeSubmissionStatus.objects.filter(
                performance=performance,
                submitted=True
            ).count() == performance.category.judges.count()
            
            if all_submitted:
                # Mettre à jour le statut de la performance
                performance.status = 'pending_validation'
                performance.save()
                
            return redirect('competitions:technical_scoring:judge_category_view', category_id=performance.category.id)
    
    except ValueError as e:
        messages.error(request, str(e))
        return redirect('competitions:technical_scoring:score_performance', performance_id=performance_id)
    except Exception as e:
        messages.error(request, _("Une erreur est survenue lors de la soumission des scores: {}").format(str(e)))
        return redirect('competitions:technical_scoring:score_performance', performance_id=performance_id)

@login_required
def judge_settings(request):
    """
    Permet au juge de configurer ses préférences personnelles
    pour l'interface de notation.
    """
    # Vérifier que l'utilisateur est un juge
    if not hasattr(request.user, 'judge'):
        messages.error(request, _("Vous n'êtes pas autorisé à accéder aux paramètres de juge."))
        return redirect('competitions:dashboard:index')  # ou 'competitions:welcome' selon votre configuration
    
    # Récupérer ou créer les paramètres du juge
    judge_settings, created = JudgeSettings.objects.get_or_create(
        judge=request.user.judge,
        defaults={
            'display_mode': 'standard',
            'notification_sounds': True,
            'auto_submit': False,
            'show_timer': True,
            'theme': 'light'
        }
    )
    
    if request.method == 'POST':
        form = JudgeSettingsForm(request.POST, instance=judge_settings)
        if form.is_valid():
            form.save()
            messages.success(request, _("Vos paramètres ont été enregistrés avec succès."))
            return redirect('competitions:technical_scoring:judge_dashboard')
    else:
        form = JudgeSettingsForm(instance=judge_settings)
    
    return render(request, 'competitions/technical_scoring/judge_settings.html', {
        'form': form
    })
    
def judge_help(request):
    """
    Affiche une page d'aide pour les juges avec des tutoriels
    sur l'utilisation du système de notation.
    """
    # Récupérer la langue de l'utilisateur pour afficher l'aide appropriée
    user_language = request.LANGUAGE_CODE if hasattr(request, 'LANGUAGE_CODE') else 'fr'
    
    # Différentes sections d'aide
    help_sections = {
        'getting_started': {
            'title': _("Premiers pas"),
            'content': _("Guide pour commencer avec l'interface de notation.")
        },
        'scoring_process': {
            'title': _("Processus de notation"),
            'content': _("Comment évaluer une performance étape par étape.")
        },
        'criteria_explanation': {
            'title': _("Explications des critères"),
            'content': _("Détails sur les différents critères de notation et leur interprétation.")
        },
        'troubleshooting': {
            'title': _("Résolution de problèmes"),
            'content': _("Solutions aux problèmes courants rencontrés lors de la notation.")
        }
    }
    
    # Tutoriels vidéo (liens)
    video_tutorials = [
        {
            'title': _("Comment noter une performance"),
            'url': "https://example.com/tutorials/scoring",
            'thumbnail': "scoring-thumbnail.jpg"
        },
        {
            'title': _("Utilisation de l'interface de juge"),
            'url': "https://example.com/tutorials/interface",
            'thumbnail': "interface-thumbnail.jpg"
        }
    ]
    
    return render(request, 'competitions/technical_scoring/judge_help.html', {
        'help_sections': help_sections,
        'video_tutorials': video_tutorials,
        'user_language': user_language
    })


@login_required
@manager_required
def manage_performances(request, category_id):
    """Gérer les prestations techniques d'une catégorie"""
    category = get_object_or_404(CompetitionCategory, id=category_id)
    competition = category.competition
    
    # Vérifier que l'utilisateur a les permissions sur cette compétition
    if not request.user.has_perm('competitions.change_competition', competition):
        messages.error(request, _("Vous n'avez pas les permissions pour gérer cette catégorie."))
        return redirect('competitions:competitions:detail', pk=competition.id)
    
    # Récupérer les prestations de cette catégorie
    performances = TechnicalPerformance.objects.filter(
        category=category
    ).order_by('performance_order', 'practitioner__last_name')
    
    # Vérifier s'il existe des prestations
    if not performances.exists():
        # Créer automatiquement les prestations pour tous les participants inscrits
        with transaction.atomic():
            # Récupérer tous les inscrits dans cette catégorie
            registrations = category.registrations.all()
            
            order = 1
            for registration in registrations:
                TechnicalPerformance.objects.create(
                    competition=competition,
                    category=category,
                    practitioner=registration.practitioner,
                    performance_order=order
                )
                order += 1
            
            # Recharger les prestations
            performances = TechnicalPerformance.objects.filter(
                category=category
            ).order_by('performance_order', 'practitioner__last_name')
            
            if performances.exists():
                messages.success(request, _("Les prestations ont été automatiquement créées."))
            else:
                messages.warning(request, _("Aucun participant n'est inscrit dans cette catégorie."))
    
    # Formulaire pour modifier l'ordre de passage
    order_form = PerformanceOrderForm(
        request.POST or None,
        category=category,
        prefix='order'
    ) if performances.exists() else None
    
    if request.method == 'POST' and order_form and order_form.is_valid():
        with transaction.atomic():
            # Mettre à jour l'ordre de passage de chaque performance
            for field_name, new_order in order_form.cleaned_data.items():
                if field_name.startswith('performance_'):
                    performance_id = int(field_name.split('_')[1])
                    performance = TechnicalPerformance.objects.get(id=performance_id)
                    performance.performance_order = new_order
                    performance.save()
            
            messages.success(request, _("Ordre de passage mis à jour avec succès."))
            return redirect('competitions:technical_scoring:manage_performances', category_id=category.id)
    
    context = {
        'category': category,
        'competition': competition,
        'performances': performances,
        'order_form': order_form,
        'title': _("Gestion des prestations - {}").format(category.name)
    }
    
    return render(request, 'competitions/technical_scoring/manage_performances.html', context)


@login_required
@manager_required
def start_performance(request, performance_id):
    """Démarrer une prestation technique"""
    performance = get_object_or_404(TechnicalPerformance, id=performance_id)
    category = performance.category
    competition = performance.competition
    
    # Vérifier que l'utilisateur a les permissions sur cette compétition
    if not request.user.has_perm('competitions.change_competition', competition):
        messages.error(request, _("Vous n'avez pas les permissions pour gérer cette prestation."))
        return redirect('competitions:competitions:detail', pk=competition.id)
    
    # Vérifier que la prestation n'est pas déjà terminée
    if performance.is_completed:
        messages.warning(request, _("Cette prestation est déjà terminée."))
        return redirect('competitions:technical_scoring:manage_performances', category_id=category.id)
    
    # Vérifier qu'aucune autre prestation n'est en cours dans cette catégorie
    if TechnicalPerformance.objects.filter(category=category, status='in_progress').exists():
        messages.error(request, _("Une autre prestation est déjà en cours dans cette catégorie."))
        return redirect('competitions:technical_scoring:manage_performances', category_id=category.id)
    
    # Formulaire de confirmation
    form = StartPerformanceForm(request.POST or None)
    
    if request.method == 'POST' and form.is_valid():
        performance.start_performance()
        messages.success(request, _("La prestation a démarré."))
        return redirect('competitions:technical_scoring:monitor_performance', performance_id=performance.id)
    
    context = {
        'performance': performance,
        'category': category,
        'competition': competition,
        'practitioner': performance.practitioner,
        'form': form,
        'title': _("Démarrer la prestation de {}").format(performance.practitioner.full_name)
    }
    
    return render(request, 'competitions/technical_scoring/start_performance.html', context)


@login_required
@manager_required
def monitor_performance(request, performance_id):
    """Suivre une prestation en cours"""
    performance = get_object_or_404(TechnicalPerformance, id=performance_id)
    category = performance.category
    competition = performance.competition
    
    # Vérifier que l'utilisateur a les permissions sur cette compétition
    if not request.user.has_perm('competitions.change_competition', competition):
        messages.error(request, _("Vous n'avez pas les permissions pour gérer cette prestation."))
        return redirect('competitions:competitions:detail', pk=competition.id)
    
    # Récupérer tous les critères de cette catégorie
    criteria = ScoringCriterion.objects.filter(category=category, is_active=True).order_by('order')
    
    # Récupérer tous les juges assignés
    judges = User.objects.filter(
        Q(judge_assignments__category=category) |
        Q(chief_judge_assignments__category=category)
    ).distinct()
    
    # Récupérer les notes actuelles
    scores = TechnicalScore.objects.filter(
        performance=performance
    ).select_related('judge', 'criterion')
    
    # Organiser les notes par juge et critère
    scores_by_judge = {}
    for score in scores:
        if score.judge.id not in scores_by_judge:
            scores_by_judge[score.judge.id] = {}
        scores_by_judge[score.judge.id][score.criterion.id] = score.value
    
    # Vérifier si tous les juges ont soumis leurs notes
    all_scores_submitted = True
    for judge in judges:
        if judge.id not in scores_by_judge:
            all_scores_submitted = False
            break
        elif len(scores_by_judge[judge.id]) != len(criteria):
            all_scores_submitted = False
            break
    
    # Formulaire pour terminer la prestation
    if request.method == 'POST' and 'end_performance' in request.POST:
        performance.end_performance()
        messages.success(request, _("La prestation est terminée."))
        return redirect('competitions:technical_scoring:performance_results', performance_id=performance.id)
    
    context = {
        'performance': performance,
        'category': category,
        'competition': competition,
        'practitioner': performance.practitioner,
        'criteria': criteria,
        'judges': judges,
        'scores_by_judge': scores_by_judge,
        'all_scores_submitted': all_scores_submitted,
        'title': _("Suivi de la prestation de {}").format(performance.practitioner.full_name)
    }
    
    return render(request, 'competitions/technical_scoring/monitor_performance.html', context)


@login_required
@manager_required
def performance_results(request, performance_id):
    """Afficher et valider les résultats d'une prestation"""
    performance = get_object_or_404(TechnicalPerformance, id=performance_id)
    category = performance.category
    competition = performance.competition
    
    # Vérifier que l'utilisateur a les permissions sur cette compétition
    if not request.user.has_perm('competitions.change_competition', competition):
        messages.error(request, _("Vous n'avez pas les permissions pour gérer cette prestation."))
        return redirect('competitions:competitions:detail', pk=competition.id)
    
    # Vérifier que la prestation est terminée
    if not performance.is_completed:
        messages.warning(request, _("Cette prestation n'est pas encore terminée."))
        return redirect('competitions:technical_scoring:monitor_performance', performance_id=performance.id)
    
    # Récupérer la configuration de notation
    config = ScoringConfiguration.objects.filter(category=category).first()
    
    # Récupérer tous les critères de cette catégorie
    criteria = ScoringCriterion.objects.filter(category=category, is_active=True).order_by('order')
    
    # Récupérer tous les juges assignés
    judges = User.objects.filter(
        Q(judge_assignments__category=category) |
        Q(chief_judge_assignments__category=category)
    ).distinct()
    
    # Récupérer les notes
    scores = TechnicalScore.objects.filter(
        performance=performance
    ).select_related('judge', 'criterion')
    
    # Organiser les notes par juge et critère
    scores_by_judge = {}
    scores_by_criterion = {}
    
    for score in scores:
        # Par juge
        if score.judge.id not in scores_by_judge:
            scores_by_judge[score.judge.id] = {}
        scores_by_judge[score.judge.id][score.criterion.id] = score.value
        
        # Par critère
        if score.criterion.id not in scores_by_criterion:
            scores_by_criterion[score.criterion.id] = []
        scores_by_criterion[score.criterion.id].append({
            'judge': score.judge,
            'value': score.value
        })
    
    # Calculer le score final
    final_score = performance.calculate_final_score()
    
    # Formulaire pour valider les résultats
    form = PerformanceResultsForm(request.POST or None)
    
    if request.method == 'POST' and form.is_valid():
        # Créer ou mettre à jour le classement
        ranking, created = CompetitionRanking.objects.update_or_create(
            competition=competition,
            category=category,
            practitioner=performance.practitioner,
            defaults={
                'final_score': final_score,
                'rank': 0  # Sera calculé ultérieurement
            }
        )
        
        # Si l'option de publication est sélectionnée, calculer le classement
        if form.cleaned_data.get('publish_results'):
            # Calculer le classement pour toutes les prestations terminées
            calculate_rankings(category)
            messages.success(request, _("Résultats validés et publiés."))
        else:
            messages.success(request, _("Résultats validés."))
        
        return redirect('competitions:technical_scoring:manage_performances', category_id=category.id)
    
    context = {
        'performance': performance,
        'category': category,
        'competition': competition,
        'practitioner': performance.practitioner,
        'criteria': criteria,
        'judges': judges,
        'scores_by_judge': scores_by_judge,
        'scores_by_criterion': scores_by_criterion,
        'final_score': final_score,
        'form': form,
        'title': _("Résultats de {}").format(performance.practitioner.full_name)
    }
    
    return render(request, 'competitions/technical_scoring/performance_results.html', context)


@login_required
@manager_required
def category_results(request, category_id):
    """Afficher les résultats complets d'une catégorie"""
    category = get_object_or_404(CompetitionCategory, id=category_id)
    competition = category.competition
    
    # Vérifier que l'utilisateur a les permissions sur cette compétition
    if not request.user.has_perm('competitions.view_competition', competition):
        messages.error(request, _("Vous n'avez pas les permissions pour voir cette catégorie."))
        return redirect('competitions:competitions:detail', pk=competition.id)
    
    # Récupérer tous les classements
    rankings = CompetitionRanking.objects.filter(
        category=category
    ).select_related('practitioner').order_by('rank')
    
    # Vérifier s'il y a des classements
    if not rankings.exists():
        messages.warning(request, _("Aucun résultat n'est disponible pour cette catégorie."))
        return redirect('competitions:technical_scoring:manage_performances', category_id=category.id)
    
    # Récupérer les prestations pour voir les détails
    performances = TechnicalPerformance.objects.filter(
        category=category,
        is_completed=True
    ).select_related('practitioner')
    
    # Map des performances par practitioner
    performances_by_practitioner = {p.practitioner.id: p for p in performances}
    
    # Récupérer la configuration de notation
    config = ScoringConfiguration.objects.filter(category=category).first()
    
    # Proposer de recalculer le classement
    if request.method == 'POST' and 'recalculate' in request.POST:
        calculate_rankings(category)
        messages.success(request, _("Classement recalculé avec succès."))
        return redirect('competitions:technical_scoring:category_results', category_id=category.id)
    
    # Proposer d'exporter les résultats
    if request.method == 'POST' and 'export_csv' in request.POST:
        return export_results_csv(category)
    
    context = {
        'category': category,
        'competition': competition,
        'rankings': rankings,
        'performances': performances,
        'performances_by_practitioner': performances_by_practitioner,
        'config': config,
        'title': _("Résultats - {}").format(category.name)
    }
    
    return render(request, 'competitions/technical_scoring/category_results.html', context)


# ===== Vues pour les juges =====

@login_required
@judge_required
def judge_dashboard(request):
    """Tableau de bord du juge"""
    # Récupérer les compétitions où l'utilisateur est juge
    judge_assignments = request.user.judge_assignments.all().select_related('category', 'category__competition')
    chief_judge_assignments = request.user.chief_judge_assignments.all().select_related('category', 'category__competition')
    
    # Combiner les assignations
    categories = set()
    for assignment in list(judge_assignments) + list(chief_judge_assignments):
        categories.add(assignment.category)
    
    # Récupérer les compétitions uniques
    competitions = set(category.competition for category in categories)
    
    # Vérifier s'il y a des prestations en cours dans ces catégories
    active_performances = TechnicalPerformance.objects.filter(
        category__in=categories,
        status='in_progress'
    ).select_related('category', 'practitioner')
    
    # Récupérer l'historique des notes récentes
    recent_scores = TechnicalScore.objects.filter(
        judge=request.user
    ).select_related('performance', 'performance__practitioner', 'criterion').order_by('-submitted_at')[:10]
    
    context = {
        'competitions': competitions,
        'categories': categories,
        'active_performances': active_performances,
        'recent_scores': recent_scores
    }
    
    return render(request, 'competitions/judge/dashboard.html', context)


@login_required
@judge_required
def judge_category_view(request, category_id):
    """Vue de catégorie pour un juge"""
    category = get_object_or_404(CompetitionCategory, id=category_id)
    competition = category.competition
    
    # Vérifier que l'utilisateur est bien juge pour cette catégorie
    is_judge = request.user.judge_assignments.filter(category=category).exists()
    is_chief_judge = request.user.chief_judge_assignments.filter(category=category).exists()
    
    if not (is_judge or is_chief_judge):
        messages.error(request, _("Vous n'êtes pas assigné comme juge pour cette catégorie."))
        return redirect('competitions:technical_scoring:judge_dashboard')
    
    # Récupérer les prestations
    performances = TechnicalPerformance.objects.filter(
        category=category
    ).select_related('practitioner').order_by('performance_order', 'practitioner__last_name')
    
    # Récupérer la performance active s'il y en a une
    active_performance = performances.filter(status='in_progress').first()
    
    # Récupérer les critères de notation
    criteria = ScoringCriterion.objects.filter(category=category, is_active=True).order_by('order')
    
    # Récupérer les notes déjà saisies par ce juge
    scores = TechnicalScore.objects.filter(
        judge=request.user,
        performance__category=category
    ).select_related('performance', 'criterion')
    
    # Organiser les scores par performance et critère
    scores_by_performance = {}
    for score in scores:
        if score.performance.id not in scores_by_performance:
            scores_by_performance[score.performance.id] = {}
        scores_by_performance[score.performance.id][score.criterion.id] = score.value
    
    context = {
        'category': category,
        'competition': competition,
        'performances': performances,
        'active_performance': active_performance,
        'criteria': criteria,
        'scores_by_performance': scores_by_performance,
        'is_chief_judge': is_chief_judge,
        'title': _("Catégorie : {}").format(category.name)
    }
    
    return render(request, 'competitions/judge/category_view.html', context)

@login_required
@judge_required
def judge_competition_list(request):
    """Afficher la liste des compétitions où l'utilisateur est assigné comme juge."""
    # Récupérer les catégories où l'utilisateur est juge
    judge_categories = set()
    
    # Récupérer les catégories où l'utilisateur est juge normal
    judge_assignments = request.user.judge_assignments.all().select_related('category', 'category__competition')
    for assignment in judge_assignments:
        judge_categories.add(assignment.category)
    
    # Récupérer les catégories où l'utilisateur est juge en chef
    chief_judge_assignments = request.user.chief_judge_assignments.all().select_related('category', 'category__competition')
    for assignment in chief_judge_assignments:
        judge_categories.add(assignment.category)
    
    # Extraire les compétitions uniques
    competitions = set(category.competition for category in judge_categories)
    competitions_list = sorted(competitions, key=lambda comp: comp.start_date)
    
    # Organiser les catégories par compétition
    categories_by_competition = {}
    for category in judge_categories:
        if category.competition.id not in categories_by_competition:
            categories_by_competition[category.competition.id] = []
        categories_by_competition[category.competition.id].append(category)
    
    # Regrouper par statut
    upcoming_competitions = []
    ongoing_competitions = []
    past_competitions = []
    
    now = timezone.now().date()
    for comp in competitions_list:
        if comp.end_date < now:
            past_competitions.append(comp)
        elif comp.start_date > now:
            upcoming_competitions.append(comp)
        else:
            ongoing_competitions.append(comp)
    
    context = {
        'upcoming_competitions': upcoming_competitions,
        'ongoing_competitions': ongoing_competitions,
        'past_competitions': past_competitions,
        'categories_by_competition': categories_by_competition,
        'title': _("Mes compétitions à juger")
    }
    
    return render(request, 'competitions/judge/competition_list.html', context)

@login_required
@judge_required
def score_performance(request, performance_id):
    """Saisir les notes pour une prestation"""
    performance = get_object_or_404(TechnicalPerformance, id=performance_id)
    category = performance.category
    competition = performance.competition
    
    # Vérifier que l'utilisateur est bien juge pour cette catégorie
    is_judge = request.user.judge_assignments.filter(category=category).exists()
    is_chief_judge = request.user.chief_judge_assignments.filter(category=category).exists()
    
    if not (is_judge or is_chief_judge):
        messages.error(request, _("Vous n'êtes pas assigné comme juge pour cette catégorie."))
        return redirect('competitions:technical_scoring:judge_dashboard')
    
    # Vérifier que la prestation est bien en cours
    if performance.status != 'in_progress':
        messages.warning(request, _("Cette prestation n'est pas en cours actuellement."))
        return redirect('competitions:technical_scoring:judge_category_view', category_id=category.id)
    
    # Récupérer la configuration de notation
    config = ScoringConfiguration.objects.filter(category=category).first()
    
    # Récupérer les critères de notation
    criteria = ScoringCriterion.objects.filter(category=category, is_active=True).order_by('order')
    
    # Récupérer les notes déjà saisies
    scores = TechnicalScore.objects.filter(
        judge=request.user,
        performance=performance
    ).select_related('criterion')
    
    # Organiser les scores par critère
    scores_by_criterion = {score.criterion.id: score for score in scores}
    
    # Vérifier si toutes les notes ont été saisies
    all_scores_submitted = len(scores) == len(criteria)
    
    if request.method == 'POST':
        if 'submit_scores' in request.POST:
            try:
                with transaction.atomic():
                    for criterion in criteria:
                        value_key = f'criterion_{criterion.id}'
                        if value_key in request.POST and request.POST[value_key]:
                            try:
                                value = float(request.POST[value_key])
                                
                                # Vérifier que la note est dans la plage autorisée
                                min_score = config.min_score if config else 0
                                max_score = config.max_score if config else 10
                                
                                if value < min_score or value > max_score:
                                    messages.error(request, _("La note doit être comprise entre {} et {}.").format(min_score, max_score))
                                    continue
                                
                                # Créer ou mettre à jour le score
                                TechnicalScore.objects.update_or_create(
                                    judge=request.user,
                                    performance=performance,
                                    criterion=criterion,
                                    defaults={'value': value}
                                )
                            except ValueError:
                                messages.error(request, _("Valeur invalide pour le critère {}.").format(criterion.name))
                    
                    messages.success(request, _("Notes enregistrées avec succès."))
                    return redirect('competitions:technical_scoring:judge_category_view', category_id=category.id)
            except Exception as e:
                messages.error(request, _("Une erreur est survenue: {}").format(str(e)))
    
    context = {
        'performance': performance,
        'category': category,
        'competition': competition,
        'practitioner': performance.practitioner,
        'criteria': criteria,
        'scores_by_criterion': scores_by_criterion,
        'all_scores_submitted': all_scores_submitted,
        'config': config,
        'title': _("Notation: {}").format(performance.practitioner.full_name)
    }
    
    return render(request, 'competitions/judge/score_performance.html', context)


# ===== Vues publiques =====

def public_results(request, category_id):
    """Afficher les résultats publics d'une catégorie"""
    category = get_object_or_404(CompetitionCategory, id=category_id)
    competition = category.competition
    
    # Récupérer la configuration
    config = ScoringConfiguration.objects.filter(category=category).first()
    
    # Vérifier si l'affichage public est autorisé
    if not config or not config.display_public_results:
        messages.error(request, _("Les résultats de cette catégorie ne sont pas disponibles publiquement."))
        return redirect('competitions:competitions:detail', pk=competition.id)
    
    # Récupérer les classements
    rankings = CompetitionRanking.objects.filter(
        category=category
    ).select_related('practitioner').order_by('rank')
    
    context = {
        'category': category,
        'competition': competition,
        'rankings': rankings,
        'config': config,
        'title': _("Résultats - {}").format(category.name)
    }
    
    return render(request, 'competitions/technical_scoring/public_results.html', context)


# ===== Fonctions utilitaires =====

def calculate_rankings(category):
    """Calculer le classement pour une catégorie"""
    # Récupérer la configuration
    config = ScoringConfiguration.objects.filter(category=category).first()
    
    # Récupérer tous les classements existants
    rankings = CompetitionRanking.objects.filter(
        category=category
    ).select_related('practitioner').order_by('-final_score')
    
    # Si aucun classement n'existe, rien à faire
    if not rankings:
        return
    
    # Attribuer les rangs
    current_rank = 1
    previous_score = None
    previous_rank = 1
    
    for i, ranking in enumerate(rankings):
        if previous_score is not None and ranking.final_score < previous_score:
            current_rank = i + 1
        
        ranking.rank = current_rank
        ranking.save()
        
        previous_score = ranking.final_score
        previous_rank = current_rank
    
    # Gérer les ex-aequo pour la 3ème place si configuré
    if config and config.third_place_tie_allowed:
        handle_third_place_ties(category)


def handle_third_place_ties(category):
    """Gérer les ex-aequo pour la 3ème place"""
    third_place_rankings = CompetitionRanking.objects.filter(
        category=category,
        rank=3
    )
    
    # S'il y a plusieurs 3èmes places, les mettre toutes au même rang
    if third_place_rankings.count() > 1:
        for ranking in third_place_rankings:
            ranking.is_tie = True
            ranking.save()


def export_results_csv(category):
    """Exporter les résultats en CSV"""
    # Nom du fichier
    filename = f"resultats_{category.name}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    # Créer la réponse HTTP avec le bon content-type
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Créer le writer CSV
    writer = csv.writer(response)
    
    # Écrire l'en-tête
    writer.writerow([
        _('Rang'), 
        _('Nom'), 
        _('Prénom'), 
        _('Club'), 
        _('Score Final'),
        _('Ex-aequo')
    ])
    
    # Récupérer les classements
    rankings = CompetitionRanking.objects.filter(
        category=category
    ).select_related('practitioner').order_by('rank')
    
    # Écrire les données
    for ranking in rankings:
        writer.writerow([
            ranking.rank,
            ranking.practitioner.last_name,
            ranking.practitioner.first_name,
            ranking.practitioner.club.name if ranking.practitioner.club else '',
            ranking.final_score,
            _('Oui') if ranking.is_tie else _('Non')
        ])
    
    return response


# ===== API JSON pour les mises à jour en temps réel =====

@login_required
def get_performance_scores(request, performance_id):
    """API pour récupérer les notes d'une prestation en temps réel"""
    try:
        performance = TechnicalPerformance.objects.get(id=performance_id)
        
        # Vérifier les permissions
        is_manager = request.user.has_perm('competitions.change_competition', performance.competition)
        is_judge = request.user.judge_assignments.filter(category=performance.category).exists()
        is_chief_judge = request.user.chief_judge_assignments.filter(category=performance.category).exists()
        
        if not (is_manager or is_judge or is_chief_judge):
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Récupérer tous les critères
        criteria = ScoringCriterion.objects.filter(
            category=performance.category, 
            is_active=True
        ).values('id', 'name', 'order', 'weight')
        
        # Récupérer tous les juges assignés
        judges = User.objects.filter(
            Q(judge_assignments__category=performance.category) |
            Q(chief_judge_assignments__category=performance.category)
        ).values('id', 'first_name', 'last_name')
        
        # Récupérer les notes
        scores = TechnicalScore.objects.filter(
            performance=performance
        ).values('judge_id', 'criterion_id', 'value')
        
        # Organiser les scores pour l'API
        scores_data = {}
        for score in scores:
            if score['judge_id'] not in scores_data:
                scores_data[score['judge_id']] = {}
            scores_data[score['judge_id']][score['criterion_id']] = score['value']
        
        # Construire la réponse
        data = {
            'performance': {
                'id': performance.id,
                'practitioner': f"{performance.practitioner.first_name} {performance.practitioner.last_name}",
                'status': performance.status,
                'start_time': performance.start_time.isoformat() if performance.start_time else None,
                'end_time': performance.end_time.isoformat() if performance.end_time else None,
                'is_completed': performance.is_completed
            },
            'criteria': list(criteria),
            'judges': list(judges),
            'scores': scores_data
        }
        
        return JsonResponse(data)
    except TechnicalPerformance.DoesNotExist:
        return JsonResponse({'error': 'Performance not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def get_category_results(request, category_id):
    """API pour récupérer les résultats d'une catégorie en temps réel"""
    try:
        category = CompetitionCategory.objects.get(id=category_id)
        
        # Vérifier si l'utilisateur a accès à ces résultats
        config = ScoringConfiguration.objects.filter(category=category).first()
        
        if not config.display_public_results and not request.user.has_perm('competitions.view_competition', category.competition):
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Récupérer les classements
        rankings = CompetitionRanking.objects.filter(
            category=category
        ).select_related('practitioner').order_by('rank')
        
        # Préparer les données
        results = []
        for rank in rankings:
            results.append({
                'rank': rank.rank,
                'practitioner_id': rank.practitioner.id,
                'name': f"{rank.practitioner.first_name} {rank.practitioner.last_name}",
                'club': rank.practitioner.club.name if rank.practitioner.club else None,
                'final_score': rank.final_score,
                'is_tie': rank.is_tie
            })
        
        data = {
            'category': {
                'id': category.id,
                'name': category.name,
                'competition_id': category.competition.id,
                'competition_name': category.competition.title
            },
            'results': results,
            'last_updated': timezone.now().isoformat()
        }
        
        return JsonResponse(data)
    except CompetitionCategory.DoesNotExist:
        return JsonResponse({'error': 'Category not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)