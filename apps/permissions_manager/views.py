from django.core.exceptions import PermissionDenied
# permissions_manager/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

from .models import Permission, Role, UserRoleAssignment
from .auth import user_has_permission
from .decorators import permission_required
from .forms import RoleForm, UserRoleAssignmentForm
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

@login_required
@permission_required('permission.view_role')
def role_list(request):
    """Liste des rÃ´les disponibles"""
    roles = get_organization_queryset(Role, self.request.user).order_by('context_type', 'name')
    
    # Filtrage par type de contexte
    context_type = request.GET.get('context_type')
    if context_type:
        roles = roles.filter(context_type=context_type)
    
    # Recherche
    search_query = request.GET.get('q')
    if search_query:
        roles = roles.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    context = {
        'roles': roles,
        'context_types': [choice[0] for choice in Role._meta.get_field('context_type').choices],
        'selected_context_type': context_type,
        'search_query': search_query,
    }
    return render(request, 'permissions_manager/role_list.html', context)

@login_required
@permission_required('permission.view_role')
def role_detail(request, pk):
    """Détails d'un rÃ´le et de ses permissions"""
    role = get_object_or_404(Role, pk=pk)
    
    # Récupérer les utilisateurs ayant ce rÃ´le
    assignments = UserRoleAssignment.objects.filter(
        role=role,
        is_active=True
    ).select_related('user')
    
    context = {
        'role': role,
        'assignments': assignments,
        'permissions': role.permissions.all().order_by('category', 'code'),
    }
    return render(request, 'permissions_manager/role_detail.html', context)

@login_required
@permission_required('permission.add_role')
def role_create(request):
    """Création d'un nouveau rÃ´le"""
    if request.method == 'POST':
        form = RoleForm(request.POST)
        if form.is_valid():
            role = form.save()
            messages.success(request, _("Le rÃ´le a été créé avec succès."))
            return redirect('permissions_manager:role_detail', pk=role.pk)
    else:
        form = RoleForm()
    
    context = {
        'form': form,
        'title': _("Créer un nouveau rÃ´le"),
    }
    return render(request, 'permissions_manager/role_form.html', context)

@login_required
@permission_required('permission.change_role')
def role_update(request, pk):
    """Modification d'un rÃ´le existant"""
    role = get_object_or_404(Role, pk=pk)
    
    # Vérifier si c'est un rÃ´le système (non modifiable)
    if role.is_system_role and not request.user.is_superuser:
        messages.error(request, _("Les rÃ´les système ne peuvent pas Ãªtre modifiés."))
        return redirect('permissions_manager:role_detail', pk=role.pk)
    
    if request.method == 'POST':
        form = RoleForm(request.POST, instance=role)
        if form.is_valid():
            form.save()
            messages.success(request, _("Le rÃ´le a été mis Ã  jour avec succès."))
            return redirect('permissions_manager:role_detail', pk=role.pk)
    else:
        form = RoleForm(instance=role)
    
    context = {
        'form': form,
        'role': role,
        'title': _("Modifier le rÃ´le"),
    }
    return render(request, 'permissions_manager/role_form.html', context)

@login_required
@permission_required('permission.delete_role')
def role_delete(request, pk):
    """Suppression d'un rÃ´le"""
    role = get_object_or_404(Role, pk=pk)
    
    # Vérifier si c'est un rÃ´le système (non supprimable)
    if role.is_system_role and not request.user.is_superuser:
        messages.error(request, _("Les rÃ´les système ne peuvent pas Ãªtre supprimés."))
        return redirect('permissions_manager:role_detail', pk=role.pk)
    
    if request.method == 'POST':
        # Vérifier s'il y a des attributions actives
        active_assignments = UserRoleAssignment.objects.filter(role=role, is_active=True).count()
        if active_assignments > 0 and not request.POST.get('confirm_with_assignments'):
            # Demander confirmation si le rÃ´le est utilisé
            messages.warning(request, _(
                "Ce rÃ´le est attribué Ã  %(count)d utilisateurs. "
                "Cochez la case pour confirmer la suppression."
            ) % {'count': active_assignments})
            return render(request, 'permissions_manager/role_confirm_delete.html', {
                'role': role,
                'active_assignments': active_assignments,
                'show_confirm_checkbox': True,
            })
        
        # Supprimer le rÃ´le
        role.delete()
        messages.success(request, _("Le rÃ´le a été supprimé avec succès."))
        return redirect('permissions_manager:role_list')
    
    context = {
        'role': role,
        'active_assignments': UserRoleAssignment.objects.filter(role=role, is_active=True).count(),
    }
    return render(request, 'permissions_manager/role_confirm_delete.html', context)

@login_required
@permission_required('permission.view_userroleassignment')
def user_role_list(request):
    """Liste des attributions de rÃ´les aux utilisateurs"""
    assignments = UserRoleAssignment.objects.select_related('user', 'role').order_by('-created_at')
    
    # Filtres
    role_id = request.GET.get('role')
    is_active = request.GET.get('is_active')
    context_type = request.GET.get('context_type')
    search_query = request.GET.get('q')
    
    if role_id:
        assignments = assignments.filter(role_id=role_id)
    
    if is_active:
        is_active_bool = is_active == 'true'
        assignments = assignments.filter(is_active=is_active_bool)
    
    if context_type:
        if context_type == 'global':
            assignments = assignments.filter(content_type__isnull=True, object_id__isnull=True)
        else:
            content_types = ContentType.objects.filter(model__icontains=context_type)
            assignments = assignments.filter(content_type__in=content_types)
    
    if search_query:
        assignments = assignments.filter(
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(role__name__icontains=search_query)
        )
    
    context = {
        'assignments': assignments,
        'roles': get_organization_queryset(Role, self.request.user),
        'selected_role': role_id,
        'selected_is_active': is_active,
        'selected_context_type': context_type,
        'search_query': search_query,
    }
    return render(request, 'permissions_manager/user_role_list.html', context)

@login_required
@permission_required('permission.add_userroleassignment')
def user_role_create(request):
    """Attribution d'un rÃ´le Ã  un utilisateur"""
    if request.method == 'POST':
        form = UserRoleAssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.assigned_by = request.user
            assignment.save()
            messages.success(request, _("Le rÃ´le a été attribué avec succès."))
            return redirect('permissions_manager:user_role_list')
    else:
        form = UserRoleAssignmentForm()
    
    context = {
        'form': form,
        'title': _("Attribuer un rÃ´le"),
    }
    return render(request, 'permissions_manager/user_role_form.html', context)

@login_required
@permission_required('permission.change_userroleassignment')
def user_role_update(request, pk):
    """Modification d'une attribution de rÃ´le"""
    assignment = get_object_or_404(UserRoleAssignment, pk=pk)
    
    if request.method == 'POST':
        form = UserRoleAssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            form.save()
            messages.success(request, _("L'attribution de rÃ´le a été mise Ã  jour avec succès."))
            return redirect('permissions_manager:user_role_list')
    else:
        form = UserRoleAssignmentForm(instance=assignment)
    
    context = {
        'form': form,
        'assignment': assignment,
        'title': _("Modifier l'attribution de rÃ´le"),
    }
    return render(request, 'permissions_manager/user_role_form.html', context)

@login_required
@permission_required('permission.delete_userroleassignment')
def user_role_delete(request, pk):
    """Suppression d'une attribution de rÃ´le"""
    assignment = get_object_or_404(UserRoleAssignment, pk=pk)
    
    if request.method == 'POST':
        assignment.delete()
        messages.success(request, _("L'attribution de rÃ´le a été supprimée avec succès."))
        return redirect('permissions_manager:user_role_list')
    
    context = {
        'assignment': assignment,
    }
    return render(request, 'permissions_manager/user_role_confirm_delete.html', context)

@login_required
@permission_required('permission.view_userroleassignment')
def entity_roles(request, content_type, object_id):
    """Vue des rÃ´les attribués dans une entité spécifique"""
    # Récupérer le modèle et l'objet
    try:
        content_type_obj = ContentType.objects.get(pk=content_type)
        entity = content_type_obj.get_object_for_this_type(pk=object_id)
    except (ContentType.DoesNotExist, Exception) as e:
        messages.error(request, _("Entité introuvable: %(error)s") % {'error': str(e)})
        return redirect('permissions_manager:user_role_list')
    
    # Récupérer les attributions de rÃ´le pour cette entité
    assignments = UserRoleAssignment.objects.filter(
        content_type=content_type_obj,
        object_id=object_id,
        is_active=True
    ).select_related('user', 'role')
    
    context = {
        'entity': entity,
        'entity_type': content_type_obj.name,
        'assignments': assignments,
    }
    return render(request, 'permissions_manager/entity_roles.html', context)

@login_required
@permission_required('permission.view_userroleassignment')
def user_roles(request, user_id):
    """Vue des rÃ´les attribués Ã  un utilisateur spécifique"""
    user = get_object_or_404(User, pk=user_id)
    
    # Récupérer toutes les attributions de rÃ´le pour cet utilisateur
    assignments = UserRoleAssignment.objects.filter(
        user=user,
        is_active=True
    ).select_related('role')
    
    # Regrouper par type de contexte
    assignments_by_context = {}
    for a in assignments:
        context_name = "Global"
        if a.context:
            context_name = f"{a.content_type.name}: {a.context}"
        
        if context_name not in assignments_by_context:
            assignments_by_context[context_name] = []
            
        assignments_by_context[context_name].append(a)
    
    context = {
        'user_obj': user,
        'assignments_by_context': assignments_by_context,
    }
    return render(request, 'permissions_manager/user_roles.html', context)
