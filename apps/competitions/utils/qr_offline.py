"""
Module de gestion des QR codes en mode hors-ligne.
Permet la validation locale des QR codes sans accès au serveur.
"""
import uuid
import json
import hashlib
import base64
import time
import os
from django.utils import timezone
from django.conf import settings
from django.core.files.base import ContentFile
from datetime import datetime, timedelta

# Constantes
TOKEN_VALIDITY_DAYS = 7  # Durée de validité du token de vérification hors-ligne en jours
PROFILE_VALIDITY_DAYS = 30  # Durée de validité du profil hors-ligne en jours
HASH_SECRET = getattr(settings, 'QR_OFFLINE_SECRET', 'martialcomp_offline_secret')  # Secret pour la génération des signatures


class OfflineQRTokenGenerator:
    """
    Générateur de tokens pour la validation hors-ligne des QR codes.
    Permet de vérifier l'authenticité d'un QR code sans accéder au serveur.
    """
    
    @staticmethod
    def generate_offline_token(practitioner_id, qr_code_uuid, federation_validated=False, club_id=None):
        """
        Génère un token de validation hors-ligne.
        
        Args:
            practitioner_id: ID du pratiquant
            qr_code_uuid: UUID du QR code
            federation_validated: Si le QR code est validé par la fédération
            club_id: ID du club du pratiquant (optionnel)
            
        Returns:
            str: Token encodé en JSON+Base64 avec signature
        """
        # Générer les dates d'expiration
        now = timezone.now()
        expiry = now + timedelta(days=TOKEN_VALIDITY_DAYS)
        
        # Créer le payload du token
        token_data = {
            "prac_id": practitioner_id,
            "qr_uuid": str(qr_code_uuid),
            "fed_val": federation_validated,
            "club_id": club_id,
            "iat": int(now.timestamp()),
            "exp": int(expiry.timestamp()),
            "jti": str(uuid.uuid4())  # ID unique du token
        }
        
        # Ajouter signature de sécurité
        token_data["sig"] = OfflineQRTokenGenerator._generate_signature(token_data)
        
        # Encoder en Base64
        token_json = json.dumps(token_data)
        return base64.urlsafe_b64encode(token_json.encode()).decode()
    
    @staticmethod
    def verify_offline_token(token):
        """
        Vérifie un token de validation hors-ligne.
        
        Args:
            token: Token encodé en Base64
            
        Returns:
            dict: Données du token si valide, None sinon
        """
        try:
            # Décoder le token
            raw_data = base64.urlsafe_b64decode(token.encode()).decode()
            token_data = json.loads(raw_data)
            
            # Extraire et vérifier la signature
            signature = token_data.pop("sig", None)
            expected_signature = OfflineQRTokenGenerator._generate_signature(token_data)
            
            if not signature or signature != expected_signature:
                return {"valid": False, "reason": "signature_invalid"}
            
            # Vérifier l'expiration
            now = int(time.time())
            if token_data.get("exp", 0) < now:
                return {"valid": False, "reason": "token_expired"}
            
            # Token valide
            token_data["sig"] = signature  # Remettre la signature
            token_data["valid"] = True
            return token_data
            
        except (ValueError, TypeError, base64.binascii.Error, json.JSONDecodeError):
            return {"valid": False, "reason": "token_malformed"}
    
    @staticmethod
    def _generate_signature(data):
        """
        Génère une signature pour les données du token.
        
        Args:
            data: Données Ã  signer
            
        Returns:
            str: Signature hexadécimale
        """
        # Créer une copie sans champs variables
        sign_data = {k: v for k, v in data.items() if k not in ["sig", "jti"]}
        
        # Canonicaliser les données
        canonical = json.dumps(sign_data, sort_keys=True)
        
        # Générer la signature HMAC
        key = f"{HASH_SECRET}_{sign_data.get('qr_uuid', '')}"
        signature = hashlib.sha256((canonical + key).encode()).hexdigest()
        
        return signature


class OfflineQRValidator:
    """
    Validateur de QR codes en mode hors-ligne.
    Permet de vérifier la validité d'un QR code sans accès au serveur.
    """
    
    @staticmethod
    def validate_qr_scan(token_data, scan_type, event_id=None):
        """
        Valide un scan QR en mode hors-ligne.
        
        Args:
            token_data: Données du token décodé
            scan_type: Type de scan (attendance, competition, etc.)
            event_id: ID de l'événement, compétition, etc.
            
        Returns:
            dict: Résultat de la validation
        """
        if not token_data.get("valid", False):
            return {
                "valid": False,
                "message": "Token invalide",
                "reason": token_data.get("reason", "unknown")
            }
        
        # Vérifier la validation fédération pour certains types
        if scan_type in ["competition", "event"] and not token_data.get("fed_val", False):
            return {
                "valid": False,
                "message": "Validation fédération requise pour ce type d'événement",
                "reason": "federation_validation_required"
            }
        
        # Vérifier la cohérence des données pour la compétition/événement
        if scan_type in ["competition", "event"] and event_id:
            # En mode hors-ligne, on ne peut pas vérifier si l'événement correspond
            # Nous enregistrons simplement cette information pour synchronisation ultérieure
            pass
        
        # Scan valide
        return {
            "valid": True,
            "message": "Scan validé (mode hors-ligne)",
            "practitioner_id": token_data.get("prac_id"),
            "qr_uuid": token_data.get("qr_uuid"),
            "timestamp": int(time.time()),
            "scan_type": scan_type,
            "event_id": event_id,
            "offline": True
        }


class OfflineProfileGenerator:
    """
    Générateur de profils pratiquants en mode hors-ligne.
    Permet d'accéder aux informations d'un pratiquant sans connexion au serveur.
    """
    
    @staticmethod
    def generate_offline_profile(practitioner):
        """
        Génère un token contenant les données du profil d'un pratiquant pour utilisation hors-ligne.
        
        Args:
            practitioner: Instance du modèle Practitioner
            
        Returns:
            dict: Données formatées et token pour le profil hors-ligne
        """
        # Générer les dates d'expiration
        now = timezone.now()
        expiry = now + timedelta(days=PROFILE_VALIDITY_DAYS)
        
        # Récupérer les données pertinentes du pratiquant avec des clés courtes pour économiser de l'espace
        profile_data = {
            "id": practitioner.id,  # Au lieu de "prac_id"
            "fn": practitioner.first_name,  # Au lieu de "first_name"
            "ln": practitioner.last_name,  # Au lieu de "last_name"
            "bd": practitioner.birth_date.isoformat() if practitioner.birth_date else None,
            "nat": practitioner.nationality,
            "lic": practitioner.license_number,
            "em": practitioner.email,
            "ph": practitioner.phone,
            "cl": {
                "id": practitioner.organization.id if practitioner.organization else None,
                "nm": practitioner.organization.name if practitioner.organization else None,
            },
            "gr": practitioner.grade_display,
            "ds": [
                {"id": d.id, "nm": d.name}
                for d in practitioner.disciplines.all()
            ],
            "pd": {
                "id": practitioner.primary_discipline.id if practitioner.primary_discipline else None,
                "nm": practitioner.primary_discipline.name if practitioner.primary_discipline else None,
            },
            "ic": practitioner.is_coach,  # is_coach
            "mcd": (
                practitioner.medical_certificate_date.isoformat() 
                if practitioner.medical_certificate_date 
                else None
            ),
            "med": (
                practitioner.membership_end_date.isoformat() 
                if practitioner.membership_end_date 
                else None
            ),
            "iat": int(now.timestamp()),  # Issued at
            "exp": int(expiry.timestamp()),  # Expiration
            "jti": str(uuid.uuid4()).replace("-", "")  # ID unique du token, sans les tirets
        }
        
        # Supprimer les valeurs None pour réduire la taille
        profile_data = {k: v for k, v in profile_data.items() if v is not None}
        
        # Ajouter signature de sécurité
        profile_data["sig"] = OfflineProfileGenerator._generate_profile_signature(profile_data)
        
        # Utiliser une compression JSON plus efficace (pas d'espaces ni de retours Ã  la ligne)
        token_json = json.dumps(profile_data, separators=(',', ':'))
        
        # Encoder en Base64
        token = base64.urlsafe_b64encode(token_json.encode()).decode()
        
        # Préparer les données Ã  retourner avec les noms de champs complets pour l'API
        full_profile_data = {
            "prac_id": practitioner.id,
            "first_name": practitioner.first_name,
            "last_name": practitioner.last_name,
            "birth_date": practitioner.birth_date.isoformat() if practitioner.birth_date else None,
            "nationality": practitioner.nationality,
            "license_number": practitioner.license_number,
            "email": practitioner.email,
            "phone": practitioner.phone,
            "club": {
                "id": practitioner.organization.id if practitioner.organization else None,
                "name": practitioner.organization.name if practitioner.organization else None,
            },
            "grade": practitioner.grade_display,
            "disciplines": [
                {"id": discipline.id, "name": discipline.name}
                for discipline in practitioner.disciplines.all()
            ],
            "primary_discipline": {
                "id": practitioner.primary_discipline.id if practitioner.primary_discipline else None,
                "name": practitioner.primary_discipline.name if practitioner.primary_discipline else None,
            },
            "is_coach": practitioner.is_coach,
            "medical_certificate_date": (
                practitioner.medical_certificate_date.isoformat() 
                if practitioner.medical_certificate_date 
                else None
            ),
            "membership_end_date": (
                practitioner.membership_end_date.isoformat() 
                if practitioner.membership_end_date 
                else None
            ),
            "iat": int(now.timestamp()),
            "exp": int(expiry.timestamp()),
            "jti": profile_data["jti"],
            "sig": profile_data["sig"]
        }
        
        return {
            "token": token,
            "profile_data": full_profile_data,  # Version complète pour l'API
            "generated_at": now.isoformat(),
            "expires_at": expiry.isoformat(),
            "compressed_size": len(token),  # Information sur la taille pour le débogage
            "compression_ratio": round(len(token) / len(json.dumps(full_profile_data)), 2)  # Ratio de compression
        }
    
    @staticmethod
    def verify_offline_profile(token):
        """
        Vérifie et décode un token de profil hors-ligne.
        
        Args:
            token: Token encodé du profil
            
        Returns:
            dict: Données du profil si valide, None sinon
        """
        try:
            # Décoder le token
            raw_data = base64.urlsafe_b64decode(token.encode()).decode()
            profile_data = json.loads(raw_data)
            
            # Extraire et vérifier la signature
            signature = profile_data.pop("sig", None)
            expected_signature = OfflineProfileGenerator._generate_profile_signature(profile_data)
            
            if not signature or signature != expected_signature:
                return {"valid": False, "reason": "signature_invalid"}
            
            # Vérifier l'expiration
            now = int(time.time())
            exp_time = profile_data.get("exp", 0)
            if exp_time < now:
                return {"valid": False, "reason": "token_expired"}
            
            # Remettre la signature
            profile_data["sig"] = signature
            
            # Convertir le format compressé au format complet
            full_profile = {
                "valid": True,
                "prac_id": profile_data.get("id"),
                "first_name": profile_data.get("fn"),
                "last_name": profile_data.get("ln"),
                "birth_date": profile_data.get("bd"),
                "nationality": profile_data.get("nat"),
                "license_number": profile_data.get("lic"),
                "email": profile_data.get("em"),
                "phone": profile_data.get("ph"),
                "club": {
                    "id": profile_data.get("cl", {}).get("id"),
                    "name": profile_data.get("cl", {}).get("nm")
                },
                "grade": profile_data.get("gr"),
                "disciplines": [
                    {"id": d.get("id"), "name": d.get("nm")}
                    for d in profile_data.get("ds", [])
                ],
                "primary_discipline": {
                    "id": profile_data.get("pd", {}).get("id"),
                    "name": profile_data.get("pd", {}).get("nm")
                },
                "is_coach": profile_data.get("ic", False),
                "medical_certificate_date": profile_data.get("mcd"),
                "membership_end_date": profile_data.get("med"),
                "iat": profile_data.get("iat"),
                "exp": exp_time,
                "jti": profile_data.get("jti"),
                "days_until_expiry": (exp_time - now) // (24 * 3600)  # Jours restants avant expiration
            }
            
            return full_profile
            
        except (ValueError, TypeError, base64.binascii.Error, json.JSONDecodeError) as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur de décodage du profil hors-ligne: {str(e)}")
            return {"valid": False, "reason": "token_malformed"}
    
    @staticmethod
    def _generate_profile_signature(data):
        """
        Génère une signature pour les données du profil.
        
        Args:
            data: Données Ã  signer
            
        Returns:
            str: Signature hexadécimale
        """
        # Créer une copie sans champs variables
        sign_data = {k: v for k, v in data.items() if k not in ["sig", "jti"]}
        
        # Canonicaliser les données
        canonical = json.dumps(sign_data, sort_keys=True)
        
        # Générer la signature HMAC
        profile_key = f"{HASH_SECRET}_profile_{sign_data.get('prac_id', '')}"
        signature = hashlib.sha256((canonical + profile_key).encode()).hexdigest()
        
        return signature
    
    @staticmethod
    def generate_profile_qr_image(practitioner):
        """
        Génère une image QR contenant le profil complet pour utilisation hors-ligne.
        
        Args:
            practitioner: Instance du modèle Practitioner
            
        Returns:
            tuple: (ContentFile de l'image, taille en octets)
        """
        try:
            import qrcode
            from io import BytesIO
            from PIL import Image
            
            # Générer les données du profil
            profile_data = OfflineProfileGenerator.generate_offline_profile(practitioner)
            token = profile_data["token"]
            
            # Créer un QR code avec une capacité élevée
            qr = qrcode.QRCode(
                version=20,  # La plus grande version (1-40)
                error_correction=qrcode.constants.ERROR_CORRECT_L,  # Pour maximiser la capacité
                box_size=10,
                border=4,
            )
            qr.add_data(token)
            qr.make(fit=True)
            
            # Créer l'image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Sauvegarder l'image dans un buffer
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            size = buffer.getbuffer().nbytes
            
            # Créer un ContentFile pour le stockage sur le modèle
            content_file = ContentFile(buffer.getvalue(), name=f"profile_{practitioner.id}_{uuid.uuid4()}.png")
            
            return content_file, size
            
        except ImportError:
            import logging
            logger = logging.getLogger(__name__)
            logger.error("Module qrcode non installé. Impossible de générer l'image QR du profil.")
            return None, 0


class OfflineQRStorage:
    """
    Stockage local pour les scans QR hors-ligne.
    Permet de stocker les scans en local jusqu'Ã  la synchronisation avec le serveur.
    """
    
    @staticmethod
    def store_offline_scan(scan_data):
        """
        Génère les données Ã  stocker pour un scan hors-ligne.
        Ã€ implémenter cÃ´té client (mobile).
        
        Args:
            scan_data: Données du scan validé
            
        Returns:
            dict: Données formatées pour stockage local
        """
        return {
            "id": str(uuid.uuid4()),
            "practitioner_id": scan_data.get("practitioner_id"),
            "qr_uuid": scan_data.get("qr_uuid"),
            "scan_type": scan_data.get("scan_type"),
            "event_id": scan_data.get("event_id"),
            "timestamp": scan_data.get("timestamp"),
            "location": scan_data.get("location", ""),
            "synced": False,
            "offline": True
        }
    
    @staticmethod
    def merge_offline_scans(offline_scans):
        """
        Fusionne les scans hors-ligne lors de la synchronisation.
        Ã€ implémenter cÃ´té serveur.
        
        Args:
            offline_scans: Liste des scans hors-ligne Ã  synchroniser
            
        Returns:
            tuple: (scans_créés, scans_ignorés)
        """
        from ..models import PractitionerQRCode, QRCodeScan
        
        created = 0
        ignored = 0
        
        for scan in offline_scans:
            try:
                # Vérifier si le scan a déjÃ  été synchronisé
                if QRCodeScan.objects.filter(
                    offline_scan_id=scan.get("id"),
                    is_offline_scan=True
                ).exists():
                    ignored += 1
                    continue
                    
                # Rechercher le QR code correspondant
                qr_code = PractitionerQRCode.objects.get(code=scan.get("qr_uuid"))
                
                # Vérifier si un scan similaire existe déjÃ  (vérification plus précise)
                existing_scan = QRCodeScan.objects.filter(
                    qr_code=qr_code,
                    scan_type=scan.get("scan_type"),
                    scan_date__range=(
                        timezone.datetime.fromtimestamp(scan.get("timestamp") - 300),  # -5 minutes
                        timezone.datetime.fromtimestamp(scan.get("timestamp") + 300)   # +5 minutes
                    )
                ).exists()
                
                if existing_scan:
                    ignored += 1
                    continue
                
                # Utiliser la méthode de création depuis les données hors-ligne
                QRCodeScan.create_from_offline_data(scan, qr_code)
                created += 1
                
            except PractitionerQRCode.DoesNotExist:
                ignored += 1
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Erreur lors de la synchronisation du scan hors-ligne: {e}")
                ignored += 1
        
        return (created, ignored)
