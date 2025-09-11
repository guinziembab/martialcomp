from django.core.exceptions import PermissionDenied
"""
Vues pour la gestion des QR codes et liens de parrainage.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.utils import timezone
import json
import uuid

from ..models.organization_qr_code import OrganizationQRCode, OrganizationQRCodeScan, ReferralLink, ReferralUse
from ..models import Club, Federation, CoachProfile
from ..utils.qr_generator import generate_qr_code_for_entity
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset


@login_required
def dashboard_qr_management(request):
    """
    Vue principale du tableau de bord de gestion des QR codes.
    Affiche les QR codes existants et permet d'en créer de nouveaux.
    """
    # Déterminer les entités associées Ã  l'utilisateur
    user_clubs = Club.objects.filter(owner=request.user)
    user_federations = Federation.objects.filter(owner=request.user)
    user_coach_profiles = CoachProfile.objects.filter(practitioner__user=request.user)
    
    # Récupérer les QR codes associés
    club_qr_codes = OrganizationQRCode.objects.filter(club__in=user_clubs) if user_clubs.exists() else []
    federation_qr_codes = OrganizationQRCode.objects.filter(federation__in=user_federations) if user_federations.exists() else []
    coach_qr_codes = OrganizationQRCode.objects.filter(coach_profile__in=user_coach_profiles) if user_coach_profiles.exists() else []
    
    # Récupérer les liens de parrainage
    referral_links = ReferralLink.objects.filter(referrer=request.user)
    
    context = {
        'user_clubs': user_clubs,
        'user_federations': user_federations,
        'user_coach_profiles': user_coach_profiles,
        'club_qr_codes': club_qr_codes,
        'federation_qr_codes': federation_qr_codes,
        'coach_qr_codes': coach_qr_codes,
        'referral_links': referral_links,
        'page_title': _("Gestion des QR codes et parrainages")
    }
    
    return render(request, 'competitions/qr_management/dashboard.html', context)


@login_required
def create_organization_qr_code(request):
    """
    Crée un nouveau QR code pour une organisation (club, fédération ou coach).
    """
    if request.method == 'POST':
        entity_type = request.POST.get('entity_type')
        entity_id = request.POST.get('entity_id')
        purpose = request.POST.get('purpose', 'both')
        custom_title = request.POST.get('custom_title', '')
        custom_message = request.POST.get('custom_message', '')
        
        # Vérifier les permissions
        if entity_type == 'club':
            entity = get_object_or_404(Club, id=entity_id)
            if entity.owner != request.user:
                messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
                return redirect('competitions:qr_management:dashboard')
        elif entity_type == 'federation':
            entity = get_object_or_404(Federation, id=entity_id)
            if entity.owner != request.user:
                messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
                return redirect('competitions:qr_management:dashboard')
        elif entity_type == 'coach':
            entity = get_object_or_404(CoachProfile, id=entity_id)
            if entity.user != request.user:
                messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
                return redirect('competitions:qr_management:dashboard')
        else:
            messages.error(request, _("Type d'entité non valide."))
            return redirect('competitions:qr_management:dashboard')
        
        # Créer le QR code
        qr_code = OrganizationQRCode(
            purpose=purpose,
            custom_title=custom_title,
            custom_message=custom_message,
            code=str(uuid.uuid4())
        )
        
        # Associer Ã  l'entité appropriée
        if entity_type == 'club':
            qr_code.club = entity
        elif entity_type == 'federation':
            qr_code.federation = entity
        elif entity_type == 'coach':
            qr_code.coach_profile = entity
        
        qr_code.save()
        
        messages.success(request, _("QR code créé avec succès !"))
        return redirect('competitions:qr_management:view_qr_code', qr_code_id=qr_code.id)
    
    # Si la méthode est GET, rediriger vers le tableau de bord
    return redirect('competitions:qr_management:dashboard')


@login_required
def view_qr_code(request, qr_code_id):
    """
    Affiche les détails d'un QR code et permet de le télécharger.
    """
    qr_code = get_object_or_404(OrganizationQRCode, id=qr_code_id)
    
    # Vérifier les permissions
    entity = qr_code.get_entity()
    if not entity:
        messages.error(request, _("QR code invalide."))
        return redirect('competitions:qr_management:dashboard')
    
    has_permission = False
    if qr_code.club and qr_code.club.owner == request.user:
        has_permission = True
    elif qr_code.federation and qr_code.federation.owner == request.user:
        has_permission = True
    elif qr_code.coach_profile and qr_code.coach_profile.user == request.user:
        has_permission = True
    
    if not has_permission:
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour voir ce QR code."))
        return redirect('competitions:qr_management:dashboard')
    
    # Récupérer les statistiques de scan
    scans = qr_code.scans.all()
    recent_scans = scans.order_by('-scanned_at')[:10]
    
    # Calculer les taux de conversion
    conversion_rate = 0
    if qr_code.scan_count > 0:
        conversion_rate = (qr_code.conversion_count / qr_code.scan_count) * 100
    
    context = {
        'qr_code': qr_code,
        'entity': entity,
        'entity_type': qr_code.get_entity_type(),
        'scans': scans,
        'recent_scans': recent_scans,
        'scan_count': qr_code.scan_count,
        'conversion_count': qr_code.conversion_count,
        'conversion_rate': conversion_rate,
        'page_title': _("Détails du QR code")
    }
    
    return render(request, 'competitions/qr_management/view_qr_code.html', context)


@login_required
@require_POST
def regenerate_qr_code(request, qr_code_id):
    """
    Régénère l'image du QR code.
    """
    qr_code = get_object_or_404(OrganizationQRCode, id=qr_code_id)
    
    # Vérifier les permissions
    entity = qr_code.get_entity()
    if not entity:
        return JsonResponse({'success': False, 'error': _("QR code invalide.")})
    
    has_permission = False
    if qr_code.club and qr_code.club.owner == request.user:
        has_permission = True
    elif qr_code.federation and qr_code.federation.owner == request.user:
        has_permission = True
    elif qr_code.coach_profile and qr_code.coach_profile.user == request.user:
        has_permission = True
    
    if not has_permission:
        return JsonResponse({'success': False, 'error': _("Permissions insuffisantes.")})
    
    # Régénérer le QR code
    qr_code.generate_qr_code()
    
    return JsonResponse({
        'success': True,
        'message': _("QR code régénéré avec succès."),
        'qr_image_url': qr_code.qr_image.url if qr_code.qr_image else None,
        'url': qr_code.url
    })


@login_required
@require_POST
def deactivate_qr_code(request, qr_code_id):
    """
    Désactive un QR code.
    """
    qr_code = get_object_or_404(OrganizationQRCode, id=qr_code_id)
    
    # Vérifier les permissions
    entity = qr_code.get_entity()
    if not entity:
        return JsonResponse({'success': False, 'error': _("QR code invalide.")})
    
    has_permission = False
    if qr_code.club and qr_code.club.owner == request.user:
        has_permission = True
    elif qr_code.federation and qr_code.federation.owner == request.user:
        has_permission = True
    elif qr_code.coach_profile and qr_code.coach_profile.user == request.user:
        has_permission = True
    
    if not has_permission:
        return JsonResponse({'success': False, 'error': _("Permissions insuffisantes.")})
    
    # Désactiver le QR code
    qr_code.deactivate()
    
    return JsonResponse({
        'success': True,
        'message': _("QR code désactivé avec succès."),
        'is_active': qr_code.is_active
    })


@login_required
@require_POST
def reactivate_qr_code(request, qr_code_id):
    """
    Réactive un QR code.
    """
    qr_code = get_object_or_404(OrganizationQRCode, id=qr_code_id)
    
    # Vérifier les permissions
    entity = qr_code.get_entity()
    if not entity:
        return JsonResponse({'success': False, 'error': _("QR code invalide.")})
    
    has_permission = False
    if qr_code.club and qr_code.club.owner == request.user:
        has_permission = True
    elif qr_code.federation and qr_code.federation.owner == request.user:
        has_permission = True
    elif qr_code.coach_profile and qr_code.coach_profile.user == request.user:
        has_permission = True
    
    if not has_permission:
        return JsonResponse({'success': False, 'error': _("Permissions insuffisantes.")})
    
    # Réactiver le QR code
    qr_code.reactivate()
    
    return JsonResponse({
        'success': True,
        'message': _("QR code réactivé avec succès."),
        'is_active': qr_code.is_active
    })


@login_required
def download_qr_code(request, qr_code_id):
    """
    Télécharge l'image du QR code.
    """
    qr_code = get_object_or_404(OrganizationQRCode, id=qr_code_id)
    
    # Vérifier les permissions
    entity = qr_code.get_entity()
    if not entity:
        messages.error(request, _("QR code invalide."))
        return redirect('competitions:qr_management:dashboard')
    
    has_permission = False
    if qr_code.club and qr_code.club.owner == request.user:
        has_permission = True
    elif qr_code.federation and qr_code.federation.owner == request.user:
        has_permission = True
    elif qr_code.coach_profile and qr_code.coach_profile.user == request.user:
        has_permission = True
    
    if not has_permission:
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour télécharger ce QR code."))
        return redirect('competitions:qr_management:dashboard')
    
    # Vérifier que l'image existe
    if not qr_code.qr_image:
        messages.error(request, _("L'image du QR code n'existe pas."))
        return redirect('competitions:qr_management:view_qr_code', qr_code_id=qr_code.id)
    
    # Lire l'image
    try:
        from django.core.files.storage import default_storage
        with default_storage.open(qr_code.qr_image.name, 'rb') as f:
            response = HttpResponse(f.read(), content_type='image/png')
            response['Content-Disposition'] = f'attachment; filename="{qr_code.code}.png"'
            return response
    except Exception as e:
        messages.error(request, _("Erreur lors du téléchargement: {}").format(str(e)))
        return redirect('competitions:qr_management:view_qr_code', qr_code_id=qr_code.id)


@login_required
def create_referral_link(request):
    """
    Crée un nouveau lien de parrainage.
    """
    if request.method == 'POST':
        entity_type = request.POST.get('entity_type')
        entity_id = request.POST.get('entity_id')
        discount_type = request.POST.get('discount_type')
        discount_value = request.POST.get('discount_value')
        custom_message = request.POST.get('custom_message', '')
        max_uses = request.POST.get('max_uses', 10)
        
        # Valider les données
        if not entity_type or not entity_id or not discount_type or not discount_value:
            messages.error(request, _("Tous les champs obligatoires doivent Ãªtre remplis."))
            return redirect('competitions:qr_management:dashboard')
        
        # Vérifier les permissions
        if entity_type == 'club':
            entity = get_object_or_404(Club, id=entity_id)
            if entity.owner != request.user:
                messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
                return redirect('competitions:qr_management:dashboard')
        elif entity_type == 'federation':
            entity = get_object_or_404(Federation, id=entity_id)
            if entity.owner != request.user:
                messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
                return redirect('competitions:qr_management:dashboard')
        else:
            messages.error(request, _("Type d'entité non valide."))
            return redirect('competitions:qr_management:dashboard')
        
        # Créer le lien de parrainage
        referral_link = ReferralLink(
            referrer=request.user,
            custom_message=custom_message,
            max_uses=int(max_uses) if max_uses else 10
        )
        
        # Associer Ã  l'entité appropriée
        if entity_type == 'club':
            referral_link.club = entity
        elif entity_type == 'federation':
            referral_link.federation = entity
        
        # Définir la réduction
        try:
            if discount_type == 'amount':
                referral_link.discount_amount = float(discount_value)
            elif discount_type == 'percentage':
                referral_link.discount_percentage = float(discount_value)
        except ValueError:
            messages.error(request, _("Valeur de réduction invalide."))
            return redirect('competitions:qr_management:dashboard')
        
        referral_link.save()
        
        messages.success(request, _("Lien de parrainage créé avec succès !"))
        return redirect('competitions:qr_management:view_referral_link', referral_link_id=referral_link.id)
    
    # Si la méthode est GET, rediriger vers le tableau de bord
    return redirect('competitions:qr_management:dashboard')


@login_required
def view_referral_link(request, referral_link_id):
    """
    Affiche les détails d'un lien de parrainage.
    """
    referral_link = get_object_or_404(ReferralLink, id=referral_link_id)
    
    # Vérifier les permissions
    if referral_link.referrer != request.user:
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour voir ce lien de parrainage."))
        return redirect('competitions:qr_management:dashboard')
    
    # Récupérer les utilisations du lien
    uses = referral_link.uses.all().order_by('-created_at')
    
    # Calculer les statistiques
    total_uses = uses.count()
    converted_uses = uses.filter(converted=True).count()
    completed_payments = uses.filter(payment_completed=True).count()
    
    conversion_rate = 0
    if total_uses > 0:
        conversion_rate = (converted_uses / total_uses) * 100
    
    payment_rate = 0
    if converted_uses > 0:
        payment_rate = (completed_payments / converted_uses) * 100
    
    # Générer le QR code pour le lien de parrainage
    qr_buffer = referral_link.generate_qr_code()
    if qr_buffer:
        import base64
        qr_image_base64 = base64.b64encode(qr_buffer.getvalue()).decode('utf-8')
    else:
        qr_image_base64 = None
    
    context = {
        'referral_link': referral_link,
        'uses': uses,
        'total_uses': total_uses,
        'converted_uses': converted_uses,
        'completed_payments': completed_payments,
        'conversion_rate': conversion_rate,
        'payment_rate': payment_rate,
        'qr_image_base64': qr_image_base64,
        'page_title': _("Détails du lien de parrainage"),
        'discount_info': referral_link.get_discount_info()
    }
    
    return render(request, 'competitions/qr_management/view_referral_link.html', context)


@login_required
@require_POST
def deactivate_referral_link(request, referral_link_id):
    """
    Désactive un lien de parrainage.
    """
    referral_link = get_object_or_404(ReferralLink, id=referral_link_id)
    
    # Vérifier les permissions
    if referral_link.referrer != request.user:
        return JsonResponse({'success': False, 'error': _("Permissions insuffisantes.")})
    
    # Désactiver le lien
    referral_link.is_active = False
    referral_link.save()
    
    return JsonResponse({
        'success': True,
        'message': _("Lien de parrainage désactivé avec succès."),
        'is_active': referral_link.is_active
    })


@login_required
@require_POST
def reactivate_referral_link(request, referral_link_id):
    """
    Réactive un lien de parrainage.
    """
    referral_link = get_object_or_404(ReferralLink, id=referral_link_id)
    
    # Vérifier les permissions
    if referral_link.referrer != request.user:
        return JsonResponse({'success': False, 'error': _("Permissions insuffisantes.")})
    
    # Réactiver le lien
    referral_link.is_active = True
    referral_link.save()
    
    return JsonResponse({
        'success': True,
        'message': _("Lien de parrainage réactivé avec succès."),
        'is_active': referral_link.is_active
    })


# Vue pour le scan d'un QR code
def scan_qr_code(request, qr_code):
    """
    Traite le scan d'un QR code.
    Redirige vers la page appropriée selon le type de QR code.
    """
    # Chercher le QR code dans la base de données
    qr_code_obj = get_object_or_404(OrganizationQRCode, code=qr_code)
    
    # Vérifier si le QR code est valide et actif
    if qr_code_obj.is_expired():
        return render(request, 'competitions/qr_management/scan_error.html', {
            'error': _("Ce QR code a expiré ou n'est plus valide."),
            'page_title': _("QR code expiré")
        })
    
    # Enregistrer le scan
    user = request.user if request.user.is_authenticated else None
    ip_address = request.META.get('REMOTE_ADDR')
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    scan = qr_code_obj.record_scan(
        user=user,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    # Déterminer la redirection en fonction du type et de l'objectif du QR code
    entity_type = qr_code_obj.get_entity_type()
    entity = qr_code_obj.get_entity()
    
    if not entity:
        return render(request, 'competitions/qr_management/scan_error.html', {
            'error': _("L'organisation associée Ã  ce QR code n'existe plus."),
            'page_title': _("Organisation introuvable")
        })
    
    # Construire l'URL de redirection
    if qr_code_obj.purpose == 'registration':
        url = f"/signup/{entity_type}/{entity.id}/?qr_scan={scan.id}"
    elif qr_code_obj.purpose == 'payment':
        url = f"/payment/{entity_type}/{entity.id}/?qr_scan={scan.id}"
    elif qr_code_obj.purpose == 'both':
        url = f"/signup/{entity_type}/{entity.id}/?qr_scan={scan.id}&payment=1"
    else:  # 'info'
        url = f"/{entity_type}/{entity.id}/?qr_scan={scan.id}"
    
    # Rediriger vers l'URL appropriée
    return redirect(url)
