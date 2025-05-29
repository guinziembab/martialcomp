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
        # Récupérer toutes les catégories
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


class AccountingCategoryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Vue pour créer une nouvelle catégorie comptable."""
    model = AccountingCategory
    form_class = AccountingCategoryForm
    template_name = 'finances/accounts/categories/form.html'
    permission_required = 'finances.add_accountingcategory'
    success_url = reverse_lazy('finances:accounting_category_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('La catégorie comptable a été créée avec succès.'))
        return response
    
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


class AccountingCategoryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Vue pour modifier une catégorie comptable."""
    model = AccountingCategory
    form_class = AccountingCategoryForm
    template_name = 'finances/accounts/categories/form.html'
    permission_required = 'finances.change_accountingcategory'
    success_url = reverse_lazy('finances:accounting_category_list')
    
    def form_valid(self, form):
        # Vérifier si on essaie de définir un parent qui créerait une boucle
        instance = form.instance
        if form.cleaned_data.get('parent'):
            parent = form.cleaned_data['parent']
            # Si le parent est l'instance elle-même, c'est une boucle directe
            if parent.id == instance.id:
                form.add_error('parent', _('Une catégorie ne peut pas être son propre parent.'))
                return self.form_invalid(form)
                
            # Vérifier les boucles indirectes (si un descendant devient le parent)
            descendants = instance.get_descendants()
            if parent.id in [desc.id for desc in descendants]:
                form.add_error('parent', _('Vous ne pouvez pas définir comme parent une sous-catégorie.'))
                return self.form_invalid(form)
        
        response = super().form_valid(form)
        messages.success(self.request, _('La catégorie comptable a été mise à jour avec succès.'))
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Modifier la catégorie comptable')
        context['permissions'] = get_financial_permissions(self.request.user)
        return context


class AccountingCategoryDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Vue pour supprimer une catégorie comptable."""
    model = AccountingCategory
    template_name = 'finances/accounts/categories/confirm_delete.html'
    permission_required = 'finances.delete_accountingcategory'
    success_url = reverse_lazy('finances:accounting_category_list')
    
    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        
        # Vérifier si la catégorie a des enfants
        if category.children.exists():
            messages.error(request, _('Impossible de supprimer une catégorie qui contient des sous-catégories.'))
            return redirect('finances:accounting_category_list')
            
        # Vérifier si la catégorie est utilisée
        if category.transactions.exists():
            messages.error(request, _(
                'Impossible de supprimer une catégorie utilisée dans des transactions. '
                'Vous pouvez la désactiver à la place.'
            ))
            return redirect('finances:accounting_category_list')
            
        response = super().delete(request, *args, **kwargs)
        messages.success(request, _('La catégorie comptable a été supprimée avec succès.'))
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['permissions'] = get_financial_permissions(self.request.user)
        
        # Vérifier si la catégorie peut être supprimée
        category = self.get_object()
        context['has_children'] = category.children.exists()
        context['is_used'] = category.transactions.exists()
        
        return context


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


class FinancialAccountDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Vue détaillée d'un compte financier."""
    model = FinancialAccount
    template_name = 'finances/accounts/financial/detail.html'
    context_object_name = 'account'
    permission_required = 'finances.view_financialaccount'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['permissions'] = get_financial_permissions(self.request.user)
        
        # Récupérer les transactions récentes pour ce compte
        context['recent_transactions'] = self.object.transactions.all().order_by('-date')[:10]
        
        return context


class FinancialAccountCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Vue pour créer un nouveau compte financier."""
    model = FinancialAccount
    form_class = FinancialAccountForm
    template_name = 'finances/accounts/financial/form.html'
    permission_required = 'finances.add_financialaccount'
    success_url = reverse_lazy('finances:financial_account_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Le compte financier a été créé avec succès.'))
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Nouveau compte financier')
        context['permissions'] = get_financial_permissions(self.request.user)
        return context


class FinancialAccountUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Vue pour modifier un compte financier."""
    model = FinancialAccount
    form_class = FinancialAccountForm
    template_name = 'finances/accounts/financial/form.html'
    permission_required = 'finances.change_financialaccount'
    
    def get_success_url(self):
        return reverse('finances:financial_account_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Le compte financier a été mis à jour avec succès.'))
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Modifier le compte financier')
        context['permissions'] = get_financial_permissions(self.request.user)
        return context


class FinancialAccountDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Vue pour supprimer un compte financier."""
    model = FinancialAccount
    template_name = 'finances/accounts/financial/confirm_delete.html'
    permission_required = 'finances.delete_financialaccount'
    success_url = reverse_lazy('finances:financial_account_list')
    
    def delete(self, request, *args, **kwargs):
        account = self.get_object()
        
        # Vérifier si le compte a des transactions
        if account.transactions.exists():
            messages.error(request, _(
                'Impossible de supprimer un compte qui contient des transactions. '
                'Vous pouvez le désactiver à la place.'
            ))
            return redirect('finances:financial_account_detail', pk=account.pk)
            
        response = super().delete(request, *args, **kwargs)
        messages.success(request, _('Le compte financier a été supprimé avec succès.'))
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['permissions'] = get_financial_permissions(self.request.user)
        
        # Vérifier si le compte peut être supprimé
        account = self.get_object()
        context['has_transactions'] = account.transactions.exists()
        
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


class MembershipFeeCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Vue pour créer une nouvelle cotisation."""
    model = MembershipFee
    form_class = MembershipFeeForm
    template_name = 'finances/accounts/membership/form.html'
    permission_required = 'finances.add_membershipfee'
    success_url = reverse_lazy('finances:membership_fee_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('La cotisation a été créée avec succès.'))
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Nouvelle cotisation')
        context['permissions'] = get_financial_permissions(self.request.user)
        return context


class MembershipFeeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Vue pour modifier une cotisation."""
    model = MembershipFee
    form_class = MembershipFeeForm
    template_name = 'finances/accounts/membership/form.html'
    permission_required = 'finances.change_membershipfee'
    success_url = reverse_lazy('finances:membership_fee_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('La cotisation a été mise à jour avec succès.'))
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Modifier la cotisation')
        context['permissions'] = get_financial_permissions(self.request.user)
        return context


class MembershipFeeDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Vue pour supprimer une cotisation."""
    model = MembershipFee
    template_name = 'finances/accounts/membership/confirm_delete.html'
    permission_required = 'finances.delete_membershipfee'
    success_url = reverse_lazy('finances:membership_fee_list')
    
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, _('La cotisation a été supprimée avec succès.'))
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['permissions'] = get_financial_permissions(self.request.user)
        return context