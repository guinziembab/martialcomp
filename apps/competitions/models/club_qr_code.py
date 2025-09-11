from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import uuid
import qrcode
from io import BytesIO
from django.core.files import File
from django.conf import settings

class ClubQRCode(models.Model):
    """QR Code pour inscription directe au club"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    club = models.ForeignKey('competitions.Club', on_delete=models.CASCADE, related_name='qr_codes')
    
    # Types de QR codes
    QR_TYPE_CHOICES = [
        ('registration', _('Inscription directe')),
        ('activity', _('Suivi activité')),
        ('access', _('Accès rapide')),
    ]
    
    qr_type = models.CharField(max_length=20, choices=QR_TYPE_CHOICES, default='registration')
    title = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    
    # Données du QR code
    qr_image = models.ImageField(upload_to='qr_codes/clubs/', null=True, blank=True)
    qr_url = models.URLField(max_length=500, blank=True)
    
    # Statistiques
    scan_count = models.PositiveIntegerField(default=0)
    registration_count = models.PositiveIntegerField(default=0)
    last_scan = models.DateTimeField(null=True, blank=True)
    
    # Métadonnées
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['club', 'qr_type']
    
    def __str__(self):
        return f"QR {self.get_qr_type_display()} - {self.club.name}"
    
    def generate_qr_code(self):
        """Génère l'image du QR code"""
        if not self.qr_url:
            self.qr_url = self._generate_url()
        
        # Créer le QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(self.qr_url)
        qr.make(fit=True)
        
        # Créer l'image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Sauvegarder
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        filename = f'qr_club_{self.club.id}_{self.qr_type}_{uuid.uuid4()}.png'
        self.qr_image.save(filename, File(buffer), save=False)
    
    def _generate_url(self):
        """Génère l'URL pour le QR code"""
        base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
        
        if self.qr_type == 'registration':
            # URL d'inscription directe au club
            return f"{base_url}/club/{self.club.id}/register/?qr={self.id}&source=qr_code"
        elif self.qr_type == 'activity':
            # URL de suivi d'activité
            return f"{base_url}/club/{self.club.id}/activity/?qr={self.id}"
        elif self.qr_type == 'access':
            # URL d'accès rapide au dashboard
            return f"{base_url}/club/{self.club.id}/dashboard/?qr={self.id}"
        
        return f"{base_url}/club/{self.club.id}/"
    
    def record_scan(self):
        """Enregistre un scan du QR code"""
        self.scan_count += 1
        self.last_scan = timezone.now()
        self.save(update_fields=['scan_count', 'last_scan'])
    
    def record_registration(self):
        """Enregistre une inscription via le QR code"""
        self.registration_count += 1
        self.save(update_fields=['registration_count'])

class ClubQRScan(models.Model):
    """Historique des scans de QR codes club"""
    
    qr_code = models.ForeignKey(ClubQRCode, on_delete=models.CASCADE, related_name='scans')
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Informations du scan
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True)
    
    # Résultat
    resulted_in_registration = models.BooleanField(default=False)
    registration_user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='qr_registrations')
    
    scanned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-scanned_at']
    
    def __str__(self):
        return f"Scan {self.qr_code} - {self.scanned_at}"
