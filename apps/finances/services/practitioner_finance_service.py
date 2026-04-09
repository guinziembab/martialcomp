# -*- coding: utf-8 -*-
"""
Service de gestion financière pour les pratiquants
Fournit les données d'adhésion, solde, historique des paiements
"""

from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum, Q
from decimal import Decimal
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class PractitionerFinanceService:
    """
    Service pour récupérer et gérer les données financières d'un pratiquant.

    Utilise les modèles:
    - MembershipSubscription (apps.membership)
    - Transaction (apps.finances)
    - PaymentAttempt (apps.finances)
    - Invoice (apps.finances)
    """

    def __init__(self, practitioner):
        """
        Initialise le service avec un pratiquant.

        Args:
            practitioner: Instance du modèle Practitioner
        """
        self.practitioner = practitioner
        self._membership = None
        self._balance = None
        self._payments = None

    def get_finance_summary(self):
        """
        Retourne un résumé complet des informations financières du pratiquant.

        Returns:
            dict: Résumé financier complet
        """
        return {
            'membership': self.get_membership_info(),
            'balance': self.get_balance_info(),
            'payments': self.get_payment_history(limit=5),
            'invoices': self.get_pending_invoices(),
            'alerts': self.get_finance_alerts(),
        }

    def get_membership_info(self):
        """
        Récupère les informations d'adhésion du pratiquant.

        Returns:
            dict: Informations d'adhésion ou None si aucune adhésion
        """
        try:
            from apps.membership.models import MembershipSubscription

            # Récupérer l'adhésion active ou la plus récente
            subscription = MembershipSubscription.objects.filter(
                practitioner=self.practitioner
            ).select_related('package').order_by('-end_date').first()

            if not subscription:
                return {
                    'status': 'none',
                    'status_display': _('Aucune adhésion'),
                    'status_color': 'secondary',
                    'package_name': None,
                    'amount': None,
                    'start_date': None,
                    'end_date': None,
                    'renewal_date': None,
                    'days_remaining': None,
                    'is_active': False,
                    'is_expiring_soon': False,
                    'auto_renew': False,
                }

            today = timezone.now().date()
            days_remaining = (subscription.end_date - today).days if subscription.end_date else None

            # Déterminer le statut et la couleur
            status_info = self._get_subscription_status_info(subscription, days_remaining)

            return {
                'status': subscription.status,
                'status_display': status_info['display'],
                'status_color': status_info['color'],
                'package_name': subscription.package.name if subscription.package else 'N/A',
                'amount': float(subscription.price_paid) if subscription.price_paid else 0,
                'currency': subscription.currency or 'EUR',
                'start_date': subscription.start_date,
                'end_date': subscription.end_date,
                'renewal_date': subscription.renewal_date,
                'days_remaining': days_remaining,
                'is_active': subscription.is_active,
                'is_expiring_soon': days_remaining is not None and 0 < days_remaining <= 30,
                'auto_renew': subscription.auto_renew,
                'subscription_id': str(subscription.id),
            }

        except ImportError as e:
            logger.warning(f"Module membership non disponible: {e}")
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des infos d'adhésion: {e}")
            return None

    def _get_subscription_status_info(self, subscription, days_remaining):
        """
        Retourne le statut formaté et la couleur selon l'état de l'adhésion.
        """
        if subscription.status == 'active':
            if days_remaining is not None:
                if days_remaining <= 0:
                    return {'display': _('Expiré'), 'color': 'danger'}
                elif days_remaining <= 14:
                    return {'display': _('Expire dans %(days)s j') % {'days': days_remaining}, 'color': 'warning'}
                elif days_remaining <= 30:
                    return {'display': _('Actif (expire bientôt)'), 'color': 'info'}
            return {'display': _('Actif'), 'color': 'success'}
        elif subscription.status == 'expired':
            return {'display': _('Expiré'), 'color': 'danger'}
        elif subscription.status == 'suspended':
            return {'display': _('Suspendu'), 'color': 'warning'}
        elif subscription.status == 'cancelled':
            return {'display': _('Annulé'), 'color': 'secondary'}
        elif subscription.status == 'pending':
            return {'display': _('En attente'), 'color': 'info'}
        else:
            return {'display': subscription.get_status_display(), 'color': 'secondary'}

    def get_balance_info(self):
        """
        Calcule le solde du pratiquant (montants dus vs payés).

        Returns:
            dict: Informations de solde
        """
        try:
            from apps.finances.models import Transaction, Invoice
            from django.contrib.contenttypes.models import ContentType

            # Obtenir le ContentType du pratiquant
            practitioner_ct = ContentType.objects.get_for_model(self.practitioner)

            # Calculer le total des revenus validés (paiements reçus)
            total_paid = Transaction.objects.filter(
                source_content_type=practitioner_ct,
                source_object_id=str(self.practitioner.pk),
                type='income',
                status='validated'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

            # Calculer le total des factures en attente
            total_due = Invoice.objects.filter(
                recipient_content_type=practitioner_ct,
                recipient_object_id=str(self.practitioner.pk),
                status__in=['issued', 'partially_paid', 'overdue']
            ).aggregate(total=Sum('total'))['total'] or Decimal('0')

            # Calculer le montant déjà payé sur les factures
            amount_paid_on_invoices = Invoice.objects.filter(
                recipient_content_type=practitioner_ct,
                recipient_object_id=str(self.practitioner.pk),
            ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')

            balance = float(amount_paid_on_invoices) - float(total_due)

            # Déterminer le statut du solde
            if balance > 0:
                status = 'credit'
                status_display = _('Crédit')
                status_color = 'success'
            elif balance < 0:
                status = 'debit'
                status_display = _('À payer')
                status_color = 'danger'
            else:
                status = 'balanced'
                status_display = _('Soldé')
                status_color = 'success'

            return {
                'balance': balance,
                'total_paid': float(total_paid),
                'total_due': float(total_due),
                'status': status,
                'status_display': status_display,
                'status_color': status_color,
                'currency': 'EUR',
            }

        except ImportError as e:
            logger.warning(f"Module finances non disponible: {e}")
            return {
                'balance': 0,
                'total_paid': 0,
                'total_due': 0,
                'status': 'unknown',
                'status_display': _('Inconnu'),
                'status_color': 'secondary',
                'currency': 'EUR',
            }
        except Exception as e:
            logger.error(f"Erreur lors du calcul du solde: {e}")
            return {
                'balance': 0,
                'total_paid': 0,
                'total_due': 0,
                'status': 'error',
                'status_display': _('Erreur'),
                'status_color': 'danger',
                'currency': 'EUR',
            }

    def get_payment_history(self, limit=5):
        """
        Récupère l'historique des paiements du pratiquant.

        Args:
            limit: Nombre maximum de paiements à retourner

        Returns:
            list: Liste des paiements récents
        """
        try:
            from apps.finances.models import Transaction, PaymentAttempt
            from django.contrib.contenttypes.models import ContentType

            practitioner_ct = ContentType.objects.get_for_model(self.practitioner)

            # Récupérer les transactions liées au pratiquant
            transactions = Transaction.objects.filter(
                Q(source_content_type=practitioner_ct, source_object_id=str(self.practitioner.pk)) |
                Q(destination_content_type=practitioner_ct, destination_object_id=str(self.practitioner.pk))
            ).select_related('category', 'payment_method').order_by('-date_created')[:limit]

            payments = []
            for tx in transactions:
                payment_method_name = tx.payment_method.name if tx.payment_method else 'N/A'

                # Déterminer la couleur du statut
                status_colors = {
                    'pending': 'warning',
                    'validated': 'success',
                    'rejected': 'danger',
                    'refunded': 'info',
                    'cancelled': 'secondary',
                }

                payments.append({
                    'id': str(tx.id),
                    'reference': tx.reference,
                    'date': tx.date,
                    'amount': float(tx.amount),
                    'currency': tx.currency,
                    'type': tx.type,
                    'type_display': tx.get_type_display(),
                    'status': tx.status,
                    'status_display': tx.get_status_display(),
                    'status_color': status_colors.get(tx.status, 'secondary'),
                    'description': tx.description or tx.category.name if tx.category else 'N/A',
                    'payment_method': payment_method_name,
                })

            return payments

        except ImportError as e:
            logger.warning(f"Module finances non disponible: {e}")
            return []
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'historique: {e}")
            return []

    def get_pending_invoices(self):
        """
        Récupère les factures en attente du pratiquant.

        Returns:
            list: Liste des factures non payées
        """
        try:
            from apps.finances.models import Invoice
            from django.contrib.contenttypes.models import ContentType

            practitioner_ct = ContentType.objects.get_for_model(self.practitioner)

            invoices = Invoice.objects.filter(
                recipient_content_type=practitioner_ct,
                recipient_object_id=str(self.practitioner.pk),
                status__in=['issued', 'partially_paid', 'overdue']
            ).order_by('due_date')[:5]

            result = []
            for inv in invoices:
                days_until_due = (inv.due_date - timezone.now().date()).days if inv.due_date else None

                result.append({
                    'id': str(inv.id),
                    'number': inv.number,
                    'issued_date': inv.issued_date,
                    'due_date': inv.due_date,
                    'total': float(inv.total),
                    'amount_paid': float(inv.amount_paid) if inv.amount_paid else 0,
                    'balance_due': float(inv.balance_due) if hasattr(inv, 'balance_due') else float(inv.total - (inv.amount_paid or 0)),
                    'status': inv.status,
                    'status_display': inv.get_status_display(),
                    'is_overdue': inv.status == 'overdue' or (days_until_due is not None and days_until_due < 0),
                    'days_until_due': days_until_due,
                    'currency': inv.currency,
                })

            return result

        except ImportError as e:
            logger.warning(f"Module finances non disponible: {e}")
            return []
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des factures: {e}")
            return []

    def get_finance_alerts(self):
        """
        Génère des alertes financières pour le pratiquant.

        Returns:
            list: Liste des alertes actives
        """
        alerts = []

        # Vérifier le statut d'adhésion
        membership = self.get_membership_info()
        if membership:
            if membership['status'] == 'none':
                alerts.append({
                    'type': 'membership',
                    'level': 'warning',
                    'message': _('Aucune adhésion active'),
                    'icon': 'fas fa-exclamation-triangle',
                })
            elif membership['is_expiring_soon']:
                alerts.append({
                    'type': 'membership',
                    'level': 'warning',
                    'message': _("Adhésion expire dans %(days)s jours") % {'days': membership['days_remaining']},
                    'icon': 'fas fa-clock',
                })
            elif membership.get('days_remaining') is not None and membership['days_remaining'] <= 0:
                alerts.append({
                    'type': 'membership',
                    'level': 'danger',
                    'message': _('Adhésion expirée'),
                    'icon': 'fas fa-exclamation-circle',
                })

        # Vérifier le solde
        balance = self.get_balance_info()
        if balance and balance['balance'] < 0:
            alerts.append({
                'type': 'balance',
                'level': 'danger',
                'message': _("Solde négatif: %(amount).2f %(currency)s à payer") % {
                    'amount': abs(balance['balance']),
                    'currency': balance['currency']
                },
                'icon': 'fas fa-euro-sign',
            })

        # Vérifier les factures en retard
        invoices = self.get_pending_invoices()
        overdue_count = sum(1 for inv in invoices if inv['is_overdue'])
        if overdue_count > 0:
            alerts.append({
                'type': 'invoice',
                'level': 'danger',
                'message': _("%(count)s facture(s) en retard") % {'count': overdue_count},
                'icon': 'fas fa-file-invoice',
            })

        return alerts

    @staticmethod
    def record_payment(practitioner, amount, payment_method_id, description='', user=None):
        """
        Enregistre un paiement pour un pratiquant.

        Args:
            practitioner: Instance Practitioner
            amount: Montant du paiement
            payment_method_id: ID de la méthode de paiement
            description: Description optionnelle
            user: Utilisateur effectuant l'opération

        Returns:
            Transaction: La transaction créée ou None en cas d'erreur
        """
        try:
            from apps.finances.models import Transaction, PaymentMethod
            from django.contrib.contenttypes.models import ContentType

            practitioner_ct = ContentType.objects.get_for_model(practitioner)

            payment_method = None
            if payment_method_id:
                try:
                    payment_method = PaymentMethod.objects.get(pk=payment_method_id)
                except PaymentMethod.DoesNotExist:
                    pass

            transaction = Transaction.objects.create(
                type='income',
                amount=Decimal(str(amount)),
                currency='EUR',
                date=timezone.now().date(),
                status='validated',
                description=description or f"Paiement de {practitioner.full_name}",
                source_content_type=practitioner_ct,
                source_object_id=str(practitioner.pk),
                payment_method=payment_method,
                created_by=user,
                date_validated=timezone.now(),
                validated_by=user,
            )

            logger.info(f"Paiement enregistré: {transaction.reference} - {amount} EUR pour {practitioner.full_name}")
            return transaction

        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement du paiement: {e}")
            return None

    @staticmethod
    def send_payment_reminder(practitioner, user=None):
        """
        Envoie un rappel de paiement au pratiquant.

        Args:
            practitioner: Instance Practitioner
            user: Utilisateur effectuant l'opération

        Returns:
            bool: True si envoyé avec succès
        """
        try:
            from django.core.mail import send_mail
            from django.template.loader import render_to_string
            from django.conf import settings

            if not practitioner.email:
                logger.warning(f"Pas d'email pour le pratiquant {practitioner.full_name}")
                return False

            service = PractitionerFinanceService(practitioner)
            context = {
                'practitioner': practitioner,
                'finance_summary': service.get_finance_summary(),
            }

            # Pour l'instant, on simule l'envoi
            logger.info(f"Rappel de paiement envoyé à {practitioner.email}")

            # TODO: Implémenter l'envoi réel d'email
            # subject = f"Rappel de paiement - {settings.SITE_NAME}"
            # message = render_to_string('emails/payment_reminder.html', context)
            # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [practitioner.email])

            return True

        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du rappel: {e}")
            return False
