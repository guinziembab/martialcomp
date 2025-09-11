from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.conf import settings
from functools import wraps

from ..models.transactions import Transaction
from ..models.invoices import Invoice

def has_finance_permission(permission_codename):
    """
    Décorateur pour vérifier si l'utilisateur a une permission finance spécifique.
    
    Args:
        permission_codename (str): Le nom de code de la permission Ã  vérifier
    
    Returns:
        function: Décorateur qui vérifie la permission
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Vérifier si l'utilisateur est authentifié
            if not request.user.is_authenticated:
                messages.error(request, _("Vous devez Ãªtre connecté pour accéder Ã  cette page."))
                return redirect('login')
            
            # Vérifier si l'utilisateur a la permission spécifique
            if not request.user.has_perm(f'finances.{permission_codename}'):
                # Si superuser ou staff, autoriser l'accès automatiquement
                if request.user.is_superuser or request.user.is_staff:
                    return view_func(request, *args, **kwargs)
                
                # Vérifier les permissions spéciales selon l'entité
                entity_type = kwargs.get('entity_type')
                entity_id = kwargs.get('entity_id')
                
                if entity_type and entity_id:
                    has_access = check_entity_permission(
                        request.user, 
                        permission_codename, 
                        entity_type, 
                        entity_id
                    )
                    
                    if has_access:
                        return view_func(request, *args, **kwargs)
                
                # Si aucune vérification n'a réussi, refuser l'accès
                messages.error(request, _("Vous n'avez pas les permissions nécessaires pour accéder Ã  cette page."))
                return redirect('finances:dashboard')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def can_view_transaction(user, transaction):
    """
    Vérifie si l'utilisateur peut voir une transaction spécifique.
    
    Args:
        user (User): L'utilisateur Ã  vérifier
        transaction (Transaction): La transaction Ã  vérifier
        
    Returns:
        bool: True si l'utilisateur peut voir la transaction, False sinon
    """
    # Les superusers et staff peuvent voir toutes les transactions
    if user.is_superuser or user.is_staff:
        return True
    
    # L'utilisateur peut voir ses propres transactions
    if transaction.created_by == user:
        return True
    
    # Vérifier si l'utilisateur a la permission générale de voir toutes les transactions
    if user.has_perm('finances.view_all_transactions'):
        return True
    
    # Vérifier si l'utilisateur a des permissions spéciales selon l'entité associée
    if transaction.entity_content_type and transaction.entity_object_id:
        try:
            entity = transaction.entity_content_type.get_object_for_this_type(pk=transaction.entity_object_id)
            
            # Vérifier les permissions selon le type d'entité
            # Par exemple, si l'entité est une fédération, vérifier si l'utilisateur est administrateur
            if hasattr(entity, 'administrators'):
                if entity.administrators.filter(user=user).exists():
                    return True
            
            # Si l'entité est un club, vérifier si l'utilisateur est manager
            if hasattr(entity, 'managers'):
                if entity.managers.filter(user=user).exists():
                    return True
        except:
            pass
    
    return False


def can_validate_transaction(user, transaction):
    """
    Vérifie si l'utilisateur peut valider une transaction spécifique.
    
    Args:
        user (User): L'utilisateur Ã  vérifier
        transaction (Transaction): La transaction Ã  valider
        
    Returns:
        bool: True si l'utilisateur peut valider la transaction, False sinon
    """
    # Les superusers et staff peuvent valider toutes les transactions
    if user.is_superuser or user.is_staff:
        return True
    
    # Vérifier si l'utilisateur a la permission générale de valider toutes les transactions
    if user.has_perm('finances.validate_transaction'):
        return True
    
    # Vérifier si l'utilisateur a des permissions spéciales selon l'entité associée
    if transaction.entity_content_type and transaction.entity_object_id:
        try:
            entity = transaction.entity_content_type.get_object_for_this_type(pk=transaction.entity_object_id)
            
            # Vérifier selon le type d'entité
            # Par exemple, si l'entité est une fédération, vérifier si l'utilisateur est trésorier
            if hasattr(entity, 'administrators'):
                admin = entity.administrators.filter(user=user, role='treasurer').first()
                if admin:
                    return True
        except:
            pass
    
    return False


def can_view_invoice(user, invoice):
    """
    Vérifie si l'utilisateur peut voir une facture spécifique.
    
    Args:
        user (User): L'utilisateur Ã  vérifier
        invoice (Invoice): La facture Ã  vérifier
        
    Returns:
        bool: True si l'utilisateur peut voir la facture, False sinon
    """
    # Les superusers et staff peuvent voir toutes les factures
    if user.is_superuser or user.is_staff:
        return True
    
    # L'utilisateur peut voir les factures qu'il a créées
    if invoice.created_by == user:
        return True
    
    # Vérifier si l'utilisateur a la permission générale de voir toutes les factures
    if user.has_perm('finances.view_all_invoices'):
        return True
    
    # Vérifier l'émetteur de la facture
    if invoice.issuer_content_type and invoice.issuer_object_id:
        try:
            issuer = invoice.issuer_content_type.get_object_for_this_type(pk=invoice.issuer_object_id)
            
            # Vérifier selon le type d'émetteur
            if hasattr(issuer, 'administrators'):
                if issuer.administrators.filter(user=user).exists():
                    return True
        except:
            pass
    
    # Vérifier le destinataire de la facture
    if invoice.client_content_type and invoice.client_object_id:
        try:
            client = invoice.client_content_type.get_object_for_this_type(pk=invoice.client_object_id)
            
            # Vérifier selon le type de client
            if hasattr(client, 'managers'):
                if client.managers.filter(user=user).exists():
                    return True
        except:
            pass
    
    return False


def check_entity_permission(user, permission, entity_type, entity_id):
    """
    Vérifie si l'utilisateur a une permission spécifique sur une entité.
    
    Args:
        user (User): L'utilisateur Ã  vérifier
        permission (str): La permission Ã  vérifier
        entity_type (str): Le type d'entité (federation, club, etc.)
        entity_id (int): L'ID de l'entité
        
    Returns:
        bool: True si l'utilisateur a la permission, False sinon
    """
    try:
        # Importer les modèles selon le type d'entité
        if entity_type == 'federation':
            from apps.competitions.models import Federation
            entity = Federation.objects.get(pk=entity_id)
            
            # Vérifier si l'utilisateur est administrateur de la fédération
            is_admin = False
            if hasattr(entity, 'administrators'):
                is_admin = entity.administrators.filter(user=user).exists()
            
            # Vérifier si l'utilisateur est propriétaire
            is_owner = entity.owner == user if hasattr(entity, 'owner') else False
            
            if is_admin or is_owner:
                # Vérifier les permissions financières spécifiques
                if permission in ['view_transaction', 'view_invoice', 'view_financial_dashboard']:
                    return True
                    
                # Pour les permissions plus sensibles, vérifier le rÃ´le d'administrateur
                if hasattr(entity, 'administrators'):
                    admin = entity.administrators.filter(user=user).first()
                    if admin and admin.role in ['treasurer', 'owner', 'president']:
                        return True
        
        elif entity_type == 'club':
            from apps.competitions.models import Club
            entity = Club.objects.get(pk=entity_id)
            
            # Vérifier si l'utilisateur est manager du club
            is_manager = False
            if hasattr(entity, 'managers'):
                is_manager = entity.managers.filter(user=user).exists()
            
            # Vérifier si l'utilisateur est propriétaire
            is_owner = entity.owner == user if hasattr(entity, 'owner') else False
            
            if is_manager or is_owner:
                # Vérifier les permissions financières spécifiques
                if permission in ['view_transaction', 'view_invoice', 'view_financial_dashboard']:
                    return True
                
                # Pour les permissions plus sensibles, vérifier le rÃ´le de manager
                if hasattr(entity, 'managers'):
                    manager = entity.managers.filter(user=user).first()
                    if manager and manager.role in ['treasurer', 'owner', 'president']:
                        return True
    except:
        pass
    
    return False


def finance_dashboard_required(view_func):
    """
    Décorateur pour vérifier si l'utilisateur peut accéder au tableau de bord financier.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Vérifier si l'utilisateur est authentifié
        if not request.user.is_authenticated:
            messages.error(request, _("Vous devez Ãªtre connecté pour accéder Ã  cette page."))
            return redirect('login')
        
        # Les superusers et staff peuvent accéder
        if request.user.is_superuser or request.user.is_staff:
            return view_func(request, *args, **kwargs)
        
        # Vérifier si l'utilisateur a la permission générale
        if request.user.has_perm('finances.view_dashboard'):
            return view_func(request, *args, **kwargs)
        
        # Vérifier les permissions spéciales selon l'entité
        entity_type = kwargs.get('entity_type')
        entity_id = kwargs.get('entity_id')
        
        if entity_type and entity_id:
            has_access = check_entity_permission(
                request.user, 
                'view_financial_dashboard', 
                entity_type, 
                entity_id
            )
            
            if has_access:
                return view_func(request, *args, **kwargs)
        
        # Si aucune vérification n'a réussi, refuser l'accès
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour accéder au tableau de bord financier."))
        return redirect('finances:dashboard')
        
    return _wrapped_view


def transaction_action_required(action):
    """
    Décorateur pour vérifier si l'utilisateur peut effectuer une action sur une transaction.
    
    Args:
        action (str): L'action Ã  vérifier (validate, reject, cancel)
    
    Returns:
        function: Décorateur qui vérifie la permission
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, pk, *args, **kwargs):
            # Vérifier si l'utilisateur est authentifié
            if not request.user.is_authenticated:
                messages.error(request, _("Vous devez Ãªtre connecté pour accéder Ã  cette page."))
                return redirect('login')
            
            # Récupérer la transaction
            try:
                transaction = Transaction.objects.get(pk=pk)
            except Transaction.DoesNotExist:
                messages.error(request, _("Transaction introuvable."))
                return redirect('finances:transaction_list')
            
            # Vérifier l'action demandée
            if action == 'validate':
                if not can_validate_transaction(request.user, transaction):
                    messages.error(request, _("Vous n'avez pas les permissions nécessaires pour valider cette transaction."))
                    return redirect('finances:transaction_detail', pk=transaction.pk)
            
            elif action == 'reject':
                if not can_validate_transaction(request.user, transaction):
                    messages.error(request, _("Vous n'avez pas les permissions nécessaires pour rejeter cette transaction."))
                    return redirect('finances:transaction_detail', pk=transaction.pk)
            
            elif action == 'cancel':
                # Seul le créateur ou un administrateur peut annuler
                if not (transaction.created_by == request.user or request.user.is_superuser or request.user.has_perm('finances.cancel_transaction')):
                    messages.error(request, _("Vous n'avez pas les permissions nécessaires pour annuler cette transaction."))
                    return redirect('finances:transaction_detail', pk=transaction.pk)
            
            return view_func(request, pk, *args, **kwargs)
        return _wrapped_view
    return decorator

