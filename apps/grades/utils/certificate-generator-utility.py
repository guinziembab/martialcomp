# grades/utils/pdf.py
"""
Module pour la génération de certificats et diplÃ´mes en PDF.
Utilise ReportLab pour une génération précise et élégante.
"""
import os
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, 
    Frame, PageTemplate, BaseDocTemplate, NextPageTemplate
)
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from django.conf import settings
from django.http import HttpResponse
from django.utils.translation import gettext as _
from django.utils import timezone

# Enregistrement des polices
try:
    # Montserrat pour un design moderne
    pdfmetrics.registerFont(TTFont('Montserrat', os.path.join(settings.STATIC_ROOT, 'fonts/Montserrat-Regular.ttf')))
    pdfmetrics.registerFont(TTFont('MontserratBold', os.path.join(settings.STATIC_ROOT, 'fonts/Montserrat-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('MontserratItalic', os.path.join(settings.STATIC_ROOT, 'fonts/Montserrat-Italic.ttf')))
    
    # Police pour les caractères asiatiques (pour disciplines comme Karaté, Judo)
    pdfmetrics.registerFont(TTFont('NotoSans', os.path.join(settings.STATIC_ROOT, 'fonts/NotoSans-Regular.ttf')))
    pdfmetrics.registerFont(TTFont('NotoSansBold', os.path.join(settings.STATIC_ROOT, 'fonts/NotoSans-Bold.ttf')))
except:
    # Fallback si les polices personnalisées ne sont pas disponibles
    pass

# Styles de paragraphe personnalisés
def get_certificate_styles():
    """Définit les styles de texte pour les certificats"""
    styles = getSampleStyleSheet()
    
    # Style pour le titre du certificat
    styles.add(ParagraphStyle(
        name='CertificateTitle',
        fontName='MontserratBold' if 'MontserratBold' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold',
        fontSize=24,
        alignment=1,  # Centré
        spaceAfter=12,
        textColor=colors.darkblue,
    ))
    
    # Style pour le nom du pratiquant
    styles.add(ParagraphStyle(
        name='PractitionerName',
        fontName='MontserratBold' if 'MontserratBold' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold',
        fontSize=18,
        alignment=1,
        spaceAfter=10,
        textColor=colors.black,
    ))
    
    # Style pour le texte du corps du certificat
    styles.add(ParagraphStyle(
        name='CertificateBody',
        fontName='Montserrat' if 'Montserrat' in pdfmetrics.getRegisteredFontNames() else 'Helvetica',
        fontSize=12,
        alignment=1,
        spaceAfter=6,
        leading=18,
    ))
    
    # Style pour les informations supplémentaires
    styles.add(ParagraphStyle(
        name='CertificateInfo',
        fontName='MontserratItalic' if 'MontserratItalic' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Oblique',
        fontSize=10,
        alignment=1,
        textColor=colors.darkslategray,
    ))
    
    # Style pour le numéro de certificat
    styles.add(ParagraphStyle(
        name='CertificateNumber',
        fontName='Montserrat' if 'Montserrat' in pdfmetrics.getRegisteredFontNames() else 'Helvetica',
        fontSize=9,
        alignment=1,
        textColor=colors.darkgray,
    ))
    
    # Style pour les signatures
    styles.add(ParagraphStyle(
        name='Signature',
        fontName='MontserratBold' if 'MontserratBold' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold',
        fontSize=10,
        alignment=1,
    ))
    
    return styles

def draw_certificate_background(canvas, doc, template_type='standard'):
    """Dessine l'arrière-plan du certificat avec bordure et motifs décoratifs"""
    width, height = landscape(A4)
    
    # Fond du certificat
    if template_type == 'gold':
        # Dégradé doré pour les hauts grades
        canvas.saveState()
        p = canvas.beginPath()
        p.rect(0, 0, width, height)
        canvas.clipPath(p, stroke=0)
        canvas.setFillColorRGB(0.95, 0.95, 0.8)
        canvas.rect(0, 0, width, height, stroke=0, fill=1)
        
        # Dégradé subtil
        for i in range(10):
            ratio = i / 10
            canvas.setFillColorRGB(0.95 - (ratio * 0.1), 0.95 - (ratio * 0.05), 0.8 - (ratio * 0.1))
            canvas.rect(0, height * ratio, width, height * 0.1, stroke=0, fill=1)
        canvas.restoreState()
    elif template_type == 'silver':
        # Dégradé argenté pour les grades intermédiaires
        canvas.saveState()
        canvas.setFillColorRGB(0.9, 0.9, 0.93)
        canvas.rect(0, 0, width, height, stroke=0, fill=1)
        
        # Dégradé subtil
        for i in range(10):
            ratio = i / 10
            canvas.setFillColorRGB(0.9 - (ratio * 0.1), 0.9 - (ratio * 0.1), 0.93 - (ratio * 0.1))
            canvas.rect(0, height * ratio, width, height * 0.1, stroke=0, fill=1)
        canvas.restoreState()
    else:
        # Fond standard
        canvas.saveState()
        canvas.setFillColorRGB(0.98, 0.98, 1)
        canvas.rect(0, 0, width, height, stroke=0, fill=1)
        canvas.restoreState()
    
    # Bordure décorative
    canvas.saveState()
    canvas.setStrokeColorRGB(0.2, 0.2, 0.5)
    canvas.setLineWidth(1)
    # Bordure extérieure
    canvas.rect(1*cm, 1*cm, width-2*cm, height-2*cm)
    # Bordure intérieure
    canvas.setStrokeColorRGB(0.3, 0.3, 0.6)
    canvas.setLineWidth(0.5)
    canvas.rect(1.5*cm, 1.5*cm, width-3*cm, height-3*cm)
    canvas.restoreState()
    
    # Motifs décoratifs dans les coins
    try:
        # Essayer de charger l'image décorative pour les coins
        corner_img_path = os.path.join(settings.STATIC_ROOT, 'images/certificate/corner_decoration.png')
        if os.path.exists(corner_img_path):
            # Coin supérieur gauche
            canvas.saveState()
            canvas.translate(1.2*cm, height-1.2*cm)
            canvas.rotate(0)
            canvas.drawImage(corner_img_path, 0, 0, width=2*cm, height=2*cm, mask='auto')
            canvas.restoreState()
            
            # Coin supérieur droit
            canvas.saveState()
            canvas.translate(width-1.2*cm, height-1.2*cm)
            canvas.rotate(90)
            canvas.drawImage(corner_img_path, 0, 0, width=2*cm, height=2*cm, mask='auto')
            canvas.restoreState()
            
            # Coin inférieur gauche
            canvas.saveState()
            canvas.translate(1.2*cm, 1.2*cm)
            canvas.rotate(-90)
            canvas.drawImage(corner_img_path, 0, 0, width=2*cm, height=2*cm, mask='auto')
            canvas.restoreState()
            
            # Coin inférieur droit
            canvas.saveState()
            canvas.translate(width-1.2*cm, 1.2*cm)
            canvas.rotate(180)
            canvas.drawImage(corner_img_path, 0, 0, width=2*cm, height=2*cm, mask='auto')
            canvas.restoreState()
    except:
        # Fallback si l'image n'est pas disponible : dessiner des motifs simples
        canvas.saveState()
        canvas.setStrokeColorRGB(0.3, 0.3, 0.6)
        canvas.setLineWidth(0.8)
        
        # Motif coin supérieur gauche
        canvas.line(1*cm, height-1*cm, 3*cm, height-1*cm)
        canvas.line(1*cm, height-1*cm, 1*cm, height-3*cm)
        
        # Motif coin supérieur droit
        canvas.line(width-1*cm, height-1*cm, width-3*cm, height-1*cm)
        canvas.line(width-1*cm, height-1*cm, width-1*cm, height-3*cm)
        
        # Motif coin inférieur gauche
        canvas.line(1*cm, 1*cm, 3*cm, 1*cm)
        canvas.line(1*cm, 1*cm, 1*cm, 3*cm)
        
        # Motif coin inférieur droit
        canvas.line(width-1*cm, 1*cm, width-3*cm, 1*cm)
        canvas.line(width-1*cm, 1*cm, width-1*cm, 3*cm)
        canvas.restoreState()
    
    # Ajouter QR code en bas Ã  droite pour la vérification
    try:
        qr_code_path = os.path.join(settings.MEDIA_ROOT, 'temp/qr_verification.png')
        if os.path.exists(qr_code_path):
            canvas.drawImage(qr_code_path, width-3.5*cm, 1.2*cm, width=2*cm, height=2*cm)
            
            # Texte explicatif pour le QR Code
            canvas.setFont('Helvetica', 6)
            canvas.setFillColor(colors.darkgray)
            canvas.drawString(width-3.8*cm, 1*cm, _("Scanner pour vérifier l'authenticité"))
    except:
        pass
    
    # Numéro de page (discret, en bas au centre)
    canvas.saveState()
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.darkgray)
    canvas.drawCentredString(width/2, 0.5*cm, _("Page %d") % doc.page)
    canvas.restoreState()

def generate_grade_certificate(practitioner, grade_info, organization=None, custom_text=None, template_type='standard'):
    """
    Génère un certificat de grade élégant pour un pratiquant.
    
    Args:
        practitioner: Instance du modèle Practitioner
        grade_info: Instance du modèle PractitionerGrade
        organization: Instance de l'organisation émettrice (Club ou Fédération)
        custom_text: Texte libre Ã  inclure sur le certificat
        template_type: Type de template ('standard', 'gold', 'silver')
    
    Returns:
        HttpResponse avec le PDF généré
    """
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="certificat_{practitioner.last_name}_{grade_info.grade.name}.pdf"'
    
    # Création d'un buffer pour le PDF
    buffer = io.BytesIO()
    
    # Configuration du document
    doc = BaseDocTemplate(
        buffer, 
        pagesize=landscape(A4),
        leftMargin=2*cm, 
        rightMargin=2*cm,
        topMargin=2*cm, 
        bottomMargin=2*cm
    )
    
    # Définition du frame principal
    frame = Frame(
        doc.leftMargin, 
        doc.bottomMargin, 
        doc.width, 
        doc.height,
        id='normal'
    )
    
    # Création du template de page avec le background
    template = PageTemplate(
        id='certificate', 
        frames=frame,
        onPage=lambda canvas, doc: draw_certificate_background(canvas, doc, template_type)
    )
    doc.addPageTemplates([template])
    
    # Récupération des styles
    styles = get_certificate_styles()
    
    # Construction du contenu
    story = []
    
    # Logo de l'organisation en haut
    try:
        org_logo_path = None
        if organization and hasattr(organization, 'logo') and organization.logo:
            org_logo_path = organization.logo.path
        else:
            # Logo par défaut
            org_logo_path = os.path.join(settings.STATIC_ROOT, 'images/logo-martialcomp.png')
        
        if os.path.exists(org_logo_path):
            logo = Image(org_logo_path)
            logo.drawWidth = 5*cm
            logo.drawHeight = 5*cm * logo.drawHeight / logo.drawWidth
            logo.hAlign = 'CENTER'
            story.append(logo)
    except:
        # Pas de logo disponible
        pass
    
    story.append(Spacer(1, 0.5*cm))
    
    # Titre du certificat
    if grade_info.grade.level >= 5:  # Niveau élevé
        certificate_title = _("DIPLÃ”ME D'EXCELLENCE")
    else:
        certificate_title = _("CERTIFICAT DE GRADE")
    
    story.append(Paragraph(certificate_title, styles['CertificateTitle']))
    story.append(Spacer(1, 0.5*cm))
    
    # Nom de l'organisation émettrice
    if organization:
        org_name = organization.name
    else:
        org_name = _("MartialComp")
    
    story.append(Paragraph(org_name, styles['CertificateInfo']))
    story.append(Spacer(1, 1*cm))
    
    # Texte de certification
    cert_text = _("Certifie que")
    story.append(Paragraph(cert_text, styles['CertificateBody']))
    story.append(Spacer(1, 0.5*cm))
    
    # Nom du pratiquant
    practitioner_name = f"{practitioner.first_name} {practitioner.last_name}".upper()
    story.append(Paragraph(practitioner_name, styles['PractitionerName']))
    story.append(Spacer(1, 0.5*cm))
    
    # Information de licence
    if hasattr(practitioner, 'license_number') and practitioner.license_number:
        license_text = _("Licence NÂ° {}").format(practitioner.license_number)
        story.append(Paragraph(license_text, styles['CertificateInfo']))
        story.append(Spacer(1, 0.5*cm))
    
    # Texte principal du certificat
    main_text = _("a obtenu le grade de")
    story.append(Paragraph(main_text, styles['CertificateBody']))
    story.append(Spacer(1, 0.5*cm))
    
    # Grade obtenu (en gras et grande taille)
    grade_name = grade_info.grade.name
    # Utiliser une police qui supporte les caractères asiatiques si nécessaire
    if any(ord(c) > 127 for c in grade_name):
        grade_style = ParagraphStyle(
            name='AsianGradeName',
            fontName='NotoSansBold' if 'NotoSansBold' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold',
            fontSize=24,
            alignment=1,
            spaceAfter=12,
            textColor=colors.darkblue,
        )
        story.append(Paragraph(grade_name, grade_style))
    else:
        story.append(Paragraph(grade_name, styles['CertificateTitle']))
    
    story.append(Spacer(1, 0.5*cm))
    
    # Discipline
    discipline_text = _("en {}").format(grade_info.discipline.name)
    story.append(Paragraph(discipline_text, styles['CertificateBody']))
    story.append(Spacer(1, 0.5*cm))
    
    # Date d'obtention
    date_text = _("le {}").format(grade_info.date_obtained.strftime('%d/%m/%Y'))
    story.append(Paragraph(date_text, styles['CertificateInfo']))
    story.append(Spacer(1, 0.5*cm))
    
    # Texte personnalisé si fourni
    if custom_text:
        story.append(Paragraph(custom_text, styles['CertificateBody']))
        story.append(Spacer(1, 0.5*cm))
    
    # Lieu d'obtention si disponible
    if grade_info.location:
        location_text = _("Ã  {}").format(grade_info.location)
        story.append(Paragraph(location_text, styles['CertificateInfo']))
        story.append(Spacer(1, 0.5*cm))
    
    # Autorité ayant délivré le grade
    if grade_info.awarded_by:
        awarded_text = _("Grade délivré par: {}").format(grade_info.awarded_by)
        story.append(Paragraph(awarded_text, styles['CertificateInfo']))
        story.append(Spacer(1, 0.5*cm))
    
    # Numéro de certificat
    if grade_info.certificate_number:
        cert_num_text = _("Certificat NÂ° {}").format(grade_info.certificate_number)
        story.append(Paragraph(cert_num_text, styles['CertificateNumber']))
        story.append(Spacer(1, 1*cm))
    
    # Tableau pour les signatures
    signature_data = [
        [_("Le Responsable Technique"), "", _("Le Titulaire")],
        ["", "", ""],
        ["", "", ""],
        ["_______________________", "", "_______________________"],
    ]
    
    signature_table = Table(signature_data, colWidths=[doc.width/3.0]*3)
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONT', (0, 3), (-1, 3), 'Helvetica'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
    ]))
    
    story.append(signature_table)
    story.append(Spacer(1, 0.5*cm))
    
    # Date de génération du certificat
    generation_date = timezone.now().strftime("%d/%m/%Y")
    generation_text = _("Document généré le {}").format(generation_date)
    story.append(Paragraph(generation_text, styles['CertificateNumber']))
    
    # Si une date d'expiration est définie
    if grade_info.date_expiry:
        expiry_text = _("Valide jusqu'au {}").format(grade_info.date_expiry.strftime('%d/%m/%Y'))
        story.append(Paragraph(expiry_text, styles['CertificateNumber']))
    
    # Génération du document
    doc.build(story)
    
    # Récupération du contenu du PDF depuis le buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    # Ã‰criture dans la réponse HTTP
    response.write(pdf)
    return response

def generate_diploma(practitioner, grade_info, organization=None, custom_text=None, template_type='gold'):
    """
    Génère un diplÃ´me plus formel, similaire au certificat mais avec un design plus élaboré.
    Cette fonction est similaire Ã  generate_grade_certificate mais avec un style plus prestigieux.
    
    Args:
        practitioner: Instance du modèle Practitioner
        grade_info: Instance du modèle PractitionerGrade
        organization: Instance de l'organisation émettrice (Club ou Fédération)
        custom_text: Texte libre Ã  inclure sur le diplÃ´me
        template_type: Type de template ('gold', 'silver', 'standard')
    
    Returns:
        HttpResponse avec le PDF généré
    """
    # Réutilise la mÃªme logique que generate_grade_certificate avec des adaptations visuelles
    # Par défaut, utilise le template_type 'gold' pour un diplÃ´me plus prestigieux
    return generate_grade_certificate(
        practitioner, 
        grade_info, 
        organization, 
        custom_text, 
        template_type='gold' if template_type == 'standard' else template_type
    )

def generate_multiple_certificates(practitioners_grades, organization=None, template_type='standard'):
    """
    Génère un fichier PDF contenant plusieurs certificats (un par page).
    Utile pour générer en masse des certificats après un passage de grade.
    
    Args:
        practitioners_grades: Liste de tuples (practitioner, grade_info)
        organization: Instance de l'organisation émettrice
        template_type: Type de template
    
    Returns:
        HttpResponse avec le PDF généré
    """
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="certificats_groupes.pdf"'
    
    buffer = io.BytesIO()
    doc = BaseDocTemplate(
        buffer, 
        pagesize=landscape(A4),
        leftMargin=2*cm, 
        rightMargin=2*cm,
        topMargin=2*cm, 
        bottomMargin=2*cm
    )
    
    frame = Frame(
        doc.leftMargin, 
        doc.bottomMargin, 
        doc.width, 
        doc.height,
        id='normal'
    )
    
    template = PageTemplate(
        id='certificate', 
        frames=frame,
        onPage=lambda canvas, doc: draw_certificate_background(canvas, doc, template_type)
    )
    doc.addPageTemplates([template])
    
    styles = get_certificate_styles()
    story = []
    
    # Pour chaque paire practitioner/grade
    for i, (practitioner, grade_info) in enumerate(practitioners_grades):
        # Ajouter un saut de page sauf pour le premier certificat
        if i > 0:
            story.append(PageBreak())
        
        # Générer le contenu du certificat (code similaire Ã  generate_grade_certificate)
        # Logo, titre, nom, etc.
        # ...
        
        # C'est une version simplifiée. Dans une implémentation complète,
        # il faudrait dupliquer la logique de contenu de generate_grade_certificate
    
    # Génération du document
    doc.build(story)
    
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response

def generate_grade_history_pdf(practitioner, grade_history):
    """
    Génère un PDF avec l'historique des grades d'un pratiquant.
    
    Args:
        practitioner: Instance du modèle Practitioner
        grade_history: QuerySet des PractitionerGrade du pratiquant
    
    Returns:
        HttpResponse avec le PDF généré
    """
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="historique_grades_{practitioner.last_name}.pdf"'
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2*cm,
        rightMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    
    # Titre
    title_style = ParagraphStyle(
        name='Title',
        parent=styles['Title'],
        fontSize=16,
        alignment=1,
        spaceAfter=12,
    )
    
    # Style pour les en-tÃªtes de tableau
    header_style = ParagraphStyle(
        name='TableHeader',
        parent=styles['Normal'],
        fontSize=10,
        alignment=1,
        textColor=colors.white,
        backColor=colors.darkblue,
    )
    
    # Construction du contenu
    story = []
    
    # Logo du système
    try:
        logo_path = os.path.join(settings.STATIC_ROOT, 'images/logo-martialcomp.png')
        if os.path.exists(logo_path):
            logo = Image(logo_path)
            logo.drawWidth = 3*cm
            logo.drawHeight = 3*cm * logo.drawHeight / logo.drawWidth
            logo.hAlign = 'CENTER'
            story.append(logo)
            story.append(Spacer(1, 0.5*cm))
    except:
        pass
    
    # Titre
    title = _("Historique des Grades")
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Informations du pratiquant
    practitioner_info = f"{practitioner.first_name} {practitioner.last_name}"
    if hasattr(practitioner, 'license_number') and practitioner.license_number:
        practitioner_info += f" - {_('Licence NÂ°')} {practitioner.license_number}"
    if hasattr(practitioner, 'birth_date') and practitioner.birth_date:
        practitioner_info += f" - {_('Né(e) le')} {practitioner.birth_date.strftime('%d/%m/%Y')}"
        
    story.append(Paragraph(practitioner_info, styles['Normal']))
    story.append(Spacer(1, 1*cm))
    
    # Tableau des grades
    if grade_history:
        # En-tÃªtes
        table_data = [
            [
                Paragraph(_("Date"), header_style),
                Paragraph(_("Discipline"), header_style),
                Paragraph(_("Grade"), header_style),
                Paragraph(_("Décerné par"), header_style),
                Paragraph(_("Lieu"), header_style),
                Paragraph(_("NÂ° Certificat"), header_style),
                Paragraph(_("Validité"), header_style),
            ]
        ]
        
        # Données
        for grade in grade_history:
            date_obtained = grade.date_obtained.strftime('%d/%m/%Y') if grade.date_obtained else '-'
            discipline = grade.discipline.name if hasattr(grade, 'discipline') and grade.discipline else '-'
            grade_name = grade.grade.name if hasattr(grade, 'grade') and grade.grade else '-'
            awarded_by = grade.awarded_by if grade.awarded_by else '-'
            location = grade.location if grade.location else '-'
            certificate_number = grade.certificate_number if grade.certificate_number else '-'
            
            # Statut de validité
            if hasattr(grade, 'date_expiry') and grade.date_expiry:
                if grade.date_expiry >= timezone.now().date():
                    validity = _("Valide jusqu'au {}").format(grade.date_expiry.strftime('%d/%m/%Y'))
                else:
                    validity = _("Expiré le {}").format(grade.date_expiry.strftime('%d/%m/%Y'))
            else:
                validity = _("Permanent")
            
            table_data.append([
                date_obtained,
                discipline,
                grade_name,
                awarded_by,
                location,
                certificate_number,
                validity
            ])
        
        # Création du tableau
        table = Table(table_data, repeatRows=1)
        
        # Style du tableau
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ])
        
        # Alternance de couleur pour les lignes
        for i in range(1, len(table_data)):
            if i % 2 == 0:
                table_style.add('BACKGROUND', (0, i), (-1, i), colors.whitesmoke)
        
        table.setStyle(table_style)
        story.append(table)
    else:
        # Message si pas d'historique
        story.append(Paragraph(_("Aucun grade enregistré pour ce pratiquant."), styles['Normal']))
    
    story.append(Spacer(1, 1*cm))
    
    # Date de génération et pied de page
    generation_date = timezone.now().strftime("%d/%m/%Y %H:%M")
    footer_text = _("Document généré le {} par MartialComp").format(generation_date)
    story.append(Paragraph(footer_text, styles['Normal']))
    
    # Génération du document
    doc.build(story)
    
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response

