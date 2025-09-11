"""
Module d'utilitaires pour la génération de QR codes.
Ce module fournit des fonctions pour générer des QR codes pour différentes entités
(clubs, fédérations, coachs) avec des identifiants uniques et des liens d'inscription.
"""
import os
import uuid
import qrcode
from io import BytesIO
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils.text import slugify

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

def generate_qr_code_url(entity_type, entity_id, action='register', data=None):
    """
    Génère une URL pour le QR code qui pointera vers la page appropriée.
    
    Args:
        entity_type: Type d'entité (club, federation, coach)
        entity_id: ID de l'entité
        action: Action Ã  effectuer (register, view, etc.)
        data: Données additionnelles Ã  inclure
        
    Returns:
        URL Ã  encoder dans le QR code
    """
    base_url = settings.BASE_URL
    unique_id = generate_unique_id()
    
    if action == 'register':
        url = f"{base_url}/signup/{entity_type}/{entity_id}/?qr={unique_id}"
    elif action == 'payment':
        url = f"{base_url}/payment/{entity_type}/{entity_id}/?qr={unique_id}"
    elif action == 'referral' and data and 'referrer_id' in data:
        url = f"{base_url}/signup/{entity_type}/{entity_id}/?ref={data['referrer_id']}"
    else:
        url = f"{base_url}/{entity_type}/{entity_id}/?qr={unique_id}"
        
    return url

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
        error_correction=qrcode.constants.ERROR_CORRECTION_H,
        box_size=size,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
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

def generate_qr_code_for_entity(entity, entity_type, action='register', data=None):
    """
    Génère un QR code pour une entité donnée et le sauvegarde.
    
    Args:
        entity: Instance de l'entité (Club, Federation, Coach)
        entity_type: Type d'entité ('club', 'federation', 'coach')
        action: Action Ã  effectuer lors du scan
        data: Données additionnelles
        
    Returns:
        Tuple (URL, chemin relatif vers l'image)
    """
    # Générer l'URL
    url = generate_qr_code_url(entity_type, entity.id, action, data)
    
    # Créer l'image QR code
    img = create_qr_code_image(url)
    
    # Définir un nom de fichier
    entity_name = getattr(entity, 'name', '') or getattr(entity, 'title', '')
    filename = f"qr_{entity_type}_{slugify(entity_name)}_{uuid.uuid4()}.png"
    
    # Sauvegarder l'image
    file_path = save_qr_code(img, entity_type, entity.id, filename)
    
    return url, file_path

def generate_qr_code_for_model(model_instance, field_name='qr_code'):
    """
    Génère un QR code pour un modèle et enregistre le chemin dans un champ spécifié.
    
    Args:
        model_instance: Instance du modèle
        field_name: Nom du champ ImageField oÃ¹ stocker le QR code
        
    Returns:
        Chemin vers l'image du QR code
    """
    # Déterminer le type d'entité
    if hasattr(model_instance, '__class__') and hasattr(model_instance.__class__, '__name__'):
        entity_type = model_instance.__class__.__name__.lower()
    else:
        entity_type = 'entity'
    
    # Générer l'URL
    url = generate_qr_code_url(entity_type, model_instance.id)
    
    # Créer l'image QR code
    img = create_qr_code_image(url)
    
    # Convertir l'image en bytes
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    
    # Générer un nom de fichier
    filename = f"qr_{entity_type}_{model_instance.id}.png"
    
    # Enregistrer l'image dans le champ
    if hasattr(model_instance, field_name):
        field = getattr(model_instance, field_name)
        field.save(filename, ContentFile(buffer.read()), save=False)
        model_instance.save(update_fields=[field_name])
        
    # Ã‰galement sauvegarder l'image sur le disque
    file_path = save_qr_code(img, entity_type, model_instance.id, filename)
    
    return file_path
