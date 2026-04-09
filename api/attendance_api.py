# -*- coding: utf-8 -*-
"""
API pour la gestion des présences et déclarations d'absence.
Permet aux pratiquants/parents de déclarer des absences et aux instructeurs de les gérer.
"""

import logging
from datetime import date, timedelta
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django.utils import timezone

logger = logging.getLogger(__name__)


class TrainingSlotsListView(APIView):
    """
    GET /api/v1/attendance/training-slots/
    Liste des créneaux d'entraînement disponibles pour le pratiquant.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            from apps.competitions.models import UserProfile, Practitioner, TrainingSlot

            # Récupérer le profil utilisateur
            user_profile = UserProfile.objects.filter(user=request.user).first()
            user_organization = user_profile.organization if user_profile else None

            # Récupérer le practitioner associé ou les enfants
            practitioner_id = request.query_params.get('practitioner_id')

            if practitioner_id:
                # Vérifier que l'utilisateur a accès à ce pratiquant
                practitioner = get_object_or_404(Practitioner, id=practitioner_id)

                # Vérifier les permissions:
                # - L'utilisateur est le pratiquant lui-même
                # - Ou l'utilisateur est dans la même organisation
                is_own_practitioner = practitioner.user == request.user
                same_organization = user_organization and practitioner.organization and user_organization == practitioner.organization

                if not is_own_practitioner and not same_organization:
                    return Response({
                        'success': False,
                        'message': _("Accès non autorisé")
                    }, status=status.HTTP_403_FORBIDDEN)

                organization = practitioner.organization
            else:
                # Si pas de practitioner_id, essayer de récupérer l'org de l'utilisateur
                # ou de son propre practitioner
                if user_organization:
                    organization = user_organization
                else:
                    own_practitioner = Practitioner.objects.filter(user=request.user).first()
                    organization = own_practitioner.organization if own_practitioner else None

            if not organization:
                return Response({
                    'success': True,
                    'training_slots': []  # Pas d'erreur, juste pas de créneaux
                })

            # Récupérer les créneaux actifs de l'organisation
            # On récupère les créneaux du club associé à l'organisation
            slots = TrainingSlot.objects.filter(
                club__organization=organization,
                is_active=True
            ).select_related('club', 'discipline', 'instructor').order_by('day_of_week', 'start_time')

            slots_data = []
            day_names = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']

            for slot in slots:
                slots_data.append({
                    'id': slot.id,
                    'name': slot.name,
                    'day_of_week': slot.day_of_week,
                    'day_name': day_names[slot.day_of_week],
                    'start_time': slot.start_time.strftime('%H:%M'),
                    'end_time': slot.end_time.strftime('%H:%M'),
                    'level': slot.level,
                    'level_display': slot.get_level_display(),
                    'location': slot.location,
                    'instructor_name': slot.instructor.get_full_name() if slot.instructor else None,
                    'discipline': slot.discipline.name if slot.discipline else None,
                    'club_name': slot.club.name if slot.club else None,
                })

            return Response({
                'success': True,
                'training_slots': slots_data
            })

        except Exception as e:
            logger.error(f"Erreur lors de la récupération des créneaux: {e}", exc_info=True)
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeclarationListCreateView(APIView):
    """
    GET /api/v1/attendance/declarations/
    Liste les déclarations de l'utilisateur (ou de ses enfants).

    POST /api/v1/attendance/declarations/
    Crée une nouvelle déclaration d'absence.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            from apps.competitions.models import UserProfile, Practitioner, AbsenceDeclaration

            user_profile = UserProfile.objects.filter(user=request.user).first()
            user_organization = user_profile.organization if user_profile else None

            # Filtres
            practitioner_id = request.query_params.get('practitioner_id')
            status_filter = request.query_params.get('status')
            upcoming = request.query_params.get('upcoming', 'false').lower() == 'true'

            # Récupérer les pratiquants accessibles par l'utilisateur
            # Si l'utilisateur a une organisation, filtrer par cette org
            # Sinon, juste récupérer les pratiquants liés à l'utilisateur
            if user_organization:
                practitioner = Practitioner.objects.filter(
                    user=request.user,
                    organization=user_organization
                ).first()
            else:
                practitioner = Practitioner.objects.filter(user=request.user).first()

            # Base query: déclarations créées par l'utilisateur ou pour ses pratiquants
            declarations = AbsenceDeclaration.objects.filter(
                Q(declared_by=request.user) |
                Q(practitioner__user=request.user)
            )

            # Filtrer par pratiquant spécifique
            if practitioner_id:
                declarations = declarations.filter(practitioner_id=practitioner_id)

            # Filtrer par statut
            if status_filter:
                declarations = declarations.filter(status=status_filter)

            # Filtrer les déclarations à venir (date >= aujourd'hui)
            if upcoming:
                declarations = declarations.filter(date__gte=date.today())

            declarations = declarations.select_related(
                'practitioner', 'training_slot', 'declared_by', 'acknowledged_by'
            ).order_by('-date', '-declared_at')[:50]

            declarations_data = []
            for decl in declarations:
                declarations_data.append(self._serialize_declaration(decl))

            return Response({
                'success': True,
                'declarations': declarations_data
            })

        except Exception as e:
            logger.error(f"Erreur lors de la récupération des déclarations: {e}", exc_info=True)
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            from apps.competitions.models import (
                UserProfile, Practitioner, TrainingSlot, AbsenceDeclaration, Notification
            )

            user_profile = UserProfile.objects.filter(user=request.user).first()

            # Récupérer les données
            practitioner_id = request.data.get('practitioner_id')
            declaration_type = request.data.get('declaration_type', 'absence')
            date_str = request.data.get('date')
            date_end_str = request.data.get('date_end')
            training_slot_id = request.data.get('training_slot_id')
            reason = request.data.get('reason', '')
            reason_category = request.data.get('reason_category')

            # Validation
            if not practitioner_id:
                return Response({
                    'success': False,
                    'message': _("Pratiquant requis")
                }, status=status.HTTP_400_BAD_REQUEST)

            if not date_str:
                return Response({
                    'success': False,
                    'message': _("Date requise")
                }, status=status.HTTP_400_BAD_REQUEST)

            # Récupérer le pratiquant
            practitioner = get_object_or_404(Practitioner, id=practitioner_id)

            # Récupérer l'organisation (priorité: user_profile, puis practitioner)
            user_organization = user_profile.organization if user_profile else None
            practitioner_organization = practitioner.organization

            # Vérifier les permissions:
            # - L'utilisateur peut déclarer pour lui-même (practitioner.user == request.user)
            # - Ou si l'utilisateur est dans la même organisation que le pratiquant
            is_own_practitioner = practitioner.user == request.user
            same_organization = user_organization and practitioner_organization and user_organization == practitioner_organization

            if not is_own_practitioner and not same_organization:
                return Response({
                    'success': False,
                    'message': _("Accès non autorisé")
                }, status=status.HTTP_403_FORBIDDEN)

            # Utiliser l'organisation du pratiquant pour les notifications
            organization = practitioner_organization or user_organization

            # Parser les dates
            try:
                from datetime import datetime
                declaration_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                declaration_date_end = None
                if date_end_str:
                    declaration_date_end = datetime.strptime(date_end_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({
                    'success': False,
                    'message': _("Format de date invalide (utilisez YYYY-MM-DD)")
                }, status=status.HTTP_400_BAD_REQUEST)

            # Récupérer le créneau si spécifié
            training_slot = None
            if training_slot_id:
                training_slot = TrainingSlot.objects.filter(id=training_slot_id).first()

            # Créer la déclaration
            declaration = AbsenceDeclaration.objects.create(
                practitioner=practitioner,
                declaration_type=declaration_type,
                date=declaration_date,
                date_end=declaration_date_end,
                training_slot=training_slot,
                reason=reason,
                reason_category=reason_category,
                declared_by=request.user
            )

            # Envoyer une notification aux instructeurs
            if organization:
                self._notify_instructors(declaration, organization)

            return Response({
                'success': True,
                'message': _("Déclaration enregistrée"),
                'declaration': self._serialize_declaration(declaration)
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Erreur lors de la création de la déclaration: {e}", exc_info=True)
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _serialize_declaration(self, decl):
        """Sérialise une déclaration d'absence."""
        return {
            'uuid': str(decl.uuid),
            'id': decl.id,
            'practitioner': {
                'id': decl.practitioner.id,
                'full_name': decl.practitioner.full_name,
                'first_name': decl.practitioner.first_name,
                'last_name': decl.practitioner.last_name,
            },
            'declaration_type': decl.declaration_type,
            'declaration_type_display': decl.get_declaration_type_display(),
            'date': decl.date.isoformat(),
            'date_end': decl.date_end.isoformat() if decl.date_end else None,
            'is_multi_day': decl.is_multi_day,
            'training_slot': {
                'id': decl.training_slot.id,
                'name': decl.training_slot.name,
                'day_of_week': decl.training_slot.day_of_week,
                'start_time': decl.training_slot.start_time.strftime('%H:%M'),
                'end_time': decl.training_slot.end_time.strftime('%H:%M'),
            } if decl.training_slot else None,
            'reason': decl.reason,
            'reason_category': decl.reason_category,
            'reason_category_display': decl.get_reason_category_display() if decl.reason_category else None,
            'declared_by': {
                'id': decl.declared_by.id,
                'name': decl.declared_by.get_full_name(),
            } if decl.declared_by else None,
            'declared_at': decl.declared_at.isoformat() if decl.declared_at else None,
            'status': decl.status,
            'status_display': decl.get_status_display(),
            'acknowledged_by': {
                'id': decl.acknowledged_by.id,
                'name': decl.acknowledged_by.get_full_name(),
            } if decl.acknowledged_by else None,
            'acknowledged_at': decl.acknowledged_at.isoformat() if decl.acknowledged_at else None,
            'instructor_note': decl.instructor_note,
        }

    def _notify_instructors(self, declaration, organization):
        """Envoie une notification aux instructeurs du club."""
        try:
            from apps.competitions.models import Notification, UserProfile

            # Trouver les instructeurs (club_manager, coach)
            instructor_profiles = UserProfile.objects.filter(
                organization=organization,
                role__in=['club_manager', 'coach', 'admin']
            ).select_related('user')

            type_display = declaration.get_declaration_type_display()
            practitioner_name = declaration.practitioner.full_name

            for profile in instructor_profiles:
                if profile.user and profile.user != declaration.declared_by:
                    Notification.objects.create(
                        recipient=profile.user,
                        title=_("Nouvelle déclaration d'absence"),
                        message=f"{practitioner_name} - {type_display} le {declaration.date.strftime('%d/%m/%Y')}",
                        notification_type='absence_declaration',
                        organization=organization,
                        action_url=f'/attendance/declarations/{declaration.uuid}/'
                    )
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi des notifications: {e}")


class DeclarationDetailView(APIView):
    """
    GET /api/v1/attendance/declarations/<uuid>/
    Détail d'une déclaration.

    DELETE /api/v1/attendance/declarations/<uuid>/
    Annule une déclaration (seulement si en attente).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, declaration_uuid):
        try:
            from apps.competitions.models import AbsenceDeclaration

            declaration = get_object_or_404(AbsenceDeclaration, uuid=declaration_uuid)

            # Vérifier les permissions
            if declaration.declared_by != request.user and declaration.practitioner.user != request.user:
                # Vérifier si l'utilisateur est instructeur
                from apps.competitions.models import UserProfile
                user_profile = UserProfile.objects.filter(user=request.user).first()
                if not user_profile or user_profile.role not in ['club_manager', 'coach', 'admin']:
                    return Response({
                        'success': False,
                        'message': _("Accès non autorisé")
                    }, status=status.HTTP_403_FORBIDDEN)

            return Response({
                'success': True,
                'declaration': DeclarationListCreateView()._serialize_declaration(declaration)
            })

        except Exception as e:
            logger.error(f"Erreur: {e}", exc_info=True)
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, declaration_uuid):
        try:
            from apps.competitions.models import AbsenceDeclaration

            declaration = get_object_or_404(AbsenceDeclaration, uuid=declaration_uuid)

            # Vérifier les permissions (créateur uniquement)
            if declaration.declared_by != request.user:
                return Response({
                    'success': False,
                    'message': _("Seul le créateur peut annuler cette déclaration")
                }, status=status.HTTP_403_FORBIDDEN)

            # Seulement si en attente
            if declaration.status != 'pending':
                return Response({
                    'success': False,
                    'message': _("Seules les déclarations en attente peuvent être annulées")
                }, status=status.HTTP_400_BAD_REQUEST)

            declaration.delete()

            return Response({
                'success': True,
                'message': _("Déclaration annulée")
            })

        except Exception as e:
            logger.error(f"Erreur: {e}", exc_info=True)
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PendingDeclarationsView(APIView):
    """
    GET /api/v1/attendance/declarations/pending/
    Liste les déclarations en attente pour les instructeurs.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            from apps.competitions.models import UserProfile, AbsenceDeclaration

            user_profile = UserProfile.objects.filter(user=request.user).first()
            if not user_profile or not user_profile.organization:
                return Response({
                    'success': False,
                    'message': _("Aucune organisation associée")
                }, status=status.HTTP_400_BAD_REQUEST)

            # Vérifier le rôle instructeur
            allowed_roles = ['club_manager', 'coach', 'admin', 'federation_admin']
            if not (request.user.is_staff or user_profile.role in allowed_roles):
                return Response({
                    'success': False,
                    'message': _("Permissions insuffisantes")
                }, status=status.HTTP_403_FORBIDDEN)

            # Récupérer les déclarations en attente de l'organisation
            declarations = AbsenceDeclaration.objects.filter(
                practitioner__organization=user_profile.organization,
                status='pending',
                date__gte=date.today() - timedelta(days=7)  # 7 jours max en arrière
            ).select_related(
                'practitioner', 'training_slot', 'declared_by'
            ).order_by('date', 'declared_at')

            declarations_data = []
            for decl in declarations:
                declarations_data.append(DeclarationListCreateView()._serialize_declaration(decl))

            return Response({
                'success': True,
                'pending_count': len(declarations_data),
                'declarations': declarations_data
            })

        except Exception as e:
            logger.error(f"Erreur: {e}", exc_info=True)
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AcknowledgeDeclarationView(APIView):
    """
    POST /api/v1/attendance/declarations/<uuid>/acknowledge/
    Valide ou refuse une déclaration.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, declaration_uuid):
        try:
            from apps.competitions.models import UserProfile, AbsenceDeclaration, Notification

            user_profile = UserProfile.objects.filter(user=request.user).first()
            if not user_profile or not user_profile.organization:
                return Response({
                    'success': False,
                    'message': _("Aucune organisation associée")
                }, status=status.HTTP_400_BAD_REQUEST)

            # Vérifier le rôle instructeur
            allowed_roles = ['club_manager', 'coach', 'admin', 'federation_admin']
            if not (request.user.is_staff or user_profile.role in allowed_roles):
                return Response({
                    'success': False,
                    'message': _("Permissions insuffisantes")
                }, status=status.HTTP_403_FORBIDDEN)

            declaration = get_object_or_404(AbsenceDeclaration, uuid=declaration_uuid)

            # Vérifier que c'est dans la même organisation
            if declaration.practitioner.organization != user_profile.organization:
                return Response({
                    'success': False,
                    'message': _("Accès non autorisé")
                }, status=status.HTTP_403_FORBIDDEN)

            # Récupérer l'action (acknowledge ou reject)
            action = request.data.get('action', 'acknowledge')
            note = request.data.get('note', '')

            if action == 'reject':
                declaration.reject(request.user, note)
                status_msg = _("Déclaration refusée")
            else:
                declaration.acknowledge(request.user, note)
                status_msg = _("Déclaration prise en compte")

            # Notifier le déclarant
            if declaration.declared_by:
                Notification.objects.create(
                    recipient=declaration.declared_by,
                    title=_("Déclaration mise à jour"),
                    message=f"{declaration.practitioner.full_name} - {declaration.get_status_display()}",
                    notification_type='absence_status',
                    organization=user_profile.organization
                )

            return Response({
                'success': True,
                'message': status_msg,
                'declaration': DeclarationListCreateView()._serialize_declaration(declaration)
            })

        except Exception as e:
            logger.error(f"Erreur: {e}", exc_info=True)
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RollCallSessionsView(APIView):
    """
    GET /api/v1/attendance/sessions/<date>/
    Liste les séances d'entraînement pour une date donnée.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, session_date):
        try:
            from apps.competitions.models import UserProfile, TrainingSlot, TrainingSession
            from datetime import datetime

            user_profile = UserProfile.objects.filter(user=request.user).first()
            if not user_profile or not user_profile.organization:
                return Response({
                    'success': False,
                    'message': _("Aucune organisation associée")
                }, status=status.HTTP_400_BAD_REQUEST)

            # Vérifier le rôle instructeur
            allowed_roles = ['club_manager', 'coach', 'admin', 'federation_admin']
            if not (request.user.is_staff or user_profile.role in allowed_roles):
                return Response({
                    'success': False,
                    'message': _("Permissions insuffisantes")
                }, status=status.HTTP_403_FORBIDDEN)

            # Parser la date
            try:
                target_date = datetime.strptime(session_date, '%Y-%m-%d').date()
            except ValueError:
                return Response({
                    'success': False,
                    'message': _("Format de date invalide")
                }, status=status.HTTP_400_BAD_REQUEST)

            # Récupérer le jour de la semaine (0=Lundi)
            day_of_week = target_date.weekday()

            # Récupérer les créneaux du jour
            slots = TrainingSlot.objects.filter(
                club__organization=user_profile.organization,
                day_of_week=day_of_week,
                is_active=True
            ).select_related('club', 'discipline', 'instructor')

            sessions_data = []
            for slot in slots:
                # Vérifier si une session existe déjà
                session = TrainingSession.objects.filter(
                    training_slot=slot,
                    date=target_date
                ).first()

                # Compter les absences déclarées
                absence_count = slot.absence_declarations.filter(
                    Q(date=target_date) |
                    (Q(date__lte=target_date) & Q(date_end__gte=target_date))
                ).count()

                sessions_data.append({
                    'slot_id': slot.id,
                    'slot_name': slot.name,
                    'start_time': slot.start_time.strftime('%H:%M'),
                    'end_time': slot.end_time.strftime('%H:%M'),
                    'location': slot.location,
                    'instructor_name': slot.instructor.get_full_name() if slot.instructor else None,
                    'session_exists': session is not None,
                    'session_id': session.id if session else None,
                    'is_cancelled': session.is_cancelled if session else False,
                    'declared_absences': absence_count,
                })

            return Response({
                'success': True,
                'date': target_date.isoformat(),
                'day_name': ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'][day_of_week],
                'sessions': sessions_data
            })

        except Exception as e:
            logger.error(f"Erreur: {e}", exc_info=True)
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RollCallView(APIView):
    """
    GET /api/v1/attendance/sessions/<date>/<slot_id>/roll-call/
    Récupère la feuille d'appel pour une séance.

    POST /api/v1/attendance/sessions/<date>/<slot_id>/roll-call/
    Enregistre l'appel.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, session_date, slot_id):
        try:
            from apps.competitions.models import (
                UserProfile, TrainingSlot, TrainingSession, Practitioner,
                Attendance, AbsenceDeclaration
            )
            from datetime import datetime

            user_profile = UserProfile.objects.filter(user=request.user).first()
            if not user_profile or not user_profile.organization:
                return Response({
                    'success': False,
                    'message': _("Aucune organisation associée")
                }, status=status.HTTP_400_BAD_REQUEST)

            # Vérifier le rôle instructeur
            allowed_roles = ['club_manager', 'coach', 'admin', 'federation_admin']
            if not (request.user.is_staff or user_profile.role in allowed_roles):
                return Response({
                    'success': False,
                    'message': _("Permissions insuffisantes")
                }, status=status.HTTP_403_FORBIDDEN)

            # Parser la date
            try:
                target_date = datetime.strptime(session_date, '%Y-%m-%d').date()
            except ValueError:
                return Response({
                    'success': False,
                    'message': _("Format de date invalide")
                }, status=status.HTTP_400_BAD_REQUEST)

            # Récupérer le créneau
            slot = get_object_or_404(TrainingSlot, id=slot_id)

            # Vérifier que c'est dans la même organisation
            if slot.club.organization != user_profile.organization:
                return Response({
                    'success': False,
                    'message': _("Accès non autorisé")
                }, status=status.HTTP_403_FORBIDDEN)

            # Récupérer ou créer la session
            session, created = TrainingSession.objects.get_or_create(
                training_slot=slot,
                date=target_date,
                defaults={'actual_instructor': request.user}
            )

            # Récupérer les pratiquants du club
            practitioners = Practitioner.objects.filter(
                organization=user_profile.organization,
                is_active=True
            ).order_by('last_name', 'first_name')

            # Récupérer les présences existantes
            attendances = {
                a.practitioner_id: a
                for a in Attendance.objects.filter(session=session)
            }

            # Récupérer les déclarations d'absence pour cette date/ce créneau
            declarations = {
                d.practitioner_id: d
                for d in AbsenceDeclaration.objects.filter(
                    Q(date=target_date) |
                    (Q(date__lte=target_date) & Q(date_end__gte=target_date))
                ).filter(
                    Q(training_slot=slot) | Q(training_slot__isnull=True)
                )
            }

            roll_call_data = []
            for pract in practitioners:
                attendance = attendances.get(pract.id)
                declaration = declarations.get(pract.id)

                status_value = 'pending'
                if attendance:
                    status_value = attendance.status
                elif declaration:
                    if declaration.declaration_type == 'absence':
                        status_value = 'excused'
                    elif declaration.declaration_type == 'late':
                        status_value = 'late'

                roll_call_data.append({
                    'practitioner_id': pract.id,
                    'full_name': pract.full_name,
                    'first_name': pract.first_name,
                    'last_name': pract.last_name,
                    'current_grade': pract.current_grade.name if hasattr(pract, 'current_grade') and pract.current_grade else None,
                    'status': status_value,
                    'has_declaration': declaration is not None,
                    'declaration': {
                        'type': declaration.declaration_type,
                        'type_display': declaration.get_declaration_type_display(),
                        'reason': declaration.reason,
                        'reason_category_display': declaration.get_reason_category_display() if declaration.reason_category else None,
                    } if declaration else None,
                    'arrival_time': attendance.arrival_time.strftime('%H:%M') if attendance and attendance.arrival_time else None,
                    'notes': attendance.notes if attendance else '',
                })

            return Response({
                'success': True,
                'session': {
                    'id': session.id,
                    'date': target_date.isoformat(),
                    'slot_name': slot.name,
                    'start_time': slot.start_time.strftime('%H:%M'),
                    'end_time': slot.end_time.strftime('%H:%M'),
                    'is_cancelled': session.is_cancelled,
                },
                'roll_call': roll_call_data,
                'summary': {
                    'total': len(roll_call_data),
                    'present': sum(1 for r in roll_call_data if r['status'] == 'present'),
                    'absent': sum(1 for r in roll_call_data if r['status'] in ['absent', 'excused']),
                    'late': sum(1 for r in roll_call_data if r['status'] == 'late'),
                    'pending': sum(1 for r in roll_call_data if r['status'] == 'pending'),
                }
            })

        except Exception as e:
            logger.error(f"Erreur: {e}", exc_info=True)
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, session_date, slot_id):
        try:
            from apps.competitions.models import (
                UserProfile, TrainingSlot, TrainingSession, Attendance
            )
            from datetime import datetime

            user_profile = UserProfile.objects.filter(user=request.user).first()
            if not user_profile or not user_profile.organization:
                return Response({
                    'success': False,
                    'message': _("Aucune organisation associée")
                }, status=status.HTTP_400_BAD_REQUEST)

            # Vérifier le rôle instructeur
            allowed_roles = ['club_manager', 'coach', 'admin', 'federation_admin']
            if not (request.user.is_staff or user_profile.role in allowed_roles):
                return Response({
                    'success': False,
                    'message': _("Permissions insuffisantes")
                }, status=status.HTTP_403_FORBIDDEN)

            # Parser la date
            try:
                target_date = datetime.strptime(session_date, '%Y-%m-%d').date()
            except ValueError:
                return Response({
                    'success': False,
                    'message': _("Format de date invalide")
                }, status=status.HTTP_400_BAD_REQUEST)

            # Récupérer le créneau
            slot = get_object_or_404(TrainingSlot, id=slot_id)

            # Vérifier que c'est dans la même organisation
            if slot.club.organization != user_profile.organization:
                return Response({
                    'success': False,
                    'message': _("Accès non autorisé")
                }, status=status.HTTP_403_FORBIDDEN)

            # Récupérer ou créer la session
            session, _ = TrainingSession.objects.get_or_create(
                training_slot=slot,
                date=target_date,
                defaults={'actual_instructor': request.user}
            )

            # Récupérer les données d'appel
            attendances_data = request.data.get('attendances', [])

            for att_data in attendances_data:
                practitioner_id = att_data.get('practitioner_id')
                status_value = att_data.get('status', 'present')
                arrival_time_str = att_data.get('arrival_time')
                notes = att_data.get('notes', '')

                # Parser l'heure d'arrivée si fournie
                arrival_time = None
                if arrival_time_str:
                    try:
                        arrival_time = datetime.strptime(arrival_time_str, '%H:%M').time()
                    except ValueError:
                        pass

                # Créer ou mettre à jour la présence
                Attendance.objects.update_or_create(
                    session=session,
                    practitioner_id=practitioner_id,
                    defaults={
                        'status': status_value,
                        'arrival_time': arrival_time,
                        'notes': notes,
                        'recorded_by': request.user
                    }
                )

            return Response({
                'success': True,
                'message': _("Appel enregistré"),
                'attendances_count': len(attendances_data)
            })

        except Exception as e:
            logger.error(f"Erreur: {e}", exc_info=True)
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AttendanceStatisticsView(APIView):
    """
    GET /api/v1/attendance/statistics/
    Statistiques globales de présence.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            from apps.competitions.models import (
                UserProfile, TrainingSession, Attendance, AbsenceDeclaration
            )
            from datetime import datetime
            from django.db.models import Count

            user_profile = UserProfile.objects.filter(user=request.user).first()
            if not user_profile or not user_profile.organization:
                return Response({
                    'success': False,
                    'message': _("Aucune organisation associée")
                }, status=status.HTTP_400_BAD_REQUEST)

            # Vérifier le rôle instructeur
            allowed_roles = ['club_manager', 'coach', 'admin', 'federation_admin']
            if not (request.user.is_staff or user_profile.role in allowed_roles):
                return Response({
                    'success': False,
                    'message': _("Permissions insuffisantes")
                }, status=status.HTTP_403_FORBIDDEN)

            # Période par défaut: dernier mois
            period = request.query_params.get('period', 'month')
            today = date.today()

            if period == 'week':
                start_date = today - timedelta(days=7)
            elif period == 'month':
                start_date = today - timedelta(days=30)
            elif period == 'year':
                start_date = today - timedelta(days=365)
            else:
                start_date = today - timedelta(days=30)

            # Sessions dans la période
            sessions = TrainingSession.objects.filter(
                training_slot__club__organization=user_profile.organization,
                date__gte=start_date,
                date__lte=today,
                is_cancelled=False
            )

            total_sessions = sessions.count()

            # Statistiques de présence
            attendances = Attendance.objects.filter(
                session__in=sessions
            )

            attendance_stats = attendances.values('status').annotate(count=Count('status'))
            stats_dict = {s['status']: s['count'] for s in attendance_stats}

            total_attendances = sum(stats_dict.values())
            present_count = stats_dict.get('present', 0)
            absent_count = stats_dict.get('absent', 0)
            excused_count = stats_dict.get('excused', 0)
            late_count = stats_dict.get('late', 0)

            attendance_rate = (present_count / total_attendances * 100) if total_attendances > 0 else 0

            # Déclarations
            declarations = AbsenceDeclaration.objects.filter(
                practitioner__organization=user_profile.organization,
                date__gte=start_date
            )

            declarations_count = declarations.count()
            pending_declarations = declarations.filter(status='pending').count()

            # Alertes: pratiquants avec plus de 3 absences
            from apps.competitions.models import Practitioner
            frequent_absences = Attendance.objects.filter(
                session__in=sessions,
                status__in=['absent', 'excused']
            ).values('practitioner').annotate(
                absence_count=Count('id')
            ).filter(absence_count__gte=3).order_by('-absence_count')[:5]

            alerts = []
            for fa in frequent_absences:
                pract = Practitioner.objects.filter(id=fa['practitioner']).first()
                if pract:
                    alerts.append({
                        'practitioner_id': pract.id,
                        'practitioner_name': pract.full_name,
                        'absence_count': fa['absence_count'],
                    })

            return Response({
                'success': True,
                'period': period,
                'start_date': start_date.isoformat(),
                'end_date': today.isoformat(),
                'statistics': {
                    'total_sessions': total_sessions,
                    'total_attendances': total_attendances,
                    'attendance_rate': round(attendance_rate, 1),
                    'present': present_count,
                    'absent': absent_count,
                    'excused': excused_count,
                    'late': late_count,
                },
                'declarations': {
                    'total': declarations_count,
                    'pending': pending_declarations,
                },
                'alerts': alerts
            })

        except Exception as e:
            logger.error(f"Erreur: {e}", exc_info=True)
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PractitionerAttendanceView(APIView):
    """
    GET /api/v1/attendance/practitioners/<id>/
    Statistiques de présence pour un pratiquant.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, practitioner_id):
        try:
            from apps.competitions.models import (
                UserProfile, Practitioner, Attendance, AbsenceDeclaration
            )

            user_profile = UserProfile.objects.filter(user=request.user).first()
            if not user_profile or not user_profile.organization:
                return Response({
                    'success': False,
                    'message': _("Aucune organisation associée")
                }, status=status.HTTP_400_BAD_REQUEST)

            practitioner = get_object_or_404(Practitioner, id=practitioner_id)

            # Vérifier les permissions
            if practitioner.organization != user_profile.organization:
                # Si pas dans la même org, vérifier si c'est le propre pratiquant
                if practitioner.user != request.user:
                    return Response({
                        'success': False,
                        'message': _("Accès non autorisé")
                    }, status=status.HTTP_403_FORBIDDEN)

            # Période: dernier mois
            today = date.today()
            start_date = today - timedelta(days=30)

            # Présences
            attendances = Attendance.objects.filter(
                practitioner=practitioner,
                session__date__gte=start_date
            ).select_related('session', 'session__training_slot')

            attendance_stats = attendances.values('status').annotate(count=Count('status'))
            stats_dict = {s['status']: s['count'] for s in attendance_stats}

            total = sum(stats_dict.values())
            present = stats_dict.get('present', 0)
            rate = (present / total * 100) if total > 0 else 0

            # Historique récent
            history = []
            for att in attendances.order_by('-session__date')[:10]:
                history.append({
                    'date': att.session.date.isoformat(),
                    'slot_name': att.session.training_slot.name,
                    'status': att.status,
                    'status_display': att.get_status_display(),
                })

            # Déclarations récentes
            declarations = AbsenceDeclaration.objects.filter(
                practitioner=practitioner,
                date__gte=start_date
            ).order_by('-date')[:5]

            declarations_data = [
                DeclarationListCreateView()._serialize_declaration(d)
                for d in declarations
            ]

            return Response({
                'success': True,
                'practitioner': {
                    'id': practitioner.id,
                    'full_name': practitioner.full_name,
                },
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': today.isoformat(),
                },
                'statistics': {
                    'total_sessions': total,
                    'present': present,
                    'absent': stats_dict.get('absent', 0),
                    'excused': stats_dict.get('excused', 0),
                    'late': stats_dict.get('late', 0),
                    'attendance_rate': round(rate, 1),
                },
                'recent_history': history,
                'recent_declarations': declarations_data
            })

        except Exception as e:
            logger.error(f"Erreur: {e}", exc_info=True)
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
