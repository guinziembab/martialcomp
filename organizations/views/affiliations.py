"""
Vues liées à la gestion des affiliations entre organisations.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, UpdateView
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

from ..models import Organization, Affiliation
from ..forms import AffiliationForm


class AffiliationCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Vue pour créer une nouvelle affiliation."""
    model = Affiliation
    form_class = AffiliationForm
    template_name = 'organizations/affiliation_form.html'
    
    def test_func(self):
        """Vérifie si l'utilisateur a le droit de créer une affiliation."""
        # Récupérer l'organisation depuis les paramètres
        organization_id = self.kwargs.get('organization_id')
        if not organization_id:
            return False
            
        organization = get_object_or_404(Organization, id=organization_id)
        return organization.can_user_edit(self.request.user)
    
    def get_form_kwargs(self):
        """Passe les paramètres nécessaires au formulaire."""
        kwargs = super().get_form_kwargs()
        
        # Récupérer l'organisation et le type d'affiliation
        organization_id = self.kwargs.get('organization_id')
        affiliation_direction = self.kwargs.get('direction', 'parent')
        
        if organization_id:
            organization = get_object_or_404(Organization, id=organization_id)
            
            if affiliation_direction == 'parent':
                # Affiliation à une organisation parente
                kwargs['child_org'] = organization
            else:
                # Affiliation d'une organisation enfant
                kwargs['parent_org'] = organization
        
        return kwargs
    
    def get_context_data(self, **kwargs):
        """Ajoute des données supplémentaires au contexte."""
        context = super().get_context_data(**kwargs)
        
        organization_id = self.kwargs.get('organization_id')
        affiliation_direction = self.kwargs.get('direction', 'parent')
        
        organization = get_object_or_404(Organization, id=organization_id)
        context['organization'] = organization
        
        if affiliation_direction == 'parent':
            context['title'] = _("Ajouter une affiliation à une organisation parente")
            context['subtitle'] = _("Affilier {} à une autre organisation").format(organization.name)
        else:
            context['title'] = _("Ajouter une organisation affiliée")
            context['subtitle'] = _("Affilier une organisation à {}").format(organization.name)
        
        return context
    
    def form_valid(self, form):
        """Traitement lorsque le formulaire est valide."""
        messages.success(self.request, _("L'affiliation a été créée avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        """Redirection après succès."""
        return reverse('organizations:detail', kwargs={'pk': self.kwargs.get('organization_id')})


class AffiliationUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Vue pour modifier une affiliation existante."""
    model = Affiliation
    form_class = AffiliationForm
    template_name = 'organizations/affiliation_form.html'
    
    def test_func(self):
        """Vérifie si l'utilisateur a le droit de modifier l'affiliation."""
        affiliation = self.get_object()
        # Vérifier les droits sur l'une des deux organisations
        return (
            affiliation.parent_organization.can_user_edit(self.request.user) or
            affiliation.child_organization.can_user_edit(self.request.user)
        )
    
    def get_context_data(self, **kwargs):
        """Ajoute des données supplémentaires au contexte."""
        context = super().get_context_data(**kwargs)
        context['title'] = _("Modifier l'affiliation")
        affiliation = self.get_object()
        context['organization'] = affiliation.parent_organization
        return context
    
    def form_valid(self, form):
        """Traitement lorsque le formulaire est valide."""
        messages.success(self.request, _("L'affiliation a été mise à jour avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        """Redirection après succès."""
        affiliation = self.get_object()
        return reverse('organizations:detail', kwargs={'pk': affiliation.parent_organization.pk})


@login_required
@require_POST
def delete_affiliation(request, pk):
    """Vue pour supprimer une affiliation."""
    affiliation = get_object_or_404(Affiliation, pk=pk)
    
    # Vérifier les permissions
    if not (
        affiliation.parent_organization.can_user_edit(request.user) or
        affiliation.child_organization.can_user_edit(request.user)
    ):
        return HttpResponseForbidden(_("Vous n'avez pas les droits pour supprimer cette affiliation."))
    
    # Mémoriser l'organisation pour la redirection
    organization = affiliation.parent_organization
    
    # Supprimer l'affiliation
    affiliation.delete()
    
    messages.success(request, _("L'affiliation a été supprimée avec succès."))
    return redirect('organizations:detail', pk=organization.pk)