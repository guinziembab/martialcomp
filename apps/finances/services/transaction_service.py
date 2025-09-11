from django.utils import timezone
from django.db import transaction as db_transaction
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.conf import settings

from ..models.transactions import Transaction, TransactionCategory, TransactionAttachment
from ..models.accounts import FinancialAccount

User = get_user_model()


class TransactionService:
    """
    Service pour gérer les opérations métier liées aux transactions financières.
    """
    
    @staticmethod
    def create_transaction(data, user):
        """
        Crée une nouvelle transaction avec les validations métier appropriées.
        
        Args:
            data (dict): Les données de la transaction
            user (User): L'utilisateur qui crée la transaction
            
        Returns:
            Transaction: L'objet transaction créé
            
        Raises:
            ValidationError: Si les données ne sont pas valides
        """
        # Valider les données de base
        if not data.get('description'):
            raise ValidationError(_('La description est obligatoire'))
        
        if not data.get('amount') or data.get('amount') <= 0:
            raise ValidationError(_('Le montant doit Ãªtre supérieur Ã  zéro'))
        
        # Valider que le compte existe
        account = None
        if data.get('account_id'):
            try:
                account = FinancialAccount.objects.get(pk=data['account_id'], active=True)
            except FinancialAccount.DoesNotExist:
                raise ValidationError(_('Le compte financier spécifié n\'existe pas'))
        
        # Valider la catégorie
        category = None
        if data.get('category_id'):
            try:
                category = TransactionCategory.objects.get(pk=data['category_id'], active=True)
            except TransactionCategory.DoesNotExist:
                raise ValidationError(_('La catégorie spécifiée n\'existe pas'))
                
            # Vérifier si la catégorie correspond au type de transaction
            if category.transaction_type and category.transaction_type != data.get('type'):
                raise ValidationError(_('La catégorie ne correspond pas au type de transaction'))
        
        # Créer la transaction avec transaction atomique
        with db_transaction.atomic():
            transaction = Transaction(
                description=data['description'],
                amount=data['amount'],
                type=data.get('type', 'expense'),
                date=data.get('date', timezone.now().date()),
                reference=data.get('reference', ''),
                notes=data.get('notes', ''),
                status='pending',
                category=category,
                account=account,
                created_by=user,
                updated_by=user
            )
            
            # Traiter les entités associées via GenericForeignKey
            if data.get('entity_content_type_id') and data.get('entity_object_id'):
                transaction.entity_content_type_id = data['entity_content_type_id']
                transaction.entity_object_id = data['entity_object_id']
            
            # Sauvegarder la transaction
            transaction.save()
            
            # Traiter les pièces jointes si présentes
            if 'attachments' in data and isinstance(data['attachments'], list):
                for attachment_data in data['attachments']:
                    if 'file' in attachment_data:
                        attachment = TransactionAttachment(
                            transaction=transaction,
                            file=attachment_data['file'],
                            description=attachment_data.get('description', ''),
                            uploaded_by=user
                        )
                        attachment.save()
            
            return transaction
    
    @staticmethod
    def validate_transaction(transaction_id, user, notes=None):
        """
        Valide une transaction en attente.
        
        Args:
            transaction_id (str): L'ID de la transaction Ã  valider
            user (User): L'utilisateur qui effectue la validation
            notes (str, optional): Notes additionnelles pour la validation
            
        Returns:
            Transaction: L'objet transaction validé
            
        Raises:
            ValidationError: Si la transaction n'est pas validable
        """
        try:
            transaction = Transaction.objects.get(pk=transaction_id)
        except Transaction.DoesNotExist:
            raise ValidationError(_('Transaction introuvable'))
        
        if transaction.status != 'pending':
            raise ValidationError(_('Seules les transactions en attente peuvent Ãªtre validées'))
        
        # Vérifier les permissions (Ã  adapter selon votre système de permissions)
        # if not user.has_perm('finances.validate_transaction'):
        #     raise ValidationError(_('Vous n\'avez pas les permissions nécessaires'))
        
        # Valider la transaction
        with db_transaction.atomic():
            # Si la transaction est liée Ã  un compte, mettre Ã  jour le solde
            if transaction.account:
                if transaction.type == 'income':
                    transaction.account.balance += transaction.amount
                else:  # expense
                    if not transaction.account.allow_overdraft and transaction.account.balance < transaction.amount:
                        raise ValidationError(_('Solde insuffisant sur le compte'))
                    transaction.account.balance -= transaction.amount
                
                transaction.account.save()
            
            # Mettre Ã  jour le statut de la transaction
            transaction.status = 'validated'
            transaction.date_validated = timezone.now()
            transaction.validated_by = user
            if notes:
                transaction.notes = f"{transaction.notes}\n\nValidation: {notes}" if transaction.notes else f"Validation: {notes}"
            
            transaction.save()
            
            return transaction
    
    @staticmethod
    def reject_transaction(transaction_id, user, reason=None):
        """
        Rejette une transaction en attente.
        
        Args:
            transaction_id (str): L'ID de la transaction Ã  rejeter
            user (User): L'utilisateur qui effectue le rejet
            reason (str, optional): Raison du rejet
            
        Returns:
            Transaction: L'objet transaction rejeté
            
        Raises:
            ValidationError: Si la transaction n'est pas rejetable
        """
        try:
            transaction = Transaction.objects.get(pk=transaction_id)
        except Transaction.DoesNotExist:
            raise ValidationError(_('Transaction introuvable'))
        
        if transaction.status != 'pending':
            raise ValidationError(_('Seules les transactions en attente peuvent Ãªtre rejetées'))
        
        # Mettre Ã  jour le statut de la transaction
        transaction.status = 'rejected'
        transaction.date_validated = timezone.now()
        transaction.validated_by = user
        if reason:
            transaction.notes = f"{transaction.notes}\n\nRejet: {reason}" if transaction.notes else f"Rejet: {reason}"
        
        transaction.save()
        
        return transaction
    
    @staticmethod
    def cancel_transaction(transaction_id, user, reason=None):
        """
        Annule une transaction validée.
        
        Args:
            transaction_id (str): L'ID de la transaction Ã  annuler
            user (User): L'utilisateur qui effectue l'annulation
            reason (str, optional): Raison de l'annulation
            
        Returns:
            Transaction: L'objet transaction annulé
            
        Raises:
            ValidationError: Si la transaction n'est pas annulable
        """
        try:
            transaction = Transaction.objects.get(pk=transaction_id)
        except Transaction.DoesNotExist:
            raise ValidationError(_('Transaction introuvable'))
        
        if transaction.status not in ['validated', 'pending']:
            raise ValidationError(_('Seules les transactions validées ou en attente peuvent Ãªtre annulées'))
        
        # Annuler l'impact sur le compte si transaction validée
        with db_transaction.atomic():
            if transaction.status == 'validated' and transaction.account:
                # Inverser l'effet sur le solde
                if transaction.type == 'income':
                    transaction.account.current_balance -= transaction.amount
                else:  # expense
                    transaction.account.current_balance += transaction.amount
                
                transaction.account.save()
            
            # Mettre Ã  jour le statut de la transaction
            transaction.status = 'cancelled'
            transaction.date_cancelled = timezone.now()
            transaction.cancelled_by = user
            if reason:
                transaction.notes = f"{transaction.notes}\n\nAnnulation: {reason}" if transaction.notes else f"Annulation: {reason}"
            
            transaction.save()
            
            return transaction
    
    @staticmethod
    def get_transaction_summary(start_date, end_date, filters=None):
        """
        Récupère un résumé des transactions pour une période donnée.
        
        Args:
            start_date (date): Date de début
            end_date (date): Date de fin
            filters (dict, optional): Filtres supplémentaires
            
        Returns:
            dict: Un résumé des transactions
        """
        transactions = Transaction.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        )
        
        # Appliquer des filtres supplémentaires si présents
        if filters:
            if 'type' in filters:
                transactions = transactions.filter(type=filters['type'])
            if 'status' in filters:
                transactions = transactions.filter(status=filters['status'])
            if 'category' in filters:
                transactions = transactions.filter(category_id=filters['category'])
            if 'account' in filters:
                transactions = transactions.filter(account_id=filters['account'])
        
        # Calculer les totaux
        income_transactions = transactions.filter(type='income')
        expense_transactions = transactions.filter(type='expense')
        
        from django.db.models import Sum
        
        total_income = income_transactions.aggregate(Sum('amount'))['amount__sum'] or 0
        total_expense = expense_transactions.aggregate(Sum('amount'))['amount__sum'] or 0
        net_result = total_income - total_expense
        
        # Pour les catégories
        from django.db.models import Count
        
        income_by_category = income_transactions.values('category__name').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        expense_by_category = expense_transactions.values('category__name').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        # Pour les statuts
        transactions_by_status = transactions.values('status').annotate(
            count=Count('id'),
            total=Sum('amount')
        )
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'total_transactions': transactions.count(),
            'total_income': total_income,
            'total_expense': total_expense,
            'net_result': net_result,
            'income_by_category': list(income_by_category),
            'expense_by_category': list(expense_by_category),
            'transactions_by_status': list(transactions_by_status)
        }
