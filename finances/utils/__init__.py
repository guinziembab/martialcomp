import uuid
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from django.contrib.auth.models import User
from django.conf import settings

def get_financial_permissions(user):
    """
    Retourne un dictionnaire des permissions financières pour un utilisateur.
    
    Args:
        user (User): L'utilisateur pour lequel vérifier les permissions
        
    Returns:
        dict: Dictionnaire contenant les permissions financières
    """
    if not user.is_authenticated:
        return {
            'can_view_dashboard': False,
            'can_view_transactions': False,
            'can_add_transactions': False,
            'can_validate_transactions': False,
            'can_view_all_transactions': False,
            'can_view_invoices': False,
            'can_create_invoices': False,
            'can_view_all_invoices': False,
            'can_process_payment': False,
            'can_view_reports': False,
            'can_view_accounts': False,
            'can_manage_accounts': False,
            'can_approve_all_transactions': False,
        }
    
    # Vérifier si l'utilisateur a un rôle spécifique
    is_admin_role = False
    user_role = None
    
    if hasattr(user, 'userprofile') and hasattr(user.userprofile, 'role'):
        user_role = user.userprofile.role
        admin_roles = ['federation_admin', 'club_admin', 'club_owner', 'club_manager', 'coach']
        is_admin_role = user_role in admin_roles
    
    # Permissions de base pour un utilisateur authentifié
    perms = {
        'can_view_dashboard': True,
        'can_view_transactions': True,
        'can_add_transactions': is_admin_role,  # Autorisé pour les rôles administratifs
        'can_validate_transactions': is_admin_role,  # Autorisé pour les rôles administratifs
        'can_view_all_transactions': is_admin_role,  # Autorisé pour les rôles administratifs
        'can_view_invoices': True,
        'can_create_invoices': is_admin_role,  # Autorisé pour les rôles administratifs
        'can_view_all_invoices': is_admin_role,  # Autorisé pour les rôles administratifs
        'can_process_payment': is_admin_role,  # Autorisé pour les rôles administratifs
        'can_view_reports': is_admin_role,  # Autorisé pour les rôles administratifs
        'can_view_accounts': is_admin_role,  # Autorisé pour les rôles administratifs
        'can_manage_accounts': is_admin_role and user_role in ['federation_admin', 'club_admin', 'club_owner'],  # Plus restreint
        'can_approve_all_transactions': is_admin_role and user_role in ['federation_admin', 'club_admin', 'club_owner'],  # Plus restreint
    }
    
    # Vérifier les permissions spécifiques
    if user.has_perm('finances.add_transaction'):
        perms['can_add_transactions'] = True
        
    if user.has_perm('finances.validate_transaction'):
        perms['can_validate_transactions'] = True
        
    if user.has_perm('finances.view_all_transactions'):
        perms['can_view_all_transactions'] = True
        
    if user.has_perm('finances.add_invoice'):
        perms['can_create_invoices'] = True
        
    if user.has_perm('finances.view_all_invoices'):
        perms['can_view_all_invoices'] = True
        
    if user.has_perm('finances.process_payment'):
        perms['can_process_payment'] = True
        
    if user.has_perm('finances.view_reports'):
        perms['can_view_reports'] = True
        
    if user.has_perm('finances.view_financialaccount'):
        perms['can_view_accounts'] = True
        
    if user.has_perm('finances.change_financialaccount'):
        perms['can_manage_accounts'] = True
        
    if user.has_perm('finances.approve_all_transactions'):
        perms['can_approve_all_transactions'] = True
    
    # Permissions pour les superutilisateurs
    if user.is_superuser:
        for key in perms:
            perms[key] = True
    
    # Vérifier si l'utilisateur a un rôle spécifique dans le système
    # Cela dépendra de l'implémentation des rôles dans votre application
    
    return perms


def generate_unique_id():
    """
    Génère un identifiant unique UUID.
    
    Returns:
        str: Chaîne UUID unique
    """
    return str(uuid.uuid4())


def render_to_pdf(template_src, context_dict=None):
    """
    Génère un PDF à partir d'un template HTML et d'un contexte.
    
    Args:
        template_src (str): Contenu HTML du template
        context_dict (dict, optional): Contexte pour le rendu du template
    
    Returns:
        HttpResponse: Réponse HTTP contenant le PDF ou None en cas d'erreur
    """
    if context_dict is None:
        context_dict = {}
    
    try:
        # Utiliser xhtml2pdf pour convertir HTML en PDF
        from xhtml2pdf import pisa
        
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(template_src.encode("UTF-8")), result)
        
        if not pdf.err:
            return result.getvalue()
        return None
    except Exception as e:
        # Fallback si xhtml2pdf n'est pas disponible ou échoue
        try:
            # Utiliser weasyprint comme alternative
            from weasyprint import HTML, CSS
            
            html = HTML(string=template_src)
            result = html.write_pdf()
            return result
        except:
            # Si toutes les méthodes échouent
            return None