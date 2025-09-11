from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from apps.finances.models.transactions import Transaction
from apps.finances.models.invoices import Invoice
from apps.finances.models.payments import PaymentMethod, PaymentAttempt
from apps.finances.models.accounts import FinancialAccount, AccountingCategory, MembershipFee

class Command(BaseCommand):
    help = 'Initialize finance permissions and groups'

    def handle(self, *args, **kwargs):
        self.stdout.write('Initializing finance permissions and groups...')
        
        # Créer les groupes principaux
        self.create_finance_groups()
        
        # Créer les permissions personnalisées
        self.create_custom_permissions()
        
        # Attribuer les permissions aux groupes
        self.assign_permissions_to_groups()
        
        self.stdout.write(self.style.SUCCESS('Finance permissions and groups initialized successfully!'))
    
    def create_finance_groups(self):
        """Créer les groupes principaux pour la gestion financière."""
        groups = [
            'Finance Admin',
            'Finance Manager',
            'Finance Viewer',
            'Transaction Manager',
            'Invoice Manager',
            'Payment Processor'
        ]
        
        for group_name in groups:
            Group.objects.get_or_create(name=group_name)
            self.stdout.write(f'Group created: {group_name}')
    
    def create_custom_permissions(self):
        """Créer des permissions personnalisées pour les modèles financiers."""
        # Obtenir les content_types
        transaction_ct = ContentType.objects.get_for_model(Transaction)
        invoice_ct = ContentType.objects.get_for_model(Invoice)
        payment_method_ct = ContentType.objects.get_for_model(PaymentMethod)
        payment_attempt_ct = ContentType.objects.get_for_model(PaymentAttempt)
        financial_account_ct = ContentType.objects.get_for_model(FinancialAccount)
        
        # Permissions pour Transaction
        transaction_perms = [
            ('view_all_transactions', 'Can view all transactions'),
            ('validate_transaction', 'Can validate transactions'),
            ('reject_transaction', 'Can reject transactions'),
            ('cancel_transaction', 'Can cancel transactions'),
            ('approve_all_transactions', 'Can approve all transactions'),
        ]
        
        for codename, name in transaction_perms:
            Permission.objects.get_or_create(
                codename=codename,
                name=name,
                content_type=transaction_ct,
            )
            self.stdout.write(f'Permission created: {codename}')
        
        # Permissions pour Invoice
        invoice_perms = [
            ('view_all_invoices', 'Can view all invoices'),
            ('cancel_invoice', 'Can cancel invoices'),
            ('mark_invoice_as_paid', 'Can mark invoices as paid'),
            ('generate_credit_note', 'Can generate credit notes'),
        ]
        
        for codename, name in invoice_perms:
            Permission.objects.get_or_create(
                codename=codename,
                name=name,
                content_type=invoice_ct,
            )
            self.stdout.write(f'Permission created: {codename}')
        
        # Permissions pour PaymentMethod
        payment_method_perms = [
            ('manage_payment_methods', 'Can manage payment methods'),
        ]
        
        for codename, name in payment_method_perms:
            Permission.objects.get_or_create(
                codename=codename,
                name=name,
                content_type=payment_method_ct,
            )
            self.stdout.write(f'Permission created: {codename}')
        
        # Permissions pour PaymentAttempt
        payment_attempt_perms = [
            ('process_payment', 'Can process payments'),
            ('view_all_payments', 'Can view all payments'),
        ]
        
        for codename, name in payment_attempt_perms:
            Permission.objects.get_or_create(
                codename=codename,
                name=name,
                content_type=payment_attempt_ct,
            )
            self.stdout.write(f'Permission created: {codename}')
        
        # Permissions pour FinancialAccount
        financial_account_perms = [
            ('view_reports', 'Can view financial reports'),
            ('view_dashboard', 'Can view financial dashboard'),
        ]
        
        for codename, name in financial_account_perms:
            Permission.objects.get_or_create(
                codename=codename,
                name=name,
                content_type=financial_account_ct,
            )
            self.stdout.write(f'Permission created: {codename}')
    
    def assign_permissions_to_groups(self):
        """Attribuer les permissions aux groupes."""
        # Finance Admin - toutes les permissions
        admin_group = Group.objects.get(name='Finance Admin')
        finance_models = [
            Transaction, Invoice, PaymentMethod, PaymentAttempt, 
            FinancialAccount, AccountingCategory, MembershipFee
        ]
        
        # Obtenir toutes les permissions pour les modèles financiers
        finance_permissions = Permission.objects.filter(
            content_type__in=[ContentType.objects.get_for_model(model) for model in finance_models]
        )
        
        admin_group.permissions.add(*finance_permissions)
        self.stdout.write(f'Assigned {finance_permissions.count()} permissions to Finance Admin group')
        
        # Finance Manager - permissions de gestion sans suppression
        manager_group = Group.objects.get(name='Finance Manager')
        manager_permissions = Permission.objects.filter(
            Q(content_type__in=[ContentType.objects.get_for_model(model) for model in finance_models]) &
            (Q(codename__startswith='add_') | Q(codename__startswith='change_') | 
             Q(codename__startswith='view_'))
        )
        
        # Ajouter les permissions personnalisées
        custom_permissions = Permission.objects.filter(
            Q(codename='validate_transaction') | Q(codename='reject_transaction') |
            Q(codename='view_all_transactions') | Q(codename='mark_invoice_as_paid') |
            Q(codename='view_all_invoices') | Q(codename='process_payment') |
            Q(codename='view_all_payments') | Q(codename='view_reports') |
            Q(codename='view_dashboard')
        )
        
        manager_permissions = manager_permissions.union(custom_permissions)
        manager_group.permissions.add(*manager_permissions)
        self.stdout.write(f'Assigned {manager_permissions.count()} permissions to Finance Manager group')
        
        # Finance Viewer - permissions de consultation uniquement
        viewer_group = Group.objects.get(name='Finance Viewer')
        viewer_permissions = Permission.objects.filter(
            Q(content_type__in=[ContentType.objects.get_for_model(model) for model in finance_models]) &
            Q(codename__startswith='view_')
        )
        
        viewer_group.permissions.add(*viewer_permissions)
        self.stdout.write(f'Assigned {viewer_permissions.count()} permissions to Finance Viewer group')
        
        # Transaction Manager - permissions sur les transactions
        transaction_group = Group.objects.get(name='Transaction Manager')
        transaction_permissions = Permission.objects.filter(
            Q(content_type=ContentType.objects.get_for_model(Transaction)) &
            (Q(codename__startswith='add_') | Q(codename__startswith='change_') | 
             Q(codename__startswith='view_'))
        ).union(
            Permission.objects.filter(codename__in=[
                'validate_transaction', 'reject_transaction', 'view_all_transactions'
            ])
        )
        
        transaction_group.permissions.add(*transaction_permissions)
        self.stdout.write(f'Assigned {transaction_permissions.count()} permissions to Transaction Manager group')
        
        # Invoice Manager - permissions sur les factures
        invoice_group = Group.objects.get(name='Invoice Manager')
        invoice_permissions = Permission.objects.filter(
            Q(content_type=ContentType.objects.get_for_model(Invoice)) &
            (Q(codename__startswith='add_') | Q(codename__startswith='change_') | 
             Q(codename__startswith='view_'))
        ).union(
            Permission.objects.filter(codename__in=[
                'mark_invoice_as_paid', 'view_all_invoices', 'generate_credit_note'
            ])
        )
        
        invoice_group.permissions.add(*invoice_permissions)
        self.stdout.write(f'Assigned {invoice_permissions.count()} permissions to Invoice Manager group')
        
        # Payment Processor - permissions sur les paiements
        payment_group = Group.objects.get(name='Payment Processor')
        payment_permissions = Permission.objects.filter(
            (Q(content_type=ContentType.objects.get_for_model(PaymentMethod)) |
             Q(content_type=ContentType.objects.get_for_model(PaymentAttempt))) &
            (Q(codename__startswith='add_') | Q(codename__startswith='change_') | 
             Q(codename__startswith='view_'))
        ).union(
            Permission.objects.filter(codename__in=[
                'process_payment', 'view_all_payments'
            ])
        )
        
        payment_group.permissions.add(*payment_permissions)
        self.stdout.write(f'Assigned {payment_permissions.count()} permissions to Payment Processor group')

