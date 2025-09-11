from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.urls import reverse

from ...models import Club
from ...models.club_qr_code import ClubQRCode
from ...services.club_qr_service import ClubQRService
from ...utils.permission_helpers import get_user_club
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

@login_required
def club_qr_dashboard(request, club_id=None):
    """Dashboard de gestion des QR codes pour un club"""
    
    # Si club_id n'est pas fourni, récupérer le club de l'utilisateur
    if club_id is None:
        user_club = get_user_club(request)
        if not user_club:
            messages.error(request, _("Aucun club associé à votre compte."))
            return redirect('competitions:dashboard:dashboard')
        club = user_club
    else:
        club = get_object_or_404(Club, id=club_id)
        # Vérifier les permissions
        user_club = get_user_club(request)
        if not user_club or user_club.id != club.id:
            messages.error(request, _("Vous n'avez pas les permissions pour accéder à ce club."))
            return redirect('competitions:dashboard:dashboard')
    
    # Récupérer ou créer les QR codes
    registration_qr = ClubQRService.get_or_create_registration_qr(club)
    activity_qr = ClubQRService.get_or_create_activity_qr(club)
    
    # Statistiques
    stats = ClubQRService.get_club_statistics(club)
    
    context = {
        'club': club,
        'registration_qr': registration_qr,
        'activity_qr': activity_qr,
        'stats': stats,
        'page_title': _("QR Codes du Club"),
    }
    
    return render(request, 'competitions/club/qr_dashboard.html', context)

@login_required
@require_POST
def regenerate_qr_code(request, club_id):
    """Régénère un QR code"""
    
    club = get_object_or_404(Club, id=club_id)
    
    # Vérifier les permissions
    user_club = get_user_club(request)
    if not user_club or user_club.id != club.id:
        return JsonResponse({'success': False, 'error': 'Permissions insuffisantes'})
    
    qr_type = request.GET.get('type')
    
    try:
        if qr_type == 'registration':
            qr_code = ClubQRService.get_or_create_registration_qr(club)
        elif qr_type == 'activity':
            qr_code = ClubQRService.get_or_create_activity_qr(club)
        else:
            return JsonResponse({'success': False, 'error': 'Type de QR code invalide'})
        
        # Régénérer le QR code
        qr_code.generate_qr_code()
        qr_code.save()
        
        return JsonResponse({
            'success': True,
            'qr_url': qr_code.qr_url,
            'qr_image': qr_code.qr_image.url if qr_code.qr_image else None,
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def qr_statistics(request, club_id):
    """Affiche les statistiques détaillées des QR codes"""
    
    club = get_object_or_404(Club, id=club_id)
    
    # Vérifier les permissions
    user_club = get_user_club(request)
    if not user_club or user_club.id != club.id:
        messages.error(request, _("Vous n'avez pas les permissions pour accéder à ce club."))
        return redirect('competitions:dashboard:index')
    
    # Statistiques détaillées
    stats = ClubQRService.get_club_statistics(club)
    
    # Récupérer tous les QR codes du club
    qr_codes = ClubQRCode.objects.filter(club=club).prefetch_related('scans')
    
    context = {
        'club': club,
        'stats': stats,
        'qr_codes': qr_codes,
        'page_title': _("Statistiques QR Codes"),
    }
    
    return render(request, 'competitions/club/qr_statistics.html', context)
