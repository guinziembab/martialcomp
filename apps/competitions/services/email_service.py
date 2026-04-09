"""
Service d'envoi d'emails pour MartialComp.
Gère l'envoi d'emails pour:
- Assignations de juges
- Notifications diverses
- Réinitialisation de mot de passe (Prompt 1)
- Activation de compte avec credentials (Prompt 2)
- Authentification sociale (Prompt 3)
"""

import logging
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.competitions.models.notifications import NotificationPreference

logger = logging.getLogger(__name__)


class EmailService:
    """
    Service pour envoyer des emails liés aux compétitions.
    Gère l'envoi d'emails avec templates HTML et gestion des préférences.
    """

    @staticmethod
    def send_judge_assignment_email(judge_assignment):
        """
        Envoie un email à un juge lorsqu'il est assigné à une catégorie.
        
        Args:
            judge_assignment: Instance de JudgeAssignment
            
        Returns:
            bool: True si l'email a été envoyé avec succès, False sinon
        """
        try:
            if not judge_assignment.judge:
                logger.warning(f"Pas de juge associé à l'assignation {judge_assignment.id}")
                return False
            
            # Vérifier les préférences email de l'utilisateur
            prefs, _ = NotificationPreference.objects.get_or_create(
                user=judge_assignment.judge,
                defaults={
                    'email_enabled': True,
                    'competition_notifications': True,
                }
            )
            
            # Vérifier si l'utilisateur a activé les emails et les notifications de compétition
            if not prefs.email_enabled:
                logger.debug(
                    f"Emails désactivés pour {judge_assignment.judge.username} - "
                    f"Assignation {judge_assignment.id} ignorée"
                )
                return False
            
            if not prefs.competition_notifications:
                logger.debug(
                    f"Notifications de compétition désactivées pour {judge_assignment.judge.username} - "
                    f"Assignation {judge_assignment.id} ignorée"
                )
                return False
            
            # Vérifier que l'utilisateur a une adresse email
            judge = judge_assignment.judge
            if not hasattr(judge, 'email') or not judge.email:
                logger.warning(f"Pas d'email pour le juge {judge.username}")
                return False
            
            # Préparer les informations pour l'email
            competition_name = (
                judge_assignment.competition.title 
                if hasattr(judge_assignment.competition, 'title') 
                else str(judge_assignment.competition)
            )
            category_name = (
                judge_assignment.category.name 
                if judge_assignment.category 
                else "Compétition générale"
            )
            role_display = (
                judge_assignment.get_role_display() 
                if hasattr(judge_assignment, 'get_role_display') 
                else judge_assignment.role
            )
            
            # Générer le lien vers l'interface de notation
            try:
                if judge_assignment.category:
                    # Lien vers l'interface de notation spécifique à la catégorie
                    action_url = reverse('competitions:management:judge_scoring_interface', kwargs={
                        'competition_id': judge_assignment.competition.id,
                        'category_id': judge_assignment.category.id,
                        'judge_id': judge_assignment.judge.id,
                    })
                else:
                    # Lien vers le dashboard scoring général
                    action_url = reverse('competitions:management:scoring_dashboard', kwargs={
                        'competition_id': judge_assignment.competition.id,
                    })
            except Exception as url_error:
                # En cas d'erreur de génération d'URL, utiliser le dashboard général
                logger.warning(f"Erreur génération URL pour assignation {judge_assignment.id}: {url_error}")
                try:
                    action_url = reverse('competitions:dashboard')
                except:
                    action_url = None
            
            # Construire l'URL complète avec le domaine
            site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
            full_action_url = f"{site_url}{action_url}" if action_url else None
            
            # Préparer le contexte pour le template
            context = {
                'judge': judge,
                'judge_assignment': judge_assignment,
                'competition': judge_assignment.competition,
                'category': judge_assignment.category,
                'competition_name': competition_name,
                'category_name': category_name,
                'role_display': role_display,
                'action_url': full_action_url,
                'start_time': judge_assignment.start_time,
                'site_url': site_url,
            }
            
            # Sujet de l'email
            subject = f"Assignation comme juge - {competition_name}"
            
            # Charger et rendre le template email
            try:
                html_content = render_to_string(
                    'competitions/emails/judge_assignment.html',
                    context
                )
                text_content = strip_tags(html_content)
            except Exception as template_error:
                # Si le template n'existe pas, créer un email simple
                logger.warning(
                    f"Template email non trouvé, utilisation du format simple: {template_error}"
                )
                html_content = EmailService._create_simple_assignment_email(context)
                text_content = strip_tags(html_content)
            
            # Adresse email de l'expéditeur
            from_email = getattr(
                settings,
                'DEFAULT_FROM_EMAIL',
                getattr(settings, 'SERVER_EMAIL', 'noreply@martialcomp.com')
            )
            
            # Créer l'email avec contenu HTML et texte
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[judge.email]
            )
            email.attach_alternative(html_content, "text/html")
            
            # Envoyer l'email
            email.send(fail_silently=False)
            
            logger.info(
                f"Email d'assignation envoyé à {judge.email} pour l'assignation #{judge_assignment.id} "
                f"({competition_name} - {category_name})"
            )
            
            return True
            
        except Exception as e:
            logger.error(
                f"Erreur lors de l'envoi de l'email d'assignation pour l'assignation "
                f"#{judge_assignment.id}: {e}",
                exc_info=True
            )
            return False

    @staticmethod
    def _create_simple_assignment_email(context):
        """
        Crée un email simple en HTML si le template n'existe pas.
        
        Args:
            context: Contexte pour le template
            
        Returns:
            str: Contenu HTML de l'email
        """
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #4CAF50;
                    color: white;
                    padding: 20px;
                    text-align: center;
                }}
                .content {{
                    padding: 20px;
                    background-color: #f9f9f9;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #4CAF50;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    padding: 20px;
                    color: #666;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Assignation comme juge</h1>
                </div>
                <div class="content">
                    <p>Bonjour {context['judge'].get_full_name() or context['judge'].username},</p>
                    
                    <p>Vous avez été assigné comme <strong>{context['role_display']}</strong> 
                    pour la catégorie <strong>{context['category_name']}</strong> 
                    de la compétition <strong>{context['competition_name']}</strong>.</p>
                    
                    {f"<p><strong>Heure de début prévue :</strong> {context['start_time'].strftime('%d/%m/%Y à %H:%M')}</p>" if context.get('start_time') else ""}
                    
                    <p style="text-align: center;">
                        <a href="{context.get('action_url', '#')}" class="button">
                            Accéder à l'interface de notation
                        </a>
                    </p>
                    
                    <p>Si le bouton ne fonctionne pas, copiez et collez ce lien dans votre navigateur :<br>
                    <a href="{context.get('action_url', '#')}">{context.get('action_url', '#')}</a></p>
                </div>
                <div class="footer">
                    <p>Cet email est automatique, merci de ne pas y répondre.</p>
                    <p>L'équipe de gestion des compétitions</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html

    @staticmethod
    def check_email_preferences(user):
        """
        Vérifie si un utilisateur souhaite recevoir des emails.
        
        Args:
            user: Instance de User
            
        Returns:
            bool: True si l'utilisateur souhaite recevoir des emails, False sinon
        """
        try:
            prefs, _ = NotificationPreference.objects.get_or_create(
                user=user,
                defaults={
                    'email_enabled': True,
                    'competition_notifications': True,
                }
            )
            return prefs.email_enabled and prefs.competition_notifications
        except Exception as e:
            logger.warning(f"Erreur lors de la vérification des préférences email pour {user.username}: {e}")
            return True  # Par défaut, accepter l'envoi d'emails

    @staticmethod
    def send_notification_email(notification):
        """
        Envoie un email pour une notification existante.
        
        Args:
            notification: Instance de Notification
            
        Returns:
            bool: True si l'email a été envoyé avec succès, False sinon
        """
        try:
            user = notification.user
            
            # Vérifier les préférences
            if not EmailService.check_email_preferences(user):
                logger.debug(f"Emails désactivés pour {user.username} - Notification {notification.id} ignorée")
                return False
            
            # Vérifier que l'utilisateur a une adresse email
            if not hasattr(user, 'email') or not user.email:
                logger.warning(f"Pas d'email pour l'utilisateur {user.username}")
                return False
            
            # Construire l'URL complète avec le domaine
            site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
            full_action_url = f"{site_url}{notification.action_url}" if notification.action_url else None
            
            # Préparer le contexte
            context = {
                'user': user,
                'notification': notification,
                'action_url': full_action_url,
                'site_url': site_url,
            }
            
            # Sujet de l'email
            subject = notification.title
            
            # Charger et rendre le template email
            try:
                html_content = render_to_string(
                    'competitions/emails/notification.html',
                    context
                )
                text_content = strip_tags(html_content)
            except Exception as template_error:
                # Si le template n'existe pas, créer un email simple
                logger.warning(
                    f"Template email non trouvé, utilisation du format simple: {template_error}"
                )
                html_content = EmailService._create_simple_notification_email(context)
                text_content = strip_tags(html_content)
            
            # Adresse email de l'expéditeur
            from_email = getattr(
                settings,
                'DEFAULT_FROM_EMAIL',
                getattr(settings, 'SERVER_EMAIL', 'noreply@martialcomp.com')
            )
            
            # Créer l'email avec contenu HTML et texte
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[user.email]
            )
            email.attach_alternative(html_content, "text/html")
            
            # Envoyer l'email
            email.send(fail_silently=False)
            
            logger.info(f"Email de notification envoyé à {user.email} pour la notification #{notification.id}")
            
            return True
            
        except Exception as e:
            logger.error(
                f"Erreur lors de l'envoi de l'email de notification pour la notification "
                f"#{notification.id}: {e}",
                exc_info=True
            )
            return False

    @staticmethod
    def _create_simple_notification_email(context):
        """
        Crée un email simple en HTML si le template n'existe pas.
        
        Args:
            context: Contexte pour le template
            
        Returns:
            str: Contenu HTML de l'email
        """
        notification = context['notification']
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #2196F3;
                    color: white;
                    padding: 20px;
                    text-align: center;
                }}
                .content {{
                    padding: 20px;
                    background-color: #f9f9f9;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #2196F3;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    padding: 20px;
                    color: #666;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{notification.title}</h1>
                </div>
                <div class="content">
                    <p>Bonjour {context['user'].get_full_name() or context['user'].username},</p>
                    
                    <p>{notification.message}</p>
                    
                    {f'<p style="text-align: center;"><a href="{context.get("action_url", "#")}" class="button">{notification.action_text or "Voir plus"}</a></p>' if context.get('action_url') else ''}
                    
                    {f'<p>Si le bouton ne fonctionne pas, copiez et collez ce lien dans votre navigateur :<br><a href="{context.get("action_url", "#")}">{context.get("action_url", "#")}</a></p>' if context.get('action_url') else ''}
                </div>
                <div class="footer">
                    <p>Cet email est automatique, merci de ne pas y répondre.</p>
                    <p>L'équipe de gestion des compétitions</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html

    # ================================================================
    # MÉTHODES POUR L'AUTHENTIFICATION (PHASE 1 - Prompts 1, 2, 3)
    # ================================================================

    @staticmethod
    def send_password_reset_email(user, reset_url, token_expiry_hours=24):
        """
        Envoie un email de réinitialisation de mot de passe.

        Args:
            user: Instance de User
            reset_url: URL complète pour réinitialiser le mot de passe
            token_expiry_hours: Durée de validité du token en heures

        Returns:
            bool: True si l'email a été envoyé avec succès, False sinon
        """
        try:
            if not user.email:
                logger.warning(f"Pas d'email pour l'utilisateur {user.username}")
                return False

            site_url = getattr(settings, 'SITE_URL', 'https://martialcomp.com')

            context = {
                'user': user,
                'reset_url': reset_url,
                'token_expiry_hours': token_expiry_hours,
                'site_url': site_url,
                'site_name': 'MartialComp',
            }

            subject = _("Réinitialisation de votre mot de passe MartialComp")

            try:
                html_content = render_to_string(
                    'account/email/password_reset_message.html',
                    context
                )
                text_content = strip_tags(html_content)
            except Exception as template_error:
                logger.warning(f"Template password_reset non trouvé: {template_error}")
                html_content = EmailService._create_password_reset_email(context)
                text_content = strip_tags(html_content)

            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'MartialComp <noreply@martialcomp.com>')

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[user.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)

            logger.info(f"Email de réinitialisation envoyé à {user.email}")
            return True

        except Exception as e:
            logger.error(f"Erreur envoi email réinitialisation pour {user.username}: {e}", exc_info=True)
            return False

    @staticmethod
    def _create_password_reset_email(context):
        """Crée un email HTML simple pour la réinitialisation de mot de passe."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; background-color: #f4f4f4; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .card {{ background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #dc3545 0%, #a71d2a 100%); color: white; padding: 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .content {{ padding: 30px; }}
                .button {{ display: inline-block; padding: 14px 28px; background: linear-gradient(135deg, #dc3545 0%, #a71d2a 100%); color: white !important; text-decoration: none; border-radius: 8px; margin: 20px 0; font-weight: bold; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; background: #f9f9f9; }}
                .warning {{ background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; padding: 15px; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="card">
                    <div class="header">
                        <h1>🔐 Réinitialisation de mot de passe</h1>
                    </div>
                    <div class="content">
                        <p>Bonjour <strong>{context['user'].get_full_name() or context['user'].username}</strong>,</p>

                        <p>Vous avez demandé la réinitialisation de votre mot de passe sur <strong>MartialComp</strong>.</p>

                        <p style="text-align: center;">
                            <a href="{context['reset_url']}" class="button">
                                Réinitialiser mon mot de passe
                            </a>
                        </p>

                        <div class="warning">
                            <strong>⚠️ Important :</strong> Ce lien est valable pendant <strong>{context['token_expiry_hours']} heures</strong>.
                            Après ce délai, vous devrez refaire une demande de réinitialisation.
                        </div>

                        <p>Si vous n'avez pas demandé cette réinitialisation, vous pouvez ignorer cet email.
                        Votre mot de passe ne sera pas modifié.</p>

                        <p style="color: #666; font-size: 12px;">
                            Si le bouton ne fonctionne pas, copiez et collez ce lien dans votre navigateur :<br>
                            <a href="{context['reset_url']}" style="color: #dc3545;">{context['reset_url']}</a>
                        </p>
                    </div>
                    <div class="footer">
                        <p>Cet email a été envoyé automatiquement par MartialComp.</p>
                        <p>© {timezone.now().year} MartialComp - Plateforme de gestion des arts martiaux</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        return html

    @staticmethod
    def send_account_activation_email(user, password_plain=None, activation_url=None):
        """
        Envoie un email d'activation de compte avec les credentials.
        Utilisé lors de la création de compte par un admin/club.

        Args:
            user: Instance de User
            password_plain: Mot de passe en clair (optionnel, pour création par admin)
            activation_url: URL d'activation du compte

        Returns:
            bool: True si l'email a été envoyé avec succès, False sinon
        """
        try:
            if not user.email:
                logger.warning(f"Pas d'email pour l'utilisateur {user.username}")
                return False

            site_url = getattr(settings, 'SITE_URL', 'https://martialcomp.com')
            login_url = f"{site_url}/accounts/login/"

            context = {
                'user': user,
                'username': user.username,
                'email': user.email,
                'password_plain': password_plain,
                'activation_url': activation_url,
                'login_url': login_url,
                'site_url': site_url,
                'site_name': 'MartialComp',
            }

            if password_plain:
                subject = _("Votre compte MartialComp a été créé")
            else:
                subject = _("Activez votre compte MartialComp")

            try:
                html_content = render_to_string(
                    'account/email/account_activation_message.html',
                    context
                )
                text_content = strip_tags(html_content)
            except Exception as template_error:
                logger.warning(f"Template account_activation non trouvé: {template_error}")
                html_content = EmailService._create_account_activation_email(context)
                text_content = strip_tags(html_content)

            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'MartialComp <noreply@martialcomp.com>')

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[user.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)

            logger.info(f"Email d'activation envoyé à {user.email}")
            return True

        except Exception as e:
            logger.error(f"Erreur envoi email activation pour {user.username}: {e}", exc_info=True)
            return False

    @staticmethod
    def _create_account_activation_email(context):
        """Crée un email HTML simple pour l'activation de compte."""
        password_section = ""
        if context.get('password_plain'):
            password_section = f"""
            <div style="background: #e8f5e9; border: 1px solid #4caf50; border-radius: 8px; padding: 15px; margin: 15px 0;">
                <strong>🔑 Vos identifiants de connexion :</strong><br><br>
                <strong>Email :</strong> {context['email']}<br>
                <strong>Nom d'utilisateur :</strong> {context['username']}<br>
                <strong>Mot de passe temporaire :</strong> <code style="background: #fff; padding: 2px 6px; border-radius: 4px;">{context['password_plain']}</code>
                <br><br>
                <em style="color: #666;">⚠️ Nous vous recommandons de changer ce mot de passe dès votre première connexion.</em>
            </div>
            """

        activation_button = ""
        if context.get('activation_url'):
            activation_button = f"""
            <p style="text-align: center;">
                <a href="{context['activation_url']}" class="button">
                    Activer mon compte
                </a>
            </p>
            """

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; background-color: #f4f4f4; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .card {{ background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #dc3545 0%, #a71d2a 100%); color: white; padding: 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .content {{ padding: 30px; }}
                .button {{ display: inline-block; padding: 14px 28px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white !important; text-decoration: none; border-radius: 8px; margin: 20px 0; font-weight: bold; }}
                .button-secondary {{ display: inline-block; padding: 12px 24px; background: linear-gradient(135deg, #dc3545 0%, #a71d2a 100%); color: white !important; text-decoration: none; border-radius: 8px; margin: 10px 5px; font-weight: bold; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; background: #f9f9f9; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="card">
                    <div class="header">
                        <h1>🎉 Bienvenue sur MartialComp !</h1>
                    </div>
                    <div class="content">
                        <p>Bonjour <strong>{context['user'].get_full_name() or context['user'].username}</strong>,</p>

                        <p>Votre compte sur <strong>MartialComp</strong> a été créé avec succès !</p>

                        {password_section}

                        {activation_button}

                        <p style="text-align: center;">
                            <a href="{context['login_url']}" class="button-secondary">
                                Se connecter
                            </a>
                        </p>

                        <p>MartialComp est votre plateforme de gestion complète pour les arts martiaux :
                        clubs, compétitions, grades, et bien plus encore !</p>
                    </div>
                    <div class="footer">
                        <p>Cet email a été envoyé automatiquement par MartialComp.</p>
                        <p>© {timezone.now().year} MartialComp - Plateforme de gestion des arts martiaux</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        return html

    @staticmethod
    def send_welcome_email(user, provider=None):
        """
        Envoie un email de bienvenue après inscription (standard ou sociale).

        Args:
            user: Instance de User
            provider: Fournisseur d'authentification sociale (google, facebook, apple) ou None

        Returns:
            bool: True si l'email a été envoyé avec succès, False sinon
        """
        try:
            if not user.email:
                logger.warning(f"Pas d'email pour l'utilisateur {user.username}")
                return False

            site_url = getattr(settings, 'SITE_URL', 'https://martialcomp.com')
            dashboard_url = f"{site_url}/competitions/dashboard/"

            provider_names = {
                'google': 'Google',
                'facebook': 'Facebook',
                'apple': 'Apple',
            }
            provider_display = provider_names.get(provider, provider) if provider else None

            context = {
                'user': user,
                'provider': provider,
                'provider_display': provider_display,
                'dashboard_url': dashboard_url,
                'site_url': site_url,
                'site_name': 'MartialComp',
            }

            if provider:
                subject = _("Bienvenue sur MartialComp - Connexion via %(provider)s réussie") % {'provider': provider_display}
            else:
                subject = _("Bienvenue sur MartialComp !")

            try:
                html_content = render_to_string(
                    'account/email/welcome_message.html',
                    context
                )
                text_content = strip_tags(html_content)
            except Exception as template_error:
                logger.warning(f"Template welcome non trouvé: {template_error}")
                html_content = EmailService._create_welcome_email(context)
                text_content = strip_tags(html_content)

            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'MartialComp <noreply@martialcomp.com>')

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[user.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)

            logger.info(f"Email de bienvenue envoyé à {user.email} (provider: {provider or 'standard'})")
            return True

        except Exception as e:
            logger.error(f"Erreur envoi email bienvenue pour {user.username}: {e}", exc_info=True)
            return False

    @staticmethod
    def _create_welcome_email(context):
        """Crée un email HTML simple de bienvenue."""
        provider_message = ""
        if context.get('provider_display'):
            provider_message = f"""
            <p style="background: #e3f2fd; border-radius: 8px; padding: 15px; margin: 15px 0;">
                <strong>✅ Connexion via {context['provider_display']}</strong><br>
                Vous pouvez vous connecter à tout moment en utilisant votre compte {context['provider_display']}.
            </p>
            """

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; background-color: #f4f4f4; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .card {{ background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #dc3545 0%, #a71d2a 100%); color: white; padding: 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .content {{ padding: 30px; }}
                .button {{ display: inline-block; padding: 14px 28px; background: linear-gradient(135deg, #dc3545 0%, #a71d2a 100%); color: white !important; text-decoration: none; border-radius: 8px; margin: 20px 0; font-weight: bold; }}
                .features {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin: 20px 0; }}
                .feature {{ background: #f8f9fa; border-radius: 8px; padding: 15px; text-align: center; }}
                .feature-icon {{ font-size: 24px; margin-bottom: 5px; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; background: #f9f9f9; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="card">
                    <div class="header">
                        <h1>🥋 Bienvenue sur MartialComp !</h1>
                    </div>
                    <div class="content">
                        <p>Bonjour <strong>{context['user'].get_full_name() or context['user'].username}</strong>,</p>

                        <p>Félicitations ! Votre compte MartialComp a été créé avec succès.</p>

                        {provider_message}

                        <p>Découvrez tout ce que vous pouvez faire avec MartialComp :</p>

                        <div class="features">
                            <div class="feature">
                                <div class="feature-icon">🏆</div>
                                <strong>Compétitions</strong><br>
                                <small>Gérez et participez</small>
                            </div>
                            <div class="feature">
                                <div class="feature-icon">🥋</div>
                                <strong>Clubs</strong><br>
                                <small>Trouvez votre club</small>
                            </div>
                            <div class="feature">
                                <div class="feature-icon">📊</div>
                                <strong>Grades</strong><br>
                                <small>Suivez votre progression</small>
                            </div>
                            <div class="feature">
                                <div class="feature-icon">👨‍⚖️</div>
                                <strong>Arbitrage</strong><br>
                                <small>Officiez en compétition</small>
                            </div>
                        </div>

                        <p style="text-align: center;">
                            <a href="{context['dashboard_url']}" class="button">
                                Accéder à mon espace
                            </a>
                        </p>
                    </div>
                    <div class="footer">
                        <p>Cet email a été envoyé automatiquement par MartialComp.</p>
                        <p>© {timezone.now().year} MartialComp - Plateforme de gestion des arts martiaux</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        return html

    @staticmethod
    def test_email_configuration():
        """
        Teste la configuration email en envoyant un email de test.
        Utile pour vérifier que SMTP fonctionne correctement.

        Returns:
            dict: Résultat du test avec statut et message
        """
        try:
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@martialcomp.com')
            admin_email = getattr(settings, 'ADMIN_EMAIL', None)

            if not admin_email:
                admins = getattr(settings, 'ADMINS', [])
                if admins:
                    admin_email = admins[0][1]
                else:
                    return {
                        'success': False,
                        'message': "Aucune adresse admin configurée (ADMIN_EMAIL ou ADMINS)"
                    }

            subject = f"[MartialComp] Test de configuration email - {timezone.now().strftime('%Y-%m-%d %H:%M')}"
            message = f"""
            Ceci est un email de test envoyé depuis MartialComp.

            Configuration actuelle:
            - EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'non configuré')}
            - EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'non configuré')}
            - EMAIL_USE_TLS: {getattr(settings, 'EMAIL_USE_TLS', False)}
            - DEFAULT_FROM_EMAIL: {from_email}

            Si vous recevez cet email, la configuration SMTP est correcte.

            Date du test: {timezone.now().strftime('%d/%m/%Y à %H:%M:%S')}
            """

            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[admin_email],
                fail_silently=False
            )

            logger.info(f"Email de test envoyé avec succès à {admin_email}")
            return {
                'success': True,
                'message': f"Email de test envoyé à {admin_email}"
            }

        except Exception as e:
            logger.error(f"Échec du test email: {e}", exc_info=True)
            return {
                'success': False,
                'message': f"Erreur: {str(e)}"
            }

    # =============================================
    # Contact Form Emails
    # =============================================

    @staticmethod
    def send_contact_acknowledgment(submission):
        """
        Envoie un accuse de reception a l'expediteur du formulaire de contact.
        Email professionnel avec logo MartialComp et recapitulatif.
        """
        try:
            site_url = getattr(settings, 'SITE_URL', 'https://martialcomp.com')
            context = {
                'submission': submission,
                'site_url': site_url,
                'year': timezone.now().year,
            }

            subject = _("[MartialComp] Nous avons bien recu votre message")

            try:
                html_content = render_to_string(
                    'competitions/emails/contact_acknowledgment.html', context
                )
            except Exception as tmpl_err:
                logger.warning(f"Template contact_acknowledgment non trouve: {tmpl_err}")
                html_content = f"""
                <html><body style="font-family:Arial,sans-serif;">
                <h2 style="color:#d4af37;">MartialComp</h2>
                <p>Bonjour {submission.name},</p>
                <p>Nous avons bien recu votre message concernant <strong>{submission.get_subject_display()}</strong>.</p>
                <p>Notre equipe vous repondra dans les 48 heures ouvrables.</p>
                <hr><p style="color:#999;font-size:12px;">MartialComp - {site_url}</p>
                </body></html>
                """

            text_content = strip_tags(html_content)
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'MartialComp <noreply@martialcomp.com>')

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[submission.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)

            logger.info(f"Accuse de reception envoye a {submission.email}")
            return True

        except Exception as e:
            logger.error(f"Erreur envoi accuse de reception a {submission.email}: {e}", exc_info=True)
            return False

    @staticmethod
    def send_contact_admin_notification(submission):
        """
        Envoie une notification a l'equipe support avec les details du message.
        """
        try:
            site_url = getattr(settings, 'SITE_URL', 'https://martialcomp.com')
            admin_url = f"{site_url}/admin/competitions/contactsubmission/{submission.id}/change/"
            contact_email = getattr(settings, 'CONTACT_EMAIL', 'support@martialcomp.com')

            context = {
                'submission': submission,
                'site_url': site_url,
                'admin_url': admin_url,
            }

            subject = f"[Contact MartialComp] {submission.get_subject_display()} - {submission.name}"
            if submission.organization:
                subject += f" ({submission.organization})"

            try:
                html_content = render_to_string(
                    'competitions/emails/contact_notification_admin.html', context
                )
            except Exception as tmpl_err:
                logger.warning(f"Template contact_notification_admin non trouve: {tmpl_err}")
                html_content = f"""
                <html><body style="font-family:Arial,sans-serif;">
                <h2 style="color:#c41e3a;">Nouveau message de contact</h2>
                <p><strong>De:</strong> {submission.name} ({submission.email})</p>
                <p><strong>Organisation:</strong> {submission.organization or 'Non renseigne'}</p>
                <p><strong>Sujet:</strong> {submission.get_subject_display()}</p>
                <p><strong>Message:</strong></p>
                <blockquote style="background:#f5f5f5;padding:15px;border-left:3px solid #c41e3a;">
                {submission.message}
                </blockquote>
                <p><a href="mailto:{submission.email}">Repondre</a></p>
                </body></html>
                """

            text_content = strip_tags(html_content)
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'MartialComp <noreply@martialcomp.com>')

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[contact_email],
                reply_to=[submission.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)

            logger.info(f"Notification contact admin envoyee a {contact_email} pour {submission.email}")
            return True

        except Exception as e:
            logger.error(f"Erreur envoi notification contact admin: {e}", exc_info=True)
            return False
