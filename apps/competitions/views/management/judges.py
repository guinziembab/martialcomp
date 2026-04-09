from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from apps.competitions.models import (
    Competition, CompetitionCategory, JudgeAssignment,
    CompetitionRegistration, Judge, Discipline
)
# Importer JudgeQualification depuis le bon module
try:
    from apps.competitions.models.judging import JudgeQualification
except ImportError:
    try:
        from apps.competitions.models.judges import JudgeQualification
    except ImportError:
        JudgeQualification = None
from apps.competitions.models.schedule import TatamiSchedule
from apps.competitions.utils.decorators import competition_management_permission_required
from apps.competitions.forms.judges import (
    JudgeQualificationForm, JudgeAssignmentForm, JudgeProfileForm
)
from apps.competitions.utils.organization_discipline_filtering import (
    get_organization_disciplines
)
from django.db.models import Count, Q


@login_required
@competition_management_permission_required
def judges_list(request, competition_id):
    """
    Affiche la liste des juges assignés Ã  une compétition.
    """
    # Récupérer la compétition
    competition = get_object_or_404(Competition, pk=competition_id)
    
    # Récupérer les assignations de juges
    assignments = JudgeAssignment.objects.filter(
        category__competition=competition
    ).select_related('user', 'category', 'registration__practitioner')
    
    # Filtres
    category_id = request.GET.get('category')
    assignment_type = request.GET.get('type')
    search_query = request.GET.get('q')
    
    # Appliquer les filtres
    if category_id:
        assignments = assignments.filter(category_id=category_id)
    
    if assignment_type:
        assignments = assignments.filter(assignment_type=assignment_type)
    
    if search_query:
        assignments = assignments.filter(
            Q(user__first_name__icontains=search_query) | 
            Q(user__last_name__icontains=search_query) |
            Q(registration__practitioner__first_name__icontains=search_query) |
            Q(registration__practitioner__last_name__icontains=search_query)
        )
    
    # Récupérer les catégories pour les filtres
    categories = CompetitionCategory.objects.filter(
        competition=competition
    ).order_by('name')
    
    # Grouper les assignations par catégorie pour l'onglet "Assignments"
    assignments_by_category = {}
    # Évaluer le QuerySet avant l'itération pour éviter les problèmes
    assignments_list = list(assignments)
    for assignment in assignments_list:
        category_id = assignment.category_id
        if category_id not in assignments_by_category:
            assignments_by_category[category_id] = []
        assignments_by_category[category_id].append(assignment)
    
    # Pagination - utiliser le queryset original pour la pagination
    paginator = Paginator(assignments.order_by('category', 'user__last_name'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Récupérer les juges: inscrits comme juges OU ayant des assignations
    assigned_user_ids_for_comp = set(
        JudgeAssignment.objects.filter(
            category__competition=competition
        ).values_list('registration_id', flat=True)
    )
    registered_judges = CompetitionRegistration.objects.filter(
        competition=competition
    ).filter(
        Q(is_technical_judge=True) | Q(is_combat_referee=True) | Q(id__in=assigned_user_ids_for_comp)
    ).select_related('practitioner', 'practitioner__user').order_by('practitioner__last_name')

    # Créer deux listes séparées:
    # - assigned_judges_list: juges avec au moins une assignation à une catégorie
    # - registered_judges_list: juges inscrits mais SANS assignation (disponibles)
    assigned_judges_list = []
    registered_judges_list = []
    confirmed_count = 0
    pending_count = 0

    for registration in registered_judges:
        practitioner = registration.practitioner
        user = getattr(practitioner, 'user', None)

        # Récupérer toutes les assignations de ce juge pour cette compétition
        user_assignments = None
        has_assignments = False
        if user:
            user_assignments = JudgeAssignment.objects.filter(
                category__competition=competition,
                user=user
            ).select_related('category', 'user')
            has_assignments = user_assignments.exists()

        # Déterminer les catégories assignées
        categories = []
        if has_assignments:
            categories = [ass.category.name for ass in user_assignments]

        # Déterminer le rôle principal basé sur l'inscription ou les assignations
        if has_assignments:
            assignment_types = [ass.assignment_type for ass in user_assignments]
            main_type = max(set(assignment_types), key=assignment_types.count) if assignment_types else 'technical_judge'
        elif registration.is_combat_referee:
            main_type = 'combat_referee'
        else:
            main_type = 'technical_judge'

        # Récupérer le niveau de qualification
        qualification_level = 'novice'
        if JudgeQualification:
            qual = JudgeQualification.objects.filter(
                practitioner=practitioner
            ).order_by('-level' if hasattr(JudgeQualification, 'level') else '-qualification_level').first()
            if qual:
                qualification_level = qual.level if hasattr(qual, 'level') else getattr(qual, 'qualification_level', 'novice')

        # Déterminer le statut de confirmation
        is_confirmed = False
        if has_assignments:
            is_confirmed = any(ass.status == 'confirmed' for ass in user_assignments)
        else:
            # Si pas d'assignations, utiliser le statut de l'inscription
            is_confirmed = registration.status == 'approved'

        # Construire les données du juge
        judge_data = {
            'user': user,
            'practitioner': practitioner,
            'registration': registration,
            'full_name': practitioner.full_name,
            'email': user.email if user else getattr(practitioner, 'email', ''),
            'categories': categories,
            'assignment_type': main_type,
            'qualification_level': qualification_level,
            'is_confirmed': is_confirmed,
            'assignments': user_assignments if user_assignments else [],
            'first_assignment_id': user_assignments.first().id if has_assignments else None,
        }

        # Séparer les juges assignés des juges disponibles (inscrits sans assignation)
        if has_assignments:
            # Comptabiliser les confirmés et en attente seulement pour les juges assignés
            if is_confirmed:
                confirmed_count += 1
            else:
                pending_count += 1
            assigned_judges_list.append(judge_data)
        else:
            # Juge inscrit mais pas encore assigné à une catégorie
            registered_judges_list.append(judge_data)
    
    # Calculer les statistiques de qualifications par discipline (uniquement disciplines de l'organisation)
    qualification_summary = {}
    qualification_levels = ['international', 'national', 'regional', 'novice']
    qualification_types = ['technical', 'combat', 'chief', 'assistant']
    
    # Récupérer l'organisation de la compétition
    org = getattr(competition, 'organizing_organization', None)
    if org and JudgeQualification:
        # Récupérer uniquement les disciplines de l'organisation
        org_disciplines = get_organization_disciplines(org)
        
        # S'assurer qu'on ne traite que les disciplines de l'organisation
        org_discipline_ids = set(org_disciplines.values_list('id', flat=True))
        
        # Pour chaque discipline de l'organisation, calculer les statistiques
        for discipline in org_disciplines:
            # Double vérification : s'assurer que la discipline appartient bien à l'organisation
            if discipline.id not in org_discipline_ids:
                continue
            # Récupérer les qualifications pour cette discipline (actives uniquement)
            qualifications = JudgeQualification.objects.filter(
                discipline=discipline
            )
            
            # Vérifier si le modèle a is_active
            if hasattr(JudgeQualification, 'is_active'):
                qualifications = qualifications.filter(is_active=True)
            
            # Compter par niveau - vérifier quel champ est utilisé
            level_counts = {}
            for level in qualification_levels:
                # Essayer qualification_level d'abord (modèle judging.py), puis level (modèle judges.py)
                if hasattr(JudgeQualification, 'qualification_level'):
                    count = qualifications.filter(qualification_level=level).count()
                elif hasattr(JudgeQualification, 'level'):
                    count = qualifications.filter(level=level).count()
                else:
                    count = 0
                level_counts[level] = count
            
            # Compter par type
            type_counts = {}
            for qtype in qualification_types:
                # Mapper les types selon le modèle utilisé
                if qtype == 'assistant':
                    # Pour assistant, essayer 'assistant' ou 'timekeeper'
                    count = qualifications.filter(
                        Q(qualification_type='assistant') | Q(qualification_type='timekeeper')
                    ).count()
                else:
                    # Essayer le type direct ou avec _judge
                    count = qualifications.filter(
                        Q(qualification_type=qtype) | Q(qualification_type=f'{qtype}_judge')
                    ).count()
                type_counts[qtype] = count
            
            qualification_summary[discipline] = {
                'level_counts': level_counts,
                'type_counts': type_counts,
                'total': qualifications.count()
            }
    
    # Fallback: si aucune qualification formelle, calculer depuis les assignations
    if not qualification_summary or all(s['total'] == 0 for s in qualification_summary.values()):
        # Compter les types depuis les assignations de cette compétition
        from apps.competitions.models import Judge as JudgeModel
        all_judges_active = JudgeModel.objects.filter(active=True, user__isnull=False)
        type_from_assignments = {}
        for at in JudgeAssignment.objects.filter(category__competition=competition):
            atype = at.assignment_type or 'technical_judge'
            mapped = 'technical' if 'technical' in atype else 'combat' if 'combat' in atype else 'chief' if 'chief' in atype else 'assistant'
            type_from_assignments[mapped] = type_from_assignments.get(mapped, 0) + 1

        # Compter les niveaux depuis le modèle Judge
        level_from_judges = {}
        for j in all_judges_active:
            lvl = getattr(j, 'qualification_level', 'novice') or 'novice'
            level_from_judges[lvl] = level_from_judges.get(lvl, 0) + 1

        # Injecter comme si c'était une discipline unique
        from apps.competitions.models.competitions import Competition as Comp
        disc_name = str(competition.discipline) if competition.discipline else 'General'
        qualification_summary = {
            competition.discipline or type('D', (), {'id': 0, 'name': disc_name}): {
                'level_counts': {l: level_from_judges.get(l, 0) for l in qualification_levels},
                'type_counts': {t: type_from_assignments.get(t, 0) for t in qualification_types},
                'total': all_judges_active.count()
            }
        }

    # Calculer les totaux globaux
    total_levels = {level: 0 for level in qualification_levels}
    total_types = {qtype: 0 for qtype in qualification_types}
    grand_total = 0
    
    # Vérifier que toutes les disciplines dans qualification_summary appartiennent à l'organisation
    if org:
        org_discipline_ids = set(get_organization_disciplines(org).values_list('id', flat=True))
        filtered_summary = {
            disc: stats for disc, stats in qualification_summary.items()
            if disc.id in org_discipline_ids
        }
        qualification_summary = filtered_summary
    
    for discipline, stats in qualification_summary.items():
        for level, count in stats['level_counts'].items():
            total_levels[level] = total_levels.get(level, 0) + count
        for qtype, count in stats['type_counts'].items():
            total_types[qtype] = total_types.get(qtype, 0) + count
        grand_total += stats['total']
    
    # Récupérer les juges disponibles (filtrés par les disciplines de l'organisation)
    available_judges = []
    if org and JudgeQualification:
        # Récupérer les disciplines de l'organisation
        org_disciplines = get_organization_disciplines(org)
        
        if org_disciplines.exists():
            # Récupérer les IDs des utilisateurs déjà assignés à cette compétition
            assigned_user_ids = set(
                JudgeAssignment.objects.filter(
                    category__competition=competition
                ).values_list('user_id', flat=True)
            )
            
            # Récupérer les qualifications dans les disciplines de l'organisation
            discipline_ids = list(org_disciplines.values_list('id', flat=True))
            qualifications = JudgeQualification.objects.filter(
                discipline_id__in=discipline_ids
            ).select_related('practitioner', 'practitioner__user', 'discipline')
            
            # Grouper par praticien et construire la liste des juges disponibles
            judges_dict = {}
            for qual in qualifications:
                practitioner = qual.practitioner
                user = getattr(practitioner, 'user', None)
                
                # Ignorer si l'utilisateur est déjà assigné
                if user and user.id in assigned_user_ids:
                    continue
                
                # Créer ou mettre à jour l'entrée pour ce praticien
                if practitioner.id not in judges_dict:
                    judges_dict[practitioner.id] = {
                        'practitioner': practitioner,
                        'user': user,
                        'qualifications': [],
                        'disciplines': set(),
                        'highest_level': 'novice',
                        'years_experience': 0,
                    }
                
                # Ajouter la qualification
                judges_dict[practitioner.id]['qualifications'].append(qual)
                if qual.discipline:
                    judges_dict[practitioner.id]['disciplines'].add(qual.discipline)
                
                # Mettre à jour le niveau le plus élevé
                level_order = {'novice': 0, 'regional': 1, 'national': 2, 'international': 3}
                current_level = qual.level if hasattr(qual, 'level') else getattr(qual, 'qualification_level', 'novice')
                if level_order.get(current_level, 0) > level_order.get(judges_dict[practitioner.id]['highest_level'], 0):
                    judges_dict[practitioner.id]['highest_level'] = current_level
            
            # Convertir en liste et calculer les années d'expérience
            from apps.competitions.models import Judge
            for judge_data in judges_dict.values():
                practitioner = judge_data['practitioner']
                # Essayer de récupérer les années d'expérience depuis le modèle Judge
                try:
                    judge = Judge.objects.get(practitioner=practitioner)
                    judge_data['years_experience'] = judge.years_experience
                except Judge.DoesNotExist:
                    judge_data['years_experience'] = 0
                
                available_judges.append(judge_data)
            
            # Trier par niveau de qualification (international en premier) puis par nom
            level_order = {'international': 0, 'national': 1, 'regional': 2, 'novice': 3}
            available_judges.sort(
                key=lambda x: (
                    level_order.get(x['highest_level'], 3),
                    x['practitioner'].last_name or '',
                    x['practitioner'].first_name or ''
                )
            )
    
    # Fallback: si aucun juge trouvé via qualifications, montrer tous les juges actifs
    if not available_judges:
        from apps.competitions.models import Judge as JudgeModel
        assigned_user_ids = set(
            JudgeAssignment.objects.filter(
                category__competition=competition
            ).values_list('user_id', flat=True)
        )
        all_active_judges = JudgeModel.objects.filter(
            active=True, user__isnull=False
        ).select_related('user', 'practitioner').exclude(user_id__in=assigned_user_ids)
        for j in all_active_judges:
            available_judges.append({
                'practitioner': j.practitioner,
                'user': j.user,
                'qualifications': [],
                'disciplines': set(),
                'highest_level': j.qualification_level if hasattr(j, 'qualification_level') else 'novice',
                'years_experience': j.years_experience or 0,
            })

    # Calculer le total des juges disponibles (inscrits sans assignation + qualifiés disponibles)
    total_available = len(registered_judges_list) + len(available_judges)

    context = {
        'competition': competition,
        'page_obj': page_obj,
        'categories': categories,
        'categories_with_assignments_ids': set(assignments_by_category.keys()),
        'registered_judges': registered_judges,
        'assigned_judges': assigned_judges_list,
        'registered_judges_list': registered_judges_list,  # Juges inscrits sans assignation
        'confirmed_count': confirmed_count,
        'pending_count': pending_count,
        'available_judges': available_judges,
        'total_available': total_available,  # Total des juges disponibles
        'assignments_by_category': assignments_by_category,
        'all_assignments': assignments,  # Pour l'onglet Assignments
        'org_disciplines': list(get_organization_disciplines(org)) if org else [],
        'category_filter': category_id,
        'type_filter': assignment_type,
        'search_query': search_query,
        'assignment_types': dict(JudgeAssignment.ASSIGNMENT_TYPES),
        'qualification_summary': qualification_summary,
        'qualification_levels': qualification_levels,
        'qualification_types': qualification_types,
        'total_levels': total_levels,
        'total_types': total_types,
        'grand_total': grand_total,
    }
    
    return render(request, 'competitions/management/judges.html', context)


@login_required
@competition_management_permission_required
def judge_detail(request, competition_id, assignment_id):
    """
    Affiche les détails d'une assignation de juge et permet de la modifier.
    """
    # Récupérer la compétition et l'assignation
    competition = get_object_or_404(Competition, pk=competition_id)
    assignment = get_object_or_404(
        JudgeAssignment, 
        pk=assignment_id, 
        category__competition=competition
    )
    
    if request.method == 'POST':
        form = JudgeAssignmentForm(request.POST, instance=assignment, competition=competition)
        if form.is_valid():
            form.save()
            messages.success(request, _("L'assignation du juge a été mise Ã  jour avec succès."))
            return redirect('competitions:management:judges', competition_id=competition_id)
    else:
        form = JudgeAssignmentForm(instance=assignment, competition=competition)
    
    # Récupérer les autres assignations du mÃªme juge
    other_assignments = JudgeAssignment.objects.filter(
        category__competition=competition,
        user=assignment.user
    ).exclude(pk=assignment.pk)
    
    context = {
        'competition': competition,
        'assignment': assignment,
        'form': form,
        'other_assignments': other_assignments,
    }
    
    return render(request, 'competitions/management/judge_detail.html', context)


@login_required
@competition_management_permission_required
def add_judge_assignment(request, competition_id):
    """
    Ajoute une nouvelle assignation de juge.
    """
    # Récupérer la compétition
    competition = get_object_or_404(Competition, pk=competition_id)
    
    if request.method == 'POST':
        form = JudgeAssignmentForm(request.POST, competition=competition)
        if form.is_valid():
            assignment = form.save(commit=False)
            
            # Vérifier si le juge a une inscription Ã  la compétition
            try:
                registration = CompetitionRegistration.objects.get(
                    competition=competition,
                    user=assignment.user,
                    is_technical_judge=True
                )
                assignment.registration = registration
            except CompetitionRegistration.DoesNotExist:
                # Créer une inscription automatique si le juge n'est pas inscrit
                registration = CompetitionRegistration.objects.create(
                    competition=competition,
                    user=assignment.user,
                    is_technical_judge=True,
                    is_competitor=False,
                    status='approved'
                )
                assignment.registration = registration
                messages.info(request, _("Une inscription a été automatiquement créée pour ce juge."))
            
            assignment.save()
            messages.success(request, _("L'assignation du juge a été créée avec succès."))
            return redirect('competitions:management:judges', competition_id=competition_id)
    else:
        form = JudgeAssignmentForm(competition=competition)
    
    context = {
        'competition': competition,
        'form': form,
    }
    
    return render(request, 'competitions/management/add_judge_assignment.html', context)


@login_required
@competition_management_permission_required
@require_POST
def delete_judge_assignment(request, competition_id, assignment_id):
    """
    Supprime une assignation de juge.
    """
    # Récupérer la compétition et l'assignation
    competition = get_object_or_404(Competition, pk=competition_id)
    assignment = get_object_or_404(
        JudgeAssignment, 
        pk=assignment_id, 
        category__competition=competition
    )
    
    assignment.delete()
    messages.success(request, _("L'assignation du juge a été supprimée."))
    return redirect('competitions:management:judges', competition_id=competition_id)


@login_required
@competition_management_permission_required
@require_POST
def remove_judge_from_competition(request, competition_id, user_id):
    """
    Supprime toutes les assignations d'un juge pour une compétition.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Récupérer la compétition et l'utilisateur
    competition = get_object_or_404(Competition, pk=competition_id)
    user = get_object_or_404(User, pk=user_id)
    
    # Récupérer toutes les assignations de ce juge pour cette compétition
    assignments = JudgeAssignment.objects.filter(
        category__competition=competition,
        user=user
    )
    
    count = assignments.count()
    assignments.delete()
    
    if count > 0:
        messages.success(request, _("Le juge a été retiré de la compétition ({} assignation(s) supprimée(s)).").format(count))
    else:
        messages.info(request, _("Aucune assignation trouvée pour ce juge."))

    return redirect('competitions:management:judges', competition_id=competition_id)


@login_required
@competition_management_permission_required
@require_POST
def remove_judge_registration(request, competition_id, registration_id):
    """
    Retire un juge de la compétition via son inscription.
    Supprime le flag is_technical_judge et is_combat_referee de l'inscription.
    """
    # Récupérer la compétition et l'inscription
    competition = get_object_or_404(Competition, pk=competition_id)
    registration = get_object_or_404(
        CompetitionRegistration,
        pk=registration_id,
        competition=competition
    )

    # Récupérer le nom du juge pour le message
    judge_name = registration.practitioner.full_name if registration.practitioner else "Juge inconnu"

    # Supprimer les assignations de juge associées si un user est lié
    user = getattr(registration.practitioner, 'user', None)
    assignments_deleted = 0
    if user:
        assignments = JudgeAssignment.objects.filter(
            category__competition=competition,
            user=user
        )
        assignments_deleted = assignments.count()
        assignments.delete()

    # Retirer les rôles de juge de l'inscription
    registration.is_technical_judge = False
    registration.is_combat_referee = False
    registration.save()

    if assignments_deleted > 0:
        messages.success(request, _("{} a été retiré de la liste des juges ({} assignation(s) supprimée(s)).").format(judge_name, assignments_deleted))
    else:
        messages.success(request, _("{} a été retiré de la liste des juges.").format(judge_name))

    return redirect('competitions:management:judges', competition_id=competition_id)


@login_required
@competition_management_permission_required
def bulk_judge_assignment(request, competition_id):
    """
    Permet d'assigner plusieurs juges Ã  une catégorie.
    """
    # Récupérer la compétition
    competition = get_object_or_404(Competition, pk=competition_id)
    
    if request.method == 'POST':
        form = BulkJudgeAssignmentForm(request.POST, competition=competition)
        if form.is_valid():
            category = form.cleaned_data['category']
            judges = form.cleaned_data['judges']
            assignment_type = form.cleaned_data['assignment_type']
            
            # Créer les assignations pour chaque juge
            success_count = 0
            for judge in judges:
                # Vérifier si une assignation existe déjÃ 
                exists = JudgeAssignment.objects.filter(
                    category=category,
                    user=judge,
                    assignment_type=assignment_type
                ).exists()
                
                if not exists:
                    # Vérifier si le juge a une inscription Ã  la compétition
                    try:
                        registration = CompetitionRegistration.objects.get(
                            competition=competition,
                            user=judge,
                            is_technical_judge=True
                        )
                    except CompetitionRegistration.DoesNotExist:
                        # Créer une inscription automatique
                        registration = CompetitionRegistration.objects.create(
                            competition=competition,
                            user=judge,
                            is_technical_judge=True,
                            is_competitor=False,
                            status='approved'
                        )
                    
                    # Créer l'assignation
                    JudgeAssignment.objects.create(
                        category=category,
                        user=judge,
                        registration=registration,
                        assignment_type=assignment_type,
                        status='confirmed'
                    )
                    success_count += 1
            
            if success_count > 0:
                messages.success(request, _("{} juges ont été assignés Ã  la catégorie {}.").format(
                    success_count, category.name))
            else:
                messages.info(request, _("Aucune nouvelle assignation n'a été créée. Les juges sélectionnés étaient peut-Ãªtre déjÃ  assignés."))
            
            return redirect('competitions:management:judges', competition_id=competition_id)
    else:
        form = BulkJudgeAssignmentForm(competition=competition)
    
    context = {
        'competition': competition,
        'form': form,
    }
    
    return render(request, 'competitions/management/bulk_judge_assignment.html', context)


@login_required
@competition_management_permission_required
def judge_search(request, competition_id):
    """
    Recherche de juges pour les requÃªtes AJAX.
    """
    competition = get_object_or_404(Competition, pk=competition_id)
    search_query = request.GET.get('q', '')
    
    if not search_query:
        return JsonResponse({'results': []})
    
    # Rechercher les juges qualifiés
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Rechercher d'abord parmi les utilisateurs qui ont un profil de juge
    judges = User.objects.filter(
        Q(judge_profile__isnull=False) |
        Q(judgequalifications__isnull=False)
    ).filter(
        Q(first_name__icontains=search_query) | 
        Q(last_name__icontains=search_query) |
        Q(username__icontains=search_query) |
        Q(email__icontains=search_query)
    ).distinct()[:10]
    
    results = []
    for judge in judges:
        # Vérifier si le juge a des qualifications pertinentes
        qualifications = []
        try:
            if hasattr(judge, 'judgequalifications'):
                for qual in judge.judgequalifications.all():
                    qualifications.append(qual.get_qualification_type_display())
        except:
            pass
        
        results.append({
            'id': judge.id,
            'name': f"{judge.first_name} {judge.last_name}",
            'email': judge.email,
            'qualifications': qualifications,
            'is_registered': CompetitionRegistration.objects.filter(
                competition=competition,
                user=judge,
                is_technical_judge=True
            ).exists()
        })
    
    return JsonResponse({'results': results})


@login_required
@competition_management_permission_required
def judge_schedule(request, competition_id):
    """
    Gère le planning des juges pour la compétition.
    """
    # Récupérer la compétition
    competition = get_object_or_404(Competition, pk=competition_id)
    
    # Récupérer les tatamis
    try:
        from apps.competitions.models.schedule import CompetitionSchedule
        schedule = CompetitionSchedule.objects.get(competition=competition)
        tatamis = TatamiSchedule.objects.filter(competition_schedule=schedule)
    except:
        tatamis = []
    
    # Récupérer toutes les assignations de juges
    assignments = JudgeAssignment.objects.filter(
        category__competition=competition
    ).select_related('user', 'category')
    
    # Grouper les assignations par catégorie
    assignments_by_category = {}
    for assignment in assignments:
        if assignment.category_id not in assignments_by_category:
            assignments_by_category[assignment.category_id] = []
        assignments_by_category[assignment.category_id].append(assignment)
    
    # Récupérer les catégories
    categories = CompetitionCategory.objects.filter(
        competition=competition
    ).order_by('name')
    
    # Ajouter les assignations Ã  chaque catégorie
    for category in categories:
        category.judges = assignments_by_category.get(category.id, [])
    
    if request.method == 'POST':
        form = JudgeScheduleForm(request.POST, competition=competition)
        if form.is_valid():
            judge = form.cleaned_data['judge']
            categories = form.cleaned_data['categories']
            assignment_type = form.cleaned_data['assignment_type']
            
            # Supprimer les anciennes assignations
            JudgeAssignment.objects.filter(
                category__competition=competition,
                user=judge,
                assignment_type=assignment_type
            ).delete()
            
            # Créer les nouvelles assignations
            for category in categories:
                # Vérifier si le juge a une inscription
                try:
                    registration = CompetitionRegistration.objects.get(
                        competition=competition,
                        user=judge,
                        is_technical_judge=True
                    )
                except CompetitionRegistration.DoesNotExist:
                    # Créer une inscription automatique
                    registration = CompetitionRegistration.objects.create(
                        competition=competition,
                        user=judge,
                        is_technical_judge=True,
                        is_competitor=False,
                        status='approved'
                    )
                
                JudgeAssignment.objects.create(
                    category=category,
                    user=judge,
                    registration=registration,
                    assignment_type=assignment_type,
                    status='confirmed'
                )
            
            messages.success(request, _("Le planning du juge a été mis Ã  jour avec succès."))
            return redirect('competitions:management:judge_schedule', competition_id=competition_id)
    else:
        form = JudgeScheduleForm(competition=competition)
    
    context = {
        'competition': competition,
        'categories': categories,
        'tatamis': tatamis,
        'form': form,
    }
    
    return render(request, 'competitions/management/judge_schedule.html', context)


@login_required
@competition_management_permission_required
def judge_stats(request, competition_id):
    """
    Affiche des statistiques sur les juges de la compétition.
    """
    competition = get_object_or_404(Competition, pk=competition_id)
    
    # Nombre total de juges assignés
    total_judges = JudgeAssignment.objects.filter(
        category__competition=competition
    ).values('user').distinct().count()
    
    # Répartition par type d'assignation
    from django.db.models import Count
    assignment_types = JudgeAssignment.objects.filter(
        category__competition=competition
    ).values('assignment_type').annotate(
        count=Count('id')
    ).order_by('assignment_type')
    
    # Convertir les codes en libellés
    for item in assignment_types:
        for code, label in JudgeAssignment.ASSIGNMENT_TYPES:
            if item['assignment_type'] == code:
                item['label'] = label
                break
    
    # Répartition par catégorie
    category_stats = CompetitionCategory.objects.filter(
        competition=competition
    ).annotate(
        judges_count=Count('judge_assignments')
    ).values('name', 'judges_count').order_by('-judges_count')
    
    # Juges les plus assignés
    top_judges = JudgeAssignment.objects.filter(
        category__competition=competition
    ).values('user__first_name', 'user__last_name').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    context = {
        'competition': competition,
        'total_judges': total_judges,
        'assignment_types': assignment_types,
        'category_stats': category_stats,
        'top_judges': top_judges,
    }
    
    return render(request, 'competitions/management/judge_stats.html', context)

