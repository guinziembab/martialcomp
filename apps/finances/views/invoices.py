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
from django.core.mail import send_mail
from django.contrib.contenttypes.models import ContentType

from ..models.invoices import Invoice, InvoiceItem
from ..models.payments import PaymentMethod
from ..forms.invoice_forms import (
    InvoiceForm, InvoiceItemFormSet, InvoiceFilterForm,
    InvoicePaymentForm
)
from ..forms.invoice_simple_forms import SimpleInvoiceForm
from ..utils import get_financial_permissions, render_to_pdf
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset


class InvoiceListView(LoginRequiredMixin, ListView):
    """Vue pour afficher la liste des factures."""
    model = Invoice
    template_name = 'finances/invoices/list.html'
    context_object_name = 'invoices'
    paginate_by = 20
    
    def get_queryset(self):

        # Isolation par organisation
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentification requise")
        
        # Pour l'instant, récupérer toutes les factures (sera amélioré avec l'isolation organisationnelle)
        # Les administrateurs voient toutes les factures
        if self.request.user.is_superuser or self.request.user.is_staff:
            queryset = Invoice.objects.all()
        else:
            # Les utilisateurs normaux voient toutes les factures pour l'instant
            # TODO: Implémenter le filtrage par organisation
            queryset = Invoice.objects.all()
        
        # Filtrer selon les permissions de l'utilisateur
        permissions = get_financial_permissions(self.request.user)
        if not permissions.get('can_view_all_invoices', False):
            # Restreindre aux factures de l'organisation (émetteur ou destinataire)
            try:
                from django.contrib.contenttypes.models import ContentType
                from ..currency_service import _get_request_organization
                org = _get_request_organization(self.request)
                if org is not None:
                    ct = ContentType.objects.get_for_model(org.__class__)
                    org_id = str(getattr(org, 'pk', getattr(org, 'id', '')))
                    queryset = queryset.filter(
                        Q(issuer_content_type=ct, issuer_object_id=org_id)
                        |
                        Q(recipient_content_type=ct, recipient_object_id=org_id)
                    )
                else:
                    # Fallback minimal: factures créées par l'utilisateur
                    queryset = queryset.filter(created_by=self.request.user)
            except Exception:
                queryset = queryset.filter(created_by=self.request.user)
        
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
    
    def get_queryset(self):

        # Isolation par organisation
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentification requise")
        
        # Utiliser l'isolation organisationnelle
        base_queryset = get_organization_queryset(self.queryset.model, self.request.user)
        
        # Les administrateurs voient tous les objets de leur organisation
        if self.request.user.is_superuser or self.request.user.is_staff:
            return base_queryset

        queryset = super().get_queryset()
        permissions = get_financial_permissions(self.request.user)
        if permissions.get('can_view_all_invoices', False):
            return queryset
        # Restreindre par organisation détectée
        try:
            from django.contrib.contenttypes.models import ContentType
            from ..currency_service import _get_request_organization
            org = _get_request_organization(self.request)
            if org is not None:
                ct = ContentType.objects.get_for_model(org.__class__)
                org_id = str(getattr(org, 'pk', getattr(org, 'id', '')))
                return queryset.filter(
                    Q(issuer_content_type=ct, issuer_object_id=org_id)
                    |
                    Q(recipient_content_type=ct, recipient_object_id=org_id)
                )
        except Exception:
            pass
        # Fallback: factures créées par l'utilisateur
        return queryset.filter(created_by=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all()
        # Paiements liés via Transaction -> PaymentAttempt
        try:
            from ..models.payments import PaymentAttempt
            context['payments'] = PaymentAttempt.objects.filter(transaction__invoice=self.object).select_related('payment_method', 'transaction')
        except Exception:
            context['payments'] = []
        # Méthodes actives uniquement
        context['payment_methods'] = PaymentMethod.objects.filter(is_active=True)
        context['permissions'] = get_financial_permissions(self.request.user)
        
        # Formulaire de paiement si la facture est impayée
        if self.object.status == 'unpaid':
            context['payment_form'] = InvoicePaymentForm(invoice=self.object)
            
        return context


class InvoiceCreateView(LoginRequiredMixin, CreateView):
    """Vue pour créer une nouvelle facture."""
    model = Invoice
    form_class = SimpleInvoiceForm
    template_name = 'finances/invoices/form_minimal.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Vérifier les permissions personnalisées au lieu des permissions Django strictes
        permissions = get_financial_permissions(request.user)
        if not permissions.get('can_create_invoices', False):
            from django.shortcuts import render
            
            # Afficher une page d'erreur avec des instructions claires
            context = {
                'error_title': _('Accès refusé'),
                'error_message': _('Vous n\'avez pas les permissions nécessaires pour créer des factures.'),
                'help_text': _('Pour créer des factures, vous devez avoir l\'un des rÃ´les suivants : Responsable de fédération, Responsable de club, Coach, ou Manager. Contactez votre administrateur pour obtenir les permissions appropriées.'),
                'user_role': getattr(request.user.profile, 'role', None) if hasattr(request.user, 'profile') else None,
                'current_permissions': permissions,
            }
            return render(request, 'finances/errors/permission_denied.html', context, status=403)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse('finances:invoice_detail', kwargs={'pk': self.object.pk})
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Nouvelle facture')
        context['permissions'] = get_financial_permissions(self.request.user)
        return context
    
    def form_valid(self, form):
        # SimpleInvoiceForm handles content type assignment internally
        self.object = form.save()
        messages.success(self.request, _('La facture a été créée avec succès.'))
        return redirect(self.get_success_url())


class InvoiceUpdateView(LoginRequiredMixin, UpdateView):
    """Vue pour modifier une facture existante."""
    model = Invoice
    form_class = InvoiceForm
    template_name = 'finances/invoices/form.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Vérifier les permissions personnalisées
        permissions = get_financial_permissions(request.user)
        if not permissions.get('can_create_invoices', False):
            from django.shortcuts import render
            
            context = {
                'error_title': _('Accès refusé'),
                'error_message': _('Vous n\'avez pas les permissions nécessaires pour modifier des factures.'),
                'help_text': _('Pour modifier des factures, vous devez avoir l\'un des rÃ´les suivants : Responsable de fédération, Responsable de club, Coach, ou Manager. Contactez votre administrateur pour obtenir les permissions appropriées.'),
                'user_role': getattr(request.user.profile, 'role', None) if hasattr(request.user, 'profile') else None,
                'current_permissions': permissions,
            }
            return render(request, 'finances/errors/permission_denied.html', context, status=403)
        
        return super().dispatch(request, *args, **kwargs)
    
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
            
            messages.success(self.request, _('La facture a été mise Ã  jour avec succès.'))
            return redirect(self.get_success_url())
        else:
            return self.form_invalid(form)


class InvoiceDeleteView(LoginRequiredMixin, DeleteView):
    """Vue pour supprimer une facture."""
    model = Invoice
    template_name = 'finances/invoices/confirm_delete.html'
    success_url = reverse_lazy('finances:invoice_list')
    
    def dispatch(self, request, *args, **kwargs):
        # Vérifier les permissions personnalisées
        permissions = get_financial_permissions(request.user)
        if not permissions.get('can_create_invoices', False):
            from django.shortcuts import render
            
            context = {
                'error_title': _('Accès refusé'),
                'error_message': _('Vous n\'avez pas les permissions nécessaires pour supprimer des factures.'),
                'help_text': _('Pour supprimer des factures, vous devez avoir l\'un des rÃ´les suivants : Responsable de fédération, Responsable de club, Coach, ou Manager. Contactez votre administrateur pour obtenir les permissions appropriées.'),
                'user_role': getattr(request.user.profile, 'role', None) if hasattr(request.user, 'profile') else None,
                'current_permissions': permissions,
            }
            return render(request, 'finances/errors/permission_denied.html', context, status=403)
        
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        # Vérifier si la facture est payée ou a des paiements associés
        invoice = self.get_object()
        has_payments = False
        try:
            from ..models.payments import PaymentAttempt
            has_payments = PaymentAttempt.objects.filter(transaction__invoice=invoice).exists()
        except Exception:
            has_payments = False
        if invoice.status == 'paid' or has_payments:
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
    # Restreindre l'accès selon l'organisation si nécessaire
    permissions = get_financial_permissions(request.user)
    if permissions.get('can_view_all_invoices', False):
        invoice = get_object_or_404(Invoice, pk=pk)
    else:
        try:
            from django.contrib.contenttypes.models import ContentType
            from ..currency_service import _get_request_organization
            org = _get_request_organization(request)
            if org is not None:
                ct = ContentType.objects.get_for_model(org.__class__)
                org_id = str(getattr(org, 'pk', getattr(org, 'id', '')))
                invoice = get_object_or_404(
                    Invoice,
                    Q(pk=pk) & (
                        Q(issuer_content_type=ct, issuer_object_id=org_id)
                        |
                        Q(recipient_content_type=ct, recipient_object_id=org_id)
                    )
                )
            else:
                invoice = get_object_or_404(Invoice, pk=pk, created_by=request.user)
        except Exception:
            invoice = get_object_or_404(Invoice, pk=pk, created_by=request.user)
    
    if not permissions.get('can_view_invoices', False):
        raise PermissionDenied
    
    # Préparer organisation émettrice (pour entête)
    org_ctx = {}
    try:
        ct = getattr(invoice, 'issuer_content_type', None)
        obj_id = getattr(invoice, 'issuer_object_id', None)
        if ct and obj_id:
            Model = ct.model_class()
            issuer_obj = Model.objects.filter(pk=obj_id).first()
            # Si c'est une organisation
            name = getattr(issuer_obj, 'name', '')
            address_parts = [
                getattr(issuer_obj, 'address', ''),
                ' '.join(filter(None, [getattr(issuer_obj, 'postal_code', ''), getattr(issuer_obj, 'city', '')])),
                getattr(issuer_obj, 'country', ''),
            ]
            address = '\n'.join([p for p in address_parts if p])
            logo_url = ''
            logo_path = ''
            try:
                if getattr(issuer_obj, 'logo', None):
                    logo_url = request.build_absolute_uri(issuer_obj.logo.url)
                    logo_path = issuer_obj.logo.path
            except Exception:
                pass
            org_ctx = {
                'name': name,
                'address': address,
                'email': getattr(issuer_obj, 'email', ''),
                'phone': getattr(issuer_obj, 'phone', ''),
                'website': getattr(issuer_obj, 'website', ''),
                'logo_url': logo_url,
                'logo_path': logo_path,
            }
    except Exception:
        pass

    # Générer le HTML
    html = render_to_string('finances/invoices/pdf_template.html', {
        'invoice': invoice,
        'items': invoice.items.all(),
        'org': org_ctx,
    })
    
    # Générer le PDF (fallback reportlab si nécessaire)
    pdf = render_to_pdf(html)
    if not pdf:
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from reportlab.lib.units import mm
            from io import BytesIO
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4
            y = height - 20*mm
            # Logo organisation si disponible (réservons l'espace du logo pour éviter le chevauchement)
            try:
                if org_ctx.get('logo_path'):
                    from reportlab.lib.utils import ImageReader
                    img = ImageReader(org_ctx['logo_path'])
                    iw, ih = img.getSize()
                    target_w = 40*mm
                    scale = target_w / float(iw)
                    target_h = ih * scale
                    x = 20*mm
                    y_logo_top = y
                    c.drawImage(img, x, y_logo_top - target_h, width=target_w, height=target_h, preserveAspectRatio=True, mask='auto')
                    y = y_logo_top - target_h - 4*mm
            except Exception:
                pass
            c.setFont("Helvetica-Bold", 14)
            c.drawString(20*mm, y, f"Facture {getattr(invoice, 'number', str(invoice.pk))}")
            y -= 8*mm
            c.setFont("Helvetica", 10)
            c.drawString(20*mm, y, f"Émise le: {invoice.issued_date}")
            c.drawRightString(width-20*mm, y, f"Échéance: {invoice.due_date}")
            y -= 12*mm
            c.setFont("Helvetica-Bold", 11)
            c.drawString(20*mm, y, "Émetteur")
            c.drawString(width/2, y, "Destinataire")
            y -= 6*mm
            c.setFont("Helvetica", 10)
            # Bloc adresse émetteur: priorité à l'organisation
            emitter_line = (org_ctx.get('name') or getattr(invoice, 'sender_name', '') or '')[:60]
            c.drawString(20*mm, y, emitter_line)
            c.drawString(width/2, y, (getattr(invoice, 'client_name', '') or '')[:60])
            y -= 10*mm
            if org_ctx.get('address'):
                for line in org_ctx['address'].split('\n')[:3]:
                    c.drawString(20*mm, y, line[:80])
                    y -= 5*mm
            c.setFont("Helvetica-Bold", 11)
            c.drawString(20*mm, y, "#  Article")
            c.drawRightString(width-60*mm, y, "PU")
            c.drawRightString(width-35*mm, y, "Qté")
            c.drawRightString(width-20*mm, y, "Total")
            y -= 6*mm
            c.setFont("Helvetica", 10)
            for idx, item in enumerate(invoice.items.all()):
                if y < 30*mm:
                    c.showPage()
                    y = height - 20*mm
                    c.setFont("Helvetica-Bold", 11)
                    c.drawString(20*mm, y, "#  Article")
                    c.drawRightString(width-60*mm, y, "PU")
                    c.drawRightString(width-35*mm, y, "Qté")
                    c.drawRightString(width-20*mm, y, "Total")
                    y -= 6*mm
                    c.setFont("Helvetica", 10)
                c.drawString(20*mm, y, f"{idx+1}  {item.description[:60]}")
                try:
                    c.drawRightString(width-60*mm, y, f"{float(item.unit_price):.2f}")
                    c.drawRightString(width-35*mm, y, f"{float(item.quantity):.0f}")
                    c.drawRightString(width-20*mm, y, f"{float(item.total):.2f}")
                except Exception:
                    pass
                y -= 6*mm
            y -= 6*mm
            c.setFont("Helvetica-Bold", 11)
            c.drawRightString(width-35*mm, y, "Sous-total:")
            c.setFont("Helvetica", 10)
            c.drawRightString(width-20*mm, y, f"{float(getattr(invoice, 'subtotal', 0) or 0):.2f}")
            y -= 5*mm
            c.setFont("Helvetica-Bold", 11)
            c.drawRightString(width-35*mm, y, "TVA:")
            c.setFont("Helvetica", 10)
            c.drawRightString(width-20*mm, y, f"{float(getattr(invoice, 'tax_amount', 0) or 0):.2f}")
            y -= 5*mm
            c.setFont("Helvetica-Bold", 12)
            c.drawRightString(width-35*mm, y, "Total:")
            c.drawRightString(width-20*mm, y, f"{float(getattr(invoice, 'total', 0) or 0):.2f}")
            c.showPage()
            c.save()
            pdf = buffer.getvalue()
            buffer.close()
        except Exception:
            messages.error(request, _('Erreur lors de la génération du PDF.'))
            return redirect('finances:invoice_detail', pk=invoice.pk)
    
    # Renvoyer le PDF
    filename = f"facture_{invoice.number or invoice.pk}.pdf"
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
def invoice_send_email(request, pk):
    """Envoi de la facture par e-mail (simple)."""
    invoice = get_object_or_404(Invoice, pk=pk)
    # Permissions basiques
    permissions = get_financial_permissions(request.user)
    if not permissions.get('can_view_invoices', False):
        raise PermissionDenied
    # Destinataire depuis la facture ou fallback utilisateur
    to_email = getattr(invoice, 'client_email', '') or getattr(getattr(request.user, 'email', ''), 'strip', lambda: '')()
    if not to_email:
        messages.error(request, _('Aucune adresse e-mail destinataire disponible.'))
        return redirect('finances:invoice_detail', pk=invoice.pk)
    subject = _('Facture %(number)s') % {'number': getattr(invoice, 'number', str(invoice.pk))}
    body = render_to_string('finances/invoices/email_body.txt', {
        'invoice': invoice,
        'user': request.user,
    })
    try:
        send_mail(subject, body, None, [to_email], fail_silently=False)
        messages.success(request, _('La facture a été envoyée par e-mail à %(email)s.') % {'email': to_email})
    except Exception as e:
        messages.error(request, _('Erreur lors de l\'envoi de l\'e-mail: %(error)s') % {'error': str(e)})
    return redirect('finances:invoice_detail', pk=invoice.pk)


@login_required
def invoice_cancel(request, pk):
    """Vue pour annuler une facture."""
    invoice = get_object_or_404(Invoice, pk=pk)
    
    # Vérifier les permissions
    if not request.user.has_perm('finances.cancel_invoice'):
        messages.error(request, _('Vous n\'avez pas les permissions nécessaires.'))
        return redirect('finances:invoice_detail', pk=invoice.pk)
    
    # Vérifier si la facture peut Ãªtre annulée (pas déjÃ  payée)
    if invoice.status == 'paid':
        messages.error(request, _('Impossible d\'annuler une facture déjÃ  payée.'))
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
