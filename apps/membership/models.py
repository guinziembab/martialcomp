# -*- coding: utf-8 -*-
"""
Modèles pour le système d'adhésion MartialComp v2.0
Système flexible d'adhésion adapté aux arts martiaux
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid
from dateutil.relativedelta import relativedelta

# Import des modèles existants
from apps.competitions.models import Organization, Practitioner, Discipline
from apps.core.isolation import OrganizationSecureManager


class MembershipPackage(models.Model):
    """
    Packages d'adhésion flexibles pour les arts martiaux
    """
    PACKAGE_TYPES = [
        ('monthly', _('Mensuel')),
        ('quarterly', _('Trimestriel')), 
        ('semi_annual', _('Semestriel')),
        ('annual', _('Annuel')),
        ('custom', _('Personnalisé')),
    ]
    
    MEMBERSHIP_CATEGORIES = [
        ('student', _('Élève')),
        ('competitor', _('Compétiteur')),
        ('recreational', _('Loisir')),
        ('professional', _('Professionnel')),
        ('family', _('Famille')),
        ('senior', _('Senior')),
        ('youth', _('Jeune')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='membership_packages',
        verbose_name=_('Organisation')
    )
    
    # Informations de base
    name = models.CharField(max_length=200, verbose_name=_('Nom du package'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    package_type = models.CharField(
        max_length=20, 
        choices=PACKAGE_TYPES, 
        default='monthly',
        verbose_name=_('Type de package')
    )
    category = models.CharField(
        max_length=20,
        choices=MEMBERSHIP_CATEGORIES,
        default='student',
        verbose_name=_('Catégorie')
    )
    
    # Configuration tarifaire
    base_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Prix de base')
    )
    currency = models.CharField(max_length=3, default='EUR', verbose_name=_('Devise'))
    
    # Avantages et limitations
    disciplines = models.ManyToManyField(
        Discipline, 
        blank=True,
        verbose_name=_('Disciplines incluses'),
        help_text=_('Disciplines accessibles avec ce package')
    )
    max_sessions_per_week = models.PositiveIntegerField(
        null=True, 
        blank=True,
        verbose_name=_('Sessions max/semaine'),
        help_text=_('0 = illimité')
    )
    includes_competitions = models.BooleanField(
        default=False,
        verbose_name=_('Inclut les compétitions')
    )
    includes_seminars = models.BooleanField(
        default=False,
        verbose_name=_('Inclut les stages')
    )
    includes_equipment = models.BooleanField(
        default=False,
        verbose_name=_('Inclut l\'équipement')
    )
    
    # Gestion des renouvellements
    auto_renewal = models.BooleanField(
        default=True,
        verbose_name=_('Renouvellement automatique')
    )
    grace_period_days = models.PositiveIntegerField(
        default=7,
        verbose_name=_('Période de grâce (jours)')
    )
    
    # Configuration d'âge
    min_age = models.PositiveIntegerField(
        null=True, 
        blank=True,
        verbose_name=_('Âge minimum')
    )
    max_age = models.PositiveIntegerField(
        null=True, 
        blank=True,
        verbose_name=_('Âge maximum')
    )
    
    # Méta-données
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))
    is_featured = models.BooleanField(default=False, verbose_name=_('Mis en avant'))
    sort_order = models.PositiveIntegerField(default=0, verbose_name=_('Ordre d\'affichage'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Package d\'adhésion')
        verbose_name_plural = _('Packages d\'adhésion')
        ordering = ['sort_order', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_package_type_display()})"

    def get_duration_months(self):
        """Retourne la durée en mois selon le type de package"""
        durations = {
            'monthly': 1,
            'quarterly': 3,
            'semi_annual': 6,
            'annual': 12,
            'custom': 1  # Par défaut 1 mois pour custom
        }
        return durations.get(self.package_type, 1)

    def calculate_next_renewal_date(self, start_date=None):
        """Calcule la prochaine date de renouvellement"""
        if not start_date:
            start_date = timezone.now().date()
        
        months = self.get_duration_months()
        return start_date + relativedelta(months=months)

    # Manager sécurisé pour l'isolation par organisation
    objects = OrganizationSecureManager()


class MembershipSubscription(models.Model):
    """
    Souscription d'adhésion d'un pratiquant à un package
    """
    STATUS_CHOICES = [
        ('active', _('Actif')),
        ('expired', _('Expiré')),
        ('suspended', _('Suspendu')),
        ('cancelled', _('Annulé')),
        ('pending', _('En attente')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    practitioner = models.ForeignKey(
        Practitioner,
        on_delete=models.CASCADE,
        related_name='membership_subscriptions',
        verbose_name=_('Pratiquant')
    )
    package = models.ForeignKey(
        MembershipPackage,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name=_('Package')
    )
    
    # Dates importantes
    start_date = models.DateField(verbose_name=_('Date de début'))
    end_date = models.DateField(verbose_name=_('Date de fin'))
    renewal_date = models.DateField(
        null=True, 
        blank=True,
        verbose_name=_('Prochaine date de renouvellement')
    )
    
    # Statut et configuration
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_('Statut')
    )
    auto_renew = models.BooleanField(
        default=True,
        verbose_name=_('Renouvellement automatique')
    )
    
    # Prix et facturation
    price_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Prix payé')
    )
    currency = models.CharField(max_length=3, default='EUR')
    
    # Notes et personnalisations
    notes = models.TextField(blank=True, verbose_name=_('Notes'))
    custom_disciplines = models.ManyToManyField(
        Discipline,
        blank=True,
        verbose_name=_('Disciplines personnalisées'),
        help_text=_('Remplace les disciplines du package si définies')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('Créé par')
    )

    class Meta:
        verbose_name = _('Souscription d\'adhésion')
        verbose_name_plural = _('Souscriptions d\'adhésion')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.practitioner} - {self.package.name} ({self.status})"

    @property
    def is_active(self):
        """Vérifie si l'adhésion est active"""
        today = timezone.now().date()
        return (
            self.status == 'active' and
            self.start_date <= today <= self.end_date
        )

    @property
    def days_until_expiry(self):
        """Nombre de jours avant expiration"""
        if self.end_date:
            return (self.end_date - timezone.now().date()).days
        return None

    @property
    def needs_renewal_reminder(self):
        """Vérifie si un rappel de renouvellement est nécessaire"""
        days_until_expiry = self.days_until_expiry
        if days_until_expiry is not None:
            return days_until_expiry <= 14  # Rappel 14 jours avant
        return False

    def get_available_disciplines(self):
        """Retourne les disciplines disponibles pour cette souscription"""
        if self.custom_disciplines.exists():
            return self.custom_disciplines.all()
        return self.package.disciplines.all()


class MembershipWorkflow(models.Model):
    """
    Workflows automatisés pour les adhésions
    """
    TRIGGER_TYPES = [
        ('new_subscription', _('Nouvelle souscription')),
        ('renewal_due', _('Renouvellement dû')),
        ('expiry_warning', _('Alerte d\'expiration')),
        ('payment_failed', _('Échec de paiement')),
        ('cancellation', _('Annulation')),
    ]
    
    ACTION_TYPES = [
        ('send_email', _('Envoyer un email')),
        ('send_sms', _('Envoyer un SMS')),
        ('create_notification', _('Créer une notification')),
        ('suspend_membership', _('Suspendre l\'adhésion')),
        ('auto_renew', _('Renouveler automatiquement')),
        ('create_task', _('Créer une tâche')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='membership_workflows',
        verbose_name=_('Organisation')
    )
    
    name = models.CharField(max_length=200, verbose_name=_('Nom du workflow'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    
    # Configuration du déclencheur
    trigger_type = models.CharField(
        max_length=30,
        choices=TRIGGER_TYPES,
        verbose_name=_('Type de déclencheur')
    )
    trigger_days_before = models.IntegerField(
        default=0,
        verbose_name=_('Jours avant le déclencheur'),
        help_text=_('Pour les rappels d\'expiration')
    )
    
    # Configuration de l'action
    action_type = models.CharField(
        max_length=30,
        choices=ACTION_TYPES,
        verbose_name=_('Type d\'action')
    )
    action_content = models.JSONField(
        default=dict,
        verbose_name=_('Contenu de l\'action'),
        help_text=_('Configuration spécifique à l\'action')
    )
    
    # Conditions d'application
    applicable_packages = models.ManyToManyField(
        MembershipPackage,
        blank=True,
        verbose_name=_('Packages applicables')
    )
    
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Workflow d\'adhésion')
        verbose_name_plural = _('Workflows d\'adhésion')
        ordering = ['trigger_type', 'trigger_days_before']

    def __str__(self):
        return f"{self.name} ({self.get_trigger_type_display()})"


class OnlineMembershipForm(models.Model):
    """
    Formulaires d'adhésion en ligne simplifiés
    """
    FORM_TYPES = [
        ('registration', _('Inscription')),
        ('renewal', _('Renouvellement')),
        ('upgrade', _('Changement de package')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='membership_forms',
        verbose_name=_('Organisation')
    )
    
    name = models.CharField(max_length=200, verbose_name=_('Nom du formulaire'))
    slug = models.SlugField(unique=True, verbose_name=_('URL'))
    form_type = models.CharField(
        max_length=20,
        choices=FORM_TYPES,
        default='registration',
        verbose_name=_('Type de formulaire')
    )
    
    # Configuration d'affichage
    title = models.CharField(max_length=300, verbose_name=_('Titre'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    welcome_message = models.TextField(
        blank=True,
        verbose_name=_('Message de bienvenue')
    )
    success_message = models.TextField(
        blank=True,
        verbose_name=_('Message de succès')
    )
    
    # Packages disponibles
    available_packages = models.ManyToManyField(
        MembershipPackage,
        verbose_name=_('Packages disponibles')
    )
    
    # Configuration avancée
    require_medical_certificate = models.BooleanField(
        default=True,
        verbose_name=_('Certificat médical requis')
    )
    collect_emergency_contact = models.BooleanField(
        default=True,
        verbose_name=_('Contact d\'urgence')
    )
    collect_experience_level = models.BooleanField(
        default=True,
        verbose_name=_('Niveau d\'expérience')
    )
    allow_payment_plans = models.BooleanField(
        default=False,
        verbose_name=_('Échelonnement de paiement')
    )
    
    # Méta-données
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))
    is_public = models.BooleanField(default=True, verbose_name=_('Public'))
    max_submissions_per_day = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Soumissions max/jour')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Formulaire d\'adhésion en ligne')
        verbose_name_plural = _('Formulaires d\'adhésion en ligne')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.organization.name})"

    def get_absolute_url(self):
        return f"/membership/forms/{self.slug}/"


class MembershipFormSubmission(models.Model):
    """
    Soumissions de formulaires d'adhésion
    """
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('processing', _('En traitement')),
        ('approved', _('Approuvé')),
        ('rejected', _('Rejeté')),
        ('completed', _('Complété')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    form = models.ForeignKey(
        OnlineMembershipForm,
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name=_('Formulaire')
    )
    selected_package = models.ForeignKey(
        MembershipPackage,
        on_delete=models.CASCADE,
        verbose_name=_('Package sélectionné')
    )
    
    # Données du soumetteur
    email = models.EmailField(verbose_name=_('Email'))
    first_name = models.CharField(max_length=100, verbose_name=_('Prénom'))
    last_name = models.CharField(max_length=100, verbose_name=_('Nom'))
    phone = models.CharField(max_length=20, blank=True, verbose_name=_('Téléphone'))
    date_of_birth = models.DateField(verbose_name=_('Date de naissance'))
    
    # Contact d'urgence
    emergency_contact_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Nom du contact d\'urgence')
    )
    emergency_contact_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Téléphone d\'urgence')
    )
    
    # Données personnalisées
    form_data = models.JSONField(
        default=dict,
        verbose_name=_('Données du formulaire')
    )
    
    # Traitement
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_('Statut')
    )
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Traité par')
    )
    processing_notes = models.TextField(blank=True, verbose_name=_('Notes de traitement'))
    
    # Lien avec la souscription créée
    created_subscription = models.ForeignKey(
        MembershipSubscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Souscription créée')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Soumission de formulaire d\'adhésion')
        verbose_name_plural = _('Soumissions de formulaires d\'adhésion')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.selected_package.name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class MembershipAlert(models.Model):
    """
    Alertes et notifications liées aux adhésions
    """
    ALERT_TYPES = [
        ('expiry_warning', _('Alerte d\'expiration')),
        ('renewal_reminder', _('Rappel de renouvellement')),
        ('payment_due', _('Paiement dû')),
        ('package_upgrade', _('Suggestion d\'upgrade')),
        ('attendance_low', _('Assiduité faible')),
    ]
    
    PRIORITY_LEVELS = [
        ('low', _('Faible')),
        ('medium', _('Moyenne')),
        ('high', _('Élevée')),
        ('urgent', _('Urgente')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(
        MembershipSubscription,
        on_delete=models.CASCADE,
        related_name='alerts',
        verbose_name=_('Souscription')
    )
    
    alert_type = models.CharField(
        max_length=30,
        choices=ALERT_TYPES,
        verbose_name=_('Type d\'alerte')
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_LEVELS,
        default='medium',
        verbose_name=_('Priorité')
    )
    
    title = models.CharField(max_length=200, verbose_name=_('Titre'))
    message = models.TextField(verbose_name=_('Message'))
    
    # Traitement de l'alerte
    is_resolved = models.BooleanField(default=False, verbose_name=_('Résolu'))
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Résolu par')
    )
    
    # Notification envoyée
    notification_sent = models.BooleanField(default=False, verbose_name=_('Notification envoyée'))
    notification_sent_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Alerte d\'adhésion')
        verbose_name_plural = _('Alertes d\'adhésion')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.subscription.practitioner}"