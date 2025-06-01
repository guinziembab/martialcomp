from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
)
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.exceptions import PermissionDenied

from ..models.invoices import Invoice, InvoiceItem
from ..models.payments import PaymentMethod
from ..forms.invoice_forms import (
    InvoiceForm, InvoiceItemFormSet, InvoiceFilterForm,
    InvoicePaymentForm
)
from ..utils import get_financial_permissions, render_to_pdf


class InvoiceListView(LoginRequiredMixin, ListView):
    """Vue pour afficher la liste des factures."""
    model = Invoice
    template_name = 'finances/invoices/list.html'
    context_object_name = 'invoices'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Invoice.objects.all()
        
        # Filtrer selon les permissions de l'utilisateur
        permissions = get_financial_permissions(self.request.user)
        if not permissions.get('can_view_all_invoices', False):
            # Si l'utilisateur ne peut pas voir toutes les factures, 
            # ne montrer que celles liées à ses entités
            # Ce filtre dépend des relations spécifiques dans votre modèle
            pass
        
        # Appliquer les filtres du formulaire
        form = InvoiceFilterForm(self.request.GET or None)
        if form.is_valid():
            data = form.cleaned_data
            
            if data.get('start_date'):
                queryset = queryset.filter(issued_date__gte=data['start_date'])
            if data.get('end_date'):
                queryset = queryset.filter(issued_date__lte=data['end_date'])
            if data.get('status'):
                queryset = queryset.filter(status=data['status'])
            if data.get('min_amount'):
                queryset = queryset.filter(total__gte=data['min_amount'])
            if data.get('max_amount'):
                queryset = queryset.filter(total__lte=data['max_amount'])
            if data.get('search'):
                queryset = queryset.filter(
                    Q(number__icontains=data['search']) |
                    Q(client_name__icontains=data['search']) |
                    Q(notes__icontains=data['search'])
                )
        
        return queryset.order_by('-issued_date', '-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = InvoiceFilterForm(self.request.GET or None)
        
        # Statistiques et totaux
        queryset = self.get_queryset()
        context['total_amount'] = queryset.aggregate(Sum('total'))['total__sum'] or 0
        context['unpaid_amount'] = queryset.filter(status='unpaid').aggregate(Sum('total'))['total__sum'] or 0
        context['paid_amount'] = queryset.filter(status='paid').aggregate(Sum('total'))['total__sum'] or 0
        
        # Permissions
        context['permissions'] = get_financial_permissions(self.request.user)
        
        return context


class InvoiceDetailView(LoginRequiredMixin, DetailView):
    """Vue détaillée d'une facture."""
    model = Invoice
    template_name = 'finances/invoices/detail.html'
    context_object_name = 'invoice'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all()
        context['payments'] = self.object.payment_attempts.all()
        context['payment_methods'] = PaymentMethod.objects.filter(active=True)
        context['permissions'] = get_financial_permissions(self.request.user)
        
        # Formulaire de paiement si la facture est impayée
        if self.object.status == 'unpaid':
            context['payment_form'] = InvoicePaymentForm(invoice=self.object)
            
        return context


class InvoiceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Vue pour créer une nouvelle facture."""
    model = Invoice
    form_class = InvoiceForm
    template_name = 'finances/invoices/form.html'
    permission_required = 'finances.add_invoice'
    
    def get_success_url(self):
        return reverse('finances:invoice_detail', kwargs={'pk': self.object.pk})
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.POST:
            context['formset'] = InvoiceItemFormSet(self.request.POST)
        else:
            context['formset'] = InvoiceItemFormSet()
            
        context['title'] = _('Nouvelle facture')
        context['permissions'] = get_financial_permissions(self.request.user)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            form.instance.created_by = self.request.user
            form.instance.updated_by = self.request.user
            self.object = form.save()
            
            # Sauvegarder les éléments de la facture
            instances = formset.save(commit=False)
            for instance in instances:
                instance.invoice = self.object
                instance.save()
            
            # Recalculer le total de la facture après l'ajout des éléments
            self.object.recalculate_total()
            
            messages.success(self.request, _('La facture a été créée avec succès.'))
            return redirect(self.get_success_url())
        else:
            return self.form_invalid(form)


class InvoiceUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Vue pour modifier une facture existante."""
    model = Invoice
    form_class = InvoiceForm
    template_name = 'finances/invoices/form.html'
    permission_required = 'finances.change_invoice'
    
    def get_success_url(self):
        return reverse('finances:invoice_detail', kwargs={'pk': self.object.pk})
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.POST:
            context['formset'] = InvoiceItemFormSet(
                self.request.POST, 
                instance=self.object
            )
        else:
            context['formset'] = InvoiceItemFormSet(instance=self.object)
            
        context['title'] = _('Modifier la facture')
        context['permissions'] = get_financial_permissions(self.request.user)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            form.instance.updated_by = self.request.user
            form.instance.updated_at = timezone.now()
            self.object = form.save()
            
            # Sauvegarder les éléments de la facture
            instances = formset.save(commit=False)
            for instance in instances:
                instance.invoice = self.object
                instance.save()
            
            # Supprimer les éléments marqués pour suppression
            for obj in formset.deleted_objects:
                obj.delete()
            
            # Recalculer le total de la facture après modification des éléments
            self.object.recalculate_total()
            
            messages.success(self.request, _('La facture a été mise à jour avec succès.'))
            return redirect(self.get_success_url())
        else:
            return self.form_invalid(form)


class InvoiceDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Vue pour supprimer une facture."""
    model = Invoice
    template_name = 'finances/invoices/confirm_delete.html'
    permission_required = 'finances.delete_invoice'
    success_url = reverse_lazy('finances:invoice_list')
    
    def delete(self, request, *args, **kwargs):
        # Vérifier si la facture est payée ou a des paiements associés
        invoice = self.get_object()
        if invoice.status == 'paid' or invoice.payment_attempts.exists():
            messages.error(request, _('Impossible de supprimer une facture payée ou avec des paiements associés.'))
            return redirect('finances:invoice_detail', pk=invoice.pk)
            
        response = super().delete(request, *args, **kwargs)
        messages.success(request, _('La facture a été supprimée avec succès.'))
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['permissions'] = get_financial_permissions(self.request.user)
        return context


@login_required
def invoice_pay(request, pk):
    """Vue pour enregistrer un paiement pour une facture."""
    invoice = get_object_or_404(Invoice, pk=pk, status='unpaid')
    
    # Vérifier les permissions
    if not request.user.has_perm('finances.process_payment'):
        messages.error(request, _('Vous n\'avez pas les permissions nécessaires.'))
        return redirect('finances:invoice_detail', pk=invoice.pk)
    
    if request.method == 'POST':
        form = InvoicePaymentForm(request.POST, invoice=invoice)
        if form.is_valid():
            payment_method = form.cleaned_data['payment_method']
            notes = form.cleaned_data.get('notes', '')
            
            # Créer une tentative de paiement
            payment_attempt = invoice.create_payment_attempt(
                payment_method=payment_method,
                amount=invoice.total,
                notes=notes,
                created_by=request.user
            )
            
            # Si c'est un paiement manuel, le marquer comme complété directement
            if payment_method.processor == 'manual':
                payment_attempt.status = 'completed'
                payment_attempt.processed_at = timezone.now()
                payment_attempt.processed_by = request.user
                payment_attempt.save()
                
                # Marquer la facture comme payée
                invoice.mark_as_paid(
                    payment_method=payment_method,
                    payment_reference=payment_attempt.reference,
                    payment_date=timezone.now(),
                    user=request.user
                )
                
                messages.success(request, _('Le paiement manuel a été enregistré avec succès.'))
                return redirect('finances:invoice_detail', pk=invoice.pk)
            else:
                # Rediriger vers le processus de paiement
                return redirect('finances:process_payment', pk=payment_attempt.pk)
    else:
        form = InvoicePaymentForm(invoice=invoice)
    
    return render(request, 'finances/invoices/payment_form.html', {
        'form': form,
        'invoice': invoice,
        'permissions': get_financial_permissions(request.user)
    })


@login_required
def invoice_pdf(request, pk):
    """Vue pour générer un PDF de la facture."""
    invoice = get_object_or_404(Invoice, pk=pk)
    
    # Vérifier les permissions
    permissions = get_financial_permissions(request.user)
    if not permissions.get('can_view_invoices', False):
        raise PermissionDenied
    
    # Générer le HTML
    html = render_to_string('finances/invoices/pdf_template.html', {
        'invoice': invoice,
        'items': invoice.items.all(),
    })
    
    # Générer le PDF
    pdf = render_to_pdf(html)
    if not pdf:
        messages.error(request, _('Erreur lors de la génération du PDF.'))
        return redirect('finances:invoice_detail', pk=invoice.pk)
    
    # Renvoyer le PDF
    filename = f"facture_{invoice.number}.pdf"
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def invoice_send(request, pk):
    """Vue pour marquer une facture comme envoyée."""
    invoice = get_object_or_404(Invoice, pk=pk)
    
    # Vérifier les permissions
    if not request.user.has_perm('finances.change_invoice'):
        messages.error(request, _('Vous n\'avez pas les permissions nécessaires.'))
        return redirect('finances:invoice_detail', pk=invoice.pk)
    
    if request.method == 'POST':
        invoice.mark_as_sent(request.user)
        messages.success(request, _('La facture a été marquée comme envoyée.'))
    
    return redirect('finances:invoice_detail', pk=invoice.pk)


@login_required
def invoice_cancel(request, pk):
    """Vue pour annuler une facture."""
    invoice = get_object_or_404(Invoice, pk=pk)
    
    # Vérifier les permissions
    if not request.user.has_perm('finances.cancel_invoice'):
        messages.error(request, _('Vous n\'avez pas les permissions nécessaires.'))
        return redirect('finances:invoice_detail', pk=invoice.pk)
    
    # Vérifier si la facture peut être annulée (pas déjà payée)
    if invoice.status == 'paid':
        messages.error(request, _('Impossible d\'annuler une facture déjà payée.'))
        return redirect('finances:invoice_detail', pk=invoice.pk)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        invoice.cancel(reason, request.user)
        messages.success(request, _('La facture a été annulée avec succès.'))
    
    return redirect('finances:invoice_detail', pk=invoice.pk)


@login_required
def recalculate_invoice(request, pk):
    """Vue pour recalculer le total d'une facture."""
    invoice = get_object_or_404(Invoice, pk=pk)
    
    # Vérifier les permissions
    if not request.user.has_perm('finances.change_invoice'):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Permission denied'}, status=403)
        messages.error(request, _('Vous n\'avez pas les permissions nécessaires.'))
        return redirect('finances:invoice_detail', pk=invoice.pk)
    
    invoice.recalculate_total()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'total_amount': invoice.total,
            'tax_amount': invoice.tax_amount,
            'subtotal': invoice.subtotal
        })
    
    messages.success(request, _('Le total de la facture a été recalculé.'))
    return redirect('finances:invoice_detail', pk=invoice.pk)