# -*- coding: utf-8 -*-
"""
Migration: Ajout des modèles Currency et ExchangeRate pour le support multi-devise.

Cette migration:
1. Crée le modèle Currency avec les devises initiales
2. Crée le modèle ExchangeRate pour les taux de change
3. Ajoute les taux de change initiaux (fallback)

Créé: Janvier 2025
"""

from django.db import migrations, models
import django.db.models.deletion
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils import timezone


def create_initial_currencies(apps, schema_editor):
    """
    Crée les devises initiales supportées par MartialComp.

    Priorité 1 (P1): EUR, USD, XOF - 80% des utilisateurs
    Priorité 2 (P2): GBP, CHF, JPY - marchés premium
    Priorité 3 (P3): BRL, INR, CNY, XAF - expansion future
    """
    Currency = apps.get_model('finances', 'Currency')

    currencies_data = [
        # P1 - Devises principales
        {
            'code': 'EUR',
            'name': 'Euro',
            'name_local': 'Euro',
            'symbol': '€',
            'decimal_places': 2,
            'symbol_position': 'after',
            'thousand_separator': ' ',
            'decimal_separator': ',',
            'is_active': True,
            'is_base_currency': True,
            'stripe_supported': True,
            'paypal_supported': True,
            'mobile_money_supported': False,
            'countries': 'FR,DE,IT,ES,PT,BE,NL,AT,IE,FI,LU,MT,CY,SK,SI,EE,LV,LT,GR,AD,MC,SM,VA',
        },
        {
            'code': 'USD',
            'name': 'US Dollar',
            'name_local': 'Dollar américain',
            'symbol': '$',
            'decimal_places': 2,
            'symbol_position': 'before',
            'thousand_separator': ',',
            'decimal_separator': '.',
            'is_active': True,
            'is_base_currency': False,
            'stripe_supported': True,
            'paypal_supported': True,
            'mobile_money_supported': False,
            'countries': 'US,EC,SV,PA,PR,VI,GU,AS,MP',
        },
        {
            'code': 'XOF',
            'name': 'CFA Franc BCEAO',
            'name_local': 'Franc CFA (UEMOA)',
            'symbol': 'FCFA',
            'decimal_places': 0,
            'symbol_position': 'after',
            'thousand_separator': ' ',
            'decimal_separator': ',',
            'is_active': True,
            'is_base_currency': False,
            'stripe_supported': False,
            'paypal_supported': False,
            'mobile_money_supported': True,
            'countries': 'BJ,BF,CI,GW,ML,NE,SN,TG',
        },
        # P2 - Marchés premium
        {
            'code': 'GBP',
            'name': 'British Pound',
            'name_local': 'Livre sterling',
            'symbol': '£',
            'decimal_places': 2,
            'symbol_position': 'before',
            'thousand_separator': ',',
            'decimal_separator': '.',
            'is_active': True,
            'is_base_currency': False,
            'stripe_supported': True,
            'paypal_supported': True,
            'mobile_money_supported': False,
            'countries': 'GB,GG,IM,JE,GI,FK,GS,SH',
        },
        {
            'code': 'CHF',
            'name': 'Swiss Franc',
            'name_local': 'Franc suisse',
            'symbol': 'CHF',
            'decimal_places': 2,
            'symbol_position': 'after',
            'thousand_separator': "'",
            'decimal_separator': '.',
            'is_active': True,
            'is_base_currency': False,
            'stripe_supported': True,
            'paypal_supported': True,
            'mobile_money_supported': False,
            'countries': 'CH,LI',
        },
        {
            'code': 'JPY',
            'name': 'Japanese Yen',
            'name_local': '日本円',
            'symbol': '¥',
            'decimal_places': 0,
            'symbol_position': 'before',
            'thousand_separator': ',',
            'decimal_separator': '.',
            'is_active': True,
            'is_base_currency': False,
            'stripe_supported': True,
            'paypal_supported': True,
            'mobile_money_supported': False,
            'countries': 'JP',
        },
        # P3 - Expansion future
        {
            'code': 'BRL',
            'name': 'Brazilian Real',
            'name_local': 'Real brasileiro',
            'symbol': 'R$',
            'decimal_places': 2,
            'symbol_position': 'before',
            'thousand_separator': '.',
            'decimal_separator': ',',
            'is_active': True,
            'is_base_currency': False,
            'stripe_supported': True,
            'paypal_supported': True,
            'mobile_money_supported': False,
            'countries': 'BR',
        },
        {
            'code': 'INR',
            'name': 'Indian Rupee',
            'name_local': 'भारतीय रुपया',
            'symbol': '₹',
            'decimal_places': 2,
            'symbol_position': 'before',
            'thousand_separator': ',',
            'decimal_separator': '.',
            'is_active': True,
            'is_base_currency': False,
            'stripe_supported': True,
            'paypal_supported': True,
            'mobile_money_supported': False,
            'countries': 'IN',
        },
        {
            'code': 'CNY',
            'name': 'Chinese Yuan',
            'name_local': '人民币',
            'symbol': '¥',
            'decimal_places': 2,
            'symbol_position': 'before',
            'thousand_separator': ',',
            'decimal_separator': '.',
            'is_active': True,
            'is_base_currency': False,
            'stripe_supported': False,
            'paypal_supported': False,
            'mobile_money_supported': False,
            'countries': 'CN',
        },
        {
            'code': 'XAF',
            'name': 'CFA Franc BEAC',
            'name_local': 'Franc CFA (CEMAC)',
            'symbol': 'FCFA',
            'decimal_places': 0,
            'symbol_position': 'after',
            'thousand_separator': ' ',
            'decimal_separator': ',',
            'is_active': True,
            'is_base_currency': False,
            'stripe_supported': False,
            'paypal_supported': False,
            'mobile_money_supported': True,
            'countries': 'CM,CF,TD,CG,GA,GQ',
        },
        # Devises additionnelles utiles
        {
            'code': 'CAD',
            'name': 'Canadian Dollar',
            'name_local': 'Dollar canadien',
            'symbol': '$',
            'decimal_places': 2,
            'symbol_position': 'before',
            'thousand_separator': ',',
            'decimal_separator': '.',
            'is_active': True,
            'is_base_currency': False,
            'stripe_supported': True,
            'paypal_supported': True,
            'mobile_money_supported': False,
            'countries': 'CA',
        },
        {
            'code': 'MAD',
            'name': 'Moroccan Dirham',
            'name_local': 'الدرهم المغربي',
            'symbol': 'DH',
            'decimal_places': 2,
            'symbol_position': 'after',
            'thousand_separator': ' ',
            'decimal_separator': ',',
            'is_active': True,
            'is_base_currency': False,
            'stripe_supported': False,
            'paypal_supported': False,
            'mobile_money_supported': False,
            'countries': 'MA',
        },
    ]

    for data in currencies_data:
        Currency.objects.create(**data)


def create_initial_exchange_rates(apps, schema_editor):
    """
    Crée les taux de change initiaux (fallback).

    Ces taux sont des approximations et doivent être mis à jour
    régulièrement via la tâche Celery update_exchange_rates.

    Base: EUR = 1.0
    """
    Currency = apps.get_model('finances', 'Currency')
    ExchangeRate = apps.get_model('finances', 'ExchangeRate')

    # Taux approximatifs au 7 janvier 2025
    # EUR → autres devises
    rates_from_eur = {
        'USD': Decimal('1.0300'),      # 1 EUR = 1.03 USD
        'GBP': Decimal('0.8350'),      # 1 EUR = 0.835 GBP
        'CHF': Decimal('0.9400'),      # 1 EUR = 0.94 CHF
        'JPY': Decimal('162.50'),      # 1 EUR = 162.5 JPY
        'XOF': Decimal('655.957'),     # 1 EUR = 655.957 XOF (taux fixe)
        'XAF': Decimal('655.957'),     # 1 EUR = 655.957 XAF (taux fixe)
        'BRL': Decimal('6.3500'),      # 1 EUR = 6.35 BRL
        'INR': Decimal('89.50'),       # 1 EUR = 89.5 INR
        'CNY': Decimal('7.5200'),      # 1 EUR = 7.52 CNY
        'CAD': Decimal('1.4900'),      # 1 EUR = 1.49 CAD
        'MAD': Decimal('10.65'),       # 1 EUR = 10.65 MAD
    }

    now = timezone.now()

    try:
        eur = Currency.objects.get(code='EUR')
    except Currency.DoesNotExist:
        return

    for currency_code, rate in rates_from_eur.items():
        try:
            to_currency = Currency.objects.get(code=currency_code)
            ExchangeRate.objects.create(
                from_currency=eur,
                to_currency=to_currency,
                rate=rate,
                valid_from=now,
                valid_until=None,
                is_current=True,
                source='FALLBACK',
                source_reference='Initial migration data'
            )
        except Currency.DoesNotExist:
            continue


def reverse_currencies(apps, schema_editor):
    """Supprime les devises créées"""
    Currency = apps.get_model('finances', 'Currency')
    Currency.objects.all().delete()


def reverse_rates(apps, schema_editor):
    """Supprime les taux créés"""
    ExchangeRate = apps.get_model('finances', 'ExchangeRate')
    ExchangeRate.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('finances', '0004_initial'),
    ]

    operations = [
        # 1. Créer le modèle Currency
        migrations.CreateModel(
            name='Currency',
            fields=[
                ('code', models.CharField(
                    help_text='Code ISO 4217 de la devise (ex: EUR, USD, XOF)',
                    max_length=3,
                    primary_key=True,
                    serialize=False,
                    unique=True,
                    verbose_name='Code ISO 4217'
                )),
                ('name', models.CharField(
                    help_text='Nom complet de la devise',
                    max_length=100,
                    verbose_name='Nom'
                )),
                ('name_local', models.CharField(
                    blank=True,
                    help_text='Nom dans la langue locale (ex: Euro, Dollar américain)',
                    max_length=100,
                    verbose_name='Nom local'
                )),
                ('symbol', models.CharField(
                    help_text='Symbole de la devise (ex: €, $, FCFA)',
                    max_length=10,
                    verbose_name='Symbole'
                )),
                ('decimal_places', models.PositiveSmallIntegerField(
                    default=2,
                    help_text='Nombre de décimales (0 pour JPY, 2 pour EUR)',
                    verbose_name='Décimales'
                )),
                ('symbol_position', models.CharField(
                    choices=[('before', 'Avant le montant'), ('after', 'Après le montant')],
                    default='before',
                    help_text='Position du symbole par rapport au montant',
                    max_length=10,
                    verbose_name='Position du symbole'
                )),
                ('thousand_separator', models.CharField(
                    default=' ',
                    help_text='Caractère de séparation des milliers',
                    max_length=1,
                    verbose_name='Séparateur de milliers'
                )),
                ('decimal_separator', models.CharField(
                    default=',',
                    help_text='Caractère de séparation décimale',
                    max_length=1,
                    verbose_name='Séparateur décimal'
                )),
                ('is_active', models.BooleanField(
                    default=True,
                    help_text='Devise disponible pour les transactions',
                    verbose_name='Active'
                )),
                ('is_base_currency', models.BooleanField(
                    default=False,
                    help_text='Devise de référence pour les conversions (EUR)',
                    verbose_name='Devise de référence'
                )),
                ('stripe_supported', models.BooleanField(
                    default=False,
                    verbose_name='Supporté par Stripe'
                )),
                ('paypal_supported', models.BooleanField(
                    default=False,
                    verbose_name='Supporté par PayPal'
                )),
                ('mobile_money_supported', models.BooleanField(
                    default=False,
                    help_text='Pour Orange Money, MTN Mobile Money, etc.',
                    verbose_name='Supporté par Mobile Money'
                )),
                ('countries', models.TextField(
                    blank=True,
                    help_text='Liste des pays utilisant cette devise (codes ISO séparés par virgules)',
                    verbose_name='Pays'
                )),
                ('created_at', models.DateTimeField(
                    auto_now_add=True,
                    verbose_name='Créé le'
                )),
                ('updated_at', models.DateTimeField(
                    auto_now=True,
                    verbose_name='Modifié le'
                )),
            ],
            options={
                'verbose_name': 'Devise',
                'verbose_name_plural': 'Devises',
                'ordering': ['code'],
            },
        ),

        # 2. Créer le modèle ExchangeRate
        migrations.CreateModel(
            name='ExchangeRate',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True,
                    primary_key=True,
                    serialize=False,
                    verbose_name='ID'
                )),
                ('rate', models.DecimalField(
                    decimal_places=8,
                    help_text='Taux de conversion (ex: 1.10 pour 1 EUR = 1.10 USD)',
                    max_digits=18,
                    validators=[MinValueValidator(Decimal('0.00000001'))],
                    verbose_name='Taux'
                )),
                ('valid_from', models.DateTimeField(
                    help_text='Date/heure de début de validité',
                    verbose_name='Valide depuis'
                )),
                ('valid_until', models.DateTimeField(
                    blank=True,
                    help_text='Date/heure de fin de validité (null = toujours valide)',
                    null=True,
                    verbose_name="Valide jusqu'à"
                )),
                ('is_current', models.BooleanField(
                    db_index=True,
                    default=True,
                    help_text='Ce taux est-il le taux actuel pour cette paire de devises?',
                    verbose_name='Taux actuel'
                )),
                ('source', models.CharField(
                    choices=[
                        ('ECB', 'Banque Centrale Européenne'),
                        ('OPENEXCHANGE', 'Open Exchange Rates'),
                        ('FIXER', 'Fixer.io'),
                        ('MANUAL', 'Saisie manuelle'),
                        ('FALLBACK', 'Taux de secours'),
                    ],
                    default='OPENEXCHANGE',
                    max_length=50,
                    verbose_name='Source'
                )),
                ('source_reference', models.CharField(
                    blank=True,
                    help_text='ID ou référence de la source (pour audit)',
                    max_length=100,
                    verbose_name='Référence source'
                )),
                ('created_at', models.DateTimeField(
                    auto_now_add=True,
                    verbose_name='Créé le'
                )),
                ('from_currency', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='rates_from',
                    to='finances.currency',
                    verbose_name='Devise source'
                )),
                ('to_currency', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='rates_to',
                    to='finances.currency',
                    verbose_name='Devise cible'
                )),
            ],
            options={
                'verbose_name': 'Taux de change',
                'verbose_name_plural': 'Taux de change',
                'ordering': ['-valid_from'],
            },
        ),

        # 3. Ajouter les index
        migrations.AddIndex(
            model_name='exchangerate',
            index=models.Index(
                fields=['from_currency', 'to_currency', 'is_current'],
                name='idx_exchange_current'
            ),
        ),
        migrations.AddIndex(
            model_name='exchangerate',
            index=models.Index(
                fields=['from_currency', 'to_currency', 'valid_from'],
                name='idx_exchange_history'
            ),
        ),

        # 4. Ajouter la contrainte (devises différentes)
        migrations.AddConstraint(
            model_name='exchangerate',
            constraint=models.CheckConstraint(
                check=~models.Q(from_currency=models.F('to_currency')),
                name='different_currencies'
            ),
        ),

        # 5. Peupler les devises initiales
        migrations.RunPython(
            create_initial_currencies,
            reverse_currencies
        ),

        # 6. Peupler les taux de change initiaux
        migrations.RunPython(
            create_initial_exchange_rates,
            reverse_rates
        ),
    ]
