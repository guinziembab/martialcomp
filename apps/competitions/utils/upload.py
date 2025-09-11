import os
import uuid
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from PIL import Image
from io import BytesIO

def handle_uploaded_image(uploaded_file, destination_path, max_size=None, thumbnail_size=None):
    """
    Traite une image téléchargée en la redimensionnant si nécessaire et en la sauvegardant.
    
    Args:
        uploaded_file: Fichier téléchargé (request.FILES['field_name'])
        destination_path: Chemin de destination dans le stockage
        max_size: Tuple (width, height) pour redimensionner l'image
        thumbnail_size: Tuple (width, height) pour générer une miniature
        
    Returns:
        Chemin du fichier enregistré dans le système de stockage
    """
    # Génère un nom de fichier unique pour éviter les collisions
    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # Chemin complet de destination
    dest_path = os.path.join(destination_path, unique_filename)
    
    # Si aucun traitement spécial n'est requis, sauvegarde directement le fichier
    if not max_size and not thumbnail_size:
        return default_storage.save(dest_path, uploaded_file)
    
    # Ouvre l'image avec PIL
    img = Image.open(uploaded_file)
    
    # Convertit en RGB si c'est une image RGBA (pour les JPEG)
    if img.mode == 'RGBA' and file_extension in ['.jpg', '.jpeg']:
        img = img.convert('RGB')
    
    # Redimensionne l'image si max_size est spécifié
    if max_size:
        img.thumbnail(max_size, Image.LANCZOS)
    
    # Sauvegarde l'image principale
    img_io = BytesIO()
    
    # Détermine le format en fonction de l'extension
    if file_extension == '.png':
        img.save(img_io, format='PNG', optimize=True)
    elif file_extension in ['.jpg', '.jpeg']:
        img.save(img_io, format='JPEG', quality=85, optimize=True)
    elif file_extension == '.gif':
        img.save(img_io, format='GIF')
    elif file_extension == '.webp':
        img.save(img_io, format='WEBP', quality=85)
    elif file_extension == '.svg':
        # SVG est un format vectoriel, on le sauvegarde directement
        return default_storage.save(dest_path, uploaded_file)
    else:
        # Format non reconnu, on sauvegarde directement
        return default_storage.save(dest_path, uploaded_file)
    
    img_io.seek(0)
    saved_path = default_storage.save(dest_path, ContentFile(img_io.read()))
    
    # Génère la miniature si demandé
    if thumbnail_size:
        thumb = img.copy()
        thumb.thumbnail(thumbnail_size, Image.LANCZOS)
        
        thumb_io = BytesIO()
        
        # MÃªme format que l'image principale
        if file_extension == '.png':
            thumb.save(thumb_io, format='PNG', optimize=True)
        elif file_extension in ['.jpg', '.jpeg']:
            thumb.save(thumb_io, format='JPEG', quality=85, optimize=True)
        elif file_extension == '.gif':
            thumb.save(thumb_io, format='GIF')
        elif file_extension == '.webp':
            thumb.save(thumb_io, format='WEBP', quality=85)
        
        thumb_io.seek(0)
        
        # Chemin de la miniature (ajout de _thumb avant l'extension)
        thumb_path = os.path.join(
            destination_path, 
            os.path.splitext(unique_filename)[0] + '_thumb' + file_extension
        )
        default_storage.save(thumb_path, ContentFile(thumb_io.read()))
    
    return saved_path

def handle_federation_logo_upload(uploaded_file, federation_name):
    """
    Fonction utilitaire spécifique pour traiter les logos de fédération.
    
    Args:
        uploaded_file: Fichier logo téléchargé
        federation_name: Nom de la fédération pour le nommage
        
    Returns:
        Chemin du fichier logo enregistré
    """
    max_size = (400, 400)  # Taille max pour les logos
    thumbnail_size = (150, 150)  # Taille de la miniature
    
    # Destination spécifique pour les logos de fédération
    destination_path = 'federations/logos/'
    
    return handle_uploaded_image(
        uploaded_file, 
        destination_path, 
        max_size=max_size, 
        thumbnail_size=thumbnail_size
    )

def handle_club_logo_upload(uploaded_file, club_name):
    """
    Fonction utilitaire spécifique pour traiter les logos de club.
    
    Args:
        uploaded_file: Fichier logo téléchargé
        club_name: Nom du club pour le nommage
        
    Returns:
        Chemin du fichier logo enregistré
    """
    max_size = (400, 400)  # Taille max pour les logos
    thumbnail_size = (150, 150)  # Taille de la miniature
    
    # Destination spécifique pour les logos de club
    destination_path = 'clubs/logos/'
    
    return handle_uploaded_image(
        uploaded_file, 
        destination_path, 
        max_size=max_size, 
        thumbnail_size=thumbnail_size
    )
