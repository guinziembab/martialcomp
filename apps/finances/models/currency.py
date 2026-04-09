# -*- coding: utf-8 -*-
"""
Modèles pour la gestion multi-devise de MartialComp

Ce module implémente:
- Currency: Devises supportées par la plateforme
- ExchangeRate: Taux de change historiques

Créé: Janvier 2025
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone


class Currency(models.Model):
    """
    Devises supportées par la plateforme MartialComp.

    Utilise les codes ISO 4217 (EUR, USD, XOF, etc.)
    """

    SYMBOL_POSITION_CHOICES = [
        ('before', _('Avant le montant')),
        ('after', _('Après le montant')),
    ]

    # Identification (clé primaire = code ISO 4217)
    code = models.CharField(
        _("Code ISO 4217"),
        max_length=3,
        unique=True,
        primary_key=True,
        help_text=_("Code ISO 4217 de la devise (ex: EUR, USD, XOF)")
    )
    name = models.CharField(
        _("Nom"),
        max_length=100,
        help_text=_("Nom complet de la devise")
    )
    name_local = models.CharField(
        _("Nom local"),
        max_length=100,
        blank=True,
        help_text=_("Nom dans la langue locale (ex: Euro, Dollar américain)")
    )
    symbol = models.CharField(
        _("Symbole"),
        max_length=10,
        help_text=_("Symbole de la devise (ex: €, $, FCFA)")
    )

    # Formatage
    decimal_places = models.PositiveSmallIntegerField(
        _("Décimales"),
        default=2,
        help_text=_("Nombre de décimales (0 pour JPY, 2 pour EUR)")
    )
    symbol_position = models.CharField(
        _("Position du symbole"),
        max_length=10,
        choices=SYMBOL_POSITION_CHOICES,
        default='before',
        help_text=_("Position du symbole par rapport au montant")
    )
    thousand_separator = models.CharField(
        _("Séparateur de milliers"),
        max_length=1,
        default=' ',
        help_text=_("Caractère de séparation des milliers")
    )
    decimal_separator = models.CharField(
        _("Séparateur décimal"),
        max_length=1,
        default=',',
        help_text=_("Caractère de séparation décimale")
    )

    # État
    is_active = models.BooleanField(
        _("Active"),
        default=True,
        help_text=_("Devise disponible pour les transactions")
    )
    is_base_currency = models.BooleanField(
        _("Devise de référence"),
        default=False,
        help_text=_("Devise de référence pour les conversions (EUR)")
    )

    # Support des passerelles de paiement
    stripe_supported = models.BooleanField(
        _("Supporté par Stripe"),
        default=False
    )
    paypal_supported = models.BooleanField(
        _("Supporté par PayPal"),
        default=False
    )
    mobile_money_supported = models.BooleanField(
        _("Supporté par Mobile Money"),
        default=False,
        help_text=_("Pour Orange Money, MTN Mobile Money, etc.")
    )

    # Métadonnées
    countries = models.TextField(
        _("Pays"),
        blank=True,
        help_text=_("Liste des pays utilisant cette devise (codes ISO séparés par virgules)")
    )

    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Modifié le"), auto_now=True)

    class Meta:
        app_label = 'finances'
        verbose_name = _('Devise')
        verbose_name_plural = _('Devises')
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"

    def save(self, *args, **kwargs):
        """S'assure qu'il n'y a qu'une seule devise de référence"""
        if self.is_base_currency:
            # Désactiver les autres devises de référence
            Currency.objects.filter(is_base_currency=True).exclude(
                code=self.code
            ).update(is_base_currency=False)
        super().save(*args, **kwargs)

    def format_amount(self, amount, include_symbol=True):
        """
        Formate un montant selon les conventions de la devise.

        Args:
            amount: Montant à formater (Decimal ou float)
            include_symbol: Inclure le symbole de la devise

        Returns:
            str: Montant formaté (ex: "1 234,56 €" ou "€1,234.56")
        """
        if amount is None:
            return ""

        # Convertir en Decimal si nécessaire
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))

        # Arrondir selon le nombre de décimales
        quantize_str = '1.' + '0' * self.decimal_places if self.decimal_places > 0 else '1'
        amount = amount.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)

        # Formater le nombre
        if self.decimal_places > 0:
            format_str = f"{{:,.{self.decimal_places}f}}"
        else:
            format_str = "{:,.0f}"

        formatted = format_str.format(float(amount))

        # Remplacer les séparateurs (Python utilise , et . par défaut)
        formatted = formatted.replace(',', 'TEMP_THOUSAND')
        formatted = formatted.replace('.', self.decimal_separator)
        formatted = formatted.replace('TEMP_THOUSAND', self.thousand_separator)

        if not include_symbol:
            return formatted

        # Ajouter le symbole
        if self.symbol_position == 'before':
            return f"{self.symbol}{formatted}"
        else:
            return f"{formatted} {self.symbol}"

    def get_countries_list(self):
        """Retourne la liste des codes pays"""
        if self.countries:
            return [c.strip() for c in self.countries.split(',')]
        return []

    @classmethod
    def get_base_currency(cls):
        """Retourne la devise de référence (EUR par défaut)"""
        try:
            return cls.objects.get(is_base_currency=True)
        except cls.DoesNotExist:
            # Fallback sur EUR
            return cls.objects.filter(code='EUR').first()

    @classmethod
    def get_by_country(cls, country_code):
        """
        Retourne la devise par défaut pour un pays.

        Args:
            country_code: Code ISO du pays (FR, US, SN, etc.)

        Returns:
            Currency ou None
        """
        currencies = cls.objects.filter(
            is_active=True,
            countries__icontains=country_code
        )
        return currencies.first()


class ExchangeRate(models.Model):
    """
    Taux de change historiques entre devises.

    Convention: Toujours stocker le taux FROM → TO
    où FROM est la devise source et TO la devise cible.

    Exemple: EUR → USD = 1.10 signifie 1 EUR = 1.10 USD
    """

    SOURCE_CHOICES = [
        ('ECB', _('Banque Centrale Européenne')),
        ('OPENEXCHANGE', _('Open Exchange Rates')),
        ('FIXER', _('Fixer.io')),
        ('MANUAL', _('Saisie manuelle')),
        ('FALLBACK', _('Taux de secours')),
    ]

    from_currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name='rates_from',
        verbose_name=_("Devise source")
    )
    to_currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name='rates_to',
        verbose_name=_("Devise cible")
    )

    rate = models.DecimalField(
        _("Taux"),
        max_digits=18,
        decimal_places=8,
        validators=[MinValueValidator(Decimal('0.00000001'))],
        help_text=_("Taux de conversion (ex: 1.10 pour 1 EUR = 1.10 USD)")
    )

    # Temporalité
    valid_from = models.DateTimeField(
        _("Valide depuis"),
        help_text=_("Date/heure de début de validité")
    )
    valid_until = models.DateTimeField(
        _("Valide jusqu'à"),
        null=True,
        blank=True,
        help_text=_("Date/heure de fin de validité (null = toujours valide)")
    )
    is_current = models.BooleanField(
        _("Taux actuel"),
        default=True,
        db_index=True,
        help_text=_("Ce taux est-il le taux actuel pour cette paire de devises?")
    )

    # Source et traçabilité
    source = models.CharField(
        _("Source"),
        max_length=50,
        choices=SOURCE_CHOICES,
        default='OPENEXCHANGE'
    )
    source_reference = models.CharField(
        _("Référence source"),
        max_length=100,
        blank=True,
        help_text=_("ID ou référence de la source (pour audit)")
    )

    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)

    class Meta:
        app_label = 'finances'
        verbose_name = _('Taux de change')
        verbose_name_plural = _('Taux de change')
        ordering = ['-valid_from']
        indexes = [
            models.Index(
                fields=['from_currency', 'to_currency', 'is_current'],
                name='idx_exchange_current'
            ),
            models.Index(
                fields=['from_currency', 'to_currency', 'valid_from'],
                name='idx_exchange_history'
            ),
        ]
        constraints = [
            models.CheckConstraint(
                check=~models.Q(from_currency=models.F('to_currency')),
                name='different_currencies'
            ),
        ]

    def __str__(self):
        return f"1 {self.from_currency.code} = {self.rate} {self.to_currency.code}"

    def save(self, *args, **kwargs):
        """
        Lors de la sauvegarde d'un nouveau taux courant,
        marque les anciens taux comme non-courants.
        """
        if self.is_current:
            # Marquer les anciens taux comme non-courants
            ExchangeRate.objects.filter(
                from_currency=self.from_currency,
                to_currency=self.to_currency,
                is_current=True
            ).exclude(pk=self.pk).update(
                is_current=False,
                valid_until=self.valid_from
            )

            # Invalider le cache
            cache_key = f"exchange_rate:{self.from_currency_id}:{self.to_currency_id}"
            cache.delete(cache_key)
            cache_key_reverse = f"exchange_rate:{self.to_currency_id}:{self.from_currency_id}"
            cache.delete(cache_key_reverse)

        super().save(*args, **kwargs)

    @classmethod
    def get_current_rate(cls, from_currency, to_currency):
        """
        Récupère le taux de change actuel entre deux devises.

        Args:
            from_currency: Code ISO ou instance Currency
            to_currency: Code ISO ou instance Currency

        Returns:
            Decimal: Taux de conversion

        Raises:
            ValueError: Si le taux n'est pas trouvé
        """
        # Normaliser les codes
        from_code = from_currency.code if hasattr(from_currency, 'code') else from_currency
        to_code = to_currency.code if hasattr(to_currency, 'code') else to_currency

        # Même devise = taux 1
        if from_code == to_code:
            return Decimal('1.0')

        # Chercher en cache
        cache_key = f"exchange_rate:{from_code}:{to_code}"
        cached_rate = cache.get(cache_key)
        if cached_rate is not None:
            return Decimal(str(cached_rate))

        # Chercher le taux direct
        try:
            rate_obj = cls.objects.get(
                from_currency_id=from_code,
                to_currency_id=to_code,
                is_current=True
            )
            rate = rate_obj.rate
            cache.set(cache_key, str(rate), 3600)  # Cache 1h
            return rate
        except cls.DoesNotExist:
            pass

        # Essayer le taux inverse
        try:
            rate_obj = cls.objects.get(
                from_currency_id=to_code,
                to_currency_id=from_code,
                is_current=True
            )
            rate = Decimal('1.0') / rate_obj.rate
            cache.set(cache_key, str(rate), 3600)
            return rate
        except cls.DoesNotExist:
            pass

        # Essayer via la devise de référence (EUR)
        base_currency = Currency.get_base_currency()
        if base_currency and from_code != base_currency.code and to_code != base_currency.code:
            try:
                # FROM → EUR → TO
                rate_from_to_base = cls.get_current_rate(from_code, base_currency.code)
                rate_base_to_to = cls.get_current_rate(base_currency.code, to_code)
                rate = rate_from_to_base * rate_base_to_to
                cache.set(cache_key, str(rate), 3600)
                return rate
            except ValueError:
                pass

        raise ValueError(
            f"Taux de change non trouvé: {from_code} → {to_code}. "
            f"Veuillez ajouter ce taux dans l'administration."
        )

    @classmethod
    def get_historical_rate(cls, from_currency, to_currency, date):
        """
        Récupère un taux de change historique pour une date donnée.

        Args:
            from_currency: Code ISO ou instance Currency
            to_currency: Code ISO ou instance Currency
            date: datetime ou date

        Returns:
            Decimal: Taux de conversion à cette date
        """
        from_code = from_currency.code if hasattr(from_currency, 'code') else from_currency
        to_code = to_currency.code if hasattr(to_currency, 'code') else to_currency

        if from_code == to_code:
            return Decimal('1.0')

        # Chercher le taux valide à cette date
        rate_obj = cls.objects.filter(
            from_currency_id=from_code,
            to_currency_id=to_code,
            valid_from__lte=date
        ).order_by('-valid_from').first()

        if rate_obj:
            return rate_obj.rate

        # Essayer le taux inverse
        rate_obj = cls.objects.filter(
            from_currency_id=to_code,
            to_currency_id=from_code,
            valid_from__lte=date
        ).order_by('-valid_from').first()

        if rate_obj:
            return Decimal('1.0') / rate_obj.rate

        raise ValueError(
            f"Taux historique non trouvé: {from_code} → {to_code} au {date}"
        )

    @classmethod
    def convert(cls, amount, from_currency, to_currency, date=None):
        """
        Convertit un montant d'une devise à une autre.

        Args:
            amount: Montant à convertir
            from_currency: Devise source
            to_currency: Devise cible
            date: Date pour taux historique (optionnel)

        Returns:
            Decimal: Montant converti
        """
        amount = Decimal(str(amount))

        if date:
            rate = cls.get_historical_rate(from_currency, to_currency, date)
        else:
            rate = cls.get_current_rate(from_currency, to_currency)

        return amount * rate
