# -*- coding: utf-8 -*-
"""
API pour l'onboarding mobile.
Permet aux nouveaux utilisateurs de sélectionner leur rôle et configurer leur compte.
"""

import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class OnboardingStatusView(APIView):
    """
    GET /api/v1/onboarding/status/
    Retourne le statut d'onboarding de l'utilisateur.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            from apps.competitions.models import UserProfile

            profile = UserProfile.objects.filter(user=request.user).first()

            if not profile:
                return Response({
                    'success': True,
                    'needs_onboarding': True,
                    'onboarding_step': 'role_selection',
                    'role': None,
                    'onboarding_completed': False,
                })

            return Response({
                'success': True,
                'needs_onboarding': not getattr(profile, 'onboarding_completed', False),
                'onboarding_step': getattr(profile, 'onboarding_step', 'role_selection'),
                'role': profile.role,
                'onboarding_completed': getattr(profile, 'onboarding_completed', False),
                'organization_id': profile.organization_id if profile.organization else None,
                'organization_name': profile.organization.name if profile.organization else None,
            })

        except Exception as e:
            logger.error(f"Erreur statut onboarding: {e}", exc_info=True)
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AvailableRolesView(APIView):
    """
    GET /api/v1/onboarding/roles/
    Liste des rôles disponibles pour l'onboarding.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Rôles principaux pour l'app mobile (simplifiés)
        roles = [
            {
                'key': 'club_manager',
                'name': str(_('Gestionnaire de club')),
                'description': str(_('Créer et gérer un club, ses membres et ses activités')),
                'icon': 'account-group',
                'color': '#8B5CF6',
                'features': [
                    str(_('Gérer les pratiquants')),
                    str(_('Organiser des événements')),
                    str(_('Suivre les grades et progressions')),
                    str(_('Gérer les inscriptions')),
                ]
            },
            {
                'key': 'federation_admin',
                'name': str(_('Administrateur fédération')),
                'description': str(_('Gérer une fédération et ses clubs affiliés')),
                'icon': 'domain',
                'color': '#10B981',
                'features': [
                    str(_('Superviser les clubs affiliés')),
                    str(_('Organiser des compétitions')),
                    str(_('Gérer les certifications')),
                    str(_('Statistiques globales')),
                ]
            },
            {
                'key': 'coach',
                'name': str(_('Entraîneur / Coach')),
                'description': str(_('Entraîner des pratiquants et suivre leur progression')),
                'icon': 'whistle',
                'color': '#F59E0B',
                'features': [
                    str(_('Suivre les élèves')),
                    str(_('Planifier les entraînements')),
                    str(_('Évaluer les progressions')),
                    str(_('Communiquer avec les pratiquants')),
                ]
            },
            {
                'key': 'participant',
                'name': str(_('Pratiquant / Parent')),
                'description': str(_('Participer aux activités et suivre sa progression')),
                'icon': 'karate',
                'color': '#EF4444',
                'features': [
                    str(_('Voir son profil et grades')),
                    str(_('S\'inscrire aux événements')),
                    str(_('Déclarer les absences')),
                    str(_('Consulter le palmarès')),
                ]
            },
        ]

        return Response({
            'success': True,
            'roles': roles
        })


class SelectRoleView(APIView):
    """
    POST /api/v1/onboarding/select-role/
    Sélectionne le rôle de l'utilisateur.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            from apps.competitions.models import UserProfile

            role = request.data.get('role')

            valid_roles = ['club_manager', 'federation_admin', 'coach', 'participant', 'judge', 'spectator']
            if not role or role not in valid_roles:
                return Response({
                    'success': False,
                    'message': _("Rôle invalide")
                }, status=status.HTTP_400_BAD_REQUEST)

            # Récupérer ou créer le profil
            profile, created = UserProfile.objects.get_or_create(
                user=request.user,
                defaults={'role': role, 'onboarding_step': 'role_selection'}
            )

            if not created:
                profile.role = role

            # Déterminer l'étape suivante
            next_steps = {
                'federation_admin': 'federation_setup',
                'club_manager': 'club_setup',
                'coach': 'coach_setup',
                'judge': 'judge_setup',
                'participant': 'participant_setup',
                'spectator': 'final_setup',
            }

            profile.onboarding_step = next_steps.get(role, 'final_setup')
            profile.save()

            return Response({
                'success': True,
                'message': _("Rôle sélectionné"),
                'role': role,
                'next_step': profile.onboarding_step,
            })

        except Exception as e:
            logger.error(f"Erreur sélection rôle: {e}", exc_info=True)
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreateClubView(APIView):
    """
    POST /api/v1/onboarding/create-club/
    Crée un club pour le gestionnaire.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            from apps.competitions.models import UserProfile, Club, Discipline
            from apps.organizations.models import Organization

            # Vérifier le profil
            profile = UserProfile.objects.filter(user=request.user).first()
            if not profile or profile.role != 'club_manager':
                return Response({
                    'success': False,
                    'message': _("Vous devez être gestionnaire de club")
                }, status=status.HTTP_403_FORBIDDEN)

            # Récupérer les données
            name = request.data.get('name')
            discipline_id = request.data.get('discipline_id')
            city = request.data.get('city', '')
            country = request.data.get('country', 'France')
            description = request.data.get('description', '')

            if not name:
                return Response({
                    'success': False,
                    'message': _("Nom du club requis")
                }, status=status.HTTP_400_BAD_REQUEST)

            # Récupérer la discipline (OBLIGATOIRE)
            if not discipline_id:
                return Response({
                    'success': False,
                    'message': _("Discipline principale requise")
                }, status=status.HTTP_400_BAD_REQUEST)

            discipline = Discipline.objects.filter(id=discipline_id).first()
            if not discipline:
                return Response({
                    'success': False,
                    'message': _("Discipline non trouvée")
                }, status=status.HTTP_400_BAD_REQUEST)

            # Créer l'organisation
            organization = Organization.objects.create(
                name=name,
                organization_type='club',
                city=city,
                country=country,
                description=description,
                created_by=request.user,
                is_active=True,
            )

            # Créer le club
            club = Club.objects.create(
                name=name,
                organization=organization,
                city=city,
                country=country,
                description=description,
                owner=request.user,
            )

            # Associer la discipline si fournie
            if discipline:
                club.disciplines.add(discipline)
                organization.disciplines.add(discipline)

            # Créer le membre de l'organisation (propriétaire)
            from apps.organizations.models import OrganizationMember, OrganizationRole
            OrganizationMember.objects.get_or_create(
                user=request.user,
                organization=organization,
                defaults={
                    'role': OrganizationRole.OWNER,
                    'can_manage_members': True,
                    'can_edit_organization': True,
                    'can_manage_competitions': True,
                }
            )

            # Mettre à jour le profil
            profile.organization = organization
            profile.onboarding_step = 'final_setup'
            profile.onboarding_completed = True
            profile.save()

            return Response({
                'success': True,
                'message': _("Club créé avec succès"),
                'club': {
                    'id': club.id,
                    'name': club.name,
                    'organization_id': organization.id,
                },
                'next_step': 'completed',
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Erreur création club: {e}", exc_info=True)
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreateFederationView(APIView):
    """
    POST /api/v1/onboarding/create-federation/
    Crée une fédération.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            from apps.competitions.models import UserProfile, Federation, Discipline
            from apps.organizations.models import Organization

            # Vérifier le profil
            profile = UserProfile.objects.filter(user=request.user).first()
            if not profile or profile.role != 'federation_admin':
                return Response({
                    'success': False,
                    'message': _("Vous devez être administrateur de fédération")
                }, status=status.HTTP_403_FORBIDDEN)

            # Récupérer les données
            name = request.data.get('name')
            acronym = request.data.get('acronym', '')
            discipline_id = request.data.get('discipline_id')
            country = request.data.get('country', 'France')
            description = request.data.get('description', '')

            if not name:
                return Response({
                    'success': False,
                    'message': _("Nom de la fédération requis")
                }, status=status.HTTP_400_BAD_REQUEST)

            # Récupérer la discipline (OBLIGATOIRE)
            if not discipline_id:
                return Response({
                    'success': False,
                    'message': _("Discipline principale requise")
                }, status=status.HTTP_400_BAD_REQUEST)

            discipline = Discipline.objects.filter(id=discipline_id).first()
            if not discipline:
                return Response({
                    'success': False,
                    'message': _("Discipline non trouvée")
                }, status=status.HTTP_400_BAD_REQUEST)

            # Créer l'organisation
            organization = Organization.objects.create(
                name=name,
                organization_type='national_federation',
                country=country,
                description=description,
                created_by=request.user,
                is_active=True,
            )

            # Créer la fédération
            federation = Federation.objects.create(
                name=name,
                organization=organization,
                country=country,
                description=description,
                owner=request.user,
            )

            # Associer la discipline si fournie
            if discipline:
                federation.disciplines.add(discipline)
                organization.disciplines.add(discipline)

            # Créer le membre de l'organisation (propriétaire)
            from apps.organizations.models import OrganizationMember, OrganizationRole
            OrganizationMember.objects.get_or_create(
                user=request.user,
                organization=organization,
                defaults={
                    'role': OrganizationRole.OWNER,
                    'can_manage_members': True,
                    'can_edit_organization': True,
                    'can_manage_competitions': True,
                }
            )

            # Mettre à jour le profil
            profile.organization = organization
            profile.onboarding_step = 'final_setup'
            profile.onboarding_completed = True
            profile.save()

            return Response({
                'success': True,
                'message': _("Fédération créée avec succès"),
                'federation': {
                    'id': federation.id,
                    'name': federation.name,
                    'organization_id': organization.id,
                },
                'next_step': 'completed',
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Erreur création fédération: {e}", exc_info=True)
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CoachSetupView(APIView):
    """
    POST /api/v1/onboarding/coach-setup/
    Configure le profil coach (rejoindre un club existant).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            from apps.competitions.models import UserProfile, Club

            # Vérifier le profil
            profile = UserProfile.objects.filter(user=request.user).first()
            if not profile or profile.role != 'coach':
                return Response({
                    'success': False,
                    'message': _("Vous devez être entraîneur")
                }, status=status.HTTP_403_FORBIDDEN)

            # Récupérer le club (optionnel - peut rejoindre plus tard)
            club_id = request.data.get('club_id')
            specialization = request.data.get('specialization', '')

            if club_id:
                club = Club.objects.filter(id=club_id).first()
                if club:
                    profile.organization = club.organization

            # Marquer onboarding comme terminé
            profile.onboarding_step = 'final_setup'
            profile.onboarding_completed = True
            profile.save()

            return Response({
                'success': True,
                'message': _("Profil coach configuré"),
                'next_step': 'completed',
            })

        except Exception as e:
            logger.error(f"Erreur setup coach: {e}", exc_info=True)
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CompleteOnboardingView(APIView):
    """
    POST /api/v1/onboarding/complete/
    Marque l'onboarding comme terminé.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            from apps.competitions.models import UserProfile

            profile = UserProfile.objects.filter(user=request.user).first()
            if not profile:
                profile = UserProfile.objects.create(
                    user=request.user,
                    role='participant',
                )

            profile.onboarding_step = 'completed'
            profile.onboarding_completed = True
            profile.save()

            return Response({
                'success': True,
                'message': _("Onboarding terminé"),
                'role': profile.role,
                'organization_id': profile.organization_id if profile.organization else None,
            })

        except Exception as e:
            logger.error(f"Erreur completion onboarding: {e}", exc_info=True)
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DisciplinesListView(APIView):
    """
    GET /api/v1/onboarding/disciplines/
    Liste des disciplines disponibles.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            from apps.competitions.models import Discipline

            disciplines = Discipline.objects.filter(is_active=True).order_by('name')

            return Response({
                'success': True,
                'disciplines': [
                    {
                        'id': d.id,
                        'name': d.name,
                        'slug': d.slug if hasattr(d, 'slug') else '',
                    }
                    for d in disciplines
                ]
            })

        except Exception as e:
            logger.error(f"Erreur liste disciplines: {e}", exc_info=True)
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
