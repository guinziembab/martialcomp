# competitions/permissions/decorators.py
"""
Décorateurs pour la gestion des permissions dans MartialComp.
Ce module fournit des décorateurs réutilisables pour protéger les vues.
"""

from functools import wraps
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import PermissionDenied


def club_permission_required(permission):
    """
    Décorateur pour vérifier une permission dans le contexte du club actif.
    
    Usage:
        @login_required
        @club_permission_required('finance.view')
        def treasury_view(request):
            ...
    
    Args:
        permission: La permission requise (ex: 'finance.view')
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Vérifier l'authentification
            if not request.user.is_authenticated:
                return redirect('account_login')
            
            # Récupérer le club depuis le contexte
            club = getattr(request, 'current_club', None)
            if not club:
                messages.error(request, _("Aucun club sélectionné."))
                return redirect('dashboard:index')
            
            # Vérifier l'appartenance au club
            from competitions.models import ClubMember
            membership = ClubMember.objects.filter(
                user=request.user,
                club=club,
                status='active'
            ).select_related('role').first()
            
            if not membership:
                messages.error(request, _("Vous n'êtes pas membre de ce club."))
                return redirect('dashboard:index')
            
            # Vérifier la permission
            if not membership.has_permission(permission):
                messages.error(
                    request, 
                    _("Vous n'avez pas la permission requise pour cette action.")
                )
                return HttpResponseForbidden(
                    _("Permission refusée: %(permission)s") % {'permission': permission}
                )
            
            # Ajouter le membership au request pour usage ultérieur
            request.club_membership = membership
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def any_permission_required(*permissions):
    """
    Décorateur pour vérifier qu'au moins une des permissions est présente.
    
    Usage:
        @login_required
        @any_permission_required('finance.view', 'finance.edit')
        def finance_dashboard(request):
            ...
    
    Args:
        *permissions: Liste des permissions dont au moins une est requise
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('account_login')
            
            club = getattr(request, 'current_club', None)
            if not club:
                messages.error(request, _("Aucun club sélectionné."))
                return redirect('dashboard:index')
            
            from competitions.models import ClubMember
            membership = ClubMember.objects.filter(
                user=request.user,
                club=club,
                status='active'
            ).select_related('role').first()
            
            if not membership:
                messages.error(request, _("Vous n'êtes pas membre de ce club."))
                return redirect('dashboard:index')
            
            # Vérifier qu'au moins une permission est présente
            if not any(membership.has_permission(p) for p in permissions):
                messages.error(
                    request,
                    _("Vous n'avez pas les permissions requises pour cette action.")
                )
                return HttpResponseForbidden(_("Permission refusée"))
            
            request.club_membership = membership
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def all_permissions_required(*permissions):
    """
    Décorateur pour vérifier que toutes les permissions sont présentes.
    
    Usage:
        @login_required
        @all_permissions_required('finance.view', 'finance.approve')
        def approve_transaction(request):
            ...
    
    Args:
        *permissions: Liste des permissions toutes requises
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('account_login')
            
            club = getattr(request, 'current_club', None)
            if not club:
                messages.error(request, _("Aucun club sélectionné."))
                return redirect('dashboard:index')
            
            from competitions.models import ClubMember
            membership = ClubMember.objects.filter(
                user=request.user,
                club=club,
                status='active'
            ).select_related('role').first()
            
            if not membership:
                messages.error(request, _("Vous n'êtes pas membre de ce club."))
                return redirect('dashboard:index')
            
            # Vérifier que toutes les permissions sont présentes
            missing = [p for p in permissions if not membership.has_permission(p)]
            if missing:
                messages.error(
                    request,
                    _("Permissions manquantes: %(permissions)s") % {
                        'permissions': ', '.join(missing)
                    }
                )
                return HttpResponseForbidden(_("Permission refusée"))
            
            request.club_membership = membership
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def api_permission_required(permission):
    """
    Décorateur pour les vues API (retourne JSON au lieu de redirect).
    
    Usage:
        @login_required
        @api_permission_required('members.edit')
        def api_update_member(request, member_id):
            ...
    
    Args:
        permission: La permission requise
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({
                    'success': False,
                    'error': 'not_authenticated',
                    'message': str(_("Authentification requise."))
                }, status=401)
            
            club = getattr(request, 'current_club', None)
            
            if not club:
                return JsonResponse({
                    'success': False,
                    'error': 'no_club',
                    'message': str(_("Aucun club sélectionné."))
                }, status=400)
            
            from competitions.models import ClubMember
            membership = ClubMember.objects.filter(
                user=request.user,
                club=club,
                status='active'
            ).select_related('role').first()
            
            if not membership:
                return JsonResponse({
                    'success': False,
                    'error': 'not_member',
                    'message': str(_("Vous n'êtes pas membre de ce club."))
                }, status=403)
            
            if not membership.has_permission(permission):
                return JsonResponse({
                    'success': False,
                    'error': 'permission_denied',
                    'message': str(_("Permission refusée")),
                    'required_permission': permission
                }, status=403)
            
            request.club_membership = membership
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def api_any_permission_required(*permissions):
    """
    Décorateur API pour vérifier qu'au moins une permission est présente.
    
    Args:
        *permissions: Liste des permissions dont au moins une est requise
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({
                    'success': False,
                    'error': 'not_authenticated',
                    'message': str(_("Authentification requise."))
                }, status=401)
            
            club = getattr(request, 'current_club', None)
            
            if not club:
                return JsonResponse({
                    'success': False,
                    'error': 'no_club',
                    'message': str(_("Aucun club sélectionné."))
                }, status=400)
            
            from competitions.models import ClubMember
            membership = ClubMember.objects.filter(
                user=request.user,
                club=club,
                status='active'
            ).select_related('role').first()
            
            if not membership or not any(membership.has_permission(p) for p in permissions):
                return JsonResponse({
                    'success': False,
                    'error': 'permission_denied',
                    'message': str(_("Permission refusée")),
                    'required_permissions': list(permissions)
                }, status=403)
            
            request.club_membership = membership
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def role_required(*role_codes):
    """
    Décorateur pour vérifier qu'un utilisateur a un rôle spécifique.
    
    Usage:
        @login_required
        @role_required('owner', 'admin')
        def admin_settings(request):
            ...
    
    Args:
        *role_codes: Codes des rôles autorisés (ex: 'owner', 'admin', 'treasurer')
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('account_login')
            
            club = getattr(request, 'current_club', None)
            if not club:
                messages.error(request, _("Aucun club sélectionné."))
                return redirect('dashboard:index')
            
            from competitions.models import ClubMember
            membership = ClubMember.objects.filter(
                user=request.user,
                club=club,
                status='active'
            ).select_related('role').first()
            
            if not membership or not membership.role:
                messages.error(request, _("Vous n'avez pas de rôle dans ce club."))
                return redirect('dashboard:index')
            
            # Vérifier si le rôle principal ou un rôle additionnel correspond
            user_roles = [membership.role.code]
            user_roles.extend([r.code for r in membership.additional_roles.all()])
            
            if not any(r in role_codes for r in user_roles):
                messages.error(
                    request,
                    _("Cette action est réservée aux rôles: %(roles)s") % {
                        'roles': ', '.join(role_codes)
                    }
                )
                return HttpResponseForbidden(_("Rôle non autorisé"))
            
            request.club_membership = membership
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def federation_permission_required(permission):
    """
    Décorateur pour vérifier une permission dans le contexte de la fédération.
    
    Usage:
        @login_required
        @federation_permission_required('members.view')
        def federation_members(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('account_login')
            
            federation = getattr(request, 'current_federation', None)
            if not federation:
                messages.error(request, _("Aucune fédération sélectionnée."))
                return redirect('dashboard:index')
            
            from competitions.models import FederationMember
            membership = FederationMember.objects.filter(
                user=request.user,
                federation=federation,
                status='active'
            ).select_related('role').first()
            
            if not membership:
                messages.error(request, _("Vous n'êtes pas membre de cette fédération."))
                return redirect('dashboard:index')
            
            if not membership.has_permission(permission):
                messages.error(
                    request,
                    _("Vous n'avez pas la permission requise pour cette action.")
                )
                return HttpResponseForbidden(_("Permission refusée"))
            
            request.federation_membership = membership
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


class PermissionRequiredMixin:
    """
    Mixin pour les vues basées sur les classes.
    
    Usage:
        class TreasuryView(PermissionRequiredMixin, View):
            required_permission = 'finance.view'
            
            def get(self, request):
                ...
    """
    required_permission = None
    required_permissions = None  # Pour plusieurs permissions (toutes requises)
    any_permissions = None  # Pour plusieurs permissions (au moins une)
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        
        club = getattr(request, 'current_club', None)
        if not club:
            messages.error(request, _("Aucun club sélectionné."))
            return redirect('dashboard:index')
        
        from competitions.models import ClubMember
        membership = ClubMember.objects.filter(
            user=request.user,
            club=club,
            status='active'
        ).select_related('role').first()
        
        if not membership:
            messages.error(request, _("Vous n'êtes pas membre de ce club."))
            return redirect('dashboard:index')
        
        # Vérifier les permissions
        if self.required_permission and not membership.has_permission(self.required_permission):
            raise PermissionDenied(_("Permission refusée"))
        
        if self.required_permissions:
            if not all(membership.has_permission(p) for p in self.required_permissions):
                raise PermissionDenied(_("Permissions manquantes"))
        
        if self.any_permissions:
            if not any(membership.has_permission(p) for p in self.any_permissions):
                raise PermissionDenied(_("Aucune permission valide"))
        
        request.club_membership = membership
        return super().dispatch(request, *args, **kwargs)
