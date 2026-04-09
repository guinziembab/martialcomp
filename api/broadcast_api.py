# -*- coding: utf-8 -*-
"""
API pour les groupes de diffusion (Broadcast Groups).
Permet aux instructeurs de créer des groupes et d'envoyer des messages.
"""

import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404

logger = logging.getLogger(__name__)


class BroadcastGroupPreviewView(APIView):
    """
    POST /api/v1/broadcast/groups/preview/
    Prévisualise les membres qui correspondent aux critères avant de créer un groupe.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            from apps.competitions.models import UserProfile, Practitioner
            from datetime import date, timedelta

            # Vérifier les permissions
            user_profile = UserProfile.objects.filter(user=request.user).first()
            if not user_profile or not user_profile.organization:
                return Response({
                    'success': False,
                    'message': _("Aucune organisation associée")
                }, status=status.HTTP_400_BAD_REQUEST)

            # Vérifier le rôle
            allowed_roles = ['club_manager', 'coach', 'admin', 'federation_admin']
            if not (request.user.is_staff or user_profile.role in allowed_roles):
                return Response({
                    'success': False,
                    'message': _("Permissions insuffisantes")
                }, status=status.HTTP_403_FORBIDDEN)

            # Récupérer les critères de filtrage
            target_type = request.data.get('target_type', 'criteria')
            age_category = request.data.get('age_category', 'all')
            min_age = request.data.get('min_age')
            max_age = request.data.get('max_age')
            gender_filter = request.data.get('gender_filter', 'all')
            min_grade_level = request.data.get('min_grade_level')
            max_grade_level = request.data.get('max_grade_level')
            grade_ids = request.data.get('grade_ids', [])
            member_ids = request.data.get('member_ids', [])

            # Commencer avec tous les pratiquants de l'organisation
            queryset = Practitioner.objects.filter(
                organization=user_profile.organization,
                is_active=True
            )

            if target_type == 'manual':
                # Pour la sélection manuelle, si des IDs sont fournis
                if member_ids:
                    queryset = queryset.filter(id__in=member_ids)
            else:
                # Filtrage par critères
                today = date.today()

                # Filtre par catégorie d'âge
                if age_category == 'enfants':
                    # 6-12 ans
                    min_birth = today - timedelta(days=12*365)
                    max_birth = today - timedelta(days=6*365)
                    queryset = queryset.filter(birth_date__gte=min_birth, birth_date__lte=max_birth)
                elif age_category == 'juniors':
                    # 13-17 ans
                    min_birth = today - timedelta(days=17*365)
                    max_birth = today - timedelta(days=13*365)
                    queryset = queryset.filter(birth_date__gte=min_birth, birth_date__lte=max_birth)
                elif age_category == 'adultes':
                    # 18+ ans
                    max_birth = today - timedelta(days=18*365)
                    queryset = queryset.filter(birth_date__lte=max_birth)
                elif min_age or max_age:
                    # Personnalisé
                    if min_age:
                        max_birth = today - timedelta(days=int(min_age)*365)
                        queryset = queryset.filter(birth_date__lte=max_birth)
                    if max_age:
                        min_birth = today - timedelta(days=int(max_age)*365)
                        queryset = queryset.filter(birth_date__gte=min_birth)

                # Filtre par genre
                if gender_filter and gender_filter != 'all':
                    queryset = queryset.filter(gender=gender_filter)

                # Filtre par grades spécifiques
                if grade_ids:
                    queryset = queryset.filter(grade_id__in=grade_ids)
                else:
                    # Filtre par niveau de grade
                    if min_grade_level:
                        queryset = queryset.filter(grade__level__gte=min_grade_level)
                    if max_grade_level:
                        queryset = queryset.filter(grade__level__lte=max_grade_level)

            # Compter le total
            count = queryset.count()

            # Récupérer un échantillon de 5 membres
            sample_members = queryset[:5]
            sample = [{
                'uuid': str(p.id),
                'id': p.id,
                'full_name': p.full_name,
                'first_name': p.first_name,
                'last_name': p.last_name,
                'grade_name': p.grade.name if p.grade else None,
                'grade_color': getattr(p.grade, 'color', None) if p.grade else None,
            } for p in sample_members]

            return Response({
                'success': True,
                'count': count,
                'sample': sample
            })

        except Exception as e:
            logger.exception("Erreur lors de la prévisualisation des membres")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BroadcastGroupListCreateView(APIView):
    """
    GET /api/v1/broadcast/groups/
    Liste les groupes de diffusion de l'utilisateur.

    POST /api/v1/broadcast/groups/
    Crée un nouveau groupe de diffusion.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            from apps.competitions.models import UserProfile, BroadcastGroup

            # Vérifier les permissions
            user_profile = UserProfile.objects.filter(user=request.user).first()
            if not user_profile or not user_profile.organization:
                return Response({
                    'success': False,
                    'message': _("Aucune organisation associée")
                }, status=status.HTTP_400_BAD_REQUEST)

            # Vérifier le rôle
            allowed_roles = ['club_manager', 'coach', 'admin', 'federation_admin']
            if not (request.user.is_staff or user_profile.role in allowed_roles):
                return Response({
                    'success': False,
                    'message': _("Permissions insuffisantes")
                }, status=status.HTTP_403_FORBIDDEN)

            # Récupérer les groupes
            groups = BroadcastGroup.objects.filter(
                organization=user_profile.organization,
                is_active=True
            ).order_by('name')

            groups_data = []
            for group in groups:
                groups_data.append({
                    'uuid': str(group.uuid),
                    'name': group.name,
                    'description': group.description,
                    'icon': group.icon,
                    'color': group.color,
                    'target_type': group.target_type,
                    'age_category': group.age_category,
                    'gender_filter': group.gender_filter,
                    'member_count': group.member_count,
                    'last_message_date': group.last_message_date.isoformat() if group.last_message_date else None,
                    'created_at': group.created_at.isoformat(),
                })

            return Response({
                'success': True,
                'groups': groups_data,
                'total': len(groups_data)
            })

        except Exception as e:
            logger.exception("Erreur lors de la récupération des groupes")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            from apps.competitions.models import UserProfile, BroadcastGroup, Practitioner
            from apps.grades.models import Grade

            # Vérifier les permissions
            user_profile = UserProfile.objects.filter(user=request.user).first()
            if not user_profile or not user_profile.organization:
                return Response({
                    'success': False,
                    'message': _("Aucune organisation associée")
                }, status=status.HTTP_400_BAD_REQUEST)

            allowed_roles = ['club_manager', 'coach', 'admin', 'federation_admin']
            if not (request.user.is_staff or user_profile.role in allowed_roles):
                return Response({
                    'success': False,
                    'message': _("Permissions insuffisantes")
                }, status=status.HTTP_403_FORBIDDEN)

            # Valider les données
            name = request.data.get('name')
            if not name:
                return Response({
                    'success': False,
                    'message': _("Le nom du groupe est requis")
                }, status=status.HTTP_400_BAD_REQUEST)

            # Créer le groupe
            group = BroadcastGroup.objects.create(
                name=name,
                description=request.data.get('description', ''),
                icon=request.data.get('icon', 'users'),
                color=request.data.get('color', '#6366F1'),
                organization=user_profile.organization,
                created_by=request.user,
                target_type=request.data.get('target_type', 'criteria'),
                age_category=request.data.get('age_category', 'all'),
                min_age=request.data.get('min_age'),
                max_age=request.data.get('max_age'),
                gender_filter=request.data.get('gender_filter', 'all'),
                min_grade_level=request.data.get('min_grade_level'),
                max_grade_level=request.data.get('max_grade_level'),
            )

            # Ajouter les grades spécifiques
            grade_ids = request.data.get('grade_ids', [])
            if grade_ids:
                grades = Grade.objects.filter(id__in=grade_ids)
                group.grades.set(grades)

            # Ajouter les membres manuels
            if group.target_type == 'manual':
                member_ids = request.data.get('member_ids', [])
                if member_ids:
                    members = Practitioner.objects.filter(
                        id__in=member_ids,
                        organization=user_profile.organization
                    )
                    group.members.set(members)

            return Response({
                'success': True,
                'message': _("Groupe créé avec succès"),
                'group': {
                    'uuid': str(group.uuid),
                    'name': group.name,
                    'member_count': group.member_count,
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.exception("Erreur lors de la création du groupe")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BroadcastGroupDetailView(APIView):
    """
    GET /api/v1/broadcast/groups/<uuid>/
    Détail d'un groupe.

    PATCH /api/v1/broadcast/groups/<uuid>/
    Modifier un groupe.

    DELETE /api/v1/broadcast/groups/<uuid>/
    Supprimer un groupe.
    """
    permission_classes = [IsAuthenticated]

    def get_group(self, uuid, user):
        from apps.competitions.models import UserProfile, BroadcastGroup

        user_profile = UserProfile.objects.filter(user=user).first()
        if not user_profile or not user_profile.organization:
            return None, "Aucune organisation associée"

        try:
            group = BroadcastGroup.objects.get(
                uuid=uuid,
                organization=user_profile.organization
            )
            return group, None
        except BroadcastGroup.DoesNotExist:
            return None, "Groupe non trouvé"

    def get(self, request, group_uuid):
        try:
            group, error = self.get_group(group_uuid, request.user)
            if error:
                return Response({
                    'success': False,
                    'message': _(error)
                }, status=status.HTTP_404_NOT_FOUND)

            # Récupérer un aperçu des membres
            recipients = group.get_recipients()[:10]
            members_preview = [{
                'uuid': str(p.id),
                'id': p.id,
                'full_name': p.full_name,
                'first_name': p.first_name,
                'last_name': p.last_name,
                'grade_name': p.grade.name if p.grade else None,
                'grade_color': getattr(p.grade, 'color', None) if p.grade else None,
            } for p in recipients]

            # Statistiques des messages
            total_messages = group.messages.count()
            sent_messages = group.messages.filter(sent_at__isnull=False).count()

            return Response({
                'success': True,
                'group': {
                    'uuid': str(group.uuid),
                    'name': group.name,
                    'description': group.description,
                    'icon': group.icon,
                    'color': group.color,
                    'target_type': group.target_type,
                    'age_category': group.age_category,
                    'min_age': group.min_age,
                    'max_age': group.max_age,
                    'gender_filter': group.gender_filter,
                    'min_grade_level': group.min_grade_level,
                    'max_grade_level': group.max_grade_level,
                    'grade_ids': list(group.grades.values_list('id', flat=True)),
                    'member_count': group.member_count,
                    'members_preview': members_preview,
                    'total_messages': total_messages,
                    'sent_messages': sent_messages,
                    'last_message_date': group.last_message_date.isoformat() if group.last_message_date else None,
                    'created_at': group.created_at.isoformat(),
                    'created_by': group.created_by.get_full_name() if group.created_by else None,
                }
            })

        except Exception as e:
            logger.exception("Erreur lors de la récupération du groupe")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, group_uuid):
        try:
            from apps.grades.models import Grade
            from apps.competitions.models import Practitioner, UserProfile

            group, error = self.get_group(group_uuid, request.user)
            if error:
                return Response({
                    'success': False,
                    'message': _(error)
                }, status=status.HTTP_404_NOT_FOUND)

            # Mettre à jour les champs
            updatable_fields = [
                'name', 'description', 'icon', 'color', 'target_type',
                'age_category', 'min_age', 'max_age', 'gender_filter',
                'min_grade_level', 'max_grade_level'
            ]

            for field in updatable_fields:
                if field in request.data:
                    setattr(group, field, request.data[field])

            group.save()

            # Mettre à jour les grades
            if 'grade_ids' in request.data:
                grades = Grade.objects.filter(id__in=request.data['grade_ids'])
                group.grades.set(grades)

            # Mettre à jour les membres manuels
            if group.target_type == 'manual' and 'member_ids' in request.data:
                user_profile = UserProfile.objects.filter(user=request.user).first()
                members = Practitioner.objects.filter(
                    id__in=request.data['member_ids'],
                    organization=user_profile.organization
                )
                group.members.set(members)

            return Response({
                'success': True,
                'message': _("Groupe mis à jour avec succès"),
                'member_count': group.member_count,
            })

        except Exception as e:
            logger.exception("Erreur lors de la mise à jour du groupe")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, group_uuid):
        try:
            group, error = self.get_group(group_uuid, request.user)
            if error:
                return Response({
                    'success': False,
                    'message': _(error)
                }, status=status.HTTP_404_NOT_FOUND)

            group_name = group.name
            group.is_active = False
            group.save()

            return Response({
                'success': True,
                'message': _("Groupe '{}' supprimé").format(group_name)
            })

        except Exception as e:
            logger.exception("Erreur lors de la suppression du groupe")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BroadcastGroupMembersView(APIView):
    """
    GET /api/v1/broadcast/groups/<uuid>/members/
    Liste tous les membres correspondant aux critères du groupe.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, group_uuid):
        try:
            from apps.competitions.models import UserProfile, BroadcastGroup

            user_profile = UserProfile.objects.filter(user=request.user).first()
            if not user_profile or not user_profile.organization:
                return Response({
                    'success': False,
                    'message': _("Aucune organisation associée")
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                group = BroadcastGroup.objects.get(
                    uuid=group_uuid,
                    organization=user_profile.organization
                )
            except BroadcastGroup.DoesNotExist:
                return Response({
                    'success': False,
                    'message': _("Groupe non trouvé")
                }, status=status.HTTP_404_NOT_FOUND)

            # Récupérer tous les membres
            recipients = group.get_recipients()

            # Construire l'URL de base pour les photos
            base_url = request.build_absolute_uri('/')[:-1]  # Enlève le / final

            members_data = [{
                'uuid': str(p.id),  # Utiliser l'ID comme UUID pour compatibilité mobile
                'id': p.id,
                'full_name': p.full_name,
                'first_name': p.first_name,
                'last_name': p.last_name,
                'grade_name': p.grade.name if p.grade else None,
                'grade_color': getattr(p.grade, 'color', None) if p.grade else None,
                'age': p.age,
                'gender': p.gender,
                'photo': f"{base_url}{p.photo.url}" if p.photo else None,
                'has_user_account': p.user is not None,
            } for p in recipients]

            return Response({
                'success': True,
                'members': members_data,
                'total': len(members_data)
            })

        except Exception as e:
            logger.exception("Erreur lors de la récupération des membres")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BroadcastGroupAddMembersView(APIView):
    """
    POST /api/v1/broadcast/groups/<uuid>/members/add/
    Ajoute des membres manuels au groupe.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, group_uuid):
        try:
            from apps.competitions.models import UserProfile, BroadcastGroup, Practitioner

            user_profile = UserProfile.objects.filter(user=request.user).first()
            if not user_profile or not user_profile.organization:
                return Response({
                    'success': False,
                    'message': _("Aucune organisation associée")
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                group = BroadcastGroup.objects.get(
                    uuid=group_uuid,
                    organization=user_profile.organization
                )
            except BroadcastGroup.DoesNotExist:
                return Response({
                    'success': False,
                    'message': _("Groupe non trouvé")
                }, status=status.HTTP_404_NOT_FOUND)

            if group.target_type != 'manual':
                return Response({
                    'success': False,
                    'message': _("Ce groupe utilise des critères automatiques")
                }, status=status.HTTP_400_BAD_REQUEST)

            practitioner_ids = request.data.get('practitioner_ids', [])
            if not practitioner_ids:
                return Response({
                    'success': False,
                    'message': _("Aucun membre spécifié")
                }, status=status.HTTP_400_BAD_REQUEST)

            members = Practitioner.objects.filter(
                id__in=practitioner_ids,
                organization=user_profile.organization
            )
            group.members.add(*members)

            return Response({
                'success': True,
                'message': _("{} membre(s) ajouté(s)").format(members.count()),
                'member_count': group.member_count
            })

        except Exception as e:
            logger.exception("Erreur lors de l'ajout des membres")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BroadcastGroupRemoveMembersView(APIView):
    """
    POST /api/v1/broadcast/groups/<uuid>/members/remove/
    Retire des membres manuels du groupe.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, group_uuid):
        try:
            from apps.competitions.models import UserProfile, BroadcastGroup, Practitioner

            user_profile = UserProfile.objects.filter(user=request.user).first()
            if not user_profile or not user_profile.organization:
                return Response({
                    'success': False,
                    'message': _("Aucune organisation associée")
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                group = BroadcastGroup.objects.get(
                    uuid=group_uuid,
                    organization=user_profile.organization
                )
            except BroadcastGroup.DoesNotExist:
                return Response({
                    'success': False,
                    'message': _("Groupe non trouvé")
                }, status=status.HTTP_404_NOT_FOUND)

            if group.target_type != 'manual':
                return Response({
                    'success': False,
                    'message': _("Ce groupe utilise des critères automatiques")
                }, status=status.HTTP_400_BAD_REQUEST)

            practitioner_ids = request.data.get('practitioner_ids', [])
            if not practitioner_ids:
                return Response({
                    'success': False,
                    'message': _("Aucun membre spécifié")
                }, status=status.HTTP_400_BAD_REQUEST)

            members = Practitioner.objects.filter(id__in=practitioner_ids)
            group.members.remove(*members)

            return Response({
                'success': True,
                'message': _("{} membre(s) retiré(s)").format(members.count()),
                'member_count': group.member_count
            })

        except Exception as e:
            logger.exception("Erreur lors du retrait des membres")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BroadcastGroupSendView(APIView):
    """
    POST /api/v1/broadcast/groups/<uuid>/send/
    Envoie un message de diffusion au groupe.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, group_uuid):
        try:
            from apps.competitions.models import UserProfile, BroadcastGroup, BroadcastMessage

            user_profile = UserProfile.objects.filter(user=request.user).first()
            if not user_profile or not user_profile.organization:
                return Response({
                    'success': False,
                    'message': _("Aucune organisation associée")
                }, status=status.HTTP_400_BAD_REQUEST)

            # Vérifier les permissions
            allowed_roles = ['club_manager', 'coach', 'admin', 'federation_admin']
            if not (request.user.is_staff or user_profile.role in allowed_roles):
                return Response({
                    'success': False,
                    'message': _("Permissions insuffisantes")
                }, status=status.HTTP_403_FORBIDDEN)

            try:
                group = BroadcastGroup.objects.get(
                    uuid=group_uuid,
                    organization=user_profile.organization,
                    is_active=True
                )
            except BroadcastGroup.DoesNotExist:
                return Response({
                    'success': False,
                    'message': _("Groupe non trouvé")
                }, status=status.HTTP_404_NOT_FOUND)

            # Valider le message
            title = request.data.get('title')
            content = request.data.get('content')

            if not title or not content:
                return Response({
                    'success': False,
                    'message': _("Le titre et le contenu sont requis")
                }, status=status.HTTP_400_BAD_REQUEST)

            # Créer et envoyer le message
            message = BroadcastMessage.objects.create(
                group=group,
                title=title,
                content=content,
                sender=request.user,
                priority=request.data.get('priority', 'normal'),
            )

            # Envoyer le message (crée les notifications)
            send_push = request.data.get('send_push', True)
            notifications = message.send(send_push=send_push)

            return Response({
                'success': True,
                'message': _("Message envoyé à {} destinataire(s)").format(len(notifications)),
                'broadcast': {
                    'uuid': str(message.uuid),
                    'title': message.title,
                    'recipients_count': message.recipients_count,
                    'sent_at': message.sent_at.isoformat() if message.sent_at else None,
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.exception("Erreur lors de l'envoi du message")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BroadcastMessageListView(APIView):
    """
    GET /api/v1/broadcast/messages/
    Liste les messages envoyés par l'utilisateur.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            from apps.competitions.models import UserProfile, BroadcastMessage

            user_profile = UserProfile.objects.filter(user=request.user).first()
            if not user_profile or not user_profile.organization:
                return Response({
                    'success': False,
                    'message': _("Aucune organisation associée")
                }, status=status.HTTP_400_BAD_REQUEST)

            # Récupérer les messages de l'organisation
            messages = BroadcastMessage.objects.filter(
                group__organization=user_profile.organization,
                sent_at__isnull=False
            ).select_related('group', 'sender').order_by('-sent_at')

            # Pagination simple
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            start = (page - 1) * page_size
            end = start + page_size

            messages_data = []
            for msg in messages[start:end]:
                messages_data.append({
                    'uuid': str(msg.uuid),
                    'title': msg.title,
                    'content': msg.content[:200] + '...' if len(msg.content) > 200 else msg.content,
                    'priority': msg.priority,
                    'group_name': msg.group.name,
                    'group_uuid': str(msg.group.uuid),
                    'sender_name': msg.sender.get_full_name() if msg.sender else None,
                    'recipients_count': msg.recipients_count,
                    'read_count': msg.read_count,
                    'read_percentage': msg.read_percentage,
                    'sent_at': msg.sent_at.isoformat() if msg.sent_at else None,
                })

            return Response({
                'success': True,
                'messages': messages_data,
                'total': messages.count(),
                'page': page,
                'page_size': page_size,
            })

        except Exception as e:
            logger.exception("Erreur lors de la récupération des messages")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BroadcastMessageDetailView(APIView):
    """
    GET /api/v1/broadcast/messages/<uuid>/
    Détail d'un message avec statistiques de lecture.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, message_uuid):
        try:
            from apps.competitions.models import UserProfile, BroadcastMessage

            user_profile = UserProfile.objects.filter(user=request.user).first()
            if not user_profile or not user_profile.organization:
                return Response({
                    'success': False,
                    'message': _("Aucune organisation associée")
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                message = BroadcastMessage.objects.select_related('group', 'sender').get(
                    uuid=message_uuid,
                    group__organization=user_profile.organization
                )
            except BroadcastMessage.DoesNotExist:
                return Response({
                    'success': False,
                    'message': _("Message non trouvé")
                }, status=status.HTTP_404_NOT_FOUND)

            # Récupérer les statuts de lecture
            receipts = message.receipts.select_related('practitioner').all()
            read_receipts = []
            unread_receipts = []

            for receipt in receipts:
                receipt_data = {
                    'practitioner_id': receipt.practitioner.id,
                    'practitioner_name': receipt.practitioner.full_name,
                    'delivered_at': receipt.delivered_at.isoformat(),
                    'read_at': receipt.read_at.isoformat() if receipt.read_at else None,
                }
                if receipt.read_at:
                    read_receipts.append(receipt_data)
                else:
                    unread_receipts.append(receipt_data)

            return Response({
                'success': True,
                'message': {
                    'uuid': str(message.uuid),
                    'title': message.title,
                    'content': message.content,
                    'priority': message.priority,
                    'group_name': message.group.name,
                    'group_uuid': str(message.group.uuid),
                    'sender_name': message.sender.get_full_name() if message.sender else None,
                    'recipients_count': message.recipients_count,
                    'read_count': message.read_count,
                    'read_percentage': message.read_percentage,
                    'sent_at': message.sent_at.isoformat() if message.sent_at else None,
                    'created_at': message.created_at.isoformat(),
                },
                'read_receipts': read_receipts,
                'unread_receipts': unread_receipts,
            })

        except Exception as e:
            logger.exception("Erreur lors de la récupération du message")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, message_uuid):
        """
        DELETE /api/v1/broadcast/messages/<uuid>/
        Supprime un message de diffusion.
        """
        try:
            from apps.competitions.models import UserProfile, BroadcastMessage

            user_profile = UserProfile.objects.filter(user=request.user).first()
            if not user_profile or not user_profile.organization:
                return Response({
                    'success': False,
                    'message': _("Aucune organisation associée")
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                message = BroadcastMessage.objects.get(
                    uuid=message_uuid,
                    group__organization=user_profile.organization
                )
            except BroadcastMessage.DoesNotExist:
                return Response({
                    'success': False,
                    'message': _("Message non trouvé")
                }, status=status.HTTP_404_NOT_FOUND)

            # Vérifier que l'utilisateur est le créateur ou un admin
            if message.sender != request.user and not request.user.is_staff:
                return Response({
                    'success': False,
                    'message': _("Vous n'avez pas la permission de supprimer ce message")
                }, status=status.HTTP_403_FORBIDDEN)

            # Supprimer les reçus associés
            message.receipts.all().delete()

            # Supprimer le message
            message_title = message.title
            message.delete()

            return Response({
                'success': True,
                'message': _("Message supprimé avec succès"),
                'deleted_title': message_title
            })

        except Exception as e:
            logger.exception("Erreur lors de la suppression du message")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BroadcastInboxView(APIView):
    """
    GET /api/v1/broadcast/inbox/
    Boîte de réception des messages de diffusion pour un pratiquant.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            from apps.competitions.models import Practitioner, BroadcastReceipt

            # Trouver le pratiquant lié à l'utilisateur
            practitioner = Practitioner.objects.filter(user=request.user).first()
            if not practitioner:
                return Response({
                    'success': True,
                    'messages': [],
                    'total': 0,
                    'unread_count': 0
                })

            # Récupérer les reçus de diffusion
            receipts = BroadcastReceipt.objects.filter(
                practitioner=practitioner
            ).select_related('broadcast', 'broadcast__group', 'broadcast__sender').order_by('-delivered_at')

            # Pagination
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            start = (page - 1) * page_size
            end = start + page_size

            unread_count = receipts.filter(read_at__isnull=True).count()

            messages_data = []
            for receipt in receipts[start:end]:
                msg = receipt.broadcast
                messages_data.append({
                    'uuid': str(msg.uuid),
                    'title': msg.title,
                    'content': msg.content[:200] + '...' if len(msg.content) > 200 else msg.content,
                    'priority': msg.priority,
                    'group_name': msg.group.name,
                    'sender_name': msg.sender.get_full_name() if msg.sender else None,
                    'sent_at': msg.sent_at.isoformat() if msg.sent_at else None,
                    'is_read': receipt.read_at is not None,
                    'read_at': receipt.read_at.isoformat() if receipt.read_at else None,
                })

            return Response({
                'success': True,
                'messages': messages_data,
                'total': receipts.count(),
                'unread_count': unread_count,
                'page': page,
                'page_size': page_size,
            })

        except Exception as e:
            logger.exception("Erreur lors de la récupération de la boîte de réception")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BroadcastMarkReadView(APIView):
    """
    POST /api/v1/broadcast/inbox/<uuid>/read/
    Marque un message comme lu.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, message_uuid):
        try:
            from apps.competitions.models import Practitioner, BroadcastReceipt, BroadcastMessage

            practitioner = Practitioner.objects.filter(user=request.user).first()
            if not practitioner:
                return Response({
                    'success': False,
                    'message': _("Pratiquant non trouvé")
                }, status=status.HTTP_404_NOT_FOUND)

            try:
                receipt = BroadcastReceipt.objects.get(
                    broadcast__uuid=message_uuid,
                    practitioner=practitioner
                )
            except BroadcastReceipt.DoesNotExist:
                return Response({
                    'success': False,
                    'message': _("Message non trouvé")
                }, status=status.HTTP_404_NOT_FOUND)

            receipt.mark_as_read()

            return Response({
                'success': True,
                'message': _("Message marqué comme lu"),
                'read_at': receipt.read_at.isoformat()
            })

        except Exception as e:
            logger.exception("Erreur lors du marquage comme lu")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
