"""
Service pour la gestion des comptes utilisateurs des pratiquants.
Permet la création de comptes avec username personnalisable et mot de passe standardisé.
"""
import logging
import re
import unicodedata
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)
User = get_user_model()


class PractitionerAccountService:
    """
    Service pour créer et gérer les comptes utilisateurs des pratiquants.
    """

    # Mot de passe standardisé par défaut
    DEFAULT_PASSWORD = "MartialComp@123"

    @staticmethod
    def normalize_string(text):
        """
        Normalise une chaîne : minuscules, sans accents, caractères autorisés uniquement.

        Args:
            text: Chaîne à normaliser

        Returns:
            str: Chaîne normalisée (a-z, 0-9, ., _)
        """
        if not text:
            return ""

        # Convertir en minuscules
        text = text.lower()

        # Supprimer les accents
        text = unicodedata.normalize('NFD', text)
        text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')

        # Remplacer les espaces par des underscores
        text = text.replace(' ', '_')

        # Ne garder que les caractères autorisés (a-z, 0-9, ., _)
        text = re.sub(r'[^a-z0-9._]', '', text)

        # Supprimer les caractères consécutifs (.. ou __)
        text = re.sub(r'\.+', '.', text)
        text = re.sub(r'_+', '_', text)

        # Supprimer les caractères en début/fin
        text = text.strip('._')

        return text

    @classmethod
    def generate_username(cls, first_name, last_name):
        """
        Génère un nom d'utilisateur unique basé sur prénom.nom.

        Args:
            first_name: Prénom du pratiquant
            last_name: Nom du pratiquant

        Returns:
            str: Username unique disponible
        """
        # Normaliser prénom et nom
        normalized_first = cls.normalize_string(first_name)
        normalized_last = cls.normalize_string(last_name)

        # Format de base : prénom.nom
        if normalized_first and normalized_last:
            base_username = f"{normalized_first}.{normalized_last}"
        elif normalized_first:
            base_username = normalized_first
        elif normalized_last:
            base_username = normalized_last
        else:
            base_username = "user"

        # Trouver un username unique
        username = base_username
        counter = 1

        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        return username

    @staticmethod
    def check_username_available(username):
        """
        Vérifie si un nom d'utilisateur est disponible.

        Args:
            username: Username à vérifier

        Returns:
            dict: {available: bool, message: str}
        """
        if not username:
            return {
                'available': False,
                'message': _("Le nom d'utilisateur ne peut pas être vide")
            }

        # Vérifier la longueur
        if len(username) < 3:
            return {
                'available': False,
                'message': _("Le nom d'utilisateur doit contenir au moins 3 caractères")
            }

        if len(username) > 30:
            return {
                'available': False,
                'message': _("Le nom d'utilisateur ne peut pas dépasser 30 caractères")
            }

        # Vérifier les caractères autorisés
        if not re.match(r'^[a-z0-9._]+$', username.lower()):
            return {
                'available': False,
                'message': _("Caractères autorisés : lettres, chiffres, point et underscore")
            }

        # Vérifier la disponibilité
        if User.objects.filter(username__iexact=username).exists():
            return {
                'available': False,
                'message': _("Ce nom d'utilisateur est déjà pris")
            }

        return {
            'available': True,
            'message': _("Disponible")
        }

    @classmethod
    def generate_custom_password(cls, practitioner):
        """
        Génère un mot de passe personnalisé basé sur le pratiquant.
        Format : {Prénom}@{AnnéeNaissance}MC

        Args:
            practitioner: Instance Practitioner

        Returns:
            str: Mot de passe personnalisé
        """
        first_name = cls.normalize_string(practitioner.first_name).capitalize()

        # Récupérer l'année de naissance
        birth_year = ""
        if hasattr(practitioner, 'birth_date') and practitioner.birth_date:
            birth_year = str(practitioner.birth_date.year)
        elif hasattr(practitioner, 'date_of_birth') and practitioner.date_of_birth:
            birth_year = str(practitioner.date_of_birth.year)
        else:
            birth_year = "2000"  # Année par défaut

        return f"{first_name}@{birth_year}MC"

    @classmethod
    def create_account(cls, practitioner, username, password=None, send_email=True, created_by=None):
        """
        Crée un compte utilisateur pour un pratiquant.

        Args:
            practitioner: Instance Practitioner
            username: Nom d'utilisateur souhaité
            password: Mot de passe (utilise DEFAULT_PASSWORD si None)
            send_email: Envoyer les identifiants par email
            created_by: Utilisateur qui crée le compte (pour logging)

        Returns:
            dict: {
                success: bool,
                user: User instance ou None,
                password: str ou None,
                message: str
            }
        """
        # Vérifier si le pratiquant a déjà un compte
        if practitioner.user:
            return {
                'success': False,
                'user': practitioner.user,
                'password': None,
                'message': _("Ce pratiquant possède déjà un compte utilisateur")
            }

        # Vérifier la disponibilité du username
        check = cls.check_username_available(username)
        if not check['available']:
            return {
                'success': False,
                'user': None,
                'password': None,
                'message': check['message']
            }

        # Utiliser le mot de passe par défaut si non spécifié
        if not password:
            password = cls.DEFAULT_PASSWORD

        # Déterminer l'email
        email = practitioner.email or f"{username}@example.com"

        try:
            # Créer l'utilisateur
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=practitioner.first_name,
                last_name=practitioner.last_name
            )

            # Configurer le profil
            if hasattr(user, 'profile'):
                user.profile.role = 'participant'
                user.profile.onboarding_completed = True
                user.profile.onboarding_step = 'completed'
                # Marquer que le mot de passe doit être changé
                if hasattr(user.profile, 'password_change_required'):
                    user.profile.password_change_required = True
                user.profile.save()
            else:
                # Créer le profil si nécessaire
                try:
                    from apps.competitions.models.users import UserProfile
                    UserProfile.objects.create(
                        user=user,
                        role='participant',
                        onboarding_completed=True,
                        onboarding_step='completed'
                    )
                except ImportError:
                    pass

            # Associer l'utilisateur au pratiquant
            practitioner.user = user
            practitioner.save()

            # Créer l'EmailAddress pour django-allauth
            try:
                from allauth.account.models import EmailAddress
                if practitioner.email and '@' in practitioner.email and not practitioner.email.endswith('@example.com'):
                    EmailAddress.objects.get_or_create(
                        user=user,
                        email=practitioner.email,
                        defaults={
                            'verified': True,
                            'primary': True
                        }
                    )
            except ImportError:
                pass

            # Logger l'événement
            logger.info(
                f"Compte créé pour {practitioner.full_name} (username: {username}) "
                f"par {created_by.username if created_by else 'système'}"
            )

            # Envoyer l'email si demandé
            email_sent = False
            if send_email and practitioner.email and '@' in practitioner.email and not practitioner.email.endswith('@example.com'):
                email_sent = cls.send_credentials_email(user, password, practitioner)

            return {
                'success': True,
                'user': user,
                'password': password,
                'email_sent': email_sent,
                'message': _("Compte créé avec succès")
            }

        except Exception as e:
            logger.error(f"Erreur lors de la création du compte pour {practitioner.full_name}: {str(e)}")
            return {
                'success': False,
                'user': None,
                'password': None,
                'message': str(e)
            }

    @staticmethod
    def send_credentials_email(user, password, practitioner=None):
        """
        Envoie un email avec les identifiants de connexion.

        Args:
            user: Instance User
            password: Mot de passe en clair
            practitioner: Instance Practitioner (optionnel)

        Returns:
            bool: True si envoyé avec succès
        """
        try:
            # Récupérer le club associé
            club = None
            if practitioner and hasattr(practitioner, 'organization') and practitioner.organization:
                try:
                    from apps.competitions.models import Club
                    club = Club.objects.filter(organization=practitioner.organization).first()
                except ImportError:
                    pass

            # Générer l'URL de connexion
            base_url = getattr(settings, 'BASE_URL', 'https://martialcomp.com')
            login_url = f"{base_url}{reverse('account_login')}"

            # Contexte pour le template
            context = {
                'user': user,
                'practitioner': practitioner,
                'username': user.username,
                'password': password,
                'club': club,
                'login_url': login_url,
                'current_year': timezone.now().year,
            }

            # Rendu des templates
            subject = _("Vos identifiants de connexion MartialComp")

            try:
                html_message = render_to_string('competitions/emails/account_credentials.html', context)
            except Exception:
                # Template de fallback simple
                html_message = f"""
                <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2>Bienvenue sur MartialComp !</h2>
                    <p>Bonjour {user.first_name},</p>
                    <p>Votre compte a été créé. Voici vos identifiants de connexion :</p>
                    <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p><strong>Nom d'utilisateur :</strong> {user.username}</p>
                        <p><strong>Mot de passe :</strong> {password}</p>
                    </div>
                    <p><a href="{login_url}" style="background: #c9a227; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Se connecter</a></p>
                    <p style="color: #888; font-size: 12px;">Vous devrez changer votre mot de passe lors de votre première connexion.</p>
                </body>
                </html>
                """

            text_message = f"""
Bienvenue sur MartialComp !

Bonjour {user.first_name},

Votre compte a été créé. Voici vos identifiants de connexion :

Nom d'utilisateur : {user.username}
Mot de passe : {password}

Connectez-vous sur : {login_url}

Vous devrez changer votre mot de passe lors de votre première connexion.

L'équipe MartialComp
            """

            # Envoi de l'email
            send_mail(
                subject=str(subject),
                message=text_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@martialcomp.com'),
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )

            logger.info(f"Email d'identifiants envoyé à {user.email}")
            return True

        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email d'identifiants à {user.email}: {str(e)}")
            return False
