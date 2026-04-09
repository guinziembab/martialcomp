# apps/competitions/views/dashboard/certification_management.py
"""
Vues avancées pour la gestion des certifications de la fédération.
Inclut la gestion des modèles de certificats, les demandes de certification,
et l'émission de certificats.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _, gettext
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_GET
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.conf import settings

import logging
import json
from datetime import timedelta

from ...models import (
    Federation,
    Club,
    Judge,
    JudgeCertification,
    CertificationRegistration,
    Exam,
    ExamRegistration,
    CertificateTemplate,
    IssuedCertificate,
    CertificationRequest,
    Discipline
)

logger = logging.getLogger(__name__)


def _user_can_access_federation(user, federation):
    """Vérifier si l'utilisateur peut accéder à cette fédération"""
    if user.is_superuser:
        return True
    if federation.owner == user:
        return True
    try:
        from ...models import FederationAdministrator
        if FederationAdministrator.objects.filter(federation=federation, user=user).exists():
            return True
    except ImportError:
        pass
    return False


# =============================================================================
# GESTION DES MODÈLES DE CERTIFICATS
# =============================================================================

@login_required
def certificate_templates_list(request, federation_id):
    """Liste des modèles de certificats de la fédération"""
    federation = get_object_or_404(Federation, id=federation_id)

    if not _user_can_access_federation(request.user, federation):
        messages.error(request, _("Vous n'avez pas les permissions pour accéder à cette fédération."))
        return redirect('competitions:dashboard:dashboard')

    templates = CertificateTemplate.objects.filter(
        organization=federation.organization
    ).order_by('template_type', 'name')

    # Stats par type
    stats = {
        'total': templates.count(),
        'judge': templates.filter(template_type='judge').count(),
        'grade': templates.filter(template_type='grade').count(),
        'participation': templates.filter(template_type='participation').count(),
        'achievement': templates.filter(template_type='achievement').count(),
    }

    context = {
        'federation': federation,
        'templates': templates,
        'stats': stats,
        'template_types': CertificateTemplate.TEMPLATE_TYPE_CHOICES,
    }
    return render(request, 'competitions/dashboard/certification/templates_list.html', context)


@login_required
def certificate_template_create(request, federation_id):
    """Créer un nouveau modèle de certificat"""
    federation = get_object_or_404(Federation, id=federation_id)

    if not _user_can_access_federation(request.user, federation):
        messages.error(request, _("Vous n'avez pas les permissions pour accéder à cette fédération."))
        return redirect('competitions:dashboard:dashboard')

    if request.method == 'POST':
        try:
            template = CertificateTemplate(
                organization=federation.organization,
                created_by=request.user,
                name=request.POST.get('name'),
                template_type=request.POST.get('template_type', 'judge'),
                description=request.POST.get('description', ''),
                orientation=request.POST.get('orientation', 'landscape'),
                primary_color=request.POST.get('primary_color', '#1a1f2e'),
                secondary_color=request.POST.get('secondary_color', '#c9a227'),
                text_color=request.POST.get('text_color', '#333333'),
                title_font_size=int(request.POST.get('title_font_size', 36)),
                body_font_size=int(request.POST.get('body_font_size', 14)),
                header_text=request.POST.get('header_text', ''),
                title_text=request.POST.get('title_text', 'CERTIFICAT'),
                body_template=request.POST.get('body_template', ''),
                footer_text=request.POST.get('footer_text', ''),
                show_signature_line=request.POST.get('show_signature_line') == 'on',
                signature_label=request.POST.get('signature_label', _('Le Président')),
                show_stamp=request.POST.get('show_stamp') == 'on',
                include_qr_code=request.POST.get('include_qr_code') == 'on',
                qr_position=request.POST.get('qr_position', 'bottom-right'),
                logo_position=request.POST.get('logo_position', 'top-center'),
                is_default=request.POST.get('is_default') == 'on',
            )

            # Gérer les fichiers uploadés
            if 'background_image' in request.FILES:
                template.background_image = request.FILES['background_image']
            if 'signature_image' in request.FILES:
                template.signature_image = request.FILES['signature_image']
            if 'stamp_image' in request.FILES:
                template.stamp_image = request.FILES['stamp_image']

            template.save()
            messages.success(request, _("Modèle de certificat créé avec succès."))
            return redirect('competitions:federations:certificate_templates', federation_id=federation_id)

        except Exception as e:
            logger.error(f"Erreur création template certificat: {e}")
            messages.error(request, _("Erreur lors de la création du modèle."))

    context = {
        'federation': federation,
        'template_types': CertificateTemplate.TEMPLATE_TYPE_CHOICES,
        'orientation_choices': CertificateTemplate.ORIENTATION_CHOICES,
    }
    return render(request, 'competitions/dashboard/certification/template_form.html', context)


@login_required
def certificate_template_edit(request, federation_id, template_id):
    """Modifier un modèle de certificat"""
    federation = get_object_or_404(Federation, id=federation_id)
    template = get_object_or_404(CertificateTemplate, id=template_id, organization=federation.organization)

    if not _user_can_access_federation(request.user, federation):
        messages.error(request, _("Vous n'avez pas les permissions pour accéder à cette fédération."))
        return redirect('competitions:dashboard:dashboard')

    if request.method == 'POST':
        try:
            template.name = request.POST.get('name')
            template.template_type = request.POST.get('template_type', 'judge')
            template.description = request.POST.get('description', '')
            template.orientation = request.POST.get('orientation', 'landscape')
            template.primary_color = request.POST.get('primary_color', '#1a1f2e')
            template.secondary_color = request.POST.get('secondary_color', '#c9a227')
            template.text_color = request.POST.get('text_color', '#333333')
            template.title_font_size = int(request.POST.get('title_font_size', 36))
            template.body_font_size = int(request.POST.get('body_font_size', 14))
            template.header_text = request.POST.get('header_text', '')
            template.title_text = request.POST.get('title_text', 'CERTIFICAT')
            template.body_template = request.POST.get('body_template', '')
            template.footer_text = request.POST.get('footer_text', '')
            template.show_signature_line = request.POST.get('show_signature_line') == 'on'
            template.signature_label = request.POST.get('signature_label', _('Le Président'))
            template.show_stamp = request.POST.get('show_stamp') == 'on'
            template.include_qr_code = request.POST.get('include_qr_code') == 'on'
            template.qr_position = request.POST.get('qr_position', 'bottom-right')
            template.logo_position = request.POST.get('logo_position', 'top-center')
            template.is_default = request.POST.get('is_default') == 'on'

            # Gérer les fichiers uploadés
            if 'background_image' in request.FILES:
                template.background_image = request.FILES['background_image']
            if 'signature_image' in request.FILES:
                template.signature_image = request.FILES['signature_image']
            if 'stamp_image' in request.FILES:
                template.stamp_image = request.FILES['stamp_image']

            template.save()
            messages.success(request, _("Modèle de certificat modifié avec succès."))
            return redirect('competitions:federations:certificate_templates', federation_id=federation_id)

        except Exception as e:
            logger.error(f"Erreur modification template certificat: {e}")
            messages.error(request, _("Erreur lors de la modification du modèle."))

    context = {
        'federation': federation,
        'template': template,
        'template_types': CertificateTemplate.TEMPLATE_TYPE_CHOICES,
        'orientation_choices': CertificateTemplate.ORIENTATION_CHOICES,
        'edit_mode': True,
    }
    return render(request, 'competitions/dashboard/certification/template_form.html', context)


@login_required
@require_POST
def certificate_template_delete(request, federation_id, template_id):
    """Supprimer un modèle de certificat"""
    federation = get_object_or_404(Federation, id=federation_id)
    template = get_object_or_404(CertificateTemplate, id=template_id, organization=federation.organization)

    if not _user_can_access_federation(request.user, federation):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    # Vérifier si des certificats ont été émis avec ce modèle
    if template.issued_certificates.exists():
        return JsonResponse({
            'success': False,
            'error': gettext("Ce modèle ne peut pas être supprimé car des certificats ont été émis avec.")
        }, status=400)

    template.delete()
    return JsonResponse({'success': True, 'message': gettext("Modèle supprimé avec succès.")})


# =============================================================================
# GESTION DES DEMANDES DE CERTIFICATION
# =============================================================================

@login_required
def certification_requests_list(request, federation_id):
    """Liste des demandes de certification"""
    federation = get_object_or_404(Federation, id=federation_id)

    if not _user_can_access_federation(request.user, federation):
        messages.error(request, _("Vous n'avez pas les permissions pour accéder à cette fédération."))
        return redirect('competitions:dashboard:dashboard')

    # Filtres
    status_filter = request.GET.get('status', '')
    level_filter = request.GET.get('level', '')

    requests_qs = CertificationRequest.objects.filter(
        organization=federation.organization
    ).select_related('applicant', 'judge', 'certification_type').order_by('-created_at')

    if status_filter:
        requests_qs = requests_qs.filter(status=status_filter)
    if level_filter:
        requests_qs = requests_qs.filter(requested_level=level_filter)

    # Pagination
    paginator = Paginator(requests_qs, 20)
    page = request.GET.get('page', 1)
    requests_page = paginator.get_page(page)

    # Stats
    stats = {
        'total': CertificationRequest.objects.filter(organization=federation.organization).count(),
        'pending': CertificationRequest.objects.filter(organization=federation.organization, status='pending').count(),
        'under_review': CertificationRequest.objects.filter(organization=federation.organization, status='under_review').count(),
        'approved': CertificationRequest.objects.filter(organization=federation.organization, status='approved').count(),
        'rejected': CertificationRequest.objects.filter(organization=federation.organization, status='rejected').count(),
    }

    context = {
        'federation': federation,
        'requests': requests_page,
        'stats': stats,
        'status_choices': CertificationRequest.STATUS_CHOICES,
        'level_choices': [
            ('novice', _('Novice')),
            ('regional', _('Régional')),
            ('national', _('National')),
            ('international', _('International')),
        ],
        'current_status': status_filter,
        'current_level': level_filter,
    }
    return render(request, 'competitions/dashboard/certification/requests_list.html', context)


@login_required
def certification_request_detail(request, federation_id, request_id):
    """Détail d'une demande de certification"""
    federation = get_object_or_404(Federation, id=federation_id)
    cert_request = get_object_or_404(
        CertificationRequest,
        id=request_id,
        organization=federation.organization
    )

    if not _user_can_access_federation(request.user, federation):
        messages.error(request, _("Vous n'avez pas les permissions pour accéder à cette fédération."))
        return redirect('competitions:dashboard:dashboard')

    context = {
        'federation': federation,
        'cert_request': cert_request,
    }
    return render(request, 'competitions/dashboard/certification/request_detail.html', context)


@login_required
@require_POST
def certification_request_process(request, federation_id, request_id):
    """Traiter une demande de certification (approuver/rejeter)"""
    federation = get_object_or_404(Federation, id=federation_id)
    cert_request = get_object_or_404(
        CertificationRequest,
        id=request_id,
        organization=federation.organization
    )

    if not _user_can_access_federation(request.user, federation):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    action = request.POST.get('action')
    notes = request.POST.get('notes', '')

    try:
        if action == 'start_review':
            cert_request.start_review(request.user)
            messages.success(request, _("Demande marquée comme en cours d'examen."))

        elif action == 'approve':
            cert_request.approve(request.user, notes)

            # Émettre automatiquement le certificat si un juge est associé
            if cert_request.judge:
                judge = cert_request.judge
                judge.qualification_level = cert_request.requested_level
                if not judge.organization:
                    judge.organization = federation.organization
                if not judge.certified_since:
                    judge.certified_since = timezone.now().date()
                if not judge.certification_number:
                    import random
                    import string
                    prefix = federation.name[:3].upper() if federation.name else 'FED'
                    suffix = ''.join(random.choices(string.digits, k=6))
                    judge.certification_number = f"{prefix}-{suffix}"
                judge.save()

            messages.success(request, _("Demande approuvée. Le certificat peut maintenant être émis."))

        elif action == 'reject':
            reason = request.POST.get('rejection_reason', '')
            cert_request.reject(request.user, reason)
            messages.success(request, _("Demande rejetée."))

        else:
            messages.error(request, _("Action non reconnue."))

    except Exception as e:
        logger.error(f"Erreur traitement demande certification: {e}")
        messages.error(request, _("Erreur lors du traitement de la demande."))

    return redirect('competitions:federations:certification_request_detail',
                    federation_id=federation_id, request_id=request_id)


# =============================================================================
# ÉMISSION DE CERTIFICATS
# =============================================================================

@login_required
def issued_certificates_list(request, federation_id):
    """Liste des certificats émis par la fédération"""
    federation = get_object_or_404(Federation, id=federation_id)

    if not _user_can_access_federation(request.user, federation):
        messages.error(request, _("Vous n'avez pas les permissions pour accéder à cette fédération."))
        return redirect('competitions:dashboard:dashboard')

    # Filtres
    status_filter = request.GET.get('status', '')
    search = request.GET.get('search', '')

    certificates = IssuedCertificate.objects.filter(
        organization=federation.organization
    ).select_related('recipient', 'template', 'certification').order_by('-issue_date')

    if status_filter:
        certificates = certificates.filter(status=status_filter)
    if search:
        certificates = certificates.filter(
            Q(recipient_name__icontains=search) |
            Q(certificate_number__icontains=search) |
            Q(verification_code__icontains=search)
        )

    # Pagination
    paginator = Paginator(certificates, 20)
    page = request.GET.get('page', 1)
    certificates_page = paginator.get_page(page)

    # Stats
    stats = {
        'total': IssuedCertificate.objects.filter(organization=federation.organization).count(),
        'valid': IssuedCertificate.objects.filter(organization=federation.organization, status='valid').count(),
        'expired': IssuedCertificate.objects.filter(organization=federation.organization, status='expired').count(),
        'revoked': IssuedCertificate.objects.filter(organization=federation.organization, status='revoked').count(),
    }

    context = {
        'federation': federation,
        'certificates': certificates_page,
        'stats': stats,
        'status_choices': IssuedCertificate.STATUS_CHOICES,
        'current_status': status_filter,
        'search_query': search,
    }
    return render(request, 'competitions/dashboard/certification/issued_certificates_list.html', context)


@login_required
def issue_certificate(request, federation_id):
    """Émettre un nouveau certificat"""
    federation = get_object_or_404(Federation, id=federation_id)

    if not _user_can_access_federation(request.user, federation):
        messages.error(request, _("Vous n'avez pas les permissions pour accéder à cette fédération."))
        return redirect('competitions:dashboard:dashboard')

    if request.method == 'POST':
        try:
            # Récupérer le juge
            judge_id = request.POST.get('judge_id')
            judge = None
            recipient = None

            if judge_id:
                judge = get_object_or_404(Judge, id=judge_id)
                if judge.practitioner and judge.practitioner.user:
                    recipient = judge.practitioner.user

            # Récupérer le template
            template_id = request.POST.get('template_id')
            template = None
            if template_id:
                template = get_object_or_404(CertificateTemplate, id=template_id, organization=federation.organization)

            # Récupérer le type de certification
            certification_id = request.POST.get('certification_id')
            certification = None
            if certification_id:
                certification = get_object_or_404(JudgeCertification, id=certification_id)

            # Générer le numéro de certificat
            prefix = federation.name[:3].upper() if federation.name else 'FED'
            year = timezone.now().year
            count = IssuedCertificate.objects.filter(
                organization=federation.organization,
                issue_date__year=year
            ).count() + 1
            certificate_number = f"{prefix}-{year}-{count:06d}"

            # Calculer la date d'expiration
            validity_months = int(request.POST.get('validity_months', 36))
            valid_until = timezone.now().date() + timedelta(days=validity_months * 30)

            certificate = IssuedCertificate(
                organization=federation.organization,
                template=template,
                recipient=recipient,
                judge=judge,
                certification=certification,
                certificate_number=certificate_number,
                title=request.POST.get('title', _('Certificat de Juge')),
                recipient_name=request.POST.get('recipient_name', ''),
                certification_type=request.POST.get('certification_type', ''),
                level=request.POST.get('level', ''),
                discipline=request.POST.get('discipline', ''),
                issue_date=timezone.now().date(),
                valid_from=timezone.now().date(),
                valid_until=valid_until,
                issued_by=request.user,
                notes=request.POST.get('notes', ''),
            )
            certificate.save()

            messages.success(request, _("Certificat émis avec succès. Numéro: %(number)s") % {'number': certificate_number})
            return redirect('competitions:federations:issued_certificates', federation_id=federation_id)

        except Exception as e:
            logger.error(f"Erreur émission certificat: {e}")
            messages.error(request, _("Erreur lors de l'émission du certificat."))

    # Récupérer les données pour le formulaire
    templates = CertificateTemplate.objects.filter(
        organization=federation.organization,
        is_active=True
    )

    # Juges certifiés par la fédération
    judges = Judge.objects.filter(
        organization=federation.organization
    ).select_related('practitioner', 'practitioner__user')

    # Types de certification disponibles
    certifications = JudgeCertification.objects.filter(
        organization=federation.organization,
        is_active=True
    )

    context = {
        'federation': federation,
        'templates': templates,
        'judges': judges,
        'certifications': certifications,
        'qualification_levels': [
            ('novice', _('Novice')),
            ('regional', _('Régional')),
            ('national', _('National')),
            ('international', _('International')),
        ],
    }
    return render(request, 'competitions/dashboard/certification/issue_certificate.html', context)


@login_required
def certificate_detail(request, federation_id, certificate_id):
    """Détail d'un certificat émis"""
    federation = get_object_or_404(Federation, id=federation_id)
    certificate = get_object_or_404(
        IssuedCertificate,
        id=certificate_id,
        organization=federation.organization
    )

    if not _user_can_access_federation(request.user, federation):
        messages.error(request, _("Vous n'avez pas les permissions pour accéder à cette fédération."))
        return redirect('competitions:dashboard:dashboard')

    context = {
        'federation': federation,
        'certificate': certificate,
    }
    return render(request, 'competitions/dashboard/certification/certificate_detail.html', context)


@login_required
@require_POST
def certificate_action(request, federation_id, certificate_id):
    """Actions sur un certificat (révoquer, suspendre, réactiver)"""
    federation = get_object_or_404(Federation, id=federation_id)
    certificate = get_object_or_404(
        IssuedCertificate,
        id=certificate_id,
        organization=federation.organization
    )

    if not _user_can_access_federation(request.user, federation):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    action = request.POST.get('action')
    reason = request.POST.get('reason', '')

    try:
        if action == 'revoke':
            certificate.revoke(request.user, reason)
            messages.success(request, _("Certificat révoqué."))
        elif action == 'suspend':
            certificate.suspend(reason)
            messages.success(request, _("Certificat suspendu."))
        elif action == 'reactivate':
            certificate.reactivate()
            messages.success(request, _("Certificat réactivé."))
        else:
            messages.error(request, _("Action non reconnue."))
    except Exception as e:
        logger.error(f"Erreur action certificat: {e}")
        messages.error(request, _("Erreur lors de l'action sur le certificat."))

    return redirect('competitions:federations:certificate_detail',
                    federation_id=federation_id, certificate_id=certificate_id)


# =============================================================================
# GESTION DES EXAMENS
# =============================================================================

@login_required
def exams_list(request, federation_id):
    """Liste des examens de certification de la fédération"""
    federation = get_object_or_404(Federation, id=federation_id)

    if not _user_can_access_federation(request.user, federation):
        messages.error(request, _("Vous n'avez pas les permissions pour accéder à cette fédération."))
        return redirect('competitions:dashboard:dashboard')

    # Filtres
    status_filter = request.GET.get('status', '')
    type_filter = request.GET.get('type', '')

    exams = Exam.objects.filter(
        organization=federation.organization
    ).select_related('discipline', 'chief_examiner').order_by('-start_date')

    if status_filter:
        exams = exams.filter(status=status_filter)
    if type_filter:
        exams = exams.filter(exam_type=type_filter)

    # Pagination
    paginator = Paginator(exams, 20)
    page = request.GET.get('page', 1)
    exams_page = paginator.get_page(page)

    # Stats
    stats = {
        'total': Exam.objects.filter(organization=federation.organization).count(),
        'upcoming': Exam.objects.filter(organization=federation.organization, start_date__gte=timezone.now().date()).count(),
        'completed': Exam.objects.filter(organization=federation.organization, status='completed').count(),
        'draft': Exam.objects.filter(organization=federation.organization, status='draft').count(),
    }

    context = {
        'federation': federation,
        'exams': exams_page,
        'stats': stats,
        'status_choices': Exam.STATUS_CHOICES,
        'type_choices': Exam.EXAM_TYPE_CHOICES,
        'current_status': status_filter,
        'current_type': type_filter,
    }
    return render(request, 'competitions/dashboard/certification/exams_list.html', context)


@login_required
def exam_create(request, federation_id):
    """Créer un nouvel examen"""
    federation = get_object_or_404(Federation, id=federation_id)

    if not _user_can_access_federation(request.user, federation):
        messages.error(request, _("Vous n'avez pas les permissions pour accéder à cette fédération."))
        return redirect('competitions:dashboard:dashboard')

    if request.method == 'POST':
        try:
            # Récupérer la discipline
            discipline_id = request.POST.get('discipline_id')
            discipline = get_object_or_404(Discipline, id=discipline_id) if discipline_id else None

            exam = Exam(
                organization=federation.organization,
                discipline=discipline,
                title=request.POST.get('title'),
                description=request.POST.get('description', ''),
                exam_type=request.POST.get('exam_type', 'certification'),
                start_date=request.POST.get('start_date'),
                end_date=request.POST.get('end_date') or None,
                start_time=request.POST.get('start_time') or None,
                end_time=request.POST.get('end_time') or None,
                location=request.POST.get('location'),
                address=request.POST.get('address', ''),
                registration_start=request.POST.get('registration_start'),
                registration_end=request.POST.get('registration_end'),
                max_participants=int(request.POST.get('max_participants', 50)),
                registration_fee=request.POST.get('registration_fee', 0),
                requirements=request.POST.get('requirements', ''),
                rules=request.POST.get('rules', ''),
                materials_needed=request.POST.get('materials_needed', ''),
                status=request.POST.get('status', 'draft'),
                created_by=request.user,
            )
            exam.save()

            messages.success(request, _("Examen créé avec succès."))
            return redirect('competitions:federations:exams', federation_id=federation_id)

        except Exception as e:
            logger.error(f"Erreur création examen: {e}")
            messages.error(request, _("Erreur lors de la création de l'examen."))

    # Disciplines de la fédération
    disciplines = federation.disciplines.all()

    context = {
        'federation': federation,
        'disciplines': disciplines,
        'type_choices': Exam.EXAM_TYPE_CHOICES,
        'status_choices': Exam.STATUS_CHOICES,
    }
    return render(request, 'competitions/dashboard/certification/exam_form.html', context)


@login_required
def exam_detail(request, federation_id, exam_id):
    """Détail d'un examen"""
    federation = get_object_or_404(Federation, id=federation_id)
    exam = get_object_or_404(Exam, id=exam_id, organization=federation.organization)

    if not _user_can_access_federation(request.user, federation):
        messages.error(request, _("Vous n'avez pas les permissions pour accéder à cette fédération."))
        return redirect('competitions:dashboard:dashboard')

    # Inscriptions à cet examen
    registrations = ExamRegistration.objects.filter(exam=exam).select_related('user').order_by('-registration_date')

    context = {
        'federation': federation,
        'exam': exam,
        'registrations': registrations,
    }
    return render(request, 'competitions/dashboard/certification/exam_detail.html', context)


@login_required
def exam_edit(request, federation_id, exam_id):
    """Modifier un examen"""
    federation = get_object_or_404(Federation, id=federation_id)
    exam = get_object_or_404(Exam, id=exam_id, organization=federation.organization)

    if not _user_can_access_federation(request.user, federation):
        messages.error(request, _("Vous n'avez pas les permissions pour accéder à cette fédération."))
        return redirect('competitions:dashboard:dashboard')

    if request.method == 'POST':
        try:
            # Récupérer la discipline
            discipline_id = request.POST.get('discipline_id')
            if discipline_id:
                exam.discipline = get_object_or_404(Discipline, id=discipline_id)

            exam.title = request.POST.get('title')
            exam.description = request.POST.get('description', '')
            exam.exam_type = request.POST.get('exam_type', 'certification')
            exam.start_date = request.POST.get('start_date')
            exam.end_date = request.POST.get('end_date') or None
            exam.start_time = request.POST.get('start_time') or None
            exam.end_time = request.POST.get('end_time') or None
            exam.location = request.POST.get('location')
            exam.address = request.POST.get('address', '')
            exam.registration_start = request.POST.get('registration_start')
            exam.registration_end = request.POST.get('registration_end')
            exam.max_participants = int(request.POST.get('max_participants', 50))
            exam.registration_fee = request.POST.get('registration_fee', 0)
            exam.requirements = request.POST.get('requirements', '')
            exam.rules = request.POST.get('rules', '')
            exam.materials_needed = request.POST.get('materials_needed', '')
            exam.status = request.POST.get('status', 'draft')
            exam.save()

            messages.success(request, _("Examen modifié avec succès."))
            return redirect('competitions:federations:exam_detail', federation_id=federation_id, exam_id=exam_id)

        except Exception as e:
            logger.error(f"Erreur modification examen: {e}")
            messages.error(request, _("Erreur lors de la modification de l'examen."))

    # Disciplines de la fédération
    disciplines = federation.disciplines.all()

    context = {
        'federation': federation,
        'exam': exam,
        'disciplines': disciplines,
        'type_choices': Exam.EXAM_TYPE_CHOICES,
        'status_choices': Exam.STATUS_CHOICES,
        'edit_mode': True,
    }
    return render(request, 'competitions/dashboard/certification/exam_form.html', context)


@login_required
@require_POST
def exam_registration_action(request, federation_id, exam_id, registration_id):
    """Actions sur une inscription à un examen"""
    federation = get_object_or_404(Federation, id=federation_id)
    exam = get_object_or_404(Exam, id=exam_id, organization=federation.organization)
    registration = get_object_or_404(ExamRegistration, id=registration_id, exam=exam)

    if not _user_can_access_federation(request.user, federation):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    action = request.POST.get('action')

    try:
        if action == 'approve':
            registration.approve(request.user)
            messages.success(request, _("Inscription approuvée."))
        elif action == 'reject':
            notes = request.POST.get('notes', '')
            registration.reject(request.user, notes)
            messages.success(request, _("Inscription rejetée."))
        elif action == 'complete':
            score = request.POST.get('score')
            grade = request.POST.get('grade', '')
            passed = request.POST.get('passed') == 'true'
            feedback = request.POST.get('feedback', '')
            registration.complete_with_results(
                request.user,
                score=float(score) if score else None,
                grade=grade,
                passed=passed,
                feedback=feedback
            )
            messages.success(request, _("Résultats enregistrés."))
        else:
            messages.error(request, _("Action non reconnue."))
    except Exception as e:
        logger.error(f"Erreur action inscription examen: {e}")
        messages.error(request, _("Erreur lors de l'action sur l'inscription."))

    return redirect('competitions:federations:exam_detail', federation_id=federation_id, exam_id=exam_id)


# =============================================================================
# TÉLÉCHARGEMENT PDF DES CERTIFICATS
# =============================================================================

@login_required
def certificate_download_pdf(request, federation_id, certificate_id):
    """Télécharger le PDF d'un certificat"""
    federation = get_object_or_404(Federation, id=federation_id)
    certificate = get_object_or_404(
        IssuedCertificate,
        id=certificate_id,
        organization=federation.organization
    )

    if not _user_can_access_federation(request.user, federation):
        messages.error(request, _("Vous n'avez pas les permissions pour accéder à cette fédération."))
        return redirect('competitions:dashboard:dashboard')

    try:
        from ...services.certificate_pdf_service import generate_certificate_pdf

        pdf_buffer = generate_certificate_pdf(certificate)
        if pdf_buffer:
            # Enregistrer le téléchargement
            certificate.record_download()

            response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
            filename = f"certificat_{certificate.certificate_number}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        else:
            messages.error(request, _("Erreur lors de la génération du PDF."))
    except ImportError:
        messages.error(request, _("La génération PDF nécessite l'installation de ReportLab. Contactez l'administrateur."))
    except Exception as e:
        logger.error(f"Erreur téléchargement PDF certificat: {e}")
        messages.error(request, _("Erreur lors de la génération du PDF."))

    return redirect('competitions:federations:certificate_detail',
                    federation_id=federation_id, certificate_id=certificate_id)


# =============================================================================
# REGISTRE PUBLIC DE VÉRIFICATION
# =============================================================================

@require_GET
def verify_certificate(request, verification_code):
    """
    Page publique de vérification d'un certificat.
    Accessible sans authentification.
    """
    try:
        certificate = IssuedCertificate.objects.select_related(
            'organization', 'certification', 'recipient'
        ).get(verification_code=verification_code)

        # Enregistrer la vérification
        certificate.record_verification()

        context = {
            'certificate': certificate,
            'is_valid': certificate.is_valid,
            'verification_date': timezone.now(),
        }
        return render(request, 'competitions/public/certificate_verification.html', context)

    except IssuedCertificate.DoesNotExist:
        context = {
            'error': True,
            'message': _("Aucun certificat trouvé avec ce code de vérification."),
        }
        return render(request, 'competitions/public/certificate_verification.html', context)


@require_GET
def certificate_qr_verify(request):
    """
    Point d'entrée pour la vérification par QR code.
    Redirige vers la page de vérification si le code est fourni.
    """
    code = request.GET.get('code', '')
    if code:
        return redirect('competitions:certificate_verify', verification_code=code)

    context = {
        'show_form': True,
    }
    return render(request, 'competitions/public/certificate_verification.html', context)
