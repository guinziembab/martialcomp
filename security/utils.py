import re
import hashlib
import logging
import secrets
from django.conf import settings

logger = logging.getLogger('security')

def generate_secure_token(length=32):
    """
    Génère un token cryptographiquement sécurisé.
    
    Args:
        length: Longueur du token en octets (par défaut 32 octets = 64 caractères hexadécimaux)
        
    Returns:
        Une chaîne hexadécimale représentant le token
    """
    return secrets.token_hex(length)

def hash_password(password, salt=None):
    """
    Hache un mot de passe avec un sel optionnel.
    
    Args:
        password: Le mot de passe à hacher
        salt: Le sel à utiliser (généré aléatoirement si non fourni)
        
    Returns:
        Un tuple (hachage, sel)
    """
    if salt is None:
        salt = secrets.token_hex(16)
    
    # Utilisation de PBKDF2 avec SHA-256
    dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    password_hash = dk.hex()
    
    return (password_hash, salt)

def validate_password_strength(password):
    """
    Valide la robustesse d'un mot de passe.
    
    Args:
        password: Le mot de passe à valider
        
    Returns:
        Un tuple (est_valide, message) où est_valide est un booléen et message est une chaîne
    """
    # Longueur minimale
    if len(password) < 8:
        return (False, "Le mot de passe doit contenir au moins 8 caractères.")
    
    # Au moins une lettre minuscule
    if not re.search(r'[a-z]', password):
        return (False, "Le mot de passe doit contenir au moins une lettre minuscule.")
    
    # Au moins une lettre majuscule
    if not re.search(r'[A-Z]', password):
        return (False, "Le mot de passe doit contenir au moins une lettre majuscule.")
    
    # Au moins un chiffre
    if not re.search(r'\d', password):
        return (False, "Le mot de passe doit contenir au moins un chiffre.")
    
    # Au moins un caractère spécial
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return (False, "Le mot de passe doit contenir au moins un caractère spécial.")
    
    return (True, "Mot de passe valide.")

def sanitize_input(input_string):
    """
    Nettoie une chaîne d'entrée pour éviter les injections.
    
    Args:
        input_string: La chaîne à nettoyer
        
    Returns:
        La chaîne nettoyée
    """
    if not isinstance(input_string, str):
        return input_string
    
    # Conversion des caractères HTML spéciaux
    sanitized = input_string.replace('&', '&amp;')
    sanitized = sanitized.replace('<', '&lt;')
    sanitized = sanitized.replace('>', '&gt;')
    sanitized = sanitized.replace('"', '&quot;')
    sanitized = sanitized.replace("'", '&#x27;')
    
    return sanitized

def is_path_traversal_attempt(path):
    """
    Vérifie si un chemin contient des tentatives de traversée de répertoire.
    
    Args:
        path: Le chemin à vérifier
        
    Returns:
        True si une tentative de traversée est détectée, False sinon
    """
    # Motifs de traversée de répertoire
    traversal_patterns = [
        '../', '..\\', '%2e%2e%2f', '%2e%2e/', '..%2f',
        '%2e%2e%5c', '..%5c', '%252e%252e%255c', '..%255c'
    ]
    
    return any(pattern in path for pattern in traversal_patterns)

def log_security_event(event_type, details, user=None, severity='INFO'):
    """
    Enregistre un événement de sécurité dans les logs.
    
    Args:
        event_type: Le type d'événement (authentification, autorisation, etc.)
        details: Les détails de l'événement
        user: L'utilisateur concerné (optionnel)
        severity: La gravité de l'événement (INFO, WARNING, ERROR, CRITICAL)
    """
    log_message = f"[{event_type}] "
    
    if user:
        if hasattr(user, 'username'):
            log_message += f"User: {user.username} "
        elif hasattr(user, 'email'):
            log_message += f"User: {user.email} "
        else:
            log_message += f"User ID: {user.id} "
    
    log_message += f"Details: {details}"
    
    if severity == 'INFO':
        logger.info(log_message)
    elif severity == 'WARNING':
        logger.warning(log_message)
    elif severity == 'ERROR':
        logger.error(log_message)
    elif severity == 'CRITICAL':
        logger.critical(log_message)