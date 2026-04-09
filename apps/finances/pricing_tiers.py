"""
Constantes et fonctions de pricing pour le système 2 offres (Free / Premium).

MATURE: Marchés à prix plein (9,99 EUR/membre/an ou 0,99 EUR/membre/mois)
EMERGENT: Marchés à prix réduit (4,99 EUR/membre/an ou 0,49 EUR/membre/mois)
"""
from decimal import Decimal
from django.utils.translation import gettext_lazy as _


# ---- Subscription tier constants ----
PRICING_TIER_FREE = 'free'
PRICING_TIER_PREMIUM = 'premium'

PRICING_TIER_CHOICES = [
    (PRICING_TIER_FREE, _('Gratuit')),
    (PRICING_TIER_PREMIUM, _('Premium')),
]

# ---- Market maturity tier constants ----
MARKET_TIER_MATURE = 'mature'
MARKET_TIER_EMERGENT = 'emergent'

MARKET_TIER_CHOICES = [
    (MARKET_TIER_MATURE, _('Marchés matures')),
    (MARKET_TIER_EMERGENT, _('Marchés émergents')),
]

# ---- Pricing per market tier ----
PRICING = {
    MARKET_TIER_MATURE: {
        'yearly_per_member': Decimal('9.99'),
        'monthly_per_member': Decimal('0.99'),
        'currency': 'EUR',
    },
    MARKET_TIER_EMERGENT: {
        'yearly_per_member': Decimal('4.99'),
        'monthly_per_member': Decimal('0.49'),
        'currency': 'EUR',
    },
}

FREE_TIER_MAX_MEMBERS = 10

# ---- Country to market tier mapping ----
# ISO 3166-1 alpha-2 codes for mature markets
MATURE_COUNTRIES = {
    # Western Europe
    'FR', 'DE', 'ES', 'IT', 'PT', 'NL', 'BE', 'IE', 'AT', 'GR', 'FI',
    'GB', 'CH', 'NO', 'SE', 'DK', 'LU', 'IS', 'MC', 'LI',
    # Central/Eastern Europe (EU high-income)
    'PL', 'CZ', 'RO', 'HR', 'SI', 'SK', 'HU', 'BG', 'LT', 'LV', 'EE',
    'CY', 'MT',
    # North America
    'US', 'CA',
    # Oceania
    'AU', 'NZ',
    # East Asia (high-income)
    'JP', 'KR', 'SG', 'HK', 'TW',
    # Middle East (high-income)
    'AE', 'SA', 'QA', 'KW', 'BH', 'OM',
    # Other high-income
    'IL',
}

# Full-name variants for matching Organization.country (freeform CharField)
MATURE_COUNTRY_NAMES = {
    # French names (primary language of the platform)
    'France', 'Allemagne', 'Espagne', 'Italie', 'Portugal', 'Pays-Bas',
    'Belgique', 'Irlande', 'Autriche', 'Grèce', 'Finlande',
    'Royaume-Uni', 'Suisse', 'Norvège', 'Suède', 'Danemark',
    'Luxembourg', 'Islande', 'Monaco', 'Liechtenstein',
    'Pologne', 'République tchèque', 'Tchéquie', 'Roumanie',
    'Croatie', 'Slovénie', 'Slovaquie', 'Hongrie', 'Bulgarie',
    'Lituanie', 'Lettonie', 'Estonie', 'Chypre', 'Malte',
    'États-Unis', 'Canada',
    'Australie', 'Nouvelle-Zélande',
    'Japon', 'Corée du Sud', 'Singapour', 'Hong Kong', 'Taïwan',
    'Émirats arabes unis', 'Arabie saoudite', 'Qatar', 'Koweït',
    'Bahreïn', 'Oman',
    'Israël',
    # English names
    'Germany', 'Spain', 'Italy', 'Netherlands', 'Belgium',
    'Ireland', 'Austria', 'Greece', 'Finland',
    'United Kingdom', 'UK', 'Switzerland', 'Norway', 'Sweden', 'Denmark',
    'Iceland',
    'Poland', 'Czech Republic', 'Czechia', 'Romania',
    'Croatia', 'Slovenia', 'Slovakia', 'Hungary', 'Bulgaria',
    'Lithuania', 'Latvia', 'Estonia', 'Cyprus', 'Malta',
    'United States', 'USA',
    'Australia', 'New Zealand',
    'Japan', 'South Korea', 'Singapore', 'Taiwan',
    'United Arab Emirates', 'UAE', 'Saudi Arabia',
    'Kuwait', 'Bahrain',
    'Israel',
}


def get_market_tier_for_country(country):
    """
    Détermine le tier marché (mature/emergent) pour un pays donné.

    Args:
        country: Code ISO alpha-2 OU nom complet du pays
                 (correspondant au champ Organization.country)

    Returns:
        'mature' ou 'emergent'
    """
    if not country:
        return MARKET_TIER_MATURE  # Défaut = mature (prix plus élevé, plus sûr)

    country_stripped = country.strip()

    # Vérifier le code ISO (uppercase)
    if country_stripped.upper() in MATURE_COUNTRIES:
        return MARKET_TIER_MATURE

    # Vérifier le nom complet (exact match)
    if country_stripped in MATURE_COUNTRY_NAMES:
        return MARKET_TIER_MATURE

    # Vérifier en title case
    if country_stripped.title() in MATURE_COUNTRY_NAMES:
        return MARKET_TIER_MATURE

    return MARKET_TIER_EMERGENT


def get_price_for_country(country, billing_cycle='yearly'):
    """
    Retourne le prix par membre pour le pays d'une organisation.

    Args:
        country: Valeur de Organization.country
        billing_cycle: 'yearly' ou 'monthly'

    Returns:
        Decimal prix par membre
    """
    tier = get_market_tier_for_country(country)
    key = 'yearly_per_member' if billing_cycle == 'yearly' else 'monthly_per_member'
    return PRICING[tier][key]
