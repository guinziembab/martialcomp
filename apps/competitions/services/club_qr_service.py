from django.utils import timezone
from ..models.club_qr_code import ClubQRCode, ClubQRScan
from ..models import Club
import logging

logger = logging.getLogger(__name__)

class ClubQRService:
    """Service pour la gestion des QR codes de club"""
    
    @staticmethod
    def get_or_create_registration_qr(club):
        """Récupère ou crée le QR code d'inscription pour un club"""
        qr_code, created = ClubQRCode.objects.get_or_create(
            club=club,
            qr_type='registration',
            defaults={
                'title': f'Inscription {club.name}',
                'description': f'QR code pour s\'inscrire directement au club {club.name}',
            }
        )
        
        if created or not qr_code.qr_image:
            qr_code.generate_qr_code()
            qr_code.save()
        
        return qr_code
    
    @staticmethod
    def get_or_create_activity_qr(club):
        """Récupère ou crée le QR code de suivi d'activité"""
        qr_code, created = ClubQRCode.objects.get_or_create(
            club=club,
            qr_type='activity',
            defaults={
                'title': f'Activité {club.name}',
                'description': f'Suivi de l\'activité du club {club.name}',
            }
        )
        
        if created or not qr_code.qr_image:
            qr_code.generate_qr_code()
            qr_code.save()
        
        return qr_code
    
    @staticmethod
    def record_scan(qr_code, request, user=None):
        """Enregistre un scan de QR code"""
        try:
            # Enregistrer le scan
            scan = ClubQRScan.objects.create(
                qr_code=qr_code,
                user=user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                referrer=request.META.get('HTTP_REFERER', ''),
            )
            
            # Mettre à jour les statistiques du QR code
            qr_code.record_scan()
            
            return scan
            
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement du scan: {e}")
            return None
    
    @staticmethod
    def record_registration(qr_code, user):
        """Enregistre une inscription via QR code"""
        try:
            # Mettre à jour les statistiques
            qr_code.record_registration()
            
            # Mettre à jour le dernier scan avec l'inscription
            last_scan = qr_code.scans.filter(user=user).first()
            if last_scan:
                last_scan.resulted_in_registration = True
                last_scan.registration_user = user
                last_scan.save()
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement de l'inscription: {e}")
            return False
    
    @staticmethod
    def get_club_statistics(club):
        """Récupère les statistiques des QR codes d'un club"""
        qr_codes = ClubQRCode.objects.filter(club=club)
        
        total_scans = sum(qr.scan_count for qr in qr_codes)
        total_registrations = sum(qr.registration_count for qr in qr_codes)
        
        # Calculer le taux de conversion
        conversion_rate = 0
        if total_scans > 0:
            conversion_rate = (total_registrations / total_scans) * 100
        
        return {
            'total_qr_codes': qr_codes.count(),
            'total_scans': total_scans,
            'total_registrations': total_registrations,
            'conversion_rate': round(conversion_rate, 2),
            'recent_scans': ClubQRScan.objects.filter(qr_code__club=club).order_by('-scanned_at')[:10],
        }
