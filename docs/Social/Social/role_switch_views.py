# competitions/views/role_switch.py
"""
Vues pour la gestion du switch de contexte/rôle dans MartialComp.
Permet aux utilisateurs de basculer entre leurs différents rôles.
"""

import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _


@login_required
@require_GET
def get_available_contexts(request):
    """
    Retourne tous les contextes disponibles pour l'utilisateur.
    Utilisé pour le menu de switch de rôle dans le header.
    
    Returns:
        JsonResponse avec la structure:
        {
            'current': {...},  // Contexte actuellement actif
            'available': [...]  // Liste des contextes disponibles
        }
    """
    from competitions.models import ClubMember, FederationMember
    
    user = request.user
    contexts = {
        'current': request.session.get('active_context', {'type': 'practitioner'}),
        'available': []
    }
    
    # 1. Contexte Pratiquant (toujours disponible si profil existe)
    if hasattr(user, 'practitioners') and user.practitioners.exists():
        practitioner = user.practitioners.first()
        contexts['available'].append({
            'type': 'practitioner',
            'id': practitioner.id,
            'name': _('Pratiquant'),
            'subtitle': practitioner.full_name,
            'icon': 'fa-user',
            'color': '#3366ff',
            'dashboard_url': '/dashboard/participant/',
        })
    else:
        # Même sans profil Practitioner, permettre le contexte de base
        contexts['available'].append({
            'type': 'practitioner',
            'id': None,
            'name': _('Pratiquant'),
            'subtitle': user.get_full_name() or user.username,
            'icon': 'fa-user',
            'color': '#3366ff',
            'dashboard_url': '/dashboard/participant/',
        })
    
    # 2. Contexte Juge (si profil juge actif)
    if hasattr(user, 'judge_profile') and user.judge_profile and user.judge_profile.active:
        judge = user.judge_profile
        contexts['available'].append({
            'type': 'judge',
            'id': judge.id,
            'name': _('Juge'),
            'subtitle': judge.get_qualification_level_display(),
            'icon': 'fa-gavel',
            'color': '#ffc107',
            'dashboard_url': '/dashboard/judge/',
            'qualification_level': judge.qualification_level,
            'is_technical_judge': judge.is_technical_judge,
            'is_combat_referee': judge.is_combat_referee,
        })
    
    # 3. Contextes organisationnels (clubs)
    memberships = ClubMember.objects.filter(
        user=user,
        status='active'
    ).select_related('club', 'role').prefetch_related('additional_roles')
    
    for membership in memberships:
        if membership.role:
            # Calculer un aperçu des permissions
            perms = list(membership.effective_permissions)[:5]
            
            contexts['available'].append({
                'type': 'organizational',
                'id': membership.id,
                'club_id': membership.club.id,
                'name': membership.role.name,
                'subtitle': membership.club.name,
                'icon': membership.role.icon,
                'color': membership.role.color,
                'dashboard_url': _get_dashboard_url_for_role(membership.role.code),
                'permissions_preview': perms,
                'has_additional_roles': membership.additional_roles.exists(),
            })
    
    # 4. Contextes fédération
    fed_memberships = FederationMember.objects.filter(
        user=user,
        status='active'
    ).select_related('federation', 'role')
    
    for membership in fed_memberships:
        if membership.role:
            contexts['available'].append({
                'type': 'federation',
                'id': membership.id,
                'federation_id': membership.federation.id,
                'name': membership.role.name,
                'subtitle': membership.federation.name,
                'icon': 'fa-building',
                'color': '#1a365d',
                'dashboard_url': '/dashboard/federation/',
            })
    
    return JsonResponse(contexts)


@login_required
@require_POST
def switch_context(request):
    """
    Change le contexte actif de l'utilisateur.
    
    Body JSON attendu:
        {
            'type': 'practitioner' | 'judge' | 'organizational' | 'federation',
            'id': int | null  // ID du membership si organizational/federation
        }
    
    Returns:
        JsonResponse avec redirect_url et nouveau contexte
    """
    from competitions.models import ClubMember, FederationMember
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'invalid_json',
            'message': _('Format JSON invalide')
        }, status=400)
    
    context_type = data.get('type')
    context_id = data.get('id')
    
    # Valider et traiter selon le type de contexte
    if context_type == 'organizational' and context_id:
        try:
            membership = ClubMember.objects.select_related('club', 'role').get(
                id=context_id,
                user=request.user,
                status='active'
            )
            
            new_context = {
                'type': 'organizational',
                'id': context_id,
                'club_id': membership.club.id,
                'club_name': membership.club.name,
                'role': membership.role.code if membership.role else None,
                'role_name': membership.role.name if membership.role else _('Membre'),
                'switched_at': timezone.now().isoformat(),
            }
            
            request.session['active_context'] = new_context
            request.session['current_club_id'] = membership.club.id
            
            redirect_url = _get_dashboard_url_for_role(membership.role.code if membership.role else 'member')
            
        except ClubMember.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'invalid_membership',
                'message': _('Appartenance au club invalide ou inactive')
            }, status=400)
    
    elif context_type == 'federation' and context_id:
        try:
            membership = FederationMember.objects.select_related('federation', 'role').get(
                id=context_id,
                user=request.user,
                status='active'
            )
            
            new_context = {
                'type': 'federation',
                'id': context_id,
                'federation_id': membership.federation.id,
                'federation_name': membership.federation.name,
                'role': membership.role.code if membership.role else None,
                'role_name': membership.role.name if membership.role else _('Membre'),
                'switched_at': timezone.now().isoformat(),
            }
            
            request.session['active_context'] = new_context
            request.session['current_federation_id'] = membership.federation.id
            
            redirect_url = '/dashboard/federation/'
            
        except FederationMember.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'invalid_membership',
                'message': _('Appartenance à la fédération invalide ou inactive')
            }, status=400)
    
    elif context_type == 'judge':
        if hasattr(request.user, 'judge_profile') and request.user.judge_profile and request.user.judge_profile.active:
            judge = request.user.judge_profile
            new_context = {
                'type': 'judge',
                'id': judge.id,
                'qualification_level': judge.qualification_level,
                'switched_at': timezone.now().isoformat(),
            }
            request.session['active_context'] = new_context
            redirect_url = '/dashboard/judge/'
        else:
            return JsonResponse({
                'success': False,
                'error': 'no_judge_profile',
                'message': _('Profil juge non trouvé ou inactif')
            }, status=400)
    
    else:  # practitioner (défaut)
        new_context = {
            'type': 'practitioner',
            'switched_at': timezone.now().isoformat(),
        }
        request.session['active_context'] = new_context
        # Retirer le club/fédération courant du contexte
        request.session.pop('current_club_id', None)
        request.session.pop('current_federation_id', None)
        redirect_url = '/dashboard/participant/'
    
    return JsonResponse({
        'success': True,
        'redirect_url': redirect_url,
        'context': request.session['active_context']
    })


def _get_dashboard_url_for_role(role_code):
    """
    Retourne l'URL du dashboard approprié selon le rôle.
    
    Args:
        role_code: Code du rôle (ex: 'owner', 'treasurer', 'coach')
    
    Returns:
        URL du dashboard correspondant
    """
    role_dashboards = {
        'owner': '/dashboard/club/',
        'admin': '/dashboard/club/',
        'manager': '/dashboard/club/',
        'secretary': '/dashboard/club/',
        'treasurer': '/dashboard/club/finances/',
        'accountant': '/dashboard/club/finances/',
        'coach': '/dashboard/coach/',
        'judge': '/dashboard/judge/',
        'member': '/dashboard/club/',
    }
    return role_dashboards.get(role_code, '/dashboard/club/')


@login_required
def context_switcher_partial(request):
    """
    Retourne le HTML du composant context_switcher.
    Utile pour les mises à jour AJAX du header.
    """
    from competitions.models import ClubMember
    
    club_memberships = ClubMember.objects.filter(
        user=request.user,
        status='active'
    ).select_related('club', 'role')
    
    context = {
        'active_context': request.session.get('active_context', {'type': 'practitioner'}),
        'club_memberships': club_memberships,
    }
    
    return render(request, 'includes/context_switcher.html', context)


# ========== Context Processors ==========

def active_context_processor(request):
    """
    Context processor pour ajouter les informations de contexte actif
    à tous les templates.
    
    Ajouter dans settings.py:
        TEMPLATES = [{
            'OPTIONS': {
                'context_processors': [
                    ...
                    'competitions.views.role_switch.active_context_processor',
                ],
            },
        }]
    """
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return {}
    
    from competitions.models import ClubMember
    
    active_context = request.session.get('active_context', {'type': 'practitioner'})
    
    # Enrichir le contexte avec des informations supplémentaires
    context_data = {
        'active_context': active_context,
        'active_context_type': active_context.get('type', 'practitioner'),
    }
    
    # Ajouter les informations de membership si contexte organisationnel
    if active_context.get('type') == 'organizational' and active_context.get('id'):
        try:
            membership = ClubMember.objects.select_related('club', 'role').get(
                id=active_context['id'],
                user=request.user
            )
            context_data['active_membership'] = membership
            context_data['active_club'] = membership.club
            context_data['active_role'] = membership.role
            context_data['user_permissions'] = membership.effective_permissions
        except ClubMember.DoesNotExist:
            pass
    
    # Charger la liste des memberships pour le switcher
    context_data['user_club_memberships'] = ClubMember.objects.filter(
        user=request.user,
        status='active'
    ).select_related('club', 'role')[:10]  # Limiter pour les performances
    
    return context_data
