from django.utils import timezone
from django.db import transaction as db_transaction
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.conf import settings

from ..models.payments import PaymentMethod, PaymentAttempt
from ..models.invoices import Invoice
from ..models.transactions import Transaction

User = get_user_model()


class PaymentService:
    """
    Service pour gérer les opérations métier liées aux paiements.
    """
    
    @staticmethod
    def create_payment_attempt(data, user):
        """
        Crée une nouvelle tentative de paiement.
        
        Args:
            data (dict): Les données du paiement
            user (User): L'utilisateur qui crée la tentative
            
        Returns:
            PaymentAttempt: L'objet tentative de paiement créé
            
        Raises:
            ValidationError: Si les données ne sont pas valides
        """
        # Valider les données de base
        if not data.get('amount') or data.get('amount') <= 0:
            raise ValidationError(_('Le montant doit Ãªtre supérieur Ã  zéro'))
            
        if not data.get('payment_method_id'):
            raise ValidationError(_('La méthode de paiement est obligatoire'))
            
        # Vérifier que la méthode de paiement existe
        try:
            payment_method = PaymentMethod.objects.get(pk=data['payment_method_id'], active=True)
        except PaymentMethod.DoesNotExist:
            raise ValidationError(_('Méthode de paiement invalide'))
            
        # Vérifier la facture si spécifiée
        invoice = None
        if data.get('invoice_id'):
            try:
                invoice = Invoice.objects.get(pk=data['invoice_id'])
                if invoice.status not in ['unpaid', 'sent']:
                    raise ValidationError(_('Cette facture ne peut pas Ãªtre payée'))
            except Invoice.DoesNotExist:
                raise ValidationError(_('Facture invalide'))
                
        # Créer la tentative de paiement
        payment_attempt = PaymentAttempt(
            payment_method=payment_method,
            invoice=invoice,
            amount=data['amount'],
            reference=data.get('reference', PaymentService.generate_payment_reference()),
            notes=data.get('notes', ''),
            status='pending',
            created_by=user
        )
        
        # Ajouter les frais de la méthode de paiement si activés
        if payment_method.apply_fee:
            payment_attempt.fee_amount = payment_method.calculate_fee(data['amount'])
            payment_attempt.total = data['amount'] + payment_attempt.fee_amount
        else:
            payment_attempt.total = data['amount']
            
        # Traiter les entités associées via GenericForeignKey
        if data.get('payer_content_type_id') and data.get('payer_object_id'):
            payment_attempt.payer_content_type_id = data['payer_content_type_id']
            payment_attempt.payer_object_id = data['payer_object_id']
            
        # Sauvegarder
        payment_attempt.save()
        
        return payment_attempt
    
    @staticmethod
    def process_payment(payment_attempt_id, processing_data, user):
        """
        Traite une tentative de paiement en attente.
        
        Args:
            payment_attempt_id (str): L'ID de la tentative de paiement
            processing_data (dict): Données du traitement
            user (User): L'utilisateur qui traite le paiement
            
        Returns:
            PaymentAttempt: L'objet tentative de paiement mis Ã  jour
            
        Raises:
            ValidationError: Si le paiement ne peut pas Ãªtre traité
        """
        try:
            payment_attempt = PaymentAttempt.objects.get(pk=payment_attempt_id)
        except PaymentAttempt.DoesNotExist:
            raise ValidationError(_('Tentative de paiement introuvable'))
            
        if payment_attempt.status != 'pending':
            raise ValidationError(_('Cette tentative de paiement a déjÃ  été traitée'))
            
        # Traitement selon la passerelle de paiement
        processor = payment_attempt.payment_method.processor
        status = processing_data.get('status', 'failed')
        processor_reference = processing_data.get('processor_reference', '')
        processor_response = processing_data.get('processor_response', {})
        
        with db_transaction.atomic():
            # Mettre Ã  jour la tentative de paiement
            payment_attempt.status = status
            payment_attempt.processor_reference = processor_reference
            payment_attempt.processor_response = processor_response
            payment_attempt.processed_at = timezone.now()
            payment_attempt.processed_by = user
            
            if processing_data.get('notes'):
                payment_attempt.notes = f"{payment_attempt.notes}\n\n{processing_data['notes']}" if payment_attempt.notes else processing_data['notes']
                
            payment_attempt.save()
            
            # Si le paiement est réussi et qu'il est lié Ã  une facture
            if status == 'completed' and payment_attempt.invoice:
                # Mettre Ã  jour la facture
                invoice = payment_attempt.invoice
                invoice.status = 'paid'
                invoice.date_paid = timezone.now()
                invoice.payment_reference = payment_attempt.reference
                invoice.payment_method = payment_attempt.payment_method
                invoice.updated_by = user
                invoice.updated_at = timezone.now()
                invoice.save()
                
                # Créer une transaction si configuré
                if processing_data.get('create_transaction', True):
                    from .transaction_service import TransactionService
                    
                    transaction_data = {
                        'description': _('Paiement de la facture %(invoice_number)s') % {'invoice_number': invoice.number},
                        'amount': payment_attempt.amount,
                        'type': 'income',
                        'date': timezone.now().date(),
                        'reference': payment_attempt.reference,
                        'notes': payment_attempt.notes,
                        'account_id': processing_data.get('account_id'),
                        'category_id': processing_data.get('category_id'),
                        'entity_content_type_id': invoice.get_content_type_id(),
                        'entity_object_id': invoice.id
                    }
                    
                    TransactionService.create_transaction(transaction_data, user)
            
            return payment_attempt
    
    @staticmethod
    def cancel_payment(payment_attempt_id, reason, user):
        """
        Annule une tentative de paiement en attente.
        
        Args:
            payment_attempt_id (str): L'ID de la tentative de paiement
            reason (str): Raison de l'annulation
            user (User): L'utilisateur qui annule le paiement
            
        Returns:
            PaymentAttempt: L'objet tentative de paiement annulé
            
        Raises:
            ValidationError: Si le paiement ne peut pas Ãªtre annulé
        """
        try:
            payment_attempt = PaymentAttempt.objects.get(pk=payment_attempt_id)
        except PaymentAttempt.DoesNotExist:
            raise ValidationError(_('Tentative de paiement introuvable'))
            
        if payment_attempt.status != 'pending':
            raise ValidationError(_('Seules les tentatives de paiement en attente peuvent Ãªtre annulées'))
            
        # Mettre Ã  jour le statut
        payment_attempt.status = 'cancelled'
        payment_attempt.processed_at = timezone.now()
        payment_attempt.processed_by = user
        
        if reason:
            payment_attempt.notes = f"{payment_attempt.notes}\n\nAnnulation: {reason}" if payment_attempt.notes else f"Annulation: {reason}"
            
        payment_attempt.save()
        
        return payment_attempt
    
    @staticmethod
    def generate_payment_reference():
        """
        Génère une référence de paiement unique.
        
        Returns:
            str: La référence générée
        """
        import random
        import string
        from datetime import datetime
        
        # Format: PYMT-{timestamp}-{random_chars}
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        
        return f"PYMT-{timestamp}-{random_chars}"
    
    @staticmethod
    def get_payment_method_details(method_id, amount=None):
        """
        Obtient les détails d'une méthode de paiement, y compris les frais calculés.
        
        Args:
            method_id (str): L'ID de la méthode de paiement
            amount (float, optional): Montant pour calculer les frais
            
        Returns:
            dict: Détails de la méthode de paiement
            
        Raises:
            ValidationError: Si la méthode n'existe pas
        """
        try:
            method = PaymentMethod.objects.get(pk=method_id, active=True)
        except PaymentMethod.DoesNotExist:
            raise ValidationError(_('Méthode de paiement invalide'))
            
        # Calculer les frais si un montant est fourni
        fee = 0
        total = 0
        
        if amount is not None and amount > 0:
            fee = method.calculate_fee(amount)
            total = amount + fee
            
        return {
            'id': method.id,
            'name': method.name,
            'description': method.description,
            'processor': method.processor,
            'instructions': method.instructions,
            'fee_fixed': method.fee_fixed,
            'fee_percentage': method.fee_percentage,
            'apply_fee': method.apply_fee,
            'calculated_fee': fee,
            'total_with_fee': total
        }
