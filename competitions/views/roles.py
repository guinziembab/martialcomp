# competitions/views/roles.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse

from competitions.models import Club
from competitions.models.permissions import ClubRole, UserClubRole
from competitions.utils.decorators import club_required
from django.contrib.auth.models import User

@login_required
@club_required
def manage_roles(request):
    """Vue principale pour la gestion des rôles de club."""
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
        
        # Filtrer les rôles utilisateur par organization également
        user_roles = UserClubRole.objects.filter(organization=club_organization).select_related('user', 'role')
    
    # Regrouper les utilisateurs par rôle
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
    """Créer un nouveau rôle pour le club."""
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
        
        # Vérifier si le nom de rôle existe déjà pour cette organisation
        if ClubRole.objects.filter(organization=club_organization, name=role_name).exists():
            messages.error(request, _("Un rôle avec ce nom existe déjà."))
            return redirect('competitions:club:manage_roles')
        
        # Créer le rôle avec organization au lieu de club
        role = ClubRole.objects.create(
            organization=club_organization,
            name=role_name,
            description=description,
            is_default=is_default,
            **permissions
        )
        
        messages.success(request, _("Le rôle a été créé avec succès."))
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
    """Modifier un rôle existant."""
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
        
        messages.success(request, _("Le rôle a été mis à jour avec succès."))
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
    """Supprimer un rôle."""
    club = request.club
    
    # Récupérer l'organisation associée au club
    club_organization = getattr(club, 'organization', None) or getattr(club, 'as_organization', None)
    
    if not club_organization:
        messages.error(request, _("Aucune organisation associée trouvée pour ce club."))
        return redirect('competitions:club:manage_roles')
    
    # Filtrer par organization au lieu de club
    role = get_object_or_404(ClubRole, id=role_id, organization=club_organization)
    
    if request.method == 'POST':
        # Vérifier si le rôle est utilisé
        if UserClubRole.objects.filter(role=role).exists():
            messages.error(request, _("Ce rôle ne peut pas être supprimé car il est attribué à des utilisateurs."))
            return redirect('competitions:club:manage_roles')
        
        role.delete()
        messages.success(request, _("Le rôle a été supprimé avec succès."))
        return redirect('competitions:club:manage_roles')
        
    # Si méthode GET, afficher la confirmation
    return render(request, 'competitions/club/confirm_delete.html', {
        'club': club,
        'organization': club_organization,
        'object': role,
        'object_name': role.name,
        'message': _("Êtes-vous sûr de vouloir supprimer ce rôle ?"),
    })

@login_required
@club_required
def assign_role(request):
    """Attribuer un rôle à un utilisateur."""
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
        
        # Vérifier si l'attribution existe déjà
        if UserClubRole.objects.filter(user=user, organization=club_organization, role=role).exists():
            messages.warning(request, _("Cet utilisateur a déjà ce rôle."))
        else:
            # Créer l'attribution avec organization au lieu de club
            UserClubRole.objects.create(
                user=user,
                organization=club_organization,
                role=role,
                assigned_by=request.user,
            )
            messages.success(request, _("Rôle attribué avec succès."))
        
        return redirect('competitions:club:manage_roles')
    
    # Si méthode GET, afficher le formulaire
    roles = ClubRole.objects.filter(organization=club_organization)
    
    # Récupérer les utilisateurs associés au club (par exemple, les pratiquants du club)
    # Adapter cette requête selon la nouvelle structure de données
    from competitions.models import Practitioner
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
    """Révoquer un rôle attribué à un utilisateur."""
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
        messages.success(request, _("Rôle révoqué avec succès."))
        return redirect('competitions:club:manage_roles')
    
    # Si méthode GET, afficher la confirmation
    return render(request, 'competitions/club/confirm_delete.html', {
        'club': club,
        'organization': club_organization,
        'object': user_role,
        'object_name': f"{user_role.user.username} - {user_role.role.name}",
        'message': _("Êtes-vous sûr de vouloir révoquer ce rôle ?"),
    })