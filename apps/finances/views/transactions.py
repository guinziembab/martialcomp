from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
)
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.db.models import Q, Sum
from django.utils import timezone

from ..models.transactions import Transaction, TransactionCategory, TransactionAttachment
from ..forms.transaction_forms import (
    TransactionForm, TransactionFilterForm, TransactionCategoryForm,
    TransactionAttachmentForm, BulkTransactionApprovalForm
)
from ..utils import get_financial_permissions
from ..utils.permissions import (
    has_finance_permission, can_view_transaction, can_validate_transaction,
    transaction_action_required
)
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset


class TransactionListView(LoginRequiredMixin, ListView):
    """Vue pour afficher la liste des transactions."""
    model = Transaction
    template_name = 'finances/transactions/list.html'
    context_object_name = 'transactions'
    paginate_by = 20
    
    def get_queryset(self):

        # Isolation par organisation
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentification requise")
        
        # Pour l'instant, récupérer toutes les transactions (sera amélioré avec l'isolation organisationnelle)
        # Les administrateurs voient toutes les transactions
        if self.request.user.is_superuser or self.request.user.is_staff:
            queryset = Transaction.objects.all()
        else:
            # Les utilisateurs normaux voient toutes les transactions pour l'instant
            # TODO: Implémenter le filtrage par organisation via financial_account
            queryset = Transaction.objects.all()
        
        # Filtrer selon les permissions de l'utilisateur
        permissions = get_financial_permissions(self.request.user)
        if not permissions.get('can_view_all_transactions', False):
            # Tenter de détecter l'organisation (club/fédération) et, si trouvée,
            # afficher toutes les transactions liées aux comptes financiers de l'organisation
            try:
                from django.contrib.contenttypes.models import ContentType
                from ..models.accounts import FinancialAccount
                from ..currency_service import _get_request_organization
                organization = _get_request_organization(self.request)
                if organization:
                    ct = ContentType.objects.get_for_model(organization.__class__)
                    owner_id = str(getattr(organization, 'id', ''))
                    org_account_ids = FinancialAccount.objects.filter(
                        owner_content_type=ct,
                        owner_id=owner_id
                    ).values('pk')
                    queryset = queryset.filter(financial_account__in=org_account_ids)
                else:
                    # Fallback: ne montrer que les transactions de l'utilisateur
                    queryset = queryset.filter(created_by=self.request.user)
            except Exception:
                queryset = queryset.filter(created_by=self.request.user)
        
        # Appliquer les filtres du formulaire
        form = TransactionFilterForm(self.request.GET or None)
        if form.is_valid():
            data = form.cleaned_data
            
            if data.get('start_date'):
                queryset = queryset.filter(date__gte=data['start_date'])
            if data.get('end_date'):
                queryset = queryset.filter(date__lte=data['end_date'])
            if data.get('type'):
                queryset = queryset.filter(type=data['type'])
            if data.get('status'):
                queryset = queryset.filter(status=data['status'])
            if data.get('category'):
                queryset = queryset.filter(category=data['category'])
            if data.get('min_amount'):
                queryset = queryset.filter(amount__gte=data['min_amount'])
            if data.get('max_amount'):
                queryset = queryset.filter(amount__lte=data['max_amount'])
            if data.get('search'):
                queryset = queryset.filter(
                    Q(description__icontains=data['search']) |
                    Q(reference__icontains=data['search'])
                )
        
        return queryset.order_by('-date', '-date_created')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = TransactionFilterForm(self.request.GET or None)
        
        # Résumé des transactions pour la période sélectionnée
        queryset = self.get_queryset()
        context['total_income'] = queryset.filter(type='income').aggregate(Sum('amount'))['amount__sum'] or 0
        context['total_expense'] = queryset.filter(type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
        context['total_balance'] = context['total_income'] - context['total_expense']
        
        # Permissions
        context['permissions'] = get_financial_permissions(self.request.user)
        
        return context


class TransactionDetailView(LoginRequiredMixin, DetailView):
    """Vue détaillée d'une transaction."""
    model = Transaction
    template_name = 'finances/transactions/detail.html'
    context_object_name = 'transaction'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['attachments'] = self.object.attachments.all()
        context['permissions'] = get_financial_permissions(self.request.user)
        return context


class TransactionCreateView(LoginRequiredMixin, CreateView):
    """Vue pour créer une nouvelle transaction."""
    model = Transaction
    form_class = TransactionForm
    template_name = 'finances/transactions/form.html'
    
    def get_template_names(self):
        """Try crispy forms template first, fallback to simple template."""
        try:
            # Test if crispy_forms is available
            import crispy_forms
            return ['finances/transactions/form.html']
        except ImportError:
            return ['finances/transactions/form_simple.html']
    
    def dispatch(self, request, *args, **kwargs):
        # Vérifier les permissions personnalisées au lieu des permissions Django strictes
        permissions = get_financial_permissions(request.user)
        if not permissions.get('can_add_transactions', False):
            from django.core.exceptions import PermissionDenied
            from django.shortcuts import render
            from django.http import HttpResponseForbidden
            
            # Afficher une page d'erreur avec des instructions claires
            context = {
                'error_title': _('Accès refusé'),
                'error_message': _('Vous n\'avez pas les permissions nécessaires pour créer des transactions.'),
                'help_text': _('Pour créer des transactions, vous devez avoir l\'un des rÃ´les suivants : Responsable de fédération, Responsable de club, Coach, ou Manager. Contactez votre administrateur pour obtenir les permissions appropriées.'),
                'user_role': getattr(request.user.profile, 'role', None) if hasattr(request.user, 'profile') else None,
                'current_permissions': permissions,
            }
            return render(request, 'finances/errors/permission_denied.html', context, status=403)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse('finances:transaction_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        
        messages.success(self.request, _('La transaction a été créée avec succès.'))
        return response
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        # Injecter request pour permettre au formulaire de filtrer par organisation
        kwargs['request'] = self.request
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Nouvelle transaction')
        context['permissions'] = get_financial_permissions(self.request.user)
        # Attacher request sur le formulaire pour filtrage org
        if 'form' in context and hasattr(context['form'], '__class__'):
            try:
                setattr(context['form'], 'request', self.request)
            except Exception:
                pass
        return context


class TransactionUpdateView(LoginRequiredMixin, UpdateView):
    """Vue pour modifier une transaction existante."""
    model = Transaction
    form_class = TransactionForm
    template_name = 'finances/transactions/form.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Vérifier les permissions personnalisées
        permissions = get_financial_permissions(request.user)
        if not permissions.get('can_add_transactions', False):
            from django.shortcuts import render
            
            context = {
                'error_title': _('Accès refusé'),
                'error_message': _('Vous n\'avez pas les permissions nécessaires pour modifier des transactions.'),
                'help_text': _('Pour modifier des transactions, vous devez avoir l\'un des rÃ´les suivants : Responsable de fédération, Responsable de club, Coach, ou Manager. Contactez votre administrateur pour obtenir les permissions appropriées.'),
                'user_role': getattr(request.user.profile, 'role', None) if hasattr(request.user, 'profile') else None,
                'current_permissions': permissions,
            }
            return render(request, 'finances/errors/permission_denied.html', context, status=403)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse('finances:transaction_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        
        messages.success(self.request, _('La transaction a été mise Ã  jour avec succès.'))
        return response
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['request'] = self.request
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Modifier la transaction')
        context['permissions'] = get_financial_permissions(self.request.user)
        # Attacher request au formulaire pour filtrer catégories par organisation
        if 'form' in context and hasattr(context['form'], '__class__'):
            try:
                setattr(context['form'], 'request', self.request)
            except Exception:
                pass
        return context


class TransactionDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Vue pour supprimer une transaction."""
    model = Transaction
    template_name = 'finances/transactions/confirm_delete.html'
    permission_required = 'finances.delete_transaction'
    success_url = reverse_lazy('finances:transaction_list')
    
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, _('La transaction a été supprimée avec succès.'))
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['permissions'] = get_financial_permissions(self.request.user)
        return context


class TransactionCategoryListView(LoginRequiredMixin, ListView):
    """Vue pour afficher la liste des catégories de transactions."""
    model = TransactionCategory
    template_name = 'finances/transactions/categories/list.html'
    context_object_name = 'categories'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['permissions'] = get_financial_permissions(self.request.user)
        return context


class TransactionCategoryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Vue pour créer une nouvelle catégorie de transaction."""
    model = TransactionCategory
    form_class = TransactionCategoryForm
    template_name = 'finances/transactions/categories/form.html'
    permission_required = 'finances.add_transactioncategory'
    success_url = reverse_lazy('finances:transaction_category_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('La catégorie a été créée avec succès.'))
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Nouvelle catégorie')
        context['permissions'] = get_financial_permissions(self.request.user)
        return context


class TransactionCategoryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Vue pour modifier une catégorie de transaction."""
    model = TransactionCategory
    form_class = TransactionCategoryForm
    template_name = 'finances/transactions/categories/form.html'
    permission_required = 'finances.change_transactioncategory'
    success_url = reverse_lazy('finances:transaction_category_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('La catégorie a été mise Ã  jour avec succès.'))
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Modifier la catégorie')
        context['permissions'] = get_financial_permissions(self.request.user)
        return context


class TransactionCategoryDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Vue pour supprimer une catégorie de transaction."""
    model = TransactionCategory
    template_name = 'finances/transactions/categories/confirm_delete.html'
    permission_required = 'finances.delete_transactioncategory'
    success_url = reverse_lazy('finances:transaction_category_list')
    
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, _('La catégorie a été supprimée avec succès.'))
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['permissions'] = get_financial_permissions(self.request.user)
        return context


@login_required
def transaction_add_attachment(request, pk):
    """Vue pour ajouter une pièce jointe Ã  une transaction."""
    transaction = get_object_or_404(Transaction, pk=pk)
    
    # Vérification des permissions
    if not request.user.has_perm('finances.change_transaction'):
        messages.error(request, _('Vous n\'avez pas les permissions nécessaires.'))
        return redirect('finances:transaction_detail', pk=transaction.pk)
    
    if request.method == 'POST':
        form = TransactionAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.transaction = transaction
            attachment.uploaded_by = request.user
            attachment.save()
            
            messages.success(request, _('La pièce jointe a été ajoutée avec succès.'))
            return redirect('finances:transaction_detail', pk=transaction.pk)
    else:
        form = TransactionAttachmentForm()
    
    return render(request, 'finances/transactions/attachment_form.html', {
        'form': form,
        'transaction': transaction,
        'permissions': get_financial_permissions(request.user)
    })


@login_required
def transaction_delete_attachment(request, transaction_pk, attachment_pk):
    """Vue pour supprimer une pièce jointe d'une transaction."""
    attachment = get_object_or_404(TransactionAttachment, pk=attachment_pk, transaction__pk=transaction_pk)
    
    # Vérification des permissions
    if not request.user.has_perm('finances.delete_transactionattachment'):
        messages.error(request, _('Vous n\'avez pas les permissions nécessaires.'))
        return redirect('finances:transaction_detail', pk=transaction_pk)
    
    if request.method == 'POST':
        attachment.delete()
        messages.success(request, _('La pièce jointe a été supprimée avec succès.'))
        return redirect('finances:transaction_detail', pk=transaction_pk)
    
    return render(request, 'finances/transactions/attachment_confirm_delete.html', {
        'attachment': attachment,
        'transaction': attachment.transaction,
        'permissions': get_financial_permissions(request.user)
    })


@login_required
@transaction_action_required(action='change_status')
def transaction_change_status(request, pk, status):
    """Vue pour changer le statut d'une transaction."""
    transaction = get_object_or_404(Transaction, pk=pk)
    
    # Appliquer le changement de statut
    try:
        if status == 'validated':
            transaction.validate(request.user)
        elif status == 'rejected':
            transaction.reject(request.user)
        elif status == 'cancelled':
            transaction.cancel(request.user)
        else:
            transaction.status = status
            transaction.updated_by = request.user
            transaction.updated_at = timezone.now()
            transaction.save()
        
        messages.success(request, _('Le statut de la transaction a été mis Ã  jour avec succès.'))
    except Exception as e:
        messages.error(request, str(e))
    
    return redirect('finances:transaction_detail', pk=transaction.pk)


class BulkTransactionApprovalView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """Vue pour approuver ou rejeter plusieurs transactions en masse."""
    template_name = 'finances/transactions/bulk_approval.html'
    form_class = BulkTransactionApprovalForm
    permission_required = 'finances.validate_transaction'
    success_url = reverse_lazy('finances:transaction_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtenir les transactions éligibles (en attente)
        transactions = Transaction.objects.filter(status='pending')
        
        # Filtrer selon les permissions utilisateur
        permissions = get_financial_permissions(self.request.user)
        if not permissions.get('can_approve_all_transactions', False):
            # Si l'utilisateur ne peut pas approuver toutes les transactions, 
            # filtrer selon d'autres critères comme la catégorie ou le montant
            pass
        
        context['transactions'] = transactions
        context['permissions'] = permissions
        return context
    
    def form_valid(self, form):
        data = form.cleaned_data
        action = data.get('action')
        selected_transactions = data.get('transactions', [])
        
        if not selected_transactions:
            messages.warning(self.request, _('Aucune transaction sélectionnée.'))
            return redirect(self.success_url)
        
        count = 0
        for transaction_id in selected_transactions:
            try:
                transaction = Transaction.objects.get(pk=transaction_id, status='pending')
                
                if action == 'validate':
                    transaction.validate(self.request.user)
                elif action == 'reject':
                    transaction.reject(self.request.user)
                
                count += 1
            except Transaction.DoesNotExist:
                continue
            except Exception as e:
                messages.error(self.request, f"Erreur pour la transaction {transaction_id}: {str(e)}")
        
        if action == 'validate':
            messages.success(self.request, _('%d transactions ont été validées avec succès.') % count)
        else:
            messages.success(self.request, _('%d transactions ont été rejetées avec succès.') % count)
        
        return super().form_valid(form)
