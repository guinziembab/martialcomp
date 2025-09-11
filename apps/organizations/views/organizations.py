from django.core.exceptions import PermissionDenied
"""
Vues liées Ã  la gestion des organisations.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models import Q

from ..models import Organization, OrganizationMember, OrganizationRole
from ..forms import OrganizationForm, OrganizationSearchForm
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset


class OrganizationListView(LoginRequiredMixin, ListView):
    """Vue pour afficher la liste des organisations."""
    model = Organization
    template_name = 'organizations/organization_list.html'
    context_object_name = 'organizations'
    paginate_by = 20
    
    def get_queryset(self):

        # Isolation par organisation
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentification requise")
        
        # Utiliser l'isolation organisationnelle
        base_queryset = get_organization_queryset(self.queryset.model, self.request.user)
        
        # Les administrateurs voient tous les objets de leur organisation
        if self.request.user.is_superuser or self.request.user.is_staff:
            return base_queryset

        """Filtre les organisations selon les paramètres de recherche."""
        queryset = super().get_queryset()
        
        # Appliquer les filtres
        org_type = self.request.GET.get('type')
        country = self.request.GET.get('country')
        search_query = self.request.GET.get('q')
        
        if org_type:
            queryset = queryset.filter(organization_type=org_type)
        
        if country:
            queryset = queryset.filter(country=country)
        
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(short_name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        """Ajoute des données supplémentaires au contexte."""
        context = super().get_context_data(**kwargs)
        
        # Récupérer les choix pour les types d'organisations
        context['organization_types'] = dict(Organization._meta.get_field('organization_type').choices)
        
        # Récupérer les paramètres de filtrage
        context['selected_type'] = self.request.GET.get('type', '')
        context['selected_country'] = self.request.GET.get('country', '')
        context['search_query'] = self.request.GET.get('q', '')
        
        # Liste des pays disponibles (distinct)
        countries = Organization.objects.exclude(
            country__isnull=True
        ).exclude(
            country__exact=''
        ).values_list('country', flat=True).distinct().order_by('country')
        
        # Créer le formulaire de recherche
        context['search_form'] = OrganizationSearchForm(
            initial={
                'q': context['search_query'],
                'type': context['selected_type'],
                'country': context['selected_country'],
            },
            countries=countries
        )
        
        # Statistiques
        context['total_organizations'] = Organization.objects.count()
        context['active_organizations'] = Organization.objects.filter(is_active=True).count()
        
        # Personnaliser pour l'utilisateur connecté
        if self.request.user.is_authenticated:
            # Organisations dont l'utilisateur est membre
            context['user_organizations'] = Organization.objects.filter(
                members__user=self.request.user,
                members__is_active=True
            ).distinct()
        
        return context


class OrganizationDetailView(LoginRequiredMixin, DetailView):
    """Vue détaillée d'une organisation."""
    model = Organization
    template_name = 'organizations/organization_detail.html'
    context_object_name = 'organization'
    
    def get_context_data(self, **kwargs):
        """Ajoute des données supplémentaires au contexte."""
        context = super().get_context_data(**kwargs)
        organization = self.get_object()
        
        # Affiliations de l'organisation
        context['parent_affiliations'] = organization.parent_affiliations.filter(
            is_active=True
        ).select_related('parent_organization').order_by('parent_organization__name')
        
        context['child_affiliations'] = organization.child_affiliations.filter(
            is_active=True
        ).select_related('child_organization').order_by('child_organization__name')
        
        # Membres de l'organisation
        context['members'] = organization.members.filter(
            is_active=True
        ).select_related('user').order_by('role', 'user__last_name')
        
        # Vérifier si l'utilisateur est membre/admin de cette organisation
        if self.request.user.is_authenticated:
            try:
                user_membership = OrganizationMember.objects.get(
                    organization=organization,
                    user=self.request.user,
                    is_active=True
                )
                context['user_membership'] = user_membership
                context['can_edit'] = organization.can_user_edit(self.request.user)
                context['can_manage_members'] = organization.can_user_manage_members(self.request.user)
            except OrganizationMember.DoesNotExist:
                context['can_edit'] = False
                context['can_manage_members'] = False
        
        # Statistiques
        context['members_count'] = organization.members.filter(is_active=True).count()
        context['affiliations_count'] = (
            organization.parent_affiliations.filter(is_active=True).count() +
            organization.child_affiliations.filter(is_active=True).count()
        )
        
        # Compétitions
        if hasattr(organization, 'organized_competitions'):
            context['competitions'] = organization.organized_competitions.all()[:5]
            context['competitions_count'] = organization.organized_competitions.count()
        
        return context


class OrganizationCreateView(LoginRequiredMixin, CreateView):
    """Vue pour créer une nouvelle organisation."""
    model = Organization
    form_class = OrganizationForm
    template_name = 'organizations/organization_form.html'
    
    def get_form_kwargs(self):
        """Passe l'utilisateur courant au formulaire."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        """Ajoute des données supplémentaires au contexte."""
        context = super().get_context_data(**kwargs)
        context['title'] = _("Créer une organisation")
        return context
    
    def form_valid(self, form):
        """Traitement lorsque le formulaire est valide."""
        messages.success(self.request, _("L'organisation a été créée avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        """Redirection après succès."""
        return reverse('organizations:detail', kwargs={'pk': self.object.pk})


class OrganizationUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Vue pour modifier une organisation existante."""
    model = Organization
    form_class = OrganizationForm
    template_name = 'organizations/organization_form.html'
    
    def test_func(self):
        """Vérifie si l'utilisateur a le droit de modifier l'organisation."""
        organization = self.get_object()
        return organization.can_user_edit(self.request.user)
    
    def get_form_kwargs(self):
        """Passe l'utilisateur courant au formulaire."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        """Ajoute des données supplémentaires au contexte."""
        context = super().get_context_data(**kwargs)
        context['title'] = _("Modifier l'organisation")
        return context
    
    def form_valid(self, form):
        """Traitement lorsque le formulaire est valide."""
        messages.success(self.request, _("L'organisation a été mise Ã  jour avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        """Redirection après succès."""
        return reverse('organizations:detail', kwargs={'pk': self.object.pk})


class OrganizationDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Vue pour supprimer une organisation."""
    model = Organization
    template_name = 'organizations/organization_confirm_delete.html'
    success_url = reverse_lazy('organizations:list')
    context_object_name = 'organization'
    
    def test_func(self):
        """Vérifie si l'utilisateur a le droit de supprimer l'organisation."""
        organization = self.get_object()
        # Seul un propriétaire ou un super-utilisateur peut supprimer
        if self.request.user.is_superuser:
            return True
            
        try:
            membership = OrganizationMember.objects.get(
                organization=organization,
                user=self.request.user,
                role=OrganizationRole.OWNER,
                is_active=True
            )
            return True
        except OrganizationMember.DoesNotExist:
            return False
    
    def delete(self, request, *args, **kwargs):
        """Traitement de la suppression."""
        organization = self.get_object()
        
        # Vérifier les dépendances avant de supprimer
        has_affiliations = (
            organization.parent_affiliations.exists() or
            organization.child_affiliations.exists()
        )
        
        # Si des dépendances existent, refuser la suppression
        if has_affiliations:
            messages.error(request, _(
                "Cette organisation ne peut pas Ãªtre supprimée car elle a des affiliations. "
                "Veuillez supprimer toutes les affiliations avant de supprimer l'organisation."
            ))
            return redirect('organizations:detail', pk=organization.pk)
        
        messages.success(request, _("L'organisation a été supprimée avec succès."))
        return super().delete(request, *args, **kwargs)
