from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.urls import reverse

from competitions.models import (
    Competition, CompetitionCategory, CompetitionRegistration, 
    Practitioner, Club
)
from competitions.utils.decorators import competition_management_permission_required
from competitions.forms.registrations import (
    CompetitionRegistrationForm, BulkRegistrationApprovalForm,
    CategoryAssignmentForm
)


@login_required
@competition_management_permission_required
def participants_list(request, competition_id):
    """
    Affiche la liste des participants à une compétition avec options de filtrage.
    """
    # Récupérer la compétition
    competition = get_object_or_404(Competition, pk=competition_id)
    
    # Récupérer les inscriptions
    registrations = CompetitionRegistration.objects.filter(
        competition=competition,
        is_competitor=True
    ).select_related('practitioner', 'practitioner__club')
    
    # Filtres
    status = request.GET.get('status')
    club_id = request.GET.get('club')
    category_id = request.GET.get('category')
    search_query = request.GET.get('q')
    
    # Appliquer les filtres
    if status:
        registrations = registrations.filter(status=status)
    
    if club_id:
        registrations = registrations.filter(practitioner__club_id=club_id)
    
    if category_id:
        registrations = registrations.filter(categories__id=category_id)
    
    if search_query:
        registrations = registrations.filter(
            Q(practitioner__first_name__icontains=search_query) | 
            Q(practitioner__last_name__icontains=search_query) |
            Q(practitioner__club__name__icontains=search_query)
        )
    
    # Récupérer les clubs et catégories pour les filtres
    clubs = Club.objects.filter(
        practitioners__registrations__competition=competition,
        practitioners__registrations__is_competitor=True
    ).distinct()
    
    categories = CompetitionCategory.objects.filter(
        competition=competition
    ).order_by('name')
    
    # Pagination
    paginator = Paginator(registrations.order_by('practitioner__last_name'), 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'competition': competition,
        'page_obj': page_obj,
        'clubs': clubs,
        'categories': categories,
        'status_filter': status,
        'club_filter': club_id,
        'category_filter': category_id,
        'search_query': search_query,
        'pending_count': registrations.filter(status='pending').count(),
        'approved_count': registrations.filter(status='approved').count(),
        'rejected_count': registrations.filter(status='rejected').count(),
    }
    
    return render(request, 'competitions/management/participants.html', context)


@login_required
@competition_management_permission_required
def participant_detail(request, competition_id, registration_id):
    """
    Affiche les détails d'une inscription et permet de la modifier.
    """
    # Récupérer la compétition et l'inscription
    competition = get_object_or_404(Competition, pk=competition_id)
    registration = get_object_or_404(
        CompetitionRegistration, 
        pk=registration_id, 
        competition=competition,
        is_competitor=True
    )
    
    if request.method == 'POST':
        form = CompetitionRegistrationForm(request.POST, instance=registration)
        if form.is_valid():
            form.save()
            messages.success(request, _("L'inscription a été mise à jour avec succès."))
            return redirect('competitions:management:participants_list', competition_id=competition_id)
    else:
        form = CompetitionRegistrationForm(instance=registration)
    
    # Récupérer les catégories auxquelles le participant est inscrit
    participant_categories = registration.categories.all()
    
    # Récupérer toutes les catégories disponibles
    all_categories = CompetitionCategory.objects.filter(competition=competition)
    
    context = {
        'competition': competition,
        'registration': registration,
        'form': form,
        'participant_categories': participant_categories,
        'all_categories': all_categories,
    }
    
    return render(request, 'competitions/management/participant_detail.html', context)


@login_required
@competition_management_permission_required
@require_POST
def update_registration_status(request, competition_id, registration_id):
    """
    Met à jour le statut d'une inscription (approuver/rejeter).
    """
    # Récupérer la compétition et l'inscription
    competition = get_object_or_404(Competition, pk=competition_id)
    registration = get_object_or_404(
        CompetitionRegistration, 
        pk=registration_id, 
        competition=competition
    )
    
    # Récupérer le nouveau statut
    status = request.POST.get('status')
    if status not in ['pending', 'approved', 'rejected']:
        messages.error(request, _("Statut invalide."))
        return redirect('competitions:management:participant_detail', 
                       competition_id=competition_id, 
                       registration_id=registration_id)
    
    # Mettre à jour le statut
    registration.status = status
    
    # Ajouter une note si fournie
    note = request.POST.get('note')
    if note:
        if registration.notes:
            registration.notes += f"\n{note}"
        else:
            registration.notes = note
    
    registration.save()
    
    messages.success(request, _("Le statut de l'inscription a été mis à jour."))
    
    # Rediriger vers la liste ou le détail selon le paramètre
    if request.POST.get('redirect_to_list'):
        return redirect('competitions:management:participants_list', competition_id=competition_id)
    
    return redirect('competitions:management:participant_detail', 
                   competition_id=competition_id, 
                   registration_id=registration_id)


@login_required
@competition_management_permission_required
def bulk_approval(request, competition_id):
    """
    Approuve ou rejette plusieurs inscriptions en une seule opération.
    """
    # Récupérer la compétition
    competition = get_object_or_404(Competition, pk=competition_id)
    
    if request.method == 'POST':
        form = BulkRegistrationApprovalForm(request.POST, competition=competition)
        if form.is_valid():
            action = form.cleaned_data['action']
            selected_registrations = form.cleaned_data['registrations']
            note = form.cleaned_data['note']
            
            # Mettre à jour le statut des inscriptions sélectionnées
            for registration in selected_registrations:
                registration.status = action
                if note:
                    if registration.notes:
                        registration.notes += f"\n{note}"
                    else:
                        registration.notes = note
                registration.save()
            
            count = len(selected_registrations)
            action_display = _("approuvées") if action == 'approved' else _("rejetées")
            messages.success(request, _("{} inscriptions ont été {}.").format(count, action_display))
            
            return redirect('competitions:management:participants_list', competition_id=competition_id)
    else:
        # Pré-sélectionner les inscriptions en attente
        initial_registrations = CompetitionRegistration.objects.filter(
            competition=competition,
            status='pending',
            is_competitor=True
        )
        form = BulkRegistrationApprovalForm(competition=competition, initial={
            'registrations': initial_registrations
        })
    
    context = {
        'competition': competition,
        'form': form,
    }
    
    return render(request, 'competitions/management/bulk_approval.html', context)


@login_required
@competition_management_permission_required
def category_assignment(request, competition_id):
    """
    Permet d'assigner plusieurs participants à des catégories.
    """
    # Récupérer la compétition
    competition = get_object_or_404(Competition, pk=competition_id)
    
    if request.method == 'POST':
        form = CategoryAssignmentForm(request.POST, competition=competition)
        if form.is_valid():
            category = form.cleaned_data['category']
            registrations = form.cleaned_data['registrations']
            
            # Ajouter les participants à la catégorie
            for registration in registrations:
                registration.categories.add(category)
            
            count = len(registrations)
            messages.success(request, _("{} participants ont été assignés à la catégorie {}.").format(
                count, category.name))
            
            return redirect('competitions:management:participants_list', competition_id=competition_id)
    else:
        # Formulaire initial
        form = CategoryAssignmentForm(competition=competition)
    
    context = {
        'competition': competition,
        'form': form,
    }
    
    return render(request, 'competitions/management/category_assignment.html', context)


@login_required
@competition_management_permission_required
def participant_search(request, competition_id):
    """
    Recherche de participants pour les requêtes AJAX.
    """
    competition = get_object_or_404(Competition, pk=competition_id)
    search_query = request.GET.get('q', '')
    
    if not search_query:
        return JsonResponse({'results': []})
    
    # Rechercher les participants inscrits
    registrations = CompetitionRegistration.objects.filter(
        competition=competition,
        is_competitor=True,
        status='approved',
        practitioner__isnull=False
    ).select_related('practitioner', 'practitioner__club').filter(
        Q(practitioner__first_name__icontains=search_query) | 
        Q(practitioner__last_name__icontains=search_query)
    )[:10]
    
    results = []
    for registration in registrations:
        p = registration.practitioner
        results.append({
            'id': registration.id,
            'name': f"{p.first_name} {p.last_name}",
            'club': p.club.name if p.club else "",
            'club_id': p.club.id if p.club else None,
            'detail_url': reverse('competitions:management:participant_detail', 
                                 kwargs={'competition_id': competition_id, 
                                         'registration_id': registration.id})
        })
    
    return JsonResponse({'results': results})


@login_required
@competition_management_permission_required
def club_participants(request, competition_id, club_id):
    """
    Affiche tous les participants d'un club spécifique.
    """
    # Récupérer la compétition et le club
    competition = get_object_or_404(Competition, pk=competition_id)
    club = get_object_or_404(Club, pk=club_id)
    
    # Récupérer les inscriptions des participants de ce club
    registrations = CompetitionRegistration.objects.filter(
        competition=competition,
        is_competitor=True,
        practitioner__club=club
    ).select_related('practitioner')
    
    context = {
        'competition': competition,
        'club': club,
        'registrations': registrations,
    }
    
    return render(request, 'competitions/management/club_participants.html', context)


@login_required
@competition_management_permission_required
def export_participants(request, competition_id):
    """
    Exporte la liste des participants au format CSV.
    """
    import csv
    from django.http import HttpResponse
    
    competition = get_object_or_404(Competition, pk=competition_id)
    
    # Filtres (comme dans la liste)
    status = request.GET.get('status')
    club_id = request.GET.get('club')
    category_id = request.GET.get('category')
    
    registrations = CompetitionRegistration.objects.filter(
        competition=competition,
        is_competitor=True
    ).select_related('practitioner', 'practitioner__club')
    
    # Appliquer les filtres
    if status:
        registrations = registrations.filter(status=status)
    
    if club_id:
        registrations = registrations.filter(practitioner__club_id=club_id)
    
    if category_id:
        registrations = registrations.filter(categories__id=category_id)
    
    # Créer la réponse HTTP avec l'en-tête CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{competition.title}_participants.csv"'
    
    # Écrire le fichier CSV
    writer = csv.writer(response)
    writer.writerow([
        _('Nom'), _('Prénom'), _('Club'), _('Grade'), 
        _('Catégories'), _('Statut'), _('Notes')
    ])
    
    for reg in registrations:
        p = reg.practitioner
        categories = ', '.join([c.name for c in reg.categories.all()])
        
        writer.writerow([
            p.last_name,
            p.first_name,
            p.club.name if p.club else "",
            p.grade,
            categories,
            reg.get_status_display(),
            reg.notes
        ])
    
    return response