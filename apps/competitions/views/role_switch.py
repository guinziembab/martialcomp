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
    from apps.competitions.models import ClubMember, FederationMember

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
            'name': str(_('Pratiquant')),
            'subtitle': practitioner.full_name if hasattr(practitioner, 'full_name') else f"{practitioner.first_name} {practitioner.last_name}",
            'icon': 'fa-user',
            'color': '#3366ff',
            'dashboard_url': '/dashboard/participant/',
        })
    else:
        # Même sans profil Practitioner, permettre le contexte de base
        contexts['available'].append({
            'type': 'practitioner',
            'id': None,
            'name': str(_('Pratiquant')),
            'subtitle': user.get_full_name() or user.username,
            'icon': 'fa-user',
            'color': '#3366ff',
            'dashboard_url': '/dashboard/participant/',
        })

    # 2. Contexte Juge (si profil juge actif)
    if hasattr(user, 'judge_profile') and user.judge_profile and getattr(user.judge_profile, 'active', True):
        judge = user.judge_profile
        contexts['available'].append({
            'type': 'judge',
            'id': judge.id,
            'name': str(_('Juge')),
            'subtitle': getattr(judge, 'get_qualification_level_display', lambda: '')(),
            'icon': 'fa-gavel',
            'color': '#ffc107',
            'dashboard_url': '/dashboard/judge/',
            'qualification_level': getattr(judge, 'qualification_level', None),
            'is_technical_judge': getattr(judge, 'is_technical_judge', False),
            'is_combat_referee': getattr(judge, 'is_combat_referee', False),
        })

    # 3. Contextes organisationnels (clubs)
    try:
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
    except Exception:
        pass  # ClubMember table might not exist yet

    # Fallback: Charger les ClubAdministrator existants pour la transition
    from apps.competitions.models import ClubAdministrator
    admin_clubs = ClubAdministrator.objects.filter(
        user=user
    ).select_related('club')

    for admin in admin_clubs:
        if admin.club:
            # Vérifier si ce club n'est pas déjà dans les contextes
            existing_club_ids = [c.get('club_id') for c in contexts['available'] if c.get('type') == 'organizational']
            if admin.club.id not in existing_club_ids:
                role_info = {
                    'owner': ('Propriétaire', 'fa-crown', '#FFD700'),
                    'admin': ('Administrateur', 'fa-user-shield', '#DC3545'),
                    'coach': ('Entraîneur', 'fa-chalkboard-teacher', '#6F42C1'),
                    'secretary': ('Secrétaire', 'fa-user-edit', '#17A2B8'),
                }
                info = role_info.get(admin.role, ('Membre', 'fa-user', '#6C757D'))

                contexts['available'].append({
                    'type': 'organizational',
                    'id': f'legacy_{admin.id}',
                    'club_id': admin.club.id,
                    'name': info[0],
                    'subtitle': admin.club.name,
                    'icon': info[1],
                    'color': info[2],
                    'dashboard_url': '/dashboard/club/',
                    'legacy': True,
                })

    # 4. Contextes fédération
    try:
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
    except Exception:
        pass  # FederationMember table might not exist yet

    # Fallback: FederationAdministrator
    from apps.competitions.models import FederationAdministrator
    fed_admins = FederationAdministrator.objects.filter(
        user=user
    ).select_related('federation')

    for admin in fed_admins:
        if admin.federation:
            existing_fed_ids = [c.get('federation_id') for c in contexts['available'] if c.get('type') == 'federation']
            if admin.federation.id not in existing_fed_ids:
                contexts['available'].append({
                    'type': 'federation',
                    'id': f'legacy_{admin.id}',
                    'federation_id': admin.federation.id,
                    'name': admin.get_role_display(),
                    'subtitle': admin.federation.name,
                    'icon': 'fa-building',
                    'color': '#1a365d',
                    'dashboard_url': f'/dashboard/federation/{admin.federation.id}/',
                    'legacy': True,
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
    from apps.competitions.models import ClubMember, FederationMember

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'invalid_json',
            'message': str(_('Format JSON invalide'))
        }, status=400)

    context_type = data.get('type')
    context_id = data.get('id')

    # Valider et traiter selon le type de contexte
    if context_type == 'organizational' and context_id:
        # Gérer les IDs legacy
        if isinstance(context_id, str) and context_id.startswith('legacy_'):
            # C'est un ClubAdministrator legacy
            from apps.competitions.models import ClubAdministrator
            admin_id = int(context_id.replace('legacy_', ''))
            try:
                admin = ClubAdministrator.objects.select_related('club').get(
                    id=admin_id,
                    user=request.user
                )
                new_context = {
                    'type': 'organizational',
                    'id': context_id,
                    'club_id': admin.club.id,
                    'club_name': admin.club.name,
                    'role': admin.role,
                    'role_name': admin.get_role_display(),
                    'switched_at': timezone.now().isoformat(),
                    'legacy': True,
                }
                request.session['active_context'] = new_context
                request.session['current_club_id'] = admin.club.id
                redirect_url = '/dashboard/club/'
            except ClubAdministrator.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'invalid_membership',
                    'message': str(_('Appartenance au club invalide ou inactive'))
                }, status=400)
        else:
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
                    'role_name': membership.role.name if membership.role else str(_('Membre')),
                    'switched_at': timezone.now().isoformat(),
                }

                request.session['active_context'] = new_context
                request.session['current_club_id'] = membership.club.id

                redirect_url = _get_dashboard_url_for_role(membership.role.code if membership.role else 'member')

            except ClubMember.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'invalid_membership',
                    'message': str(_('Appartenance au club invalide ou inactive'))
                }, status=400)

    elif context_type == 'federation' and context_id:
        # Gérer les IDs legacy
        if isinstance(context_id, str) and context_id.startswith('legacy_'):
            from apps.competitions.models import FederationAdministrator
            admin_id = int(context_id.replace('legacy_', ''))
            try:
                admin = FederationAdministrator.objects.select_related('federation').get(
                    id=admin_id,
                    user=request.user
                )
                new_context = {
                    'type': 'federation',
                    'id': context_id,
                    'federation_id': admin.federation.id,
                    'federation_name': admin.federation.name,
                    'role': admin.role,
                    'role_name': admin.get_role_display(),
                    'switched_at': timezone.now().isoformat(),
                    'legacy': True,
                }
                request.session['active_context'] = new_context
                request.session['current_federation_id'] = admin.federation.id
                redirect_url = f'/dashboard/federation/{admin.federation.id}/'
            except FederationAdministrator.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'invalid_membership',
                    'message': str(_('Appartenance à la fédération invalide ou inactive'))
                }, status=400)
        else:
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
                    'role_name': membership.role.name if membership.role else str(_('Membre')),
                    'switched_at': timezone.now().isoformat(),
                }

                request.session['active_context'] = new_context
                request.session['current_federation_id'] = membership.federation.id

                redirect_url = '/dashboard/federation/'

            except FederationMember.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'invalid_membership',
                    'message': str(_('Appartenance à la fédération invalide ou inactive'))
                }, status=400)

    elif context_type == 'judge':
        if hasattr(request.user, 'judge_profile') and request.user.judge_profile and getattr(request.user.judge_profile, 'active', True):
            judge = request.user.judge_profile
            new_context = {
                'type': 'judge',
                'id': judge.id,
                'qualification_level': getattr(judge, 'qualification_level', None),
                'switched_at': timezone.now().isoformat(),
            }
            request.session['active_context'] = new_context
            redirect_url = '/dashboard/judge/'
        else:
            return JsonResponse({
                'success': False,
                'error': 'no_judge_profile',
                'message': str(_('Profil juge non trouvé ou inactif'))
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
    from apps.competitions.models import ClubMember

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
                    'apps.competitions.views.role_switch.active_context_processor',
                ],
            },
        }]
    """
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return {}

    from apps.competitions.models import ClubMember

    active_context = request.session.get('active_context', {'type': 'practitioner'})

    # Enrichir le contexte avec des informations supplémentaires
    context_data = {
        'active_context': active_context,
        'active_context_type': active_context.get('type', 'practitioner'),
    }

    # Ajouter les informations de membership si contexte organisationnel
    if active_context.get('type') == 'organizational' and active_context.get('id'):
        context_id = active_context['id']

        # Gérer les IDs legacy
        if isinstance(context_id, str) and context_id.startswith('legacy_'):
            from apps.competitions.models import ClubAdministrator
            admin_id = int(context_id.replace('legacy_', ''))
            try:
                admin = ClubAdministrator.objects.select_related('club').get(
                    id=admin_id,
                    user=request.user
                )
                context_data['active_club'] = admin.club
                context_data['active_role_code'] = admin.role
                context_data['active_role_name'] = admin.get_role_display()
                context_data['user_permissions'] = {'*'} if admin.role == 'owner' else set()
            except ClubAdministrator.DoesNotExist:
                pass
        else:
            try:
                membership = ClubMember.objects.select_related('club', 'role').get(
                    id=context_id,
                    user=request.user
                )
                context_data['active_membership'] = membership
                context_data['active_club'] = membership.club
                context_data['active_role'] = membership.role
                context_data['user_permissions'] = membership.effective_permissions
            except ClubMember.DoesNotExist:
                pass

    # Charger la liste des memberships pour le switcher
    try:
        context_data['user_club_memberships'] = ClubMember.objects.filter(
            user=request.user,
            status='active'
        ).select_related('club', 'role')[:10]  # Limiter pour les performances
    except Exception:
        context_data['user_club_memberships'] = []

    return context_data
