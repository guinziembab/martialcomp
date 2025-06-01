from django.utils import timezone
from django.db import transaction as db_transaction
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils.text import slugify
import datetime

from ..models.invoices import Invoice, InvoiceItem
from ..models.transactions import Transaction
from ..models.payments import PaymentAttempt, PaymentMethod

User = get_user_model()


class InvoiceService:
    """
    Service pour gérer les opérations métier liées aux factures.
    """
    
    @staticmethod
    def create_invoice(data, items_data, user):
        """
        Crée une nouvelle facture avec les éléments associés.
        
        Args:
            data (dict): Les données de la facture
            items_data (list): Liste des données des éléments de la facture
            user (User): L'utilisateur qui crée la facture
            
        Returns:
            Invoice: L'objet facture créé
            
        Raises:
            ValidationError: Si les données ne sont pas valides
        """
        # Valider les données de base
        if not data.get('client_name'):
            raise ValidationError(_('Le nom du client est obligatoire'))
        
        # Générer un numéro de facture si non fourni
        if not data.get('number'):
            data['number'] = InvoiceService.generate_invoice_number()
        
        # Créer la facture avec transaction atomique
        with db_transaction.atomic():
            invoice = Invoice(
                number=data['number'],
                issued_date=data.get('date', timezone.now().date()),
                due_date=data.get('due_date'),
                client_name=data['client_name'],
                client_email=data.get('client_email', ''),
                client_address=data.get('client_address', ''),
                notes=data.get('notes', ''),
                terms=data.get('terms', ''),
                status=data.get('status', 'draft'),
                tax_rate=data.get('tax_rate', 0),
                created_by=user,
                updated_by=user
            )
            
            # Traiter les entités associées via GenericForeignKey
            if data.get('issuer_content_type_id') and data.get('issuer_object_id'):
                invoice.issuer_content_type_id = data['issuer_content_type_id']
                invoice.issuer_object_id = data['issuer_object_id']
                
            if data.get('client_content_type_id') and data.get('client_object_id'):
                invoice.client_content_type_id = data['client_content_type_id']
                invoice.client_object_id = data['client_object_id']
            
            # Sauvegarder la facture
            invoice.save()
            
            # Créer les éléments de la facture
            if items_data:
                for item_data in items_data:
                    if not item_data.get('description') or not item_data.get('amount'):
                        continue  # Ignorer les éléments incomplets
                        
                    item = InvoiceItem(
                        invoice=invoice,
                        description=item_data['description'],
                        quantity=item_data.get('quantity', 1),
                        unit_price=item_data.get('unit_price', 0),
                        amount=item_data['amount'],
                        tax_rate=item_data.get('tax_rate', invoice.tax_rate)
                    )
                    item.save()
            
            # Recalculer le total de la facture
            invoice.recalculate_total()
            
            return invoice
    
    @staticmethod
    def generate_invoice_number():
        """
        Génère un numéro de facture unique.
        
        Returns:
            str: Le numéro de facture généré
        """
        today = timezone.now().date()
        year = today.year
        month = today.month
        
        # Trouver le dernier numéro de facture pour ce mois
        prefix = f"INV-{year}{month:02d}-"
        
        last_invoice = Invoice.objects.filter(
            number__startswith=prefix
        ).order_by('-number').first()
        
        if last_invoice:
            # Extraire le numéro séquentiel du dernier numéro
            try:
                last_num = int(last_invoice.number.split('-')[-1])
                next_num = last_num + 1
            except (ValueError, IndexError):
                next_num = 1
        else:
            next_num = 1
        
        # Générer le nouveau numéro
        new_number = f"{prefix}{next_num:04d}"
        return new_number
    
    @staticmethod
    def mark_invoice_as_sent(invoice_id, user, sent_date=None):
        """
        Marque une facture comme envoyée.
        
        Args:
            invoice_id (str): L'ID de la facture
            user (User): L'utilisateur qui marque la facture
            sent_date (datetime, optional): Date d'envoi
            
        Returns:
            Invoice: L'objet facture mis à jour
            
        Raises:
            ValidationError: Si la facture n'est pas envoyable
        """
        try:
            invoice = Invoice.objects.get(pk=invoice_id)
        except Invoice.DoesNotExist:
            raise ValidationError(_('Facture introuvable'))
        
        if invoice.status not in ['draft']:
            raise ValidationError(_('Seules les factures en brouillon peuvent être marquées comme envoyées'))
        
        # Mettre à jour le statut
        invoice.status = 'unpaid'  # Une facture envoyée devient impayée
        invoice.date_sent = sent_date or timezone.now()
        invoice.updated_by = user
        invoice.updated_at = timezone.now()
        
        invoice.save()
        
        return invoice
    
    @staticmethod
    def mark_invoice_as_paid(invoice_id, payment_data, user):
        """
        Marque une facture comme payée et enregistre le paiement.
        
        Args:
            invoice_id (str): L'ID de la facture
            payment_data (dict): Données du paiement
            user (User): L'utilisateur qui enregistre le paiement
            
        Returns:
            tuple: (Invoice, PaymentAttempt) Les objets mis à jour
            
        Raises:
            ValidationError: Si la facture ne peut pas être marquée comme payée
        """
        try:
            invoice = Invoice.objects.get(pk=invoice_id)
        except Invoice.DoesNotExist:
            raise ValidationError(_('Facture introuvable'))
        
        if invoice.status not in ['unpaid', 'sent']:
            raise ValidationError(_('Seules les factures impayées peuvent être marquées comme payées'))
        
        # Valider les données de paiement
        payment_method_id = payment_data.get('payment_method_id')
        if not payment_method_id:
            raise ValidationError(_('La méthode de paiement est obligatoire'))
            
        try:
            payment_method = PaymentMethod.objects.get(pk=payment_method_id, active=True)
        except PaymentMethod.DoesNotExist:
            raise ValidationError(_('Méthode de paiement invalide'))
        
        with db_transaction.atomic():
            # Créer une tentative de paiement
            payment_attempt = PaymentAttempt(
                invoice=invoice,
                payment_method=payment_method,
                amount=invoice.total,
                status='completed',
                reference=payment_data.get('reference', ''),
                processor_response=payment_data.get('processor_response', {}),
                notes=payment_data.get('notes', ''),
                created_by=user,
                processed_by=user,
                processed_at=payment_data.get('payment_date', timezone.now())
            )
            payment_attempt.save()
            
            # Mettre à jour le statut de la facture
            invoice.status = 'paid'
            invoice.date_paid = payment_data.get('payment_date', timezone.now())
            invoice.payment_reference = payment_data.get('reference', '')
            invoice.payment_method = payment_method
            invoice.updated_by = user
            invoice.updated_at = timezone.now()
            invoice.save()
            
            # Créer une transaction de revenu si configuré
            if payment_data.get('create_transaction', True):
                from .transaction_service import TransactionService
                
                transaction_data = {
                    'description': _('Paiement de la facture %(invoice_number)s') % {'invoice_number': invoice.number},
                    'amount': invoice.total,
                    'type': 'income',
                    'date': payment_data.get('payment_date', timezone.now().date()),
                    'reference': payment_data.get('reference', ''),
                    'notes': payment_data.get('notes', ''),
                    'account_id': payment_data.get('account_id'),
                    'category_id': payment_data.get('category_id'),
                    'entity_content_type_id': invoice.get_content_type_id(),
                    'entity_object_id': invoice.id
                }
                
                TransactionService.create_transaction(transaction_data, user)
            
            return invoice, payment_attempt
    
    @staticmethod
    def cancel_invoice(invoice_id, reason, user):
        """
        Annule une facture.
        
        Args:
            invoice_id (str): L'ID de la facture
            reason (str): Raison de l'annulation
            user (User): L'utilisateur qui annule la facture
            
        Returns:
            Invoice: L'objet facture annulé
            
        Raises:
            ValidationError: Si la facture ne peut pas être annulée
        """
        try:
            invoice = Invoice.objects.get(pk=invoice_id)
        except Invoice.DoesNotExist:
            raise ValidationError(_('Facture introuvable'))
        
        if invoice.status == 'paid':
            raise ValidationError(_('Impossible d\'annuler une facture déjà payée'))
        
        if invoice.status == 'cancelled':
            raise ValidationError(_('Cette facture est déjà annulée'))
        
        # Mettre à jour le statut
        invoice.status = 'cancelled'
        invoice.date_cancelled = timezone.now()
        invoice.cancelled_by = user
        invoice.cancellation_reason = reason
        invoice.updated_by = user
        invoice.updated_at = timezone.now()
        
        invoice.save()
        
        return invoice
    
    @staticmethod
    def generate_credit_note(invoice_id, reason, user):
        """
        Génère un avoir à partir d'une facture existante.
        
        Args:
            invoice_id (str): L'ID de la facture
            reason (str): Raison de l'avoir
            user (User): L'utilisateur qui génère l'avoir
            
        Returns:
            Invoice: L'objet avoir créé
            
        Raises:
            ValidationError: Si la facture ne permet pas de générer un avoir
        """
        try:
            original_invoice = Invoice.objects.get(pk=invoice_id)
        except Invoice.DoesNotExist:
            raise ValidationError(_('Facture introuvable'))
        
        if original_invoice.status not in ['paid', 'unpaid']:
            raise ValidationError(_('Impossible de générer un avoir pour une facture en brouillon ou annulée'))
        
        with db_transaction.atomic():
            # Créer un avoir basé sur la facture originale
            credit_note = Invoice(
                is_credit_note=True,
                original_invoice=original_invoice,
                number=InvoiceService.generate_credit_note_number(original_invoice.number),
                issued_date=timezone.now().date(),
                client_name=original_invoice.client_name,
                client_email=original_invoice.client_email,
                client_address=original_invoice.client_address,
                notes=reason,
                tax_rate=original_invoice.tax_rate,
                status='draft',
                created_by=user,
                updated_by=user
            )
            
            # Copier les informations d'entité
            if original_invoice.issuer_content_type_id and original_invoice.issuer_object_id:
                credit_note.issuer_content_type_id = original_invoice.issuer_content_type_id
                credit_note.issuer_object_id = original_invoice.issuer_object_id
                
            if original_invoice.client_content_type_id and original_invoice.client_object_id:
                credit_note.client_content_type_id = original_invoice.client_content_type_id
                credit_note.client_object_id = original_invoice.client_object_id
                
            credit_note.save()
            
            # Créer les éléments de l'avoir (inverser les montants)
            for item in original_invoice.items.all():
                credit_item = InvoiceItem(
                    invoice=credit_note,
                    description=_('Avoir: %(description)s') % {'description': item.description},
                    quantity=item.quantity,
                    unit_price=-item.unit_price,  # Montant négatif
                    amount=-item.amount,  # Montant négatif
                    tax_rate=item.tax_rate
                )
                credit_item.save()
            
            # Recalculer le total
            credit_note.recalculate_total()
            
            return credit_note
    
    @staticmethod
    def generate_credit_note_number(invoice_number):
        """
        Génère un numéro d'avoir basé sur le numéro de facture.
        
        Args:
            invoice_number (str): Le numéro de facture original
            
        Returns:
            str: Le numéro d'avoir généré
        """
        # Format: 'AV-' + original_number
        return f"AV-{invoice_number}"
    
    @staticmethod
    def get_invoice_statistics(start_date, end_date, filters=None):
        """
        Récupère des statistiques sur les factures pour une période donnée.
        
        Args:
            start_date (date): Date de début
            end_date (date): Date de fin
            filters (dict, optional): Filtres supplémentaires
            
        Returns:
            dict: Statistiques des factures
        """
        invoices = Invoice.objects.filter(
            issued_date__gte=start_date,
            issued_date__lte=end_date,
            is_credit_note=False  # Exclure les avoirs
        )
        
        # Appliquer des filtres supplémentaires si présents
        if filters:
            if 'status' in filters:
                invoices = invoices.filter(status=filters['status'])
            if 'client' in filters:
                invoices = invoices.filter(client_name__icontains=filters['client'])
            if 'min_amount' in filters:
                invoices = invoices.filter(total__gte=filters['min_amount'])
            if 'max_amount' in filters:
                invoices = invoices.filter(total__lte=filters['max_amount'])
        
        # Calculer les totaux
        from django.db.models import Sum, Count, Avg, F, ExpressionWrapper, fields
        from django.db.models.functions import ExtractMonth
        
        total_count = invoices.count()
        total_amount = invoices.aggregate(Sum('total'))['total__sum'] or 0
        
        # Par statut
        status_stats = invoices.values('status').annotate(
            count=Count('id'),
            total=Sum('total_amount')
        )
        
        # Par mois
        by_month = invoices.annotate(
            month=ExtractMonth('issued_date')
        ).values('month').annotate(
            count=Count('id'),
            total=Sum('total_amount')
        ).order_by('month')
        
        # Délai de paiement moyen (pour les factures payées)
        payment_delay = invoices.filter(
            status='paid',
            paid_date__isnull=False
        ).annotate(
            delay=ExpressionWrapper(
                F('paid_date') - F('issued_date'),
                output_field=fields.DurationField()
            )
        ).aggregate(
            avg_delay=Avg('delay')
        )['avg_delay']
        
        # Convertir timedelta en jours
        avg_payment_delay = None
        if payment_delay:
            avg_payment_delay = payment_delay.days
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'total_count': total_count,
            'total_amount': total_amount,
            'status_stats': list(status_stats),
            'by_month': list(by_month),
            'avg_payment_delay': avg_payment_delay
        }