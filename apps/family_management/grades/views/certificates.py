from django.core.exceptions import PermissionDenied
# grades/views/certificates.py
"""
Vues pour la génération et la gestion des certificats et diplÃ´mes.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext as _
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
import json
import os
import uuid
import datetime
import qrcode
from io import BytesIO

from apps.competitions.models import Practitioner, Club, Federation, Discipline
from apps.grades.models import PractitionerGrade, Grade
from apps.grades.utils import get_user_club, get_user_federation
from apps.grades.utils.pdf import (
    generate_grade_certificate, 
    generate_diploma, 
    generate_multiple_certificates, 
    generate_grade_history_pdf
)
from apps.grades.services import CertificateNumberGenerator
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

@login_required
def certificate_generator(request, grade_id=None):
    """
    Interface de génération de certificat/diplÃ´me pour un grade spécifique.
    Permet la personnalisation et l'aperçu avant génération.
    """
    # Déterminer l'organisation émettrice
    club = get_user_club(request)
    federation = None if club else get_user_federation(request)
    
    organization = club or federation
    
    if not organization:
        messages.error(request, _("Vous devez Ãªtre responsable de club ou de fédération pour accéder Ã  cette page."))
        return redirect('dashboard:index')
    
    # Récupérer le grade concerné
    grade_record = get_object_or_404(PractitionerGrade, id=grade_id)
    practitioner = grade_record.practitioner
    
    # Vérifier que l'utilisateur a les droits sur ce pratiquant
    if club and practitioner.club != club:
        messages.error(request, _("Vous n'avez pas accès Ã  ce pratiquant."))
        return redirect('dashboard:index')
    
    # Variables pour le contexte
    certificate_types = [
        ('certificate', _('Certificat standard')),
        ('diploma', _('DiplÃ´me officiel')),
    ]
    
    template_types = [
        ('standard', _('Standard')),
        ('silver', _('Argent (grades intermédiaires)')),
        ('gold', _('Or (hauts grades)')),
    ]
    
    # Si le certificat a déjÃ  un numéro, l'utiliser, sinon en générer un nouveau
    if not grade_record.certificate_number:
        grade_record.certificate_number = CertificateNumberGenerator.generate(
            practitioner=practitioner,
            discipline=grade_record.discipline
        )
    
    # Contexte pour le template
    context = {
        'grade_record': grade_record,
        'practitioner': practitioner,
        'organization': organization,
        'certificate_types': certificate_types,
        'template_types': template_types,
        'custom_text': _("a démontré les compétences techniques et les connaissances requises"),
    }
    
    # Traitement du formulaire de génération
    if request.method == 'POST':
        certificate_type = request.POST.get('certificate_type', 'certificate')
        template_type = request.POST.get('template_type', 'standard')
        custom_text = request.POST.get('custom_text', '')
        certificate_number = request.POST.get('certificate_number', grade_record.certificate_number)
        
        # Mettre Ã  jour le numéro de certificat si nécessaire
        if certificate_number != grade_record.certificate_number:
            grade_record.certificate_number = certificate_number
            grade_record.save()
        
        # Générer le QR code pour la vérification (avec un lien unique)
        try:
            verification_url = f"{request.scheme}://{request.get_host()}/grades/verify/{grade_record.certificate_number}/"
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(verification_url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Sauvegarder temporairement le QR Code
            qr_path = os.path.join('temp', 'qr_verification.png')
            from django.conf import settings
            import os
            
            # Créer le dossier temp s'il n'existe pas
            temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            qr_full_path = os.path.join(settings.MEDIA_ROOT, qr_path)
            img.save(qr_full_path)
        except Exception as e:
            # Si la génération du QR échoue, continuer sans QR
            pass
        
        # Générer le PDF selon le type choisi
        if certificate_type == 'diploma':
            response = generate_diploma(
                practitioner=practitioner,
                grade_info=grade_record,
                organization=organization,
                custom_text=custom_text,
                template_type=template_type
            )
        else:
            response = generate_grade_certificate(
                practitioner=practitioner,
                grade_info=grade_record,
                organization=organization,
                custom_text=custom_text,
                template_type=template_type
            )
        
        # Supprimer le QR temporaire après génération
        try:
            os.remove(qr_full_path)
        except:
            pass
        
        return response
    
    return render(request, 'grades/certificate_generator.html', context)

@login_required
def bulk_certificate_generator(request):
    """
    Interface pour générer des certificats/diplÃ´mes en masse pour plusieurs pratiquants.
    """
    # Déterminer l'organisation émettrice
    club = get_user_club(request)
    federation = None if club else get_user_federation(request)
    
    organization = club or federation
    
    if not organization:
        messages.error(request, _("Vous devez Ãªtre responsable de club ou de fédération pour accéder Ã  cette page."))
        return redirect('dashboard:index')
    
    # Obtenir les grades les plus récents pour chaque pratiquant
    if club:
        practitioners = Practitioner.objects.filter(club=club, is_active=True)
    else:
        # Pour une fédération, récupérer les pratiquants des clubs affiliés
        club_ids = Club.objects.filter(federation=federation).values_list('id', flat=True)
        practitioners = Practitioner.objects.filter(club_id__in=club_ids, is_active=True)
    
    # Liste des grades Ã  traiter (par défaut vide)
    grade_records = []
    
    # Contexte pour le template
    context = {
        'organization': organization,
        'practitioners': practitioners,
        'grade_records': grade_records,
        'template_types': [
            ('standard', _('Standard')),
            ('silver', _('Argent (grades intermédiaires)')),
            ('gold', _('Or (hauts grades)')),
        ],
    }
    
    # Traitement de la sélection de pratiquants
    if request.method == 'POST':
        if 'select_practitioners' in request.POST:
            # Première étape : sélection des pratiquants
            selected_ids = request.POST.getlist('selected_practitioners')
            
            if not selected_ids:
                messages.warning(request, _("Aucun pratiquant sélectionné."))
                return render(request, 'grades/bulk_certificate_generator.html', context)
            
            # Récupérer les grades les plus récents pour les pratiquants sélectionnés
            grade_records = []
            for practitioner_id in selected_ids:
                practitioner = Practitioner.objects.get(id=practitioner_id)
                latest_grade = PractitionerGrade.objects.filter(
                    practitioner=practitioner,
                    is_current=True
                ).order_by('-date_obtained').first()
                
                if latest_grade:
                    grade_records.append((practitioner, latest_grade))
            
            context['grade_records'] = grade_records
            context['selected_practitioners'] = selected_ids
            
            return render(request, 'grades/bulk_certificate_generator.html', context)
        
        elif 'generate_certificates' in request.POST:
            # Deuxième étape : génération des certificats
            selected_ids = request.POST.getlist('selected_practitioners')
            template_type = request.POST.get('template_type', 'standard')
            
            if not selected_ids:
                messages.warning(request, _("Aucun pratiquant sélectionné."))
                return render(request, 'grades/bulk_certificate_generator.html', context)
            
            # Récupérer les grades pour génération
            practitioners_grades = []
            for practitioner_id in selected_ids:
                practitioner = Practitioner.objects.get(id=practitioner_id)
                latest_grade = PractitionerGrade.objects.filter(
                    practitioner=practitioner,
                    is_current=True
                ).order_by('-date_obtained').first()
                
                if latest_grade:
                    # Générer un numéro de certificat si nécessaire
                    if not latest_grade.certificate_number:
                        latest_grade.certificate_number = CertificateNumberGenerator.generate(
                            practitioner=practitioner,
                            discipline=latest_grade.discipline
                        )
                        latest_grade.save()
                    
                    practitioners_grades.append((practitioner, latest_grade))
            
            if practitioners_grades:
                return generate_multiple_certificates(
                    practitioners_grades=practitioners_grades,
                    organization=organization,
                    template_type=template_type
                )
            else:
                messages.error(request, _("Aucun grade valide trouvé pour les pratiquants sélectionnés."))
    
    return render(request, 'grades/bulk_certificate_generator.html', context)

@login_required
def verify_certificate(request, certificate_number):
    """
    Page de vérification d'un certificat via son numéro.
    """
    try:
        grade_record = PractitionerGrade.objects.get(certificate_number=certificate_number)
        practitioner = grade_record.practitioner
        
        context = {
            'grade_record': grade_record,
            'practitioner': practitioner,
            'certificate_number': certificate_number,
            'is_valid': True,
        }
        
        return render(request, 'grades/verify_certificate.html', context)
    
    except PractitionerGrade.DoesNotExist:
        context = {
            'certificate_number': certificate_number,
            'is_valid': False,
            'error_message': _("Ce numéro de certificat n'existe pas dans notre base de données."),
        }
        
        return render(request, 'grades/verify_certificate.html', context)

@require_POST
@login_required
def generate_certificate_number_ajax(request):
    """
    API pour générer un numéro de certificat via AJAX.
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
        practitioner_id = data.get('practitioner_id')
        discipline_id = data.get('discipline_id')
        
        if not practitioner_id or not discipline_id:
            return JsonResponse({'error': _('Paramètres manquants')}, status=400)
        
        practitioner = Practitioner.objects.get(id=practitioner_id)
        discipline = Discipline.objects.get(id=discipline_id)
        
        certificate_number = CertificateNumberGenerator.generate(
            practitioner=practitioner,
            discipline=discipline
        )
        
        return JsonResponse({'certificate_number': certificate_number})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def generate_verification_qr(request, certificate_number):
    """
    Génère un QR code pour la vérification du certificat.
    """
    import qrcode
    from django.http import HttpResponse
    from io import BytesIO
    
    verification_url = f"{request.scheme}://{request.get_host()}/grades/certificate/verify/{certificate_number}/"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(verification_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    response = HttpResponse(content_type="image/png")
    img_io = BytesIO()
    img.save(img_io)
    img_io.seek(0)
    response.write(img_io.read())
    
    return response

@login_required
def download_certificate(request, grade_id):
    """
    Télécharge un certificat existant ou en génère un nouveau.
    """
    grade_record = get_object_or_404(PractitionerGrade, id=grade_id)
    
    # Vérifier les permissions
    if not request.user.is_superuser:
        club = get_user_club(request)
        if not club or grade_record.practitioner.club != club:
            messages.error(request, _("Vous n'avez pas accès Ã  ce certificat."))
            return redirect('dashboard:index')
    
    # Si le certificat est déjÃ  stocké, le servir
    if grade_record.certificate_file and os.path.exists(grade_record.certificate_file.path):
        response = HttpResponse(grade_record.certificate_file.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="certificat_{grade_record.practitioner.last_name}_{grade_record.grade.name}.pdf"'
        return response
    
    # Sinon, générer un nouveau certificat
    return generate_grade_certificate(
        practitioner=grade_record.practitioner,
        grade_info=grade_record,
        organization=grade_record.practitioner.club,
    ) 

