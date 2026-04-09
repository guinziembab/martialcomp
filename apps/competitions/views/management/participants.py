from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.urls import reverse
import logging

from apps.competitions.models import (
    Competition, CompetitionCategory, CompetitionRegistration, 
    Practitioner, Club
)
from apps.competitions.utils.decorators import competition_management_permission_required
from apps.competitions.forms.registrations import (
    CompetitionRegistrationForm, BulkRegistrationApprovalForm,
    CategoryAssignmentForm
)


@login_required
@competition_management_permission_required
def participants_list(request, competition_id):
    """
    Affiche la liste des participants Ã  une compétition avec options de filtrage.
    """
    # Récupérer la compétition
    competition = get_object_or_404(Competition, pk=competition_id)
    
    # Récupérer les inscriptions - afficher toutes les inscriptions de la compétition
    # Inclure toutes les inscriptions, qu'elles aient is_competitor=True ou False
    # Cela permet d'afficher tous les participants inscrits
    registrations = CompetitionRegistration.objects.filter(
        competition=competition
    ).select_related('practitioner', 'practitioner__organization')
    
    # Debug: logger le nombre d'inscriptions trouvées
    logger = logging.getLogger(__name__)
    total_count = registrations.count()
    logger.info(f"Competition {competition_id}: Found {total_count} total registrations")
    
    # Filtres
    status = request.GET.get('status')
    club_id = request.GET.get('club')
    category_id = request.GET.get('category')
    search_query = request.GET.get('q')
    
    # Appliquer les filtres
    if status:
        registrations = registrations.filter(status=status)
    
    if club_id:
        # Filtrer par organisation via le club
        club = Club.objects.filter(id=club_id).first()
        if club:
            registrations = registrations.filter(practitioner__organization=club.organization)
    
    if category_id:
        registrations = registrations.filter(categories__id=category_id)
    
    if search_query:
        registrations = registrations.filter(
            Q(practitioner__first_name__icontains=search_query) | 
            Q(practitioner__last_name__icontains=search_query) |
            Q(practitioner__organization__name__icontains=search_query)
        )
    
    # Récupérer les clubs et catégories pour les filtres
    # Obtenir les organisations des pratiquants inscrits à cette compétition
    # Utiliser toutes les inscriptions pour obtenir les organisations
    all_registrations = CompetitionRegistration.objects.filter(competition=competition)
    organization_ids = all_registrations.values_list('practitioner__organization_id', flat=True).distinct()
    
    # Obtenir les clubs associés à ces organisations
    clubs = Club.objects.filter(
        organization_id__in=organization_ids
    ).distinct()
    
    categories = CompetitionCategory.objects.filter(
        competition=competition
    ).order_by('name')
    
    # Pagination - ordre par nom et prénom
    registrations_ordered = registrations.order_by(
        'practitioner__last_name', 'practitioner__first_name'
    )
    paginator = Paginator(registrations_ordered, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques pour le template - utiliser toutes les inscriptions
    stats_registrations = CompetitionRegistration.objects.filter(competition=competition)
    
    stats = {
        'total_participants': stats_registrations.count(),
        'approved_participants': stats_registrations.filter(status='approved').count(),
        'pending_participants': stats_registrations.filter(status='pending').count(),
        'rejected_participants': stats_registrations.filter(status='rejected').count(),
    }
    
    # Créer un mapping organisation -> club pour le template
    org_to_club = {}
    for club in clubs:
        if club.organization:
            org_to_club[club.organization.id] = club.id
    
    # Debug: compter les inscriptions avant et après filtres
    debug_info = {
        'total_before_filters': CompetitionRegistration.objects.filter(competition=competition).count(),
        'total_after_filters': registrations.count(),
        'page_obj_count': page_obj.object_list.count() if hasattr(page_obj, 'object_list') else 0,
    }
    logger.info(f"Competition {competition_id} debug: {debug_info}")
    
    context = {
        'competition': competition,
        'registrations': page_obj,  # Le template utilise 'registrations'
        'page_obj': page_obj,  # Pour la pagination
        'clubs': clubs,
        'categories': categories,
        'stats': stats,
        'org_to_club': org_to_club,  # Mapping organisation -> club
        'status_filter': status,
        'club_filter': club_id,
        'category_filter': category_id,
        'search_query': search_query,
        'pending_count': registrations.filter(status='pending').count(),
        'approved_count': registrations.filter(status='approved').count(),
        'rejected_count': registrations.filter(status='rejected').count(),
        'debug_info': debug_info,  # Pour le débogage
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
        competition=competition
        # Supprimé is_competitor=True pour permettre l'accès à toutes les inscriptions
    )
    
    if request.method == 'POST':
        # Vérifier si c'est une demande de suppression de catégorie
        if 'remove_category' in request.POST:
            category_id = request.POST.get('remove_category')
            try:
                category = CompetitionCategory.objects.get(id=category_id, competition=competition)
                registration.categories.remove(category)
                messages.success(request, _("La catégorie {} a été retirée avec succès.").format(category.name))
            except CompetitionCategory.DoesNotExist:
                messages.error(request, _("Catégorie non trouvée."))
            return redirect('competitions:management:participant_detail', 
                          competition_id=competition_id, 
                          registration_id=registration_id)
        
        # Vérifier si c'est une demande d'ajout de catégorie
        if 'add_category' in request.POST:
            category_id = request.POST.get('add_category')
            try:
                category = CompetitionCategory.objects.get(id=category_id, competition=competition)
                registration.categories.add(category)
                messages.success(request, _("La catégorie {} a été ajoutée avec succès.").format(category.name))
            except CompetitionCategory.DoesNotExist:
                messages.error(request, _("Catégorie non trouvée."))
            return redirect('competitions:management:participant_detail', 
                          competition_id=competition_id, 
                          registration_id=registration_id)
        
        # Vérifier si c'est une mise à jour des catégories via le formulaire select multiple
        if 'categories' in request.POST:
            category_ids = request.POST.getlist('categories')
            try:
                category_ids = [int(cid) for cid in category_ids]
                categories = CompetitionCategory.objects.filter(
                    id__in=category_ids,
                    competition=competition
                )
                registration.categories.set(categories)
                messages.success(request, _("Les catégories ont été mises à jour avec succès."))
            except (ValueError, TypeError):
                messages.error(request, _("Catégories invalides."))
            return redirect('competitions:management:participant_detail', 
                          competition_id=competition_id, 
                          registration_id=registration_id)
        
        # Sinon, traiter le formulaire d'inscription standard
        form = CompetitionRegistrationForm(request.POST, instance=registration)
        if form.is_valid():
            form.save()
            messages.success(request, _("L'inscription a été mise à jour avec succès."))
            return redirect('competitions:management:participants', competition_id=competition_id)
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
    Met Ã  jour le statut d'une inscription (approuver/rejeter).
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
    
    # Mettre Ã  jour le statut
    registration.status = status
    
    # Ajouter une note si fournie
    note = request.POST.get('note')
    if note:
        if registration.notes:
            registration.notes += f"\n{note}"
        else:
            registration.notes = note
    
    registration.save()
    
    messages.success(request, _("Le statut de l'inscription a été mis Ã  jour."))
    
    # Rediriger vers la liste ou le détail selon le paramètre
    if request.POST.get('redirect_to_list'):
        return redirect('competitions:management:participants', competition_id=competition_id)
    
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
        # Vérifier si c'est une demande de suppression de catégorie
        if 'remove_category' in request.POST:
            category_id = request.POST.get('remove_category')
            try:
                category = CompetitionCategory.objects.get(id=category_id, competition=competition)
                registration.categories.remove(category)
                messages.success(request, _("La catégorie {} a été retirée avec succès.").format(category.name))
            except CompetitionCategory.DoesNotExist:
                messages.error(request, _("Catégorie non trouvée."))
            return redirect('competitions:management:participant_detail', 
                          competition_id=competition_id, 
                          registration_id=registration_id)
        
        # Vérifier si c'est une demande d'ajout de catégorie
        if 'add_category' in request.POST:
            category_id = request.POST.get('add_category')
            try:
                category = CompetitionCategory.objects.get(id=category_id, competition=competition)
                registration.categories.add(category)
                messages.success(request, _("La catégorie {} a été ajoutée avec succès.").format(category.name))
            except CompetitionCategory.DoesNotExist:
                messages.error(request, _("Catégorie non trouvée."))
            return redirect('competitions:management:participant_detail', 
                          competition_id=competition_id, 
                          registration_id=registration_id)
        
        # Vérifier si c'est une mise à jour des catégories via le formulaire select multiple
        if 'categories' in request.POST:
            category_ids = request.POST.getlist('categories')
            try:
                category_ids = [int(cid) for cid in category_ids]
                categories = CompetitionCategory.objects.filter(
                    id__in=category_ids,
                    competition=competition
                )
                registration.categories.set(categories)
                messages.success(request, _("Les catégories ont été mises à jour avec succès."))
            except (ValueError, TypeError):
                messages.error(request, _("Catégories invalides."))
            return redirect('competitions:management:participant_detail', 
                          competition_id=competition_id, 
                          registration_id=registration_id)
        
        # Sinon, traiter le formulaire d'inscription standard
        form = CompetitionRegistrationForm(request.POST, instance=registration)
        if form.is_valid():
            form.save()
            messages.success(request, _("L'inscription a été mise à jour avec succès."))
            return redirect('competitions:management:participants', competition_id=competition_id)
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
    Permet d'assigner plusieurs participants Ã  des catégories.
    """
    # Récupérer la compétition
    competition = get_object_or_404(Competition, pk=competition_id)
    
    if request.method == 'POST':
        # Vérifier si c'est une demande de suppression de catégorie
        if 'remove_category' in request.POST:
            category_id = request.POST.get('remove_category')
            try:
                category = CompetitionCategory.objects.get(id=category_id, competition=competition)
                registration.categories.remove(category)
                messages.success(request, _("La catégorie {} a été retirée avec succès.").format(category.name))
            except CompetitionCategory.DoesNotExist:
                messages.error(request, _("Catégorie non trouvée."))
            return redirect('competitions:management:participant_detail', 
                          competition_id=competition_id, 
                          registration_id=registration_id)
        
        # Vérifier si c'est une demande d'ajout de catégorie
        if 'add_category' in request.POST:
            category_id = request.POST.get('add_category')
            try:
                category = CompetitionCategory.objects.get(id=category_id, competition=competition)
                registration.categories.add(category)
                messages.success(request, _("La catégorie {} a été ajoutée avec succès.").format(category.name))
            except CompetitionCategory.DoesNotExist:
                messages.error(request, _("Catégorie non trouvée."))
            return redirect('competitions:management:participant_detail', 
                          competition_id=competition_id, 
                          registration_id=registration_id)
        
        # Vérifier si c'est une mise à jour des catégories via le formulaire select multiple
        if 'categories' in request.POST:
            category_ids = request.POST.getlist('categories')
            try:
                category_ids = [int(cid) for cid in category_ids]
                categories = CompetitionCategory.objects.filter(
                    id__in=category_ids,
                    competition=competition
                )
                registration.categories.set(categories)
                messages.success(request, _("Les catégories ont été mises à jour avec succès."))
            except (ValueError, TypeError):
                messages.error(request, _("Catégories invalides."))
            return redirect('competitions:management:participant_detail', 
                          competition_id=competition_id, 
                          registration_id=registration_id)
        
        # Sinon, traiter le formulaire d'inscription standard
        form = CompetitionRegistrationForm(request.POST, instance=registration)
        if form.is_valid():
            form.save()
            messages.success(request, _("L'inscription a été mise à jour avec succès."))
            return redirect('competitions:management:participants', competition_id=competition_id)
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
    Recherche de participants pour les requÃªtes AJAX.
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
    ).select_related('practitioner', 'practitioner__organization').filter(
        Q(practitioner__first_name__icontains=search_query) | 
        Q(practitioner__last_name__icontains=search_query)
    )[:10]
    
    results = []
    for registration in registrations:
        p = registration.practitioner
        results.append({
            'id': registration.id,
            'name': f"{p.first_name} {p.last_name}",
            'club': p.organization.name if p.organization else "",
            'club_id': None,  # Pas d'ID direct, utiliser organisation
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
        practitioner__organization=club.organization
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
    ).select_related('practitioner', 'practitioner__organization')
    
    # Appliquer les filtres
    if status:
        registrations = registrations.filter(status=status)
    
    if club_id:
        # Filtrer par organisation via le club
        club = Club.objects.filter(id=club_id).first()
        if club:
            registrations = registrations.filter(practitioner__organization=club.organization)
    
    if category_id:
        registrations = registrations.filter(categories__id=category_id)
    
    # Créer la réponse HTTP avec l'en-tÃªte CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{competition.title}_participants.csv"'
    
    # Ã‰crire le fichier CSV
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
            p.organization.name if p.organization else "",
            p.grade,
            categories,
            reg.get_status_display(),
            reg.notes
        ])
    
    return response


@login_required
@competition_management_permission_required
@require_POST
def approve_participant(request, competition_id, registration_id):
    """
    Approuve une inscription de participant.
    """
    competition = get_object_or_404(Competition, pk=competition_id)
    registration = get_object_or_404(
        CompetitionRegistration,
        pk=registration_id,
        competition=competition
    )
    
    registration.status = 'approved'
    registration.save()
    
    messages.success(request, _("L'inscription a été approuvée avec succès."))
    return redirect('competitions:management:participants', competition_id=competition_id)


@login_required
@competition_management_permission_required
@require_POST
def reject_participant(request, competition_id, registration_id):
    """
    Rejette une inscription de participant.
    """
    competition = get_object_or_404(Competition, pk=competition_id)
    registration = get_object_or_404(
        CompetitionRegistration,
        pk=registration_id,
        competition=competition
    )
    
    reject_reason = request.POST.get('reject_reason', '')
    registration.status = 'rejected'
    
    if reject_reason:
        if registration.notes:
            registration.notes += f"\nRejet: {reject_reason}"
        else:
            registration.notes = f"Rejet: {reject_reason}"
    
    registration.save()
    
    messages.success(request, _("L'inscription a été rejetée."))
    return redirect('competitions:management:participants', competition_id=competition_id)


@login_required
@competition_management_permission_required
@require_POST
def delete_participant(request, competition_id, registration_id):
    """
    Supprime une inscription de participant.
    """
    competition = get_object_or_404(Competition, pk=competition_id)
    registration = get_object_or_404(
        CompetitionRegistration,
        pk=registration_id,
        competition=competition
    )
    
    practitioner_name = registration.practitioner.full_name
    registration.delete()
    
    messages.success(request, _("L'inscription de {} a été supprimée.").format(practitioner_name))
    return redirect('competitions:management:participants', competition_id=competition_id)


@login_required
@competition_management_permission_required
def assign_categories(request, competition_id, registration_id):
    """
    Attribue des catégories à un participant.
    Accepte GET et POST. En GET, redirige vers la liste des participants.
    """
    competition = get_object_or_404(Competition, pk=competition_id)
    registration = get_object_or_404(
        CompetitionRegistration,
        pk=registration_id,
        competition=competition
        # Supprimé is_competitor=True pour permettre l'assignation à toutes les inscriptions
    )
    
    # Si GET, afficher une page avec le formulaire pour assigner les catégories
    if request.method != 'POST':
        # Récupérer toutes les catégories de la compétition
        all_categories = CompetitionCategory.objects.filter(
            competition=competition
        ).order_by('name')
        
        # Récupérer les catégories déjà assignées
        assigned_categories = registration.categories.all()
        
        context = {
            'competition': competition,
            'registration': registration,
            'categories': all_categories,
            'assigned_categories': assigned_categories,
        }
        
        return render(request, 'competitions/management/assign_categories.html', context)
    
    # Récupérer les catégories sélectionnées
    category_ids = request.POST.getlist('categories[]')
    
    # Convertir en entiers
    try:
        category_ids = [int(cid) for cid in category_ids]
    except (ValueError, TypeError):
        messages.error(request, _("Catégories invalides."))
        return redirect('competitions:management:participants', competition_id=competition_id)
    
    # Vérifier que les catégories appartiennent à la compétition
    categories = CompetitionCategory.objects.filter(
        id__in=category_ids,
        competition=competition
    )
    
    # Mettre à jour les catégories du participant
    registration.categories.set(categories)
    
    messages.success(request, _("Les catégories ont été mises à jour avec succès."))
    return redirect('competitions:management:participants', competition_id=competition_id)


@login_required
@require_POST
def bulk_action_participants(request, competition_id):
    """Approuver ou rejeter plusieurs inscriptions en une fois."""
    competition = get_object_or_404(Competition, pk=competition_id)
    action = request.POST.get('action')
    ids = request.POST.getlist('registration_ids')

    if not ids:
        return JsonResponse({'success': False, 'error': 'Aucune inscription sélectionnée'})

    registrations = CompetitionRegistration.objects.filter(
        pk__in=ids,
        competition=competition
    )

    if action == 'approve':
        count = registrations.update(status='approved')
        return JsonResponse({'success': True, 'message': f'{count} inscription(s) approuvée(s)'})
    elif action == 'reject':
        count = registrations.update(status='rejected')
        return JsonResponse({'success': True, 'message': f'{count} inscription(s) rejetée(s)'})
    else:
        return JsonResponse({'success': False, 'error': 'Action inconnue'})

