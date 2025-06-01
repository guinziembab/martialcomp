from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q, Sum, Count, F
from django.conf import settings
from django.core.mail import mail_admins
from datetime import timedelta
import json
import logging

from finances.models.transactions import Transaction
from finances.models.invoices import Invoice
from finances.models.payments import PaymentAttempt
from finances.utils.access_control import check_fraud_indicators

logger = logging.getLogger('finances')

class Command(BaseCommand):
    help = 'Run financial security checks and audits'

    def add_arguments(self, parser):
        parser.add_argument(
            '--notify-admins',
            action='store_true',
            help='Send notifications to admins about security issues',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to look back for transactions',
        )
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Generate detailed reports',
        )

    def handle(self, *args, **options):
        self.stdout.write('Running financial security checks...')
        
        # Récupérer les options
        notify_admins = options['notify_admins']
        days = options['days']
        detailed = options['detailed']
        
        # Date limite pour l'analyse
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Exécuter les contrôles
        suspicious_transactions = self.check_transactions(start_date, end_date)
        unusual_payments = self.check_payments(start_date, end_date)
        invoice_anomalies = self.check_invoices(start_date, end_date)
        
        # Logger les résultats
        self.log_results(suspicious_transactions, unusual_payments, invoice_anomalies, detailed)
        
        # Notifier les administrateurs si demandé et si problèmes trouvés
        if notify_admins and (suspicious_transactions or unusual_payments or invoice_anomalies):
            self.notify_admins(suspicious_transactions, unusual_payments, invoice_anomalies, detailed)
        
        self.stdout.write(self.style.SUCCESS('Financial security checks completed!'))
        
        # Informations sommaires des problèmes trouvés
        self.stdout.write(f'Found {len(suspicious_transactions)} suspicious transactions')
        self.stdout.write(f'Found {len(unusual_payments)} unusual payments')
        self.stdout.write(f'Found {len(invoice_anomalies)} invoice anomalies')

    def check_transactions(self, start_date, end_date):
        """
        Vérifie les transactions pour détecter des comportements suspects.
        """
        self.stdout.write('Checking transactions...')
        
        # Récupérer toutes les transactions de la période
        transactions = Transaction.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).select_related('created_by', 'validated_by')
        
        suspicious_transactions = []
        
        for transaction in transactions:
            # Vérifier les indicateurs de fraude
            fraud_check = check_fraud_indicators(transaction)
            
            # Si le niveau de risque est élevé ou moyen, ajouter à la liste des transactions suspectes
            if fraud_check['risk_level'] in ['high', 'medium']:
                suspicious_transactions.append({
                    'transaction': transaction,
                    'risk_level': fraud_check['risk_level'],
                    'indicators': fraud_check['indicators'],
                    'details': {
                        'id': transaction.id,
                        'amount': float(transaction.amount),
                        'type': transaction.type,
                        'status': transaction.status,
                        'date': transaction.date.isoformat(),
                        'created_at': transaction.created_at.isoformat(),
                        'created_by': transaction.created_by.username if transaction.created_by else None,
                        'validated_by': transaction.validated_by.username if transaction.validated_by else None,
                    }
                })
        
        # Vérifier les transactions atypiques (montants inhabituels pour un utilisateur)
        for user_id, username in transactions.values_list('created_by__id', 'created_by__username').distinct():
            if user_id is None:
                continue
                
            # Calculer la moyenne et l'écart-type des montants de transactions pour cet utilisateur
            user_transactions = transactions.filter(created_by_id=user_id)
            avg_amount = user_transactions.aggregate(avg=Sum('amount') / Count('id'))['avg'] or 0
            
            # Identifier les transactions dont le montant est 3 fois supérieur à la moyenne
            for tx in user_transactions.filter(amount__gt=avg_amount * 3):
                # Vérifier si cette transaction n'est pas déjà dans la liste
                already_listed = any(item['transaction'].id == tx.id for item in suspicious_transactions)
                
                if not already_listed:
                    suspicious_transactions.append({
                        'transaction': tx,
                        'risk_level': 'medium',
                        'indicators': ['unusual_amount_for_user'],
                        'details': {
                            'id': tx.id,
                            'amount': float(tx.amount),
                            'type': tx.type,
                            'status': tx.status,
                            'date': tx.date.isoformat(),
                            'created_at': tx.created_at.isoformat(),
                            'created_by': username,
                            'avg_user_amount': float(avg_amount),
                        }
                    })
        
        return suspicious_transactions

    def check_payments(self, start_date, end_date):
        """
        Vérifie les paiements pour détecter des comportements suspects.
        """
        self.stdout.write('Checking payments...')
        
        # Récupérer tous les paiements de la période
        payments = PaymentAttempt.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).select_related('created_by', 'payment_method', 'invoice')
        
        unusual_payments = []
        
        # Vérifier les paiements comportant des anomalies
        for payment in payments:
            indicators = []
            risk_level = 'none'
            
            # Paiement sans facture
            if payment.invoice is None and payment.amount > 0:
                indicators.append('payment_without_invoice')
                risk_level = 'medium'
            
            # Paiement annulé puis réessayé rapidement
            if payment.status == 'cancelled':
                retry_attempts = PaymentAttempt.objects.filter(
                    invoice=payment.invoice,
                    created_at__gt=payment.created_at,
                    created_at__lt=payment.created_at + timedelta(hours=1)
                ).exclude(id=payment.id)
                
                if retry_attempts.exists():
                    indicators.append('quick_retry_after_cancel')
                    risk_level = 'medium'
            
            # Paiement avec plusieurs échecs
            if payment.status == 'failed':
                other_failures = PaymentAttempt.objects.filter(
                    invoice=payment.invoice,
                    status='failed'
                ).exclude(id=payment.id)
                
                if other_failures.count() >= 3:
                    indicators.append('multiple_failures')
                    risk_level = 'high'
            
            # Paiement effectué à un moment inhabituel
            created_hour = payment.created_at.hour
            if created_hour < 7 or created_hour > 22:
                indicators.append('unusual_time')
                if risk_level == 'none':
                    risk_level = 'low'
                elif risk_level == 'low':
                    risk_level = 'medium'
            
            # Si des indicateurs ont été trouvés, ajouter à la liste
            if indicators:
                unusual_payments.append({
                    'payment': payment,
                    'risk_level': risk_level,
                    'indicators': indicators,
                    'details': {
                        'id': payment.id,
                        'amount': float(payment.amount),
                        'status': payment.status,
                        'method': payment.payment_method.name if payment.payment_method else None,
                        'invoice_id': payment.invoice.id if payment.invoice else None,
                        'created_at': payment.created_at.isoformat(),
                        'created_by': payment.created_by.username if payment.created_by else None,
                    }
                })
        
        return unusual_payments

    def check_invoices(self, start_date, end_date):
        """
        Vérifie les factures pour détecter des anomalies.
        """
        self.stdout.write('Checking invoices...')
        
        # Récupérer toutes les factures de la période
        invoices = Invoice.objects.filter(
            Q(created_at__gte=start_date, created_at__lte=end_date) |
            Q(date_paid__gte=start_date, date_paid__lte=end_date)
        ).select_related('created_by')
        
        invoice_anomalies = []
        
        for invoice in invoices:
            indicators = []
            risk_level = 'none'
            
            # Facture payée le même jour que sa création pour un montant important
            if invoice.status == 'paid' and invoice.date_paid and invoice.created_at:
                if (invoice.date_paid.date() - invoice.created_at.date()).days == 0 and invoice.total > 5000:
                    indicators.append('same_day_payment_large_amount')
                    risk_level = 'medium'
            
            # Facture sans éléments
            if invoice.items.count() == 0 and invoice.total > 0:
                indicators.append('invoice_without_items')
                risk_level = 'high'
            
            # Facture avec un grand écart entre la date de création et la date de la facture
            if invoice.date and (invoice.date - invoice.created_at.date()).days < -30:
                indicators.append('backdated_invoice')
                risk_level = 'medium' if risk_level == 'none' else risk_level
            
            # Facture annulée après paiement
            if invoice.status == 'cancelled' and invoice.payment_attempts.filter(status='completed').exists():
                indicators.append('cancelled_after_payment')
                risk_level = 'high'
            
            # Si des indicateurs ont été trouvés, ajouter à la liste
            if indicators:
                invoice_anomalies.append({
                    'invoice': invoice,
                    'risk_level': risk_level,
                    'indicators': indicators,
                    'details': {
                        'id': invoice.id,
                        'number': invoice.number,
                        'total_amount': float(invoice.total),
                        'status': invoice.status,
                        'date': invoice.date.isoformat() if invoice.date else None,
                        'date_paid': invoice.date_paid.isoformat() if invoice.date_paid else None,
                        'created_at': invoice.created_at.isoformat(),
                        'created_by': invoice.created_by.username if invoice.created_by else None,
                    }
                })
        
        return invoice_anomalies

    def log_results(self, suspicious_transactions, unusual_payments, invoice_anomalies, detailed):
        """
        Journalise les résultats des contrôles de sécurité.
        """
        # Logger les transactions suspectes
        for item in suspicious_transactions:
            tx = item['transaction']
            logger.warning(
                f"SECURITY_CHECK: Suspicious transaction detected - ID: {tx.id}, "
                f"Amount: {tx.amount}, Risk: {item['risk_level']}, "
                f"Indicators: {', '.join(item['indicators'])}"
            )
            
            if detailed:
                logger.info(f"SECURITY_DETAIL: Transaction {tx.id} - {json.dumps(item['details'])}")
        
        # Logger les paiements inhabituels
        for item in unusual_payments:
            payment = item['payment']
            logger.warning(
                f"SECURITY_CHECK: Unusual payment detected - ID: {payment.id}, "
                f"Amount: {payment.amount}, Risk: {item['risk_level']}, "
                f"Indicators: {', '.join(item['indicators'])}"
            )
            
            if detailed:
                logger.info(f"SECURITY_DETAIL: Payment {payment.id} - {json.dumps(item['details'])}")
        
        # Logger les anomalies de factures
        for item in invoice_anomalies:
            invoice = item['invoice']
            logger.warning(
                f"SECURITY_CHECK: Invoice anomaly detected - ID: {invoice.id}, "
                f"Number: {invoice.number}, Risk: {item['risk_level']}, "
                f"Indicators: {', '.join(item['indicators'])}"
            )
            
            if detailed:
                logger.info(f"SECURITY_DETAIL: Invoice {invoice.id} - {json.dumps(item['details'])}")

    def notify_admins(self, suspicious_transactions, unusual_payments, invoice_anomalies, detailed):
        """
        Envoie une notification aux administrateurs concernant les problèmes de sécurité.
        """
        # Préparer le corps du message
        subject = f"[MartialComp] Alertes de sécurité financière ({timezone.now().strftime('%Y-%m-%d')})"
        
        message = "Les contrôles de sécurité financière ont détecté les anomalies suivantes :\n\n"
        
        # Ajouter les transactions suspectes
        if suspicious_transactions:
            message += f"=== TRANSACTIONS SUSPECTES ({len(suspicious_transactions)}) ===\n"
            for item in suspicious_transactions:
                tx = item['transaction']
                message += f"- Transaction {tx.id}: {tx.amount} € ({item['risk_level']})\n"
                message += f"  Indicateurs: {', '.join(item['indicators'])}\n"
                if detailed:
                    message += f"  Détails: {json.dumps(item['details'])}\n"
                message += "\n"
        
        # Ajouter les paiements inhabituels
        if unusual_payments:
            message += f"=== PAIEMENTS INHABITUELS ({len(unusual_payments)}) ===\n"
            for item in unusual_payments:
                payment = item['payment']
                message += f"- Paiement {payment.id}: {payment.amount} € ({item['risk_level']})\n"
                message += f"  Indicateurs: {', '.join(item['indicators'])}\n"
                if detailed:
                    message += f"  Détails: {json.dumps(item['details'])}\n"
                message += "\n"
        
        # Ajouter les anomalies de factures
        if invoice_anomalies:
            message += f"=== ANOMALIES DE FACTURES ({len(invoice_anomalies)}) ===\n"
            for item in invoice_anomalies:
                invoice = item['invoice']
                message += f"- Facture {invoice.id} ({invoice.number}): {invoice.total} € ({item['risk_level']})\n"
                message += f"  Indicateurs: {', '.join(item['indicators'])}\n"
                if detailed:
                    message += f"  Détails: {json.dumps(item['details'])}\n"
                message += "\n"
        
        message += "\nCes anomalies peuvent indiquer des problèmes de sécurité ou des erreurs. Veuillez les examiner dans l'interface d'administration."
        message += "\nRapport généré automatiquement par le système de sécurité financière."
        
        # Envoyer l'email
        try:
            mail_admins(subject, message, fail_silently=False)
            self.stdout.write(self.style.SUCCESS('Notification sent to admins'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to send notification: {e}'))