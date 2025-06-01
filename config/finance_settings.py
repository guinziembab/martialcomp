"""
Paramètres spécifiques au module finances.
Ce fichier est importé dans le settings.py principal.
"""

# Montant maximum pour les transactions sans validation multiple
MAX_TRANSACTION_AMOUNT_WITHOUT_VALIDATION = 5000

# Nombre de validateurs requis pour les transactions importantes
TRANSACTION_VALIDATORS_REQUIRED = {
    'default': 1,  # Par défaut
    'high_amount': 2,  # Pour les montants élevés
    'very_high_amount': 3,  # Pour les montants très élevés
}

# Seuils pour définir l'importance des transactions
TRANSACTION_THRESHOLDS = {
    'high_amount': 10000,  # Seuil pour les transactions élevées
    'very_high_amount': 50000,  # Seuil pour les transactions très élevées
}

# Configuration pour le verrouillage des transactions
TRANSACTION_LOCK_SETTINGS = {
    'lock_after_days': 30,  # Verrouiller les transactions après 30 jours
    'hard_lock_after_days': 90,  # Verrouillage définitif après 90 jours
}

# Configuration pour la détection de fraude
FRAUD_DETECTION_SETTINGS = {
    'enable': True,  # Activer la détection de fraude
    'flagged_transaction_types': ['expense'],  # Types de transactions à surveiller
    'suspicious_amount_threshold': 10000,  # Seuil pour les montants suspects
    'notify_admins': True,  # Notifier les administrateurs en cas de suspicion
}

# Paramètres pour les factures
INVOICE_SETTINGS = {
    'auto_number_format': 'INV-{year}{month:02d}-{seq:04d}',  # Format pour la numérotation automatique
    'due_date_days': 30,  # Délai de paiement par défaut en jours
    'auto_send_reminders': True,  # Envoyer des rappels automatiques
    'reminder_intervals': [7, 14, 21],  # Jours de rappel après échéance
    'apply_late_fees': False,  # Appliquer des frais de retard
    'late_fee_percentage': 5,  # Pourcentage des frais de retard
}

# Paramètres pour les permissions
PERMISSION_SETTINGS = {
    'default_groups': {
        'federation_admin': ['Finance Admin'],  # Groupes par défaut pour les administrateurs de fédération
        'club_manager': ['Transaction Manager', 'Invoice Manager'],  # Groupes par défaut pour les managers de club
        'finance_manager': ['Finance Manager'],  # Groupes par défaut pour les responsables financiers
    },
    'minimum_validation_level': {
        'validate_transaction': 'finance_manager',  # Niveau minimum pour valider une transaction
        'approve_all_transactions': 'finance_admin',  # Niveau minimum pour approuver toutes les transactions
        'manage_payment_methods': 'finance_admin',  # Niveau minimum pour gérer les méthodes de paiement
    }
}

# Paramètres pour les paiements
PAYMENT_SETTINGS = {
    'default_currency': 'EUR',  # Devise par défaut
    'available_payment_methods': ['credit_card', 'bank_transfer', 'cash', 'check'],  # Méthodes de paiement disponibles
    'payment_method_fees': {
        'credit_card': {
            'fixed': 0.30,  # Frais fixe en euros
            'percentage': 2.9,  # Pourcentage des frais
        },
        'bank_transfer': {
            'fixed': 0,
            'percentage': 0,
        },
        'cash': {
            'fixed': 0,
            'percentage': 0,
        },
        'check': {
            'fixed': 0,
            'percentage': 0,
        },
    },
}

# Paramètres pour la journalisation financière
FINANCIAL_LOGGING = {
    'log_all_transactions': True,  # Journaliser toutes les transactions
    'log_sensitive_fields': False,  # Journaliser les champs sensibles
    'audit_retention_days': 365 * 2,  # Conservation des journaux d'audit (2 ans)
}

# Paramètres pour les exports financiers
FINANCIAL_EXPORT = {
    'allowed_formats': ['csv', 'xlsx', 'pdf'],  # Formats d'export autorisés
    'default_format': 'xlsx',  # Format par défaut
    'include_sensitive_data': False,  # Inclure les données sensibles dans les exports
}

# Intégration avec les autres modules
MODULE_INTEGRATION = {
    'competition_registration': True,  # Intégration avec l'inscription aux compétitions
    'membership_fees': True,  # Intégration avec les cotisations
    'store': False,  # Intégration avec une boutique en ligne (à venir)
}

# Paramètres pour les rapports financiers
REPORT_SETTINGS = {
    'default_report_period': 'month',  # Période par défaut pour les rapports (month, quarter, year)
    'available_reports': ['income_expense', 'balance_sheet', 'cash_flow', 'invoice_summary'],  # Rapports disponibles
}

# Limites des transactions par utilisateur/rôle
TRANSACTION_LIMITS = {
    'club_manager': {
        'daily_limit': 5000,  # Limite quotidienne
        'transaction_limit': 2000,  # Limite par transaction
    },
    'finance_manager': {
        'daily_limit': 15000,
        'transaction_limit': 5000,
    },
    'finance_admin': {
        'daily_limit': 50000,
        'transaction_limit': 20000,
    },
}