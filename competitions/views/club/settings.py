from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

from competitions.models import Club, Discipline, Federation
from competitions.models.club_requests import AffiliationRequest
from competitions.utils.decorators import club_required
from ...forms.club import ClubDisciplineForm

@login_required
@club_required
def manage_club_disciplines(request, club_id=None):
    """Vue pour gérer les disciplines du club."""
    club = request.club
    if club_id and club_id != club.id and request.user.is_staff:
        club = get_object_or_404(Club, id=club_id)
    
    if request.method == 'POST':
        form = ClubDisciplineForm(request.POST, instance=club)
        if form.is_valid():
            # Enregistrer le formulaire sans commit pour modifier les relations M2M
            club = form.save(commit=False)
            
            # Enregistrer d'abord l'instance principale
            club.save()
            
            # Enregistrer les relations M2M
            form.save_m2m()
            
            messages.success(request, _("Les disciplines du club ont été mises à jour avec succès."))
            return redirect('competitions:club:dashboard')
    else:
        form = ClubDisciplineForm(instance=club)
    
    return render(request, 'competitions/club/manage_disciplines.html', {
        'club': club,
        'form': form,
        'title': _("Gérer les disciplines"),
    })


@login_required
@club_required
def join_federation(request, club_id=None):
    """Vue pour rechercher et rejoindre une fédération."""
    club = request.club
    if club_id and club_id != club.id and request.user.is_staff:
        club = get_object_or_404(Club, id=club_id)
    
    if request.method == 'POST':
        federation_id = request.POST.get('federation')
        if federation_id:
            federation = get_object_or_404(Federation, id=federation_id)
            
            # Vérifier si une demande est déjà en cours
            existing_request = AffiliationRequest.objects.filter(
                club=club,
                federation=federation,
                status='pending'
            ).exists()
            
            if existing_request:
                messages.warning(request, _("Une demande d'affiliation à cette fédération est déjà en cours."))
            else:
                # Créer une demande d'affiliation
                AffiliationRequest.objects.create(
                    club=club,
                    federation=federation,
                    status='pending'
                )
                messages.success(request, _(f"Votre demande d'affiliation à {federation.name} a été envoyée."))
            
            return redirect('competitions:club:dashboard')
    
    # Recherche de fédérations
    search_query = request.GET.get('q', '')
    federations = Federation.objects.filter(is_active=True)
    
    if search_query:
        federations = federations.filter(
            Q(name__icontains=search_query) | 
            Q(country__icontains=search_query) |
            Q(city__icontains=search_query)
        )
    
    # Filtrer par discipline si le club a une discipline principale
    if club.main_discipline:
        recommended_federations = federations.filter(
            Q(disciplines=club.main_discipline) |
            Q(disciplines__in=club.disciplines.all())
        ).distinct()
    else:
        recommended_federations = federations.none()
    
    return render(request, 'competitions/club/join_federation.html', {
        'club': club,
        'federations': federations,
        'recommended_federations': recommended_federations,
        'search_query': search_query,
        'title': _("Rejoindre une fédération"),
    })


@login_required
@club_required
def manage_requests(request, club_id=None):
    """Vue pour gérer et suivre les demandes du club."""
    club = request.club
    if club_id and club_id != club.id and request.user.is_staff:
        club = get_object_or_404(Club, id=club_id)
    
    # Récupérer les demandes d'affiliation
    affiliation_requests = AffiliationRequest.objects.filter(club=club).order_by('-created_at')
    
    # Actions sur les demandes
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        action = request.POST.get('action')
        
        if request_id and action:
            aff_request = get_object_or_404(AffiliationRequest, id=request_id, club=club)
            
            if action == 'cancel' and aff_request.status == 'pending':
                aff_request.status = 'cancelled'
                aff_request.save()
                messages.success(request, _("La demande a été annulée."))
            
        return redirect('competitions:club:manage_requests')
    
    return render(request, 'competitions/club/manage_requests.html', {
        'club': club,
        'affiliation_requests': affiliation_requests,
        'title': _("Suivi des demandes"),
    })