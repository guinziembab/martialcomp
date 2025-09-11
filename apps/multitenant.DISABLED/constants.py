"""
Constantes pour le module multi-tenant.
"""
from django.utils.translation import gettext_lazy as _

# Choix pour les fonctionnalités
FEATURE_CHOICES = [
    ('basic_management', _('Gestion de base')),
    ('grades', _('Système de grades')),
    ('local_competitions', _('Compétitions locales')),
    ('all_competitions', _('Toutes compétitions')),
    ('technical_scoring', _('Notation technique')),
    ('reporting', _('Rapports avancés')),
    ('api_access', _('Accès API')),
    ('white_label', _('White label')),
    ('advanced_analytics', _('Analytics avancés')),
]

# Continents
CONTINENT_CHOICES = [
    ('africa', _('Afrique')),
    ('asia_se', _('Asie du Sud-Est')),
    ('asia_other', _('Asie (autres)')),
    ('south_america', _('Amérique du Sud')),
    ('central_america', _('Amérique Centrale')),
    ('europe_east', _('Europe de l\'Est')),
    ('europe_west', _('Europe de l\'Ouest')),
    ('north_america', _('Amérique du Nord')),
    ('oceania', _('Océanie')),
    ('middle_east', _('Moyen-Orient')),
]

# Plans d'abonnement
SUBSCRIPTION_PLAN_CHOICES = [
    ('essentials', _('Dojo Essentials')),
    ('masters', _('Master\'s Circle')),
    ('champion', _('Grand Champion Suite')),
    ('trial', _('Essai Gratuit')),
]

# Fournisseurs de paiement
PAYMENT_PROVIDER_CHOICES = [
    ('stripe', 'Stripe'),
    ('stripe_connect', 'Stripe Connect'),
    ('paystack', 'Paystack'),
    ('mercado_pago', 'Mercado Pago'),
    ('alipay', 'Alipay'),
    ('paytm', 'Paytm'),
    ('custom', 'Custom Provider'),
]

# Matrice de prix par continent et par plan
PRICING_MATRIX = {
    'africa': {'essentials': 2.99, 'masters': 5.99, 'champion': 9.99},
    'asia_se': {'essentials': 4.99, 'masters': 9.99, 'champion': 14.99},
    'asia_other': {'essentials': 6.99, 'masters': 12.99, 'champion': 19.99},
    'south_america': {'essentials': 5.99, 'masters': 11.99, 'champion': 17.99},
    'central_america': {'essentials': 4.99, 'masters': 9.99, 'champion': 14.99},
    'europe_east': {'essentials': 6.99, 'masters': 12.99, 'champion': 19.99},
    'europe_west': {'essentials': 9.99, 'masters': 19.99, 'champion': 29.99},
    'north_america': {'essentials': 9.99, 'masters': 19.99, 'champion': 29.99},
    'oceania': {'essentials': 9.99, 'masters': 19.99, 'champion': 29.99},
    'middle_east': {'essentials': 7.99, 'masters': 15.99, 'champion': 23.99},
}

# Matrice des fonctionnalités par plan
FEATURES_MATRIX = {
    'essentials': {
        'max_members': 100,
        'max_disciplines': 2,
        'competitions': False,
        'advanced_reporting': False,
        'api_access': False,
        'mobile_app': False,
    },
    'masters': {
        'max_members': 300,
        'max_disciplines': 5,
        'competitions': True,
        'advanced_reporting': True,
        'api_access': False,
        'mobile_app': False,
    },
    'champion': {
        'max_members': None,  # Illimité
        'max_disciplines': None,  # Illimité
        'competitions': True,
        'advanced_reporting': True,
        'api_access': True,
        'mobile_app': True,
    },
}
