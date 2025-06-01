from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from functools import wraps

from .models import Family, FamilyMember


def family_access_required(view_func):
    """
    Décorateur pour vérifier l'accès à une famille.
    L'utilisateur doit être soit le responsable principal, soit un membre actif de la famille.
    """
    @wraps(view_func)
    def wrapper(request, family_id, *args, **kwargs):
        family = get_object_or_404(Family, id=family_id)
        
        # Vérifier l'accès
        has_access = (
            family.primary_responsible == request.user or
            family.members.filter(user=request.user, is_active=True).exists() or
            request.user.is_staff or
            request.user.is_superuser
        )
        
        if not has_access:
            raise PermissionDenied("Vous n'avez pas accès à cette famille.")
        
        # Ajouter la famille au request pour éviter une nouvelle requête
        request.family = family
        return view_func(request, family_id, *args, **kwargs)
    
    return wrapper


def family_management_required(view_func):
    """
    Décorateur pour vérifier les permissions de gestion d'une famille.
    L'utilisateur doit avoir les droits de gestion sur la famille.
    """
    @wraps(view_func)
    def wrapper(request, family_id, *args, **kwargs):
        family = get_object_or_404(Family, id=family_id)
        
        # Vérifier les permissions de gestion
        has_management = False
        
        # Responsable principal
        if family.primary_responsible == request.user:
            has_management = True
        
        # Membre avec permissions de gestion
        member = family.members.filter(user=request.user, is_active=True).first()
        if member and member.has_permission('manage_family'):
            has_management = True
        
        # Admin/staff
        if request.user.is_staff or request.user.is_superuser:
            has_management = True
        
        if not has_management:
            raise PermissionDenied("Vous n'avez pas les permissions pour gérer cette famille.")
        
        # Ajouter la famille et le membre au request
        request.family = family
        request.family_member = member
        return view_func(request, family_id, *args, **kwargs)
    
    return wrapper


def family_payment_required(view_func):
    """
    Décorateur pour vérifier les permissions de paiement d'une famille.
    """
    @wraps(view_func)
    def wrapper(request, family_id, *args, **kwargs):
        family = get_object_or_404(Family, id=family_id)
        
        # Vérifier les permissions de paiement
        has_payment_permission = False
        
        # Responsable principal
        if family.primary_responsible == request.user:
            has_payment_permission = True
        
        # Membre avec permissions de paiement
        member = family.members.filter(user=request.user, is_active=True).first()
        if member and member.has_permission('make_payments'):
            has_payment_permission = True
        
        # Admin/staff
        if request.user.is_staff or request.user.is_superuser:
            has_payment_permission = True
        
        if not has_payment_permission:
            raise PermissionDenied("Vous n'avez pas les permissions pour effectuer des paiements pour cette famille.")
        
        request.family = family
        request.family_member = member
        return view_func(request, family_id, *args, **kwargs)
    
    return wrapper


def can_register_family_members(view_func):
    """
    Décorateur pour vérifier les permissions d'inscription des membres d'une famille.
    """
    @wraps(view_func)
    def wrapper(request, family_id, *args, **kwargs):
        family = get_object_or_404(Family, id=family_id)
        
        # Vérifier les permissions d'inscription
        has_registration_permission = False
        
        # Responsable principal
        if family.primary_responsible == request.user:
            has_registration_permission = True
        
        # Membre avec permissions d'inscription
        member = family.members.filter(user=request.user, is_active=True).first()
        if member and member.has_permission('register_members'):
            has_registration_permission = True
        
        # Admin/staff
        if request.user.is_staff or request.user.is_superuser:
            has_registration_permission = True
        
        if not has_registration_permission:
            raise PermissionDenied("Vous n'avez pas les permissions pour inscrire les membres de cette famille.")
        
        request.family = family
        request.family_member = member
        return view_func(request, family_id, *args, **kwargs)
    
    return wrapper


class FamilyPermissionMixin:
    """
    Mixin pour les vues basées sur les classes afin de gérer les permissions familiales.
    """
    
    def dispatch(self, request, *args, **kwargs):
        family_id = kwargs.get('family_id')
        if family_id:
            self.family = get_object_or_404(Family, id=family_id)
            
            # Vérifier l'accès de base
            if not self.has_family_access(request.user):
                raise PermissionDenied("Vous n'avez pas accès à cette famille.")
            
            # Vérifier les permissions spécifiques si nécessaire
            if hasattr(self, 'required_permission'):
                if not self.has_family_permission(request.user, self.required_permission):
                    raise PermissionDenied(f"Permission requise: {self.required_permission}")
        
        return super().dispatch(request, *args, **kwargs)
    
    def has_family_access(self, user):
        """Vérifie l'accès de base à la famille"""
        return (
            self.family.primary_responsible == user or
            self.family.members.filter(user=user, is_active=True).exists() or
            user.is_staff or
            user.is_superuser
        )
    
    def has_family_permission(self, user, permission):
        """Vérifie une permission spécifique sur la famille"""
        # Responsable principal a toutes les permissions
        if self.family.primary_responsible == user:
            return True
        
        # Admin/staff ont toutes les permissions
        if user.is_staff or user.is_superuser:
            return True
        
        # Vérifier les permissions du membre
        member = self.family.members.filter(user=user, is_active=True).first()
        return member and member.has_permission(permission)
    
    def get_context_data(self, **kwargs):
        """Ajoute les données de la famille au contexte"""
        context = super().get_context_data(**kwargs)
        if hasattr(self, 'family'):
            context['family'] = self.family
            context['can_manage'] = self.has_family_permission(self.request.user, 'manage_family')
            context['can_make_payments'] = self.has_family_permission(self.request.user, 'make_payments')
            context['can_register_members'] = self.has_family_permission(self.request.user, 'register_members')
        return context


def get_user_families(user):
    """
    Récupère toutes les familles auxquelles un utilisateur a accès.
    Retourne un dictionnaire avec les familles gérées et les familles membres.
    """
    managed_families = Family.objects.filter(
        primary_responsible=user,
        is_active=True
    )
    
    member_families = Family.objects.filter(
        members__user=user,
        members__is_active=True,
        is_active=True
    ).exclude(primary_responsible=user).distinct()
    
    return {
        'managed': managed_families,
        'member': member_families,
        'all': (managed_families | member_families).distinct()
    }