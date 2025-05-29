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
from django.views.decorators.http import require_POST

from ..models.payments import PaymentMethod, PaymentAttempt
from ..models.invoices import Invoice
from ..forms.payment_forms import (
    PaymentMethodForm, PaymentAttemptForm, PaymentProcessForm
)
from ..utils import get_financial_permissions


class PaymentMethodListView(LoginRequiredMixin, ListView):
    """Vue pour afficher la liste des méthodes de paiement."""
    model = PaymentMethod
    template_name = 'finances/payments/methods/list.html'
    context_object_name = 'payment_methods'
    
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
        return PaymentMethod.objects.all().order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['permissions'] = get_financial_permissions(self.request.user)
        return context


class PaymentMethodCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Vue pour créer une nouvelle méthode de paiement."""
    model = PaymentMethod
    form_class = PaymentMethodForm
    template_name = 'finances/payment/methods/form.html'
    permission_required = 'finances.add_paymentmethod'
    success_url = reverse_lazy('finances:payment_method_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('La méthode de paiement a été créée avec succès.'))
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Nouvelle méthode de paiement')
        context['permissions'] = get_financial_permissions(self.request.user)
        return context


class PaymentMethodUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Vue pour modifier une méthode de paiement."""
    model = PaymentMethod
    form_class = PaymentMethodForm
    template_name = 'finances/payment/methods/form.html'
    permission_required = 'finances.change_paymentmethod'
    success_url = reverse_lazy('finances:payment_method_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('La méthode de paiement a été mise à jour avec succès.'))
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Modifier la méthode de paiement')
        context['permissions'] = get_financial_permissions(self.request.user)
        return context


class PaymentMethodDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Vue pour supprimer une méthode de paiement."""
    model = PaymentMethod
    template_name = 'finances/payment/methods/confirm_delete.html'
    permission_required = 'finances.delete_paymentmethod'
    success_url = reverse_lazy('finances:payment_method_list')
    
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, _('La méthode de paiement a été supprimée avec succès.'))
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['permissions'] = get_financial_permissions(self.request.user)
        return context


class PaymentAttemptListView(LoginRequiredMixin, ListView):
    """Vue pour afficher la liste des tentatives de paiement."""
    model = PaymentAttempt
    template_name = 'finances/payment/attempts/list.html'
    context_object_name = 'payment_attempts'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = PaymentAttempt.objects.all()
        
        # Filtrer selon les permissions de l'utilisateur
        permissions = get_financial_permissions(self.request.user)
        if not permissions.get('can_view_all_payments', False):
            # Si l'utilisateur ne peut pas voir tous les paiements, 
            # ne montrer que ceux liés à ses entités
            # Ce filtre dépend des relations spécifiques dans votre modèle
            pass
        
        # Recherche et filtres
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(reference__icontains=q) |
                Q(invoice__number__icontains=q) |
                Q(notes__icontains=q)
            )
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        method = self.request.GET.get('method')
        if method:
            queryset = queryset.filter(payment_method_id=method)
            
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['permissions'] = get_financial_permissions(self.request.user)
        context['payment_methods'] = PaymentMethod.objects.filter(active=True)
        context['status_choices'] = PaymentAttempt.STATUS_CHOICES
        return context


class PaymentAttemptDetailView(LoginRequiredMixin, DetailView):
    """Vue détaillée d'une tentative de paiement."""
    model = PaymentAttempt
    template_name = 'finances/payment/attempts/detail.html'
    context_object_name = 'payment_attempt'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['permissions'] = get_financial_permissions(self.request.user)
        return context


class PaymentAttemptCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Vue pour créer une nouvelle tentative de paiement."""
    model = PaymentAttempt
    form_class = PaymentAttemptForm
    template_name = 'finances/payment/attempts/form.html'
    permission_required = 'finances.add_paymentattempt'
    
    def get_success_url(self):
        return reverse('finances:payment_attempt_detail', kwargs={'pk': self.object.pk})
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        
        # Si la tentative est liée à une facture existante
        invoice_id = self.request.GET.get('invoice')
        if invoice_id:
            kwargs['invoice'] = get_object_or_404(Invoice, pk=invoice_id)
            
        return kwargs
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        
        messages.success(self.request, _('La tentative de paiement a été créée avec succès.'))
        
        # Rediriger vers le processus de paiement si nécessaire
        if form.instance.status == 'pending' and form.instance.payment_method.processor != 'manual':
            return redirect('finances:process_payment', pk=self.object.pk)
            
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Nouvelle tentative de paiement')
        context['permissions'] = get_financial_permissions(self.request.user)
        
        # Afficher des informations sur la facture si applicable
        invoice_id = self.request.GET.get('invoice')
        if invoice_id:
            context['invoice'] = get_object_or_404(Invoice, pk=invoice_id)
            
        return context


@login_required
def process_payment(request, pk):
    """Vue pour traiter un paiement en attente."""
    payment_attempt = get_object_or_404(
        PaymentAttempt, 
        pk=pk, 
        status='pending'
    )
    
    # Vérifier les permissions
    if not request.user.has_perm('finances.process_payment'):
        messages.error(request, _('Vous n\'avez pas les permissions nécessaires.'))
        return redirect('finances:payment_attempt_detail', pk=payment_attempt.pk)
    
    if request.method == 'POST':
        form = PaymentProcessForm(request.POST, instance=payment_attempt)
        if form.is_valid():
            # Logique de traitement selon le processeur de paiement
            processor = payment_attempt.payment_method.processor
            
            try:
                # Simuler la logique de traitement des différentes passerelles de paiement
                if processor == 'stripe':
                    # Intégrer ici la logique Stripe
                    payment_attempt.processor_response = {'success': True, 'transaction_id': 'stripe_1234'}
                    payment_attempt.status = 'completed'
                elif processor == 'paypal':
                    # Intégrer ici la logique PayPal
                    payment_attempt.processor_response = {'success': True, 'transaction_id': 'paypal_1234'}
                    payment_attempt.status = 'completed'
                elif processor == 'manual':
                    # Traitement manuel, mettre à jour selon le formulaire
                    payment_attempt.status = form.cleaned_data.get('result', 'completed')
                    payment_attempt.processor_response = {'manual_notes': form.cleaned_data.get('notes', '')}
                
                # Mettre à jour les informations
                payment_attempt.processed_at = timezone.now()
                payment_attempt.processed_by = request.user
                payment_attempt.save()
                
                # Mettre à jour la facture associée si le paiement est réussi
                if payment_attempt.status == 'completed' and payment_attempt.invoice:
                    payment_attempt.invoice.mark_as_paid(
                        payment_method=payment_attempt.payment_method,
                        payment_reference=payment_attempt.reference,
                        payment_date=payment_attempt.processed_at,
                        user=request.user
                    )
                
                messages.success(request, _('Le paiement a été traité avec succès.'))
                return redirect('finances:payment_attempt_detail', pk=payment_attempt.pk)
                
            except Exception as e:
                messages.error(request, _('Erreur lors du traitement: %(error)s') % {'error': str(e)})
                payment_attempt.status = 'failed'
                payment_attempt.processor_response = {'error': str(e)}
                payment_attempt.save()
    else:
        form = PaymentProcessForm(instance=payment_attempt)
    
    # Choisir le template en fonction du processeur
    processor = payment_attempt.payment_method.processor
    template_name = f'finances/payment/processors/{processor}_form.html'
    
    # Fallback vers un template générique si le template spécifique n'existe pas
    try:
        render(request, template_name, {'form': form})
    except:
        template_name = 'finances/payment/processors/generic_form.html'
    
    return render(request, template_name, {
        'form': form,
        'payment_attempt': payment_attempt,
        'permissions': get_financial_permissions(request.user)
    })


@require_POST
@login_required
def cancel_payment(request, pk):
    """Vue pour annuler une tentative de paiement en attente."""
    payment_attempt = get_object_or_404(
        PaymentAttempt, 
        pk=pk, 
        status='pending'
    )
    
    # Vérifier les permissions
    if not request.user.has_perm('finances.process_payment'):
        messages.error(request, _('Vous n\'avez pas les permissions nécessaires.'))
        return redirect('finances:payment_attempt_detail', pk=payment_attempt.pk)
    
    payment_attempt.status = 'cancelled'
    payment_attempt.processed_at = timezone.now()
    payment_attempt.processed_by = request.user
    payment_attempt.notes = payment_attempt.notes + '\n' + _('Annulé par %(user)s le %(date)s') % {
        'user': request.user.get_full_name() or request.user.username,
        'date': timezone.now().strftime('%d/%m/%Y %H:%M')
    }
    payment_attempt.save()
    
    messages.success(request, _('La tentative de paiement a été annulée.'))
    return redirect('finances:payment_attempt_detail', pk=payment_attempt.pk)


@login_required
def payment_method_options(request):
    """Vue pour obtenir les détails d'une méthode de paiement en AJAX."""
    if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Only AJAX requests are allowed'}, status=400)
    
    method_id = request.GET.get('method_id')
    if not method_id:
        return JsonResponse({'error': 'Method ID is required'}, status=400)
    
    try:
        method = PaymentMethod.objects.get(pk=method_id, active=True)
        
        # Calculer les frais pour le montant donné
        amount = request.GET.get('amount')
        fee = 0
        total = 0
        
        if amount:
            try:
                amount = float(amount)
                fee = method.calculate_fee(amount)
                total = amount + fee
            except ValueError:
                pass
                
        return JsonResponse({
            'id': method.id,
            'name': method.name,
            'description': method.description,
            'processor': method.processor,
            'fee_fixed': method.fee_fixed,
            'fee_percentage': method.fee_percentage,
            'calculated_fee': fee,
            'total_with_fee': total,
            'needs_manual_validation': method.processor == 'manual',
            'instructions': method.instructions,
        })
    except PaymentMethod.DoesNotExist:
        return JsonResponse({'error': 'Payment method not found'}, status=404)