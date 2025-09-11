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
    Frame, PageTemplate, BaseDocTemplate, NextPageTemplate, PageBreak
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

def generate_grade_certificate(practitioner, grade_info, organization=None, custom_text=None, template_type='standard'):
    """
    Génère un certificat de grade en PDF.
    
    Args:
        practitioner: Instance du modèle Practitioner
        grade_info: Instance du modèle PractitionerGrade
        organization: Instance du modèle Club ou Federation
        custom_text: Texte personnalisé pour le certificat
        template_type: Type de template ('standard', 'silver', 'gold')
    
    Returns:
        HttpResponse avec le PDF généré
    """
    # Créer le buffer pour le PDF
    buffer = io.BytesIO()
    
    # Créer le document PDF en mode paysage
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Créer le template de page avec arrière-plan
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
    template = PageTemplate(id='certificate', frames=[frame], onPage=lambda canvas, doc: draw_certificate_background(canvas, doc, template_type))
    doc.addPageTemplates([template])
    
    # Obtenir les styles
    styles = get_certificate_styles()
    
    # Contenu du certificat
    story = []
    
    # Titre du certificat
    story.append(Paragraph(_("CERTIFICAT DE GRADE"), styles['CertificateTitle']))
    story.append(Spacer(1, 20))
    
    # Texte principal
    if custom_text:
        main_text = custom_text
    else:
        main_text = _("a démontré les compétences techniques et les connaissances requises")
    
    certificate_text = f"""
    {_("Ce certificat atteste que")}
    <br/><br/>
    <strong>{practitioner.full_name}</strong>
    <br/><br/>
    {main_text}
    <br/><br/>
    {_("pour obtenir le grade de")} <strong>{grade_info.grade.name}</strong>
    <br/>
    {_("dans la discipline")} <strong>{grade_info.discipline.name}</strong>
    """
    
    story.append(Paragraph(certificate_text, styles['CertificateBody']))
    story.append(Spacer(1, 30))
    
    # Informations sur l'attribution
    info_text = f"""
    {_("Attribué le")} {grade_info.date_obtained.strftime('%d/%m/%Y')}
    """
    if grade_info.awarded_by:
        info_text += f"<br/>{_('par')} {grade_info.awarded_by}"
    if grade_info.location:
        info_text += f"<br/>{_('Ã ')} {grade_info.location}"
    
    story.append(Paragraph(info_text, styles['CertificateInfo']))
    story.append(Spacer(1, 40))
    
    # Tableau pour les signatures
    signature_data = [
        ['', '', ''],
        ['', '', ''],
        ['', '', ''],
        ['', '', ''],
    ]
    
    signature_table = Table(signature_data, colWidths=[doc.width/3]*3)
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, -1), 'Montserrat' if 'Montserrat' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('LINEBELOW', (0, 0), (0, 0), 1, colors.black),
        ('LINEBELOW', (1, 0), (1, 0), 1, colors.black),
        ('LINEBELOW', (2, 0), (2, 0), 1, colors.black),
    ]))
    
    story.append(signature_table)
    story.append(Spacer(1, 20))
    
    # Numéro de certificat
    if grade_info.certificate_number:
        story.append(Paragraph(f"Certificat NÂ° {grade_info.certificate_number}", styles['CertificateNumber']))
    
    # Générer le PDF
    doc.build(story)
    
    # Préparer la réponse
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="certificat_{practitioner.last_name}_{grade_info.grade.name}.pdf"'
    
    return response

def generate_diploma(practitioner, grade_info, organization=None, custom_text=None, template_type='gold'):
    """
    Génère un diplÃ´me officiel en PDF (version plus élaborée du certificat).
    """
    return generate_grade_certificate(practitioner, grade_info, organization, custom_text, template_type)

def generate_multiple_certificates(practitioners_grades, organization=None, template_type='standard'):
    """
    Génère plusieurs certificats en un seul PDF.
    
    Args:
        practitioners_grades: Liste de tuples (practitioner, grade_info)
        organization: Instance du modèle Club ou Federation
        template_type: Type de template
    
    Returns:
        HttpResponse avec le PDF généré
    """
    # Créer le buffer pour le PDF
    buffer = io.BytesIO()
    
    # Créer le document PDF
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Obtenir les styles
    styles = get_certificate_styles()
    
    # Contenu du document
    story = []
    
    # Titre du document
    story.append(Paragraph(_("CERTIFICATS DE GRADES"), styles['CertificateTitle']))
    story.append(Spacer(1, 20))
    
    # Générer un certificat par page
    for i, (practitioner, grade_info) in enumerate(practitioners_grades):
        if i > 0:
            story.append(PageBreak())
        
        # Contenu du certificat
        certificate_text = f"""
        {_("Ce certificat atteste que")}
        <br/><br/>
        <strong>{practitioner.full_name}</strong>
        <br/><br/>
        {_("a obtenu le grade de")} <strong>{grade_info.grade.name}</strong>
        <br/>
        {_("dans la discipline")} <strong>{grade_info.discipline.name}</strong>
        <br/><br/>
        {_("Attribué le")} {grade_info.date_obtained.strftime('%d/%m/%Y')}
        """
        
        if grade_info.certificate_number:
            certificate_text += f"<br/><br/>Certificat NÂ° {grade_info.certificate_number}"
        
        story.append(Paragraph(certificate_text, styles['CertificateBody']))
    
    # Générer le PDF
    doc.build(story)
    
    # Préparer la réponse
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="certificats_multiples.pdf"'
    
    return response

def generate_grade_history_pdf(practitioner, grade_history):
    """
    Génère un PDF avec l'historique complet des grades d'un pratiquant.
    """
    # Créer le buffer pour le PDF
    buffer = io.BytesIO()
    
    # Créer le document PDF
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Obtenir les styles
    styles = get_certificate_styles()
    
    # Contenu du document
    story = []
    
    # Titre du document
    story.append(Paragraph(f"HISTORIQUE DES GRADES - {practitioner.full_name}", styles['CertificateTitle']))
    story.append(Spacer(1, 20))
    
    # Informations du pratiquant
    story.append(Paragraph(f"<strong>Pratiquant:</strong> {practitioner.full_name}", styles['CertificateBody']))
    story.append(Paragraph(f"<strong>Date de naissance:</strong> {practitioner.birth_date.strftime('%d/%m/%Y')}", styles['CertificateBody']))
    if practitioner.club:
        story.append(Paragraph(f"<strong>Club:</strong> {practitioner.club.name}", styles['CertificateBody']))
    story.append(Spacer(1, 20))
    
    # Tableau des grades
    if grade_history:
        data = [['Grade', 'Discipline', 'Date d\'obtention', 'Statut']]
        for grade in grade_history:
            status = _("Actuel") if grade.is_current else _("Ancien")
            data.append([
                grade.grade.name,
                grade.discipline.name,
                grade.date_obtained.strftime('%d/%m/%Y'),
                status
            ])
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
    else:
        story.append(Paragraph(_("Aucun grade enregistré."), styles['CertificateBody']))
    
    # Générer le PDF
    doc.build(story)
    
    # Préparer la réponse
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="historique_grades_{practitioner.last_name}.pdf"'
    
    return response 
