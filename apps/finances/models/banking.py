# -*- coding: utf-8 -*-
"""
Modèles pour l'import bancaire et la réconciliation.
Ces modèles gèrent l'importation des relevés bancaires et le rapprochement
avec les transactions existantes du système.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid


class BankImportBatch(models.Model):
    """
    Lot d'import pour traçabilité des imports de relevés bancaires.
    Chaque import de fichier crée un lot qui regroupe toutes les transactions.
    """
    STATUS_CHOICES = [
        ('pending', _('En cours')),
        ('processing', _('Traitement en cours')),
        ('completed', _('Terminé')),
        ('completed_with_errors', _('Terminé avec erreurs')),
        ('failed', _('Échoué')),
    ]

    FILE_FORMAT_CHOICES = [
        ('csv', 'CSV'),
        ('xlsx', 'Excel (XLSX)'),
        ('xls', 'Excel (XLS)'),
        ('ofx', 'OFX'),
        ('qif', 'QIF'),
    ]

    BANK_FORMAT_CHOICES = [
        # Europe - Belgique
        ('BNP_FORTIS_BE', 'BNP Paribas Fortis (Belgique)'),
        ('ING_BE', 'ING (Belgique)'),
        ('KBC_BE', 'KBC (Belgique)'),
        ('BELFIUS_BE', 'Belfius (Belgique)'),
        # Europe - France
        ('SOCIETE_GENERALE_FR', 'Société Générale (France)'),
        ('CREDIT_AGRICOLE_FR', 'Crédit Agricole (France)'),
        ('BNP_FR', 'BNP Paribas (France)'),
        ('BOURSORAMA_FR', 'Boursorama (France)'),
        # Europe - Autres
        ('DEUTSCHE_BANK_DE', 'Deutsche Bank (Allemagne)'),
        ('SPARKASSE_DE', 'Sparkasse (Allemagne)'),
        # Afrique
        ('ORANGE_MONEY_CI', 'Orange Money (Côte d\'Ivoire)'),
        ('WAVE_SN', 'Wave (Sénégal)'),
        ('MPESA_KE', 'M-Pesa (Kenya)'),
        # Générique
        ('GENERIC', 'Format générique'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Compte bancaire cible
    financial_account = models.ForeignKey(
        'finances.FinancialAccount',
        on_delete=models.CASCADE,
        related_name='import_batches',
        verbose_name=_('Compte financier')
    )

    # Utilisateur qui a effectué l'import
    imported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='bank_imports',
        verbose_name=_('Importé par')
    )

    # Informations sur le fichier
    file_name = models.CharField(max_length=255, verbose_name=_('Nom du fichier'))
    file_format = models.CharField(
        max_length=20,
        choices=FILE_FORMAT_CHOICES,
        default='csv',
        verbose_name=_('Format du fichier')
    )
    bank_format = models.CharField(
        max_length=50,
        choices=BANK_FORMAT_CHOICES,
        default='GENERIC',
        verbose_name=_('Format bancaire')
    )
    file = models.FileField(
        upload_to='finances/bank_imports/%Y/%m/',
        null=True,
        blank=True,
        verbose_name=_('Fichier original')
    )

    # Statistiques d'import
    total_transactions = models.IntegerField(default=0, verbose_name=_('Total transactions'))
    imported_count = models.IntegerField(default=0, verbose_name=_('Importées'))
    duplicate_count = models.IntegerField(default=0, verbose_name=_('Doublons'))
    error_count = models.IntegerField(default=0, verbose_name=_('Erreurs'))

    # Statistiques financières
    total_income = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Total revenus')
    )
    total_expense = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Total dépenses')
    )

    # Période couverte
    date_start = models.DateField(null=True, blank=True, verbose_name=_('Date début'))
    date_end = models.DateField(null=True, blank=True, verbose_name=_('Date fin'))

    # Statut et erreurs
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_('Statut')
    )
    error_log = models.TextField(blank=True, verbose_name=_('Journal des erreurs'))

    # Dates
    import_date = models.DateTimeField(auto_now_add=True, verbose_name=_('Date d\'import'))
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Terminé le'))

    class Meta:
        app_label = 'finances'
        verbose_name = _('Lot d\'import bancaire')
        verbose_name_plural = _('Lots d\'import bancaires')
        ordering = ['-import_date']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['import_date']),
        ]

    def __str__(self):
        return f"{self.file_name} - {self.import_date.strftime('%d/%m/%Y %H:%M')}"

    def update_statistics(self):
        """Met à jour les statistiques basées sur les transactions du lot."""
        transactions = self.transactions.all()
        self.total_transactions = transactions.count()
        self.imported_count = transactions.filter(
            reconciliation_status__in=['pending', 'matched', 'partial']
        ).count()

        # Calcul des totaux
        income = transactions.filter(transaction_type='INCOME').aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
        expense = transactions.filter(transaction_type='EXPENSE').aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')

        self.total_income = income
        self.total_expense = abs(expense)

        # Dates couvertes
        dates = transactions.aggregate(
            min_date=models.Min('transaction_date'),
            max_date=models.Max('transaction_date')
        )
        self.date_start = dates['min_date']
        self.date_end = dates['max_date']

        self.save()


class BankTransaction(models.Model):
    """
    Transaction bancaire importée depuis un relevé.
    Ces transactions sont ensuite réconciliées avec les transactions système.
    """
    TRANSACTION_TYPE_CHOICES = [
        ('INCOME', _('Revenu')),
        ('EXPENSE', _('Dépense')),
    ]

    RECONCILIATION_STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('matched', _('Rapproché')),
        ('partial', _('Partiellement rapproché')),
        ('unmatched', _('Non rapproché')),
        ('ignored', _('Ignoré')),
        ('duplicate', _('Doublon')),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('virement_instantane', _('Virement instantané')),
        ('virement', _('Virement')),
        ('paiement_carte', _('Paiement par carte')),
        ('paiement_carte_credit', _('Paiement par carte de crédit')),
        ('prelevement', _('Prélèvement')),
        ('cheque', _('Chèque')),
        ('especes', _('Espèces')),
        ('mobile_money', _('Mobile Money')),
        ('autre', _('Autre')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Lot d'import
    import_batch = models.ForeignKey(
        BankImportBatch,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name=_('Lot d\'import')
    )

    # Référence externe (numéro de séquence bancaire)
    external_reference = models.CharField(
        max_length=100,
        verbose_name=_('Référence externe')
    )

    # Dates
    transaction_date = models.DateField(verbose_name=_('Date d\'exécution'))
    value_date = models.DateField(verbose_name=_('Date valeur'))

    # Montant
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_('Montant')
    )
    currency = models.CharField(max_length=3, default='EUR', verbose_name=_('Devise'))

    # Type et méthode
    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPE_CHOICES,
        verbose_name=_('Type')
    )
    payment_method = models.CharField(
        max_length=50,
        choices=PAYMENT_METHOD_CHOICES,
        default='autre',
        verbose_name=_('Méthode de paiement')
    )
    payment_method_raw = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Méthode de paiement (brut)')
    )

    # Contrepartie
    counterparty_iban = models.CharField(
        max_length=34,
        blank=True,
        verbose_name=_('IBAN contrepartie')
    )
    counterparty_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Nom contrepartie')
    )

    # Communication et détails
    communication = models.TextField(blank=True, verbose_name=_('Communication'))
    raw_details = models.TextField(blank=True, verbose_name=_('Détails bruts'))

    # Statut bancaire
    bank_status = models.CharField(
        max_length=50,
        default='Accepté',
        verbose_name=_('Statut bancaire')
    )

    # Réconciliation
    reconciliation_status = models.CharField(
        max_length=20,
        choices=RECONCILIATION_STATUS_CHOICES,
        default='pending',
        verbose_name=_('Statut réconciliation')
    )
    reconciliation_score = models.IntegerField(
        default=0,
        verbose_name=_('Score de confiance (%)')
    )
    reconciliation_notes = models.TextField(
        blank=True,
        verbose_name=_('Notes de réconciliation')
    )
    reconciled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Réconcilié le')
    )
    reconciled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reconciled_bank_transactions',
        verbose_name=_('Réconcilié par')
    )

    # Liens vers les entités système
    matched_transaction = models.ForeignKey(
        'finances.Transaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bank_transactions',
        verbose_name=_('Transaction système')
    )
    matched_practitioner = models.ForeignKey(
        'competitions.Practitioner',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bank_transactions',
        verbose_name=_('Pratiquant identifié')
    )
    matched_category = models.ForeignKey(
        'finances.TransactionCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Catégorie')
    )

    # Notes utilisateur
    notes = models.TextField(blank=True, verbose_name=_('Notes'))

    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Créé le'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Mis à jour le'))

    class Meta:
        app_label = 'finances'
        verbose_name = _('Transaction bancaire')
        verbose_name_plural = _('Transactions bancaires')
        ordering = ['-transaction_date', '-created_at']
        indexes = [
            models.Index(fields=['reconciliation_status']),
            models.Index(fields=['transaction_date']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['counterparty_name']),
            models.Index(fields=['external_reference']),
        ]
        unique_together = [
            ['import_batch', 'external_reference', 'transaction_date', 'amount']
        ]

    def __str__(self):
        sign = '+' if self.transaction_type == 'INCOME' else '-'
        return f"{self.transaction_date} | {sign}{abs(self.amount)} {self.currency} | {self.counterparty_name[:30]}"

    @property
    def is_income(self):
        return self.transaction_type == 'INCOME'

    @property
    def is_expense(self):
        return self.transaction_type == 'EXPENSE'

    @property
    def is_reconciled(self):
        return self.reconciliation_status in ['matched', 'partial']

    @property
    def display_amount(self):
        """Retourne le montant avec signe pour affichage."""
        if self.transaction_type == 'INCOME':
            return f"+{self.amount}"
        return f"-{abs(self.amount)}"

    def mark_as_matched(self, transaction=None, practitioner=None, user=None, score=100):
        """Marque la transaction comme rapprochée."""
        self.reconciliation_status = 'matched'
        self.reconciliation_score = score
        self.reconciled_at = timezone.now()
        if transaction:
            self.matched_transaction = transaction
        if practitioner:
            self.matched_practitioner = practitioner
        if user:
            self.reconciled_by = user
        self.save()

    def mark_as_ignored(self, user=None, reason=''):
        """Marque la transaction comme ignorée."""
        self.reconciliation_status = 'ignored'
        self.reconciliation_notes = reason
        self.reconciled_at = timezone.now()
        if user:
            self.reconciled_by = user
        self.save()


class ReconciliationRule(models.Model):
    """
    Règles de réconciliation automatique.
    Permettent de définir des critères pour matcher automatiquement
    les transactions bancaires avec les pratiquants ou catégories.
    """
    MATCH_TYPE_CHOICES = [
        ('contains', _('Contient')),
        ('exact', _('Correspondance exacte')),
        ('starts_with', _('Commence par')),
        ('ends_with', _('Finit par')),
        ('regex', _('Expression régulière')),
        ('amount_range', _('Plage de montant')),
        ('amount_exact', _('Montant exact')),
    ]

    MATCH_FIELD_CHOICES = [
        ('communication', _('Communication')),
        ('counterparty_name', _('Nom contrepartie')),
        ('counterparty_iban', _('IBAN contrepartie')),
        ('amount', _('Montant')),
        ('raw_details', _('Détails bruts')),
    ]

    ACTION_TYPE_CHOICES = [
        ('assign_category', _('Assigner catégorie')),
        ('assign_practitioner', _('Assigner pratiquant')),
        ('ignore', _('Ignorer')),
        ('flag_review', _('Marquer pour révision')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=100, verbose_name=_('Nom de la règle'))
    description = models.TextField(blank=True, verbose_name=_('Description'))

    # Organisation (pour limiter la portée de la règle)
    organization_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('ID Organisation')
    )

    # Critères de matching
    match_field = models.CharField(
        max_length=50,
        choices=MATCH_FIELD_CHOICES,
        verbose_name=_('Champ à matcher')
    )
    match_type = models.CharField(
        max_length=20,
        choices=MATCH_TYPE_CHOICES,
        verbose_name=_('Type de match')
    )
    match_value = models.CharField(
        max_length=500,
        verbose_name=_('Valeur à chercher')
    )

    # Critères supplémentaires optionnels
    min_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Montant minimum')
    )
    max_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Montant maximum')
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=BankTransaction.TRANSACTION_TYPE_CHOICES,
        blank=True,
        verbose_name=_('Type de transaction')
    )

    # Action à effectuer
    action_type = models.CharField(
        max_length=30,
        choices=ACTION_TYPE_CHOICES,
        default='assign_category',
        verbose_name=_('Action')
    )

    # Entités à assigner
    assign_category = models.ForeignKey(
        'finances.TransactionCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Catégorie à assigner')
    )
    assign_practitioner = models.ForeignKey(
        'competitions.Practitioner',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Pratiquant à assigner')
    )

    # Priorité (les règles avec priorité plus élevée sont appliquées en premier)
    priority = models.IntegerField(default=0, verbose_name=_('Priorité'))

    # État
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))

    # Statistiques
    times_applied = models.IntegerField(default=0, verbose_name=_('Fois appliquée'))
    last_applied_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Dernière application')
    )

    # Métadonnées
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_reconciliation_rules',
        verbose_name=_('Créé par')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Créé le'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Mis à jour le'))

    class Meta:
        app_label = 'finances'
        verbose_name = _('Règle de réconciliation')
        verbose_name_plural = _('Règles de réconciliation')
        ordering = ['-priority', 'name']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['priority']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_match_type_display()})"

    def increment_applied(self):
        """Incrémente le compteur d'application."""
        self.times_applied += 1
        self.last_applied_at = timezone.now()
        self.save(update_fields=['times_applied', 'last_applied_at'])


class PractitionerBankInfo(models.Model):
    """
    Informations bancaires associées à un pratiquant.
    Permet de lier un IBAN à un pratiquant pour le rapprochement automatique.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    practitioner = models.ForeignKey(
        'competitions.Practitioner',
        on_delete=models.CASCADE,
        related_name='bank_infos',
        verbose_name=_('Pratiquant')
    )

    # Informations bancaires
    iban = models.CharField(max_length=34, verbose_name=_('IBAN'))
    bic = models.CharField(max_length=11, blank=True, verbose_name=_('BIC/SWIFT'))
    account_holder_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Titulaire du compte')
    )

    # Variantes de nom (pour le matching)
    name_variants = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Variantes de nom'),
        help_text=_('Liste des noms alternatifs pour le matching')
    )

    # État
    is_primary = models.BooleanField(default=True, verbose_name=_('Compte principal'))
    is_verified = models.BooleanField(default=False, verbose_name=_('Vérifié'))

    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Créé le'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Mis à jour le'))

    class Meta:
        app_label = 'finances'
        verbose_name = _('Info bancaire pratiquant')
        verbose_name_plural = _('Infos bancaires pratiquants')
        unique_together = ['practitioner', 'iban']
        indexes = [
            models.Index(fields=['iban']),
        ]

    def __str__(self):
        return f"{self.practitioner.full_name} - {self.iban}"

    def save(self, *args, **kwargs):
        # Si c'est le compte principal, désactiver ce flag pour les autres
        if self.is_primary:
            PractitionerBankInfo.objects.filter(
                practitioner=self.practitioner,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)
