from django.core.exceptions import PermissionDenied
"""
Vues liées Ã  la gestion des membres des organisations.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden
from django.db import transaction
from django.db.models import Q

from ..models import Organization, OrganizationMember, OrganizationRole
from ..forms import OrganizationMemberForm
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset


class OrganizationMemberListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Vue pour afficher la liste des membres d'une organisation."""
    model = OrganizationMember
    template_name = 'organizations/member_list.html'
    context_object_name = 'members'
    paginate_by = 50
    
    def test_func(self):
        """Vérifie si l'utilisateur a le droit de voir les membres."""
        organization_id = self.kwargs.get('organization_id')
        if not organization_id:
            return False
            
        # Vérifier si l'utilisateur est membre de l'organisation
        organization = get_object_or_404(Organization, id=organization_id)
        return organization.is_user_member(self.request.user)
    
    def get_queryset(self):

        # Isolation par organisation
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentification requise")
        
        # Utiliser l'isolation organisationnelle
        base_queryset = get_organization_queryset(self.queryset.model, self.request.user)
        
        # Les administrateurs voient tous les objets de leur organisation
        if self.request.user.is_superuser or self.request.user.is_staff:
            return base_queryset

        """Filtre les membres par organisation."""
        organization_id = self.kwargs.get('organization_id')
        queryset = OrganizationMember.objects.filter(
            organization_id=organization_id
        ).select_related('user')
        
        # Filtre par statut
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        # Filtre par rÃ´le
        role = self.request.GET.get('role')
        if role:
            queryset = queryset.filter(role=role)
        
        # Recherche
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(user__username__icontains=search_query) |
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(title__icontains=search_query)
            )
        
        return queryset.order_by('role', 'user__last_name', 'user__first_name')
    
    def get_context_data(self, **kwargs):
        """Ajoute des données supplémentaires au contexte."""
        context = super().get_context_data(**kwargs)
        
        organization_id = self.kwargs.get('organization_id')
        organization = get_object_or_404(Organization, id=organization_id)
        context['organization'] = organization
        
        # Paramètres de filtrage
        context['selected_status'] = self.request.GET.get('status', '')
        context['selected_role'] = self.request.GET.get('role', '')
        context['search_query'] = self.request.GET.get('q', '')
        
        # Vérifier les permissions de l'utilisateur
        context['can_manage_members'] = organization.can_user_manage_members(self.request.user)
        
        # Récupérer les rÃ´les disponibles
        context['roles'] = dict(OrganizationRole.choices)
        
        return context


class OrganizationMemberCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Vue pour ajouter un membre Ã  une organisation."""
    model = OrganizationMember
    form_class = OrganizationMemberForm
    template_name = 'organizations/member_form.html'
    
    def test_func(self):
        """Vérifie si l'utilisateur a le droit d'ajouter un membre."""
        organization_id = self.kwargs.get('organization_id')
        if not organization_id:
            return False
            
        # Vérifier si l'utilisateur peut gérer les membres
        organization = get_object_or_404(Organization, id=organization_id)
        return organization.can_user_manage_members(self.request.user)
    
    def get_form_kwargs(self):
        """Passe l'organisation au formulaire."""
        kwargs = super().get_form_kwargs()
        
        organization_id = self.kwargs.get('organization_id')
        organization = get_object_or_404(Organization, id=organization_id)
        kwargs['organization'] = organization
        
        return kwargs
    
    def get_context_data(self, **kwargs):
        """Ajoute des données supplémentaires au contexte."""
        context = super().get_context_data(**kwargs)
        
        organization_id = self.kwargs.get('organization_id')
        organization = get_object_or_404(Organization, id=organization_id)
        context['organization'] = organization
        context['title'] = _("Ajouter un membre")
        
        return context
    
    def form_valid(self, form):
        """Traitement lorsque le formulaire est valide."""
        organization_id = self.kwargs.get('organization_id')
        form.instance.organization_id = organization_id
        
        messages.success(self.request, _("Le membre a été ajouté avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        """Redirection après succès."""
        return reverse('organizations:members', kwargs={'organization_id': self.kwargs.get('organization_id')})


class OrganizationMemberUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Vue pour modifier un membre d'une organisation."""
    model = OrganizationMember
    form_class = OrganizationMemberForm
    template_name = 'organizations/member_form.html'
    
    def test_func(self):
        """Vérifie si l'utilisateur a le droit de modifier un membre."""
        member = self.get_object()
        return member.organization.can_user_manage_members(self.request.user)
    
    def get_context_data(self, **kwargs):
        """Ajoute des données supplémentaires au contexte."""
        context = super().get_context_data(**kwargs)
        
        member = self.get_object()
        context['organization'] = member.organization
        context['title'] = _("Modifier le membre")
        context['member'] = member
        
        return context
    
    def form_valid(self, form):
        """Traitement lorsque le formulaire est valide."""
        messages.success(self.request, _("Le membre a été mis Ã  jour avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        """Redirection après succès."""
        member = self.get_object()
        return reverse('organizations:members', kwargs={'organization_id': member.organization.id})


@login_required
@require_POST
def delete_member(request, pk):
    """Vue pour supprimer un membre d'une organisation."""
    member = get_object_or_404(OrganizationMember, pk=pk)
    
    # Vérifier les permissions
    if not member.organization.can_user_manage_members(request.user):
        return HttpResponseForbidden(_("Vous n'avez pas les droits pour supprimer ce membre."))
    
    # Mémoriser l'organisation pour la redirection
    organization = member.organization
    
    # Vérifier si c'est le propriétaire
    if member.role == OrganizationRole.OWNER:
        # Vérifier s'il y a d'autres membres actifs
        if OrganizationMember.objects.filter(
            organization=organization,
            is_active=True
        ).exclude(id=member.id).exists():
            messages.error(request, _(
                "Vous ne pouvez pas supprimer le propriétaire. "
                "Veuillez d'abord transférer la propriété Ã  un autre membre."
            ))
            return redirect('organizations:members', organization_id=organization.id)
    
    # Supprimer le membre
    member.delete()
    
    messages.success(request, _("Le membre a été supprimé avec succès."))
    return redirect('organizations:members', organization_id=organization.id)


@login_required
@require_POST
def transfer_ownership(request, pk):
    """Vue pour transférer la propriété d'une organisation."""
    member = get_object_or_404(OrganizationMember, pk=pk)
    organization = member.organization
    
    # Vérifier si l'utilisateur actuel est le propriétaire
    try:
        current_owner = OrganizationMember.objects.get(
            organization=organization,
            role=OrganizationRole.OWNER,
            is_active=True
        )
        
        if current_owner.user != request.user:
            messages.error(request, _("Seul le propriétaire actuel peut transférer la propriété."))
            return redirect('organizations:members', organization_id=organization.id)
            
    except OrganizationMember.DoesNotExist:
        messages.error(request, _("L'organisation n'a pas de propriétaire défini."))
        return redirect('organizations:members', organization_id=organization.id)
    
    # Vérifier que le membre choisi n'est pas déjÃ  le propriétaire
    if member.role == OrganizationRole.OWNER:
        messages.error(request, _("Ce membre est déjÃ  le propriétaire de l'organisation."))
        return redirect('organizations:members', organization_id=organization.id)
    
    with transaction.atomic():
        # Mettre Ã  jour l'ancien propriétaire
        current_owner.role = OrganizationRole.ADMIN
        current_owner.save()
        
        # Mettre Ã  jour le nouveau propriétaire
        member.role = OrganizationRole.OWNER
        member.can_manage_members = True
        member.can_edit_organization = True
        member.can_manage_competitions = True
        member.save()
        
    messages.success(request, _("La propriété a été transférée avec succès."))
    return redirect('organizations:members', organization_id=organization.id)
