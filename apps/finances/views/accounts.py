from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, FormView, TemplateView
)
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, Sum
from django.utils import timezone
from django.core.exceptions import PermissionDenied

from ..models.accounts import (
    AccountingCategory, FinancialAccount, MembershipFee
)
from ..forms.accounts_forms import (
    AccountingCategoryForm, FinancialAccountForm, MembershipFeeForm
)
from ..utils import get_financial_permissions
from ..currency_service import _get_request_organization
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset


class AccountingCategoryListView(LoginRequiredMixin, ListView):
    """Vue pour afficher la liste des catégories comptables."""
    model = AccountingCategory
    template_name = 'finances/accounts/categories/list.html'
    context_object_name = 'categories'
    
    def dispatch(self, request, *args, **kwargs):
        # Permettre l'accès aux utilisateurs avec permissions financières
        permissions = get_financial_permissions(request.user)
        if not permissions.get('can_view_accounts', False):
            from django.contrib import messages
            from django.shortcuts import redirect
            messages.error(request, _("Vous n'avez pas les permissions nécessaires."))
            return redirect('finances:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):

        # Isolation par organisation
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentification requise")
        
        # Pour l'instant, récupérer toutes les catégories comptables (sera amélioré avec l'isolation organisationnelle)
        # Les administrateurs voient toutes les catégories comptables
        if self.request.user.is_superuser or self.request.user.is_staff:
            return AccountingCategory.objects.all().order_by('name')
        else:
            # Les utilisateurs normaux voient toutes les catégories comptables pour l'instant
            # TODO: Implémenter le filtrage par organisation
            return AccountingCategory.objects.all().order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['permissions'] = get_financial_permissions(self.request.user)
        
        # Obtenir toutes les catégories pour affichage hiérarchique
        all_categories = AccountingCategory.objects.all()
        context['all_categories'] = all_categories
        
        # Construire une structure hiérarchique pour faciliter l'affichage
        hierarchy = {}
        for category in all_categories:
            if category.parent_id:
                if category.parent_id not in hierarchy:
                    hierarchy[category.parent_id] = []
                hierarchy[category.parent_id].append(category)
        
        context['category_hierarchy'] = hierarchy
        return context


class AccountingCategoryCreateView(LoginRequiredMixin, CreateView):
    """Vue pour créer une nouvelle catégorie comptable."""
    model = AccountingCategory
    form_class = AccountingCategoryForm
    template_name = 'finances/accounts/categories/form.html'
    success_url = reverse_lazy('finances:accounts:accounting_category_list')
    
    def dispatch(self, request, *args, **kwargs):
        # Vérifier les permissions financières
        permissions = get_financial_permissions(request.user)
        if not permissions.get('can_manage_accounts', False):
            messages.error(request, _("Vous n'avez pas les permissions nécessaires pour créer des catégories comptables."))
            return redirect('finances:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('La catégorie comptable a été créée avec succès.'))
        return response

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Passer l'organisation détectée au formulaire pour lier la catégorie
        organization = _get_request_organization(self.request)
        if organization:
            kwargs['organization'] = organization
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Nouvelle catégorie comptable')
        context['permissions'] = get_financial_permissions(self.request.user)
        
        # Récupérer l'ID du parent si spécifié dans l'URL
        parent_id = self.request.GET.get('parent')
        if parent_id:
            try:
                parent = AccountingCategory.objects.get(pk=parent_id)
                context['parent'] = parent
                # Pré-remplir le formulaire avec le parent
                context['form'].initial['parent'] = parent
            except AccountingCategory.DoesNotExist:
                pass
                
        return context


class AccountingCategoryUpdateView(LoginRequiredMixin, UpdateView):
    """Vue pour modifier une catégorie comptable."""
    model = AccountingCategory
    form_class = AccountingCategoryForm
    template_name = 'finances/accounts/categories/form.html'
    success_url = reverse_lazy('finances:accounts:accounting_category_list')
    
    def dispatch(self, request, *args, **kwargs):
        # Vérifier les permissions financières
        permissions = get_financial_permissions(request.user)
        if not permissions.get('can_manage_accounts', False):
            messages.error(request, _("Vous n'avez pas les permissions nécessaires pour modifier des catégories comptables."))
            return redirect('finances:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        # Vérifier si on essaie de définir un parent qui créerait une boucle
        instance = form.instance
        if form.cleaned_data.get('parent'):
            parent = form.cleaned_data['parent']
            # Si le parent est l'instance elle-mÃªme, c'est une boucle directe
            if parent.id == instance.id:
                form.add_error('parent', _('Une catégorie ne peut pas Ãªtre son propre parent.'))
                return self.form_invalid(form)
                
            # Vérifier les boucles indirectes (si un descendant devient le parent)
            descendants = instance.get_descendants()
            if parent.id in [desc.id for desc in descendants]:
                form.add_error('parent', _('Vous ne pouvez pas définir comme parent une sous-catégorie.'))
                return self.form_invalid(form)
        
        response = super().form_valid(form)
        messages.success(self.request, _('La catégorie comptable a été mise Ã  jour avec succès.'))
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Modifier la catégorie comptable')
        context['permissions'] = get_financial_permissions(self.request.user)
        return context


class AccountingCategoryDeleteView(LoginRequiredMixin, DeleteView):
    """Vue pour supprimer une catégorie comptable."""
    model = AccountingCategory
    template_name = 'finances/accounts/categories/confirm_delete.html'
    success_url = reverse_lazy('finances:accounts:accounting_category_list')
    
    def dispatch(self, request, *args, **kwargs):
        # Vérifier les permissions financières
        permissions = get_financial_permissions(request.user)
        if not permissions.get('can_manage_accounts', False):
            messages.error(request, _("Vous n'avez pas les permissions nécessaires pour supprimer des catégories comptables."))
            return redirect('finances:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        
        # Vérifier si la catégorie a des enfants
        if category.children.exists():
            messages.error(request, _('Impossible de supprimer une catégorie qui contient des sous-catégories.'))
            return redirect('finances:accounts:accounting_category_list')
            
        # Vérifier si la catégorie est utilisée (via InvoiceItem ou MembershipFee)
        if category.invoiceitem_set.exists() or category.membershipfee_set.exists():
            messages.error(request, _(
                'Impossible de supprimer une catégorie utilisée dans des transactions. '
                'Vous pouvez la désactiver Ã  la place.'
            ))
            return redirect('finances:accounts:accounting_category_list')
            
        response = super().delete(request, *args, **kwargs)
        messages.success(request, _('La catégorie comptable a été supprimée avec succès.'))
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['permissions'] = get_financial_permissions(self.request.user)
        
        # Vérifier si la catégorie peut Ãªtre supprimée
        category = self.get_object()
        context['has_children'] = category.children.exists()
        context['is_used'] = category.invoiceitem_set.exists() or category.membershipfee_set.exists()
        
        return context


@login_required
def accounting_category_parent_options(request):
    """Retourne la liste des catégories parentes filtrées par type et organisation (JSON)."""
    permissions = get_financial_permissions(request.user)
    if not permissions.get('can_manage_accounts', False) and not permissions.get('can_view_accounts', False):
        return JsonResponse({'error': 'forbidden'}, status=403)

    category_type = request.GET.get('type')
    queryset = get_organization_queryset(AccountingCategory, request.user)

    if category_type in ('income', 'expense'):
        queryset = queryset.filter(type=category_type)

    # Filtrer par organisation si disponible
    organization = _get_request_organization(request)
    if organization:
        ct = ContentType.objects.get_for_model(organization.__class__)
        queryset = queryset.filter(
            Q(organization_content_type__isnull=True, organization_id__isnull=True)
            | Q(organization_content_type=ct, organization_id=str(organization.pk))
        )

    data = [
        {
            'id': str(cat.pk),
            'name': getattr(cat, 'full_name', cat.name),
        }
        for cat in queryset.order_by('name')
    ]
    return JsonResponse({'results': data})

class FinancialAccountListView(LoginRequiredMixin, ListView):
    """Vue pour afficher la liste des comptes financiers."""
    model = FinancialAccount
    template_name = 'finances/accounts/financial/list.html'
    context_object_name = 'financial_accounts'
    
    def dispatch(self, request, *args, **kwargs):
        # Permettre l'accès aux utilisateurs avec permissions financières
        permissions = get_financial_permissions(request.user)
        if not permissions.get('can_view_accounts', False):
            from django.contrib import messages
            from django.shortcuts import redirect
            messages.error(request, _("Vous n'avez pas les permissions nécessaires."))
            return redirect('finances:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):

        # Isolation par organisation
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentification requise")
        
        # Pour l'instant, récupérer tous les comptes financiers (sera amélioré avec l'isolation organisationnelle)
        # Les administrateurs voient tous les comptes financiers
        if self.request.user.is_superuser or self.request.user.is_staff:
            queryset = FinancialAccount.objects.all()
        else:
            # Les utilisateurs normaux voient tous les comptes financiers pour l'instant
            # TODO: Implémenter le filtrage par organisation
            queryset = FinancialAccount.objects.all()
        
        # Recherche
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) |
                Q(description__icontains=q)
            )
        
        # Filtre par type
        account_type = self.request.GET.get('type')
        if account_type:
            queryset = queryset.filter(account_type=account_type)
            
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['permissions'] = get_financial_permissions(self.request.user)
        
        # Calcul du solde total
        accounts = context['financial_accounts']
        context['total_balance'] = sum(account.current_balance for account in accounts if hasattr(account, 'current_balance'))
        
        return context


class FinancialAccountDetailView(LoginRequiredMixin, DetailView):
    """Vue détaillée d'un compte financier."""
    model = FinancialAccount
    template_name = 'finances/accounts/financial/detail.html'
    context_object_name = 'account'
    
    def dispatch(self, request, *args, **kwargs):
        # Vérifier les permissions financières
        permissions = get_financial_permissions(request.user)
        if not permissions.get('can_view_accounts', False):
            messages.error(request, _("Vous n'avez pas les permissions nécessaires."))
            return redirect('finances:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['permissions'] = get_financial_permissions(self.request.user)

        # Récupérer les transactions récentes pour ce compte
        # Le related_name par défaut est 'transaction_set' (pas 'transactions')
        context['recent_transactions'] = self.object.transaction_set.all().order_by('-date')[:10]

        return context


class FinancialAccountCreateView(LoginRequiredMixin, CreateView):
    """Vue pour créer un nouveau compte financier."""
    model = FinancialAccount
    form_class = FinancialAccountForm
    template_name = 'finances/accounts/financial/form.html'
    success_url = reverse_lazy('finances:accounts:financial_account_list')
    
    def dispatch(self, request, *args, **kwargs):
        # Vérifier les permissions financières
        permissions = get_financial_permissions(request.user)
        if not permissions.get('can_manage_accounts', False):
            messages.error(request, _("Vous n'avez pas les permissions nécessaires pour créer des comptes financiers."))
            return redirect('finances:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Le compte financier a été créé avec succès.'))
        return response

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Déterminer l'entité propriétaire (organisation) et la passer au formulaire
        owner = _get_request_organization(self.request) or getattr(self.request, 'user', None)
        if owner:
            kwargs['owner'] = owner
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Nouveau compte financier')
        context['permissions'] = get_financial_permissions(self.request.user)
        return context


class FinancialAccountUpdateView(LoginRequiredMixin, UpdateView):
    """Vue pour modifier un compte financier."""
    model = FinancialAccount
    form_class = FinancialAccountForm
    template_name = 'finances/accounts/financial/form.html'
    
    def get_success_url(self):
        return reverse('finances:accounts:financial_account_detail', kwargs={'pk': self.object.pk})
    
    def dispatch(self, request, *args, **kwargs):
        # Vérifier les permissions financières
        permissions = get_financial_permissions(request.user)
        if not permissions.get('can_manage_accounts', False):
            messages.error(request, _("Vous n'avez pas les permissions nécessaires pour modifier des comptes financiers."))
            return redirect('finances:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Le compte financier a été mis Ã  jour avec succès.'))
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Modifier le compte financier')
        context['permissions'] = get_financial_permissions(self.request.user)
        return context


class FinancialAccountDeleteView(LoginRequiredMixin, DeleteView):
    """Vue pour supprimer un compte financier."""
    model = FinancialAccount
    template_name = 'finances/accounts/financial/confirm_delete.html'
    success_url = reverse_lazy('finances:accounts:financial_account_list')
    
    def dispatch(self, request, *args, **kwargs):
        # Vérifier les permissions financières
        permissions = get_financial_permissions(request.user)
        if not permissions.get('can_manage_accounts', False):
            messages.error(request, _("Vous n'avez pas les permissions nécessaires pour supprimer des comptes financiers."))
            return redirect('finances:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        account = self.get_object()
        
        # Vérifier si le compte a des transactions
        if account.transaction_set.exists():
            messages.error(request, _(
                'Impossible de supprimer un compte qui contient des transactions. '
                'Vous pouvez le désactiver Ã  la place.'
            ))
            return redirect('finances:accounts:financial_account_detail', pk=account.pk)
            
        response = super().delete(request, *args, **kwargs)
        messages.success(request, _('Le compte financier a été supprimé avec succès.'))
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['permissions'] = get_financial_permissions(self.request.user)
        
        # Vérifier si le compte peut Ãªtre supprimé
        account = self.get_object()
        context['has_transactions'] = account.transaction_set.exists()
        
        return context


class MembershipFeeListView(LoginRequiredMixin, ListView):
    """Vue pour afficher la liste des cotisations."""
    model = MembershipFee
    template_name = 'finances/accounts/membership/list.html'
    context_object_name = 'membership_fees'
    
    def dispatch(self, request, *args, **kwargs):
        # Permettre l'accès aux utilisateurs avec permissions financières
        permissions = get_financial_permissions(request.user)
        if not permissions.get('can_view_accounts', False):
            from django.contrib import messages
            from django.shortcuts import redirect
            messages.error(request, _("Vous n'avez pas les permissions nécessaires."))
            return redirect('finances:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):

        # Isolation par organisation
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentification requise")
        
        # Pour l'instant, récupérer toutes les cotisations (sera amélioré avec l'isolation organisationnelle)
        # Les administrateurs voient toutes les cotisations
        if self.request.user.is_superuser or self.request.user.is_staff:
            queryset = MembershipFee.objects.all()
        else:
            # Les utilisateurs normaux voient toutes les cotisations pour l'instant
            # TODO: Implémenter le filtrage par organisation
            queryset = MembershipFee.objects.all()
        
        # Filtre par fréquence
        frequency = self.request.GET.get('frequency')
        if frequency:
            queryset = queryset.filter(frequency=frequency)
            
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['permissions'] = get_financial_permissions(self.request.user)
        return context


class MembershipFeeCreateView(LoginRequiredMixin, CreateView):
    """Vue pour créer une nouvelle cotisation."""
    model = MembershipFee
    form_class = MembershipFeeForm
    template_name = 'finances/accounts/membership/form.html'
    success_url = reverse_lazy('finances:accounts:membership_fee_list')
    
    def dispatch(self, request, *args, **kwargs):
        # Vérifier les permissions financières
        permissions = get_financial_permissions(request.user)
        if not permissions.get('can_manage_memberships', False):
            messages.error(request, _("Vous n'avez pas les permissions nécessaires pour créer des cotisations."))
            return redirect('finances:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('La cotisation a été créée avec succès.'))
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Nouvelle cotisation')
        context['permissions'] = get_financial_permissions(self.request.user)
        return context


class MembershipFeeUpdateView(LoginRequiredMixin, UpdateView):
    """Vue pour modifier une cotisation."""
    model = MembershipFee
    form_class = MembershipFeeForm
    template_name = 'finances/accounts/membership/form.html'
    success_url = reverse_lazy('finances:accounts:membership_fee_list')
    
    def dispatch(self, request, *args, **kwargs):
        # Vérifier les permissions financières
        permissions = get_financial_permissions(request.user)
        if not permissions.get('can_manage_memberships', False):
            messages.error(request, _("Vous n'avez pas les permissions nécessaires pour modifier des cotisations."))
            return redirect('finances:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('La cotisation a été mise Ã  jour avec succès.'))
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Modifier la cotisation')
        context['permissions'] = get_financial_permissions(self.request.user)
        return context


class MembershipFeeDeleteView(LoginRequiredMixin, DeleteView):
    """Vue pour supprimer une cotisation."""
    model = MembershipFee
    template_name = 'finances/accounts/membership/confirm_delete.html'
    success_url = reverse_lazy('finances:accounts:membership_fee_list')
    
    def dispatch(self, request, *args, **kwargs):
        # Vérifier les permissions financières
        permissions = get_financial_permissions(request.user)
        if not permissions.get('can_manage_memberships', False):
            messages.error(request, _("Vous n'avez pas les permissions nécessaires pour supprimer des cotisations."))
            return redirect('finances:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, _('La cotisation a été supprimée avec succès.'))
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['permissions'] = get_financial_permissions(self.request.user)
        return context
