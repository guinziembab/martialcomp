from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Sum, Avg, Max, F
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db import transaction

from apps.competitions.models import (
    Competition, CompetitionCategory, Match, CompetitionRegistration,
    Club
)
# Import unified scoring models
from apps.competitions.models.scoring_results import (
    CategoryRanking, RankingEntry, TechnicalPerformanceResult,
    PerformanceResult, CompetitionResult
)
from apps.competitions.utils.decorators import competition_management_permission_required
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset


@login_required
@competition_management_permission_required
def results_dashboard(request, competition_id):
    """
    Tableau de bord des résultats pour une compétition.
    """
    # Récupérer la compétition
    competition = get_object_or_404(Competition, pk=competition_id)
    
    # Récupérer les catégories de la compétition
    categories = CompetitionCategory.objects.filter(competition=competition)
    
    # Ajouter des informations sur l'état des résultats
    for category in categories:
        # Vérifier si des résultats existent pour cette catégorie
        category.has_results = CategoryRanking.objects.filter(
            competition=competition,
            category=category
        ).exists()
        
        # Nombre de performances terminées
        category.completed_performances_count = TechnicalPerformanceResult.objects.filter(
            category=category,
            status='completed'
        ).count()
        
        # Nombre total de performances
        category.total_performances_count = TechnicalPerformanceResult.objects.filter(
            category=category
        ).count()
        
        # Vérifier si la catégorie est terminée
        category.is_completed = category.status == 'completed'
    
    context = {
        'competition': competition,
        'categories': categories,
    }
    
    return render(request, 'competitions/management/results_dashboard.html', context)


@login_required
@competition_management_permission_required
def category_results(request, competition_id, category_id):
    """
    Affiche les résultats d'une catégorie spécifique.
    """
    # Récupérer la compétition et la catégorie
    competition = get_object_or_404(Competition, pk=competition_id)
    category = get_object_or_404(CompetitionCategory, pk=category_id, competition=competition)
    
    # Vérifier si un classement existe
    category_ranking = CategoryRanking.objects.filter(
        competition=competition,
        category=category
    ).first()
    
    # Récupérer les résultats
    if category_ranking:
        rankings = RankingEntry.objects.filter(
            ranking=category_ranking
        ).select_related('practitioner').order_by('rank')
        has_results = rankings.exists()
    else:
        rankings = []
        has_results = False
    
    # Récupérer les configurations de scoring
    from apps.competitions.models.technical_scoring import ScoringConfiguration
    try:
        scoring_config = ScoringConfiguration.objects.get(category=category)
    except ScoringConfiguration.DoesNotExist:
        scoring_config = None
    
    context = {
        'competition': competition,
        'category': category,
        'rankings': rankings,
        'has_results': has_results,
        'scoring_config': scoring_config,
        'category_ranking': category_ranking
    }
    
    return render(request, 'competitions/management/category_results.html', context)


@login_required
@competition_management_permission_required
def calculate_category_results(request, competition_id, category_id):
    """
    Calcule les résultats pour une catégorie (redirects vers la vue de scoring).
    """
    # Importer la vue de scoring pour le calcul des résultats
    from apps.competitions.views.management.scoring import calculate_results
    
    # Utiliser la vue de scoring
    return calculate_results(request, competition_id, category_id)


@login_required
@competition_management_permission_required
def edit_ranking(request, competition_id, ranking_entry_id):
    """
    Modifie manuellement un classement.
    """
    # Récupérer la compétition et l'entrée de classement
    competition = get_object_or_404(Competition, pk=competition_id)
    ranking_entry = get_object_or_404(
        RankingEntry, 
        pk=ranking_entry_id, 
        ranking__competition=competition
    )
    
    if request.method == 'POST':
        # Récupérer les nouvelles valeurs
        new_rank = request.POST.get('rank')
        new_score = request.POST.get('score')
        is_tie = request.POST.get('is_tie') == 'on'
        
        try:
            # Valider les valeurs
            if new_rank:
                ranking_entry.rank = int(new_rank)
            
            if new_score:
                ranking_entry.score = float(new_score)
            
            ranking_entry.is_tie = is_tie
            ranking_entry.save()
            
            # Mettre Ã  jour le résultat de performance associé si existant
            if ranking_entry.performance and hasattr(ranking_entry.performance, 'result'):
                result = ranking_entry.performance.result
                result.rank = ranking_entry.rank
                result.is_tie = ranking_entry.is_tie
                result.save(update_fields=['rank', 'is_tie'])
            
            messages.success(request, _("Le classement a été mis Ã  jour avec succès."))
        except ValueError:
            messages.error(request, _("Valeurs invalides. Veuillez vérifier les données saisies."))
        
        return redirect('competitions:management:category_results', 
                      competition_id=competition_id, 
                      category_id=ranking_entry.ranking.category.id)
    
    context = {
        'competition': competition,
        'ranking_entry': ranking_entry,
    }
    
    return render(request, 'competitions/management/edit_ranking.html', context)


@login_required
@competition_management_permission_required
@require_POST
def delete_ranking(request, competition_id, ranking_entry_id):
    """
    Supprime une entrée de classement.
    """
    # Récupérer la compétition et l'entrée de classement
    competition = get_object_or_404(Competition, pk=competition_id)
    ranking_entry = get_object_or_404(
        RankingEntry, 
        pk=ranking_entry_id, 
        ranking__competition=competition
    )
    
    category_id = ranking_entry.ranking.category.id
    
    # Supprimer l'entrée de classement
    ranking_entry.delete()
    
    messages.success(request, _("Le classement a été supprimé."))
    return redirect('competitions:management:category_results', 
                  competition_id=competition_id, 
                  category_id=category_id)


@login_required
@competition_management_permission_required
def all_competition_results(request, competition_id):
    """
    Affiche tous les résultats de la compétition.
    """
    # Récupérer la compétition
    competition = get_object_or_404(Competition, pk=competition_id)
    
    # Récupérer les catégories avec des résultats
    categories = CompetitionCategory.objects.filter(
        competition=competition,
        category_rankings__isnull=False
    ).distinct()
    
    # Récupérer les résultats par catégorie
    results_by_category = {}
    for category in categories:
        category_ranking = CategoryRanking.objects.get(
            competition=competition,
            category=category
        )
        
        rankings = RankingEntry.objects.filter(
            ranking=category_ranking
        ).select_related('practitioner').order_by('rank')
        
        results_by_category[category.id] = rankings
    
    context = {
        'competition': competition,
        'categories': categories,
        'results_by_category': results_by_category,
    }
    
    return render(request, 'competitions/management/all_results.html', context)


@login_required
@competition_management_permission_required
def export_all_results(request, competition_id):
    """
    Exporte tous les résultats de la compétition au format CSV.
    """
    # Récupérer la compétition
    competition = get_object_or_404(Competition, pk=competition_id)
    
    # Récupérer toutes les catégories avec des résultats
    categories = CompetitionCategory.objects.filter(
        competition=competition,
        category_rankings__isnull=False
    ).distinct()
    
    # Exporter en CSV
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{competition.title}_results.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        _('Catégorie'), _('Rang'), _('Nom'), _('Prénom'), 
        _('Club'), _('Score'), _('Ex-aequo')
    ])
    
    for category in categories:
        category_ranking = CategoryRanking.objects.get(
            competition=competition,
            category=category
        )
        
        rankings = RankingEntry.objects.filter(
            ranking=category_ranking
        ).select_related('practitioner').order_by('rank')
        
        for ranking in rankings:
            p = ranking.practitioner
            writer.writerow([
                category.name,
                ranking.rank,
                p.last_name,
                p.first_name,
                p.club.name if p.club else "",
                ranking.score,
                _('Oui') if ranking.is_tie else _('Non')
            ])
    
    return response


@login_required
@competition_management_permission_required
def club_results(request, competition_id):
    """
    Affiche les résultats groupés par club.
    """
    # Récupérer la compétition
    competition = get_object_or_404(Competition, pk=competition_id)
    
    # Récupérer tous les clubs participants
    clubs = Club.objects.filter(
        practitioners__registrations__competition=competition
    ).distinct()
    
    # Récupérer les résultats pour chaque club
    clubs_results = {}
    for club in clubs:
        # Récupérer les entrées de classement des pratiquants de ce club
        rankings = RankingEntry.objects.filter(
            ranking__competition=competition,
            practitioner__club=club
        ).select_related('practitioner', 'ranking__category').order_by('ranking__category__name', 'rank')
        
        # Compter les médailles
        gold_medals = rankings.filter(rank=1).count()
        silver_medals = rankings.filter(rank=2).count()
        bronze_medals = rankings.filter(rank=3).count()
        
        # Calculer un score global (3 points pour l'or, 2 pour l'argent, 1 pour le bronze)
        total_score = (gold_medals * 3) + (silver_medals * 2) + bronze_medals
        
        clubs_results[club.id] = {
            'club': club,
            'rankings': rankings,
            'gold_medals': gold_medals,
            'silver_medals': silver_medals,
            'bronze_medals': bronze_medals,
            'total_medals': gold_medals + silver_medals + bronze_medals,
            'total_score': total_score
        }
    
    # Trier les clubs par score total
    sorted_clubs = sorted(clubs_results.values(), key=lambda x: (-x['total_score'], -x['gold_medals'], -x['silver_medals'], -x['bronze_medals']))
    
    context = {
        'competition': competition,
        'clubs_results': sorted_clubs,
    }
    
    return render(request, 'competitions/management/club_results.html', context)


@login_required
@competition_management_permission_required
def publish_all_results(request, competition_id):
    """
    Publie tous les résultats de la compétition.
    """
    # Récupérer la compétition
    competition = get_object_or_404(Competition, pk=competition_id)
    
    if request.method == 'POST':
        # Marquer la compétition comme terminée
        competition.status = 'completed'
        competition.save()
        
        # Marquer toutes les catégories comme terminées
        CompetitionCategory.objects.filter(competition=competition).update(status='completed')
        
        # Publier tous les classements de catégorie
        CategoryRanking.objects.filter(competition=competition).update(
            is_published=True,
            is_final=True,
            published_at=timezone.now()
        )
        
        # Synchroniser avec le modèle CompetitionResult pour la compatibilité
        with transaction.atomic():
            for ranking in CategoryRanking.objects.filter(competition=competition):
                for entry in RankingEntry.objects.filter(ranking=ranking):
                    # Déterminer le type de médaille
                    medal = 'none'
                    if entry.rank == 1:
                        medal = 'gold'
                    elif entry.rank == 2:
                        medal = 'silver'
                    elif entry.rank == 3:
                        medal = 'bronze'
                    
                    # Créer ou mettre Ã  jour le résultat de compétition
                    CompetitionResult.objects.update_or_create(
                        competition=competition,
                        category=ranking.category,
                        practitioner=entry.practitioner,
                        defaults={
                            'rank': entry.rank,
                            'score': entry.score,
                            'medal': medal,
                            'date': timezone.now().date(),
                        }
                    )
        
        messages.success(request, _("Tous les résultats ont été publiés."))
    
    return redirect('competitions:management:results_dashboard', competition_id=competition_id)


@login_required
@competition_management_permission_required
def podium_preview(request, competition_id, category_id):
    """
    Prévisualisation du podium pour une catégorie.
    """
    # Récupérer la compétition et la catégorie
    competition = get_object_or_404(Competition, pk=competition_id)
    category = get_object_or_404(CompetitionCategory, pk=category_id, competition=competition)
    
    # Récupérer le classement de la catégorie
    category_ranking = get_object_or_404(
        CategoryRanking,
        competition=competition,
        category=category
    )
    
    # Récupérer les 3 premiers du classement
    podium = RankingEntry.objects.filter(
        ranking=category_ranking,
        rank__lte=3
    ).select_related('practitioner').order_by('rank')
    
    context = {
        'competition': competition,
        'category': category,
        'podium': podium,
    }
    
    return render(request, 'competitions/management/podium_preview.html', context)


@login_required
@competition_management_permission_required
def medals_report(request, competition_id):
    """
    Rapport sur les médailles distribuées.
    """
    # Récupérer la compétition
    competition = get_object_or_404(Competition, pk=competition_id)
    
    # Compter les médailles par catégorie
    categories = CompetitionCategory.objects.filter(competition=competition)
    
    medals_by_category = {}
    total_medals = {'gold': 0, 'silver': 0, 'bronze': 0, 'total': 0}
    
    for category in categories:
        try:
            category_ranking = CategoryRanking.objects.get(competition=competition, category=category)
            gold = RankingEntry.objects.filter(ranking=category_ranking, rank=1).count()
            silver = RankingEntry.objects.filter(ranking=category_ranking, rank=2).count()
            bronze = RankingEntry.objects.filter(ranking=category_ranking, rank=3).count()
            
            medals_by_category[category.id] = {
                'category': category,
                'gold': gold,
                'silver': silver,
                'bronze': bronze,
                'total': gold + silver + bronze
            }
            
            total_medals['gold'] += gold
            total_medals['silver'] += silver
            total_medals['bronze'] += bronze
            total_medals['total'] += gold + silver + bronze
        except CategoryRanking.DoesNotExist:
            # Ignorer les catégories sans classement
            pass
    
    # Compter les médailles par club
    from django.db.models import Count, Case, When, IntegerField
    
    clubs_medals = []
    for club in Club.objects.filter(practitioners__ranking_entries__ranking__competition=competition).distinct():
        entries = RankingEntry.objects.filter(
            ranking__competition=competition,
            practitioner__club=club,
            rank__lte=3
        )
        
        gold = entries.filter(rank=1).count()
        silver = entries.filter(rank=2).count()
        bronze = entries.filter(rank=3).count()
        total = gold + silver + bronze
        
        if total > 0:
            clubs_medals.append({
                'club__name': club.name,
                'gold': gold,
                'silver': silver,
                'bronze': bronze,
                'total': total
            })
    
    # Trier par or, puis argent, puis bronze
    clubs_medals.sort(key=lambda x: (-x['gold'], -x['silver'], -x['bronze']))
    
    context = {
        'competition': competition,
        'medals_by_category': medals_by_category,
        'total_medals': total_medals,
        'clubs_medals': clubs_medals,
    }
    
    return render(request, 'competitions/management/medals_report.html', context)


@login_required
@competition_management_permission_required
def public_results_link(request, competition_id):
    """
    Génère un lien pour les résultats publics.
    """
    # Récupérer la compétition
    competition = get_object_or_404(Competition, pk=competition_id)
    
    # Générer ou récupérer un token de partage existant
    from apps.competitions.models import CompetitionShareToken
    
    token, created = CompetitionShareToken.objects.get_or_create(
        competition=competition,
        token_type='results',
        defaults={
            'created_by': request.user,
            'expires_at': timezone.now() + timezone.timedelta(days=30)
        }
    )
    
    if not created and (not token.expires_at or token.expires_at < timezone.now()):
        # Renouveler le token s'il a expiré
        token.expires_at = timezone.now() + timezone.timedelta(days=30)
        token.save()
    
    # Construire l'URL
    results_url = request.build_absolute_uri(
        f'/competitions/{competition_id}/results/public/{token.token}/'
    )
    
    context = {
        'competition': competition,
        'token': token,
        'results_url': results_url,
    }
    
    return render(request, 'competitions/management/public_results_link.html', context)


def public_results(request, competition_id, token):
    """
    Affiche les résultats publics de la compétition (accessible sans connexion).
    """
    # Récupérer la compétition
    competition = get_object_or_404(Competition, pk=competition_id)
    
    # Vérifier la validité du token
    from apps.competitions.models import CompetitionShareToken
    
    token_obj = get_object_or_404(
        CompetitionShareToken, 
        competition=competition,
        token=token,
        token_type='results'
    )
    
    # Vérifier si le token n'a pas expiré
    if token_obj.expires_at and token_obj.expires_at < timezone.now():
        return render(request, 'competitions/public/expired_token.html')
    
    # Récupérer les catégories avec des résultats
    categories = CompetitionCategory.objects.filter(
        competition=competition,
        category_rankings__isnull=False
    ).distinct()
    
    # Récupérer les résultats par catégorie
    results_by_category = {}
    for category in categories:
        category_ranking = CategoryRanking.objects.filter(
            competition=competition,
            category=category,
            is_published=True  # Ne montrer que les résultats publiés
        ).first()
        
        if category_ranking:
            rankings = RankingEntry.objects.filter(
                ranking=category_ranking
            ).select_related('practitioner').order_by('rank')
            
            results_by_category[category.id] = rankings
    
    context = {
        'competition': competition,
        'categories': categories,
        'results_by_category': results_by_category,
    }
    
    return render(request, 'competitions/public/competition_results.html', context)

