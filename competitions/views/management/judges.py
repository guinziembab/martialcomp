from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from competitions.models import (
    Competition, CompetitionCategory, JudgeAssignment,
    CompetitionRegistration, Judge, JudgeQualification
)
from competitions.models.schedule import TatamiSchedule
from competitions.utils.decorators import competition_management_permission_required
from competitions.forms.judges import (
    JudgeQualificationForm, JudgeAssignmentForm, JudgeProfileForm
)


@login_required
@competition_management_permission_required
def judges_list(request, competition_id):
    """
    Affiche la liste des juges assignés à une compétition.
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
    
    # Pagination
    paginator = Paginator(assignments.order_by('category', 'user__last_name'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Récupérer les juges déjà inscrits à la compétition
    registered_judges = CompetitionRegistration.objects.filter(
        competition=competition,
        is_technical_judge=True
    ).select_related('practitioner').order_by('practitioner__last_name')
    
    context = {
        'competition': competition,
        'page_obj': page_obj,
        'categories': categories,
        'registered_judges': registered_judges,
        'category_filter': category_id,
        'type_filter': assignment_type,
        'search_query': search_query,
        'assignment_types': dict(JudgeAssignment.ASSIGNMENT_TYPES),
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
            messages.success(request, _("L'assignation du juge a été mise à jour avec succès."))
            return redirect('competitions:management:judges_list', competition_id=competition_id)
    else:
        form = JudgeAssignmentForm(instance=assignment, competition=competition)
    
    # Récupérer les autres assignations du même juge
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
            
            # Vérifier si le juge a une inscription à la compétition
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
            return redirect('competitions:management:judges_list', competition_id=competition_id)
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
    return redirect('competitions:management:judges_list', competition_id=competition_id)


@login_required
@competition_management_permission_required
def bulk_judge_assignment(request, competition_id):
    """
    Permet d'assigner plusieurs juges à une catégorie.
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
                # Vérifier si une assignation existe déjà
                exists = JudgeAssignment.objects.filter(
                    category=category,
                    user=judge,
                    assignment_type=assignment_type
                ).exists()
                
                if not exists:
                    # Vérifier si le juge a une inscription à la compétition
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
                messages.success(request, _("{} juges ont été assignés à la catégorie {}.").format(
                    success_count, category.name))
            else:
                messages.info(request, _("Aucune nouvelle assignation n'a été créée. Les juges sélectionnés étaient peut-être déjà assignés."))
            
            return redirect('competitions:management:judges_list', competition_id=competition_id)
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
    Recherche de juges pour les requêtes AJAX.
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
        from competitions.models.schedule import CompetitionSchedule
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
    
    # Ajouter les assignations à chaque catégorie
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
            
            messages.success(request, _("Le planning du juge a été mis à jour avec succès."))
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