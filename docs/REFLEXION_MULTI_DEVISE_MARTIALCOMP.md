# 🌍 Réflexion : Implémentation Multi-Devise pour MartialComp

**Date** : Janvier 2025  
**Version** : 1.0  
**Statut** : Analyse et Recommandations

---

## 📋 Table des Matières

1. [État des Lieux](#1-état-des-lieux)
2. [Analyse des Besoins](#2-analyse-des-besoins)
3. [Stratégie d'Implémentation](#3-stratégie-dimplémentation)
4. [Architecture Proposée](#4-architecture-proposée)
5. [Plan de Migration](#5-plan-de-migration)
6. [Considérations Techniques](#6-considérations-techniques)
7. [Risques et Mitigations](#7-risques-et-mitigations)

---

## 1. État des Lieux

### 1.1 Langues Implémentées (18 langues)

| Tier | Langue | Code | Statut | Couverture |
|------|--------|------|--------|------------|
| **1** | 🇫🇷 Français | `fr` | ✅ Stable | 100% |
| **1** | 🇬🇧 Anglais | `en` | ✅ Stable | 100% |
| **1** | 🇩🇪 Allemand | `de` | ✅ Stable | 98% |
| **1** | 🇪🇸 Espagnol | `es` | ✅ Stable | 95% |
| **1** | 🇮🇹 Italien | `it` | ✅ Stable | 90% |
| **1** | 🇵🇹 Portugais | `pt` | ✅ Stable | 85% |
| **1** | 🇳🇴 Norvégien | `no` | ✅ Stable | 80% |
| **1** | 🇸🇦 Arabe | `ar` | ✅ Stable | 75% |
| **2** | 🇨🇳 Chinois | `zh-hans` | 🔄 En cours | 35% |
| **2** | 🇯🇵 Japonais | `ja` | 🔄 En cours | 30% |
| **2** | 🇰🇷 Coréen | `ko` | 🔄 En cours | 25% |
| **2** | 🇮🇳 Hindi | `hi` | 🔄 En cours | 20% |
| **2** | 🇻🇳 Vietnamien | `vi` | 🔄 En cours | 20% |
| **2** | 🇷🇺 Russe | `ru` | 🔄 En cours | 15% |
| **2** | 🇪🇹 Amharique | `am` | 🔄 En cours | 15% |
| **2** | 🇹🇿 Swahili | `sw` | 🔄 En cours | 12% |
| **2** | 🇳🇬 Yoruba | `yo` | 🔄 En cours | 8% |
| **2** | 🇿🇦 Zoulou | `zu` | 🔄 En cours | 8% |

### 1.2 Système de Pricing Actuel

#### Frontend (JavaScript) - `welcome.html`

```javascript
const pricingData = {
    africa: {
        currency: 'FCFA',
        club: { price: '2 000', members: '25' },
        pro: { price: '15 000', members: '100' },
        fed: { price: '35 000', members: '500' },
        modules: { comp: '10 000', gest: '9 000' }
    },
    asia: {
        currency: '€',
        club: { price: '10', members: '25' },
        pro: { price: '29', members: '100' },
        fed: { price: '69', members: '500' },
        modules: { comp: '15', gest: '12' }
    },
    europe: {
        currency: '€',
        club: { price: '29', members: '25' },
        pro: { price: '89', members: '100' },
        fed: { price: '199', members: '500' },
        modules: { comp: '39', gest: '29' }
    },
    americas: {
        currency: '€',
        club: { price: '35', members: '25' },
        pro: { price: '99', members: '100' },
        fed: { price: '249', members: '500' },
        modules: { comp: '49', gest: '39' }
    }
};
```

#### Backend (Django) - Modèles Existants

```python
# finances/models/pricing.py
class PricingRegion(models.Model):
    name = CharField(...)
    base_price_per_member = DecimalField(...)
    # ⚠️ PAS de champ currency explicite

class VolumeDiscount(models.Model):
    min_members = IntegerField(...)
    discount_percentage = DecimalField(...)

# subscriptions/models.py
class Subscription(models.Model):
    organization = ForeignKey(Organization, ...)
    region = ForeignKey(PricingRegion, ...)
    total_amount = DecimalField(max_digits=10, decimal_places=2)
    # ⚠️ PAS de champ currency - montant en EUR implicite
```

### 1.3 Problèmes Identifiés

| # | Problème | Impact | Criticité |
|---|----------|--------|-----------|
| 1 | **Pas de champ `currency`** sur `Subscription` | Impossible de savoir la devise d'un montant stocké | 🔴 Critique |
| 2 | **Devise implicite** (EUR partout sauf affichage) | Incohérence entre affichage et stockage | 🔴 Critique |
| 3 | **Pas de taux de change** dynamiques | Impossible de convertir entre devises | 🟡 Haute |
| 4 | **Passerelles de paiement** mono-devise | Stripe configuré uniquement en EUR | 🟡 Haute |
| 5 | **Reporting** sans agrégation multi-devise | Rapports financiers faussés | 🟡 Haute |
| 6 | **Frontend hardcodé** par zone | Pas de détection automatique | 🟢 Moyenne |

### 1.4 État Production vs Développement

| Aspect | Production | Développement | Écart |
|--------|------------|---------------|-------|
| Django | 3.2.19 | 3.2.x | ✅ Identique |
| Fichiers Python | 1050 | 1051 | ⚠️ 1 fichier |
| Templates HTML | 928 | 935 | ⚠️ 7 templates |
| Traductions à jour | 8 langues | 18 langues | ⚠️ 10 anciennes |
| Database | 55GB, 267 tables | - | - |

---

## 2. Analyse des Besoins

### 2.1 Devises Cibles par Région

| Région | Devise | Code ISO | Symbole | Priorité |
|--------|--------|----------|---------|----------|
| **Europe** | Euro | EUR | € | 🔴 P1 |
| **Afrique FCFA** | Franc CFA | XOF | FCFA | 🔴 P1 |
| **Amérique Nord** | Dollar US | USD | $ | 🔴 P1 |
| **Royaume-Uni** | Livre Sterling | GBP | £ | 🟡 P2 |
| **Suisse** | Franc Suisse | CHF | CHF | 🟡 P2 |
| **Japon** | Yen | JPY | ¥ | 🟡 P2 |
| **Brésil** | Real | BRL | R$ | 🟢 P3 |
| **Inde** | Roupie | INR | ₹ | 🟢 P3 |
| **Chine** | Yuan | CNY | ¥ | 🟢 P3 |
| **Afrique Autres** | Mobile Money | - | - | 🟢 P3 |

### 2.2 Cas d'Usage Multi-Devise

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CAS D'USAGE MULTI-DEVISE                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1️⃣ ORGANISATION LOCALE                                            │
│     Club en France → Paye en EUR                                   │
│     Club au Sénégal → Paye en FCFA                                 │
│     Club aux USA → Paye en USD                                     │
│                                                                     │
│  2️⃣ COMPÉTITION INTERNATIONALE                                     │
│     Frais d'inscription en devise locale du participant            │
│     Organisateur reçoit dans sa devise                             │
│     Conversion automatique                                         │
│                                                                     │
│  3️⃣ REPORTING MartialComp                                          │
│     Agrégation globale en EUR (devise de référence)                │
│     Rapports par région en devise locale                           │
│     Historique des taux pour les audits                            │
│                                                                     │
│  4️⃣ PAIEMENTS INTER-ORGANISATIONS                                  │
│     Fédération FR collecte de clubs BE, CH, DE                     │
│     → Tout converti en EUR automatiquement                         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.3 Matrice Langue ↔ Devise par Défaut

| Langue | Code | Devise par défaut | Alternatives |
|--------|------|-------------------|--------------|
| Français | fr | EUR | XOF, CHF, CAD |
| Anglais | en | USD | GBP, EUR, AUD |
| Allemand | de | EUR | CHF |
| Espagnol | es | EUR | USD, MXN |
| Italien | it | EUR | - |
| Portugais | pt | EUR | BRL |
| Arabe | ar | EUR | SAR, AED |
| Chinois | zh | CNY | USD |
| Japonais | ja | JPY | - |
| Coréen | ko | KRW | - |
| Hindi | hi | INR | - |
| Swahili | sw | KES | TZS |
| Amharique | am | ETB | - |

---

## 3. Stratégie d'Implémentation

### 3.1 Principe Fondamental : NON-BREAKING CHANGES

```
┌─────────────────────────────────────────────────────────────────────┐
│                    STRATÉGIE DE MIGRATION                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  PRINCIPE : Ajouter SANS casser l'existant                         │
│                                                                     │
│  ✅ FAIRE :                                                         │
│     • Ajouter des champs avec valeurs par défaut                   │
│     • Créer de nouveaux modèles complémentaires                    │
│     • Utiliser des migrations réversibles                          │
│     • Implémenter en phases progressives                           │
│                                                                     │
│  ❌ NE PAS FAIRE :                                                  │
│     • Modifier les champs existants                                │
│     • Supprimer des colonnes                                       │
│     • Changer les types de données                                 │
│     • Déployer tout d'un coup                                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Plan en 4 Phases

```
Phase 1 (Semaine 1-2)          Phase 2 (Semaine 3-4)
┌─────────────────────┐        ┌─────────────────────┐
│ MODÈLES DE BASE     │        │ INTÉGRATION         │
│                     │        │                     │
│ • Currency          │───────►│ • Subscription      │
│ • ExchangeRate      │        │ • Payment           │
│ • PricingRegion+    │        │ • Invoice           │
│                     │        │                     │
└─────────────────────┘        └─────────────────────┘
         │                              │
         ▼                              ▼
Phase 3 (Semaine 5-6)          Phase 4 (Semaine 7-8)
┌─────────────────────┐        ┌─────────────────────┐
│ SERVICES            │        │ UI & ADMIN          │
│                     │        │                     │
│ • CurrencyService   │───────►│ • Sélecteur devise  │
│ • ConversionService │        │ • Formatage montants│
│ • RateUpdater       │        │ • Reporting         │
│                     │        │                     │
└─────────────────────┘        └─────────────────────┘
```

---

## 4. Architecture Proposée

### 4.1 Nouveaux Modèles

```python
# finances/models/currency.py

class Currency(models.Model):
    """
    Devises supportées par la plateforme
    """
    code = models.CharField(max_length=3, unique=True, primary_key=True)  # ISO 4217
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=10)
    decimal_places = models.PositiveSmallIntegerField(default=2)
    
    # Formatage
    symbol_position = models.CharField(
        max_length=10,
        choices=[('before', 'Avant'), ('after', 'Après')],
        default='before'
    )
    thousand_separator = models.CharField(max_length=1, default=',')
    decimal_separator = models.CharField(max_length=1, default='.')
    
    # État
    is_active = models.BooleanField(default=True)
    is_base_currency = models.BooleanField(default=False)  # EUR = True
    
    # Paiements
    stripe_supported = models.BooleanField(default=False)
    paypal_supported = models.BooleanField(default=False)
    mobile_money_supported = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Devise'
        verbose_name_plural = 'Devises'
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def format_amount(self, amount):
        """Formate un montant selon les conventions de la devise"""
        formatted = f"{amount:,.{self.decimal_places}f}"
        formatted = formatted.replace(',', 'TEMP')
        formatted = formatted.replace('.', self.decimal_separator)
        formatted = formatted.replace('TEMP', self.thousand_separator)
        
        if self.symbol_position == 'before':
            return f"{self.symbol}{formatted}"
        return f"{formatted} {self.symbol}"


class ExchangeRate(models.Model):
    """
    Taux de change historiques (devise source → EUR)
    """
    from_currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name='rates_from'
    )
    to_currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name='rates_to'
    )
    rate = models.DecimalField(max_digits=18, decimal_places=8)
    
    # Temporalité
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField(null=True, blank=True)
    is_current = models.BooleanField(default=True)
    
    # Source
    source = models.CharField(
        max_length=50,
        choices=[
            ('ECB', 'Banque Centrale Européenne'),
            ('OPENEXCHANGE', 'Open Exchange Rates'),
            ('MANUAL', 'Saisie manuelle'),
            ('FIXER', 'Fixer.io'),
        ],
        default='ECB'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Taux de change'
        verbose_name_plural = 'Taux de change'
        ordering = ['-valid_from']
        indexes = [
            models.Index(fields=['from_currency', 'to_currency', 'is_current']),
        ]
    
    def __str__(self):
        return f"1 {self.from_currency.code} = {self.rate} {self.to_currency.code}"
    
    @classmethod
    def get_current_rate(cls, from_currency, to_currency):
        """Récupère le taux actuel entre deux devises"""
        if from_currency == to_currency:
            return Decimal('1.0')
        
        try:
            rate = cls.objects.get(
                from_currency=from_currency,
                to_currency=to_currency,
                is_current=True
            )
            return rate.rate
        except cls.DoesNotExist:
            # Essayer la conversion inverse
            try:
                rate = cls.objects.get(
                    from_currency=to_currency,
                    to_currency=from_currency,
                    is_current=True
                )
                return Decimal('1.0') / rate.rate
            except cls.DoesNotExist:
                raise ValueError(f"Taux non trouvé: {from_currency} → {to_currency}")
```

### 4.2 Modifications des Modèles Existants (NON-BREAKING)

```python
# Modification de PricingRegion - AJOUT de champ
class PricingRegion(models.Model):
    # ... champs existants ...
    
    # NOUVEAU : devise par défaut de la région
    default_currency = models.ForeignKey(
        'Currency',
        on_delete=models.PROTECT,
        null=True,  # Permet migration progressive
        blank=True,
        default=None  # Par défaut EUR après migration
    )


# Modification de Subscription - AJOUT de champs
class Subscription(models.Model):
    # ... champs existants ...
    
    # NOUVEAUX CHAMPS
    currency = models.ForeignKey(
        'Currency',
        on_delete=models.PROTECT,
        null=True,  # Migration progressive
        blank=True,
        related_name='subscriptions'
    )
    
    # Montant en devise de référence (EUR) pour reporting
    total_amount_eur = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Montant converti en EUR au taux du jour"
    )
    
    exchange_rate_used = models.DecimalField(
        max_digits=18,
        decimal_places=8,
        null=True,
        blank=True,
        help_text="Taux de change utilisé lors de la création"
    )
    
    def save(self, *args, **kwargs):
        # Si pas de devise, utiliser celle de la région
        if not self.currency and self.region and self.region.default_currency:
            self.currency = self.region.default_currency
        
        # Calculer le montant EUR si devise différente
        if self.currency and self.currency.code != 'EUR' and self.total_amount:
            rate = ExchangeRate.get_current_rate(self.currency, 'EUR')
            self.total_amount_eur = self.total_amount * rate
            self.exchange_rate_used = rate
        elif self.currency and self.currency.code == 'EUR':
            self.total_amount_eur = self.total_amount
            self.exchange_rate_used = Decimal('1.0')
        
        super().save(*args, **kwargs)
```

### 4.3 Service de Conversion

```python
# finances/services/currency_service.py

from decimal import Decimal
from django.core.cache import cache
from django.utils import timezone

class CurrencyService:
    """
    Service centralisé pour toutes les opérations de devise
    """
    
    CACHE_TTL = 3600  # 1 heure
    BASE_CURRENCY = 'EUR'
    
    @classmethod
    def convert(cls, amount, from_currency, to_currency, date=None):
        """
        Convertit un montant d'une devise à une autre
        
        Args:
            amount: Montant à convertir (Decimal ou float)
            from_currency: Code ISO devise source (str ou Currency)
            to_currency: Code ISO devise cible (str ou Currency)
            date: Date pour taux historique (optionnel)
        
        Returns:
            Decimal: Montant converti
        """
        from finances.models.currency import Currency, ExchangeRate
        
        amount = Decimal(str(amount))
        
        # Normaliser les codes
        from_code = from_currency.code if hasattr(from_currency, 'code') else from_currency
        to_code = to_currency.code if hasattr(to_currency, 'code') else to_currency
        
        if from_code == to_code:
            return amount
        
        # Chercher en cache
        cache_key = f"exchange_rate:{from_code}:{to_code}"
        cached_rate = cache.get(cache_key)
        
        if cached_rate and not date:
            return amount * Decimal(str(cached_rate))
        
        # Récupérer le taux
        if date:
            rate = cls._get_historical_rate(from_code, to_code, date)
        else:
            rate = ExchangeRate.get_current_rate(from_code, to_code)
            cache.set(cache_key, str(rate), cls.CACHE_TTL)
        
        return amount * rate
    
    @classmethod
    def to_base_currency(cls, amount, from_currency):
        """Convertit vers la devise de référence (EUR)"""
        return cls.convert(amount, from_currency, cls.BASE_CURRENCY)
    
    @classmethod
    def from_base_currency(cls, amount, to_currency):
        """Convertit depuis la devise de référence (EUR)"""
        return cls.convert(amount, cls.BASE_CURRENCY, to_currency)
    
    @classmethod
    def format(cls, amount, currency_code):
        """Formate un montant selon les conventions de la devise"""
        from finances.models.currency import Currency
        
        try:
            currency = Currency.objects.get(code=currency_code)
            return currency.format_amount(amount)
        except Currency.DoesNotExist:
            return f"{amount:.2f} {currency_code}"
    
    @classmethod
    def get_user_currency(cls, user):
        """
        Détermine la devise préférée d'un utilisateur
        Ordre de priorité:
        1. Préférence utilisateur explicite
        2. Organisation de l'utilisateur
        3. Localisation (IP ou langue)
        4. EUR par défaut
        """
        from finances.models.currency import Currency
        
        # 1. Préférence utilisateur
        if hasattr(user, 'profile') and user.profile.preferred_currency:
            return user.profile.preferred_currency
        
        # 2. Organisation
        if hasattr(user, 'organization') and user.organization:
            if user.organization.default_currency:
                return user.organization.default_currency
        
        # 3. Langue → Devise par défaut
        language_currency_map = {
            'fr': 'EUR', 'en': 'USD', 'de': 'EUR', 'es': 'EUR',
            'it': 'EUR', 'pt': 'EUR', 'ja': 'JPY', 'zh': 'CNY',
            'ko': 'KRW', 'hi': 'INR', 'ar': 'EUR', 'sw': 'KES',
        }
        
        user_language = getattr(user, 'language', 'fr')[:2]
        currency_code = language_currency_map.get(user_language, 'EUR')
        
        try:
            return Currency.objects.get(code=currency_code)
        except Currency.DoesNotExist:
            return Currency.objects.get(code='EUR')
    
    @classmethod
    def _get_historical_rate(cls, from_code, to_code, date):
        """Récupère un taux historique pour une date donnée"""
        from finances.models.currency import ExchangeRate
        
        rate = ExchangeRate.objects.filter(
            from_currency__code=from_code,
            to_currency__code=to_code,
            valid_from__lte=date
        ).order_by('-valid_from').first()
        
        if rate:
            return rate.rate
        
        raise ValueError(f"Taux historique non trouvé: {from_code} → {to_code} au {date}")
```

### 4.4 Tâche de Mise à Jour des Taux

```python
# finances/tasks.py

from celery import shared_task
from decimal import Decimal
import requests
from django.utils import timezone
from django.conf import settings

@shared_task(name='finances.update_exchange_rates')
def update_exchange_rates():
    """
    Met à jour les taux de change depuis l'API ECB ou Open Exchange Rates
    Exécution: Quotidienne à 16h (après publication BCE)
    """
    from finances.models.currency import Currency, ExchangeRate
    
    # Récupérer toutes les devises actives
    currencies = Currency.objects.filter(is_active=True).exclude(code='EUR')
    
    # API gratuite: Open Exchange Rates (1000 req/mois gratuit)
    api_key = settings.OPENEXCHANGERATES_API_KEY
    url = f"https://openexchangerates.org/api/latest.json?app_id={api_key}&base=EUR"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        rates = data.get('rates', {})
        timestamp = timezone.now()
        
        # Marquer les anciens taux comme non-courants
        ExchangeRate.objects.filter(is_current=True).update(
            is_current=False,
            valid_until=timestamp
        )
        
        # Créer les nouveaux taux
        eur = Currency.objects.get(code='EUR')
        
        for currency in currencies:
            if currency.code in rates:
                ExchangeRate.objects.create(
                    from_currency=eur,
                    to_currency=currency,
                    rate=Decimal(str(rates[currency.code])),
                    valid_from=timestamp,
                    is_current=True,
                    source='OPENEXCHANGE'
                )
        
        return f"Taux mis à jour pour {len(currencies)} devises"
    
    except requests.RequestException as e:
        # Log l'erreur et réessayer plus tard
        raise self.retry(countdown=3600, exc=e)


@shared_task(name='finances.cleanup_old_rates')
def cleanup_old_exchange_rates():
    """
    Nettoie les anciens taux (garde 1 an d'historique)
    Exécution: Hebdomadaire
    """
    from finances.models.currency import ExchangeRate
    from datetime import timedelta
    
    cutoff = timezone.now() - timedelta(days=365)
    
    deleted, _ = ExchangeRate.objects.filter(
        valid_from__lt=cutoff,
        is_current=False
    ).delete()
    
    return f"{deleted} anciens taux supprimés"
```

---

## 5. Plan de Migration

### 5.1 Migration de Données

```python
# finances/migrations/XXXX_add_currency_support.py

from django.db import migrations, models
import django.db.models.deletion

def create_initial_currencies(apps, schema_editor):
    """Crée les devises initiales"""
    Currency = apps.get_model('finances', 'Currency')
    
    currencies_data = [
        {'code': 'EUR', 'name': 'Euro', 'symbol': '€', 'decimal_places': 2,
         'symbol_position': 'after', 'thousand_separator': ' ', 'decimal_separator': ',',
         'is_base_currency': True, 'stripe_supported': True, 'paypal_supported': True},
        
        {'code': 'USD', 'name': 'Dollar américain', 'symbol': '$', 'decimal_places': 2,
         'symbol_position': 'before', 'thousand_separator': ',', 'decimal_separator': '.',
         'stripe_supported': True, 'paypal_supported': True},
        
        {'code': 'XOF', 'name': 'Franc CFA (UEMOA)', 'symbol': 'FCFA', 'decimal_places': 0,
         'symbol_position': 'after', 'thousand_separator': ' ', 'decimal_separator': ',',
         'mobile_money_supported': True},
        
        {'code': 'XAF', 'name': 'Franc CFA (CEMAC)', 'symbol': 'FCFA', 'decimal_places': 0,
         'symbol_position': 'after', 'thousand_separator': ' ', 'decimal_separator': ',',
         'mobile_money_supported': True},
        
        {'code': 'GBP', 'name': 'Livre sterling', 'symbol': '£', 'decimal_places': 2,
         'symbol_position': 'before', 'stripe_supported': True, 'paypal_supported': True},
        
        {'code': 'CHF', 'name': 'Franc suisse', 'symbol': 'CHF', 'decimal_places': 2,
         'symbol_position': 'after', 'stripe_supported': True},
        
        {'code': 'JPY', 'name': 'Yen japonais', 'symbol': '¥', 'decimal_places': 0,
         'symbol_position': 'before', 'stripe_supported': True},
        
        {'code': 'CNY', 'name': 'Yuan chinois', 'symbol': '¥', 'decimal_places': 2,
         'symbol_position': 'before'},
        
        {'code': 'INR', 'name': 'Roupie indienne', 'symbol': '₹', 'decimal_places': 2,
         'symbol_position': 'before', 'stripe_supported': True},
        
        {'code': 'BRL', 'name': 'Real brésilien', 'symbol': 'R$', 'decimal_places': 2,
         'symbol_position': 'before', 'stripe_supported': True},
    ]
    
    for data in currencies_data:
        Currency.objects.create(**data)


def set_default_currency_on_regions(apps, schema_editor):
    """Associe EUR comme devise par défaut aux régions existantes"""
    PricingRegion = apps.get_model('finances', 'PricingRegion')
    Currency = apps.get_model('finances', 'Currency')
    
    eur = Currency.objects.get(code='EUR')
    PricingRegion.objects.filter(default_currency__isnull=True).update(default_currency=eur)


def set_currency_on_subscriptions(apps, schema_editor):
    """Met EUR sur toutes les souscriptions existantes"""
    Subscription = apps.get_model('subscriptions', 'Subscription')
    Currency = apps.get_model('finances', 'Currency')
    
    eur = Currency.objects.get(code='EUR')
    
    # Mettre à jour en batch pour performance
    Subscription.objects.filter(currency__isnull=True).update(
        currency=eur,
        total_amount_eur=models.F('total_amount'),
        exchange_rate_used=1.0
    )


class Migration(migrations.Migration):

    dependencies = [
        ('finances', 'XXXX_previous_migration'),
        ('subscriptions', 'XXXX_previous_migration'),
    ]

    operations = [
        # 1. Créer le modèle Currency
        migrations.CreateModel(
            name='Currency',
            fields=[
                ('code', models.CharField(max_length=3, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('symbol', models.CharField(max_length=10)),
                ('decimal_places', models.PositiveSmallIntegerField(default=2)),
                ('symbol_position', models.CharField(max_length=10, default='before')),
                ('thousand_separator', models.CharField(max_length=1, default=',')),
                ('decimal_separator', models.CharField(max_length=1, default='.')),
                ('is_active', models.BooleanField(default=True)),
                ('is_base_currency', models.BooleanField(default=False)),
                ('stripe_supported', models.BooleanField(default=False)),
                ('paypal_supported', models.BooleanField(default=False)),
                ('mobile_money_supported', models.BooleanField(default=False)),
            ],
        ),
        
        # 2. Créer le modèle ExchangeRate
        migrations.CreateModel(
            name='ExchangeRate',
            fields=[
                ('id', models.BigAutoField(primary_key=True)),
                ('rate', models.DecimalField(max_digits=18, decimal_places=8)),
                ('valid_from', models.DateTimeField()),
                ('valid_until', models.DateTimeField(null=True, blank=True)),
                ('is_current', models.BooleanField(default=True)),
                ('source', models.CharField(max_length=50, default='ECB')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('from_currency', models.ForeignKey('Currency', on_delete=models.CASCADE, related_name='rates_from')),
                ('to_currency', models.ForeignKey('Currency', on_delete=models.CASCADE, related_name='rates_to')),
            ],
        ),
        
        # 3. Ajouter currency à PricingRegion (nullable d'abord)
        migrations.AddField(
            model_name='pricingregion',
            name='default_currency',
            field=models.ForeignKey(
                'Currency',
                on_delete=models.PROTECT,
                null=True,
                blank=True
            ),
        ),
        
        # 4. Ajouter champs à Subscription (nullable d'abord)
        migrations.AddField(
            model_name='subscription',
            name='currency',
            field=models.ForeignKey(
                'finances.Currency',
                on_delete=models.PROTECT,
                null=True,
                blank=True
            ),
        ),
        migrations.AddField(
            model_name='subscription',
            name='total_amount_eur',
            field=models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='subscription',
            name='exchange_rate_used',
            field=models.DecimalField(max_digits=18, decimal_places=8, null=True, blank=True),
        ),
        
        # 5. Peupler les données
        migrations.RunPython(create_initial_currencies, migrations.RunPython.noop),
        migrations.RunPython(set_default_currency_on_regions, migrations.RunPython.noop),
        migrations.RunPython(set_currency_on_subscriptions, migrations.RunPython.noop),
    ]
```

### 5.2 Checklist de Déploiement

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CHECKLIST DÉPLOIEMENT MULTI-DEVISE               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  PRÉ-DÉPLOIEMENT                                                    │
│  ☐ Backup complet de la base de données                            │
│  ☐ Tests unitaires passent à 100%                                  │
│  ☐ Tests d'intégration validés                                     │
│  ☐ Review du code par un pair                                      │
│  ☐ Documentation mise à jour                                       │
│                                                                     │
│  PHASE 1 : MODÈLES (Jour 1)                                        │
│  ☐ Déployer migration Currency + ExchangeRate                      │
│  ☐ Vérifier création des devises initiales                         │
│  ☐ Exécuter tâche update_exchange_rates                            │
│  ☐ Vérifier les taux dans l'admin                                  │
│                                                                     │
│  PHASE 2 : SUBSCRIPTION (Jour 2)                                   │
│  ☐ Déployer migration ajout champs Subscription                    │
│  ☐ Exécuter migration de données (set_currency_on_subscriptions)   │
│  ☐ Vérifier que toutes les souscriptions ont currency=EUR          │
│  ☐ Tester création nouvelle souscription                           │
│                                                                     │
│  PHASE 3 : SERVICES (Jour 3)                                       │
│  ☐ Déployer CurrencyService                                        │
│  ☐ Configurer tâche Celery pour mise à jour quotidienne            │
│  ☐ Tester conversions via shell Django                             │
│                                                                     │
│  PHASE 4 : FRONTEND (Jour 4-5)                                     │
│  ☐ Déployer templates avec sélecteur de devise                     │
│  ☐ Tester affichage montants dans différentes devises              │
│  ☐ Vérifier le formatage (séparateurs, symboles)                   │
│                                                                     │
│  POST-DÉPLOIEMENT                                                   │
│  ☐ Monitorer les erreurs (Sentry/logs)                             │
│  ☐ Vérifier les métriques de performance                           │
│  ☐ Collecter feedback utilisateurs                                 │
│  ☐ Documenter les problèmes rencontrés                             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. Considérations Techniques

### 6.1 Intégration Stripe Multi-Devise

```python
# finances/services/stripe_service.py

import stripe
from django.conf import settings

class StripeMultiCurrencyService:
    """
    Gestion des paiements Stripe multi-devise
    """
    
    SUPPORTED_CURRENCIES = [
        'EUR', 'USD', 'GBP', 'CHF', 'JPY', 'CAD', 'AUD',
        'BRL', 'INR', 'MXN', 'SGD', 'HKD', 'NZD', 'SEK', 'NOK', 'DKK'
    ]
    
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY
    
    def create_payment_intent(self, amount, currency, organization, metadata=None):
        """
        Crée un PaymentIntent dans la devise spécifiée
        """
        if currency.upper() not in self.SUPPORTED_CURRENCIES:
            raise ValueError(f"Devise {currency} non supportée par Stripe")
        
        # Stripe attend les montants en centimes pour la plupart des devises
        # Sauf JPY qui n'a pas de décimales
        if currency.upper() in ['JPY', 'KRW', 'VND']:
            amount_cents = int(amount)
        else:
            amount_cents = int(amount * 100)
        
        return stripe.PaymentIntent.create(
            amount=amount_cents,
            currency=currency.lower(),
            metadata={
                'organization_id': organization.id,
                'organization_name': organization.name,
                **(metadata or {})
            },
            # Convertir automatiquement vers EUR sur le compte MartialComp
            transfer_data={
                'destination': settings.STRIPE_MARTIALCOMP_ACCOUNT_ID,
            } if settings.STRIPE_CONNECT_ENABLED else None
        )
    
    def get_balance_by_currency(self):
        """Récupère le solde par devise"""
        balance = stripe.Balance.retrieve()
        
        result = {}
        for available in balance.available:
            currency = available.currency.upper()
            result[currency] = {
                'available': available.amount / 100,
                'pending': next(
                    (p.amount / 100 for p in balance.pending if p.currency == available.currency),
                    0
                )
            }
        
        return result
```

### 6.2 Template Tags pour Affichage

```python
# finances/templatetags/currency_tags.py

from django import template
from django.utils.safestring import mark_safe
from finances.services.currency_service import CurrencyService

register = template.Library()

@register.filter
def format_currency(amount, currency_code):
    """
    Formate un montant dans une devise
    Usage: {{ 1234.56|format_currency:"EUR" }}
    """
    return CurrencyService.format(amount, currency_code)


@register.simple_tag(takes_context=True)
def user_currency_amount(context, amount, from_currency='EUR'):
    """
    Convertit et formate un montant dans la devise de l'utilisateur
    Usage: {% user_currency_amount 100 "EUR" %}
    """
    user = context.get('user')
    if user and user.is_authenticated:
        user_currency = CurrencyService.get_user_currency(user)
        converted = CurrencyService.convert(amount, from_currency, user_currency.code)
        return user_currency.format_amount(converted)
    return CurrencyService.format(amount, from_currency)


@register.inclusion_tag('finances/partials/currency_selector.html', takes_context=True)
def currency_selector(context):
    """
    Affiche un sélecteur de devise
    Usage: {% currency_selector %}
    """
    from finances.models.currency import Currency
    
    user = context.get('user')
    current_currency = None
    
    if user and user.is_authenticated:
        current_currency = CurrencyService.get_user_currency(user)
    
    return {
        'currencies': Currency.objects.filter(is_active=True),
        'current_currency': current_currency,
        'request': context.get('request'),
    }
```

### 6.3 API REST pour Multi-Devise

```python
# finances/api/serializers.py

from rest_framework import serializers
from finances.models.currency import Currency, ExchangeRate

class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = [
            'code', 'name', 'symbol', 'decimal_places',
            'symbol_position', 'is_active'
        ]


class ExchangeRateSerializer(serializers.ModelSerializer):
    from_currency = CurrencySerializer(read_only=True)
    to_currency = CurrencySerializer(read_only=True)
    
    class Meta:
        model = ExchangeRate
        fields = [
            'from_currency', 'to_currency', 'rate',
            'valid_from', 'source'
        ]


class ConversionRequestSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    from_currency = serializers.CharField(max_length=3)
    to_currency = serializers.CharField(max_length=3)
    date = serializers.DateField(required=False)


class ConversionResponseSerializer(serializers.Serializer):
    original_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    converted_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    from_currency = serializers.CharField()
    to_currency = serializers.CharField()
    rate_used = serializers.DecimalField(max_digits=18, decimal_places=8)
    formatted = serializers.CharField()


# finances/api/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

class CurrencyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Currency.objects.filter(is_active=True)
    serializer_class = CurrencySerializer
    
    @action(detail=False, methods=['get'])
    def rates(self, request):
        """GET /api/currencies/rates/ - Tous les taux actuels"""
        rates = ExchangeRate.objects.filter(is_current=True)
        serializer = ExchangeRateSerializer(rates, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def convert(self, request):
        """POST /api/currencies/convert/ - Conversion de montant"""
        serializer = ConversionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        try:
            converted = CurrencyService.convert(
                data['amount'],
                data['from_currency'],
                data['to_currency'],
                data.get('date')
            )
            
            to_currency = Currency.objects.get(code=data['to_currency'])
            
            return Response(ConversionResponseSerializer({
                'original_amount': data['amount'],
                'converted_amount': converted,
                'from_currency': data['from_currency'],
                'to_currency': data['to_currency'],
                'rate_used': ExchangeRate.get_current_rate(
                    data['from_currency'], data['to_currency']
                ),
                'formatted': to_currency.format_amount(converted)
            }).data)
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
```

---

## 7. Risques et Mitigations

### 7.1 Matrice des Risques

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| **Incohérence des taux de change** | Moyenne | Élevé | Cache Redis + validation quotidienne |
| **Erreurs d'arrondi** | Haute | Moyen | Utiliser `Decimal` partout, règles d'arrondi |
| **Performance (conversions)** | Moyenne | Moyen | Cache agressif, pré-calcul |
| **Migration échoue** | Basse | Critique | Backup, migration réversible, test staging |
| **API taux indisponible** | Basse | Moyen | Fallback sur dernier taux connu |
| **Stripe rejette devise** | Basse | Élevé | Validation préalable, liste blanche |

### 7.2 Points de Vigilance

```
┌─────────────────────────────────────────────────────────────────────┐
│                    POINTS DE VIGILANCE                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  💰 ARRONDIS                                                        │
│     • JPY, KRW : pas de décimales                                  │
│     • Toujours arrondir en faveur du client pour les conversions   │
│     • Utiliser ROUND_HALF_UP pour la comptabilité                  │
│                                                                     │
│  📊 REPORTING                                                       │
│     • Toujours stocker le montant EUR pour agrégation              │
│     • Garder trace du taux utilisé (audit)                         │
│     • Distinction : montant facturé vs montant reçu                │
│                                                                     │
│  🔒 SÉCURITÉ                                                        │
│     • Jamais de conversion côté client pour les paiements          │
│     • Valider la devise côté serveur avant paiement                │
│     • Rate limiting sur l'API de conversion                        │
│                                                                     │
│  ⚡ PERFORMANCE                                                     │
│     • Cache des taux : 1h minimum                                  │
│     • Batch les conversions quand possible                         │
│     • Index sur (from_currency, to_currency, is_current)           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📋 Résumé Exécutif

### Ce qui existe déjà ✅
- Système de pricing par région (4 zones)
- Affichage frontend avec devises (FCFA, EUR)
- Modèles `PricingRegion`, `VolumeDiscount`
- 18 langues implémentées

### Ce qui manque ❌
- Modèle `Currency` centralisé
- Stockage explicite de la devise sur les transactions
- Taux de change dynamiques
- Service de conversion
- Montant EUR de référence pour reporting

### Stratégie recommandée 🎯
1. **Phase 1** : Créer les modèles (Currency, ExchangeRate)
2. **Phase 2** : Ajouter `currency` aux modèles existants (non-breaking)
3. **Phase 3** : Implémenter les services de conversion
4. **Phase 4** : Mettre à jour le frontend

### Effort estimé ⏱️
- Développement : 4-6 semaines
- Tests : 1-2 semaines
- Déploiement progressif : 1 semaine
- **Total : 6-9 semaines**

### Priorité des devises 📊
1. 🔴 **P1** : EUR, XOF, USD (80% des utilisateurs)
2. 🟡 **P2** : GBP, CHF, JPY (marchés premium)
3. 🟢 **P3** : BRL, INR, CNY (expansion future)

---

**Document préparé pour discussion et validation avant implémentation.**
