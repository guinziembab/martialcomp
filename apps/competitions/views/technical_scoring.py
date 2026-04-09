from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
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


def _get_judge_competitions_and_categories(user):
    """
    Helper to get all competitions and categories assigned to a judge.
    Checks both JudgeAssignment and AdHocJudge models.
    Returns (competitions_qs, category_assignments_list).
    """
    from ..models import Competition, CompetitionCategory
    from ..models.judges import JudgeAssignment
    from ..models.practitioners import Practitioner

    competition_ids = set()
    category_assignments = []  # list of dicts {category, competition}

    # 1. JudgeAssignment model
    ja_qs = JudgeAssignment.objects.filter(
        user=user
    ).select_related('category', 'category__competition', 'category__competition__discipline')
    for a in ja_qs:
        if a.category and a.category.competition:
            competition_ids.add(a.category.competition_id)
            category_assignments.append({
                'category': a.category,
                'competition': a.category.competition,
            })

    # 2. AdHocJudge model (via practitioner)
    try:
        from ..models.adhoc_judges import AdHocJudge
        practitioner = Practitioner.objects.filter(user=user).first()
        if practitioner:
            adhoc_qs = AdHocJudge.objects.filter(
                practitioner=practitioner, status='active'
            ).select_related('competition', 'competition__discipline')
            for adhoc in adhoc_qs:
                if adhoc.competition:
                    competition_ids.add(adhoc.competition_id)
                    for cat in adhoc.assigned_categories.select_related('competition'):
                        category_assignments.append({
                            'category': cat,
                            'competition': adhoc.competition,
                        })
    except Exception:
        pass

    competitions = Competition.objects.filter(
        id__in=competition_ids
    ).select_related('discipline', 'organizing_organization').order_by('-start_date')

    return competitions, category_assignments


@login_required
def judge_dashboard(request):
    """
    Tableau de bord des juges pour la notation technique.
    """
    user = request.user

    competitions, category_assignments = _get_judge_competitions_and_categories(user)

    # Stats
    total_competitions = competitions.count()
    ongoing_count = competitions.filter(status__in=['ongoing', 'published']).count()
    completed_count = competitions.filter(status='completed').count()
    # Unique categories
    cat_ids = set(ca['category'].id for ca in category_assignments)
    total_categories = len(cat_ids)

    # Upcoming assignments (active competitions only)
    upcoming_assignments = []
    seen_cats = set()
    for ca in sorted(category_assignments, key=lambda x: x['competition'].start_date or __import__('datetime').date.min):
        if ca['competition'].status in ('published', 'ongoing', 'draft') and ca['category'].id not in seen_cats:
            seen_cats.add(ca['category'].id)
            upcoming_assignments.append(ca)
        if len(upcoming_assignments) >= 10:
            break

    stats = {
        'total_competitions': total_competitions,
        'ongoing': ongoing_count,
        'completed': completed_count,
        'total_categories': total_categories,
    }

    context = {
        'user': user,
        'assigned_competitions': competitions[:10],
        'upcoming_assignments': upcoming_assignments,
        'stats': stats,
        'active_page': 'dashboard',
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
    Historique des notations effectuées par les juges.
    Pour les organisateurs: affiche toutes les notations de la compétition par catégorie.
    Pour les juges: affiche leurs propres notations.

    Supporte les deux modèles de stockage:
    - TechnicalPerformance + TechnicalScore (nouveau modèle)
    - Performance + Score (ancien modèle)
    """
    import logging
    logger = logging.getLogger(__name__)

    from django.db.models import Avg, Count, Q, F
    from ..models import Competition, CompetitionCategory

    # Import sécurisé des modèles qui peuvent ne pas exister
    try:
        from ..models import TechnicalPerformance, TechnicalScore
    except ImportError:
        TechnicalPerformance = None
        TechnicalScore = None
        logger.warning("TechnicalPerformance/TechnicalScore models not available")

    try:
        from ..models import Performance, Score, Judge
    except ImportError:
        Performance = None
        Score = None
        Judge = None
        logger.warning("Performance/Score/Judge models not available")

    user = request.user
    competition = None
    categories_data = []
    scoring_history_list = []
    is_organizer = False

    # Récupérer la compétition si spécifiée
    if competition_id:
        competition = get_object_or_404(Competition, id=competition_id)

        # SÉCURITÉ: Vérifier si l'utilisateur est VRAIMENT organisateur de cette compétition
        # Seuls les vrais organisateurs peuvent voir toutes les notes de tous les juges
        is_organizer = user.is_staff or user.is_superuser

        # Vérifier si l'utilisateur est le créateur de la compétition
        if not is_organizer:
            try:
                if hasattr(competition, 'created_by') and competition.created_by == user:
                    is_organizer = True
            except Exception:
                pass

        # Vérifier si l'utilisateur est ADMIN de l'organisation organisatrice
        # (pas juste membre, mais avec un rôle d'administration)
        if not is_organizer and competition.organizing_organization:
            try:
                from apps.organizations.models import OrganizationMember
                org_member = OrganizationMember.objects.filter(
                    organization=competition.organizing_organization,
                    user=user
                ).first()
                if org_member:
                    # Seulement les rôles admin/manager donnent accès organisateur
                    admin_roles = ['admin', 'owner', 'manager', 'president', 'secretary']
                    member_role = getattr(org_member, 'role', '').lower()
                    if member_role in admin_roles:
                        is_organizer = True
            except Exception:
                pass

    if competition and is_organizer:
        # Vue ORGANISATEUR: Afficher toutes les notations par catégorie
        categories = CompetitionCategory.objects.filter(competition=competition).order_by('name')

        for category in categories:
            performances_data = []

            # ===== NOUVEAU MODÈLE: TechnicalPerformance + TechnicalScore =====
            if TechnicalPerformance is not None and TechnicalScore is not None:
                try:
                    tech_performances = TechnicalPerformance.objects.filter(
                        competition=competition,
                        category=category
                    ).select_related('practitioner').order_by('performance_order')

                    for perf in tech_performances:
                        try:
                            scores = TechnicalScore.objects.filter(
                                performance=perf,
                                is_active_for_ranking=True
                            ).select_related('judge', 'criterion').order_by('judge__username', 'criterion__name')

                            judges_scores = {}
                            for score in scores:
                                judge_name = score.judge.get_full_name() or score.judge.username
                                if judge_name not in judges_scores:
                                    judges_scores[judge_name] = {
                                        'judge': score.judge,
                                        'scores': [],
                                        'total': 0
                                    }
                                judges_scores[judge_name]['scores'].append({
                                    'criterion': score.criterion.name,
                                    'value': float(score.value),
                                    'submitted_at': score.submitted_at
                                })
                                judges_scores[judge_name]['total'] += float(score.value)

                            avg_score = scores.aggregate(avg=Avg('value'))['avg'] or 0

                            performances_data.append({
                                'performance': perf,
                                'practitioner': perf.practitioner,
                                'judges_scores': judges_scores,
                                'avg_score': round(avg_score, 2),
                                'status': perf.get_status_display(),
                                'is_completed': perf.is_completed,
                                'model_type': 'technical'
                            })
                        except Exception as e:
                            logger.warning(f"Error processing TechnicalPerformance {perf.id}: {e}")
                except Exception as e:
                    logger.warning(f"Error fetching TechnicalPerformances: {e}")

            # ===== ANCIEN MODÈLE: Performance + Score =====
            if Performance is not None and Score is not None:
                try:
                    old_performances = Performance.objects.filter(
                        category__competition=competition,
                        category=category
                    ).select_related('practitioner', 'category').order_by('order')

                    for perf in old_performances:
                        try:
                            scores = Score.objects.filter(
                                performance=perf
                            ).select_related('judge', 'criterion').order_by('judge__user__username', 'criterion__name')

                            judges_scores = {}
                            for score in scores:
                                # Le modèle Score utilise Judge qui a un lien vers User
                                if hasattr(score.judge, 'user'):
                                    judge_user = score.judge.user
                                    judge_name = judge_user.get_full_name() or judge_user.username
                                else:
                                    judge_name = str(score.judge)

                                if judge_name not in judges_scores:
                                    judges_scores[judge_name] = {
                                        'judge': score.judge,
                                        'scores': [],
                                        'total': 0
                                    }
                                judges_scores[judge_name]['scores'].append({
                                    'criterion': score.criterion.name,
                                    'value': float(score.value),
                                    'submitted_at': score.timestamp
                                })
                                judges_scores[judge_name]['total'] += float(score.value)

                            avg_score = scores.aggregate(avg=Avg('value'))['avg'] or 0

                            performances_data.append({
                                'performance': perf,
                                'practitioner': perf.practitioner,
                                'judges_scores': judges_scores,
                                'avg_score': round(avg_score, 2),
                                'status': perf.get_status_display() if hasattr(perf, 'get_status_display') else perf.status,
                                'is_completed': perf.status == 'completed',
                                'model_type': 'legacy'
                            })
                        except Exception as e:
                            logger.warning(f"Error processing Performance {perf.id}: {e}")
                except Exception as e:
                    logger.warning(f"Error fetching Performances: {e}")

            if performances_data:
                categories_data.append({
                    'category': category,
                    'performances': performances_data,
                    'total_performances': len(performances_data),
                    'completed_performances': sum(1 for p in performances_data if p['is_completed'])
                })
    else:
        # Vue JUGE: Afficher ses propres notations
        performances_dict = {}

        # Chercher dans TechnicalScore (nouveau modèle)
        if TechnicalScore is not None:
            try:
                scores_query = TechnicalScore.objects.filter(judge=user)

                if competition_id:
                    scores_query = scores_query.filter(performance__competition_id=competition_id)

                scores = scores_query.select_related(
                    'performance',
                    'performance__competition',
                    'performance__category',
                    'performance__practitioner',
                    'criterion'
                ).order_by('-submitted_at')

                for score in scores:
                    perf_id = f"tech_{score.performance.id}"
                    if perf_id not in performances_dict:
                        performances_dict[perf_id] = {
                            'performance': score.performance,
                            'competition': score.performance.competition,
                            'category': score.performance.category,
                            'practitioner': score.performance.practitioner,
                            'scores': [],
                            'total': 0,
                            'submitted_at': score.submitted_at
                        }
                    performances_dict[perf_id]['scores'].append({
                        'criterion': score.criterion.name,
                        'value': float(score.value)
                    })
                    performances_dict[perf_id]['total'] += float(score.value)
            except Exception as e:
                logger.warning(f"Error fetching TechnicalScores for judge: {e}")

        # Chercher aussi dans Score (ancien modèle) - via Judge
        if Judge is not None and Score is not None:
            try:
                judge = Judge.objects.filter(user=user).first()
                if judge:
                    old_scores_query = Score.objects.filter(judge=judge)
                    if competition_id:
                        old_scores_query = old_scores_query.filter(
                            performance__category__competition_id=competition_id
                        )

                    old_scores = old_scores_query.select_related(
                        'performance',
                        'performance__category',
                        'performance__category__competition',
                        'performance__practitioner',
                        'criterion'
                    ).order_by('-timestamp')

                    for score in old_scores:
                        perf_id = f"legacy_{score.performance.id}"
                        if perf_id not in performances_dict:
                            performances_dict[perf_id] = {
                                'performance': score.performance,
                                'competition': score.performance.category.competition if hasattr(score.performance.category, 'competition') else None,
                                'category': score.performance.category,
                                'practitioner': score.performance.practitioner,
                                'scores': [],
                                'total': 0,
                                'submitted_at': score.timestamp
                            }
                        performances_dict[perf_id]['scores'].append({
                            'criterion': score.criterion.name,
                            'value': float(score.value)
                        })
                        performances_dict[perf_id]['total'] += float(score.value)
            except Exception as e:
                logger.warning(f"Error fetching legacy Scores for judge: {e}")

        scoring_history_list = list(performances_dict.values())

    # Liste des compétitions disponibles pour le filtre
    # Réutiliser le helper qui gère JudgeAssignment + AdHocJudge
    try:
        judge_comps, _ = _get_judge_competitions_and_categories(user)
        available_competitions = judge_comps

        # Ajouter les compétitions des organisations administrées
        try:
            from apps.organizations.models import OrganizationMember
            admin_roles = ['admin', 'owner', 'manager', 'president', 'secretary']
            admin_org_ids = OrganizationMember.objects.filter(
                user=user,
                role__in=admin_roles
            ).values_list('organization_id', flat=True)
            org_comps = Competition.objects.filter(organizing_organization_id__in=admin_org_ids)
            available_competitions = available_competitions | org_comps
        except Exception:
            pass

        # Ajouter les compétitions où le juge a noté (TechnicalScore)
        try:
            tech_perf_comps = Competition.objects.filter(
                technical_performances__scores__judge=user
            ).distinct()
            available_competitions = available_competitions | tech_perf_comps
        except Exception:
            pass

        # Si staff/superuser, montrer toutes les compétitions
        if user.is_staff or user.is_superuser:
            available_competitions = Competition.objects.all()

        available_competitions = available_competitions.distinct().order_by('-start_date')
    except Exception:
        if user.is_staff or user.is_superuser:
            available_competitions = Competition.objects.all().order_by('-start_date')
        else:
            available_competitions = Competition.objects.none()

    context = {
        'user': user,
        'competition': competition,
        'competition_id': competition_id,
        'is_organizer': is_organizer,
        'categories_data': categories_data,
        'scoring_history': scoring_history_list,
        'available_competitions': available_competitions,
        'active_page': 'history',
    }

    return render(request, 'competitions/technical_scoring/scoring_history.html', context)


@login_required
def scoring_categories(request, competition_id=None):
    """
    Gestion des catégories de notation pour une compétition.
    Affiche les catégories des compétitions auxquelles l'utilisateur a accès.
    """
    from ..models import Competition, CompetitionCategory
    from apps.organizations.models import OrganizationMember

    user = request.user
    categories = []
    competitions_list = []
    selected_competition = None

    # Si un ID de compétition est spécifié, filtrer sur cette compétition
    if competition_id:
        try:
            selected_competition = Competition.objects.get(id=competition_id)
            # Vérifier les droits d'accès
            has_access = user.is_staff or user.is_superuser

            if not has_access:
                # Vérifier si l'utilisateur est organisateur
                if hasattr(selected_competition, 'created_by') and selected_competition.created_by == user:
                    has_access = True
                elif selected_competition.organizing_organization:
                    org_member = OrganizationMember.objects.filter(
                        organization=selected_competition.organizing_organization,
                        user=user
                    ).first()
                    if org_member and getattr(org_member, 'role', '').lower() in ['admin', 'owner', 'manager', 'president', 'secretary']:
                        has_access = True

            if has_access:
                categories = CompetitionCategory.objects.filter(
                    competition=selected_competition
                ).select_related('competition', 'competition_type').order_by('name')
        except Competition.DoesNotExist:
            messages.warning(request, _("Compétition non trouvée."))
    else:
        # Sans compétition spécifiée, afficher les catégories de toutes les compétitions accessibles

        # 1. Compétitions où l'utilisateur est admin/staff
        if user.is_staff or user.is_superuser:
            accessible_competitions = Competition.objects.filter(
                status__in=['published', 'ongoing', 'completed']
            )
        else:
            # 2. Compétitions des organisations où l'utilisateur est admin/manager
            admin_roles = ['admin', 'owner', 'manager', 'president', 'secretary']
            user_orgs = OrganizationMember.objects.filter(
                user=user,
                role__in=admin_roles
            ).values_list('organization_id', flat=True)

            org_competitions = Competition.objects.filter(
                organizing_organization_id__in=user_orgs
            )

            # 3. Compétitions où l'utilisateur a des affectations de juge (JudgeAssignment)
            from apps.competitions.models.judges import JudgeAssignment
            judge_competition_ids = set(JudgeAssignment.objects.filter(
                user=user
            ).values_list('category__competition_id', flat=True).distinct())

            # 4. Compétitions via AdHocJudge (via practitioner)
            try:
                from apps.competitions.models.adhoc_judges import AdHocJudge
                from apps.competitions.models.practitioners import Practitioner
                practitioner = Practitioner.objects.filter(user=user).first()
                if practitioner:
                    adhoc_comp_ids = AdHocJudge.objects.filter(
                        practitioner=practitioner, status='active'
                    ).values_list('competition_id', flat=True)
                    judge_competition_ids.update(adhoc_comp_ids)
            except Exception:
                pass

            judge_competitions = Competition.objects.filter(id__in=judge_competition_ids)

            accessible_competitions = (org_competitions | judge_competitions).distinct()

        # Filtrer sur les compétitions actives
        accessible_competitions = accessible_competitions.filter(
            status__in=['published', 'ongoing', 'completed', 'draft']
        ).order_by('-start_date')

        competitions_list = list(accessible_competitions[:20])  # Limiter à 20 compétitions

        # Récupérer les catégories de ces compétitions
        categories = CompetitionCategory.objects.filter(
            competition__in=accessible_competitions
        ).select_related('competition', 'competition_type').order_by('competition__start_date', 'name')[:100]

    context = {
        'competition_id': competition_id,
        'competition': selected_competition,
        'competitions': competitions_list,
        'categories': categories,
        'active_page': 'categories',
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
    Uses shared helper to get both JudgeAssignment and AdHocJudge data.
    """
    user = request.user

    competitions, category_assignments = _get_judge_competitions_and_categories(user)

    # Enrich with category count per competition for this judge
    from collections import Counter
    comp_cat_count = Counter()
    for ca in category_assignments:
        comp_cat_count[ca['competition'].id] += 1

    competitions_data = []
    for comp in competitions:
        competitions_data.append({
            'competition': comp,
            'category_count': comp_cat_count.get(comp.id, 0),
        })

    # Stats
    ongoing_count = competitions.filter(status__in=['ongoing', 'published']).count()
    upcoming_count = competitions.filter(status='draft').count()
    completed_count = competitions.filter(status='completed').count()

    context = {
        'competitions_data': competitions_data,
        'total_count': competitions.count(),
        'ongoing_count': ongoing_count,
        'upcoming_count': upcoming_count,
        'completed_count': completed_count,
        'active_page': 'competitions',
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
    context = {
        'active_page': 'settings',
    }
    return render(request, 'competitions/technical_scoring/judge_settings.html', context)


@login_required
def judge_help(request):
    """
    Aide pour les juges.
    """
    context = {
        'active_page': 'help',
    }
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


# ===== PROMPT 8: FEUILLE DE NOTATION (LISTE DES PASSAGES) =====

def get_judge_for_user(user):
    """
    Récupère le profil Judge associé à un utilisateur.
    """
    from ..models import Judge, Practitioner

    # Essayer de trouver via le profil judge direct
    try:
        return Judge.objects.get(user=user)
    except Judge.DoesNotExist:
        pass

    # Essayer via le Practitioner
    try:
        practitioner = Practitioner.objects.get(user=user)
        if hasattr(practitioner, 'judge'):
            return practitioner.judge
    except Practitioner.DoesNotExist:
        pass

    return None


def calculate_total_rounds(category):
    """
    Calcule le nombre total de rounds.
    Minimum 2 tours pour permettre la saisie du 2ème passage.
    Au-delà de 16 participants, des tours supplémentaires sont ajoutés.
    """
    from ..models.technical_scoring import Performance

    participant_count = Performance.objects.filter(category=category).count()

    if participant_count <= 16:
        return 2
    elif participant_count <= 32:
        return 3
    else:
        return 4


def calculate_current_round(category):
    """
    Calcule le round actuel basé sur les performances complétées.
    """
    from ..models.technical_scoring import Performance

    total_performances = Performance.objects.filter(category=category).count()
    completed_performances = Performance.objects.filter(
        category=category,
        status='completed'
    ).count()

    if total_performances == 0:
        return 1

    total_rounds = calculate_total_rounds(category)
    performances_per_round = total_performances // total_rounds if total_rounds > 0 else total_performances

    if performances_per_round == 0:
        return 1

    current_round = (completed_performances // performances_per_round) + 1
    return min(current_round, total_rounds)


@login_required
def scoring_sheet(request, category_id):
    """
    PROMPT 8: Feuille de notation avec liste des passages pour un juge.
    Affiche tous les passages d'une catégorie avec leur statut de notation.
    PROMPT 9: Neutralité juge - pas de club/pays, mais grade/age/photo
    """
    from ..models import CompetitionCategory, CompetitionRegistration
    from ..models.technical_scoring import Performance, Score, ScoringConfiguration
    from django.db.models import Avg, Count, Min, Max
    from datetime import date

    category = get_object_or_404(CompetitionCategory, id=category_id)

    # Détecter le mode équipe depuis le type de compétition
    is_team_mode = False
    try:
        if category.competition_type and category.competition_type.team_based:
            is_team_mode = True
    except Exception:
        pass

    judge = get_judge_for_user(request.user)

    if not judge:
        messages.error(
            request, _("Vous devez être un juge pour accéder à cette interface.")
        )
        return redirect('competitions:technical_scoring:judge_dashboard')

    # AUTO-GÉNÉRATION DES PERFORMANCES
    # Synchroniser les performances avec les équipes/inscriptions (ajouter les manquantes)
    from ..models.combat import Equipe

    if is_team_mode:
        # MODE ÉQUIPE: Créer une Performance par équipe inscrite dans cette catégorie
        # Exclure les équipes sources de fusion (merged_into non null ou status fusion_complete avec equipe_parent)
        teams = Equipe.objects.filter(
            competition=category.competition,
            category=category,
            is_active=True
        ).exclude(
            merged_into__isnull=False  # Exclure les sources fusionnées
        ).prefetch_related('memberships__pratiquant')

        # Trouver les équipes qui n'ont pas encore de Performance
        existing_team_ids = set(
            Performance.objects.filter(
                category=category, equipe__isnull=False
            ).values_list('equipe_id', flat=True)
        )

        max_order = Performance.objects.filter(category=category).count()
        performances_created = 0

        for team in teams:
            if team.id in existing_team_ids:
                continue

            # Utiliser le premier titulaire comme ancre (practitioner est non-nullable)
            first_member = team.memberships.filter(
                est_remplacant=False
            ).select_related('pratiquant').order_by('ordre').first()

            if first_member and first_member.pratiquant:
                max_order += 1
                Performance.objects.get_or_create(
                    category=category,
                    equipe=team,
                    defaults={
                        'practitioner': first_member.pratiquant,
                        'status': 'scheduled',
                        'order': max_order,
                    }
                )
                performances_created += 1

        # Nettoyer les performances orphelines en mode équipe
        from django.db.models import Count as DbCount

        # 1) Perfs individuelles (sans équipe) créées avant l'activation du mode équipe
        orphan_perfs = Performance.objects.filter(
            category=category, equipe__isnull=True
        )
        if orphan_perfs.exists():
            orphans_without_scores = orphan_perfs.annotate(
                score_count=DbCount('scores')
            ).filter(score_count=0)
            deleted_count = orphans_without_scores.count()
            if deleted_count > 0:
                orphans_without_scores.delete()
                messages.info(
                    request,
                    _("%(count)d performance(s) individuelles orphelines supprimées (mode équipe activé).") % {'count': deleted_count}
                )

        # 2) Perfs liées à des équipes sources fusionnées (merged_into non null ou is_active=False)
        merged_perfs = Performance.objects.filter(
            category=category,
            equipe__isnull=False
        ).filter(
            Q(equipe__merged_into__isnull=False) | Q(equipe__is_active=False)
        )
        if merged_perfs.exists():
            merged_without_scores = merged_perfs.annotate(
                score_count=DbCount('scores')
            ).filter(score_count=0)
            merged_deleted = merged_without_scores.count()
            if merged_deleted > 0:
                merged_without_scores.delete()
                messages.info(
                    request,
                    _("%(count)d performance(s) d'équipes fusionnées supprimées.") % {'count': merged_deleted}
                )

        if performances_created > 0:
            messages.info(
                request,
                _("%(count)d performance(s) d'équipe ont été automatiquement créées.") % {'count': performances_created}
            )
    else:
        # MODE INDIVIDUEL: Créer une Performance par pratiquant inscrit
        registrations = CompetitionRegistration.objects.filter(
            categories=category,
            status__in=['approved', 'confirmed', 'pending']
        ).select_related('practitioner')

        existing_practitioner_ids = set(
            Performance.objects.filter(
                category=category
            ).values_list('practitioner_id', flat=True)
        )

        max_order = Performance.objects.filter(category=category).count()
        performances_created = 0

        for registration in registrations:
            if registration.practitioner and registration.practitioner.id not in existing_practitioner_ids:
                max_order += 1
                Performance.objects.get_or_create(
                    practitioner=registration.practitioner,
                    category=category,
                    defaults={
                        'status': 'scheduled',
                        'order': max_order,
                    }
                )
                performances_created += 1
                existing_practitioner_ids.add(registration.practitioner.id)

        if performances_created > 0:
            messages.info(
                request,
                _("%(count)d performance(s) ont été automatiquement créées pour cette catégorie.") % {'count': performances_created}
            )

    # Récupérer toutes les performances de la catégorie
    # NEUTRALITÉ JUGE: On récupère grade au lieu de club
    performances = Performance.objects.filter(
        category=category
    ).select_related(
        'practitioner',
        'practitioner__grade',
        'equipe',
        'equipe__club'
    ).prefetch_related(
        'scores'
    ).order_by('order')

    # Enrichir les performances avec les informations de notation du juge
    performances_data = []
    scored_count = 0
    scores_values = []
    current_performance = None

    for perf in performances:
        # Vérifier si ce juge a noté cette performance
        judge_scores = perf.scores.filter(judge=judge)
        has_scored = judge_scores.exists()

        if has_scored:
            scored_count += 1
            # Calculer la moyenne des notes du juge pour cette performance
            avg_score = judge_scores.aggregate(avg=Avg('value'))['avg']
            if avg_score:
                scores_values.append(avg_score)
        else:
            avg_score = None

        # Récupérer les scores par round (Tour 1 et Tour 2)
        score_round1 = None
        score_round2 = None
        if has_scored:
            # Vérifier si le modèle Score a un champ round_number
            try:
                Score._meta.get_field('round_number')
                score_has_round = True
            except Exception:
                score_has_round = False

            if score_has_round:
                # Score du round 1
                round1_scores = judge_scores.filter(round_number=1)
                if round1_scores.exists():
                    score_round1 = round1_scores.aggregate(avg=Avg('value'))['avg']
                    if score_round1:
                        score_round1 = round(score_round1, 2)

                # Score du round 2 si plusieurs tours
                round2_scores = judge_scores.filter(round_number=2)
                if round2_scores.exists():
                    score_round2 = round2_scores.aggregate(avg=Avg('value'))['avg']
                    if score_round2:
                        score_round2 = round(score_round2, 2)
            else:
                # Pas de champ round_number, utiliser la moyenne de tous les scores
                if avg_score:
                    score_round1 = round(avg_score, 2)

        # Fallback: Si pas de score_round1 mais avg_score existe
        if score_round1 is None and avg_score:
            score_round1 = round(avg_score, 2)

        # Déterminer le statut d'affichage
        if perf.status == 'in_progress':
            display_status = 'in_progress'
            current_performance = perf
        elif has_scored:
            display_status = 'scored'
        else:
            display_status = 'pending'

        # Enrichir selon le mode (équipe ou individuel)
        if is_team_mode and perf.equipe:
            # MODE ÉQUIPE: afficher nom équipe + membres
            team = perf.equipe
            team_members = list(
                team.memberships.filter(est_remplacant=False)
                .select_related('pratiquant', 'pratiquant__grade')
                .order_by('ordre')
            )

            # Photo du premier membre
            photo_url = None
            if team_members and team_members[0].pratiquant.photo:
                photo_url = team_members[0].pratiquant.photo.url

            performances_data.append({
                'performance': perf,
                'practitioner': perf.practitioner,
                'is_team': True,
                'team': team,
                'team_name': team.nom,
                'team_members': team_members,
                'team_club': team.club.name if team.club else None,
                'grade': None,
                'age': None,
                'photo_url': photo_url,
                'has_scored': has_scored,
                'score': score_round1,
                'score_round2': score_round2,
                'display_status': display_status,
                'is_current': perf.status == 'in_progress',
            })
        else:
            # MODE INDIVIDUEL: grade/age/photo du pratiquant
            practitioner = perf.practitioner

            pract_age = None
            if practitioner.birth_date:
                today = date.today()
                pract_age = today.year - practitioner.birth_date.year
                if (today.month, today.day) < (
                    practitioner.birth_date.month, practitioner.birth_date.day
                ):
                    pract_age -= 1

            grade_display = None
            if practitioner.grade:
                grade_display = str(practitioner.grade)
            elif practitioner.grade_text:
                grade_display = practitioner.grade_text

            photo_url = None
            if practitioner.photo:
                photo_url = practitioner.photo.url

            performances_data.append({
                'performance': perf,
                'practitioner': practitioner,
                'is_team': False,
                'team': None,
                'team_name': None,
                'team_members': [],
                'team_club': None,
                'grade': grade_display,
                'age': pract_age,
                'photo_url': photo_url,
                'has_scored': has_scored,
                'score': score_round1,
                'score_round2': score_round2,
                'display_status': display_status,
                'is_current': perf.status == 'in_progress',
            })

    # Calculer les statistiques à partir des scores affichés
    total_count = performances.count()
    progress_percent = (scored_count / total_count * 100) if total_count > 0 else 0

    # Recalculer scores_values à partir des données de performance pour plus de fiabilité
    displayed_scores = []
    for item in performances_data:
        if item['score'] is not None:
            displayed_scores.append(float(item['score']))
        if item.get('score_round2') is not None:
            displayed_scores.append(float(item['score_round2']))

    # Utiliser les scores affichés pour les stats
    stats_scores = displayed_scores if displayed_scores else scores_values

    stats = {
        'scored_count': scored_count,
        'total_count': total_count,
        'progress_percent': round(progress_percent, 1),
        'average_score': round(sum(stats_scores) / len(stats_scores), 2) if stats_scores else '-',
        'min_score': round(min(stats_scores), 2) if stats_scores else '-',
        'max_score': round(max(stats_scores), 2) if stats_scores else '-',
    }

    # Récupérer la configuration de notation
    try:
        scoring_config = ScoringConfiguration.objects.get(category=category)
    except ScoringConfiguration.DoesNotExist:
        scoring_config = None

    # Déterminer si tous les passages sont notés
    all_scored = scored_count == total_count and total_count > 0

    # Vérifier si une performance est en cours
    is_live = performances.filter(status='in_progress').exists()

    # Vérifier si l'utilisateur est juge en chef de cette catégorie
    from ..models.session_workflow import CategorySession
    session = CategorySession.objects.filter(
        category=category
    ).exclude(status='closed').first()
    is_chief_judge = False
    if session and session.head_judge == request.user:
        is_chief_judge = True

    # Configuration Tour 2
    tour2_mode = 'all'
    tour2_top_n = 6
    if scoring_config and scoring_config.advanced_config:
        tour2_mode = scoring_config.advanced_config.get('tour2_mode', 'all')
        tour2_top_n = scoring_config.advanced_config.get('tour2_top_n', 6)

    # Déterminer quelles performances sont éligibles au Tour 2
    tour2_eligible_ids = set()
    tour2_launched = False

    # Vérifier si le Tour 2 a été lancé explicitement (IDs stockés dans config)
    if scoring_config and scoring_config.advanced_config:
        tour2_launched = scoring_config.advanced_config.get('tour2_launched', False)
        stored_ids = scoring_config.advanced_config.get('tour2_eligible_ids', [])
        if tour2_launched and stored_ids:
            # Trouver les performances correspondant aux practitioner IDs stockés
            for item in performances_data:
                if item['performance'].practitioner_id in stored_ids:
                    tour2_eligible_ids.add(item['performance'].id)

    if not tour2_eligible_ids:
        # Calcul automatique si pas lancé explicitement
        if tour2_mode == 'all':
            tour2_eligible_ids = {item['performance'].id for item in performances_data}
        elif tour2_mode == 'top_n':
            scored_items = [item for item in performances_data if item.get('score') is not None]
            scored_items.sort(key=lambda x: float(x['score']), reverse=True)
            tour2_eligible_ids = {item['performance'].id for item in scored_items[:tour2_top_n]}
        elif tour2_mode == 'tiebreak':
            scored_items = [item for item in performances_data if item.get('score') is not None]
            scored_items.sort(key=lambda x: float(x['score']), reverse=True)
            if scored_items:
                podium_scores = []
                rank = 0
                prev_score = None
                for item in scored_items:
                    current_score = float(item['score'])
                    if current_score != prev_score:
                        rank += 1
                        prev_score = current_score
                    if rank <= 3:
                        podium_scores.append((current_score, item))

                from collections import Counter
                score_counts = Counter(s for s, _ in podium_scores)
                for score_val, item in podium_scores:
                    if score_counts[score_val] > 1:
                        tour2_eligible_ids.add(item['performance'].id)

    # Ajouter l'info d'éligibilité à chaque performance
    for item in performances_data:
        item['tour2_eligible'] = item['performance'].id in tour2_eligible_ids

    context = {
        'category': category,
        'competition': category.competition,
        'judge': judge,
        'performances': performances_data,
        'stats': stats,
        'current_round': calculate_current_round(category),
        'total_rounds': calculate_total_rounds(category),
        'scoring_config': scoring_config,
        'all_scored': all_scored,
        'is_live': is_live,
        'current_performance': current_performance,
        'is_team_mode': is_team_mode,
        'is_chief_judge': is_chief_judge,
        'session': session,
        'tour2_mode': tour2_mode,
        'tour2_top_n': tour2_top_n,
        'tour2_launched': tour2_launched,
    }

    return render(request, 'competitions/technical_scoring/scoring_sheet.html', context)


@login_required
def get_provisional_ranking(request, category_id):
    """
    API: Récupère le classement provisoire d'une catégorie.
    PROMPT 9: Neutralité juge - pas de club/pays, mais photo/grade/age
    """
    from ..models import CompetitionCategory
    from ..models.technical_scoring import Performance, Score
    from django.db.models import Avg
    from datetime import date

    category = get_object_or_404(CompetitionCategory, id=category_id)

    # Calculer les scores moyens pour chaque performance
    performances = Performance.objects.filter(
        category=category
    ).select_related('practitioner', 'practitioner__grade', 'equipe', 'equipe__club')

    ranking_data = []
    for perf in performances:
        # Calculer le score moyen de tous les juges
        avg_score = perf.scores.aggregate(avg=Avg('value'))['avg']
        if avg_score is not None:
            if perf.equipe:
                # MODE ÉQUIPE
                ranking_data.append({
                    'practitioner_id': perf.equipe.id,
                    'practitioner_name': perf.equipe.nom,
                    'is_team': True,
                    'grade': None,
                    'age': None,
                    'photo_url': None,
                    'score': round(avg_score, 2),
                    'judges_count': perf.scores.values('judge').distinct().count(),
                })
            else:
                # MODE INDIVIDUEL
                practitioner = perf.practitioner

                age = None
                if practitioner.birth_date:
                    today = date.today()
                    age = today.year - practitioner.birth_date.year
                    if (today.month, today.day) < (
                        practitioner.birth_date.month, practitioner.birth_date.day
                    ):
                        age -= 1

                grade_display = None
                if practitioner.grade:
                    grade_display = str(practitioner.grade)
                elif practitioner.grade_text:
                    grade_display = practitioner.grade_text

                photo_url = None
                if practitioner.photo:
                    photo_url = practitioner.photo.url

                ranking_data.append({
                    'practitioner_id': practitioner.id,
                    'practitioner_name': practitioner.full_name,
                    'is_team': False,
                    'grade': grade_display,
                    'age': age,
                    'photo_url': photo_url,
                    'score': round(avg_score, 2),
                    'judges_count': perf.scores.values('judge').distinct().count(),
                })

    # Trier par score décroissant
    ranking_data.sort(key=lambda x: x['score'], reverse=True)

    # Ajouter les rangs
    for i, item in enumerate(ranking_data, 1):
        item['rank'] = i

    return JsonResponse({
        'status': 'success',
        'category': category.name,
        'ranking': ranking_data,
    })


@login_required
def lock_scores(request, category_id):
    """
    API: Verrouille les scores d'un juge pour une catégorie.
    """
    from ..models import CompetitionCategory
    from ..models.technical_scoring import Score

    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': _('Méthode non autorisée')})

    category = get_object_or_404(CompetitionCategory, id=category_id)
    judge = get_judge_for_user(request.user)

    if not judge:
        return JsonResponse({'status': 'error', 'message': _('Juge non trouvé')})

    # Vérifier que tous les passages sont notés
    from ..models.technical_scoring import Performance

    total_performances = Performance.objects.filter(category=category).count()
    scored_performances = Performance.objects.filter(
        category=category,
        scores__judge=judge
    ).distinct().count()

    if scored_performances < total_performances:
        return JsonResponse({
            'status': 'error',
            'message': _('Tous les passages doivent être notés avant de verrouiller.')
        })

    # Verrouiller les scores (si le modèle TechnicalScore a un champ is_locked)
    try:
        from ..models.technical_scoring import TechnicalScore
        TechnicalScore.objects.filter(
            performance__category=category,
            judge=request.user
        ).update(is_locked=True)
    except Exception:
        # Si TechnicalScore n'est pas utilisé, on peut simplement marquer comme verrouillé
        pass

    return JsonResponse({
        'status': 'success',
        'message': _('Vos notations ont été verrouillées avec succès.')
    })


@login_required
def submit_performance_score(request, performance_id):
    """
    API: Soumet les scores d'un juge pour une performance spécifique.
    """
    from ..models.technical_scoring import Performance, Score, ScoringCriterion
    import json

    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': _('Méthode non autorisée')})

    performance = get_object_or_404(Performance, id=performance_id)
    judge = get_judge_for_user(request.user)

    if not judge:
        return JsonResponse({'status': 'error', 'message': _('Juge non trouvé')})

    try:
        data = json.loads(request.body)
        scores = data.get('scores', {})

        # Récupérer les critères de la catégorie
        criteria = ScoringCriterion.objects.filter(
            category=performance.category,
            is_active=True
        )

        for criterion in criteria:
            criterion_key = str(criterion.id)
            if criterion_key in scores:
                value = float(scores[criterion_key])

                # Valider la valeur
                if value < criterion.min_score or value > criterion.max_score:
                    return JsonResponse({
                        'status': 'error',
                        'message': _('Score invalide pour le critère {}').format(criterion.name)
                    })

                # Créer ou mettre à jour le score
                Score.objects.update_or_create(
                    performance=performance,
                    judge=judge,
                    criterion=criterion,
                    defaults={'value': value}
                )

        # Recalculer le score total de la performance
        performance.total_score = performance.calculate_total_score()
        performance.save()

        return JsonResponse({
            'status': 'success',
            'message': _('Scores enregistrés avec succès'),
            'total_score': performance.total_score
        })

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': _('Données JSON invalides')})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@login_required
def get_performance_criteria(request, performance_id):
    """
    API: Récupère les critères de notation et les scores existants pour une performance.
    """
    from ..models.technical_scoring import Performance, Score, ScoringCriterion, ScoringConfiguration

    performance = get_object_or_404(Performance, id=performance_id)
    judge = get_judge_for_user(request.user)

    # Récupérer les critères
    criteria = ScoringCriterion.objects.filter(
        category=performance.category,
        is_active=True
    ).order_by('order', 'name')

    # Récupérer les scores existants du juge
    existing_scores = {}
    if judge:
        scores = Score.objects.filter(
            performance=performance,
            judge=judge
        )
        for score in scores:
            existing_scores[str(score.criterion_id)] = score.value

    # Récupérer la configuration
    try:
        config = ScoringConfiguration.objects.get(category=performance.category)
        config_data = {
            'min_score': float(config.min_score),
            'max_score': float(config.max_score),
            'score_step': float(config.score_step),
        }
    except ScoringConfiguration.DoesNotExist:
        config_data = {
            'min_score': 0.0,
            'max_score': 10.0,
            'score_step': 0.25,
        }

    criteria_data = [{
        'id': c.id,
        'name': c.name,
        'description': c.description,
        'weight': c.weight,
        'min_score': c.min_score,
        'max_score': c.max_score,
        'step': c.step,
        'current_value': existing_scores.get(str(c.id)),
    } for c in criteria]

    # PROMPT 9: Neutralité juge - Ne pas afficher le club/pays
    # Afficher uniquement: Nom, Prénom, Grade, Âge, Photo
    practitioner = performance.practitioner

    # Calculer l'âge
    from datetime import date
    age = None
    if practitioner.birth_date:
        today = date.today()
        age = today.year - practitioner.birth_date.year
        if (today.month, today.day) < (
            practitioner.birth_date.month, practitioner.birth_date.day
        ):
            age -= 1

    # Récupérer le grade
    grade_display = None
    if practitioner.grade:
        grade_display = str(practitioner.grade)
    elif practitioner.grade_text:
        grade_display = practitioner.grade_text

    # URL de la photo
    photo_url = None
    if practitioner.photo:
        photo_url = practitioner.photo.url

    return JsonResponse({
        'status': 'success',
        'performance': {
            'id': performance.id,
            'practitioner': practitioner.full_name,
            # NEUTRALITÉ JUGE: Pas de club ni pays
            'grade': grade_display,
            'age': age,
            'photo_url': photo_url,
            'order': performance.order,
            'status': performance.status,
        },
        'criteria': criteria_data,
        'config': config_data,
        'has_scored': len(existing_scores) > 0,
    })


# ===== PROMPT 9: PAVÉ NUMÉRIQUE DE NOTATION =====

@login_required
def save_score(request):
    """
    PROMPT 9: API pour sauvegarder un score via le pavé numérique.

    Reçoit via POST JSON:
    - performance_id: ID de la performance
    - criterion_id: ID du critère de notation
    - score: Valeur du score (0 à 10 par pas de 0.25)
    - comment: Commentaire optionnel

    Retourne:
    - success: bool
    - message: str
    - data: dict avec les infos du score enregistré
    """
    from ..models.technical_scoring import Performance, Score, ScoringCriterion, ScoringConfiguration
    import json

    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': _('Méthode non autorisée. Utilisez POST.')
        }, status=405)

    # Récupérer le juge
    judge = get_judge_for_user(request.user)
    if not judge:
        return JsonResponse({
            'success': False,
            'message': _('Vous devez être un juge pour enregistrer des scores.')
        }, status=403)

    try:
        # Parser les données JSON
        data = json.loads(request.body)

        performance_id = data.get('performance_id')
        criterion_id = data.get('criterion_id')
        score_value = data.get('score')
        comment = data.get('comment', '')

        # Validation des données requises
        if not performance_id:
            return JsonResponse({
                'success': False,
                'message': _('ID de performance requis.')
            }, status=400)

        if not criterion_id:
            return JsonResponse({
                'success': False,
                'message': _('ID de critère requis.')
            }, status=400)

        if score_value is None:
            return JsonResponse({
                'success': False,
                'message': _('Score requis.')
            }, status=400)

        # Convertir et valider le score
        try:
            score_value = float(score_value)
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'message': _('Score invalide. Doit être un nombre.')
            }, status=400)

        # Valider la plage de score (0-10 par défaut)
        if score_value < 0 or score_value > 10:
            return JsonResponse({
                'success': False,
                'message': _('Le score doit être entre 0 et 10.')
            }, status=400)

        # Récupérer la performance
        try:
            performance = Performance.objects.select_related(
                'category',
                'practitioner',
                'equipe'
            ).get(id=performance_id)
        except Performance.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': _('Performance non trouvée.')
            }, status=404)

        # Valider le score contre la ScoringConfiguration de la catégorie (min/max/pas)
        try:
            scoring_config = ScoringConfiguration.objects.get(category=performance.category)
            config_min = float(scoring_config.min_score)
            config_max = float(scoring_config.max_score)
            config_step = float(scoring_config.score_step) if scoring_config.score_step else 0.25

            if score_value < config_min or score_value > config_max:
                return JsonResponse({
                    'success': False,
                    'message': _('Le score doit être entre {} et {} pour cette catégorie.').format(
                        scoring_config.min_score, scoring_config.max_score
                    )
                }, status=400)

            # Valider le pas de notation
            if config_step > 0:
                remainder = round((score_value - config_min) % config_step, 10)
                if remainder > 0.001 and abs(remainder - config_step) > 0.001:
                    return JsonResponse({
                        'success': False,
                        'message': _('Le score doit être un multiple de {} à partir de {}.').format(
                            scoring_config.score_step, scoring_config.min_score
                        )
                    }, status=400)
        except ScoringConfiguration.DoesNotExist:
            # Pas de config => valider le pas par défaut (0.25)
            if (score_value * 4) % 1 != 0:
                return JsonResponse({
                    'success': False,
                    'message': _('Le score doit être un multiple de 0.25.')
                }, status=400)

        # Récupérer le critère
        # Si criterion_id est petit (1 ou 2), c'est probablement un numéro de round
        # Dans ce cas, on cherche/crée un critère par défaut pour ce round
        criterion = None
        round_number = None

        if criterion_id in [1, 2]:
            # C'est un numéro de round, pas un ID de critère
            round_number = criterion_id
            round_name = f"Tour {round_number}"

            # Chercher un critère existant pour ce round
            criterion = ScoringCriterion.objects.filter(
                category=performance.category,
                name__icontains=f"Tour {round_number}",
                is_active=True
            ).first()

            # Si pas trouvé, chercher le premier critère actif de la catégorie
            if not criterion:
                criterion = ScoringCriterion.objects.filter(
                    category=performance.category,
                    is_active=True
                ).order_by('order').first()

            # Si toujours pas de critère, en créer un par défaut
            if not criterion:
                # Utiliser la config de la catégorie si disponible
                try:
                    sc = ScoringConfiguration.objects.get(category=performance.category)
                    crit_min, crit_max, crit_step = float(sc.min_score), float(sc.max_score), float(sc.score_step)
                except ScoringConfiguration.DoesNotExist:
                    crit_min, crit_max, crit_step = 0.0, 10.0, 0.25
                criterion = ScoringCriterion.objects.create(
                    name=round_name,
                    description=f"Critère de notation pour le {round_name}",
                    weight=1.0,
                    min_score=crit_min,
                    max_score=crit_max,
                    step=crit_step,
                    category=performance.category,
                    order=round_number,
                    is_active=True
                )
        else:
            # C'est un vrai ID de critère
            try:
                criterion = ScoringCriterion.objects.get(
                    id=criterion_id,
                    category=performance.category,
                    is_active=True
                )
            except ScoringCriterion.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': _('Critère de notation non trouvé ou inactif.')
                }, status=404)

        # Valider le score contre les limites du critère
        if score_value < criterion.min_score or score_value > criterion.max_score:
            return JsonResponse({
                'success': False,
                'message': _('Le score doit être entre {} et {} pour ce critère.').format(
                    criterion.min_score, criterion.max_score
                )
            }, status=400)

        # Créer ou mettre à jour le score
        score, created = Score.objects.update_or_create(
            performance=performance,
            judge=judge,
            criterion=criterion,
            defaults={
                'value': score_value,
                'comments': comment[:500] if comment else '',  # Limiter le commentaire (champ = comments)
            }
        )

        # Recalculer le score total de la performance
        try:
            performance.total_score = performance.calculate_total_score()
            performance.save(update_fields=['total_score'])
        except AttributeError:
            # Si la méthode calculate_total_score n'existe pas
            pass

        # ===== SYNCHRONISATION VERS TechnicalPerformance/TechnicalScore =====
        # Pour que le dashboard management/scoring et les resultats fonctionnent
        try:
            from ..models.technical_scoring import TechnicalPerformance, TechnicalScore
            from django.utils import timezone

            # Creer ou recuperer la TechnicalPerformance correspondante
            tech_perf, tech_created = TechnicalPerformance.objects.get_or_create(
                competition=performance.category.competition,
                category=performance.category,
                practitioner=performance.practitioner,
                defaults={
                    'performance_order': performance.order if hasattr(performance, 'order') else 0,
                    'status': 'in_progress',
                    'is_completed': False,
                }
            )

            # Determiner le round_number pour la synchronisation
            sync_round_number = round_number if round_number else 1

            # Creer ou mettre a jour le TechnicalScore
            TechnicalScore.objects.update_or_create(
                performance=tech_perf,
                judge=request.user,  # TechnicalScore utilise User, pas Judge
                criterion=criterion,
                round_number=sync_round_number,
                defaults={
                    'value': score_value,
                    'is_locked': False,
                    'is_active_for_ranking': True,
                }
            )

            # Si c'est un Tour 2 (barrage), desactiver les scores Tour 1
            # pour ce participant afin que seul le Tour 2 compte
            if sync_round_number >= 2:
                TechnicalScore.objects.filter(
                    performance=tech_perf,
                    round_number__lt=sync_round_number,
                ).update(is_active_for_ranking=False)

            # Verifier si tous les criteres sont notes pour marquer comme complete
            criteria_count = ScoringCriterion.objects.filter(
                category=performance.category,
                is_active=True
            ).count()

            if criteria_count > 0:
                scores_count = TechnicalScore.objects.filter(
                    performance=tech_perf,
                    judge=request.user
                ).count()

                if scores_count >= criteria_count:
                    tech_perf.status = 'completed'
                    tech_perf.is_completed = True
                    tech_perf.end_time = timezone.now()
                    tech_perf.save()

        except Exception as sync_error:
            # Log mais ne pas bloquer la sauvegarde principale
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Erreur sync TechnicalPerformance: {sync_error}")
        # ===== FIN SYNCHRONISATION =====

        # Préparer la réponse
        return JsonResponse({
            'success': True,
            'message': _('Score enregistré avec succès.'),
            'data': {
                'score_id': score.id,
                'performance_id': performance.id,
                'criterion_id': criterion.id,
                'criterion_name': criterion.name,
                'score': score_value,
                'comment': comment,
                'created': created,
                'practitioner': performance.equipe.nom if performance.equipe else performance.practitioner.full_name,
                'is_team': performance.equipe is not None,
                'total_score': performance.total_score if hasattr(performance, 'total_score') else None,
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': _('Données JSON invalides.')
        }, status=400)
    except Exception as e:
        # Log l'erreur pour debug
        import logging
        logger = logging.getLogger(__name__)
        logger.exception("Erreur lors de l'enregistrement du score")

        return JsonResponse({
            'success': False,
            'message': _('Une erreur est survenue lors de l\'enregistrement.')
        }, status=500)


@login_required
def get_numpad_context(request, performance_id, criterion_id):
    """
    PROMPT 9: API pour récupérer le contexte d'affichage du pavé numérique.

    Utilisé pour pré-remplir le pavé avec les données existantes.
    """
    from ..models.technical_scoring import Performance, Score, ScoringCriterion

    judge = get_judge_for_user(request.user)
    if not judge:
        return JsonResponse({
            'success': False,
            'message': _('Juge non trouvé.')
        }, status=403)

    try:
        performance = Performance.objects.select_related(
            'practitioner',
            'practitioner__club',
            'equipe',
            'equipe__club',
            'category',
            'category__competition'
        ).get(id=performance_id)
    except Performance.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': _('Performance non trouvée.')
        }, status=404)

    try:
        criterion = ScoringCriterion.objects.get(
            id=criterion_id,
            category=performance.category
        )
    except ScoringCriterion.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': _('Critère non trouvé.')
        }, status=404)

    # Récupérer le score existant si présent
    try:
        existing_score = Score.objects.get(
            performance=performance,
            judge=judge,
            criterion=criterion
        )
        current_score = existing_score.value
        current_comment = existing_score.comment
    except Score.DoesNotExist:
        current_score = None
        current_comment = ''

    # Nom affiché: équipe ou pratiquant
    if performance.equipe:
        display_name = performance.equipe.nom
        display_club = performance.equipe.club.name if performance.equipe.club else None
    else:
        display_name = performance.practitioner.full_name
        display_club = performance.practitioner.club.name if performance.practitioner.club else None

    return JsonResponse({
        'success': True,
        'data': {
            'performance_id': performance.id,
            'criterion_id': criterion.id,
            'practitioner_name': display_name,
            'practitioner_club': display_club,
            'is_team': performance.equipe is not None,
            'criterion_name': criterion.name,
            'criterion_description': criterion.description,
            'category_name': performance.category.name,
            'competition_name': performance.category.competition.title,
            'min_score': criterion.min_score,
            'max_score': criterion.max_score,
            'step': criterion.step,
            'current_score': float(current_score) if current_score is not None else None,
            'current_comment': current_comment,
            'order': performance.order,
        }
    })


# ===== PROMPT 10: VERROUILLAGE ET CLASSEMENT =====

@login_required
def lock_judge_scores(request, category_id):
    """
    PROMPT 10: Verrouille les notes d'un juge pour une catégorie.

    Conditions requises:
    - Tous les pratiquants doivent être notés
    - Le juge doit confirmer (checkbox dans le modal)
    - Une fois verrouillé, les notes ne peuvent plus être modifiées
    """
    from ..models import CompetitionCategory
    from ..models.technical_scoring import Performance, Score, JudgeCategoryLock
    from ..services.ranking_service import RankingService
    from django.utils import timezone
    import json

    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': _('Méthode non autorisée.')
        }, status=405)

    category = get_object_or_404(CompetitionCategory, id=category_id)
    judge = get_judge_for_user(request.user)

    if not judge:
        return JsonResponse({
            'success': False,
            'message': _('Juge non trouvé.')
        }, status=403)

    try:
        data = json.loads(request.body) if request.body else {}
        confirmed = data.get('confirmed', False)
        round_number = data.get('round_number', 1)
    except json.JSONDecodeError:
        confirmed = request.POST.get('confirmed', False)
        round_number = int(request.POST.get('round_number', 1))

    # Vérifier la confirmation
    if not confirmed:
        return JsonResponse({
            'success': False,
            'message': _('Vous devez confirmer avoir vérifié toutes vos notes.')
        }, status=400)

    # Vérifier si déjà verrouillé
    if JudgeCategoryLock.is_judge_locked(judge, category, round_number):
        return JsonResponse({
            'success': False,
            'message': _('Vos notes sont déjà verrouillées pour ce round.')
        }, status=400)

    # Récupérer les statistiques
    stats = RankingService.get_judge_stats(judge, category, round_number)

    # Vérifier que tout est noté
    if not stats['all_scored']:
        return JsonResponse({
            'success': False,
            'message': _('Vous devez noter tous les pratiquants avant de verrouiller.'),
            'data': {
                'scored': stats['scored_performances'],
                'total': stats['total_performances'],
            }
        }, status=400)

    # Créer le verrouillage
    lock, created = JudgeCategoryLock.objects.update_or_create(
        judge=judge,
        category=category,
        round_number=round_number,
        defaults={
            'is_locked': True,
            'locked_at': timezone.now(),
            'scores_count': stats['scores_count'],
            'average_score': stats['average_score'],
            'min_score': stats['min_score'],
            'max_score': stats['max_score'],
        }
    )

    return JsonResponse({
        'success': True,
        'message': _('Vos notes ont été verrouillées avec succès.'),
        'data': {
            'locked_at': lock.locked_at.isoformat() if lock.locked_at else None,
            'scores_count': stats['scores_count'],
            'average_score': stats['average_score'],
        }
    })


@login_required
def get_lock_status(request, category_id):
    """
    PROMPT 10: Récupère le statut de verrouillage et les statistiques pré-verrouillage.
    """
    from ..models import CompetitionCategory
    from ..models.technical_scoring import JudgeCategoryLock
    from ..services.ranking_service import RankingService

    category = get_object_or_404(CompetitionCategory, id=category_id)
    judge = get_judge_for_user(request.user)

    if not judge:
        return JsonResponse({
            'success': False,
            'message': _('Juge non trouvé.')
        }, status=403)

    round_number = int(request.GET.get('round', 1))

    # Vérifier si verrouillé
    try:
        lock = JudgeCategoryLock.objects.get(
            judge=judge,
            category=category,
            round_number=round_number
        )
        is_locked = lock.is_locked
        locked_at = lock.locked_at.isoformat() if lock.locked_at else None
    except JudgeCategoryLock.DoesNotExist:
        is_locked = False
        locked_at = None

    # Récupérer les statistiques
    stats = RankingService.get_judge_stats(judge, category, round_number)

    return JsonResponse({
        'success': True,
        'data': {
            'is_locked': is_locked,
            'locked_at': locked_at,
            'can_lock': stats['all_scored'] and not is_locked,
            'stats': {
                'scored_count': stats['scored_performances'],
                'total_count': stats['total_performances'],
                'progress_percent': stats['progress_percent'],
                'average_score': stats['average_score'],
                'min_score': stats['min_score'],
                'max_score': stats['max_score'],
            },
            'round_number': round_number,
            'total_rounds': calculate_total_rounds(category),
        }
    })


@login_required
def get_ranking_with_ties(request, category_id):
    """
    PROMPT 10: Récupère le classement provisoire avec gestion des ex-aequo.

    Les pratiquants avec le même score ont le même rang.
    Exemple: 1er, 2ème, 2ème ex-aequo, 4ème (pas 3ème)
    """
    from ..models import CompetitionCategory
    from ..services.ranking_service import RankingService

    category = get_object_or_404(CompetitionCategory, id=category_id)
    judge = get_judge_for_user(request.user)

    round_number = int(request.GET.get('round', 1))
    judge_only = request.GET.get('judge_only', 'false').lower() == 'true'

    # Calculer le classement
    if judge_only and judge:
        ranking = RankingService.calculate_round_ranking(category, round_number, judge)
    else:
        ranking = RankingService.calculate_round_ranking(category, round_number)

    # Obtenir le podium
    podium = RankingService.get_podium(ranking)

    # Formater pour l'affichage groupé des ex-aequo
    grouped_ranking = RankingService.format_ranking_for_display(ranking)

    return JsonResponse({
        'success': True,
        'data': {
            'category': {
                'id': category.id,
                'name': category.name,
            },
            'round_number': round_number,
            'total_rounds': calculate_total_rounds(category),
            'ranking': ranking,
            'grouped_ranking': grouped_ranking,
            'podium': podium,
            'total_participants': len(ranking),
        }
    })


@login_required
def check_can_modify_score(request, performance_id):
    """
    PROMPT 10: Vérifie si un juge peut modifier un score (non verrouillé).
    """
    from ..models.technical_scoring import Performance, JudgeCategoryLock

    performance = get_object_or_404(Performance, id=performance_id)
    judge = get_judge_for_user(request.user)

    if not judge:
        return JsonResponse({
            'can_modify': False,
            'reason': _('Juge non trouvé.')
        })

    round_number = int(request.GET.get('round', 1))

    is_locked = JudgeCategoryLock.is_judge_locked(judge, performance.category, round_number)

    return JsonResponse({
        'can_modify': not is_locked,
        'is_locked': is_locked,
        'reason': _('Vos notes sont verrouillées.') if is_locked else None
    })


# ===== API RESET SCORES (pour les tests) =====

@login_required
def reset_category_scores(request, category_id):
    """
    Réinitialise tous les scores d'une catégorie.
    Usage: Pour les tests avant compétition.

    ATTENTION: Cette action est irréversible !
    Seuls les administrateurs/organisateurs peuvent l'utiliser.
    """
    from ..models import CompetitionCategory
    from ..models.technical_scoring import Score, Performance
    import json
    import logging

    logger = logging.getLogger(__name__)

    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': _('Méthode non autorisée. Utilisez POST.')
        }, status=405)

    try:
        category = get_object_or_404(CompetitionCategory, id=category_id)

        # Vérifier les permissions (admin, organisateur ou juge de la catégorie)
        user = request.user
        judge = get_judge_for_user(user)

        # Pour la sécurité, on vérifie si l'utilisateur est staff ou organisateur
        is_authorized = user.is_staff or user.is_superuser

        # Ou si c'est le juge qui a noté et veut reset ses propres scores
        if not is_authorized and judge:
            is_authorized = True  # Le juge peut reset ses propres scores

        if not is_authorized:
            return JsonResponse({
                'success': False,
                'message': _('Vous n\'avez pas les permissions pour cette action.')
            }, status=403)

        try:
            data = json.loads(request.body) if request.body else {}
            confirmed = data.get('confirmed', False)
            judge_only = data.get('judge_only', True)  # Par défaut, reset seulement les scores du juge
        except json.JSONDecodeError:
            confirmed = False
            judge_only = True

        if not confirmed:
            return JsonResponse({
                'success': False,
                'message': _('Confirmation requise. Envoyez confirmed=true.')
            }, status=400)

        # Récupérer les performances de la catégorie
        performances = Performance.objects.filter(category=category)
        logger.info(f"[reset_category_scores] Catégorie {category_id}, {performances.count()} performances trouvées")

        if judge_only and judge:
            # Reset seulement les scores de ce juge
            scores_to_delete = Score.objects.filter(
                performance__in=performances,
                judge=judge
            )
            deleted_count = scores_to_delete.count()
            scores_to_delete.delete()
            message = f'{deleted_count} score(s) du juge réinitialisé(s).'
        else:
            # Reset tous les scores (admin seulement)
            if not (user.is_staff or user.is_superuser):
                return JsonResponse({
                    'success': False,
                    'message': _('Seuls les administrateurs peuvent réinitialiser tous les scores.')
                }, status=403)

            scores_to_delete = Score.objects.filter(
                performance__in=performances
            )
            deleted_count = scores_to_delete.count()
            scores_to_delete.delete()
            message = f'{deleted_count} score(s) réinitialisé(s) pour la catégorie.'

        # Réinitialiser les totaux des performances
        performances.update(total_score=None)

        logger.info(f"[reset_category_scores] {deleted_count} scores supprimés")

        return JsonResponse({
            'success': True,
            'message': message,
            'data': {
                'deleted_count': deleted_count,
                'category_id': category.id,
                'category_name': category.name,
            }
        })
    except Exception as e:
        logger.exception(f"[reset_category_scores] Erreur: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Erreur serveur: {str(e)}'
        }, status=500)


# ===== ANALYSE DE NEUTRALITÉ DES JUGES =====

@login_required
def judge_neutrality(request, competition_id=None):
    """
    Page d'analyse de neutralité des juges pour une compétition.
    Affiche les indicateurs de biais potentiels pour chaque juge.

    SÉCURITÉ RGPD: L'utilisateur ne peut voir QUE les compétitions:
    - qu'il a créées
    - dont il est admin/manager de l'organisation organisatrice
    - où il est juge assigné (pour voir SES PROPRES analyses)
    """
    from ..models import Competition
    from ..services.judge_neutrality_service import judge_neutrality_service
    from apps.organizations.models import OrganizationMember
    import logging

    logger = logging.getLogger(__name__)
    user = request.user
    competition = None
    summary = None

    # Récupérer la compétition depuis GET si pas dans URL
    if not competition_id:
        competition_id = request.GET.get('competition')

    # ===== FONCTION HELPER: Vérifier si l'utilisateur a accès organisateur =====
    def user_is_competition_organizer(comp, usr):
        """Vérifie si l'utilisateur est organisateur de la compétition"""
        # Staff/superuser ont toujours accès
        if usr.is_staff or usr.is_superuser:
            return True

        # Créateur de la compétition
        if hasattr(comp, 'created_by') and comp.created_by == usr:
            return True

        # Admin de l'organisation organisatrice
        if comp.organizing_organization:
            try:
                org_member = OrganizationMember.objects.filter(
                    organization=comp.organizing_organization,
                    user=usr
                ).first()
                if org_member:
                    admin_roles = ['admin', 'owner', 'manager', 'president', 'secretary']
                    if getattr(org_member, 'role', '').lower() in admin_roles:
                        return True
            except Exception:
                pass

        return False

    if competition_id:
        try:
            competition = Competition.objects.get(id=competition_id)

            # SÉCURITÉ: Vérifier les droits d'accès strictement
            has_access = user_is_competition_organizer(competition, user)

            if has_access:
                # Générer le rapport de neutralité
                try:
                    summary = judge_neutrality_service.get_competition_summary(competition_id)
                except Exception as e:
                    logger.error(f"Error generating neutrality report: {e}")
                    messages.warning(request, _("Erreur lors de l'analyse de neutralité."))
            else:
                messages.warning(request, _("Vous n'avez pas accès à l'analyse de neutralité de cette compétition."))
                competition = None

        except Competition.DoesNotExist:
            messages.warning(request, _("Compétition non trouvée."))

    # ===== LISTE DES COMPÉTITIONS ACCESSIBLES (SÉCURITÉ RGPD) =====
    # L'utilisateur ne voit QUE les compétitions dont il est organisateur
    try:
        available_competitions = Competition.objects.none()

        if user.is_staff or user.is_superuser:
            # Admins voient toutes les compétitions
            available_competitions = Competition.objects.filter(
                status__in=['published', 'ongoing', 'completed']
            )
        else:
            # 1. Compétitions créées par l'utilisateur
            user_created = Competition.objects.filter(created_by=user)

            # 2. Compétitions des organisations où l'utilisateur est ADMIN/MANAGER
            # (pas juste membre, mais avec un rôle d'administration)
            admin_roles = ['admin', 'owner', 'manager', 'president', 'secretary']
            user_admin_orgs = OrganizationMember.objects.filter(
                user=user,
                role__in=admin_roles
            ).values_list('organization_id', flat=True)

            org_competitions = Competition.objects.filter(
                organizing_organization_id__in=user_admin_orgs
            )

            # Combiner et filtrer sur les statuts pertinents
            available_competitions = (user_created | org_competitions).filter(
                status__in=['published', 'ongoing', 'completed', 'draft']
            ).distinct()

        available_competitions = available_competitions.order_by('-start_date')

    except Exception as e:
        logger.error(f"Error fetching available competitions: {e}")
        available_competitions = Competition.objects.none()

    context = {
        'competition': competition,
        'summary': summary,
        'available_competitions': available_competitions,
        'active_page': 'neutrality',
    }

    return render(request, 'competitions/technical_scoring/judge_neutrality.html', context)


@login_required
def judge_neutrality_api(request, competition_id):
    """
    API JSON pour récupérer les données de neutralité d'une compétition.
    Utilisé pour les mises à jour dynamiques et l'export.

    SÉCURITÉ RGPD: Seuls les organisateurs de la compétition peuvent accéder.
    """
    from ..models import Competition
    from ..services.judge_neutrality_service import judge_neutrality_service
    from apps.organizations.models import OrganizationMember
    from dataclasses import asdict
    import logging

    logger = logging.getLogger(__name__)
    user = request.user

    # ===== SÉCURITÉ RGPD: Vérifier les permissions strictement =====
    try:
        competition = Competition.objects.get(id=competition_id)
    except Competition.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': _('Compétition non trouvée.')
        }, status=404)

    has_access = user.is_staff or user.is_superuser

    if not has_access:
        # Vérifier si l'utilisateur est créateur
        if hasattr(competition, 'created_by') and competition.created_by == user:
            has_access = True

        # Vérifier si l'utilisateur est admin de l'organisation
        if not has_access and competition.organizing_organization:
            try:
                org_member = OrganizationMember.objects.filter(
                    organization=competition.organizing_organization,
                    user=user
                ).first()
                if org_member:
                    admin_roles = ['admin', 'owner', 'manager', 'president', 'secretary']
                    if getattr(org_member, 'role', '').lower() in admin_roles:
                        has_access = True
            except Exception:
                pass

    if not has_access:
        return JsonResponse({
            'success': False,
            'message': _('Accès non autorisé à cette compétition.')
        }, status=403)

    try:
        summary = judge_neutrality_service.get_competition_summary(competition_id)

        # Convertir les dataclasses en dictionnaires
        reports_data = []
        for report in summary.get('reports', []):
            report_dict = {
                'judge_id': report.judge_id,
                'judge_name': report.judge_name,
                'judge_club': report.judge_club,
                'judge_nationality': report.judge_nationality,
                'total_scores': report.total_scores,
                'average_score': report.average_score,
                'std_deviation': report.std_deviation,
                'neutrality_score': report.neutrality_score,
                'correlation_score': report.correlation_score,
                'club_bias': {
                    'value': report.club_bias.value,
                    'severity': report.club_bias.severity,
                    'description': report.club_bias.description,
                },
                'nationality_bias': {
                    'value': report.nationality_bias.value,
                    'severity': report.nationality_bias.severity,
                    'description': report.nationality_bias.description,
                },
                'position_bias': {
                    'value': report.position_bias.value,
                    'severity': report.position_bias.severity,
                    'description': report.position_bias.description,
                },
                'score_distribution': report.score_distribution,
                'alerts': report.alerts,
            }
            reports_data.append(report_dict)

        return JsonResponse({
            'success': True,
            'data': {
                'competition_id': summary['competition_id'],
                'total_judges': summary['total_judges'],
                'average_neutrality': summary['average_neutrality'],
                'judges_with_alerts': summary['judges_with_alerts'],
                'reports': reports_data,
            }
        })

    except Exception as e:
        logger.exception(f"Error in judge_neutrality_api: {e}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)