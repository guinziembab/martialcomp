# competitions/permissions/definitions.py
"""
Définition centralisée de toutes les permissions MartialComp.
Ce module définit les constantes de permissions et les configurations par défaut.
"""

from django.utils.translation import gettext_lazy as _


class Permissions:
    """
    Définition centralisée de toutes les permissions MartialComp.
    Format: CATEGORIE_ACTION

    Usage:
        from apps.competitions.permissions import Permissions

        if membership.has_permission(Permissions.FINANCE_VIEW):
            # Afficher les finances
            pass
    """

    # ===== MEMBRES =====
    MEMBERS_VIEW = 'members.view'
    MEMBERS_CREATE = 'members.create'
    MEMBERS_EDIT = 'members.edit'
    MEMBERS_DELETE = 'members.delete'
    MEMBERS_EXPORT = 'members.export'
    MEMBERS_GRADES = 'members.grades'  # Modifier les grades
    MEMBERS_IMPORT = 'members.import'

    # ===== COMPÉTITIONS =====
    COMPETITIONS_VIEW = 'competitions.view'
    COMPETITIONS_CREATE = 'competitions.create'
    COMPETITIONS_EDIT = 'competitions.edit'
    COMPETITIONS_DELETE = 'competitions.delete'
    COMPETITIONS_MANAGE = 'competitions.manage'  # Gestion complète (scores, etc.)
    COMPETITIONS_REGISTER = 'competitions.register'  # Inscrire des membres

    # ===== FINANCES =====
    FINANCE_VIEW = 'finance.view'
    FINANCE_CREATE = 'finance.create'
    FINANCE_EDIT = 'finance.edit'
    FINANCE_APPROVE = 'finance.approve'
    FINANCE_EXPORT = 'finance.export'
    FINANCE_REPORTS = 'finance.reports'
    FINANCE_DELETE = 'finance.delete'

    # ===== ORGANISATION =====
    ORGANIZATION_VIEW = 'organization.view'
    ORGANIZATION_EDIT = 'organization.edit'
    ORGANIZATION_SETTINGS = 'organization.settings'
    ORGANIZATION_DELETE = 'organization.delete'

    # ===== RÔLES =====
    ROLES_VIEW = 'roles.view'
    ROLES_ASSIGN = 'roles.assign'
    ROLES_CREATE = 'roles.create'  # Créer des rôles custom
    ROLES_DELETE = 'roles.delete'

    # ===== DOCUMENTS =====
    DOCUMENTS_VIEW = 'documents.view'
    DOCUMENTS_CREATE = 'documents.create'
    DOCUMENTS_EDIT = 'documents.edit'
    DOCUMENTS_DELETE = 'documents.delete'

    # ===== COMMUNICATION =====
    COMMUNICATION_VIEW = 'communication.view'
    COMMUNICATION_SEND = 'communication.send'
    COMMUNICATION_MANAGE = 'communication.manage'

    # ===== ÉVÉNEMENTS =====
    EVENTS_VIEW = 'events.view'
    EVENTS_CREATE = 'events.create'
    EVENTS_EDIT = 'events.edit'
    EVENTS_MANAGE = 'events.manage'
    EVENTS_DELETE = 'events.delete'

    # ===== ENTRAÎNEMENT =====
    TRAINING_VIEW = 'training.view'
    TRAINING_CREATE = 'training.create'
    TRAINING_EDIT = 'training.edit'
    TRAINING_MANAGE = 'training.manage'
    TRAINING_DELETE = 'training.delete'

    # ===== BOUTIQUE =====
    SHOP_VIEW = 'shop.view'
    SHOP_MANAGE = 'shop.manage'
    SHOP_ORDERS = 'shop.orders'

    # ===== SITES/QR CODES =====
    SITES_VIEW = 'sites.view'
    SITES_MANAGE = 'sites.manage'

    # ===== RAPPORTS =====
    REPORTS_VIEW = 'reports.view'
    REPORTS_CREATE = 'reports.create'
    REPORTS_EXPORT = 'reports.export'


# Groupes de permissions pour faciliter l'assignation
PERMISSION_GROUPS = {
    'all': ['*'],

    'members_full': [
        Permissions.MEMBERS_VIEW,
        Permissions.MEMBERS_CREATE,
        Permissions.MEMBERS_EDIT,
        Permissions.MEMBERS_DELETE,
        Permissions.MEMBERS_EXPORT,
        Permissions.MEMBERS_GRADES,
        Permissions.MEMBERS_IMPORT,
    ],

    'members_read': [
        Permissions.MEMBERS_VIEW,
    ],

    'competitions_full': [
        Permissions.COMPETITIONS_VIEW,
        Permissions.COMPETITIONS_CREATE,
        Permissions.COMPETITIONS_EDIT,
        Permissions.COMPETITIONS_DELETE,
        Permissions.COMPETITIONS_MANAGE,
        Permissions.COMPETITIONS_REGISTER,
    ],

    'competitions_read': [
        Permissions.COMPETITIONS_VIEW,
    ],

    'finance_full': [
        Permissions.FINANCE_VIEW,
        Permissions.FINANCE_CREATE,
        Permissions.FINANCE_EDIT,
        Permissions.FINANCE_APPROVE,
        Permissions.FINANCE_EXPORT,
        Permissions.FINANCE_REPORTS,
        Permissions.FINANCE_DELETE,
    ],

    'finance_read': [
        Permissions.FINANCE_VIEW,
        Permissions.FINANCE_EXPORT,
        Permissions.FINANCE_REPORTS,
    ],

    'training_full': [
        Permissions.TRAINING_VIEW,
        Permissions.TRAINING_CREATE,
        Permissions.TRAINING_EDIT,
        Permissions.TRAINING_MANAGE,
        Permissions.TRAINING_DELETE,
    ],
}


# Configuration des permissions par rôle par défaut
DEFAULT_ROLE_PERMISSIONS = {
    'owner': {
        'permissions': ['*'],  # Toutes les permissions
        'can_transfer_ownership': True,
        'description': _("Tous les droits, peut transférer la propriété"),
    },

    'admin': {
        'permissions': [
            # Membres
            Permissions.MEMBERS_VIEW,
            Permissions.MEMBERS_CREATE,
            Permissions.MEMBERS_EDIT,
            Permissions.MEMBERS_DELETE,
            Permissions.MEMBERS_EXPORT,
            Permissions.MEMBERS_GRADES,
            Permissions.MEMBERS_IMPORT,
            # Compétitions
            Permissions.COMPETITIONS_VIEW,
            Permissions.COMPETITIONS_CREATE,
            Permissions.COMPETITIONS_EDIT,
            Permissions.COMPETITIONS_DELETE,
            Permissions.COMPETITIONS_MANAGE,
            Permissions.COMPETITIONS_REGISTER,
            # Finances
            Permissions.FINANCE_VIEW,
            Permissions.FINANCE_CREATE,
            Permissions.FINANCE_EDIT,
            Permissions.FINANCE_APPROVE,
            Permissions.FINANCE_EXPORT,
            Permissions.FINANCE_REPORTS,
            # Organisation
            Permissions.ORGANIZATION_VIEW,
            Permissions.ORGANIZATION_EDIT,
            Permissions.ORGANIZATION_SETTINGS,
            # Rôles
            Permissions.ROLES_VIEW,
            Permissions.ROLES_ASSIGN,
            # Documents
            Permissions.DOCUMENTS_VIEW,
            Permissions.DOCUMENTS_CREATE,
            Permissions.DOCUMENTS_EDIT,
            Permissions.DOCUMENTS_DELETE,
            # Communication
            Permissions.COMMUNICATION_VIEW,
            Permissions.COMMUNICATION_SEND,
            Permissions.COMMUNICATION_MANAGE,
            # Événements
            Permissions.EVENTS_VIEW,
            Permissions.EVENTS_CREATE,
            Permissions.EVENTS_EDIT,
            Permissions.EVENTS_MANAGE,
            # Entraînement
            Permissions.TRAINING_VIEW,
            Permissions.TRAINING_CREATE,
            Permissions.TRAINING_EDIT,
            Permissions.TRAINING_MANAGE,
            # Boutique
            Permissions.SHOP_VIEW,
            Permissions.SHOP_MANAGE,
            Permissions.SHOP_ORDERS,
            # Sites
            Permissions.SITES_VIEW,
            Permissions.SITES_MANAGE,
            # Rapports
            Permissions.REPORTS_VIEW,
            Permissions.REPORTS_CREATE,
            Permissions.REPORTS_EXPORT,
        ],
        'can_transfer_ownership': False,
        'description': _("Gestion complète sauf transfert propriété"),
    },

    'manager': {
        'permissions': [
            Permissions.MEMBERS_VIEW,
            Permissions.MEMBERS_CREATE,
            Permissions.MEMBERS_EDIT,
            Permissions.MEMBERS_EXPORT,
            Permissions.COMPETITIONS_VIEW,
            Permissions.COMPETITIONS_CREATE,
            Permissions.COMPETITIONS_EDIT,
            Permissions.COMPETITIONS_MANAGE,
            Permissions.COMPETITIONS_REGISTER,
            Permissions.DOCUMENTS_VIEW,
            Permissions.DOCUMENTS_CREATE,
            Permissions.COMMUNICATION_VIEW,
            Permissions.COMMUNICATION_SEND,
            Permissions.EVENTS_VIEW,
            Permissions.EVENTS_CREATE,
            Permissions.EVENTS_EDIT,
            Permissions.REPORTS_VIEW,
        ],
        'description': _("Gestion membres et compétitions"),
    },

    'treasurer': {
        'permissions': [
            Permissions.MEMBERS_VIEW,
            Permissions.FINANCE_VIEW,
            Permissions.FINANCE_CREATE,
            Permissions.FINANCE_EDIT,
            Permissions.FINANCE_APPROVE,
            Permissions.FINANCE_EXPORT,
            Permissions.FINANCE_REPORTS,
            Permissions.REPORTS_VIEW,
            Permissions.REPORTS_EXPORT,
        ],
        'description': _("Gestion finances et transactions"),
    },

    'accountant': {
        'permissions': [
            Permissions.MEMBERS_VIEW,
            Permissions.FINANCE_VIEW,
            Permissions.FINANCE_EXPORT,
            Permissions.FINANCE_REPORTS,
            Permissions.REPORTS_VIEW,
            Permissions.REPORTS_EXPORT,
        ],
        'description': _("Consultation et export finances"),
    },

    'secretary': {
        'permissions': [
            Permissions.MEMBERS_VIEW,
            Permissions.MEMBERS_CREATE,
            Permissions.MEMBERS_EDIT,
            Permissions.MEMBERS_EXPORT,
            Permissions.DOCUMENTS_VIEW,
            Permissions.DOCUMENTS_CREATE,
            Permissions.DOCUMENTS_EDIT,
            Permissions.COMMUNICATION_VIEW,
            Permissions.COMMUNICATION_SEND,
            Permissions.COMMUNICATION_MANAGE,
            Permissions.EVENTS_VIEW,
            Permissions.EVENTS_CREATE,
        ],
        'description': _("Gestion administrative et communication"),
    },

    'coach': {
        'permissions': [
            Permissions.MEMBERS_VIEW,
            Permissions.MEMBERS_GRADES,
            Permissions.COMPETITIONS_VIEW,
            Permissions.COMPETITIONS_REGISTER,
            Permissions.TRAINING_VIEW,
            Permissions.TRAINING_CREATE,
            Permissions.TRAINING_EDIT,
            Permissions.TRAINING_MANAGE,
            Permissions.EVENTS_VIEW,
        ],
        'description': _("Gestion cours et pratiquants"),
    },

    'judge': {
        'permissions': [
            Permissions.MEMBERS_VIEW,
            Permissions.COMPETITIONS_VIEW,
            Permissions.COMPETITIONS_MANAGE,
        ],
        'description': _("Arbitrage compétitions"),
    },

    'member': {
        'permissions': [
            Permissions.MEMBERS_VIEW,  # Lecture seule (liste membres)
            Permissions.COMPETITIONS_VIEW,
            Permissions.EVENTS_VIEW,
            Permissions.TRAINING_VIEW,
            Permissions.SHOP_VIEW,
        ],
        'description': _("Accès basique au club"),
    },
}


# Labels lisibles pour les permissions (pour l'interface admin)
PERMISSION_LABELS = {
    Permissions.MEMBERS_VIEW: _("Voir les membres"),
    Permissions.MEMBERS_CREATE: _("Créer des membres"),
    Permissions.MEMBERS_EDIT: _("Modifier les membres"),
    Permissions.MEMBERS_DELETE: _("Supprimer des membres"),
    Permissions.MEMBERS_EXPORT: _("Exporter les membres"),
    Permissions.MEMBERS_GRADES: _("Gérer les grades"),
    Permissions.MEMBERS_IMPORT: _("Importer des membres"),

    Permissions.COMPETITIONS_VIEW: _("Voir les compétitions"),
    Permissions.COMPETITIONS_CREATE: _("Créer des compétitions"),
    Permissions.COMPETITIONS_EDIT: _("Modifier les compétitions"),
    Permissions.COMPETITIONS_DELETE: _("Supprimer des compétitions"),
    Permissions.COMPETITIONS_MANAGE: _("Gérer les compétitions"),
    Permissions.COMPETITIONS_REGISTER: _("Inscrire aux compétitions"),

    Permissions.FINANCE_VIEW: _("Voir les finances"),
    Permissions.FINANCE_CREATE: _("Créer des transactions"),
    Permissions.FINANCE_EDIT: _("Modifier les transactions"),
    Permissions.FINANCE_APPROVE: _("Approuver les transactions"),
    Permissions.FINANCE_EXPORT: _("Exporter les finances"),
    Permissions.FINANCE_REPORTS: _("Voir les rapports financiers"),
    Permissions.FINANCE_DELETE: _("Supprimer des transactions"),

    Permissions.ORGANIZATION_VIEW: _("Voir l'organisation"),
    Permissions.ORGANIZATION_EDIT: _("Modifier l'organisation"),
    Permissions.ORGANIZATION_SETTINGS: _("Paramètres de l'organisation"),

    Permissions.ROLES_VIEW: _("Voir les rôles"),
    Permissions.ROLES_ASSIGN: _("Assigner des rôles"),
    Permissions.ROLES_CREATE: _("Créer des rôles"),

    Permissions.DOCUMENTS_VIEW: _("Voir les documents"),
    Permissions.DOCUMENTS_CREATE: _("Créer des documents"),
    Permissions.DOCUMENTS_EDIT: _("Modifier les documents"),
    Permissions.DOCUMENTS_DELETE: _("Supprimer des documents"),

    Permissions.COMMUNICATION_VIEW: _("Voir les communications"),
    Permissions.COMMUNICATION_SEND: _("Envoyer des communications"),
    Permissions.COMMUNICATION_MANAGE: _("Gérer les communications"),

    Permissions.EVENTS_VIEW: _("Voir les événements"),
    Permissions.EVENTS_CREATE: _("Créer des événements"),
    Permissions.EVENTS_EDIT: _("Modifier les événements"),
    Permissions.EVENTS_MANAGE: _("Gérer les événements"),

    Permissions.TRAINING_VIEW: _("Voir les entraînements"),
    Permissions.TRAINING_CREATE: _("Créer des entraînements"),
    Permissions.TRAINING_EDIT: _("Modifier les entraînements"),
    Permissions.TRAINING_MANAGE: _("Gérer les entraînements"),

    Permissions.SHOP_VIEW: _("Voir la boutique"),
    Permissions.SHOP_MANAGE: _("Gérer la boutique"),
    Permissions.SHOP_ORDERS: _("Gérer les commandes"),

    Permissions.SITES_VIEW: _("Voir les sites"),
    Permissions.SITES_MANAGE: _("Gérer les sites"),

    Permissions.REPORTS_VIEW: _("Voir les rapports"),
    Permissions.REPORTS_CREATE: _("Créer des rapports"),
    Permissions.REPORTS_EXPORT: _("Exporter les rapports"),
}


def get_permission_label(permission):
    """Retourne le label lisible d'une permission."""
    return PERMISSION_LABELS.get(permission, permission)


def get_permissions_by_category():
    """Retourne les permissions groupées par catégorie."""
    categories = {
        'members': {
            'label': _("Membres"),
            'icon': 'fa-users',
            'permissions': []
        },
        'competitions': {
            'label': _("Compétitions"),
            'icon': 'fa-trophy',
            'permissions': []
        },
        'finance': {
            'label': _("Finances"),
            'icon': 'fa-coins',
            'permissions': []
        },
        'organization': {
            'label': _("Organisation"),
            'icon': 'fa-building',
            'permissions': []
        },
        'roles': {
            'label': _("Rôles"),
            'icon': 'fa-user-tag',
            'permissions': []
        },
        'documents': {
            'label': _("Documents"),
            'icon': 'fa-file-alt',
            'permissions': []
        },
        'communication': {
            'label': _("Communication"),
            'icon': 'fa-envelope',
            'permissions': []
        },
        'events': {
            'label': _("Événements"),
            'icon': 'fa-calendar',
            'permissions': []
        },
        'training': {
            'label': _("Entraînement"),
            'icon': 'fa-dumbbell',
            'permissions': []
        },
        'shop': {
            'label': _("Boutique"),
            'icon': 'fa-shopping-cart',
            'permissions': []
        },
        'sites': {
            'label': _("Sites"),
            'icon': 'fa-qrcode',
            'permissions': []
        },
        'reports': {
            'label': _("Rapports"),
            'icon': 'fa-chart-bar',
            'permissions': []
        },
    }

    for perm, label in PERMISSION_LABELS.items():
        category = perm.split('.')[0]
        if category in categories:
            categories[category]['permissions'].append({
                'code': perm,
                'label': label
            })

    return categories
