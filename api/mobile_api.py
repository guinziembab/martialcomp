"""
API Mobile MartialComp
======================
Endpoints REST dédiés à l'application mobile React Native.
"""

import json
import logging
from datetime import datetime, timedelta

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.db.models import Q, Count
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status

logger = logging.getLogger(__name__)
User = get_user_model()


# =============================================================================
# QR SCANNER API
# =============================================================================

class QRScanProcessView(APIView):
    """
    POST /api/qr/scan/process/
    Traite le scan d'un QR code depuis l'application mobile.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            from apps.competitions.models import PractitionerQRCode, QRCodeScan, Practitioner

            qr_code_uuid = request.data.get('qr_code')
            scan_type = request.data.get('scan_type', 'general')

            if not qr_code_uuid:
                return Response({
                    'success': False,
                    'message': _("QR code manquant")
                }, status=status.HTTP_400_BAD_REQUEST)

            # Trouver le QR code
            try:
                qr_code = PractitionerQRCode.objects.select_related('practitioner').get(code=qr_code_uuid)
            except PractitionerQRCode.DoesNotExist:
                return Response({
                    'success': False,
                    'message': _("QR Code invalide")
                }, status=status.HTTP_404_NOT_FOUND)

            # Créer le scan
            scan = QRCodeScan.objects.create(
                qr_code=qr_code,
                scan_type=scan_type,
                scanned_by=request.user,
                location=request.data.get('location', ''),
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )

            # Préparer la réponse
            practitioner = qr_code.practitioner
            return Response({
                'success': True,
                'valid': scan.is_valid,
                'message': scan.validation_message or _("Scan effectué avec succès"),
                'practitioner': {
                    'id': practitioner.id,
                    'name': practitioner.full_name,
                    'first_name': practitioner.first_name,
                    'last_name': practitioner.last_name,
                    'photo': practitioner.photo.url if practitioner.photo else None,
                    'organization': practitioner.organization.name if practitioner.organization else None,
                    'license_number': practitioner.license_number,
                    'is_federation_validated': qr_code.is_federation_validated
                },
                'scan_count': qr_code.scan_count,
                'scan_id': scan.id
            })

        except Exception as e:
            logger.exception("Erreur lors du traitement du scan QR")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class QRScanHistoryView(APIView):
    """
    GET /api/qr/scan/history/
    Récupère l'historique des scans pour l'utilisateur connecté.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            from apps.competitions.models import QRCodeScan

            # Filtres optionnels
            scan_type = request.query_params.get('type')
            limit = int(request.query_params.get('limit', 50))

            # Récupérer les scans effectués par l'utilisateur
            scans = QRCodeScan.objects.filter(
                scanned_by=request.user
            ).select_related(
                'qr_code__practitioner'
            ).order_by('-scan_date')

            if scan_type:
                scans = scans.filter(scan_type=scan_type)

            scans = scans[:limit]

            return Response({
                'success': True,
                'scans': [{
                    'id': scan.id,
                    'scan_type': scan.scan_type,
                    'scan_date': scan.scan_date.isoformat(),
                    'is_valid': scan.is_valid,
                    'practitioner': {
                        'id': scan.qr_code.practitioner.id,
                        'name': scan.qr_code.practitioner.full_name,
                    } if scan.qr_code else None,
                    'location': scan.location
                } for scan in scans],
                'total': len(scans)
            })

        except Exception as e:
            logger.exception("Erreur lors de la récupération de l'historique")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class QRPractitionerView(APIView):
    """
    GET /api/qr/practitioner/<id>/
    Récupère les informations d'un pratiquant via son ID.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, practitioner_id):
        try:
            from apps.competitions.models import Practitioner, PractitionerQRCode

            practitioner = get_object_or_404(Practitioner, id=practitioner_id)
            qr_code, _ = PractitionerQRCode.objects.get_or_create(practitioner=practitioner)

            return Response({
                'success': True,
                'practitioner': {
                    'id': practitioner.id,
                    'first_name': practitioner.first_name,
                    'last_name': practitioner.last_name,
                    'full_name': practitioner.full_name,
                    'email': practitioner.email,
                    'photo': practitioner.photo.url if practitioner.photo else None,
                    'organization': practitioner.organization.name if practitioner.organization else None,
                    'license_number': practitioner.license_number,
                    'birth_date': practitioner.birth_date.isoformat() if practitioner.birth_date else None,
                },
                'qr_code': {
                    'uuid': str(qr_code.code),
                    'is_federation_validated': qr_code.is_federation_validated,
                    'scan_count': qr_code.scan_count,
                    'created_at': qr_code.created_at.isoformat() if qr_code.created_at else None,
                }
            })

        except Exception as e:
            logger.exception("Erreur lors de la récupération du pratiquant")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class QROfflineTokenView(APIView):
    """
    GET /api/qr/practitioner/<id>/offline-token/
    Génère un token pour utilisation hors-ligne.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, practitioner_id):
        try:
            from apps.competitions.models import Practitioner, PractitionerQRCode
            from apps.competitions.utils.qr_offline import OfflineQRTokenGenerator

            practitioner = get_object_or_404(Practitioner, id=practitioner_id)
            qr_code, _ = PractitionerQRCode.objects.get_or_create(practitioner=practitioner)

            # Vérifier les permissions
            is_owner = practitioner.user == request.user
            is_admin = request.user.is_staff or request.user.is_superuser

            if not (is_owner or is_admin):
                return Response({
                    'success': False,
                    'message': _("Permissions insuffisantes")
                }, status=status.HTTP_403_FORBIDDEN)

            # Générer le token
            club_id = practitioner.organization.id if practitioner.organization else None
            offline_token = OfflineQRTokenGenerator.generate_offline_token(
                practitioner_id=practitioner.id,
                qr_code_uuid=qr_code.code,
                federation_validated=qr_code.is_federation_validated,
                club_id=club_id
            )

            return Response({
                'success': True,
                'token': offline_token,
                'practitioner_id': practitioner.id,
                'qr_uuid': str(qr_code.code),
                'expires_in_days': 7,
                'federation_validated': qr_code.is_federation_validated,
            })

        except Exception as e:
            logger.exception("Erreur lors de la génération du token offline")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class QRVerifyOfflineTokenView(APIView):
    """
    POST /api/qr/scan/verify-offline-token/
    Vérifie un token hors-ligne.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            from apps.competitions.utils.qr_offline import OfflineQRTokenGenerator

            token = request.data.get('token')
            if not token:
                return Response({
                    'success': False,
                    'message': _("Token manquant")
                }, status=status.HTTP_400_BAD_REQUEST)

            # Vérifier le token
            token_data = OfflineQRTokenGenerator.verify_offline_token(token)

            if not token_data.get('valid', False):
                return Response({
                    'valid': False,
                    'reason': token_data.get('reason', 'unknown')
                })

            return Response({
                'valid': True,
                'practitioner_id': token_data.get('prac_id'),
                'qr_uuid': token_data.get('qr_uuid'),
                'federation_validated': token_data.get('fed_val'),
                'club_id': token_data.get('club_id'),
                'expires_at': token_data.get('exp'),
            })

        except Exception as e:
            logger.exception("Erreur lors de la vérification du token")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class QRSyncOfflineView(APIView):
    """
    POST /api/qr/scan/sync-offline/
    Synchronise les scans effectués hors-ligne.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            from apps.competitions.utils.qr_offline import OfflineQRStorage

            offline_scans = request.data.get('scans', [])

            if not offline_scans:
                return Response({
                    'success': True,
                    'message': _("Aucun scan à synchroniser"),
                    'synced': 0,
                    'ignored': 0
                })

            # Fusionner les scans
            created, ignored = OfflineQRStorage.merge_offline_scans(offline_scans)

            return Response({
                'success': True,
                'message': f"{created} scans synchronisés, {ignored} ignorés",
                'synced': created,
                'ignored': ignored
            })

        except Exception as e:
            logger.exception("Erreur lors de la synchronisation")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# OFFLINE PROFILES API
# =============================================================================

class OfflineProfilesListView(APIView):
    """
    GET /api/offline/profiles/
    Récupère les profils disponibles pour utilisation hors-ligne.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            from apps.competitions.models import Practitioner

            # Récupérer les pratiquants de l'organisation de l'utilisateur
            practitioners = Practitioner.objects.filter(
                Q(user=request.user) |
                Q(organization__membership__user=request.user)
            ).distinct().select_related('organization')[:100]

            profiles = []
            for p in practitioners:
                profiles.append({
                    'id': p.id,
                    'first_name': p.first_name,
                    'last_name': p.last_name,
                    'full_name': p.full_name,
                    'photo': request.build_absolute_uri(p.photo.url) if p.photo else None,
                    'organization': p.organization.name if p.organization else None,
                    'license_number': p.license_number,
                })

            return Response({
                'success': True,
                'profiles': profiles,
                'total': len(profiles)
            })

        except Exception as e:
            logger.exception("Erreur lors de la récupération des profils offline")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OfflineSyncView(APIView):
    """
    POST /api/offline/sync/
    Synchronise toutes les données hors-ligne.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            sync_data = request.data.get('data', {})
            results = {
                'scans': {'synced': 0, 'failed': 0},
                'attendance': {'synced': 0, 'failed': 0},
            }

            # Synchroniser les scans
            if 'scans' in sync_data:
                from apps.competitions.utils.qr_offline import OfflineQRStorage
                created, ignored = OfflineQRStorage.merge_offline_scans(sync_data['scans'])
                results['scans']['synced'] = created
                results['scans']['failed'] = ignored

            return Response({
                'success': True,
                'message': _("Synchronisation terminée"),
                'results': results,
                'synced_at': timezone.now().isoformat()
            })

        except Exception as e:
            logger.exception("Erreur lors de la synchronisation offline")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# DOCUMENTS API
# =============================================================================

class DocumentsListView(APIView):
    """
    GET /api/documents/
    Liste les documents de l'utilisateur.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            from apps.documents.models import Document, DocumentShare

            category = request.query_params.get('category')
            document_type = request.query_params.get('document_type')
            is_public = request.query_params.get('is_public')
            is_required = request.query_params.get('is_required')
            limit = int(request.query_params.get('limit', 50))

            # Documents partagés avec l'utilisateur
            shared_doc_ids = DocumentShare.objects.filter(
                user=request.user
            ).values_list('document_id', flat=True)

            # Documents liés aux organisations gérées par l'utilisateur
            from django.contrib.contenttypes.models import ContentType
            from apps.organizations.models import Organization
            managed_org_ids = Organization.objects.filter(
                members__user=request.user,
                members__role__in=['owner', 'admin', 'manager']
            ).values_list('id', flat=True)

            org_filter = Q()
            if managed_org_ids:
                org_ct = ContentType.objects.get_for_model(Organization)
                org_filter = Q(
                    content_type=org_ct,
                    object_id__in=[str(oid) for oid in managed_org_ids]
                )

            # Combiner les requêtes
            documents = Document.objects.filter(
                Q(created_by=request.user) |
                Q(id__in=shared_doc_ids) |
                Q(is_public=True) |
                org_filter
            ).distinct().order_by('-created_at')

            # Filtres optionnels
            if category:
                documents = documents.filter(document_type=category)
            if document_type:
                documents = documents.filter(document_type=document_type)
            if is_public == 'true':
                documents = documents.filter(is_public=True)

            documents = documents[:limit]

            return Response({
                'success': True,
                'documents': [{
                    'id': str(doc.id),
                    'title': doc.title,
                    'description': doc.description or '',
                    'category': doc.document_type or 'other',
                    'file_type': doc.mime_type or 'application/octet-stream',
                    'file_url': doc.file.url if doc.file else None,
                    'file_size': doc.file_size or (doc.file.size if doc.file else 0),
                    'created_at': doc.created_at.isoformat(),
                    'updated_at': doc.updated_at.isoformat() if doc.updated_at else None,
                    'is_public': doc.is_public,
                    'owner': doc.created_by.get_full_name() or doc.created_by.username if doc.created_by else None,
                } for doc in documents],
                'total': len(documents),
                'hasMore': False,
            })

        except ImportError:
            # App documents non installée
            return Response({
                'success': True,
                'documents': [],
                'total': 0,
                'hasMore': False,
                'message': _("Module documents non disponible")
            })
        except Exception as e:
            logger.exception("Erreur lors de la récupération des documents")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentDetailView(APIView):
    """
    GET /api/documents/<id>/
    Détails d'un document.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, document_id):
        try:
            from apps.documents.models import Document, DocumentShare

            # IDs des documents partagés avec l'utilisateur
            shared_doc_ids = DocumentShare.objects.filter(
                user=request.user
            ).values_list('document_id', flat=True)

            document = get_object_or_404(
                Document.objects.filter(
                    Q(created_by=request.user) | Q(id__in=shared_doc_ids) | Q(is_public=True)
                ),
                id=document_id
            )

            # Incrémenter le compteur de vues
            document.view_count += 1
            document.save(update_fields=['view_count'])

            return Response({
                'success': True,
                'document': {
                    'id': str(document.id),
                    'title': document.title,
                    'description': document.description or '',
                    'category': document.document_type or 'other',
                    'file_type': document.mime_type or 'application/octet-stream',
                    'file_url': document.file.url if document.file else None,
                    'file_size': document.file_size or (document.file.size if document.file else 0),
                    'created_at': document.created_at.isoformat(),
                    'updated_at': document.updated_at.isoformat() if document.updated_at else None,
                    'owner': document.created_by.get_full_name() or document.created_by.username if document.created_by else None,
                    'is_public': document.is_public,
                    'view_count': document.view_count,
                    'download_count': document.download_count,
                }
            })

        except ImportError:
            return Response({
                'success': False,
                'message': _("Module documents non disponible")
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception("Erreur lors de la récupération du document")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentCategoriesView(APIView):
    """
    GET /api/documents/categories/
    Liste les catégories de documents disponibles.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            from apps.documents.models import Document, DocumentShare

            # IDs des documents partagés avec l'utilisateur
            shared_doc_ids = DocumentShare.objects.filter(
                user=request.user
            ).values_list('document_id', flat=True)

            # Récupérer les catégories distinctes
            categories = Document.objects.filter(
                Q(created_by=request.user) | Q(id__in=shared_doc_ids) | Q(is_public=True)
            ).exclude(document_type='').exclude(document_type__isnull=True).values_list('document_type', flat=True).distinct()

            # Catégories par défaut
            default_categories = [
                {'id': 'certificate', 'name': _('Certificat'), 'icon': 'ribbon'},
                {'id': 'diploma', 'name': _('Diplôme'), 'icon': 'school'},
                {'id': 'license', 'name': _('Licence'), 'icon': 'card-account-details'},
                {'id': 'medical', 'name': _('Certificat médical'), 'icon': 'medical-bag'},
                {'id': 'competition', 'name': _('Document de compétition'), 'icon': 'trophy'},
                {'id': 'training', 'name': _('Document d\'entraînement'), 'icon': 'dumbbell'},
                {'id': 'technical', 'name': _('Document technique'), 'icon': 'book-open-variant'},
                {'id': 'administrative', 'name': _('Document administratif'), 'icon': 'file-document'},
                {'id': 'other', 'name': _('Autre'), 'icon': 'file'},
            ]

            return Response({
                'success': True,
                'categories': default_categories,
                'user_categories': list(categories)
            })

        except ImportError:
            return Response({
                'success': True,
                'categories': [
                    {'id': 'certificate', 'name': 'Certificat', 'icon': 'ribbon'},
                    {'id': 'license', 'name': 'Licence', 'icon': 'card-account-details'},
                    {'id': 'medical', 'name': 'Certificat médical', 'icon': 'medical-bag'},
                    {'id': 'other', 'name': 'Autre', 'icon': 'file'},
                ]
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentUploadView(APIView):
    """
    POST /api/documents/upload/
    Upload d'un nouveau document.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            from apps.documents.models import Document, DocumentFolder

            # Récupérer le fichier
            uploaded_file = request.FILES.get('file')
            if not uploaded_file:
                return Response({
                    'success': False,
                    'message': _("Aucun fichier fourni")
                }, status=status.HTTP_400_BAD_REQUEST)

            # Valider la taille du fichier (max 50 MB)
            max_size = 50 * 1024 * 1024  # 50 MB
            if uploaded_file.size > max_size:
                return Response({
                    'success': False,
                    'message': _("Fichier trop volumineux. Maximum: 50 MB")
                }, status=status.HTTP_400_BAD_REQUEST)

            # Récupérer les métadonnées
            title = request.data.get('title', uploaded_file.name)
            description = request.data.get('description', '')
            document_type = request.data.get('document_type', request.data.get('category', 'other'))
            is_public = request.data.get('is_public', 'false').lower() == 'true'
            folder_id = request.data.get('folder_id')

            # Récupérer le dossier si spécifié
            folder = None
            if folder_id:
                try:
                    folder = DocumentFolder.objects.get(id=folder_id, owner=request.user)
                except DocumentFolder.DoesNotExist:
                    pass

            # Créer le document
            document = Document(
                title=title,
                description=description,
                file=uploaded_file,
                document_type=document_type,
                is_public=is_public,
                folder=folder,
                created_by=request.user,
                modified_by=request.user,
            )
            document.save()

            return Response({
                'success': True,
                'message': _("Document uploadé avec succès"),
                'document': {
                    'id': str(document.id),
                    'title': document.title,
                    'description': document.description,
                    'category': document.document_type,
                    'file_type': document.mime_type,
                    'file_url': document.file.url if document.file else None,
                    'file_size': document.file_size,
                    'created_at': document.created_at.isoformat(),
                    'is_public': document.is_public,
                }
            }, status=status.HTTP_201_CREATED)

        except ImportError:
            return Response({
                'success': False,
                'message': _("Module documents non disponible")
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            logger.exception("Erreur lors de l'upload du document")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentDownloadView(APIView):
    """
    GET /api/documents/<id>/download/
    Télécharge un document.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, document_id):
        try:
            from apps.documents.models import Document, DocumentShare, DocumentAccessLog
            from django.http import FileResponse

            # IDs des documents partagés avec l'utilisateur
            shared_doc_ids = DocumentShare.objects.filter(
                user=request.user
            ).values_list('document_id', flat=True)

            document = get_object_or_404(
                Document.objects.filter(
                    Q(created_by=request.user) | Q(id__in=shared_doc_ids) | Q(is_public=True)
                ),
                id=document_id
            )

            if not document.file:
                return Response({
                    'success': False,
                    'message': _("Aucun fichier disponible pour ce document")
                }, status=status.HTTP_404_NOT_FOUND)

            # Incrémenter le compteur de téléchargements
            document.download_count += 1
            document.save(update_fields=['download_count'])

            # Enregistrer l'accès
            try:
                DocumentAccessLog.objects.create(
                    document=document,
                    user=request.user,
                    action='download',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
            except Exception:
                pass

            # Renvoyer le fichier
            response = FileResponse(
                document.file.open('rb'),
                content_type=document.mime_type or 'application/octet-stream'
            )
            filename = document.file.name.split('/')[-1]
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

        except ImportError:
            return Response({
                'success': False,
                'message': _("Module documents non disponible")
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            logger.exception("Erreur lors du téléchargement du document")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentDeleteView(APIView):
    """
    DELETE /api/documents/<id>/
    Supprime un document.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, document_id):
        try:
            from apps.documents.models import Document

            document = get_object_or_404(
                Document.objects.filter(created_by=request.user),
                id=document_id
            )

            document_title = document.title
            document.delete()

            return Response({
                'success': True,
                'message': _("Document supprimé: {title}").format(title=document_title)
            })

        except ImportError:
            return Response({
                'success': False,
                'message': _("Module documents non disponible")
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            logger.exception("Erreur lors de la suppression du document")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# TRAINING API
# =============================================================================

class TrainingSessionsListView(APIView):
    """
    GET /api/training/sessions/
    Liste les sessions d'entraînement avec support complet des filtres.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            from apps.competitions.models import TrainingSession

            # Filtres
            date_from = request.query_params.get('from')
            date_to = request.query_params.get('to')
            page = int(request.query_params.get('page', 1))
            limit = int(request.query_params.get('limit', 20))
            category = request.query_params.get('category')
            level = request.query_params.get('level')
            query = request.query_params.get('query')
            is_active = request.query_params.get('is_active')
            is_recurring = request.query_params.get('is_recurring')
            my_trainings = request.query_params.get('my_trainings')

            sessions = TrainingSession.objects.filter(
                training_slot__club__organization__membership__user=request.user
            ).select_related('training_slot', 'training_slot__club').order_by('-date')

            if date_from:
                sessions = sessions.filter(date__gte=date_from)
            if date_to:
                sessions = sessions.filter(date__lte=date_to)
            if query:
                sessions = sessions.filter(
                    Q(training_slot__name__icontains=query) |
                    Q(training_slot__description__icontains=query)
                )
            if is_active == 'true':
                sessions = sessions.filter(date__gte=timezone.now().date())
            if is_recurring == 'true':
                sessions = sessions.filter(training_slot__is_recurring=True)

            total = sessions.count()
            offset = (page - 1) * limit
            sessions = sessions[offset:offset + limit]
            has_more = (offset + limit) < total

            return Response({
                'success': True,
                'trainings': [{
                    'id': str(s.id),
                    'title': getattr(s.training_slot, 'name', f'Session {s.id}'),
                    'description': getattr(s.training_slot, 'description', ''),
                    'startDate': s.date.isoformat(),
                    'start_date': s.date.isoformat(),
                    'endDate': s.date.isoformat(),
                    'end_date': s.date.isoformat(),
                    'duration': getattr(s.training_slot, 'duration', 60),
                    'location': getattr(s.training_slot, 'location', None),
                    'instructor': s.training_slot.club.name if s.training_slot.club else None,
                    'maxParticipants': getattr(s.training_slot, 'max_participants', 30),
                    'currentParticipants': getattr(s, 'attendance_count', 0),
                    'price': 0,
                    'currency': 'EUR',
                    'level': getattr(s.training_slot, 'level', 'all_levels'),
                    'isActive': s.date >= timezone.now().date(),
                    'isRecurring': getattr(s.training_slot, 'is_recurring', False),
                    'isRegistrationOpen': s.date >= timezone.now().date(),
                    'isRegistered': False,
                } for s in sessions],
                'sessions': [{
                    'id': s.id,
                    'date': s.date.isoformat(),
                    'start_time': s.training_slot.start_time.strftime('%H:%M') if s.training_slot.start_time else None,
                    'end_time': s.training_slot.end_time.strftime('%H:%M') if s.training_slot.end_time else None,
                    'club': s.training_slot.club.name if s.training_slot.club else None,
                    'location': s.training_slot.location if hasattr(s.training_slot, 'location') else None,
                    'status': s.status if hasattr(s, 'status') else 'scheduled',
                } for s in sessions],
                'total': total,
                'hasMore': has_more,
                'has_next': has_more,
                'page': page,
            })

        except Exception as e:
            logger.exception("Erreur lors de la récupération des sessions")
            return Response({
                'success': False,
                'trainings': [],
                'sessions': [],
                'total': 0,
                'hasMore': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TrainingCategoriesView(APIView):
    """
    GET /api/training/categories/
    Liste les catégories d'entraînement.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Catégories par défaut pour les entraînements
            default_categories = [
                {'id': 'technique', 'name': 'Technique', 'icon': 'fitness-outline', 'color': '#4CAF50', 'isActive': True, 'trainingCount': 0},
                {'id': 'physical', 'name': 'Préparation physique', 'icon': 'barbell-outline', 'color': '#FF9800', 'isActive': True, 'trainingCount': 0},
                {'id': 'combat', 'name': 'Combat/Sparring', 'icon': 'flame-outline', 'color': '#F44336', 'isActive': True, 'trainingCount': 0},
                {'id': 'kata', 'name': 'Kata/Formes', 'icon': 'body-outline', 'color': '#9C27B0', 'isActive': True, 'trainingCount': 0},
                {'id': 'competition', 'name': 'Préparation compétition', 'icon': 'trophy-outline', 'color': '#FFD700', 'isActive': True, 'trainingCount': 0},
                {'id': 'seminar', 'name': 'Stage/Séminaire', 'icon': 'school-outline', 'color': '#2196F3', 'isActive': True, 'trainingCount': 0},
            ]

            return Response({
                'success': True,
                'categories': default_categories,
                'results': default_categories,
            })

        except Exception as e:
            logger.exception("Erreur lors de la récupération des catégories")
            return Response({
                'success': False,
                'categories': [],
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TrainingAttendanceView(APIView):
    """
    GET/POST /api/training/attendance/
    Gère les présences aux sessions.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            from apps.competitions.models import Attendance

            session_id = request.query_params.get('session_id')

            attendances = Attendance.objects.filter(
                session__training_slot__club__organization__membership__user=request.user
            ).select_related('practitioner', 'session')

            if session_id:
                attendances = attendances.filter(session_id=session_id)

            return Response({
                'success': True,
                'attendances': [{
                    'id': a.id,
                    'session_id': a.session_id,
                    'practitioner': {
                        'id': a.practitioner.id,
                        'name': a.practitioner.full_name,
                    },
                    'status': a.status,
                    'arrival_time': a.arrival_time.strftime('%H:%M') if a.arrival_time else None,
                } for a in attendances[:100]]
            })

        except Exception as e:
            logger.exception("Erreur lors de la récupération des présences")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            from apps.competitions.models import Attendance, TrainingSession, Practitioner

            session_id = request.data.get('session_id')
            practitioner_id = request.data.get('practitioner_id')
            attendance_status = request.data.get('status', 'present')

            session = get_object_or_404(TrainingSession, id=session_id)
            practitioner = get_object_or_404(Practitioner, id=practitioner_id)

            attendance, created = Attendance.objects.update_or_create(
                session=session,
                practitioner=practitioner,
                defaults={
                    'status': attendance_status,
                    'arrival_time': timezone.now().time() if attendance_status == 'present' else None
                }
            )

            return Response({
                'success': True,
                'created': created,
                'attendance': {
                    'id': attendance.id,
                    'status': attendance.status,
                    'arrival_time': attendance.arrival_time.strftime('%H:%M') if attendance.arrival_time else None,
                }
            })

        except Exception as e:
            logger.exception("Erreur lors de l'enregistrement de la présence")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# COMMUNICATION API
# =============================================================================

class CommunicationMessagesView(APIView):
    """
    GET /api/communication/messages/
    Liste les messages.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Placeholder - à implémenter selon le modèle de messages
            return Response({
                'success': True,
                'messages': [],
                'total': 0,
                'message': _("Module de messagerie à venir")
            })

        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CommunicationAnnouncementsView(APIView):
    """
    GET /api/communication/announcements/
    Liste les annonces.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Récupérer les actualités de l'organisation
            from apps.organizations.models import OrganizationNews

            news = OrganizationNews.objects.filter(
                organization__membership__user=request.user,
                is_published=True
            ).order_by('-published_at')[:20]

            return Response({
                'success': True,
                'announcements': [{
                    'id': n.id,
                    'title': n.title,
                    'content': n.content[:200] + '...' if len(n.content) > 200 else n.content,
                    'published_at': n.published_at.isoformat() if n.published_at else None,
                    'organization': n.organization.name,
                    'priority': getattr(n, 'priority', 'medium'),
                } for n in news]
            })

        except ImportError:
            return Response({
                'success': True,
                'announcements': [],
                'message': _("Aucune annonce disponible")
            })
        except Exception as e:
            logger.exception("Erreur lors de la récupération des annonces")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# PASSWORD RESET API (Mobile)
# =============================================================================

class PasswordResetRequestView(APIView):
    """
    POST /api/v1/auth/password-reset/
    Demande de réinitialisation de mot de passe depuis mobile.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            from allauth.account.forms import ResetPasswordForm
            from django.test import RequestFactory

            email = request.data.get('email')

            if not email:
                return Response({
                    'success': False,
                    'message': _("Email requis")
                }, status=status.HTTP_400_BAD_REQUEST)

            # Créer une requête factice pour allauth
            factory = RequestFactory()
            fake_request = factory.post('/accounts/password/reset/')
            fake_request.META['HTTP_HOST'] = request.get_host()

            form = ResetPasswordForm(data={'email': email})
            if form.is_valid():
                form.save(fake_request)
                return Response({
                    'success': True,
                    'message': _("Si un compte existe avec cet email, un lien de réinitialisation a été envoyé.")
                })
            else:
                return Response({
                    'success': True,  # Pour des raisons de sécurité, ne pas révéler si l'email existe
                    'message': _("Si un compte existe avec cet email, un lien de réinitialisation a été envoyé.")
                })

        except Exception as e:
            logger.exception("Erreur lors de la demande de réinitialisation")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# EVENT CHECK-IN API
# =============================================================================

class EventCheckInView(APIView):
    """
    POST /api/qr/event/<id>/check-in/
    Check-in à un événement via QR code.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, event_id):
        try:
            from apps.competitions.models import Event, Practitioner

            event = get_object_or_404(Event, id=event_id)
            practitioner_id = request.data.get('practitioner_id')

            # Trouver le pratiquant (soit par ID, soit via l'utilisateur connecté)
            if practitioner_id:
                practitioner = get_object_or_404(Practitioner, id=practitioner_id)
            else:
                practitioner = Practitioner.objects.filter(user=request.user).first()

            if not practitioner:
                return Response({
                    'success': False,
                    'message': _("Pratiquant non trouvé")
                }, status=status.HTTP_404_NOT_FOUND)

            # Enregistrer le check-in (à adapter selon le modèle)
            # EventRegistration ou EventAttendance selon l'implémentation

            return Response({
                'success': True,
                'message': _("Check-in effectué avec succès"),
                'event': {
                    'id': event.id,
                    'name': event.title,
                },
                'practitioner': {
                    'id': practitioner.id,
                    'name': practitioner.full_name,
                },
                'checked_in_at': timezone.now().isoformat()
            })

        except Exception as e:
            logger.exception("Erreur lors du check-in")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# PRACTITIONER CRUD API (Mobile)
# =============================================================================

class MobilePractitionerFormOptionsView(APIView):
    """
    GET /api/v1/mobile/practitioners/form-options/
    Retourne les disciplines et grades disponibles pour le formulaire.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            from apps.competitions.models import UserProfile, Discipline
            from apps.grades.models import Grade

            # Récupérer l'organisation de l'utilisateur
            user_profile = UserProfile.objects.filter(user=request.user).first()
            organization = user_profile.organization if user_profile else None

            # Récupérer les disciplines
            disciplines_qs = Discipline.objects.filter(is_active=True)
            if organization:
                # Filtrer par organisation si disponible
                org_disciplines = organization.disciplines.all()
                if org_disciplines.exists():
                    disciplines_qs = org_disciplines.filter(is_active=True)

            disciplines = [{
                'id': str(d.id),
                'name': d.name,
            } for d in disciplines_qs.order_by('name')]

            # Récupérer les grades
            grades_qs = Grade.objects.filter(is_active=True)
            if organization:
                # Filtrer par disciplines de l'organisation
                org_discipline_ids = [d.id for d in disciplines_qs]
                if org_discipline_ids:
                    grades_qs = grades_qs.filter(
                        Q(discipline_id__in=org_discipline_ids) | Q(discipline__isnull=True)
                    )

            grades = [{
                'id': str(g.id),
                'name': g.name,
                'level': getattr(g, 'level', 0) or 0,
                'discipline_id': str(g.discipline_id) if g.discipline_id else None,
            } for g in grades_qs.order_by('level', 'name')]

            return Response({
                'success': True,
                'disciplines': disciplines,
                'grades': grades,
            })

        except Exception as e:
            logger.exception("Erreur lors de la récupération des options du formulaire")
            return Response({
                'success': False,
                'disciplines': [],
                'grades': [],
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MobilePractitionerListCreateView(APIView):
    """
    GET /api/v1/mobile/practitioners/
    Liste les pratiquants de l'organisation de l'utilisateur.

    POST /api/v1/mobile/practitioners/
    Crée un nouveau pratiquant.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            from apps.competitions.models import Practitioner, UserProfile

            # Récupérer l'organisation de l'utilisateur
            user_profile = UserProfile.objects.filter(user=request.user).first()
            if not user_profile or not user_profile.organization:
                return Response({
                    'success': False,
                    'message': _("Aucune organisation associée")
                }, status=status.HTTP_400_BAD_REQUEST)

            organization = user_profile.organization

            # Vérifier les permissions (club manager ou admin)
            if not (request.user.is_staff or user_profile.role in ['club_manager', 'coach', 'admin', 'federation_admin']):
                return Response({
                    'success': False,
                    'message': _("Permissions insuffisantes")
                }, status=status.HTTP_403_FORBIDDEN)

            practitioners = Practitioner.objects.filter(
                organization=organization
            ).select_related('user').order_by('last_name', 'first_name')

            return Response({
                'success': True,
                'practitioners': [{
                    'id': p.id,
                    'first_name': p.first_name,
                    'last_name': p.last_name,
                    'full_name': p.full_name,
                    'email': p.email,
                    'phone': getattr(p, 'phone', None),
                    'photo': request.build_absolute_uri(p.photo.url) if p.photo else None,
                    'birth_date': p.birth_date.isoformat() if p.birth_date else None,
                    'gender': p.gender,
                    'license_number': p.license_number,
                    'grade': p.current_grade.name if hasattr(p, 'current_grade') and p.current_grade else None,
                    'status': 'active' if getattr(p, 'is_active', True) else 'inactive',
                } for p in practitioners],
                'total': practitioners.count(),
            })

        except Exception as e:
            logger.exception("Erreur lors de la récupération des pratiquants")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            from apps.competitions.models import Practitioner, UserProfile

            # Récupérer l'organisation de l'utilisateur
            user_profile = UserProfile.objects.filter(user=request.user).first()
            if not user_profile or not user_profile.organization:
                return Response({
                    'success': False,
                    'message': _("Aucune organisation associée")
                }, status=status.HTTP_400_BAD_REQUEST)

            organization = user_profile.organization

            # Vérifier les permissions
            if not (request.user.is_staff or user_profile.role in ['club_manager', 'coach', 'admin', 'federation_admin']):
                return Response({
                    'success': False,
                    'message': _("Permissions insuffisantes pour créer un pratiquant")
                }, status=status.HTTP_403_FORBIDDEN)

            # -- Vérification limite membres (Free tier) --
            from apps.finances.services.subscription_service import get_subscription_info
            sub_info = get_subscription_info(organization)
            if sub_info.get('is_at_limit', False):
                return Response({
                    'success': False,
                    'error': 'member_limit_reached',
                    'message': _("Limite de membres atteinte (%(max)s). Passez au plan Premium.") % {'max': sub_info.get('max_members', 10)},
                    'max_members': sub_info.get('max_members', 10),
                    'current_members': sub_info.get('members_count', 0),
                }, status=status.HTTP_403_FORBIDDEN)

            # Valider les données requises
            first_name = request.data.get('first_name', '').strip()
            last_name = request.data.get('last_name', '').strip()

            if not first_name or not last_name:
                return Response({
                    'success': False,
                    'message': _("Le prénom et le nom sont requis")
                }, status=status.HTTP_400_BAD_REQUEST)

            # Créer le pratiquant
            practitioner = Practitioner.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=request.data.get('email', '').strip() or None,
                organization=organization,
                gender=request.data.get('gender', ''),
                birth_date=request.data.get('birth_date') or None,
            )

            # Ajouter les champs optionnels s'ils existent sur le modèle
            if hasattr(practitioner, 'phone'):
                practitioner.phone = request.data.get('phone', '').strip() or None
            if hasattr(practitioner, 'address'):
                practitioner.address = request.data.get('address', '').strip() or None
            if hasattr(practitioner, 'city'):
                practitioner.city = request.data.get('city', '').strip() or None
            if hasattr(practitioner, 'postal_code'):
                practitioner.postal_code = request.data.get('postal_code', '').strip() or None

            # Contact d'urgence
            emergency_contact = request.data.get('emergency_contact')
            if emergency_contact and hasattr(practitioner, 'emergency_contact_name'):
                practitioner.emergency_contact_name = emergency_contact.get('name', '')
                practitioner.emergency_contact_phone = emergency_contact.get('phone', '')
                practitioner.emergency_contact_relation = emergency_contact.get('relation', '')

            practitioner.save()

            # Sync Stripe quantity if premium
            from apps.finances.services.subscription_service import sync_stripe_member_count
            sync_stripe_member_count(organization)

            return Response({
                'success': True,
                'message': _("Pratiquant créé avec succès"),
                'practitioner': {
                    'id': practitioner.id,
                    'first_name': practitioner.first_name,
                    'last_name': practitioner.last_name,
                    'full_name': practitioner.full_name,
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.exception("Erreur lors de la création du pratiquant")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MobilePractitionerDetailView(APIView):
    """
    GET /api/v1/mobile/practitioners/<id>/
    Récupère les détails d'un pratiquant.

    PATCH /api/v1/mobile/practitioners/<id>/
    Met à jour un pratiquant.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, practitioner_id):
        try:
            from apps.competitions.models import Practitioner, UserProfile

            # Vérifier les permissions
            user_profile = UserProfile.objects.filter(user=request.user).first()

            practitioner = get_object_or_404(Practitioner, id=practitioner_id)

            # Vérifier que le pratiquant appartient à l'organisation de l'utilisateur
            if user_profile and user_profile.organization:
                if practitioner.organization != user_profile.organization:
                    if not request.user.is_staff:
                        return Response({
                            'success': False,
                            'message': _("Accès non autorisé")
                        }, status=status.HTTP_403_FORBIDDEN)

            return Response({
                'success': True,
                'practitioner': {
                    'id': practitioner.id,
                    'first_name': practitioner.first_name,
                    'last_name': practitioner.last_name,
                    'full_name': practitioner.full_name,
                    'email': practitioner.email,
                    'phone': getattr(practitioner, 'phone', None),
                    'photo': practitioner.photo.url if practitioner.photo else None,
                    'birth_date': practitioner.birth_date.isoformat() if practitioner.birth_date else None,
                    'gender': practitioner.gender,
                    'license_number': practitioner.license_number,
                    'grade': practitioner.current_grade.name if hasattr(practitioner, 'current_grade') and practitioner.current_grade else None,
                    'address': getattr(practitioner, 'address', None),
                    'city': getattr(practitioner, 'city', None),
                    'postal_code': getattr(practitioner, 'postal_code', None),
                    'nationality': getattr(practitioner, 'nationality', None),
                    'medical_certificate_date': practitioner.medical_certificate_expiry.isoformat() if hasattr(practitioner, 'medical_certificate_expiry') and practitioner.medical_certificate_expiry else None,
                    'registration_date': practitioner.created_at.isoformat() if hasattr(practitioner, 'created_at') and practitioner.created_at else None,
                    'emergency_contact': {
                        'name': getattr(practitioner, 'emergency_contact_name', None),
                        'phone': getattr(practitioner, 'emergency_contact_phone', None),
                        'relation': getattr(practitioner, 'emergency_contact_relation', None),
                    } if hasattr(practitioner, 'emergency_contact_name') else None,
                    'organization': {
                        'id': practitioner.organization.id,
                        'name': practitioner.organization.name,
                    } if practitioner.organization else None,
                    'status': 'active' if getattr(practitioner, 'is_active', True) else 'inactive',
                    'has_account': practitioner.user is not None,
                    'username': practitioner.user.username if practitioner.user else None,
                    'user_role': (
                        UserProfile.objects.filter(user=practitioner.user).values_list('role', flat=True).first()
                        if practitioner.user else None
                    ),
                    'is_coach': getattr(practitioner, 'is_coach', False),
                }
            })

        except Exception as e:
            logger.exception("Erreur lors de la récupération du pratiquant")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, practitioner_id):
        try:
            from apps.competitions.models import Practitioner, UserProfile

            # Vérifier les permissions
            user_profile = UserProfile.objects.filter(user=request.user).first()
            if not user_profile or not user_profile.organization:
                return Response({
                    'success': False,
                    'message': _("Aucune organisation associée")
                }, status=status.HTTP_400_BAD_REQUEST)

            # Vérifier le rôle
            if not (request.user.is_staff or user_profile.role in ['club_manager', 'coach', 'admin', 'federation_admin']):
                return Response({
                    'success': False,
                    'message': _("Permissions insuffisantes")
                }, status=status.HTTP_403_FORBIDDEN)

            practitioner = get_object_or_404(Practitioner, id=practitioner_id)

            # Vérifier que le pratiquant appartient à l'organisation
            if practitioner.organization != user_profile.organization:
                if not request.user.is_staff:
                    return Response({
                        'success': False,
                        'message': _("Accès non autorisé")
                    }, status=status.HTTP_403_FORBIDDEN)

            # Mettre à jour les champs
            data = request.data

            if 'first_name' in data:
                practitioner.first_name = data['first_name'].strip()
            if 'last_name' in data:
                practitioner.last_name = data['last_name'].strip()
            if 'email' in data:
                practitioner.email = data['email'].strip() or None
            if 'gender' in data:
                practitioner.gender = data['gender']
            if 'birth_date' in data:
                practitioner.birth_date = data['birth_date'] or None

            # Champs optionnels
            if 'phone' in data and hasattr(practitioner, 'phone'):
                practitioner.phone = data['phone'].strip() or None
            if 'address' in data and hasattr(practitioner, 'address'):
                practitioner.address = data['address'].strip() or None
            if 'city' in data and hasattr(practitioner, 'city'):
                practitioner.city = data['city'].strip() or None
            if 'postal_code' in data and hasattr(practitioner, 'postal_code'):
                practitioner.postal_code = data['postal_code'].strip() or None

            # Contact d'urgence
            emergency_contact = data.get('emergency_contact')
            if emergency_contact and hasattr(practitioner, 'emergency_contact_name'):
                practitioner.emergency_contact_name = emergency_contact.get('name', '')
                practitioner.emergency_contact_phone = emergency_contact.get('phone', '')
                practitioner.emergency_contact_relation = emergency_contact.get('relation', '')

            practitioner.save()

            return Response({
                'success': True,
                'message': _("Pratiquant mis à jour avec succès"),
                'practitioner': {
                    'id': practitioner.id,
                    'first_name': practitioner.first_name,
                    'last_name': practitioner.last_name,
                    'full_name': practitioner.full_name,
                }
            })

        except Exception as e:
            logger.exception("Erreur lors de la mise à jour du pratiquant")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# PRACTITIONER ACCOUNT MANAGEMENT API (Mobile)
# =============================================================================

class MobilePractitionerActivateAccountView(APIView):
    """
    POST /api/v1/mobile/practitioners/<id>/activate-account/
    Creates a login account for a practitioner and sends credentials by email.
    If account already exists, resets password and resends credentials.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, practitioner_id):
        try:
            from apps.competitions.models import Practitioner, UserProfile
            from apps.competitions.services.account_service import PractitionerAccountService

            # Check permissions
            user_profile = UserProfile.objects.filter(user=request.user).first()
            if not user_profile or not user_profile.organization:
                return Response({
                    'success': False,
                    'message': _("Aucune organisation associée")
                }, status=status.HTTP_400_BAD_REQUEST)

            if not (request.user.is_staff or user_profile.role in ['club_manager', 'coach', 'admin', 'federation_admin']):
                return Response({
                    'success': False,
                    'message': _("Permissions insuffisantes")
                }, status=status.HTTP_403_FORBIDDEN)

            practitioner = get_object_or_404(Practitioner, id=practitioner_id)

            # Check organization
            if practitioner.organization != user_profile.organization and not request.user.is_staff:
                return Response({
                    'success': False,
                    'message': _("Accès non autorisé")
                }, status=status.HTTP_403_FORBIDDEN)

            # Check email
            if not practitioner.email:
                return Response({
                    'success': False,
                    'message': _("Ce pratiquant n'a pas d'adresse email. Ajoutez un email d'abord.")
                }, status=status.HTTP_400_BAD_REQUEST)

            DEFAULT_PASSWORD = PractitionerAccountService.DEFAULT_PASSWORD

            if practitioner.user:
                # Account exists - reset password and resend
                user = practitioner.user
                user.set_password(DEFAULT_PASSWORD)
                if practitioner.email:
                    user.email = practitioner.email
                user.save()

                email_sent = PractitionerAccountService.send_credentials_email(
                    user, DEFAULT_PASSWORD, practitioner
                )

                return Response({
                    'success': True,
                    'message': _("Identifiants renvoyés par email"),
                    'username': user.username,
                    'email_sent': email_sent,
                    'account_created': False,
                })
            else:
                # Create new account
                username = PractitionerAccountService.generate_username(
                    practitioner.first_name, practitioner.last_name
                )

                result = PractitionerAccountService.create_account(
                    practitioner=practitioner,
                    username=username,
                    password=DEFAULT_PASSWORD,
                    send_email=True,
                    created_by=request.user,
                )

                if result.get('success'):
                    return Response({
                        'success': True,
                        'message': _("Compte créé et identifiants envoyés par email"),
                        'username': result.get('user', {}).username if hasattr(result.get('user'), 'username') else username,
                        'email_sent': True,
                        'account_created': True,
                    })
                else:
                    return Response({
                        'success': False,
                        'message': result.get('message', _("Erreur lors de la création du compte")),
                    }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.exception("Error activating practitioner account")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MobilePractitionerAssignRoleView(APIView):
    """
    POST /api/v1/mobile/practitioners/<id>/assign-role/
    Assigns a role to a practitioner's user account.
    Requires the practitioner to have an active account.
    """
    permission_classes = [IsAuthenticated]

    VALID_ROLES = ['participant', 'coach', 'judge', 'club_manager']

    def post(self, request, practitioner_id):
        try:
            from apps.competitions.models import Practitioner, UserProfile

            # Check permissions
            user_profile = UserProfile.objects.filter(user=request.user).first()
            if not user_profile or not user_profile.organization:
                return Response({
                    'success': False,
                    'message': _("Aucune organisation associée")
                }, status=status.HTTP_400_BAD_REQUEST)

            if not (request.user.is_staff or user_profile.role in ['club_manager', 'admin', 'federation_admin']):
                return Response({
                    'success': False,
                    'message': _("Permissions insuffisantes")
                }, status=status.HTTP_403_FORBIDDEN)

            practitioner = get_object_or_404(Practitioner, id=practitioner_id)

            # Check organization
            if practitioner.organization != user_profile.organization and not request.user.is_staff:
                return Response({
                    'success': False,
                    'message': _("Accès non autorisé")
                }, status=status.HTTP_403_FORBIDDEN)

            # Check if practitioner has an account
            if not practitioner.user:
                return Response({
                    'success': False,
                    'message': _("Ce pratiquant n'a pas de compte utilisateur. Activez son compte d'abord.")
                }, status=status.HTTP_400_BAD_REQUEST)

            role = request.data.get('role')
            if not role or role not in self.VALID_ROLES:
                return Response({
                    'success': False,
                    'message': _("Rôle invalide. Rôles possibles: participant, coach, judge, club_manager")
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get or create the practitioner's UserProfile
            target_profile, created = UserProfile.objects.get_or_create(
                user=practitioner.user,
                defaults={
                    'organization': practitioner.organization,
                    'role': role,
                }
            )

            if not created:
                target_profile.role = role
                if not target_profile.organization:
                    target_profile.organization = practitioner.organization
                target_profile.save()

            # Also update is_coach on Practitioner if relevant
            if role == 'coach':
                practitioner.is_coach = True
                practitioner.save(update_fields=['is_coach'])
            elif practitioner.is_coach and role != 'coach':
                practitioner.is_coach = False
                practitioner.save(update_fields=['is_coach'])

            role_labels = {
                'participant': _("Participant"),
                'coach': _("Coach"),
                'judge': _("Juge/Arbitre"),
                'club_manager': _("Responsable de club"),
            }

            return Response({
                'success': True,
                'message': _("Rôle '%(role)s' attribué avec succès") % {'role': role_labels.get(role, role)},
                'role': role,
                'role_label': str(role_labels.get(role, role)),
            })

        except Exception as e:
            logger.exception("Error assigning role to practitioner")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# EVENT REGISTRATION API (Mobile) - Club Manager Bulk Registration
# =============================================================================

class MobileEventRegistrationOptionsView(APIView):
    """
    GET /api/v1/mobile/events/<event_id>/registration-options/
    Retourne les options d'inscription pour un événement (catégories, types, etc.)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, event_id):
        try:
            from apps.competitions.models import (
                Event, Competition, UserProfile, Practitioner,
                CompetitionCategory, CompetitionType
            )
            from apps.competitions.models.event import EventParticipant

            # Vérifier les permissions (club manager ou admin)
            user_profile = UserProfile.objects.filter(user=request.user).first()

            # Résoudre l'organisation avec plusieurs stratégies (comme get_user_club)
            organization = None
            if user_profile and user_profile.organization:
                organization = user_profile.organization
                logger.info(f"[RegistrationOptions] Org via UserProfile: {organization} (id={organization.id})")

            if not organization:
                # Fallback: chercher via Club ownership
                from apps.competitions.models import Club
                owned_club = Club.objects.filter(owner=request.user).select_related('organization').first()
                if owned_club and owned_club.organization:
                    organization = owned_club.organization
                    logger.info(f"[RegistrationOptions] Org via owned Club: {organization} (id={organization.id})")

            if not organization:
                # Fallback: chercher via Practitioner
                from django.db.models import Q
                practitioner_record = Practitioner.objects.filter(
                    Q(user=request.user) | Q(email=request.user.email)
                ).select_related('organization').first()
                if practitioner_record and practitioner_record.organization:
                    organization = practitioner_record.organization
                    logger.info(f"[RegistrationOptions] Org via Practitioner: {organization} (id={organization.id})")

            if not organization:
                # Fallback: middleware
                if hasattr(request, 'user_organization') and request.user_organization:
                    organization = request.user_organization
                    logger.info(f"[RegistrationOptions] Org via middleware: {organization}")

            if not organization:
                logger.warning(f"[RegistrationOptions] No organization found for user {request.user.username} (id={request.user.id})")
                return Response({
                    'success': False,
                    'message': _("Aucune organisation associée")
                }, status=status.HTTP_400_BAD_REQUEST)

            user_role = user_profile.role if user_profile else None
            if not (request.user.is_staff or user_role in ['club_manager', 'coach', 'admin', 'federation_admin']):
                return Response({
                    'success': False,
                    'message': _("Permissions insuffisantes pour inscrire des pratiquants")
                }, status=status.HTTP_403_FORBIDDEN)

            # Chercher l'événement ou la compétition
            event = None
            competition = None
            event_type = None

            try:
                event = Event.objects.get(id=event_id)
                event_type = 'event'
            except Event.DoesNotExist:
                try:
                    competition = Competition.objects.get(id=event_id)
                    event_type = 'competition'
                except Competition.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': _("Événement non trouvé")
                    }, status=status.HTTP_404_NOT_FOUND)

            # Récupérer les pratiquants du club
            practitioners = Practitioner.objects.filter(
                organization=organization,
                is_active=True
            ).select_related('grade').order_by('last_name', 'first_name')

            logger.info(f"[RegistrationOptions] User={request.user.username}, Org={organization} (id={organization.id}), "
                        f"Event/Comp={event_type} id={event_id}, Practitioners found={practitioners.count()}")

            practitioners_data = [{
                'id': str(p.id),
                'name': p.full_name,
                'first_name': p.first_name,
                'last_name': p.last_name,
                'grade': getattr(p, 'grade_text', None) or (p.grade.name if hasattr(p, 'grade') and p.grade else None),
                'birth_date': str(p.birth_date) if p.birth_date else None,
                'photo': request.build_absolute_uri(p.photo.url) if p.photo else None,
                'is_registered': False,  # Sera mis à jour ci-dessous
            } for p in practitioners]

            # Options spécifiques selon le type
            categories = []
            competition_types = []
            roles = [
                {'id': 'competitor', 'name': _('Compétiteur')},
                {'id': 'coach', 'name': _('Coach')},
                {'id': 'judge', 'name': _('Juge')},
                {'id': 'volunteer', 'name': _('Bénévole')},
            ]

            if event_type == 'competition' and competition:
                # Récupérer les pratiquants déjà inscrits
                from apps.competitions.models import CompetitionRegistration
                registered_ids = set(
                    CompetitionRegistration.objects.filter(
                        competition=competition
                    ).values_list('practitioner_id', flat=True)
                )

                # Marquer les pratiquants déjà inscrits
                for p in practitioners_data:
                    p['is_registered'] = int(p['id']) in registered_ids

                # Récupérer les catégories de la compétition
                if hasattr(competition, 'categories'):
                    categories = [{
                        'id': str(c.id),
                        'name': c.name,
                        'description': getattr(c, 'description', ''),
                        'competition_type_id': str(c.competition_type_id) if c.competition_type_id else None,
                    } for c in competition.categories.select_related('competition_type').all()]

                # Récupérer les types de compétition
                if hasattr(competition, 'competition_types'):
                    competition_types = [{
                        'id': str(ct.id),
                        'name': ct.name,
                    } for ct in competition.competition_types.all()]

                return Response({
                    'success': True,
                    'event_type': 'competition',
                    'event': {
                        'id': competition.id,
                        'name': competition.title,
                        'date': str(competition.start_date) if competition.start_date else None,
                        'registration_deadline': str(competition.registration_deadline) if hasattr(competition, 'registration_deadline') and competition.registration_deadline else None,
                        'max_participants': getattr(competition, 'max_participants', None),
                        'current_participants': len(registered_ids),
                    },
                    'practitioners': practitioners_data,
                    'categories': categories,
                    'competition_types': competition_types,
                    'roles': roles,
                })

            else:
                # Événement générique
                registered_ids = set(
                    EventParticipant.objects.filter(
                        event=event
                    ).exclude(status='cancelled').values_list('practitioner_id', flat=True)
                )

                for p in practitioners_data:
                    p['is_registered'] = int(p['id']) in registered_ids

                return Response({
                    'success': True,
                    'event_type': 'event',
                    'event': {
                        'id': event.id,
                        'name': event.title,
                        'date': str(event.start_date) if event.start_date else None,
                        'registration_deadline': str(event.registration_deadline) if hasattr(event, 'registration_deadline') and event.registration_deadline else None,
                        'max_participants': getattr(event, 'max_participants', None),
                        'current_participants': len(registered_ids),
                    },
                    'practitioners': practitioners_data,
                    'categories': [],
                    'competition_types': [],
                    'roles': roles[:2],  # Seulement participant et coach pour les événements
                })

        except Exception as e:
            logger.exception("Erreur lors de la récupération des options d'inscription")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MobileEventBulkRegistrationView(APIView):
    """
    POST /api/v1/mobile/events/<event_id>/register-practitioners/
    Inscrit plusieurs pratiquants à un événement.

    Body: {
        "registrations": [
            {
                "practitioner_id": 123,
                "role": "competitor",
                "category_ids": [1, 2],
                "competition_type_ids": [1]
            },
            ...
        ]
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, event_id):
        try:
            from django.db import transaction
            from apps.competitions.models import (
                Event, Competition, UserProfile, Practitioner,
                CompetitionCategory, CompetitionType, CompetitionRegistration
            )
            from apps.competitions.models.event import EventParticipant

            # Vérifier les permissions
            user_profile = UserProfile.objects.filter(user=request.user).first()
            if not user_profile or not user_profile.organization:
                return Response({
                    'success': False,
                    'message': _("Aucune organisation associée")
                }, status=status.HTTP_400_BAD_REQUEST)

            if not (request.user.is_staff or user_profile.role in ['club_manager', 'coach', 'admin', 'federation_admin']):
                return Response({
                    'success': False,
                    'message': _("Permissions insuffisantes")
                }, status=status.HTTP_403_FORBIDDEN)

            registrations = request.data.get('registrations', [])
            if not registrations:
                return Response({
                    'success': False,
                    'message': _("Aucune inscription fournie")
                }, status=status.HTTP_400_BAD_REQUEST)

            # Chercher l'événement ou la compétition
            event = None
            competition = None
            event_type = None

            try:
                event = Event.objects.get(id=event_id)
                event_type = 'event'
            except Event.DoesNotExist:
                try:
                    competition = Competition.objects.get(id=event_id)
                    event_type = 'competition'
                except Competition.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': _("Événement non trouvé")
                    }, status=status.HTTP_404_NOT_FOUND)

            results = []
            success_count = 0
            error_count = 0

            with transaction.atomic():
                for reg in registrations:
                    practitioner_id = reg.get('practitioner_id')
                    role = reg.get('role', 'competitor')

                    try:
                        # Vérifier que le pratiquant existe et appartient au club
                        practitioner = Practitioner.objects.get(
                            id=practitioner_id,
                            organization=user_profile.organization
                        )

                        if event_type == 'competition':
                            # Vérifier si déjà inscrit
                            existing = CompetitionRegistration.objects.filter(
                                competition=competition,
                                practitioner=practitioner
                            ).first()

                            if existing:
                                results.append({
                                    'practitioner_id': practitioner_id,
                                    'practitioner_name': practitioner.full_name,
                                    'success': False,
                                    'error': _("Déjà inscrit à cette compétition")
                                })
                                error_count += 1
                                continue

                            # Créer l'inscription à la compétition
                            registration = CompetitionRegistration.objects.create(
                                competition=competition,
                                practitioner=practitioner,
                                is_competitor=(role == 'competitor'),
                                is_technical_judge=(role == 'judge'),
                                is_combat_referee=(role == 'referee'),
                                is_volunteer=(role == 'volunteer'),
                                is_coach=(role == 'coach'),
                                status='pending',
                            )

                            # Ajouter les catégories
                            category_ids = reg.get('category_ids', [])
                            if category_ids:
                                categories = CompetitionCategory.objects.filter(id__in=category_ids)
                                registration.categories.set(categories)
                            else:
                                # Auto-assign categories based on practitioner profile
                                auto_categories = self._get_eligible_categories(
                                    practitioner, competition
                                )
                                if auto_categories:
                                    registration.categories.set(auto_categories)

                            # Ajouter les types de compétition
                            type_ids = reg.get('competition_type_ids', [])
                            if type_ids:
                                comp_types = CompetitionType.objects.filter(id__in=type_ids)
                                registration.competition_types.set(comp_types)
                            else:
                                # Auto-assign competition types from matched categories
                                auto_type_ids = registration.categories.values_list(
                                    'competition_type_id', flat=True
                                ).distinct()
                                if auto_type_ids:
                                    from apps.competitions.models import CompetitionType as CT
                                    registration.competition_types.set(
                                        CT.objects.filter(id__in=auto_type_ids)
                                    )

                            results.append({
                                'practitioner_id': practitioner_id,
                                'practitioner_name': practitioner.full_name,
                                'success': True,
                                'registration_id': registration.id
                            })
                            success_count += 1

                        else:
                            # Événement générique
                            existing = EventParticipant.objects.filter(
                                event=event,
                                practitioner=practitioner
                            ).exclude(status='cancelled').first()

                            if existing:
                                results.append({
                                    'practitioner_id': practitioner_id,
                                    'practitioner_name': practitioner.full_name,
                                    'success': False,
                                    'error': _("Déjà inscrit à cet événement")
                                })
                                error_count += 1
                                continue

                            # Vérifier la capacité
                            if event.max_participants:
                                current_count = EventParticipant.objects.filter(
                                    event=event
                                ).exclude(status='cancelled').count()

                                if current_count >= event.max_participants:
                                    results.append({
                                        'practitioner_id': practitioner_id,
                                        'practitioner_name': practitioner.full_name,
                                        'success': False,
                                        'error': _("Capacité maximale atteinte")
                                    })
                                    error_count += 1
                                    continue

                            # Créer l'inscription à l'événement
                            participant = EventParticipant.objects.create(
                                event=event,
                                practitioner=practitioner,
                                user=practitioner.user if hasattr(practitioner, 'user') and practitioner.user else None,
                                status='registered',
                                role=role,
                            )

                            results.append({
                                'practitioner_id': practitioner_id,
                                'practitioner_name': practitioner.full_name,
                                'success': True,
                                'participant_id': participant.id
                            })
                            success_count += 1

                    except Practitioner.DoesNotExist:
                        results.append({
                            'practitioner_id': practitioner_id,
                            'practitioner_name': None,
                            'success': False,
                            'error': _("Pratiquant non trouvé ou non autorisé")
                        })
                        error_count += 1

                    except Exception as e:
                        results.append({
                            'practitioner_id': practitioner_id,
                            'practitioner_name': None,
                            'success': False,
                            'error': str(e)
                        })
                        error_count += 1

            return Response({
                'success': success_count > 0,
                'message': _("{success} inscription(s) réussie(s), {errors} erreur(s)").format(
                    success=success_count,
                    errors=error_count
                ),
                'success_count': success_count,
                'error_count': error_count,
                'results': results
            })

        except Exception as e:
            logger.exception("Erreur lors de l'inscription en masse")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_eligible_categories(self, practitioner, competition):
        """
        Auto-assign categories based on practitioner's age, gender, and grade.
        Returns a list of matching CompetitionCategory objects.
        """
        from apps.competitions.models.categories import CompetitionCategory
        from datetime import date

        eligible = []
        categories = CompetitionCategory.objects.filter(
            competition=competition,
            registration_status='open'
        )

        # Calculate practitioner age
        p_age = None
        if practitioner.birth_date:
            today = date.today()
            p_age = today.year - practitioner.birth_date.year - (
                (today.month, today.day) < (practitioner.birth_date.month, practitioner.birth_date.day)
            )

        # Get practitioner gender
        p_gender = getattr(practitioner, 'gender', None) or ''

        # Get practitioner grade name for comparison
        p_grade = ''
        if practitioner.grade:
            p_grade = str(practitioner.grade.name) if hasattr(practitioner.grade, 'name') else str(practitioner.grade)
        elif practitioner.grade_text:
            p_grade = practitioner.grade_text

        for cat in categories:
            match = True

            # Check age range
            if cat.min_age is not None and p_age is not None:
                if p_age < cat.min_age:
                    match = False
            if cat.max_age is not None and p_age is not None:
                if p_age > cat.max_age:
                    match = False

            # Check gender
            if cat.gender and cat.gender != 'mixed':
                if p_gender and p_gender.lower() != cat.gender.lower():
                    # Handle M/F vs male/female
                    gender_map = {'m': 'male', 'f': 'female', 'h': 'male'}
                    p_norm = gender_map.get(p_gender.lower()[:1], p_gender.lower())
                    if p_norm != cat.gender.lower():
                        match = False

            # If no age/gender criteria at all, don't auto-match
            # (avoid assigning to every category)
            has_criteria = (cat.min_age is not None or cat.max_age is not None or
                          (cat.gender and cat.gender != 'mixed'))
            if not has_criteria:
                # Category has no filtering criteria — only match if name suggests it
                match = False

            if match:
                eligible.append(cat)

        return eligible


class MobileEventRegistrationsListView(APIView):
    """
    GET /api/v1/mobile/events/<event_id>/registrations/
    Liste les inscriptions à un événement.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, event_id):
        try:
            from apps.competitions.models import (
                Event, Competition, UserProfile, CompetitionRegistration
            )
            from apps.competitions.models.event import EventParticipant

            # Vérifier les permissions
            user_profile = UserProfile.objects.filter(user=request.user).first()
            if not user_profile:
                return Response({
                    'success': False,
                    'message': _("Profil utilisateur non trouvé")
                }, status=status.HTTP_400_BAD_REQUEST)

            # Chercher l'événement ou la compétition
            event = None
            competition = None

            try:
                event = Event.objects.get(id=event_id)
            except Event.DoesNotExist:
                try:
                    competition = Competition.objects.get(id=event_id)
                except Competition.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': _("Événement non trouvé")
                    }, status=status.HTTP_404_NOT_FOUND)

            registrations_data = []

            if competition:
                registrations = CompetitionRegistration.objects.filter(
                    competition=competition
                ).select_related('practitioner')

                # Filtrer par organisation si pas admin
                if not request.user.is_staff and user_profile.organization:
                    registrations = registrations.filter(
                        practitioner__organization=user_profile.organization
                    )

                for reg in registrations:
                    registrations_data.append({
                        'id': reg.id,
                        'practitioner_id': reg.practitioner_id,
                        'practitioner_name': reg.practitioner.full_name if reg.practitioner else None,
                        'status': reg.status,
                        'role': 'competitor' if reg.is_competitor else ('coach' if reg.is_coach else 'other'),
                        'registered_at': str(reg.created_at) if hasattr(reg, 'created_at') else None,
                    })

            else:
                participants = EventParticipant.objects.filter(
                    event=event
                ).exclude(status='cancelled')

                # Filtrer par organisation si pas admin
                if not request.user.is_staff and user_profile.organization:
                    participants = participants.filter(
                        practitioner__organization=user_profile.organization
                    )

                for p in participants:
                    registrations_data.append({
                        'id': p.id,
                        'practitioner_id': p.practitioner_id if p.practitioner else None,
                        'practitioner_name': p.practitioner.full_name if p.practitioner else (p.user.get_full_name() if p.user else 'Invité'),
                        'status': p.status,
                        'role': getattr(p, 'role', 'participant'),
                        'registered_at': str(p.registered_at) if hasattr(p, 'registered_at') else None,
                    })

            return Response({
                'success': True,
                'registrations': registrations_data,
                'total': len(registrations_data)
            })

        except Exception as e:
            logger.exception("Erreur lors de la récupération des inscriptions")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# REGISTRATION CATEGORY MANAGEMENT (Mobile)
# =============================================================================

class MobileRegistrationCategoriesView(APIView):
    """
    GET /api/v1/mobile/events/<event_id>/registrations/<registration_id>/categories/
    Returns all competition types and categories with selection status for a registration.
    Allows the mobile app to display a category picker when clicking on a practitioner name.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, event_id, registration_id):
        try:
            from apps.competitions.models import (
                Event, Competition, CompetitionRegistration,
                CompetitionCategory, CompetitionType, UserProfile
            )
            from datetime import date

            event = Event.objects.get(pk=event_id)
            competition = getattr(event, 'competition', None)
            if not competition:
                return Response({'error': 'Not a competition event'}, status=400)

            registration = CompetitionRegistration.objects.get(
                pk=registration_id, competition=competition
            )

            # Currently selected category IDs
            selected_cat_ids = set(registration.categories.values_list('id', flat=True))
            selected_type_ids = set(registration.competition_types.values_list('id', flat=True))

            # Practitioner info for age/grade display
            practitioner = registration.practitioner
            p_age = practitioner.age if hasattr(practitioner, 'age') else None
            p_gender = getattr(practitioner, 'gender', '') or ''
            p_grade = ''
            if practitioner.grade:
                p_grade = str(practitioner.grade.name) if hasattr(practitioner.grade, 'name') else str(practitioner.grade)
            elif practitioner.grade_text:
                p_grade = practitioner.grade_text

            # Build competition types with their categories
            comp_types = competition.competition_types.all()
            types_data = []

            for ct in comp_types:
                cats = CompetitionCategory.objects.filter(
                    competition=competition,
                    competition_type=ct
                ).order_by('name')

                cats_data = []
                for cat in cats:
                    # Check eligibility
                    eligible = True
                    reasons = []

                    if cat.min_age is not None and p_age is not None and p_age < cat.min_age:
                        eligible = False
                        reasons.append(f"Age min: {cat.min_age}")
                    if cat.max_age is not None and p_age is not None and p_age > cat.max_age:
                        eligible = False
                        reasons.append(f"Age max: {cat.max_age}")
                    if cat.gender and cat.gender != 'mixed' and p_gender:
                        gender_map = {'m': 'male', 'f': 'female', 'h': 'male'}
                        p_norm = gender_map.get(p_gender.lower()[:1], p_gender.lower())
                        if p_norm != cat.gender.lower():
                            eligible = False
                            reasons.append(f"Genre: {cat.get_gender_display()}")

                    cats_data.append({
                        'id': cat.id,
                        'name': cat.name,
                        'selected': cat.id in selected_cat_ids,
                        'eligible': eligible,
                        'reasons': reasons,
                        'gender': cat.gender,
                        'min_age': cat.min_age,
                        'max_age': cat.max_age,
                        'participants_count': cat.registrations.count() if hasattr(cat, 'registrations') else 0,
                    })

                types_data.append({
                    'id': ct.id,
                    'name': ct.name,
                    'selected': ct.id in selected_type_ids,
                    'categories': cats_data,
                    'categories_count': len(cats_data),
                })

            return Response({
                'registration_id': registration.id,
                'practitioner': {
                    'id': practitioner.id,
                    'name': practitioner.full_name,
                    'age': p_age,
                    'gender': p_gender,
                    'grade': p_grade,
                },
                'competition_types': types_data,
                'selected_categories_count': len(selected_cat_ids),
            })

        except CompetitionRegistration.DoesNotExist:
            return Response({'error': 'Registration not found'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class MobileRegistrationUpdateCategoriesView(APIView):
    """
    POST /api/v1/mobile/events/<event_id>/registrations/<registration_id>/update-categories/
    Updates the categories for a registration from the mobile category picker.

    Body: {
        "category_ids": [1, 2, 3],
        "competition_type_ids": [1, 2]  // optional, auto-derived if omitted
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, event_id, registration_id):
        try:
            from apps.competitions.models import (
                Event, Competition, CompetitionRegistration,
                CompetitionCategory, CompetitionType, UserProfile
            )

            event = Event.objects.get(pk=event_id)
            competition = getattr(event, 'competition', None)
            if not competition:
                return Response({'error': 'Not a competition event'}, status=400)

            registration = CompetitionRegistration.objects.get(
                pk=registration_id, competition=competition
            )

            category_ids = request.data.get('category_ids', [])
            type_ids = request.data.get('competition_type_ids', [])

            # Set categories
            categories = CompetitionCategory.objects.filter(
                id__in=category_ids, competition=competition
            )
            registration.categories.set(categories)

            # Set competition types (auto-derive from categories if not provided)
            if type_ids:
                comp_types = CompetitionType.objects.filter(id__in=type_ids)
                registration.competition_types.set(comp_types)
            else:
                auto_type_ids = categories.values_list('competition_type_id', flat=True).distinct()
                registration.competition_types.set(
                    CompetitionType.objects.filter(id__in=auto_type_ids)
                )

            return Response({
                'success': True,
                'message': f'{categories.count()} catégorie(s) assignée(s)',
                'categories_count': categories.count(),
                'category_ids': list(categories.values_list('id', flat=True)),
            })

        except CompetitionRegistration.DoesNotExist:
            return Response({'error': 'Registration not found'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=500)


# =============================================================================
# TASK MANAGEMENT API (Mobile) - Boards, Tasks, Kanban
# =============================================================================

class MobileTaskBoardListView(APIView):
    """
    GET /api/v1/mobile/tasks/boards/
    List all boards accessible to the current user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            from apps.task_management.models import Board
            from apps.task_management.utils import get_user_organizations

            user_orgs = get_user_organizations(request.user)

            if not user_orgs:
                # Fallback: try UserProfile.organization
                from apps.competitions.models import UserProfile
                user_profile = UserProfile.objects.filter(user=request.user).first()
                if user_profile and user_profile.organization:
                    user_orgs = [user_profile.organization.id]
                else:
                    return Response({
                        'success': True,
                        'boards': [],
                        'total': 0,
                    })

            boards = Board.objects.filter(
                organization__in=user_orgs,
                is_archived=False,
            ).select_related('created_by', 'organization').order_by('-updated_at')

            accessible_boards = list(boards)

            boards_data = []
            for board in accessible_boards:
                task_count = board.tasks.count()
                done_count = board.tasks.filter(status='done').count()
                boards_data.append({
                    'id': board.id,
                    'name': board.name,
                    'description': board.description or '',
                    'board_type': board.board_type,
                    'color_theme': board.color_theme,
                    'is_public': board.is_public,
                    'task_count': task_count,
                    'completed_count': done_count,
                    'progress': round((done_count / task_count * 100), 1) if task_count > 0 else 0,
                    'created_by': board.created_by.get_full_name() or board.created_by.username if board.created_by else None,
                    'updated_at': board.updated_at.isoformat() if board.updated_at else None,
                })

            return Response({
                'success': True,
                'boards': boards_data,
                'total': len(boards_data),
            })

        except Exception as e:
            logger.exception("Error fetching task boards")
            return Response({
                'success': False,
                'message': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MobileTaskBoardDetailView(APIView):
    """
    GET /api/v1/mobile/tasks/boards/<board_id>/
    Get board detail with columns and tasks (Kanban data).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, board_id):
        try:
            from apps.task_management.models import Board, Column, Task
            from django.db.models import Count

            board = Board.objects.select_related('created_by', 'organization').get(id=board_id)

            if not board.can_access(request.user):
                return Response({
                    'success': False,
                    'message': _("Accès refusé à ce tableau"),
                }, status=status.HTTP_403_FORBIDDEN)

            # Helper: get photo URL for a user (via Practitioner)
            def _get_member_photo(user_id):
                try:
                    from apps.competitions.models import Practitioner as _P
                    p = _P.objects.filter(user_id=user_id).first()
                    if p and p.photo:
                        url = p.photo.url
                        if url and not url.startswith('http'):
                            url = request.build_absolute_uri(url)
                        return url
                except Exception:
                    pass
                return None

            # Get columns with task counts
            columns = board.columns.all().annotate(
                task_count_val=Count('tasks')
            ).order_by('position')

            columns_data = []
            for col in columns:
                tasks = col.tasks.select_related('created_by').prefetch_related(
                    'assignments__assignee'
                ).order_by('position')

                tasks_data = []
                for task in tasks:
                    assignees = [{
                        'id': a.assignee.id,
                        'name': a.assignee.get_full_name() or a.assignee.username,
                        'role': a.role,
                        'photo_url': _get_member_photo(a.assignee.id),
                    } for a in task.assignments.filter(is_active=True)]

                    tasks_data.append({
                        'id': task.id,
                        'title': task.title,
                        'description': task.description[:200] if task.description else '',
                        'status': task.status,
                        'priority': task.priority,
                        'position': task.position,
                        'due_date': task.due_date.isoformat() if task.due_date else None,
                        'is_overdue': task.is_overdue,
                        'assignees': assignees,
                        'labels': task.labels or [],
                        'comments_count': task.comments.count(),
                        'has_subtasks': task.subtasks.exists(),
                        'subtask_progress': task.get_progress_percentage() if task.subtasks.exists() else None,
                        'created_by': task.created_by.get_full_name() or task.created_by.username if task.created_by else None,
                    })

                columns_data.append({
                    'id': col.id,
                    'name': col.name,
                    'position': col.position,
                    'color': col.color,
                    'wip_limit': col.wip_limit,
                    'task_count': len(tasks_data),
                    'is_done_column': col.is_done_column,
                    'tasks': tasks_data,
                })

            # Get organization members for assignee picker (multiple sources)
            members_map = {}
            org = board.organization

            if org:
                from apps.organizations.models import OrganizationMember
                # Source 1: OrganizationMember
                for m in OrganizationMember.objects.filter(
                    organization=org, is_active=True
                ).select_related('user'):
                    members_map[m.user.id] = {
                        'id': m.user.id,
                        'name': m.user.get_full_name() or m.user.username,
                        'role': m.get_role_display() if hasattr(m, 'get_role_display') else m.role,
                        'photo_url': _get_member_photo(m.user.id),
                    }
                # Source 2: Practitioners with user accounts
                from apps.competitions.models import Practitioner
                for p in Practitioner.objects.filter(
                    organization=org, user__isnull=False, status='active'
                ).select_related('user'):
                    if p.user_id not in members_map:
                        photo_url = None
                        if p.photo:
                            try:
                                photo_url = p.photo.url
                                if photo_url and not photo_url.startswith('http'):
                                    photo_url = request.build_absolute_uri(photo_url)
                            except Exception:
                                pass
                        members_map[p.user_id] = {
                            'id': p.user_id,
                            'name': p.user.get_full_name() or f"{p.first_name} {p.last_name}".strip() or p.user.username,
                            'role': str(_('Pratiquant')),
                            'photo_url': photo_url,
                        }
                # Source 3: UserProfiles linked to org
                from apps.competitions.models import UserProfile
                for up in UserProfile.objects.filter(organization=org).select_related('user'):
                    if up.user_id not in members_map:
                        members_map[up.user_id] = {
                            'id': up.user_id,
                            'name': up.user.get_full_name() or up.user.username,
                            'role': up.get_role_display() if hasattr(up, 'get_role_display') else (up.role or ''),
                            'photo_url': _get_member_photo(up.user_id),
                        }
            members_data = sorted(members_map.values(), key=lambda m: m['name'].lower())

            return Response({
                'success': True,
                'board': {
                    'id': board.id,
                    'name': board.name,
                    'description': board.description or '',
                    'board_type': board.board_type,
                    'color_theme': board.color_theme,
                    'can_edit': board.can_edit(request.user),
                    'task_count': board.tasks.count(),
                    'completed_count': board.tasks.filter(status='done').count(),
                },
                'columns': columns_data,
                'members': members_data,
            })

        except Board.DoesNotExist:
            return Response({
                'success': False,
                'message': _("Tableau non trouvé"),
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception("Error fetching board detail")
            return Response({
                'success': False,
                'message': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MobileTaskMyTasksView(APIView):
    """
    GET /api/v1/mobile/tasks/my-tasks/
    Get tasks assigned to the current user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            from apps.task_management.models import Task, TaskAssignment
            from django.utils import timezone

            tasks = Task.objects.filter(
                assignments__assignee=request.user,
                assignments__is_active=True,
            ).select_related('board', 'column', 'created_by').prefetch_related(
                'assignments__assignee'
            ).distinct().order_by('-updated_at')

            status_filter = request.query_params.get('status')
            if status_filter:
                tasks = tasks.filter(status=status_filter)

            tasks_data = []
            for task in tasks[:100]:
                assignees = [{
                    'id': a.assignee.id,
                    'name': a.assignee.get_full_name() or a.assignee.username,
                } for a in task.assignments.filter(is_active=True)]

                tasks_data.append({
                    'id': task.id,
                    'title': task.title,
                    'description': task.description[:200] if task.description else '',
                    'status': task.status,
                    'priority': task.priority,
                    'board': {
                        'id': task.board.id,
                        'name': task.board.name,
                    },
                    'column': {
                        'id': task.column.id,
                        'name': task.column.name,
                    },
                    'due_date': task.due_date.isoformat() if task.due_date else None,
                    'is_overdue': task.is_overdue,
                    'assignees': assignees,
                    'labels': task.labels or [],
                    'comments_count': task.comments.count(),
                    'created_at': task.created_at.isoformat(),
                })

            # Stats
            overdue_count = Task.objects.filter(
                assignments__assignee=request.user,
                assignments__is_active=True,
                due_date__lt=timezone.now(),
                status__in=['todo', 'in_progress', 'in_review'],
            ).distinct().count()

            return Response({
                'success': True,
                'tasks': tasks_data,
                'total': len(tasks_data),
                'overdue_count': overdue_count,
            })

        except Exception as e:
            logger.exception("Error fetching my tasks")
            return Response({
                'success': False,
                'message': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MobileTaskDetailView(APIView):
    """
    GET /api/v1/mobile/tasks/<task_id>/
    Get full task detail with comments and activity.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        try:
            from apps.task_management.models import Task

            task = Task.objects.select_related(
                'board', 'column', 'created_by', 'parent_task'
            ).prefetch_related(
                'assignments__assignee',
                'comments__author',
                'subtasks',
            ).get(id=task_id)

            if not task.board.can_access(request.user):
                return Response({
                    'success': False,
                    'message': _("Accès refusé"),
                }, status=status.HTTP_403_FORBIDDEN)

            # Helper: get photo URL for a user (via Practitioner)
            def _get_photo(uid):
                try:
                    from apps.competitions.models import Practitioner as _P
                    p = _P.objects.filter(user_id=uid).first()
                    if p and p.photo:
                        url = p.photo.url
                        if url and not url.startswith('http'):
                            url = request.build_absolute_uri(url)
                        return url
                except Exception:
                    pass
                return None

            assignees = [{
                'id': a.assignee.id,
                'name': a.assignee.get_full_name() or a.assignee.username,
                'role': a.role,
                'role_display': a.get_role_display(),
                'photo_url': _get_photo(a.assignee.id),
            } for a in task.assignments.filter(is_active=True)]

            comments = [{
                'id': c.id,
                'content': c.content,
                'author': c.author.get_full_name() or c.author.username,
                'author_id': c.author.id,
                'created_at': c.created_at.isoformat(),
                'is_edited': c.is_edited,
            } for c in task.comments.select_related('author').order_by('-created_at')[:50]]

            subtasks = [{
                'id': s.id,
                'title': s.title,
                'status': s.status,
                'priority': s.priority,
            } for s in task.subtasks.all().order_by('position')]

            return Response({
                'success': True,
                'task': {
                    'id': task.id,
                    'title': task.title,
                    'description': task.description or '',
                    'status': task.status,
                    'priority': task.priority,
                    'board': {
                        'id': task.board.id,
                        'name': task.board.name,
                    },
                    'column': {
                        'id': task.column.id,
                        'name': task.column.name,
                    },
                    'due_date': task.due_date.isoformat() if task.due_date else None,
                    'start_date': task.start_date.isoformat() if task.start_date else None,
                    'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                    'is_overdue': task.is_overdue,
                    'estimated_hours': float(task.estimated_hours) if task.estimated_hours else None,
                    'time_spent': float(task.time_spent) if task.time_spent else 0,
                    'assignees': assignees,
                    'labels': task.labels or [],
                    'comments': comments,
                    'subtasks': subtasks,
                    'has_subtasks': len(subtasks) > 0,
                    'subtask_progress': task.get_progress_percentage() if task.subtasks.exists() else None,
                    'can_edit': task.can_edit(request.user),
                    'created_by': task.created_by.get_full_name() or task.created_by.username if task.created_by else None,
                    'created_at': task.created_at.isoformat(),
                    'updated_at': task.updated_at.isoformat(),
                },
            })

        except Task.DoesNotExist:
            return Response({
                'success': False,
                'message': _("Tâche non trouvée"),
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception("Error fetching task detail")
            return Response({
                'success': False,
                'message': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MobileTaskCreateView(APIView):
    """
    POST /api/v1/mobile/tasks/create/
    Create a new task on a board.
    Body: { board_id, column_id?, title, description?, priority?, due_date?, assignee_ids? }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            from apps.task_management.models import Board, Column, Task, TaskAssignment

            board_id = request.data.get('board_id')
            if not board_id:
                return Response({
                    'success': False,
                    'message': _("board_id requis"),
                }, status=status.HTTP_400_BAD_REQUEST)

            board = Board.objects.get(id=board_id)
            if not board.can_edit(request.user):
                return Response({
                    'success': False,
                    'message': _("Permission insuffisante"),
                }, status=status.HTTP_403_FORBIDDEN)

            title = request.data.get('title', '').strip()
            if not title:
                return Response({
                    'success': False,
                    'message': _("Le titre est requis"),
                }, status=status.HTTP_400_BAD_REQUEST)

            # Determine column
            column_id = request.data.get('column_id')
            if column_id:
                column = board.columns.get(id=column_id)
            else:
                column = board.columns.order_by('position').first()
                if not column:
                    return Response({
                        'success': False,
                        'message': _("Aucune colonne dans ce tableau"),
                    }, status=status.HTTP_400_BAD_REQUEST)

            # Parse due_date
            due_date = None
            due_date_str = request.data.get('due_date')
            if due_date_str:
                from django.utils.dateparse import parse_datetime
                due_date = parse_datetime(due_date_str)

            task = Task.objects.create(
                board=board,
                column=column,
                title=title,
                description=request.data.get('description', ''),
                priority=request.data.get('priority', 'medium'),
                due_date=due_date,
                created_by=request.user,
                status='todo',
            )

            # Handle assignees
            assignee_ids = request.data.get('assignee_ids', [])
            for uid in assignee_ids:
                try:
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    assignee = User.objects.get(id=uid)
                    TaskAssignment.objects.create(
                        task=task,
                        assignee=assignee,
                        assigned_by=request.user,
                    )
                except Exception:
                    pass

            return Response({
                'success': True,
                'task': {
                    'id': task.id,
                    'title': task.title,
                    'status': task.status,
                    'priority': task.priority,
                    'column_id': column.id,
                },
                'message': _("Tâche créée avec succès"),
            }, status=status.HTTP_201_CREATED)

        except Board.DoesNotExist:
            return Response({
                'success': False,
                'message': _("Tableau non trouvé"),
            }, status=status.HTTP_404_NOT_FOUND)
        except Column.DoesNotExist:
            return Response({
                'success': False,
                'message': _("Colonne non trouvée"),
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception("Error creating task")
            return Response({
                'success': False,
                'message': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MobileTaskUpdateView(APIView):
    """
    PATCH /api/v1/mobile/tasks/<task_id>/update/
    Update task fields (title, description, priority, status, due_date).
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, task_id):
        try:
            from apps.task_management.models import Task

            task = Task.objects.get(id=task_id)
            if not task.can_edit(request.user):
                return Response({
                    'success': False,
                    'message': _("Permission insuffisante"),
                }, status=status.HTTP_403_FORBIDDEN)

            allowed_fields = ['title', 'description', 'priority', 'status']
            for field in allowed_fields:
                value = request.data.get(field)
                if value is not None:
                    setattr(task, field, value)

            due_date_str = request.data.get('due_date')
            if due_date_str is not None:
                if due_date_str == '' or due_date_str is False:
                    task.due_date = None
                else:
                    from django.utils.dateparse import parse_datetime
                    task.due_date = parse_datetime(due_date_str)

            task.save()

            return Response({
                'success': True,
                'task': {
                    'id': task.id,
                    'title': task.title,
                    'status': task.status,
                    'priority': task.priority,
                },
                'message': _("Tâche mise à jour"),
            })

        except Task.DoesNotExist:
            return Response({
                'success': False,
                'message': _("Tâche non trouvée"),
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception("Error updating task")
            return Response({
                'success': False,
                'message': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MobileTaskMoveView(APIView):
    """
    POST /api/v1/mobile/tasks/<task_id>/move/
    Move task to a different column.
    Body: { column_id, position? }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, task_id):
        try:
            from apps.task_management.models import Task, Column
            from apps.task_management.utils import move_task

            task = Task.objects.get(id=task_id)
            if not task.board.can_edit(request.user):
                return Response({
                    'success': False,
                    'message': _("Permission insuffisante"),
                }, status=status.HTTP_403_FORBIDDEN)

            column_id = request.data.get('column_id')
            if not column_id:
                return Response({
                    'success': False,
                    'message': _("column_id requis"),
                }, status=status.HTTP_400_BAD_REQUEST)

            new_column = Column.objects.get(id=column_id, board=task.board)
            position = request.data.get('position', 0)

            move_task(task, new_column, position)

            # Update status if moved to done column
            if new_column.is_done_column and task.status != 'done':
                task.status = 'done'
                task.save()
            elif not new_column.is_done_column and task.status == 'done':
                task.status = 'in_progress'
                task.completed_at = None
                task.save()

            return Response({
                'success': True,
                'task': {
                    'id': task.id,
                    'column_id': new_column.id,
                    'column_name': new_column.name,
                    'status': task.status,
                },
            })

        except Task.DoesNotExist:
            return Response({
                'success': False,
                'message': _("Tâche non trouvée"),
            }, status=status.HTTP_404_NOT_FOUND)
        except Column.DoesNotExist:
            return Response({
                'success': False,
                'message': _("Colonne non trouvée"),
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception("Error moving task")
            return Response({
                'success': False,
                'message': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MobileTaskCommentView(APIView):
    """
    POST /api/v1/mobile/tasks/<task_id>/comment/
    Add a comment to a task.
    Body: { content }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, task_id):
        try:
            from apps.task_management.models import Task, TaskComment

            task = Task.objects.get(id=task_id)
            if not task.board.can_access(request.user):
                return Response({
                    'success': False,
                    'message': _("Accès refusé"),
                }, status=status.HTTP_403_FORBIDDEN)

            content = request.data.get('content', '').strip()
            if not content:
                return Response({
                    'success': False,
                    'message': _("Le contenu est requis"),
                }, status=status.HTTP_400_BAD_REQUEST)

            comment = TaskComment.objects.create(
                task=task,
                author=request.user,
                content=content,
            )

            return Response({
                'success': True,
                'comment': {
                    'id': comment.id,
                    'content': comment.content,
                    'author': request.user.get_full_name() or request.user.username,
                    'created_at': comment.created_at.isoformat(),
                },
                'message': _("Commentaire ajouté"),
            }, status=status.HTTP_201_CREATED)

        except Task.DoesNotExist:
            return Response({
                'success': False,
                'message': _("Tâche non trouvée"),
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception("Error adding comment")
            return Response({
                'success': False,
                'message': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MobileTaskAssigneesView(APIView):
    """
    GET  /api/v1/mobile/tasks/<task_id>/assignees/
    Returns current assignees and all available organization members.

    POST /api/v1/mobile/tasks/<task_id>/assignees/
    Updates assignees. Body: { assignee_ids: [user_id, ...] }
    Notifications are sent automatically via task_assignment_notify signal.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        try:
            from apps.task_management.models import Task
            from apps.organizations.models import OrganizationMember

            task = Task.objects.select_related('board__organization').get(id=task_id)
            if not task.board.can_access(request.user):
                return Response({
                    'success': False,
                    'message': _("Accès refusé"),
                }, status=status.HTTP_403_FORBIDDEN)

            # Helper: get photo URL for a user (via Practitioner)
            def _get_member_photo(user_id):
                try:
                    from apps.competitions.models import Practitioner as _P
                    p = _P.objects.filter(user_id=user_id).first()
                    if p and p.photo:
                        url = p.photo.url
                        if url and not url.startswith('http'):
                            url = request.build_absolute_uri(url)
                        return url
                except Exception:
                    pass
                return None

            # Current assignees
            current_assignees = [{
                'id': a.assignee.id,
                'name': a.assignee.get_full_name() or a.assignee.username,
                'role': a.role,
                'photo_url': _get_member_photo(a.assignee.id),
            } for a in task.assignments.filter(is_active=True).select_related('assignee')]

            current_ids = {a['id'] for a in current_assignees}

            # Available members from the organization (multiple sources)
            members_map = {}  # user_id -> {id, name, role, is_assigned, photo_url}
            org = task.board.organization

            if org:
                # Source 1: OrganizationMember
                org_members = OrganizationMember.objects.filter(
                    organization=org,
                    is_active=True,
                ).select_related('user').order_by('user__first_name', 'user__last_name')
                for m in org_members:
                    members_map[m.user.id] = {
                        'id': m.user.id,
                        'name': m.user.get_full_name() or m.user.username,
                        'role': m.get_role_display() if hasattr(m, 'get_role_display') else m.role,
                        'is_assigned': m.user.id in current_ids,
                        'photo_url': _get_member_photo(m.user.id),
                    }

                # Source 2: Practitioners with user accounts in same organization
                from apps.competitions.models import Practitioner
                practitioners = Practitioner.objects.filter(
                    organization=org,
                    user__isnull=False,
                    status='active',
                ).select_related('user')
                for p in practitioners:
                    if p.user_id not in members_map:
                        photo_url = None
                        if p.photo:
                            try:
                                photo_url = p.photo.url
                                if photo_url and not photo_url.startswith('http'):
                                    photo_url = request.build_absolute_uri(photo_url)
                            except Exception:
                                pass
                        members_map[p.user_id] = {
                            'id': p.user_id,
                            'name': p.user.get_full_name() or f"{p.first_name} {p.last_name}".strip() or p.user.username,
                            'role': _('Pratiquant'),
                            'is_assigned': p.user_id in current_ids,
                            'photo_url': photo_url,
                        }

                # Source 3: UserProfiles linked to same organization
                from apps.competitions.models import UserProfile
                profiles = UserProfile.objects.filter(
                    organization=org,
                ).select_related('user')
                for up in profiles:
                    if up.user_id not in members_map:
                        members_map[up.user_id] = {
                            'id': up.user_id,
                            'name': up.user.get_full_name() or up.user.username,
                            'role': up.get_role_display() if hasattr(up, 'get_role_display') else (up.role or ''),
                            'is_assigned': up.user_id in current_ids,
                            'photo_url': _get_member_photo(up.user_id),
                        }

            # Sort by name
            members = sorted(members_map.values(), key=lambda m: m['name'].lower())

            return Response({
                'success': True,
                'assignees': current_assignees,
                'members': members,
            })

        except Task.DoesNotExist:
            return Response({
                'success': False,
                'message': _("Tâche non trouvée"),
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception("Error fetching task assignees")
            return Response({
                'success': False,
                'message': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, task_id):
        try:
            from apps.task_management.models import Task, TaskAssignment
            from django.contrib.auth import get_user_model
            User = get_user_model()

            task = Task.objects.select_related('board').get(id=task_id)
            if not task.board.can_edit(request.user):
                return Response({
                    'success': False,
                    'message': _("Permission insuffisante"),
                }, status=status.HTTP_403_FORBIDDEN)

            assignee_ids = request.data.get('assignee_ids', [])
            assignee_ids_set = set(assignee_ids)

            # Get current active assignments
            current_assignments = task.assignments.filter(is_active=True)
            current_ids = set(current_assignments.values_list('assignee_id', flat=True))

            # Remove assignments no longer in the list
            to_remove = current_ids - assignee_ids_set
            if to_remove:
                task.assignments.filter(assignee_id__in=to_remove, is_active=True).update(is_active=False)

            # Add new assignments (signal will send notifications)
            to_add = assignee_ids_set - current_ids
            for uid in to_add:
                try:
                    assignee = User.objects.get(id=uid)
                    # Check if inactive assignment exists, reactivate it
                    existing = task.assignments.filter(assignee=assignee, is_active=False).first()
                    if existing:
                        existing.is_active = True
                        existing.assigned_by = request.user
                        existing.save()
                        # Manually trigger notification since save won't trigger post_save with created=True
                        from apps.task_management.signals import _create_task_notification, _get_task_url
                        if assignee != request.user:
                            assigner_name = request.user.get_full_name() or request.user.username
                            _create_task_notification(
                                user=assignee,
                                title=f"Nouvelle tâche assignée : {task.title}",
                                message=f"{assigner_name} vous a assigné la tâche « {task.title} » dans le tableau « {task.board.name} ».",
                                action_url=_get_task_url(task),
                                priority='important',
                            )
                    else:
                        # Creating new assignment triggers signal notification automatically
                        TaskAssignment.objects.create(
                            task=task,
                            assignee=assignee,
                            assigned_by=request.user,
                        )
                except User.DoesNotExist:
                    pass

            # Return updated assignees
            updated_assignees = [{
                'id': a.assignee.id,
                'name': a.assignee.get_full_name() or a.assignee.username,
                'role': a.role,
            } for a in task.assignments.filter(is_active=True).select_related('assignee')]

            return Response({
                'success': True,
                'assignees': updated_assignees,
                'message': _("Assignation mise à jour"),
            })

        except Task.DoesNotExist:
            return Response({
                'success': False,
                'message': _("Tâche non trouvée"),
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception("Error updating task assignees")
            return Response({
                'success': False,
                'message': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# PRACTITIONER TRANSFER API
# =============================================================================

class MobilePractitionerTransferRequestView(APIView):
    """
    POST /api/v1/mobile/practitioners/<id>/request-transfer/
    Créer une demande de transfert vers un autre club.
    Body: { target_organization_id: int, reason?: string }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, practitioner_id):
        try:
            from apps.competitions.models import Practitioner, PractitionerTransfer
            from apps.competitions.models.notifications import Notification
            from apps.organizations.models import Organization, OrganizationMember

            practitioner = get_object_or_404(Practitioner, id=practitioner_id)

            # Vérifier les droits : soit manager du club source, soit le pratiquant lui-même
            user = request.user
            is_own_practitioner = (practitioner.user == user)
            is_manager = False
            initiated_by = 'practitioner'

            if practitioner.organization:
                is_manager = OrganizationMember.objects.filter(
                    user=user,
                    organization=practitioner.organization,
                    role__in=['president', 'manager', 'admin'],
                    is_active=True,
                ).exists()

            if is_manager:
                initiated_by = 'manager'

            if not is_own_practitioner and not is_manager:
                return Response({
                    'success': False,
                    'message': _("Vous n'avez pas les droits pour transférer ce pratiquant"),
                }, status=status.HTTP_403_FORBIDDEN)

            target_org_id = request.data.get('target_organization_id')
            if not target_org_id:
                return Response({
                    'success': False,
                    'message': _("Club cible requis"),
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                target_org = Organization.objects.get(id=target_org_id)
            except Organization.DoesNotExist:
                return Response({
                    'success': False,
                    'message': _("Club cible introuvable"),
                }, status=status.HTTP_404_NOT_FOUND)

            if practitioner.organization and target_org.id == practitioner.organization.id:
                return Response({
                    'success': False,
                    'message': _("Le pratiquant est déjà dans ce club"),
                }, status=status.HTTP_400_BAD_REQUEST)

            # Vérifier qu'il n'y a pas déjà une demande en attente
            if PractitionerTransfer.objects.filter(
                practitioner=practitioner,
                status='pending',
            ).exists():
                return Response({
                    'success': False,
                    'message': _("Une demande de transfert est déjà en attente pour ce pratiquant"),
                }, status=status.HTTP_400_BAD_REQUEST)

            transfer = PractitionerTransfer.objects.create(
                practitioner=practitioner,
                source_organization=practitioner.organization,
                target_organization=target_org,
                initiated_by=initiated_by,
                requested_by=user,
                reason=request.data.get('reason', ''),
            )

            # Notifier les managers du club cible
            target_managers = OrganizationMember.objects.filter(
                organization=target_org,
                role__in=['president', 'manager', 'admin'],
                is_active=True,
            ).select_related('user')
            for member in target_managers:
                Notification.objects.create(
                    user=member.user,
                    title=_("Demande de transfert"),
                    message=f"{practitioner.full_name} souhaite rejoindre votre club.",
                    notification_type='info',
                    priority='important',
                )

            return Response({
                'success': True,
                'transfer_id': transfer.id,
                'message': _("Demande de transfert envoyée"),
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.exception("Error creating transfer request")
            return Response({
                'success': False,
                'message': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MobileTransferRequestsListView(APIView):
    """
    GET /api/v1/mobile/transfer-requests/
    Lister les demandes de transfert entrantes (pending) pour le club de l'utilisateur.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            from apps.competitions.models import PractitionerTransfer
            from apps.organizations.models import OrganizationMember

            user = request.user

            # Trouver les clubs où l'utilisateur est manager
            managed_orgs = OrganizationMember.objects.filter(
                user=user,
                role__in=['president', 'manager', 'admin'],
                is_active=True,
            ).values_list('organization_id', flat=True)

            if not managed_orgs:
                return Response({
                    'success': True,
                    'transfers': [],
                })

            transfers = PractitionerTransfer.objects.filter(
                target_organization_id__in=managed_orgs,
                status='pending',
            ).select_related(
                'practitioner', 'source_organization', 'target_organization', 'requested_by'
            ).order_by('-created_at')

            data = []
            for t in transfers:
                data.append({
                    'id': t.id,
                    'practitioner': {
                        'id': t.practitioner.id,
                        'full_name': t.practitioner.full_name,
                        'license_number': getattr(t.practitioner, 'license_number', None) or '',
                    },
                    'source_organization': {
                        'id': t.source_organization.id,
                        'name': t.source_organization.name,
                    } if t.source_organization else None,
                    'target_organization': {
                        'id': t.target_organization.id,
                        'name': t.target_organization.name,
                    },
                    'initiated_by': t.initiated_by,
                    'requested_by': t.requested_by.get_full_name() or t.requested_by.username if t.requested_by else '',
                    'reason': t.reason or '',
                    'created_at': t.created_at.isoformat(),
                })

            return Response({
                'success': True,
                'transfers': data,
            })

        except Exception as e:
            logger.exception("Error listing transfer requests")
            return Response({
                'success': False,
                'message': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MobileTransferRequestApproveView(APIView):
    """
    POST /api/v1/mobile/transfer-requests/<id>/approve/
    Approuver une demande de transfert.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, transfer_id):
        try:
            from apps.competitions.models import PractitionerTransfer
            from apps.competitions.models.notifications import Notification
            from apps.organizations.models import OrganizationMember

            transfer = get_object_or_404(PractitionerTransfer, id=transfer_id, status='pending')

            # Vérifier que l'utilisateur est manager du club cible
            is_manager = OrganizationMember.objects.filter(
                user=request.user,
                organization=transfer.target_organization,
                role__in=['president', 'manager', 'admin'],
                is_active=True,
            ).exists()

            if not is_manager:
                return Response({
                    'success': False,
                    'message': _("Vous n'avez pas les droits pour approuver ce transfert"),
                }, status=status.HTTP_403_FORBIDDEN)

            transfer.approve(request.user)

            # Notifier le demandeur
            if transfer.requested_by:
                Notification.objects.create(
                    user=transfer.requested_by,
                    title=_("Transfert approuvé"),
                    message=f"{transfer.practitioner.full_name} a été transféré vers {transfer.target_organization.name}.",
                    notification_type='success',
                    priority='important',
                )

            # Notifier le pratiquant si c'est différent du demandeur
            if transfer.practitioner.user and transfer.practitioner.user != transfer.requested_by:
                Notification.objects.create(
                    user=transfer.practitioner.user,
                    title=_("Transfert approuvé"),
                    message=f"Votre transfert vers {transfer.target_organization.name} a été approuvé.",
                    notification_type='success',
                    priority='important',
                )

            return Response({
                'success': True,
                'message': _("Transfert approuvé avec succès"),
            })

        except Exception as e:
            logger.exception("Error approving transfer")
            return Response({
                'success': False,
                'message': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MobileTransferRequestRejectView(APIView):
    """
    POST /api/v1/mobile/transfer-requests/<id>/reject/
    Rejeter une demande de transfert.
    Body optionnel: { message?: string }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, transfer_id):
        try:
            from apps.competitions.models import PractitionerTransfer
            from apps.competitions.models.notifications import Notification
            from apps.organizations.models import OrganizationMember

            transfer = get_object_or_404(PractitionerTransfer, id=transfer_id, status='pending')

            # Vérifier que l'utilisateur est manager du club cible
            is_manager = OrganizationMember.objects.filter(
                user=request.user,
                organization=transfer.target_organization,
                role__in=['president', 'manager', 'admin'],
                is_active=True,
            ).exists()

            if not is_manager:
                return Response({
                    'success': False,
                    'message': _("Vous n'avez pas les droits pour rejeter ce transfert"),
                }, status=status.HTTP_403_FORBIDDEN)

            response_msg = request.data.get('message', '')
            transfer.reject(request.user, response_msg)

            # Notifier le demandeur
            if transfer.requested_by:
                Notification.objects.create(
                    user=transfer.requested_by,
                    title=_("Transfert refusé"),
                    message=f"La demande de transfert de {transfer.practitioner.full_name} vers {transfer.target_organization.name} a été refusée.",
                    notification_type='warning',
                    priority='important',
                )

            return Response({
                'success': True,
                'message': _("Transfert refusé"),
            })

        except Exception as e:
            logger.exception("Error rejecting transfer")
            return Response({
                'success': False,
                'message': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
