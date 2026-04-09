"""
Module d'utilitaires pour la génération de QR codes enhanced.
Ce module fournit des fonctions pour générer des QR codes pour différentes entités
(clubs, fédérations, coachs) avec des identifiants uniques et des liens d'inscription.
Support intégré des sous-domaines multi-tenant.
"""
import os
import uuid
import qrcode
from io import BytesIO
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils.text import slugify
from .subdomain_generator import SubdomainGenerator

def generate_unique_id():
    """Génère un identifiant unique pour le QR code."""
    return str(uuid.uuid4())

def generate_qr_code_data(entity_type, entity_id, action='register', data=None):
    """
    Génère les données Ã  encoder dans le QR code.
    
    Args:
        entity_type: Type d'entité (club, federation, coach)
        entity_id: ID de l'entité
        action: Action Ã  effectuer (register, view, etc.)
        data: Données additionnelles Ã  inclure
        
    Returns:
        Un dictionnaire avec les données Ã  encoder
    """
    payload = {
        'type': entity_type,
        'id': entity_id,
        'action': action,
        'unique_id': generate_unique_id()
    }
    
    if data:
        payload.update(data)
        
    return payload

def generate_qr_code_url(entity_type, entity_id, action='register', data=None, use_subdomain=True):
    """
    Génère une URL pour le QR code qui pointera vers la page appropriée.
    
    Args:
        entity_type: Type d'entité (club, federation, coach)
        entity_id: ID de l'entité
        action: Action Ã  effectuer (register, view, etc.)
        data: Données additionnelles Ã  inclure
        use_subdomain: Utiliser le sous-domaine de l'organisation (défaut: True)
        
    Returns:
        URL Ã  encoder dans le QR code
    """
    unique_id = generate_unique_id()
    
    # Essayer d'utiliser le sous-domaine si demandé
    if use_subdomain:
        try:
            organization = _get_organization_by_type_and_id(entity_type, entity_id)
            if organization:
                generator = SubdomainGenerator()
                base_url = generator.get_organization_subdomain_url(organization).rstrip('/')
            else:
                base_url = settings.BASE_URL
        except Exception:
            # Fallback vers l'URL principale si erreur
            base_url = settings.BASE_URL
    else:
        base_url = settings.BASE_URL
    
    if action == 'register':
        # Lien d'inscription unifié par organisation
        url = f"{base_url}/signup/?qr={unique_id}&type={entity_type}&id={entity_id}"
    elif action == 'payment':
        url = f"{base_url}/payment/?qr={unique_id}&type={entity_type}&id={entity_id}"
    elif action == 'referral' and data and 'referrer_id' in data:
        url = f"{base_url}/referral/?ref={data['referrer_id']}&type={entity_type}&id={entity_id}"
    elif action == 'check_in':
        # QR code pour le check-in rapide aux cours/événements
        url = f"{base_url}/check-in/?qr={unique_id}&type={entity_type}&id={entity_id}"
    elif action == 'profile':
        # QR code personnel du pratiquant
        url = f"{base_url}/profile/?qr={unique_id}&type={entity_type}&id={entity_id}"
    elif action == 'shop':
        # QR code pour la boutique du club
        url = f"{base_url}/shop/?qr={unique_id}&type={entity_type}&id={entity_id}"
    else:
        url = f"{base_url}/?qr={unique_id}&type={entity_type}&id={entity_id}"
        
    return url

def _get_organization_by_type_and_id(entity_type, entity_id):
    """
    Récupère l'organisation selon son type et son ID.
    
    Args:
        entity_type: Type d'entité (club, federation, coach, organization)
        entity_id: ID de l'entité
        
    Returns:
        Instance de l'organisation ou None
    """
    try:
        if entity_type == 'club':
            from apps.competitions.models import Club
            return Club.objects.get(id=entity_id)
        elif entity_type == 'federation':
            from apps.competitions.models import Federation
            return Federation.objects.get(id=entity_id)
        elif entity_type == 'organization':
            from apps.organizations.models import Organization
            return Organization.objects.get(id=entity_id)
        elif entity_type == 'coach':
            # Rechercher dans les profils coach
            from apps.competitions.models import CoachProfile
            coach = CoachProfile.objects.get(id=entity_id)
            return getattr(coach, 'organization', None)
    except Exception:
        pass
    return None

def create_qr_code_image(url, size=10, border=4):
    """
    Crée une image QR code Ã  partir d'une URL.
    
    Args:
        url: URL Ã  encoder
        size: Taille du QR code
        border: Largeur de la bordure
        
    Returns:
        Une image PIL
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=size,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    return img

def create_qr_code_with_logo(url, entity, size=10, border=4):
    """
    Crée un QR code avec le logo de l'organisation au centre.
    
    Args:
        url: URL Ã  encoder
        entity: Instance de l'entité pour récupérer le logo
        size: Taille du QR code
        border: Largeur de la bordure
        
    Returns:
        Une image PIL
    """
    from PIL import Image, ImageDraw
    
    # Créer le QR code de base
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # Haute correction pour logo
        box_size=size,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Essayer d'ajouter le logo si disponible
    try:
        logo_field = getattr(entity, 'logo', None) or getattr(entity, 'image', None)
        if logo_field and hasattr(logo_field, 'path') and os.path.exists(logo_field.path):
            logo = Image.open(logo_field.path)
            
            # Calculer la taille du logo (max 20% de la taille du QR code)
            qr_width, qr_height = img.size
            logo_size = min(qr_width, qr_height) // 5
            
            # Redimensionner le logo
            logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            
            # Créer un fond blanc rond pour le logo
            mask = Image.new('L', (logo_size + 20, logo_size + 20), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, logo_size + 20, logo_size + 20), fill=255)
            
            # Créer l'image de fond blanc
            white_bg = Image.new('RGB', (logo_size + 20, logo_size + 20), 'white')
            
            # Positionner le logo au centre
            logo_pos = ((qr_width - logo_size) // 2 - 10, (qr_height - logo_size) // 2 - 10)
            
            # Coller le fond blanc puis le logo
            img.paste(white_bg, logo_pos, mask)
            
            # Ajuster la position du logo
            logo_pos = ((qr_width - logo_size) // 2, (qr_height - logo_size) // 2)
            img.paste(logo, logo_pos)
            
    except Exception as e:
        # En cas d'erreur, retourner le QR code sans logo
        pass
    
    return img

def save_qr_code(img, entity_type, entity_id, filename=None):
    """
    Sauvegarde l'image QR code dans le système de fichiers.
    
    Args:
        img: Image PIL du QR code
        entity_type: Type d'entité
        entity_id: ID de l'entité
        filename: Nom de fichier (optionnel)
        
    Returns:
        Chemin vers le fichier sauvegardé
    """
    if filename is None:
        filename = f"qr_{entity_type}_{entity_id}_{uuid.uuid4()}.png"
        
    # Créer le dossier s'il n'existe pas
    qr_dir = os.path.join(settings.MEDIA_ROOT, 'qr_codes')
    os.makedirs(qr_dir, exist_ok=True)
    
    # Chemin complet du fichier
    file_path = os.path.join(qr_dir, filename)
    
    # Sauvegarder l'image
    img.save(file_path)
    
    # Chemin relatif pour le stockage en base de données
    relative_path = os.path.join('qr_codes', filename)
    return relative_path

def generate_qr_code_for_entity(entity, entity_type, action='register', data=None, use_subdomain=True, with_logo=False):
    """
    Génère un QR code pour une entité donnée et le sauvegarde.
    
    Args:
        entity: Instance de l'entité (Club, Federation, Coach)
        entity_type: Type d'entité ('club', 'federation', 'coach')
        action: Action Ã  effectuer lors du scan
        data: Données additionnelles
        use_subdomain: Utiliser le sous-domaine de l'organisation
        with_logo: Intégrer le logo de l'organisation au centre du QR code
        
    Returns:
        Tuple (URL, chemin relatif vers l'image)
    """
    # Générer l'URL
    url = generate_qr_code_url(entity_type, entity.id, action, data, use_subdomain)
    
    # Créer l'image QR code
    if with_logo:
        img = create_qr_code_with_logo(url, entity)
    else:
        img = create_qr_code_image(url)
    
    # Définir un nom de fichier
    entity_name = getattr(entity, 'name', '') or getattr(entity, 'title', '') or getattr(entity, 'nom', '')
    action_suffix = f"_{action}" if action != 'register' else ""
    filename = f"qr_{entity_type}_{slugify(entity_name)}{action_suffix}_{uuid.uuid4()}.png"
    
    # Sauvegarder l'image
    file_path = save_qr_code(img, entity_type, entity.id, filename)
    
    return url, file_path

def generate_qr_code_for_model(model_instance, field_name='qr_code', action='register', use_subdomain=True):
    """
    Génère un QR code pour un modèle et enregistre le chemin dans un champ spécifié.
    
    Args:
        model_instance: Instance du modèle
        field_name: Nom du champ ImageField oÃ¹ stocker le QR code
        action: Action Ã  effectuer lors du scan
        use_subdomain: Utiliser le sous-domaine de l'organisation
        
    Returns:
        Chemin vers l'image du QR code
    """
    # Déterminer le type d'entité
    if hasattr(model_instance, '__class__') and hasattr(model_instance.__class__, '__name__'):
        entity_type = model_instance.__class__.__name__.lower()
    else:
        entity_type = 'entity'
    
    # Générer l'URL
    url = generate_qr_code_url(entity_type, model_instance.id, action, use_subdomain=use_subdomain)
    
    # Créer l'image QR code avec logo si possible
    try:
        img = create_qr_code_with_logo(url, model_instance)
    except:
        img = create_qr_code_image(url)
    
    # Convertir l'image en bytes
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    
    # Générer un nom de fichier
    action_suffix = f"_{action}" if action != 'register' else ""
    filename = f"qr_{entity_type}_{model_instance.id}{action_suffix}.png"
    
    # Enregistrer l'image dans le champ
    if hasattr(model_instance, field_name):
        field = getattr(model_instance, field_name)
        field.save(filename, ContentFile(buffer.read()), save=False)
        model_instance.save(update_fields=[field_name])
        
    # Ã‰galement sauvegarder l'image sur le disque
    file_path = save_qr_code(img, entity_type, model_instance.id, filename)
    
    return file_path

# Nouvelles fonctions utilitaires pour QR codes spécialisés

def generate_practitioner_qr_code(practitioner, action='profile'):
    """
    Génère un QR code personnel pour un pratiquant.
    
    Args:
        practitioner: Instance du pratiquant
        action: Action (profile, check_in, etc.)
        
    Returns:
        Tuple (URL, chemin vers l'image)
    """
    return generate_qr_code_for_entity(practitioner, 'practitioner', action, use_subdomain=False)

def generate_event_qr_code(event, action='register'):
    """
    Génère un QR code pour un événement/compétition.
    
    Args:
        event: Instance de l'événement
        action: Action (register, info, etc.)
        
    Returns:
        Tuple (URL, chemin vers l'image)
    """
    return generate_qr_code_for_entity(event, 'event', action, use_subdomain=True)

def generate_course_qr_code(course, action='register'):
    """
    Génère un QR code pour un cours.
    
    Args:
        course: Instance du cours
        action: Action (register, check_in, etc.)
        
    Returns:
        Tuple (URL, chemin vers l'image)
    """
    return generate_qr_code_for_entity(course, 'course', action, use_subdomain=True)

def generate_organization_qr_codes_set(organization):
    """
    Génère un ensemble complet de QR codes pour une organisation.
    
    Args:
        organization: Instance de l'organisation
        
    Returns:
        Dict avec les différents QR codes générés
    """
    entity_type = organization._meta.model_name.lower()
    
    qr_codes = {}
    
    # QR code principal (page d'accueil)
    qr_codes['home'] = generate_qr_code_for_entity(
        organization, entity_type, 'home', use_subdomain=True, with_logo=True
    )
    
    # QR code d'inscription
    qr_codes['register'] = generate_qr_code_for_entity(
        organization, entity_type, 'register', use_subdomain=True, with_logo=True
    )
    
    # QR code de paiement/adhésion
    qr_codes['payment'] = generate_qr_code_for_entity(
        organization, entity_type, 'payment', use_subdomain=True, with_logo=True
    )
    
    # QR code avec parrainage (si applicable)
    referral_data = {'referrer_id': organization.id}
    qr_codes['referral'] = generate_qr_code_for_entity(
        organization, entity_type, 'referral', referral_data, use_subdomain=True, with_logo=True
    )

    # QR code pour la boutique du club
    qr_codes['shop'] = generate_qr_code_for_entity(
        organization, entity_type, 'shop', use_subdomain=True, with_logo=True
    )

    return qr_codes

def generate_temporary_qr_code(entity, entity_type, expiry_days=7, action='register'):
    """
    Génère un QR code temporaire avec expiration.
    
    Args:
        entity: Instance de l'entité
        entity_type: Type d'entité
        expiry_days: Nombre de jours avant expiration
        action: Action Ã  effectuer
        
    Returns:
        Tuple (URL, chemin vers l'image)
    """
    from datetime import datetime, timedelta
    
    expiry_date = datetime.now() + timedelta(days=expiry_days)
    data = {
        'expires': expiry_date.isoformat(),
        'temporary': True
    }
    
    return generate_qr_code_for_entity(entity, entity_type, action, data, use_subdomain=True)

# Fonctions de validation et sécurité

def validate_qr_code_data(qr_data):
    """
    Valide les données d'un QR code.
    
    Args:
        qr_data: Données extraites du QR code
        
    Returns:
        Tuple (valid, error_message)
    """
    if not isinstance(qr_data, dict):
        return False, "Format de données invalide"
    
    required_fields = ['type', 'id']
    for field in required_fields:
        if field not in qr_data:
            return False, f"Champ requis manquant: {field}"
    
    # Vérifier l'expiration si QR code temporaire
    if qr_data.get('temporary') and 'expires' in qr_data:
        try:
            from datetime import datetime
            expiry_date = datetime.fromisoformat(qr_data['expires'])
            if datetime.now() > expiry_date:
                return False, "QR code expiré"
        except:
            return False, "Format de date d'expiration invalide"
    
    return True, None

def get_qr_scan_analytics(organization, start_date=None, end_date=None):
    """
    Récupère les analytics de scan des QR codes pour une organisation.
    
    Args:
        organization: Instance de l'organisation
        start_date: Date de début (optionnel)
        end_date: Date de fin (optionnel)
        
    Returns:
        Dict avec les statistiques de scan
    """
    # Cette fonction nécessiterait l'implémentation d'un système de tracking
    # des scans dans la base de données
    return {
        'total_scans': 0,
        'unique_scans': 0,
        'conversion_rate': 0.0,
        'most_scanned_qr': None,
        'scan_by_date': []
    }

