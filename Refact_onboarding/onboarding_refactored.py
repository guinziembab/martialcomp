# apps/competitions/views/onboarding/wizard.py
"""
Onboarding simplifié en 2-3 étapes maximum
Utilise Django FormWizard pour un processus robuste
"""

from django.shortcuts import redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.translation import gettext as _
from formtools.wizard.views import SessionWizardView
import logging

from ...models import Club, Federation, Discipline, UserProfile
from ...forms.onboarding import (
    AccountCreationForm,
    RoleSelectionForm,
    ClubBasicInfoForm,
    FederationBasicInfoForm,
    JudgeBasicInfoForm,
    ParticipantBasicInfoForm
)

logger = logging.getLogger(__name__)


class SimplifiedOnboardingWizard(SessionWizardView):
    """
    Wizard d'onboarding simplifié en 2-3 étapes:
    1. Création compte + sélection rôle
    2. Informations spécifiques au rôle (optionnel)
    3. Redirection vers dashboard
    """
    
    template_name = 'competitions/onboarding/wizard.html'
    
    # Mapping des formulaires par étape
    form_list = [
        ('account', AccountCreationForm),
        ('role', RoleSelectionForm),
    ]
    
    def get_template_names(self):
        """Template différent par étape"""
        return [self.template_name]
    
    def get_form_list(self):
        """Détermine les formulaires à afficher selon le rôle"""
        form_list = dict(self.form_list)
        
        # Récupérer le rôle sélectionné si l'étape 'role' est complétée
        role_data = self.get_cleaned_data_for_step('role')
        
        if role_data:
            role = role_data.get('role')
            
            # Ajouter le formulaire spécifique au rôle
            if role == 'club_manager':
                form_list['details'] = ClubBasicInfoForm
            elif role == 'federation_admin':
                form_list['details'] = FederationBasicInfoForm
            elif role == 'judge':
                form_list['details'] = JudgeBasicInfoForm
            elif role == 'participant':
                form_list['details'] = ParticipantBasicInfoForm
            # Spectateur n'a pas besoin de formulaire supplémentaire
        
        return form_list
    
    def get_context_data(self, form, **kwargs):
        """Ajoute des données au contexte"""
        context = super().get_context_data(form=form, **kwargs)
        
        # Ajouter le rôle sélectionné au contexte
        role_data = self.get_cleaned_data_for_step('role')
        if role_data:
            context['selected_role'] = role_data.get('role')
        
        # Ajouter les disciplines disponibles
        context['disciplines'] = Discipline.objects.filter(is_active=True)
        
        # Progression
        total_steps = len(self.get_form_list())
        current_step = self.steps.current
        context['progress'] = {
            'current': self.steps.index + 1,
            'total': total_steps,
            'percent': int(((self.steps.index + 1) / total_steps) * 100)
        }
        
        return context
    
    def done(self, form_list, **kwargs):
        """
        Traitement final quand toutes les étapes sont complétées
        """
        try:
            # Récupérer les données de tous les formulaires
            all_data = {}
            for form in form_list:
                all_data.update(form.cleaned_data)
            
            # 1. Créer l'utilisateur
            user = self._create_user(all_data)
            
            # 2. Créer le profil avec le rôle
            profile = self._create_profile(user, all_data)
            
            # 3. Créer l'entité selon le rôle (club, fédération, etc.)
            entity = self._create_entity(user, profile, all_data)
            
            # 4. Marquer l'onboarding comme terminé
            profile.onboarding_completed = True
            profile.save()
            
            # 5. Connecter l'utilisateur
            login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            # 6. Message de succès
            messages.success(
                self.request,
                _("Bienvenue sur MartialComp! Votre compte a été créé avec succès.")
            )
            
            # 7. Redirection vers le dashboard approprié
            return redirect(self._get_dashboard_url(profile.role))
        
        except Exception as e:
            logger.error(f"Onboarding failed: {e}", exc_info=True)
            messages.error(
                self.request,
                _("Une erreur est survenue lors de la création de votre compte. Notre équipe a été notifiée.")
            )
            return redirect('signup')
    
    def _create_user(self, data):
        """Crée l'utilisateur Django"""
        try:
            user = User.objects.create_user(
                username=data['email'],
                email=data['email'],
                password=data['password'],
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', '')
            )
            logger.info(f"User created: {user.email}")
            return user
        except Exception as e:
            logger.error(f"Error creating user: {e}", exc_info=True)
            raise
    
    def _create_profile(self, user, data):
        """Crée ou met à jour le profil utilisateur"""
        try:
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.role = data['role']
            profile.onboarding_step = 'completed'
            profile.save()
            
            logger.info(f"Profile created/updated for user: {user.email}, role: {data['role']}")
            return profile
        except Exception as e:
            logger.error(f"Error creating profile: {e}", exc_info=True)
            raise
    
    def _create_entity(self, user, profile, data):
        """Crée l'entité selon le rôle (club, fédération, etc.)"""
        try:
            role = data['role']
            
            if role == 'club_manager':
                return self._create_club(user, profile, data)
            elif role == 'federation_admin':
                return self._create_federation(user, profile, data)
            elif role == 'judge':
                return self._create_judge_profile(user, profile, data)
            elif role == 'participant':
                return self._create_participant_profile(user, profile, data)
            else:
                # Spectateur n'a pas d'entité supplémentaire
                return None
        except Exception as e:
            logger.error(f"Error creating entity for role {role}: {e}", exc_info=True)
            # Ne pas bloquer la création du compte si l'entité échoue
            messages.warning(
                self.request,
                _("Votre compte a été créé, mais certaines informations complémentaires n'ont pas pu être enregistrées. Vous pourrez les compléter plus tard.")
            )
            return None
    
    def _create_club(self, user, profile, data):
        """Crée le club"""
        try:
            # Vérifier qu'une discipline par défaut existe
            disciplines = Discipline.objects.filter(is_active=True)
            if not disciplines.exists():
                # Créer une discipline par défaut
                default_discipline = Discipline.objects.create(
                    name='Arts Martiaux',
                    is_active=True
                )
                logger.warning("Created default discipline as none existed")
            else:
                default_discipline = disciplines.first()
            
            club = Club.objects.create(
                name=data.get('club_name', f"Club de {user.get_full_name()}"),
                city=data.get('city', ''),
                address=data.get('address', ''),
                owner=user
            )
            
            # Associer les disciplines
            discipline_ids = data.get('disciplines', [])
            if discipline_ids:
                club.disciplines.set(discipline_ids)
            else:
                club.disciplines.add(default_discipline)
            
            # Lier le club au profil
            profile.club = club
            profile.save()
            
            logger.info(f"Club created: {club.name} for user: {user.email}")
            return club
        except Exception as e:
            logger.error(f"Error creating club: {e}", exc_info=True)
            raise
    
    def _create_federation(self, user, profile, data):
        """Crée la fédération"""
        try:
            federation = Federation.objects.create(
                name=data.get('federation_name', f"Fédération de {user.get_full_name()}"),
                country=data.get('country', ''),
                description=data.get('description', '')
            )
            
            # Associer les disciplines
            discipline_ids = data.get('disciplines', [])
            if discipline_ids:
                federation.disciplines.set(discipline_ids)
            
            logger.info(f"Federation created: {federation.name} for user: {user.email}")
            return federation
        except Exception as e:
            logger.error(f"Error creating federation: {e}", exc_info=True)
            raise
    
    def _create_judge_profile(self, user, profile, data):
        """Crée le profil juge"""
        try:
            # Les informations du juge sont stockées dans le profil utilisateur
            # On pourrait créer un modèle Judge séparé si nécessaire
            profile.judge_experience = data.get('experience', '')
            profile.judge_certifications = data.get('certifications', '')
            profile.save()
            
            logger.info(f"Judge profile created for user: {user.email}")
            return profile
        except Exception as e:
            logger.error(f"Error creating judge profile: {e}", exc_info=True)
            raise
    
    def _create_participant_profile(self, user, profile, data):
        """Crée le profil participant"""
        try:
            # Les informations du participant sont stockées dans le profil utilisateur
            profile.birth_date = data.get('birth_date')
            profile.weight = data.get('weight')
            profile.save()
            
            logger.info(f"Participant profile created for user: {user.email}")
            return profile
        except Exception as e:
            logger.error(f"Error creating participant profile: {e}", exc_info=True)
            raise
    
    def _get_dashboard_url(self, role):
        """Retourne l'URL du dashboard selon le rôle"""
        role_dashboards = {
            'club_manager': 'dashboard:club',
            'federation_admin': 'dashboard:admin',
            'judge': 'dashboard:referee',
            'participant': 'dashboard:participant',
            'spectator': 'dashboard:spectator',
        }
        return role_dashboards.get(role, 'dashboard:index')
