"""
Data migration: Populate pricing_tier on all existing Organization records.
Uses the country field to determine mature vs emergent market.
"""
from django.db import migrations


# Inline the country sets to avoid importing from app code in migrations
MATURE_COUNTRIES = {
    'FR', 'DE', 'ES', 'IT', 'PT', 'NL', 'BE', 'IE', 'AT', 'GR', 'FI',
    'GB', 'CH', 'NO', 'SE', 'DK', 'LU', 'IS', 'MC', 'LI',
    'PL', 'CZ', 'RO', 'HR', 'SI', 'SK', 'HU', 'BG', 'LT', 'LV', 'EE',
    'CY', 'MT',
    'US', 'CA',
    'AU', 'NZ',
    'JP', 'KR', 'SG', 'HK', 'TW',
    'AE', 'SA', 'QA', 'KW', 'BH', 'OM',
    'IL',
}

MATURE_COUNTRY_NAMES = {
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


def get_market_tier(country):
    if not country:
        return 'mature'
    country_stripped = country.strip()
    if country_stripped.upper() in MATURE_COUNTRIES:
        return 'mature'
    if country_stripped in MATURE_COUNTRY_NAMES:
        return 'mature'
    if country_stripped.title() in MATURE_COUNTRY_NAMES:
        return 'mature'
    return 'emergent'


def populate_pricing_tiers(apps, schema_editor):
    Organization = apps.get_model('organizations', 'Organization')
    for org in Organization.objects.all():
        org.pricing_tier = get_market_tier(org.country)
        org.save(update_fields=['pricing_tier'])


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0016_add_pricing_tier'),
    ]

    operations = [
        migrations.RunPython(populate_pricing_tiers, reverse_noop),
    ]
