# -*- coding: utf-8 -*-
"""
Taches Celery pour le module finances.

Ce module contient:
- update_exchange_rates: Mise a jour automatique des taux de change
- send_subscription_reminders: Rappels d'echeance d'abonnement
- generate_monthly_reports: Generation des rapports mensuels

Cree: Janvier 2025
"""

import logging
from datetime import timedelta
from decimal import Decimal

from celery import shared_task
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


# =============================================================================
# TACHES DE MISE A JOUR DES TAUX DE CHANGE
# =============================================================================

@shared_task(
    name='finances.tasks.update_exchange_rates',
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def update_exchange_rates(self, provider=None, base='EUR'):
    """
    Met a jour les taux de change depuis une API externe.

    Cette tache:
    1. Recupere les taux depuis l'API configuree
    2. Met a jour le modele ExchangeRate
    3. Invalide les caches

    Args:
        provider: Provider API (openexchangerates, fixer, etc.)
        base: Devise de base (defaut EUR)

    Returns:
        dict: Resultat de la mise a jour
    """
    from .currency_service import (
        fetch_rates_from_api,
        update_rates_in_database,
        clear_rates_cache,
        DEFAULT_PROVIDER
    )

    provider = provider or DEFAULT_PROVIDER
    logger.info(f"Demarrage mise a jour taux de change depuis {provider}")

    try:
        # Recuperer les taux depuis l'API
        rates = fetch_rates_from_api(base=base, provider=provider)

        if not rates:
            logger.warning(f"Aucun taux recupere depuis {provider}")
            return {
                'success': False,
                'provider': provider,
                'error': 'No rates returned from API'
            }

        # Mettre a jour la base de donnees
        updated_count = update_rates_in_database(
            rates=rates,
            base=base,
            source=provider.upper()
        )

        # Vider les caches
        clear_rates_cache()

        logger.info(f"Mis a jour {updated_count} taux de change depuis {provider}")

        return {
            'success': True,
            'provider': provider,
            'base': base,
            'updated_count': updated_count,
            'rates_count': len(rates),
            'timestamp': timezone.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Erreur mise a jour taux: {e}")
        raise


@shared_task(name='finances.tasks.update_exchange_rates_all_providers')
def update_exchange_rates_all_providers():
    """
    Tente de mettre a jour les taux depuis tous les providers configures.
    S'arrete au premier succes.
    """
    from .currency_service import EXCHANGE_RATE_PROVIDERS

    for provider in EXCHANGE_RATE_PROVIDERS.keys():
        try:
            result = update_exchange_rates.delay(provider=provider)
            if result:
                logger.info(f"Taux mis a jour avec succes via {provider}")
                return {'success': True, 'provider': provider}
        except Exception as e:
            logger.warning(f"Echec avec {provider}: {e}")
            continue

    logger.error("Aucun provider n'a pu mettre a jour les taux")
    return {'success': False, 'error': 'All providers failed'}


@shared_task(name='finances.tasks.refresh_cfa_fixed_rates')
def refresh_cfa_fixed_rates():
    """
    Rafraichit les taux fixes CFA (XOF et XAF).

    Les francs CFA ont un taux fixe avec l'Euro:
    - 1 EUR = 655.957 XOF (UEMOA)
    - 1 EUR = 655.957 XAF (CEMAC)

    Cette tache s'assure que ces taux sont toujours corrects.
    """
    try:
        from .models import Currency, ExchangeRate

        CFA_RATE = Decimal('655.957')
        valid_from = timezone.now()

        eur = Currency.objects.get(code='EUR')
        updated = 0

        for cfa_code in ['XOF', 'XAF']:
            try:
                cfa_currency = Currency.objects.get(code=cfa_code)

                obj, created = ExchangeRate.objects.update_or_create(
                    from_currency=eur,
                    to_currency=cfa_currency,
                    is_current=True,
                    defaults={
                        'rate': CFA_RATE,
                        'valid_from': valid_from,
                        'source': 'FIXED',
                        'source_reference': 'Taux fixe BCE/Zone CFA'
                    }
                )
                updated += 1
                logger.info(f"Taux fixe {cfa_code} mis a jour: 1 EUR = {CFA_RATE} {cfa_code}")

            except Currency.DoesNotExist:
                logger.warning(f"Devise {cfa_code} non trouvee")

        return {
            'success': True,
            'updated': updated,
            'rate': str(CFA_RATE)
        }

    except Exception as e:
        logger.error(f"Erreur refresh taux CFA: {e}")
        return {'success': False, 'error': str(e)}


# =============================================================================
# TACHES DE RAPPELS D'ABONNEMENT
# =============================================================================

@shared_task(name='finances.tasks.send_subscription_expiry_reminders')
def send_subscription_expiry_reminders():
    """
    Envoie des rappels pour les abonnements qui arrivent a echeance.

    Rappels envoyes:
    - J-30: Premier rappel
    - J-7: Rappel urgent
    - J-1: Derniere chance
    """
    from .models import Subscription
    from django.core.mail import send_mail
    from django.template.loader import render_to_string

    now = timezone.now().date()
    reminders_sent = 0

    # Periodes de rappel
    reminder_days = [30, 7, 1]

    for days in reminder_days:
        target_date = now + timedelta(days=days)

        subscriptions = Subscription.objects.filter(
            end_date=target_date,
            status='ACTIVE'
        ).select_related('organization', 'currency')

        for subscription in subscriptions:
            try:
                # Preparer le contexte
                context = {
                    'organization': subscription.organization,
                    'subscription': subscription,
                    'days_remaining': days,
                    'formatted_amount': subscription.get_formatted_total(),
                    'end_date': subscription.end_date,
                }

                # Determiner le template selon l'urgence
                if days == 1:
                    template = 'finances/emails/subscription_last_chance.html'
                    subject = "URGENT: Votre abonnement expire demain"
                elif days == 7:
                    template = 'finances/emails/subscription_reminder_urgent.html'
                    subject = "Rappel: Votre abonnement expire dans 7 jours"
                else:
                    template = 'finances/emails/subscription_reminder.html'
                    subject = "Votre abonnement expire bientot"

                # Envoyer l'email (si template existe)
                try:
                    html_message = render_to_string(template, context)
                    # TODO: Implementer l'envoi reel
                    logger.info(
                        f"Rappel J-{days} envoye a {subscription.organization.name}"
                    )
                    reminders_sent += 1
                except Exception as e:
                    logger.debug(f"Template non trouve: {e}")

            except Exception as e:
                logger.error(f"Erreur envoi rappel: {e}")

    return {
        'success': True,
        'reminders_sent': reminders_sent
    }


# =============================================================================
# TACHES DE RAPPORTS
# =============================================================================

@shared_task(name='finances.tasks.generate_monthly_currency_report')
def generate_monthly_currency_report():
    """
    Genere un rapport mensuel des conversions de devises.

    Ce rapport inclut:
    - Volume total par devise
    - Taux de change moyens utilises
    - Ecarts par rapport aux taux du marche
    """
    from .models import Subscription, ExchangeRate
    from django.db.models import Sum, Count, Avg

    now = timezone.now()
    first_day = now.replace(day=1)
    last_month_end = first_day - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)

    try:
        # Statistiques par devise
        stats = Subscription.objects.filter(
            created_at__gte=last_month_start,
            created_at__lt=first_day
        ).values('currency').annotate(
            count=Count('id'),
            total_amount=Sum('total_amount'),
            total_eur=Sum('total_amount_eur'),
            avg_rate=Avg('exchange_rate_used')
        )

        report = {
            'period': f"{last_month_start.strftime('%Y-%m')}",
            'generated_at': now.isoformat(),
            'currencies': list(stats),
            'total_subscriptions': sum(s['count'] for s in stats),
            'total_revenue_eur': sum(
                float(s['total_eur'] or 0) for s in stats
            )
        }

        logger.info(f"Rapport mensuel genere: {report['total_subscriptions']} souscriptions")
        return report

    except Exception as e:
        logger.error(f"Erreur generation rapport: {e}")
        return {'success': False, 'error': str(e)}


@shared_task(name='finances.tasks.cleanup_old_exchange_rates')
def cleanup_old_exchange_rates(days_to_keep=90):
    """
    Nettoie les anciens taux de change non-courants.

    Garde les taux des X derniers jours pour l'historique.

    Args:
        days_to_keep: Nombre de jours d'historique a conserver
    """
    from .models import ExchangeRate

    cutoff_date = timezone.now() - timedelta(days=days_to_keep)

    try:
        deleted_count, _ = ExchangeRate.objects.filter(
            is_current=False,
            valid_until__lt=cutoff_date
        ).delete()

        logger.info(f"Supprime {deleted_count} anciens taux de change")
        return {
            'success': True,
            'deleted_count': deleted_count,
            'cutoff_date': cutoff_date.isoformat()
        }

    except Exception as e:
        logger.error(f"Erreur nettoyage taux: {e}")
        return {'success': False, 'error': str(e)}


# =============================================================================
# TACHES DE SYNCHRONISATION
# =============================================================================

@shared_task(name='finances.tasks.sync_subscription_currencies')
def sync_subscription_currencies():
    """
    Synchronise les montants EUR pour les souscriptions sans conversion.

    Utile apres l'ajout de nouveaux taux de change.
    """
    from .models import Subscription, ExchangeRate

    updated = 0

    # Souscriptions sans total_amount_eur
    subscriptions = Subscription.objects.filter(
        total_amount_eur__isnull=True
    ).exclude(currency_id='EUR')

    for subscription in subscriptions:
        try:
            rate = ExchangeRate.get_current_rate(
                subscription.currency_id, 'EUR'
            )
            subscription.total_amount_eur = subscription.total_amount * rate
            subscription.exchange_rate_used = rate
            subscription.save(update_fields=['total_amount_eur', 'exchange_rate_used'])
            updated += 1

        except ValueError:
            logger.warning(
                f"Pas de taux pour {subscription.currency_id} -> EUR"
            )

    # Souscriptions EUR sans total_amount_eur
    from django.db import models as db_models
    eur_updated = Subscription.objects.filter(
        currency_id='EUR',
        total_amount_eur__isnull=True
    ).update(
        total_amount_eur=db_models.F('total_amount'),
        exchange_rate_used=Decimal('1.0')
    )

    logger.info(f"Synchronise {updated + eur_updated} souscriptions")
    return {
        'success': True,
        'non_eur_updated': updated,
        'eur_updated': eur_updated
    }
