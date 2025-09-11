"""
Intégration du système de gestion familiale avec le module finances.
Ce module fournit les services pour connecter les paiements familiaux
avec le système financier de MartialComp.
"""

from django.utils import timezone
from django.db import transaction as db_transaction
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from decimal import Decimal
import uuid

# Import du module finances
try:
    from apps.finances.models.payments import PaymentMethod, PaymentAttempt
    from apps.finances.models.invoices import Invoice, InvoiceItem
    from apps.finances.models.transactions import Transaction
    from apps.finances.services.payment_service import PaymentService
    from apps.finances.services.invoice_service import InvoiceService
    FINANCES_AVAILABLE = True
except ImportError:
    FINANCES_AVAILABLE = False

from .models import Family, FamilyPaymentGroup, FamilyMember

User = get_user_model()


class FamilyFinanceIntegrationService:
    """
    Service d'intégration entre la gestion familiale et le module finances.
    """
    
    def __init__(self):
        if not FINANCES_AVAILABLE:
            raise ImportError("Le module finances n'est pas disponible")
    
    @staticmethod
    def create_family_invoice(family, items, description="Facture familiale", due_date=None):
        """
        Crée une facture pour une famille avec plusieurs éléments.
        
        Args:
            family (Family): La famille pour laquelle créer la facture
            items (list): Liste des éléments de facture
                Format: [{'description': str, 'amount': Decimal, 'member_id': int}, ...]
            description (str): Description de la facture
            due_date (datetime): Date d'échéance (optionnel)
            
        Returns:
            Invoice: La facture créée
        """
        if not due_date:
            due_date = timezone.now() + timezone.timedelta(days=30)
        
        with db_transaction.atomic():
            # Calculer le montant total
            total_amount = sum(Decimal(str(item['amount'])) for item in items)
            
            # Créer la facture principale
            invoice_data = {
                'client_name': family.family_name,
                'client_email': family.billing_email or family.primary_responsible.email,
                'client_address': family.billing_address,
                'total_amount': total_amount,
                'due_date': due_date,
                'description': description,
                'status': 'draft',
                # Métadonnées pour lier Ã  la famille
                'metadata': {
                    'family_id': str(family.id),
                    'family_name': family.family_name,
                    'created_by_family_system': True
                }
            }
            
            invoice = InvoiceService.create_invoice(invoice_data, family.primary_responsible)
            
            # Ajouter les éléments individuels
            for item in items:
                item_data = {
                    'invoice': invoice,
                    'description': item['description'],
                    'quantity': item.get('quantity', 1),
                    'unit_price': Decimal(str(item['amount'])),
                    'total_price': Decimal(str(item['amount'])) * item.get('quantity', 1),
                    'metadata': {
                        'member_id': item.get('member_id'),
                        'family_member': True
                    }
                }
                
                InvoiceItem.objects.create(**item_data)
            
            return invoice
    
    @staticmethod
    def create_family_payment_group_invoice(payment_group):
        """
        Crée une facture Ã  partir d'un groupe de paiement familial.
        
        Args:
            payment_group (FamilyPaymentGroup): Le groupe de paiement
            
        Returns:
            Invoice: La facture créée
        """
        # Récupérer les membres concernés par ce groupe de paiement
        # (ceci dépendrait de la logique métier spécifique)
        family = payment_group.family
        
        # Créer un élément de facture pour le groupe
        items = [{
            'description': payment_group.description,
            'amount': payment_group.total_amount,
            'member_id': None,  # Groupe entier
        }]
        
        invoice = FamilyFinanceIntegrationService.create_family_invoice(
            family=family,
            items=items,
            description=f"Facture familiale - {payment_group.description}"
        )
        
        # Lier la facture au groupe de paiement
        payment_group.invoice_id = invoice.id
        payment_group.save()
        
        return invoice
    
    @staticmethod
    def process_family_payment(payment_group, payment_method_id, additional_data=None):
        """
        Traite un paiement pour un groupe de paiement familial.
        
        Args:
            payment_group (FamilyPaymentGroup): Le groupe de paiement
            payment_method_id (UUID): ID de la méthode de paiement
            additional_data (dict): Données supplémentaires pour le paiement
            
        Returns:
            dict: Résultat du traitement du paiement
        """
        if additional_data is None:
            additional_data = {}
        
        try:
            with db_transaction.atomic():
                # Créer ou récupérer la facture associée
                if hasattr(payment_group, 'invoice_id') and payment_group.invoice_id:
                    try:
                        invoice = Invoice.objects.get(id=payment_group.invoice_id)
                    except Invoice.DoesNotExist:
                        invoice = FamilyFinanceIntegrationService.create_family_payment_group_invoice(payment_group)
                else:
                    invoice = FamilyFinanceIntegrationService.create_family_payment_group_invoice(payment_group)
                
                # Préparer les données de paiement
                payment_data = {
                    'amount': payment_group.total_amount,
                    'payment_method_id': payment_method_id,
                    'invoice_id': invoice.id,
                    'description': f"Paiement familial - {payment_group.description}",
                    'metadata': {
                        'family_id': str(payment_group.family.id),
                        'payment_group_id': payment_group.id,
                        'family_payment': True
                    }
                }
                
                # Ajouter les données supplémentaires
                payment_data.update(additional_data)
                
                # Créer la tentative de paiement
                payment_attempt = PaymentService.create_payment_attempt(
                    payment_data, 
                    payment_group.family.primary_responsible
                )
                
                # Marquer le groupe comme payé si le paiement réussit
                if payment_attempt.status == 'completed':
                    payment_group.is_paid = True
                    payment_group.paid_at = timezone.now()
                    payment_group.payment_reference = str(payment_attempt.id)
                    payment_group.save()
                    
                    # Mettre Ã  jour le statut de la facture
                    invoice.status = 'paid'
                    invoice.paid_at = timezone.now()
                    invoice.save()
                
                return {
                    'success': True,
                    'payment_attempt': payment_attempt,
                    'invoice': invoice,
                    'payment_group': payment_group
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'payment_group': payment_group
            }
    
    @staticmethod
    def get_family_financial_summary(family):
        """
        Récupère un résumé financier pour une famille.
        
        Args:
            family (Family): La famille
            
        Returns:
            dict: Résumé financier
        """
        try:
            # Récupérer toutes les factures liées Ã  cette famille
            family_invoices = Invoice.objects.filter(
                metadata__family_id=str(family.id)
            )
            
            # Récupérer tous les groupes de paiement
            payment_groups = family.payment_groups.all()
            
            # Calculer les totaux
            total_invoiced = sum(invoice.total_amount for invoice in family_invoices)
            total_paid = sum(invoice.total_amount for invoice in family_invoices.filter(status='paid'))
            total_pending = sum(group.total_amount for group in payment_groups.filter(is_paid=False))
            
            return {
                'total_invoiced': total_invoiced,
                'total_paid': total_paid,
                'total_pending': total_pending,
                'outstanding_balance': total_invoiced - total_paid,
                'invoices_count': family_invoices.count(),
                'pending_payments_count': payment_groups.filter(is_paid=False).count(),
                'recent_invoices': family_invoices.order_by('-created_at')[:5],
                'recent_payments': payment_groups.filter(is_paid=True).order_by('-created_at')[:5]
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'total_invoiced': Decimal('0.00'),
                'total_paid': Decimal('0.00'),
                'total_pending': Decimal('0.00'),
                'outstanding_balance': Decimal('0.00')
            }
    
    @staticmethod
    def create_member_subscription_invoice(family_member, subscription_type, amount, period_start, period_end):
        """
        Crée une facture d'abonnement pour un membre de famille.
        
        Args:
            family_member (FamilyMember): Le membre de famille
            subscription_type (str): Type d'abonnement (mensuel, annuel, etc.)
            amount (Decimal): Montant de l'abonnement
            period_start (date): Début de la période
            period_end (date): Fin de la période
            
        Returns:
            Invoice: La facture créée
        """
        family = family_member.family
        member_name = family_member.practitioner.user.get_full_name() if family_member.practitioner else "Membre famille"
        
        items = [{
            'description': f"Abonnement {subscription_type} - {member_name} ({period_start} - {period_end})",
            'amount': amount,
            'member_id': family_member.id,
        }]
        
        return FamilyFinanceIntegrationService.create_family_invoice(
            family=family,
            items=items,
            description=f"Abonnement {subscription_type} - {member_name}"
        )
    
    @staticmethod
    def apply_family_discount(invoice, discount_percentage=0, discount_amount=None, reason=""):
        """
        Applique une remise familiale Ã  une facture.
        
        Args:
            invoice (Invoice): La facture
            discount_percentage (float): Pourcentage de remise
            discount_amount (Decimal): Montant fixe de remise
            reason (str): Raison de la remise
            
        Returns:
            Invoice: La facture mise Ã  jour
        """
        if discount_amount:
            final_discount = discount_amount
        else:
            final_discount = invoice.total_amount * (Decimal(str(discount_percentage)) / 100)
        
        # Ajouter un élément de remise Ã  la facture
        discount_item = InvoiceItem.objects.create(
            invoice=invoice,
            description=f"Remise familiale - {reason}",
            quantity=1,
            unit_price=-final_discount,
            total_price=-final_discount,
            metadata={
                'discount': True,
                'family_discount': True,
                'reason': reason
            }
        )
        
        # Recalculer le total de la facture
        invoice.total_amount = invoice.total_amount - final_discount
        invoice.save()
        
        return invoice


class FamilyFinanceUtils:
    """
    Utilitaires pour l'intégration financière familiale.
    """
    
    @staticmethod
    def is_finances_module_available():
        """Vérifie si le module finances est disponible."""
        return FINANCES_AVAILABLE
    
    @staticmethod
    def get_available_payment_methods(organization=None):
        """
        Récupère les méthodes de paiement disponibles pour une organisation.
        
        Args:
            organization: L'organisation (optionnel)
            
        Returns:
            QuerySet: Les méthodes de paiement disponibles
        """
        if not FINANCES_AVAILABLE:
            return []
        
        methods = PaymentMethod.objects.filter(is_active=True)
        
        if organization:
            # Filtrer par organisation si spécifié
            methods = methods.filter(
                models.Q(organization_id=str(organization.id)) |
                models.Q(organization_id__isnull=True)
            )
        
        return methods.order_by('name')
    
    @staticmethod
    def format_currency(amount, currency='EUR'):
        """
        Formate un montant en devise.
        
        Args:
            amount (Decimal): Le montant
            currency (str): La devise
            
        Returns:
            str: Le montant formaté
        """
        return f"{amount:.2f} {currency}"
    
    @staticmethod
    def calculate_family_discount(family, base_amount, discount_rules=None):
        """
        Calcule une remise familiale basée sur des règles.
        
        Args:
            family (Family): La famille
            base_amount (Decimal): Montant de base
            discount_rules (dict): Règles de remise personnalisées
            
        Returns:
            dict: Détails de la remise calculée
        """
        if discount_rules is None:
            discount_rules = {
                'multiple_members': {
                    'threshold': 2,
                    'percentage': 10
                },
                'large_family': {
                    'threshold': 4,
                    'percentage': 20
                }
            }
        
        active_members = family.get_active_members().count()
        discount_percentage = 0
        reason = ""
        
        if active_members >= discount_rules['large_family']['threshold']:
            discount_percentage = discount_rules['large_family']['percentage']
            reason = f"Remise famille nombreuse ({active_members} membres)"
        elif active_members >= discount_rules['multiple_members']['threshold']:
            discount_percentage = discount_rules['multiple_members']['percentage']
            reason = f"Remise famille multiple ({active_members} membres)"
        
        discount_amount = base_amount * (Decimal(str(discount_percentage)) / 100)
        final_amount = base_amount - discount_amount
        
        return {
            'original_amount': base_amount,
            'discount_percentage': discount_percentage,
            'discount_amount': discount_amount,
            'final_amount': final_amount,
            'reason': reason,
            'members_count': active_members
        }

