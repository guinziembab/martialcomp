# apps/competitions/services/certificate_pdf_service.py
"""
Service de génération PDF pour les certificats.
Utilise ReportLab pour créer des certificats PDF professionnels.
"""

from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext as _

import os
import logging
from io import BytesIO

logger = logging.getLogger(__name__)

# Vérifier si ReportLab est disponible
try:
    from reportlab.lib.pagesizes import A4, landscape, portrait
    from reportlab.lib.units import mm, cm
    from reportlab.lib.colors import HexColor, black, white
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("ReportLab non disponible. La génération PDF sera limitée.")

# Vérifier si qrcode est disponible
try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False
    logger.warning("qrcode non disponible. Les QR codes ne seront pas générés.")


class CertificatePDFGenerator:
    """Générateur de certificats PDF"""

    def __init__(self, certificate, template=None):
        """
        Initialise le générateur avec un certificat IssuedCertificate.

        Args:
            certificate: Instance de IssuedCertificate
            template: Instance de CertificateTemplate (optionnel, utilise celui du certificat sinon)
        """
        self.certificate = certificate
        self.template = template or certificate.template
        self.buffer = BytesIO()

    def generate(self):
        """
        Génère le PDF du certificat.

        Returns:
            BytesIO: Buffer contenant le PDF généré
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab est requis pour générer des PDFs. "
                            "Installez-le avec: pip install reportlab")

        # Déterminer l'orientation
        if self.template and self.template.orientation == 'portrait':
            page_size = portrait(A4)
        else:
            page_size = landscape(A4)

        width, height = page_size

        # Créer le canvas
        c = canvas.Canvas(self.buffer, pagesize=page_size)

        # Appliquer le fond
        self._draw_background(c, width, height)

        # Dessiner le logo
        self._draw_logo(c, width, height)

        # Dessiner l'en-tête
        self._draw_header(c, width, height)

        # Dessiner le titre
        self._draw_title(c, width, height)

        # Dessiner le corps
        self._draw_body(c, width, height)

        # Dessiner la signature et le cachet
        self._draw_signature_and_stamp(c, width, height)

        # Dessiner le QR code si activé
        if self.template and self.template.include_qr_code:
            self._draw_qr_code(c, width, height)

        # Dessiner le pied de page
        self._draw_footer(c, width, height)

        # Finaliser
        c.save()
        self.buffer.seek(0)
        return self.buffer

    def _get_color(self, color_hex, default='#333333'):
        """Convertit une couleur hex en objet Color ReportLab"""
        try:
            return HexColor(color_hex or default)
        except:
            return HexColor(default)

    def _draw_background(self, c, width, height):
        """Dessine le fond du certificat"""
        # Couleur de fond par défaut (crème/beige)
        c.setFillColor(HexColor('#FFFEF7'))
        c.rect(0, 0, width, height, fill=True, stroke=False)

        # Bordure décorative
        primary_color = self._get_color(
            self.template.primary_color if self.template else '#1a1f2e'
        )
        c.setStrokeColor(primary_color)
        c.setLineWidth(3)
        margin = 15 * mm
        c.rect(margin, margin, width - 2*margin, height - 2*margin, stroke=True, fill=False)

        # Bordure intérieure
        c.setLineWidth(1)
        inner_margin = 20 * mm
        c.rect(inner_margin, inner_margin, width - 2*inner_margin, height - 2*inner_margin, stroke=True, fill=False)

        # Image de fond si disponible
        if self.template and self.template.background_image:
            try:
                img_path = self.template.background_image.path
                if os.path.exists(img_path):
                    img = ImageReader(img_path)
                    c.drawImage(img, 0, 0, width=width, height=height,
                               preserveAspectRatio=True, anchor='c', mask='auto')
            except Exception as e:
                logger.warning(f"Erreur chargement image de fond: {e}")

    def _draw_logo(self, c, width, height):
        """Dessine le logo de l'organisation"""
        # Position selon le template
        logo_position = self.template.logo_position if self.template else 'top-center'

        if logo_position == 'top-left':
            x = 30 * mm
        elif logo_position == 'top-right':
            x = width - 60 * mm
        else:  # top-center
            x = width / 2 - 15 * mm

        y = height - 50 * mm

        # Essayer de charger le logo de l'organisation
        org = self.certificate.organization
        if org and hasattr(org, 'logo') and org.logo:
            try:
                logo_path = org.logo.path
                if os.path.exists(logo_path):
                    img = ImageReader(logo_path)
                    c.drawImage(img, x, y, width=30*mm, height=30*mm,
                               preserveAspectRatio=True, mask='auto')
                    return
            except Exception as e:
                logger.warning(f"Erreur chargement logo: {e}")

        # Placeholder si pas de logo
        primary_color = self._get_color(
            self.template.primary_color if self.template else '#1a1f2e'
        )
        c.setFillColor(primary_color)
        c.circle(x + 15*mm, y + 15*mm, 15*mm, fill=True, stroke=False)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 14)
        org_initials = org.name[:2].upper() if org else "MC"
        c.drawCentredString(x + 15*mm, y + 12*mm, org_initials)

    def _draw_header(self, c, width, height):
        """Dessine l'en-tête du certificat"""
        header_text = self.template.header_text if self.template else ""
        if not header_text and self.certificate.organization:
            header_text = self.certificate.organization.name

        if header_text:
            text_color = self._get_color(
                self.template.text_color if self.template else '#333333'
            )
            c.setFillColor(text_color)
            c.setFont("Helvetica", 12)
            c.drawCentredString(width / 2, height - 85 * mm, header_text)

    def _draw_title(self, c, width, height):
        """Dessine le titre du certificat"""
        title_text = self.template.title_text if self.template else _("CERTIFICAT")
        if not title_text:
            title_text = self.certificate.title

        primary_color = self._get_color(
            self.template.primary_color if self.template else '#1a1f2e'
        )
        font_size = self.template.title_font_size if self.template else 36

        c.setFillColor(primary_color)
        c.setFont("Helvetica-Bold", font_size)
        c.drawCentredString(width / 2, height - 100 * mm, title_text.upper())

    def _draw_body(self, c, width, height):
        """Dessine le corps du certificat"""
        # Récupérer le template du corps
        body_template = ""
        if self.template and self.template.body_template:
            body_template = self.template.body_template
        else:
            body_template = _("Certifie que {recipient_name} a obtenu la certification de {certification_type} niveau {level} en date du {date}.")

        # Remplacer les variables
        body_text = body_template.format(
            recipient_name=self.certificate.recipient_name,
            certification_type=self.certificate.certification_type or "",
            level=self.certificate.level or "",
            date=self.certificate.issue_date.strftime("%d/%m/%Y"),
            certification_number=self.certificate.certificate_number,
            organization_name=self.certificate.organization.name if self.certificate.organization else "",
            discipline=self.certificate.discipline or ""
        )

        text_color = self._get_color(
            self.template.text_color if self.template else '#333333'
        )
        font_size = self.template.body_font_size if self.template else 14

        c.setFillColor(text_color)
        c.setFont("Helvetica", font_size)

        # Centrer le texte (simplifié - pour une meilleure mise en page, utiliser Platypus)
        y_position = height - 130 * mm
        lines = body_text.split('\n')
        for line in lines:
            # Découper les lignes trop longues
            if len(line) > 80:
                words = line.split()
                current_line = ""
                for word in words:
                    if len(current_line + " " + word) < 80:
                        current_line = current_line + " " + word if current_line else word
                    else:
                        c.drawCentredString(width / 2, y_position, current_line)
                        y_position -= 20
                        current_line = word
                if current_line:
                    c.drawCentredString(width / 2, y_position, current_line)
                    y_position -= 20
            else:
                c.drawCentredString(width / 2, y_position, line)
                y_position -= 20

        # Nom du bénéficiaire en grand
        c.setFont("Helvetica-Bold", 24)
        primary_color = self._get_color(
            self.template.primary_color if self.template else '#1a1f2e'
        )
        c.setFillColor(primary_color)
        c.drawCentredString(width / 2, height - 115 * mm, self.certificate.recipient_name)

        # Numéro de certificat
        c.setFont("Helvetica", 10)
        c.setFillColor(text_color)
        c.drawCentredString(width / 2, 45 * mm,
                           f"N° {self.certificate.certificate_number}")

    def _draw_signature_and_stamp(self, c, width, height):
        """Dessine la signature et le cachet"""
        show_signature = self.template.show_signature_line if self.template else True
        show_stamp = self.template.show_stamp if self.template else True

        text_color = self._get_color(
            self.template.text_color if self.template else '#333333'
        )

        if show_signature:
            # Zone de signature
            sig_x = width * 0.7
            sig_y = 60 * mm

            # Image de signature si disponible
            if self.template and self.template.signature_image:
                try:
                    sig_path = self.template.signature_image.path
                    if os.path.exists(sig_path):
                        img = ImageReader(sig_path)
                        c.drawImage(img, sig_x - 25*mm, sig_y, width=50*mm, height=20*mm,
                                   preserveAspectRatio=True, mask='auto')
                except Exception as e:
                    logger.warning(f"Erreur chargement signature: {e}")

            # Ligne de signature
            c.setStrokeColor(text_color)
            c.setLineWidth(0.5)
            c.line(sig_x - 40*mm, sig_y - 5*mm, sig_x + 40*mm, sig_y - 5*mm)

            # Label
            sig_label = self.template.signature_label if self.template else _("Le Président")
            c.setFont("Helvetica", 10)
            c.setFillColor(text_color)
            c.drawCentredString(sig_x, sig_y - 15*mm, sig_label)

        if show_stamp:
            # Zone du cachet
            stamp_x = width * 0.3
            stamp_y = 55 * mm

            # Image du cachet si disponible
            if self.template and self.template.stamp_image:
                try:
                    stamp_path = self.template.stamp_image.path
                    if os.path.exists(stamp_path):
                        img = ImageReader(stamp_path)
                        c.drawImage(img, stamp_x - 20*mm, stamp_y, width=40*mm, height=40*mm,
                                   preserveAspectRatio=True, mask='auto')
                except Exception as e:
                    logger.warning(f"Erreur chargement cachet: {e}")

    def _draw_qr_code(self, c, width, height):
        """Dessine le QR code de vérification"""
        if not QRCODE_AVAILABLE:
            return

        # Générer l'URL de vérification
        verification_url = f"{settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'https://martialcomp.com'}/competitions/certificate/verify/{self.certificate.verification_code}/"

        # Créer le QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=1)
        qr.add_data(verification_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")

        # Convertir en format utilisable par ReportLab
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)

        # Position du QR code
        qr_position = self.template.qr_position if self.template else 'bottom-right'
        qr_size = 25 * mm

        if qr_position == 'bottom-left':
            x = 30 * mm
        elif qr_position == 'bottom-center':
            x = width / 2 - qr_size / 2
        else:  # bottom-right
            x = width - 55 * mm

        y = 25 * mm

        # Dessiner le QR code
        img = ImageReader(qr_buffer)
        c.drawImage(img, x, y, width=qr_size, height=qr_size)

        # Texte sous le QR code
        text_color = self._get_color(
            self.template.text_color if self.template else '#333333'
        )
        c.setFillColor(text_color)
        c.setFont("Helvetica", 7)
        c.drawCentredString(x + qr_size/2, y - 5*mm, _("Scanner pour vérifier"))

    def _draw_footer(self, c, width, height):
        """Dessine le pied de page"""
        footer_text = self.template.footer_text if self.template else ""

        if footer_text:
            text_color = self._get_color(
                self.template.text_color if self.template else '#333333'
            )
            c.setFillColor(text_color)
            c.setFont("Helvetica", 8)
            c.drawCentredString(width / 2, 20 * mm, footer_text)

        # Date d'émission
        c.setFont("Helvetica", 8)
        issue_date_text = _("Émis le %(date)s") % {'date': self.certificate.issue_date.strftime("%d/%m/%Y")}
        c.drawCentredString(width / 2, 15 * mm, issue_date_text)

        # Code de vérification
        c.setFont("Helvetica", 7)
        c.drawCentredString(width / 2, 10 * mm,
                           f"Code: {self.certificate.verification_code}")


def generate_certificate_pdf(certificate):
    """
    Fonction utilitaire pour générer un PDF de certificat.

    Args:
        certificate: Instance de IssuedCertificate

    Returns:
        BytesIO: Buffer contenant le PDF, ou None en cas d'erreur
    """
    try:
        generator = CertificatePDFGenerator(certificate)
        return generator.generate()
    except Exception as e:
        logger.error(f"Erreur génération PDF certificat {certificate.id}: {e}")
        return None
