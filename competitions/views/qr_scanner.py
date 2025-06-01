import json
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
from django.views.decorators.http import require_POST
from io import BytesIO
import base64

from ..utils.qr_offline import OfflineQRTokenGenerator, OfflineQRValidator, OfflineQRStorage

# Import conditionnel de qrcode
try:
    import qrcode
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("Module qrcode non installé. Installer avec: pip install qrcode[pil]")

from ..models import (
    PractitionerQRCode, 
    QRCodeScan, 
    Competition, 
    TrainingSession, 
    Event,
    Practitioner,
    Attendance
)
from ..utils.decorators import club_admin_required, club_required


@login_required
@club_required
def scan_practitioner_qr(request):
    """Interface de scan des QR codes pour les responsables de club"""
    # Vérifier si l'utilisateur est un administrateur du club
    club = request.club
    if not (club.owner == request.user or request.user.has_perm('competitions.change_club')):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour scanner les QR codes. Vous devez être administrateur du club."))
        return redirect('competitions:dashboard:index')
        
    context = {
        'page_title': _("Scanner QR Code"),
        'scan_types': QRCodeScan.SCAN_TYPE_CHOICES,
        'competitions': Competition.objects.filter(
            organizing_organization=club.organization,
            status__in=['published', 'open'],
            end_date__gte=timezone.now().date()
        ),
        'training_sessions': TrainingSession.objects.filter(
            training_slot__club=club,
            date=timezone.now().date()
        ),
        'events': Event.objects.filter(
            organization=club.organization,
            start_date__gte=timezone.now().date()
        )
    }
    return render(request, 'competitions/qr_scanner/scan.html', context)


@login_required
@require_POST
@csrf_exempt  # Temporairement pour faciliter l'AJAX
def process_qr_scan(request):
    """Traite le scan d'un QR code"""
    try:
        data = json.loads(request.body)
        qr_code_uuid = data.get('qr_code')
        scan_type = data.get('scan_type')
        
        # Trouver le QR code
        qr_code = get_object_or_404(PractitionerQRCode, code=qr_code_uuid)
        
        # Créer le scan
        scan = QRCodeScan(
            qr_code=qr_code,
            scan_type=scan_type,
            scanned_by=request.user,
            location=data.get('location', ''),
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Ajouter les références selon le type
        if scan_type == 'competition' and data.get('competition_id'):
            scan.competition_id = data.get('competition_id')
        elif scan_type == 'training' and data.get('training_session_id'):
            scan.training_session_id = data.get('training_session_id')
        elif scan_type == 'event' and data.get('event_id'):
            scan.event_id = data.get('event_id')
        
        # Valider et sauvegarder
        scan.save()
        
        # Créer l'entrée de présence si nécessaire
        if scan_type == 'attendance' and scan.training_session:
            attendance, created = Attendance.objects.get_or_create(
                session=scan.training_session,
                practitioner=qr_code.practitioner,
                defaults={'status': 'present'}
            )
            if not created:
                attendance.status = 'present'
                attendance.save()
        
        # Préparer la réponse
        response_data = {
            'success': True,
            'valid': scan.is_valid,
            'message': scan.validation_message,
            'practitioner': {
                'id': qr_code.practitioner.id,
                'name': qr_code.practitioner.full_name,
                'photo': qr_code.practitioner.photo.url if qr_code.practitioner.photo else None,
                'club': qr_code.practitioner.organization.name if qr_code.practitioner.organization else None,
                'license_number': qr_code.practitioner.license_number,
                'is_federation_validated': qr_code.is_federation_validated
            },
            'scan_count': qr_code.scan_count
        }
        
        return JsonResponse(response_data)
        
    except PractitionerQRCode.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': _("QR Code invalide")
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
def view_practitioner_qr(request, practitioner_id):
    """Affiche le QR code d'un pratiquant"""
    practitioner = get_object_or_404(Practitioner, id=practitioner_id)
    
    # Vérifier les permissions
    is_owner = practitioner.user == request.user
    is_club_admin = request.user.has_perm('competitions.view_practitioner') and \
                   practitioner.organization == request.user.club.organization
    
    if not (is_owner or is_club_admin or request.user.is_superuser):
        messages.error(request, _("Vous n'avez pas les permissions pour voir ce QR code"))
        return redirect('competitions:dashboard:index')
    
    # Obtenir ou créer le QR code
    qr_code, created = PractitionerQRCode.objects.get_or_create(practitioner=practitioner)
    
    # Générer ou récupérer le QR code hors-ligne si demandé
    offline_mode = request.GET.get('offline', 'false').lower() == 'true'
    if offline_mode and (not qr_code.qr_offline_image or not qr_code.offline_token):
        qr_code.generate_offline_token()
        qr_code.generate_offline_qr_code()
    
    context = {
        'practitioner': practitioner,
        'qr_code': qr_code,
        'page_title': _("QR Code - ") + practitioner.full_name,
        'offline_mode': offline_mode,
        'offline_token_data': qr_code.get_offline_token_data() if offline_mode else None,
    }
    
    return render(request, 'competitions/qr_scanner/view_qr.html', context)


@login_required
def qr_code_image(request, practitioner_id):
    """Génère et retourne l'image du QR code"""
    practitioner = get_object_or_404(Practitioner, id=practitioner_id)
    
    # Vérifier les permissions
    is_owner = practitioner.user == request.user
    is_club_admin = request.user.has_perm('competitions.view_practitioner') and \
                   practitioner.organization == request.user.club.organization
    
    if not (is_owner or is_club_admin or request.user.is_superuser):
        return HttpResponse(status=403)
    
    # Vérifier le type de QR code demandé (standard ou hors-ligne)
    offline = request.GET.get('offline', 'false').lower() == 'true'
    
    # Obtenir ou créer le QR code
    qr_code, created = PractitionerQRCode.objects.get_or_create(practitioner=practitioner)
    
    if offline:
        # Générer ou récupérer l'image hors-ligne
        if not qr_code.qr_offline_image:
            qr_code.generate_offline_token()
            qr_code.generate_offline_qr_code()
            
        # Retourner l'image du QR code hors-ligne
        return HttpResponse(qr_code.qr_offline_image.read(), content_type="image/png")
    else:
        # Générer l'image standard si elle n'existe pas
        if not qr_code.qr_image:
            qr_code.generate_qr_code()
            qr_code.save()
        
        # Retourner l'image du QR code standard
        return HttpResponse(qr_code.qr_image.read(), content_type="image/png")


@login_required
@club_required
def scan_history(request):
    """Historique des scans pour un club"""
    club = request.club
    
    # Vérifier si l'utilisateur est un administrateur du club
    if not (club.owner == request.user or request.user.has_perm('competitions.change_club')):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour voir l'historique des scans."))
        return redirect('competitions:dashboard:index')
    
    # Récupérer les scans du club
    scans = QRCodeScan.objects.filter(
        qr_code__practitioner__organization=club.organization
    ).select_related(
        'qr_code__practitioner',
        'scanned_by',
        'competition',
        'training_session',
        'event'
    ).order_by('-scan_date')
    
    # Filtrer par type si demandé
    scan_type = request.GET.get('type')
    if scan_type:
        scans = scans.filter(scan_type=scan_type)
    
    # Filtrer par date si demandé
    date_from = request.GET.get('from')
    date_to = request.GET.get('to')
    if date_from:
        scans = scans.filter(scan_date__date__gte=date_from)
    if date_to:
        scans = scans.filter(scan_date__date__lte=date_to)
    
    context = {
        'scans': scans[:100],  # Limiter à 100 derniers scans
        'scan_types': QRCodeScan.SCAN_TYPE_CHOICES,
        'selected_type': scan_type,
        'date_from': date_from,
        'date_to': date_to,
        'page_title': _("Historique des scans QR")
    }
    
    return render(request, 'competitions/qr_scanner/history.html', context)


@login_required
def validate_federation_qr(request, practitioner_id):
    """Valide le QR code au niveau fédération"""
    practitioner = get_object_or_404(Practitioner, id=practitioner_id)
    
    # Vérifier les permissions (admin fédération)
    if not request.user.has_perm('competitions.change_federation'):
        messages.error(request, _("Vous n'avez pas les permissions"))
        return redirect('competitions:dashboard:index')
    
    qr_code = get_object_or_404(PractitionerQRCode, practitioner=practitioner)
    
    if qr_code.validate_for_federation():
        messages.success(request, _("QR Code validé pour la fédération"))
    else:
        messages.error(request, _("Le club n'est pas en règle avec la fédération"))
    
    return redirect('competitions:practitioner:view_qr', practitioner_id=practitioner_id)


@login_required
def qr_code_offline_token(request, practitioner_id):
    """Génère un token pour le QR code utilisable hors-ligne"""
    practitioner = get_object_or_404(Practitioner, id=practitioner_id)
    
    # Vérifier les permissions
    is_owner = practitioner.user == request.user
    is_club_admin = request.user.has_perm('competitions.view_practitioner') and \
                   practitioner.organization == request.user.club.organization
    
    if not (is_owner or is_club_admin or request.user.is_superuser):
        return JsonResponse({"error": _("Permissions insuffisantes")}, status=403)
    
    # Obtenir le QR code
    qr_code, created = PractitionerQRCode.objects.get_or_create(practitioner=practitioner)
    
    # Générer le token hors-ligne
    club_id = practitioner.organization.id if practitioner.organization else None
    offline_token = OfflineQRTokenGenerator.generate_offline_token(
        practitioner_id=practitioner.id,
        qr_code_uuid=qr_code.code,
        federation_validated=qr_code.is_federation_validated,
        club_id=club_id
    )
    
    # Retourner le token
    return JsonResponse({
        "success": True,
        "token": offline_token,
        "practitioner_id": practitioner.id,
        "qr_uuid": str(qr_code.code),
        "expires_in_days": 7,  # Valeur en dur correspondant à TOKEN_VALIDITY_DAYS dans qr_offline.py
        "federation_validated": qr_code.is_federation_validated,
    })
    
    
@login_required
def qr_code_offline_profile(request, practitioner_id):
    """Génère et retourne les données de profil pour utilisation hors-ligne"""
    practitioner = get_object_or_404(Practitioner, id=practitioner_id)
    
    # Vérifier les permissions
    is_owner = practitioner.user == request.user
    is_club_admin = request.user.has_perm('competitions.view_practitioner') and \
                   practitioner.organization == request.user.club.organization
    
    if not (is_owner or is_club_admin or request.user.is_superuser):
        return JsonResponse({"error": _("Permissions insuffisantes")}, status=403)
    
    # Obtenir le QR code
    qr_code, created = PractitionerQRCode.objects.get_or_create(practitioner=practitioner)
    
    # Format de réponse (JSON ou HTML)
    response_format = request.GET.get('format', 'json')
    
    # Générer ou récupérer les données de profil hors-ligne
    profile_data = qr_code.get_offline_profile_data()
    
    if response_format == 'html':
        # Rendre la page HTML du profil hors-ligne
        context = {
            'practitioner': practitioner,
            'qr_code': qr_code,
            'profile_data': profile_data,
            'page_title': _("Profil hors-ligne - ") + practitioner.full_name,
        }
        return render(request, 'competitions/qr_scanner/offline_profile.html', context)
    else:
        # Retourner les données en JSON
        return JsonResponse({
            "success": True,
            "profile_token": profile_data.get("token"),
            "generated_at": profile_data.get("generated_at"),
            "qr_image_url": qr_code.offline_profile_qr_image.url if qr_code.offline_profile_qr_image else None,
            "expires_in_days": 30,  # PROFILE_VALIDITY_DAYS dans qr_offline.py
        })


@login_required
def verify_offline_profile(request):
    """Vérifie un token de profil hors-ligne (pour test)"""
    if request.method != "POST":
        return JsonResponse({"error": "Méthode non autorisée"}, status=405)
    
    try:
        from ..utils.qr_offline import OfflineProfileGenerator
        
        data = json.loads(request.body)
        token = data.get("token")
        
        if not token:
            return JsonResponse({"error": "Token manquant"}, status=400)
        
        # Vérifier le token
        profile_data = OfflineProfileGenerator.verify_offline_profile(token)
        
        if not profile_data.get("valid", False):
            return JsonResponse({
                "valid": False,
                "reason": profile_data.get("reason", "unknown")
            })
        
        # Token valide, retourner les informations
        return JsonResponse({
            "valid": True,
            "profile": profile_data
        })
        
    except (ValueError, json.JSONDecodeError):
        return JsonResponse({"error": "Format de requête invalide"}, status=400)
    

def view_offline_profile_public(request, token=None):
    """
    Affiche le profil d'un pratiquant à partir d'un token hors-ligne.
    Cette vue est accessible sans authentification.
    """
    from ..utils.qr_offline import OfflineProfileGenerator
    
    # Si le token n'est pas fourni, afficher le formulaire de saisie
    if not token and request.method == "GET":
        return render(request, 'competitions/qr_scanner/offline_profile_entry.html', {
            'page_title': _("Consulter un profil hors-ligne")
        })
    
    # Si le token est soumis via formulaire POST
    if not token and request.method == "POST":
        token = request.POST.get('token', '')
    
    # Vérifier le token
    profile_data = OfflineProfileGenerator.verify_offline_profile(token)
    
    # Si le token est invalide
    if not profile_data.get("valid", False):
        error_message = _("Token de profil invalide ou expiré")
        if profile_data.get("reason") == "token_expired":
            error_message = _("Ce profil a expiré. Veuillez scanner un QR code récent.")
        
        context = {
            'page_title': _("Erreur - Profil invalide"),
            'error': error_message,
            'reason': profile_data.get("reason", "unknown")
        }
        return render(request, 'competitions/qr_scanner/offline_profile_error.html', context)
    
    # Afficher le profil
    context = {
        'page_title': _("Profil - ") + f"{profile_data.get('first_name')} {profile_data.get('last_name')}",
        'profile': profile_data,
        'token': token,
        'is_offline': True
    }
    
    return render(request, 'competitions/qr_scanner/offline_profile_view.html', context)


@login_required
def verify_offline_token(request):
    """Vérifie un token hors-ligne (pour test)"""
    if request.method != "POST":
        return JsonResponse({"error": "Méthode non autorisée"}, status=405)
    
    try:
        data = json.loads(request.body)
        token = data.get("token")
        
        if not token:
            return JsonResponse({"error": "Token manquant"}, status=400)
        
        # Vérifier le token
        token_data = OfflineQRTokenGenerator.verify_offline_token(token)
        
        if not token_data.get("valid", False):
            return JsonResponse({
                "valid": False,
                "reason": token_data.get("reason", "unknown")
            })
        
        # Token valide, retourner les informations
        return JsonResponse({
            "valid": True,
            "practitioner_id": token_data.get("prac_id"),
            "qr_uuid": token_data.get("qr_uuid"),
            "federation_validated": token_data.get("fed_val"),
            "club_id": token_data.get("club_id"),
            "expires_at": token_data.get("exp"),
        })
        
    except (ValueError, json.JSONDecodeError):
        return JsonResponse({"error": "Format de requête invalide"}, status=400)


@csrf_exempt
@require_POST
def process_offline_scan(request):
    """Traite un scan QR en mode hors-ligne"""
    try:
        data = json.loads(request.body)
        token = data.get("token")
        scan_type = data.get("scan_type")
        event_id = data.get("event_id")
        
        if not token or not scan_type:
            return JsonResponse({"error": "Paramètres manquants"}, status=400)
        
        # Vérifier le token
        token_data = OfflineQRTokenGenerator.verify_offline_token(token)
        
        # Valider le scan
        validation_result = OfflineQRValidator.validate_qr_scan(
            token_data=token_data,
            scan_type=scan_type,
            event_id=event_id
        )
        
        if not validation_result.get("valid", False):
            return JsonResponse({
                "success": False,
                "message": validation_result.get("message"),
                "reason": validation_result.get("reason")
            })
        
        # Préparer les données pour stockage local
        storage_data = OfflineQRStorage.store_offline_scan(validation_result)
        
        # Enrichir avec des données de praticien (simulées en mode hors-ligne)
        # En production, ces données seraient stockées localement ou incluses dans le token
        practitioner_data = {
            "id": token_data.get("prac_id"),
            "name": f"Pratiquant #{token_data.get('prac_id')}",  # Nom simulé
            "photo": None,
            "club": None,
            "license_number": "Vérifié hors-ligne",
            "is_federation_validated": token_data.get("fed_val", False)
        }
        
        return JsonResponse({
            "success": True,
            "valid": True,
            "message": validation_result.get("message"),
            "offline": True,
            "scan_data": storage_data,
            "practitioner": practitioner_data
        })
        
    except (ValueError, json.JSONDecodeError):
        return JsonResponse({"error": "Format de requête invalide"}, status=400)


@login_required
@require_POST
def sync_offline_scans(request):
    """Synchronise les scans effectués hors-ligne avec le serveur"""
    try:
        data = json.loads(request.body)
        offline_scans = data.get("scans", [])
        
        if not offline_scans:
            return JsonResponse({
                "success": True,
                "message": "Aucun scan à synchroniser",
                "synced": 0,
                "ignored": 0
            })
        
        # Fusionner les scans
        created, ignored = OfflineQRStorage.merge_offline_scans(offline_scans)
        
        return JsonResponse({
            "success": True,
            "message": f"{created} scans synchronisés, {ignored} ignorés",
            "synced": created,
            "ignored": ignored
        })
        
    except (ValueError, json.JSONDecodeError):
        return JsonResponse({"error": "Format de requête invalide"}, status=400)
    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=500)


@login_required
def generate_event_check_in_qr(request, event_id):
    """Génère un QR code pour le check-in d'un événement"""
    event = get_object_or_404(Event, id=event_id)
    
    # Vérifier les permissions
    if not request.user.has_perm('competitions.change_event'):
        return HttpResponse(status=403)
    
    # Créer l'URL de check-in
    check_in_url = request.build_absolute_uri(
        reverse('competitions:qr:event_check_in', args=[event_id])
    )
    
    context = {
        'event': event,
        'check_in_url': check_in_url,
        'page_title': _("QR Code Check-in - ") + event.name
    }
    
    if HAS_QRCODE:
        # Générer le QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(check_in_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convertir en base64 pour l'affichage HTML
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        context['qr_code_base64'] = img_str
    else:
        context['qr_code_error'] = _("Module QR Code non installé. Installer avec: pip install qrcode[pil]")
    
    return render(request, 'competitions/qr_scanner/event_check_in_qr.html', context)