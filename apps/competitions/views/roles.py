from django.core.exceptions import PermissionDenied
# competitions/views/roles.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse

from apps.competitions.models import Club
from apps.competitions.models.permissions import ClubRole, UserClubRole
from apps.competitions.utils.decorators import club_required
from django.contrib.auth.models import User
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

@login_required
@club_required
def manage_roles(request):
    """Vue principale pour la gestion des rÃ´les de club."""
    club = request.club
    
    # Récupérer l'organisation associée au club
    club_organization = getattr(club, 'organization', None) or getattr(club, 'as_organization', None)
    
    if not club_organization:
        messages.warning(request, _("Aucune organisation associée trouvée pour ce club."))
        roles = ClubRole.objects.none()
        user_roles = UserClubRole.objects.none()
    else:
        # Filtrer par organization au lieu de club
        roles = ClubRole.objects.filter(organization=club_organization)
        
        # Filtrer les rÃ´les utilisateur par organization également
        user_roles = UserClubRole.objects.filter(organization=club_organization).select_related('user', 'role')
    
    # Regrouper les utilisateurs par rÃ´le
    users_by_role = {}
    for user_role in user_roles:
        if user_role.role.id not in users_by_role:
            users_by_role[user_role.role.id] = []
        users_by_role[user_role.role.id].append(user_role)
    
    return render(request, 'competitions/club/roles_management.html', {
        'club': club,
        'organization': club_organization,
        'roles': roles,
        'users_by_role': users_by_role,
    })

@login_required
@club_required
def create_role(request):
    """Créer un nouveau rÃ´le pour le club."""
    club = request.club
    
    # Récupérer l'organisation associée au club
    club_organization = getattr(club, 'organization', None) or getattr(club, 'as_organization', None)
    
    if not club_organization:
        messages.error(request, _("Aucune organisation associée trouvée pour ce club."))
        return redirect('competitions:club:manage_roles')
    
    if request.method == 'POST':
        role_name = request.POST.get('role_name')
        description = request.POST.get('description', '')
        is_default = request.POST.get('is_default') == 'on'
        
        # Permissions
        permissions = {
            'can_manage_practitioners': request.POST.get('can_manage_practitioners') == 'on',
            'can_manage_registrations': request.POST.get('can_manage_registrations') == 'on',
            'can_manage_competitions': request.POST.get('can_manage_competitions') == 'on',
            'can_manage_judges': request.POST.get('can_manage_judges') == 'on',
            'can_manage_grades': request.POST.get('can_manage_grades') == 'on',
            'can_manage_roles': request.POST.get('can_manage_roles') == 'on',
        }
        
        # Vérifier si le nom de rÃ´le existe déjÃ  pour cette organisation
        if ClubRole.objects.filter(organization=club_organization, name=role_name).exists():
            messages.error(request, _("Un rÃ´le avec ce nom existe déjÃ ."))
            return redirect('competitions:club:manage_roles')
        
        # Créer le rÃ´le avec organization au lieu de club
        role = ClubRole.objects.create(
            organization=club_organization,
            name=role_name,
            description=description,
            is_default=is_default,
            **permissions
        )
        
        messages.success(request, _("Le rÃ´le a été créé avec succès."))
        return redirect('competitions:club:manage_roles')
        
    # Si méthode GET, afficher le formulaire
    return render(request, 'competitions/club/role_form.html', {
        'club': club,
        'organization': club_organization,
        'action': 'create',
    })

@login_required
@club_required
def edit_role(request, role_id):
    """Modifier un rÃ´le existant."""
    club = request.club
    
    # Récupérer l'organisation associée au club
    club_organization = getattr(club, 'organization', None) or getattr(club, 'as_organization', None)
    
    if not club_organization:
        messages.error(request, _("Aucune organisation associée trouvée pour ce club."))
        return redirect('competitions:club:manage_roles')
    
    # Filtrer par organization au lieu de club
    role = get_object_or_404(ClubRole, id=role_id, organization=club_organization)
    
    if request.method == 'POST':
        role.name = request.POST.get('role_name')
        role.description = request.POST.get('description', '')
        role.is_default = request.POST.get('is_default') == 'on'
        
        # Permissions
        role.can_manage_practitioners = request.POST.get('can_manage_practitioners') == 'on'
        role.can_manage_registrations = request.POST.get('can_manage_registrations') == 'on'
        role.can_manage_competitions = request.POST.get('can_manage_competitions') == 'on'
        role.can_manage_judges = request.POST.get('can_manage_judges') == 'on'
        role.can_manage_grades = request.POST.get('can_manage_grades') == 'on'
        role.can_manage_roles = request.POST.get('can_manage_roles') == 'on'
        
        role.save()
        
        messages.success(request, _("Le rÃ´le a été mis Ã  jour avec succès."))
        return redirect('competitions:club:manage_roles')
        
    # Si méthode GET, afficher le formulaire avec les valeurs actuelles
    return render(request, 'competitions/club/role_form.html', {
        'club': club,
        'organization': club_organization,
        'role': role,
        'action': 'edit',
    })

@login_required
@club_required
def delete_role(request, role_id):
    """Supprimer un rÃ´le."""
    club = request.club
    
    # Récupérer l'organisation associée au club
    club_organization = getattr(club, 'organization', None) or getattr(club, 'as_organization', None)
    
    if not club_organization:
        messages.error(request, _("Aucune organisation associée trouvée pour ce club."))
        return redirect('competitions:club:manage_roles')
    
    # Filtrer par organization au lieu de club
    role = get_object_or_404(ClubRole, id=role_id, organization=club_organization)
    
    if request.method == 'POST':
        # Vérifier si le rÃ´le est utilisé
        if UserClubRole.objects.filter(role=role).exists():
            messages.error(request, _("Ce rÃ´le ne peut pas Ãªtre supprimé car il est attribué Ã  des utilisateurs."))
            return redirect('competitions:club:manage_roles')
        
        role.delete()
        messages.success(request, _("Le rÃ´le a été supprimé avec succès."))
        return redirect('competitions:club:manage_roles')
        
    # Si méthode GET, afficher la confirmation
    return render(request, 'competitions/club/confirm_delete.html', {
        'club': club,
        'organization': club_organization,
        'object': role,
        'object_name': role.name,
        'message': _("ÃŠtes-vous sÃ»r de vouloir supprimer ce rÃ´le ?"),
    })

@login_required
@club_required
def assign_role(request):
    """Attribuer un rÃ´le Ã  un utilisateur."""
    club = request.club
    
    # Récupérer l'organisation associée au club
    club_organization = getattr(club, 'organization', None) or getattr(club, 'as_organization', None)
    
    if not club_organization:
        messages.error(request, _("Aucune organisation associée trouvée pour ce club."))
        return redirect('competitions:club:manage_roles')
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        role_id = request.POST.get('role_id')
        
        user = get_object_or_404(User, id=user_id)
        # Filtrer par organization au lieu de club
        role = get_object_or_404(ClubRole, id=role_id, organization=club_organization)
        
        # Vérifier si l'attribution existe déjÃ 
        if UserClubRole.objects.filter(user=user, organization=club_organization, role=role).exists():
            messages.warning(request, _("Cet utilisateur a déjÃ  ce rÃ´le."))
        else:
            # Créer l'attribution avec organization au lieu de club
            UserClubRole.objects.create(
                user=user,
                organization=club_organization,
                role=role,
                assigned_by=request.user,
            )
            messages.success(request, _("RÃ´le attribué avec succès."))
        
        return redirect('competitions:club:manage_roles')
    
    # Si méthode GET, afficher le formulaire
    roles = ClubRole.objects.filter(organization=club_organization)
    
    # Récupérer les utilisateurs associés au club (par exemple, les pratiquants du club)
    # Adapter cette requÃªte selon la nouvelle structure de données
    from apps.competitions.models import Practitioner
    practitioners = Practitioner.objects.filter(organization=club_organization).select_related('user')
    club_users = [p.user for p in practitioners if p.user]
    
    return render(request, 'competitions/club/assign_role_form.html', {
        'club': club,
        'organization': club_organization,
        'roles': roles,
        'users': club_users,
    })

@login_required
@club_required
def revoke_role(request, user_role_id):
    """Révoquer un rÃ´le attribué Ã  un utilisateur."""
    club = request.club
    
    # Récupérer l'organisation associée au club
    club_organization = getattr(club, 'organization', None) or getattr(club, 'as_organization', None)
    
    if not club_organization:
        messages.error(request, _("Aucune organisation associée trouvée pour ce club."))
        return redirect('competitions:club:manage_roles')
    
    # Filtrer par organization au lieu de club
    user_role = get_object_or_404(UserClubRole, id=user_role_id, organization=club_organization)
    
    if request.method == 'POST':
        user_role.delete()
        messages.success(request, _("RÃ´le révoqué avec succès."))
        return redirect('competitions:club:manage_roles')
    
    # Si méthode GET, afficher la confirmation
    return render(request, 'competitions/club/confirm_delete.html', {
        'club': club,
        'organization': club_organization,
        'object': user_role,
        'object_name': f"{user_role.user.username} - {user_role.role.name}",
        'message': _("Êtes-vous sûr de vouloir révoquer ce rôle ?"),
    })


# ============================================================================
# NOUVELLES VUES POUR LE SYSTÈME DE RÔLES AVEC VALIDATION
# ============================================================================

import logging
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET
from django.core.paginator import Paginator
from django.db import transaction

from apps.organizations.models import (
    Organization, OrganizationMember, OrganizationRole, MembershipStatus
)
from apps.competitions.models import Practitioner
from apps.competitions.models.judges import Judge
from apps.competitions.forms.role_forms import AssignRoleForm, ValidateRoleForm
from apps.competitions.views.club.practitioners import get_user_club
from apps.competitions.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


@login_required
@require_POST
def assign_organization_role(request, practitioner_id):
    """
    Attribuer un rôle d'organisation à un pratiquant.
    Crée une entrée OrganizationMember avec statut 'pending' pour validation.
    """
    try:
        user_club = get_user_club(request)
        if not user_club:
            messages.error(request, _("Vous n'êtes associé à aucune organisation."))
            return redirect('competitions:dashboard:club')

        practitioner = get_object_or_404(Practitioner, pk=practitioner_id)

        # Vérifier les permissions
        if not request.user.is_superuser:
            if practitioner.organization and practitioner.organization != user_club:
                messages.error(request, _("Vous n'avez pas l'autorisation de modifier ce pratiquant."))
                return redirect('competitions:club:practitioner_detail', pk=practitioner_id)

        form = AssignRoleForm(request.POST)
        if not form.is_valid():
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            return redirect('competitions:club:practitioner_detail', pk=practitioner_id)

        role = form.cleaned_data['role']
        title = form.cleaned_data.get('title', '')
        notes = form.cleaned_data.get('notes', '')

        # Vérifier si le pratiquant a un compte utilisateur
        if not practitioner.user:
            messages.error(request, _(
                "Ce pratiquant n'a pas de compte utilisateur. "
                "Veuillez d'abord créer un compte pour pouvoir lui attribuer un rôle."
            ))
            return redirect('competitions:club:practitioner_detail', pk=practitioner_id)

        # Vérifier si le membre a déjà ce rôle dans cette organisation
        existing_membership = OrganizationMember.objects.filter(
            user=practitioner.user,
            organization=user_club,
            role=role
        ).first()

        if existing_membership:
            if existing_membership.membership_status == MembershipStatus.PENDING:
                messages.warning(request, _(
                    "Une demande de rôle {} est déjà en attente de validation pour ce membre."
                ).format(existing_membership.get_role_display()))
            elif existing_membership.membership_status == MembershipStatus.APPROVED:
                messages.warning(request, _(
                    "Ce membre possède déjà le rôle {} dans cette organisation."
                ).format(existing_membership.get_role_display()))
            else:
                # Rôle précédemment refusé, on peut le redemander
                existing_membership.membership_status = MembershipStatus.PENDING
                existing_membership.title = title
                existing_membership.notes = notes
                existing_membership.rejection_reason = ''
                existing_membership.save()
                messages.success(request, _(
                    "La demande de rôle {} a été soumise à nouveau pour validation."
                ).format(existing_membership.get_role_display()))

            return redirect('competitions:club:practitioner_detail', pk=practitioner_id)

        # Créer le nouveau membership avec statut 'pending'
        with transaction.atomic():
            membership = OrganizationMember.objects.create(
                user=practitioner.user,
                organization=user_club,
                role=role,
                title=title,
                notes=notes,
                practitioner=practitioner,
                membership_status=MembershipStatus.PENDING,
                is_active=True
            )

            # Si c'est un rôle de juge, créer aussi le profil Judge
            if role == OrganizationRole.JUDGE:
                _create_judge_profile_for_role(request, practitioner, user_club, form.cleaned_data)

            logger.info(
                f"Rôle {role} attribué (en attente) à {practitioner.full_name} "
                f"par {request.user.username} dans {user_club.name}"
            )

            # Envoyer notification au demandeur
            try:
                NotificationService.create_role_assignment_notification(
                    membership, action='pending'
                )
            except Exception as notif_err:
                logger.warning(f"Erreur notification demandeur: {notif_err}")

            # Notifier les admins/owners de l'organisation
            try:
                admin_members = OrganizationMember.objects.filter(
                    organization=user_club,
                    role__in=[OrganizationRole.OWNER, OrganizationRole.ADMIN],
                    is_active=True,
                    membership_status=MembershipStatus.APPROVED
                ).select_related('user')
                admin_users = [m.user for m in admin_members if m.user]
                NotificationService.create_pending_approval_notification(
                    membership, admin_users
                )
            except Exception as notif_err:
                logger.warning(f"Erreur notification admins: {notif_err}")

        messages.success(request, _(
            "Le rôle {} a été attribué à {}. En attente de validation par un administrateur."
        ).format(membership.get_role_display(), practitioner.full_name))

        return redirect('competitions:club:practitioner_detail', pk=practitioner_id)

    except Exception as e:
        logger.error(f"Erreur lors de l'attribution du rôle: {str(e)}", exc_info=True)
        messages.error(request, _("Erreur lors de l'attribution du rôle: {}").format(str(e)))
        return redirect('competitions:club:practitioner_detail', pk=practitioner_id)


def _create_judge_profile_for_role(request, practitioner, organization, form_data):
    """Crée un profil Judge pour un pratiquant."""
    if hasattr(practitioner, 'judge') and practitioner.judge:
        return practitioner.judge

    judge = Judge.objects.create(
        practitioner=practitioner,
        user=practitioner.user,
        organization=organization,
        is_technical_judge=form_data.get('is_technical_judge', False),
        is_combat_referee=form_data.get('is_combat_referee', False),
        qualification_level=form_data.get('qualification_level', 'novice'),
        years_experience=form_data.get('years_experience') or 0,
        certification_number=form_data.get('certification_number', ''),
        notes=form_data.get('notes', ''),
        active=False  # Inactif jusqu'à validation du rôle
    )
    return judge


@login_required
def pending_role_approvals(request):
    """Liste des demandes de rôle en attente de validation."""
    try:
        user_club = get_user_club(request)
        if not user_club:
            messages.error(request, _("Vous n'êtes associé à aucune organisation."))
            return redirect('competitions:dashboard:club')

        # Vérifier les permissions (owner ou admin)
        user_membership = OrganizationMember.objects.filter(
            user=request.user,
            organization=user_club,
            role__in=[OrganizationRole.OWNER, OrganizationRole.ADMIN],
            is_active=True,
            membership_status=MembershipStatus.APPROVED
        ).first()

        if not user_membership and not request.user.is_superuser:
            messages.error(request, _(
                "Seuls les propriétaires et administrateurs peuvent valider les demandes de rôle."
            ))
            return redirect('competitions:dashboard:club')

        # Récupérer les demandes en attente
        pending_memberships = OrganizationMember.objects.filter(
            organization=user_club,
            membership_status=MembershipStatus.PENDING
        ).select_related('user', 'practitioner').order_by('-created_at')

        # Pagination
        paginator = Paginator(pending_memberships, 20)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        # Statistiques
        stats = {
            'pending_count': pending_memberships.count(),
            'approved_today': OrganizationMember.objects.filter(
                organization=user_club,
                membership_status=MembershipStatus.APPROVED,
                approved_at__date=timezone.now().date()
            ).count(),
            'rejected_today': OrganizationMember.objects.filter(
                organization=user_club,
                membership_status=MembershipStatus.REJECTED,
                approved_at__date=timezone.now().date()
            ).count(),
        }

        context = {
            'page_obj': page_obj,
            'stats': stats,
            'organization': user_club,
        }

        return render(request, 'competitions/roles/pending_approvals.html', context)

    except Exception as e:
        logger.error(f"Erreur lors de l'affichage des demandes de rôle: {str(e)}", exc_info=True)
        messages.error(request, _("Erreur lors du chargement des demandes."))
        return redirect('competitions:dashboard:club')


@login_required
@require_POST
def validate_organization_role(request, membership_id):
    """Valider ou rejeter une demande de rôle."""
    try:
        user_club = get_user_club(request)
        if not user_club:
            return JsonResponse({'success': False, 'error': _("Organisation non trouvée.")}, status=400)

        membership = get_object_or_404(
            OrganizationMember,
            pk=membership_id,
            organization=user_club,
            membership_status=MembershipStatus.PENDING
        )

        # Vérifier les permissions
        user_membership = OrganizationMember.objects.filter(
            user=request.user,
            organization=user_club,
            role__in=[OrganizationRole.OWNER, OrganizationRole.ADMIN],
            is_active=True,
            membership_status=MembershipStatus.APPROVED
        ).first()

        if not user_membership and not request.user.is_superuser:
            return JsonResponse({
                'success': False,
                'error': _("Vous n'avez pas les permissions pour cette action.")
            }, status=403)

        action = request.POST.get('action')
        rejection_reason = request.POST.get('rejection_reason', '')

        with transaction.atomic():
            if action == 'approve':
                membership.approve(request.user)

                # Si c'est un juge, activer le profil Judge
                if membership.role == OrganizationRole.JUDGE and membership.practitioner:
                    try:
                        judge = membership.practitioner.judge
                        if judge:
                            judge.active = True
                            judge.save(update_fields=['active'])
                    except Exception:
                        pass

                logger.info(
                    f"Rôle {membership.role} approuvé pour {membership.user.username} "
                    f"par {request.user.username}"
                )

                message = _("Le rôle {} a été approuvé pour {}.").format(
                    membership.get_role_display(),
                    membership.user.get_full_name() or membership.user.username
                )

                # Notifier l'utilisateur de l'approbation
                try:
                    NotificationService.create_role_assignment_notification(
                        membership, action='approved'
                    )
                except Exception as notif_err:
                    logger.warning(f"Erreur notification approbation: {notif_err}")

            elif action == 'reject':
                membership.reject(request.user, rejection_reason)

                logger.info(
                    f"Rôle {membership.role} refusé pour {membership.user.username} "
                    f"par {request.user.username}: {rejection_reason}"
                )

                message = _("Le rôle {} a été refusé pour {}.").format(
                    membership.get_role_display(),
                    membership.user.get_full_name() or membership.user.username
                )

                # Notifier l'utilisateur du rejet
                try:
                    NotificationService.create_role_assignment_notification(
                        membership, action='rejected'
                    )
                except Exception as notif_err:
                    logger.warning(f"Erreur notification rejet: {notif_err}")

            else:
                return JsonResponse({
                    'success': False,
                    'error': _("Action invalide.")
                }, status=400)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': str(message),
                'new_status': membership.membership_status,
                'new_status_display': membership.get_membership_status_display()
            })

        messages.success(request, message)
        return redirect('competitions:pending_role_approvals')

    except OrganizationMember.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': _("Demande non trouvée ou déjà traitée.")
            }, status=404)
        messages.error(request, _("Demande non trouvée ou déjà traitée."))
        return redirect('competitions:pending_role_approvals')

    except Exception as e:
        logger.error(f"Erreur lors de la validation du rôle: {str(e)}", exc_info=True)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
        messages.error(request, _("Erreur lors de la validation: {}").format(str(e)))
        return redirect('competitions:pending_role_approvals')


@login_required
@require_GET
def get_user_roles_api(request):
    """API: Récupère les rôles actifs de l'utilisateur connecté."""
    try:
        memberships = OrganizationMember.objects.filter(
            user=request.user,
            is_active=True,
            membership_status=MembershipStatus.APPROVED
        ).select_related('organization')

        roles = []
        for m in memberships:
            try:
                dashboard_url = m.get_dashboard_url()
            except Exception:
                dashboard_url = '/competitions/dashboard/'
            roles.append({
                'id': m.id,
                'role': m.role,
                'role_display': m.get_role_display(),
                'organization_id': m.organization.id,
                'organization_name': m.organization.name,
                'title': m.title or '',
                'dashboard_url': dashboard_url,
                'has_dashboard_access': m.has_dashboard_access,
            })

            # Ajouter les rôles additionnels comme entrées séparées
            additional = getattr(m, 'additional_roles', None) or []
            for extra_role in additional:
                if extra_role == m.role:
                    continue
                try:
                    extra_display = dict(OrganizationRole.choices).get(extra_role, extra_role)
                    extra_url = OrganizationMember.get_role_dashboard_url(extra_role)
                except Exception:
                    extra_display = extra_role
                    extra_url = '/competitions/dashboard/'
                roles.append({
                    'id': m.id,
                    'role': extra_role,
                    'role_display': str(extra_display),
                    'organization_id': m.organization.id,
                    'organization_name': m.organization.name,
                    'title': m.title or '',
                    'dashboard_url': extra_url,
                    'has_dashboard_access': True,
                })

        # Ajouter le rôle "Pratiquant" par défaut
        practitioner = Practitioner.objects.filter(user=request.user).first()
        if practitioner:
            roles.insert(0, {
                'id': 0,
                'role': 'practitioner',
                'role_display': _("Pratiquant"),
                'organization_id': practitioner.organization_id if practitioner.organization else None,
                'organization_name': practitioner.organization.name if practitioner.organization else '',
                'title': '',
                'dashboard_url': '/competitions/dashboard/participant/',
                'has_dashboard_access': True,
            })

        return JsonResponse({
            'success': True,
            'roles': roles,
            'current_role': request.session.get('current_role', 'practitioner')
        })

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des rôles: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
def switch_user_role(request):
    """API: Change le rôle actif de l'utilisateur."""
    try:
        role = request.POST.get('role')
        membership_id = request.POST.get('membership_id')

        if role == 'practitioner' or (not membership_id and not role):
            request.session['current_role'] = 'practitioner'
            request.session['current_membership_id'] = None
            request.session['dashboard_mode'] = 'participant'

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'redirect_url': '/competitions/dashboard/participant/'
                })
            return redirect('competitions:dashboard:participant')

        membership = get_object_or_404(
            OrganizationMember,
            pk=membership_id,
            user=request.user,
            is_active=True,
            membership_status=MembershipStatus.APPROVED
        )

        # Déterminer le rôle effectif (peut être un additional_role)
        effective_role = role if role else membership.role
        if effective_role != membership.role:
            # Vérifier que ce rôle est bien dans additional_roles
            additional = getattr(membership, 'additional_roles', None) or []
            if effective_role not in additional:
                effective_role = membership.role

        request.session['current_role'] = effective_role
        request.session['current_membership_id'] = membership.id
        request.session['current_organization_id'] = membership.organization_id

        role_to_mode = {
            OrganizationRole.OWNER: 'club',
            OrganizationRole.ADMIN: 'club',
            OrganizationRole.MANAGER: 'manager',
            OrganizationRole.TREASURER: 'finances',
            OrganizationRole.ACCOUNTANT: 'finances',
            OrganizationRole.COACH: 'coach',
            OrganizationRole.JUDGE: 'judge_technical',
            OrganizationRole.MEMBER: 'participant',
        }
        request.session['dashboard_mode'] = role_to_mode.get(
            effective_role, 'participant'
        )

        dashboard_url = OrganizationMember.get_role_dashboard_url(
            effective_role
        )

        role_display = dict(OrganizationRole.choices).get(
            effective_role, effective_role
        )

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'redirect_url': dashboard_url,
                'role': effective_role,
                'role_display': str(role_display)
            })

        return redirect(dashboard_url)

    except OrganizationMember.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': _("Rôle non trouvé ou non autorisé.")
            }, status=404)
        messages.error(request, _("Rôle non trouvé ou non autorisé."))
        return redirect('competitions:dashboard')

    except Exception as e:
        logger.error(f"Erreur lors du changement de rôle: {str(e)}", exc_info=True)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
        messages.error(request, _("Erreur lors du changement de rôle."))
        return redirect('competitions:dashboard')


# ============================================================================
# API POUR LA GESTION DES RÔLES DANS LE DASHBOARD CLUB
# ============================================================================

@login_required
@require_GET
def get_club_members_with_roles_api(request):
    """
    API: Récupère la liste des membres du club avec leurs rôles.
    Utilisé par l'onglet "Rôles & Permissions" du dashboard club.

    Combine:
    - Les OrganizationMember existants (membres avec rôles spéciaux)
    - Les Practitioner de l'organisation (tous les pratiquants)
    """
    try:
        from apps.competitions.models import Practitioner

        # Récupérer le club de l'utilisateur
        user_club = get_user_club(request)
        if not user_club:
            return JsonResponse({
                'success': False,
                'error': _("Vous n'êtes associé à aucune organisation.")
            }, status=400)

        # Paramètres de pagination et filtrage
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        search = request.GET.get('search', '').strip()
        role_filter = request.GET.get('role', '')
        status_filter = request.GET.get('status', '')

        # Construire une liste combinée de tous les membres
        all_members = []

        # 1. Récupérer les OrganizationMember (membres avec rôles spéciaux)
        org_members = OrganizationMember.objects.filter(
            organization=user_club
        ).select_related('user', 'practitioner')

        # Créer un set des user_ids et practitioner_ids déjà dans OrganizationMember
        existing_user_ids = set()
        existing_practitioner_ids = set()

        for member in org_members:
            if member.user_id:
                existing_user_ids.add(member.user_id)
            if member.practitioner_id:
                existing_practitioner_ids.add(member.practitioner_id)

            # Obtenir les permissions du rôle
            permissions = _get_role_permissions(member.role)

            all_members.append({
                'id': f'om_{member.id}',  # Préfixe pour identifier le type
                'member_id': member.id,
                'type': 'organization_member',
                'user_id': member.user_id,
                'practitioner_id': member.practitioner_id,
                'name': member.user.get_full_name() or member.user.username if member.user else _('Sans compte'),
                'first_name': member.user.first_name if member.user else '',
                'last_name': member.user.last_name if member.user else '',
                'email': member.user.email if member.user else '',
                'avatar_url': member.practitioner.photo.url if member.practitioner and member.practitioner.photo else None,
                'role': member.role,
                'role_display': member.get_role_display(),
                'title': member.title or '',
                'is_active': member.is_active,
                'membership_status': member.membership_status,
                'membership_status_display': member.get_membership_status_display(),
                'permissions': permissions,
                'joined_at': member.created_at.strftime('%d/%m/%Y') if member.created_at else '',
                'can_edit': request.user.is_superuser or _can_edit_member_role(request.user, member, user_club),
                'can_remove': request.user.is_superuser or _can_remove_member_role(request.user, member, user_club),
                'has_role': True,
            })

        # 2. Récupérer les Practitioner de l'organisation (qui n'ont pas déjà un OrganizationMember)
        practitioners = Practitioner.objects.filter(
            organization=user_club,
            is_active=True
        ).exclude(
            id__in=existing_practitioner_ids
        ).select_related('user')

        for practitioner in practitioners:
            # Vérifier si le user de ce practitioner n'est pas déjà dans la liste
            if practitioner.user_id and practitioner.user_id in existing_user_ids:
                continue

            all_members.append({
                'id': f'p_{practitioner.id}',  # Préfixe pour identifier le type
                'member_id': None,
                'type': 'practitioner',
                'user_id': practitioner.user_id,
                'practitioner_id': practitioner.id,
                'name': f"{practitioner.first_name} {practitioner.last_name}".strip() or practitioner.license_number or _('Sans nom'),
                'first_name': practitioner.first_name or '',
                'last_name': practitioner.last_name or '',
                'email': practitioner.email or (practitioner.user.email if practitioner.user else ''),
                'avatar_url': practitioner.photo.url if practitioner.photo else None,
                'role': 'member',  # Rôle par défaut pour les pratiquants
                'role_display': _('Membre'),
                'title': '',
                'is_active': practitioner.is_active,
                'membership_status': 'approved',  # Les pratiquants actifs sont considérés comme approuvés
                'membership_status_display': _('Actif'),
                'permissions': ['view_only'],
                'joined_at': practitioner.registration_date.strftime('%d/%m/%Y') if practitioner.registration_date else '',
                'can_edit': True,  # On peut assigner un rôle à un pratiquant
                'can_remove': False,  # On ne peut pas "retirer" un pratiquant de cette liste
                'has_role': False,
            })

        # Appliquer les filtres
        if search:
            search_lower = search.lower()
            all_members = [
                m for m in all_members
                if search_lower in m['name'].lower()
                or search_lower in m['email'].lower()
                or search_lower in m['first_name'].lower()
                or search_lower in m['last_name'].lower()
            ]

        if role_filter:
            if role_filter == 'no_role':
                all_members = [m for m in all_members if not m['has_role']]
            else:
                all_members = [m for m in all_members if m['role'] == role_filter]

        if status_filter:
            if status_filter == 'active':
                all_members = [m for m in all_members if m['is_active'] and m['membership_status'] == 'approved']
            elif status_filter == 'inactive':
                all_members = [m for m in all_members if not m['is_active'] or m['membership_status'] != 'approved']
            elif status_filter == 'pending':
                all_members = [m for m in all_members if m['membership_status'] == 'pending']

        # Trier par nom
        all_members.sort(key=lambda x: (x['last_name'].lower(), x['first_name'].lower()))

        # Pagination manuelle
        total_count = len(all_members)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_members = all_members[start_idx:end_idx]

        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
        has_next = page < total_pages
        has_previous = page > 1

        # Statistiques des rôles
        role_stats = {
            'admin_count': OrganizationMember.objects.filter(
                organization=user_club,
                role__in=[OrganizationRole.OWNER, OrganizationRole.ADMIN],
                is_active=True,
                membership_status=MembershipStatus.APPROVED
            ).count(),
            'manager_count': OrganizationMember.objects.filter(
                organization=user_club,
                role=OrganizationRole.MANAGER,
                is_active=True,
                membership_status=MembershipStatus.APPROVED
            ).count(),
            'coach_count': OrganizationMember.objects.filter(
                organization=user_club,
                role=OrganizationRole.COACH,
                is_active=True,
                membership_status=MembershipStatus.APPROVED
            ).count(),
            'member_count': Practitioner.objects.filter(
                organization=user_club,
                is_active=True
            ).count(),
            'pending_count': OrganizationMember.objects.filter(
                organization=user_club,
                membership_status=MembershipStatus.PENDING
            ).count(),
        }

        return JsonResponse({
            'success': True,
            'members': paginated_members,
            'stats': role_stats,
            'pagination': {
                'current_page': page,
                'total_pages': total_pages,
                'total_count': total_count,
                'has_next': has_next,
                'has_previous': has_previous,
            }
        })

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des membres: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def _get_role_permissions(role):
    """Retourne les permissions associées à un rôle."""
    if role in [OrganizationRole.OWNER, OrganizationRole.ADMIN]:
        return ['manage_members', 'manage_competitions', 'edit_organization', 'manage_roles', 'manage_finances']
    elif role == OrganizationRole.MANAGER:
        return ['manage_members', 'manage_competitions']
    elif role == OrganizationRole.TREASURER:
        return ['manage_finances', 'view_finances', 'manage_transactions']
    elif role == OrganizationRole.ACCOUNTANT:
        return ['view_finances', 'manage_transactions', 'export_finances']
    elif role == OrganizationRole.COACH:
        return ['manage_practitioners', 'view_competitions']
    elif role == OrganizationRole.JUDGE:
        return ['judge_competitions']
    else:
        return ['view_only']


def _can_edit_member_role(user, member, organization):
    """Vérifie si l'utilisateur peut modifier le rôle d'un membre."""
    # L'utilisateur ne peut pas modifier son propre rôle
    if member.user == user:
        return False

    # Vérifier si l'utilisateur est le créateur/propriétaire du club
    is_club_owner = False
    if hasattr(organization, 'owner') and organization.owner == user:
        is_club_owner = True
    elif hasattr(organization, 'created_by') and organization.created_by == user:
        is_club_owner = True

    # Le propriétaire du club peut tout modifier
    if is_club_owner:
        return True

    # Vérifier si l'utilisateur est owner ou admin dans OrganizationMember
    user_membership = OrganizationMember.objects.filter(
        user=user,
        organization=organization,
        role__in=[OrganizationRole.OWNER, OrganizationRole.ADMIN],
        is_active=True,
        membership_status=MembershipStatus.APPROVED
    ).first()

    if not user_membership:
        return False

    # Le owner peut tout modifier sauf un autre owner
    if user_membership.role == OrganizationRole.OWNER:
        return member.role != OrganizationRole.OWNER

    # L'admin ne peut pas modifier les owners et autres admins
    return member.role not in [OrganizationRole.OWNER, OrganizationRole.ADMIN]


def _can_remove_member_role(user, member, organization):
    """Vérifie si l'utilisateur peut retirer le rôle d'un membre."""
    # Même logique que _can_edit_member_role
    return _can_edit_member_role(user, member, organization)


@login_required
@require_POST
def invite_club_member_api(request):
    """
    API: Invite un nouveau membre au club par email.
    Envoie un email d'invitation avec le rôle attribué.
    """
    try:
        user_club = get_user_club(request)
        if not user_club:
            return JsonResponse({
                'success': False,
                'error': _("Vous n'êtes associé à aucune organisation.")
            }, status=400)

        # Vérifier les permissions
        user_membership = OrganizationMember.objects.filter(
            user=request.user,
            organization=user_club,
            role__in=[OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.MANAGER],
            is_active=True,
            membership_status=MembershipStatus.APPROVED
        ).first()

        # Vérifier aussi si l'utilisateur est le créateur/propriétaire du club
        is_club_owner = False
        if hasattr(user_club, 'owner') and user_club.owner == request.user:
            is_club_owner = True
        elif hasattr(user_club, 'created_by') and user_club.created_by == request.user:
            is_club_owner = True

        if not user_membership and not request.user.is_superuser and not is_club_owner:
            return JsonResponse({
                'success': False,
                'error': _("Vous n'avez pas les permissions pour inviter des membres.")
            }, status=403)

        import json
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST

        email = data.get('email', '').strip().lower()
        role = data.get('role', 'member')
        message = data.get('message', '')

        if not email:
            return JsonResponse({
                'success': False,
                'error': _("L'email est requis.")
            }, status=400)

        # Vérifier si l'email est valide
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({
                'success': False,
                'error': _("L'adresse email n'est pas valide.")
            }, status=400)

        # Mapper le rôle string vers OrganizationRole
        role_mapping = {
            'member': OrganizationRole.MEMBER,
            'coach': OrganizationRole.COACH,
            'judge': OrganizationRole.JUDGE,
            'treasurer': OrganizationRole.TREASURER,
            'accountant': OrganizationRole.ACCOUNTANT,
            'manager': OrganizationRole.MANAGER,
            'admin': OrganizationRole.ADMIN,
        }
        org_role = role_mapping.get(role, OrganizationRole.MEMBER)

        # Vérifier si l'utilisateur existe déjà
        existing_user = User.objects.filter(email=email).first()

        if existing_user:
            # Vérifier si déjà membre
            existing_membership = OrganizationMember.objects.filter(
                user=existing_user,
                organization=user_club
            ).first()

            if existing_membership:
                return JsonResponse({
                    'success': False,
                    'error': _("Cet utilisateur est déjà membre de votre organisation.")
                }, status=400)

            # Créer le membership directement
            with transaction.atomic():
                membership = OrganizationMember.objects.create(
                    user=existing_user,
                    organization=user_club,
                    role=org_role,
                    membership_status=MembershipStatus.PENDING,
                    is_active=True,
                    notes=message
                )

                # Envoyer notification
                try:
                    NotificationService.create_role_assignment_notification(
                        membership, action='pending'
                    )
                except Exception as notif_err:
                    logger.warning(f"Erreur notification invitation: {notif_err}")

            return JsonResponse({
                'success': True,
                'message': _("L'utilisateur {} a été invité avec le rôle {}. En attente de validation.").format(
                    existing_user.get_full_name() or existing_user.email,
                    membership.get_role_display()
                ),
                'member': {
                    'id': membership.id,
                    'name': existing_user.get_full_name() or existing_user.username,
                    'email': existing_user.email,
                    'role': membership.role,
                    'role_display': membership.get_role_display(),
                    'membership_status': membership.membership_status,
                }
            })

        else:
            # L'utilisateur n'existe pas - envoyer un email d'invitation
            # Créer un token d'invitation
            from django.contrib.auth.tokens import default_token_generator
            from django.utils.http import urlsafe_base64_encode
            from django.utils.encoding import force_bytes
            import uuid

            invitation_token = str(uuid.uuid4())

            # Stocker l'invitation en session ou en base (simplifié ici)
            # TODO: Créer un modèle Invitation pour persister ces données

            # Pour l'instant, envoyer juste l'email de notification
            try:
                from django.core.mail import send_mail
                from django.template.loader import render_to_string
                from django.conf import settings

                subject = _("Invitation à rejoindre {} sur MartialComp").format(user_club.name)

                context = {
                    'organization_name': user_club.name,
                    'inviter_name': request.user.get_full_name() or request.user.username,
                    'role_display': dict(OrganizationRole.choices).get(org_role, role),
                    'message': message,
                    'signup_url': request.build_absolute_uri('/accounts/signup/'),
                }

                # Essayer de charger le template, sinon message simple
                try:
                    html_message = render_to_string('emails/club_invitation.html', context)
                    text_message = render_to_string('emails/club_invitation.txt', context)
                except Exception:
                    text_message = _(
                        "Bonjour,\n\n"
                        "{inviter_name} vous invite à rejoindre {organization_name} sur MartialComp "
                        "en tant que {role_display}.\n\n"
                        "{message}\n\n"
                        "Pour accepter cette invitation, créez votre compte sur: {signup_url}\n\n"
                        "Cordialement,\nL'équipe MartialComp"
                    ).format(**context)
                    html_message = None

                send_mail(
                    subject=subject,
                    message=text_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    html_message=html_message,
                    fail_silently=False
                )

                logger.info(f"Email d'invitation envoyé à {email} pour rejoindre {user_club.name}")

                return JsonResponse({
                    'success': True,
                    'message': _("Un email d'invitation a été envoyé à {}. L'utilisateur pourra rejoindre votre organisation après avoir créé son compte.").format(email),
                    'invited_email': email,
                    'role': role,
                })

            except Exception as mail_err:
                logger.error(f"Erreur envoi email invitation: {mail_err}")
                return JsonResponse({
                    'success': False,
                    'error': _("Erreur lors de l'envoi de l'email d'invitation. Veuillez réessayer.")
                }, status=500)

    except Exception as e:
        logger.error(f"Erreur lors de l'invitation du membre: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
def update_member_role_api(request, member_id):
    """
    API: Met à jour le rôle d'un membre existant.
    """
    try:
        user_club = get_user_club(request)
        if not user_club:
            return JsonResponse({
                'success': False,
                'error': _("Vous n'êtes associé à aucune organisation.")
            }, status=400)

        member = get_object_or_404(OrganizationMember, pk=member_id, organization=user_club)

        # Vérifier les permissions
        if not request.user.is_superuser and not _can_edit_member_role(request.user, member, user_club):
            return JsonResponse({
                'success': False,
                'error': _("Vous n'avez pas les permissions pour modifier ce rôle.")
            }, status=403)

        import json
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST

        new_role = data.get('role')
        reason = data.get('reason', '')

        # Mapper le rôle string vers OrganizationRole
        role_mapping = {
            'member': OrganizationRole.MEMBER,
            'coach': OrganizationRole.COACH,
            'judge': OrganizationRole.JUDGE,
            'treasurer': OrganizationRole.TREASURER,
            'accountant': OrganizationRole.ACCOUNTANT,
            'manager': OrganizationRole.MANAGER,
            'admin': OrganizationRole.ADMIN,
            'owner': OrganizationRole.OWNER,
        }

        if new_role not in role_mapping:
            return JsonResponse({
                'success': False,
                'error': _("Rôle invalide.")
            }, status=400)

        org_role = role_mapping[new_role]

        # Vérifier qu'on ne peut pas promouvoir au-dessus de son propre niveau
        user_membership = OrganizationMember.objects.filter(
            user=request.user,
            organization=user_club,
            is_active=True,
            membership_status=MembershipStatus.APPROVED
        ).first()

        if user_membership and not request.user.is_superuser:
            # Empêcher de créer un owner si on n'est pas owner
            if org_role == OrganizationRole.OWNER and user_membership.role != OrganizationRole.OWNER:
                return JsonResponse({
                    'success': False,
                    'error': _("Seul un propriétaire peut transférer la propriété.")
                }, status=403)

        old_role = member.role
        old_role_display = member.get_role_display()

        with transaction.atomic():
            member.role = org_role
            member.notes = f"{member.notes}\n[{timezone.now().strftime('%d/%m/%Y')}] Changement de rôle par {request.user.username}: {old_role_display} -> {member.get_role_display()}. Raison: {reason}" if reason else member.notes
            member.save()

            logger.info(
                f"Rôle de {member.user.username} changé de {old_role} à {org_role} "
                f"par {request.user.username} dans {user_club.name}"
            )

            # Notifier le membre
            try:
                NotificationService.create_role_change_notification(member, old_role_display)
            except Exception as notif_err:
                logger.warning(f"Erreur notification changement rôle: {notif_err}")

        return JsonResponse({
            'success': True,
            'message': _("Le rôle de {} a été changé en {}.").format(
                member.user.get_full_name() or member.user.username,
                member.get_role_display()
            ),
            'member': {
                'id': member.id,
                'role': member.role,
                'role_display': member.get_role_display(),
            }
        })

    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du rôle: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
def remove_member_role_api(request, member_id):
    """
    API: Retire un membre de l'organisation.
    """
    try:
        user_club = get_user_club(request)
        if not user_club:
            return JsonResponse({
                'success': False,
                'error': _("Vous n'êtes associé à aucune organisation.")
            }, status=400)

        member = get_object_or_404(OrganizationMember, pk=member_id, organization=user_club)

        # Vérifier les permissions
        if not request.user.is_superuser and not _can_remove_member_role(request.user, member, user_club):
            return JsonResponse({
                'success': False,
                'error': _("Vous n'avez pas les permissions pour retirer ce membre.")
            }, status=403)

        member_name = member.user.get_full_name() or member.user.username if member.user else _('Membre')

        with transaction.atomic():
            # Désactiver plutôt que supprimer pour garder l'historique
            member.is_active = False
            member.membership_status = MembershipStatus.REJECTED
            member.rejection_reason = _("Retiré par {}").format(request.user.username)
            member.save()

            logger.info(
                f"Membre {member_name} retiré de {user_club.name} "
                f"par {request.user.username}"
            )

        return JsonResponse({
            'success': True,
            'message': _("{} a été retiré de l'organisation.").format(member_name)
        })

    except Exception as e:
        logger.error(f"Erreur lors du retrait du membre: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
def assign_role_to_practitioner_api(request):
    """
    API: Assigne un rôle à un pratiquant en créant un OrganizationMember.
    Utilisé quand on veut promouvoir un pratiquant à un rôle spécial.
    """
    try:
        from apps.competitions.models import Practitioner

        user_club = get_user_club(request)
        if not user_club:
            return JsonResponse({
                'success': False,
                'error': _("Vous n'êtes associé à aucune organisation.")
            }, status=400)

        # Vérifier les permissions de l'utilisateur courant
        user_membership = OrganizationMember.objects.filter(
            user=request.user,
            organization=user_club,
            role__in=[OrganizationRole.OWNER, OrganizationRole.ADMIN],
            is_active=True,
            membership_status=MembershipStatus.APPROVED
        ).first()

        # Vérifier aussi si l'utilisateur est le créateur/propriétaire du club
        is_club_owner = False
        if hasattr(user_club, 'owner') and user_club.owner == request.user:
            is_club_owner = True
        elif hasattr(user_club, 'created_by') and user_club.created_by == request.user:
            is_club_owner = True

        if not user_membership and not request.user.is_superuser and not is_club_owner:
            return JsonResponse({
                'success': False,
                'error': _("Vous n'avez pas les permissions pour assigner des rôles.")
            }, status=403)

        import json
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST

        practitioner_id = data.get('practitioner_id')
        role = data.get('role', 'member')
        reason = data.get('reason', '')

        if not practitioner_id:
            return JsonResponse({
                'success': False,
                'error': _("L'ID du pratiquant est requis.")
            }, status=400)

        # Récupérer le pratiquant
        practitioner = get_object_or_404(Practitioner, pk=practitioner_id, organization=user_club)

        # Vérifier si le pratiquant a un compte utilisateur
        if not practitioner.user:
            return JsonResponse({
                'success': False,
                'error': _("Ce pratiquant n'a pas de compte utilisateur associé. Créez d'abord un compte pour lui assigner un rôle.")
            }, status=400)

        # Vérifier si un OrganizationMember existe déjà pour ce pratiquant
        existing_membership = OrganizationMember.objects.filter(
            Q(practitioner=practitioner) | Q(user=practitioner.user) if practitioner.user else Q(practitioner=practitioner),
            organization=user_club
        ).first()

        if existing_membership:
            return JsonResponse({
                'success': False,
                'error': _("Ce pratiquant a déjà un rôle assigné. Utilisez la modification de rôle.")
            }, status=400)

        # Mapper le rôle string vers OrganizationRole
        role_mapping = {
            'member': OrganizationRole.MEMBER,
            'coach': OrganizationRole.COACH,
            'judge': OrganizationRole.JUDGE,
            'treasurer': OrganizationRole.TREASURER,
            'accountant': OrganizationRole.ACCOUNTANT,
            'manager': OrganizationRole.MANAGER,
            'admin': OrganizationRole.ADMIN,
        }

        if role not in role_mapping:
            return JsonResponse({
                'success': False,
                'error': _("Rôle invalide.")
            }, status=400)

        org_role = role_mapping[role]

        # Vérifier qu'un non-owner ne peut pas créer d'admin
        if org_role == OrganizationRole.ADMIN and user_membership and user_membership.role != OrganizationRole.OWNER:
            return JsonResponse({
                'success': False,
                'error': _("Seul un propriétaire peut créer des administrateurs.")
            }, status=403)

        # Créer le OrganizationMember
        with transaction.atomic():
            membership = OrganizationMember.objects.create(
                user=practitioner.user,
                practitioner=practitioner,
                organization=user_club,
                role=org_role,
                membership_status=MembershipStatus.APPROVED,
                is_active=True,
                notes=f"Rôle assigné par {request.user.username}. Raison: {reason}" if reason else f"Rôle assigné par {request.user.username}"
            )

            logger.info(
                f"Rôle {org_role} assigné au pratiquant {practitioner.first_name} {practitioner.last_name} "
                f"par {request.user.username} dans {user_club.name}"
            )

            # Notifier si le pratiquant a un user
            if practitioner.user:
                try:
                    NotificationService.create_role_assignment_notification(
                        membership, action='approved'
                    )
                except Exception as notif_err:
                    logger.warning(f"Erreur notification assignation rôle: {notif_err}")

        practitioner_name = f"{practitioner.first_name} {practitioner.last_name}".strip() or practitioner.license_number

        return JsonResponse({
            'success': True,
            'message': _("Le rôle {} a été assigné à {}.").format(
                membership.get_role_display(),
                practitioner_name
            ),
            'member': {
                'id': f'om_{membership.id}',
                'member_id': membership.id,
                'practitioner_id': practitioner.id,
                'name': practitioner_name,
                'role': membership.role,
                'role_display': membership.get_role_display(),
            }
        })

    except Exception as e:
        logger.error(f"Erreur lors de l'assignation du rôle au pratiquant: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

