from rest_framework import viewsets, filters, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, FileResponse
from django.contrib.contenttypes.models import ContentType
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from .models import (
    DocumentFolder, DocumentTag, Document, DocumentShare, DocumentAccessLog, 
    DocumentComment, TechnicalDocumentMetadata, GradeDocumentMetadata, 
    CompetitionDocumentMetadata
)
from .serializers import (
    DocumentFolderSerializer, DocumentTagSerializer, DocumentSerializer, 
    DocumentDetailSerializer, DocumentShareSerializer, DocumentAccessLogSerializer, 
    DocumentCommentSerializer, TechnicalDocumentMetadataSerializer,
    GradeDocumentMetadataSerializer, CompetitionDocumentMetadataSerializer
)
from .permissions import (
    IsOwnerOrReadOnly, HasDocumentPermission, HasFolderPermission, CanViewDocumentLogs
)


class DocumentFolderViewSet(viewsets.ModelViewSet):
    """API endpoint pour les dossiers de documents"""
    queryset = DocumentFolder.objects.all()
    serializer_class = DocumentFolderSerializer
    permission_classes = [permissions.IsAuthenticated, HasFolderPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_public', 'parent', 'visible_to_admins', 'visible_to_federations', 
                       'visible_to_clubs', 'visible_to_practitioners', 'visible_to_judges']
    search_fields = ['name', 'description', 'path']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        """Filtre les dossiers selon les permissions de l'utilisateur"""
        user = self.request.user
        
        # Les administrateurs voient tous les dossiers
        if user.is_superuser or user.is_staff:
            return DocumentFolder.objects.all()
        
        # Filtrer selon les rôles
        is_federation_admin = False
        is_club_admin = False
        is_practitioner = False
        is_judge = False
        
        try:
            # Vérifier si l'utilisateur est un administrateur de fédération
            from competitions.models import FederationRole
            fed_roles = FederationRole.objects.filter(user=user, role='admin')
            is_federation_admin = fed_roles.exists()
            
            # Vérifier si l'utilisateur est un administrateur de club
            from competitions.models import ClubRole
            club_roles = ClubRole.objects.filter(user=user, role='admin')
            is_club_admin = club_roles.exists()
            
            # Vérifier si l'utilisateur est un pratiquant
            from competitions.models import Practitioner
            is_practitioner = Practitioner.objects.filter(user=user).exists()
            
            # Vérifier si l'utilisateur est un juge/arbitre
            from competitions.models import Judge
            is_judge = Judge.objects.filter(user=user).exists()
        except:
            pass
        
        # Construire la requête selon les rôles de l'utilisateur
        queryset = DocumentFolder.objects.filter(
            # Dossiers dont l'utilisateur est propriétaire
            Q(owner=user) |
            # Dossiers publics
            Q(is_public=True)
        )
        
        if is_federation_admin:
            queryset = queryset | DocumentFolder.objects.filter(visible_to_federations=True)
        
        if is_club_admin:
            queryset = queryset | DocumentFolder.objects.filter(visible_to_clubs=True)
        
        if is_practitioner:
            queryset = queryset | DocumentFolder.objects.filter(visible_to_practitioners=True)
        
        if is_judge:
            queryset = queryset | DocumentFolder.objects.filter(visible_to_judges=True)
        
        return queryset.distinct()
    
    def perform_create(self, serializer):
        """Ajoute l'utilisateur actuel comme propriétaire lors de la création"""
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        """Récupère les documents contenus dans le dossier"""
        folder = self.get_object()
        documents = Document.objects.filter(folder=folder)
        page = self.paginate_queryset(documents)
        if page is not None:
            serializer = DocumentSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = DocumentSerializer(documents, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        """Récupère les sous-dossiers du dossier"""
        folder = self.get_object()
        children = DocumentFolder.objects.filter(parent=folder)
        page = self.paginate_queryset(children)
        if page is not None:
            serializer = DocumentFolderSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = DocumentFolderSerializer(children, many=True, context={'request': request})
        return Response(serializer.data)


class DocumentTagViewSet(viewsets.ModelViewSet):
    """API endpoint pour les tags de documents"""
    queryset = DocumentTag.objects.all()
    serializer_class = DocumentTagSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name']
    ordering = ['name']
    
    def get_queryset(self):
        """Filtre les tags selon le tenant multi-tenant si applicable"""
        user = self.request.user
        
        # Les administrateurs voient tous les tags
        if user.is_superuser or user.is_staff:
            return DocumentTag.objects.all()
        
        # Utiliser tous les tags disponibles pour les autres utilisateurs
        return DocumentTag.objects.all()
    
    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        """Récupère les documents associés au tag"""
        tag = self.get_object()
        documents = tag.documents.all()
        page = self.paginate_queryset(documents)
        if page is not None:
            serializer = DocumentSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = DocumentSerializer(documents, many=True, context={'request': request})
        return Response(serializer.data)


class DocumentViewSet(viewsets.ModelViewSet):
    """API endpoint pour les documents"""
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated, HasDocumentPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['folder', 'is_public', 'is_template', 'document_type']
    search_fields = ['title', 'description', 'metadata']
    ordering_fields = ['title', 'created_at', 'updated_at', 'view_count', 'download_count']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Utilise le serializer détaillé pour les actions retrieve et versions"""
        if self.action in ['retrieve', 'versions']:
            return DocumentDetailSerializer
        return DocumentSerializer
    
    def get_queryset(self):
        """Filtre les documents accessibles à l'utilisateur"""
        user = self.request.user
        
        # Les administrateurs voient tous les documents
        if user.is_superuser or user.is_staff:
            return Document.objects.all()
        
        # Documents créés par l'utilisateur
        queryset = Document.objects.filter(created_by=user)
        
        # Documents publics
        queryset = queryset | Document.objects.filter(is_public=True)
        
        # Documents partagés directement avec l'utilisateur
        user_shared = DocumentShare.objects.filter(user=user).values_list('document_id', flat=True)
        queryset = queryset | Document.objects.filter(id__in=user_shared)
        
        # Documents partagés avec des groupes dont l'utilisateur fait partie
        try:
            # Club
            from competitions.models import Club, ClubRole
            club_ids = []
            club_roles = ClubRole.objects.filter(user=user)
            for role in club_roles:
                club_ids.append(role.club.id)
            
            if club_ids:
                club_content_type = ContentType.objects.get_for_model(Club)
                club_shared = DocumentShare.objects.filter(
                    group_content_type=club_content_type,
                    group_object_id__in=club_ids
                ).values_list('document_id', flat=True)
                queryset = queryset | Document.objects.filter(id__in=club_shared)
            
            # Fédération
            from competitions.models import Federation, FederationRole
            federation_ids = []
            federation_roles = FederationRole.objects.filter(user=user)
            for role in federation_roles:
                federation_ids.append(role.federation.id)
            
            if federation_ids:
                federation_content_type = ContentType.objects.get_for_model(Federation)
                federation_shared = DocumentShare.objects.filter(
                    group_content_type=federation_content_type,
                    group_object_id__in=federation_ids
                ).values_list('document_id', flat=True)
                queryset = queryset | Document.objects.filter(id__in=federation_shared)
            
            # Groupes Django
            from django.contrib.auth.models import Group
            group_ids = user.groups.values_list('id', flat=True)
            
            if group_ids:
                group_content_type = ContentType.objects.get_for_model(Group)
                group_shared = DocumentShare.objects.filter(
                    group_content_type=group_content_type,
                    group_object_id__in=group_ids
                ).values_list('document_id', flat=True)
                queryset = queryset | Document.objects.filter(id__in=group_shared)
        except:
            pass
        
        return queryset.distinct()
    
    def perform_create(self, serializer):
        """Ajoute l'utilisateur actuel comme créateur lors de la création"""
        serializer.save(created_by=self.request.user, modified_by=self.request.user)
    
    def perform_update(self, serializer):
        """Met à jour l'utilisateur qui a modifié le document"""
        serializer.save(modified_by=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        """Incrémente le compteur de vues lors de la consultation d'un document"""
        instance = self.get_object()
        # Incrémenter le compteur de vues
        instance.view_count += 1
        instance.save(update_fields=['view_count'])
        
        # Enregistrer l'accès dans le journal
        DocumentAccessLog.objects.create(
            document=instance,
            user=request.user,
            action=DocumentAccessLog.ACTION_VIEW,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return super().retrieve(request, *args, **kwargs)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Télécharge le fichier du document"""
        document = self.get_object()
        
        # Incrémenter le compteur de téléchargements
        document.download_count += 1
        document.save(update_fields=['download_count'])
        
        # Enregistrer l'accès dans le journal
        DocumentAccessLog.objects.create(
            document=document,
            user=request.user,
            action=DocumentAccessLog.ACTION_DOWNLOAD,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Vérifier si le fichier existe
        if not document.file:
            return Response(
                {"detail": _("Aucun fichier disponible pour ce document.")},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Renvoyer le fichier en tant que réponse de téléchargement
        response = FileResponse(document.file.open())
        response['Content-Disposition'] = f'attachment; filename="{document.file.name.split("/")[-1]}"'
        return response
    
    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        """Récupère toutes les versions d'un document"""
        document = self.get_object()
        
        # Trouver la version racine
        root = document
        while root.parent:
            root = root.parent
        
        # Récupérer toutes les versions (racine + descendants)
        versions = Document.objects.filter(
            Q(id=root.id) | Q(parent=root) | 
            Q(parent__parent=root) | Q(parent__parent__parent=root)
        ).order_by('version')
        
        serializer = DocumentSerializer(versions, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def shares(self, request, pk=None):
        """Récupère les partages d'un document"""
        document = self.get_object()
        
        # Vérifier si l'utilisateur a les permissions pour voir les partages
        if request.user != document.created_by and not request.user.is_superuser:
            return Response(
                {"detail": _("Vous n'avez pas la permission de voir les partages de ce document.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        shares = document.shares.all()
        serializer = DocumentShareSerializer(shares, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        """Récupère les commentaires d'un document"""
        document = self.get_object()
        comments = document.comments.filter(parent=None)  # Uniquement les commentaires de premier niveau
        serializer = DocumentCommentSerializer(comments, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        """Ajoute un commentaire à un document"""
        document = self.get_object()
        
        # Récupérer le commentaire parent si fourni
        parent_id = request.data.get('parent')
        parent = None
        if parent_id:
            parent = get_object_or_404(DocumentComment, id=parent_id, document=document)
        
        # Créer le commentaire
        comment = DocumentComment.objects.create(
            document=document,
            author=request.user,
            content=request.data.get('content', ''),
            parent=parent
        )
        
        serializer = DocumentCommentSerializer(comment, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """Partage un document avec un utilisateur ou un groupe"""
        document = self.get_object()
        
        # Vérifier si l'utilisateur a les permissions pour partager
        if request.user != document.created_by and not request.user.is_superuser:
            return Response(
                {"detail": _("Vous n'avez pas la permission de partager ce document.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Valider et traiter les données de partage
        serializer = DocumentShareSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        # Déterminer le type de partage
        share_type = request.data.get('share_type')
        entity_id = request.data.get('entity_id')
        
        if not share_type or not entity_id:
            return Response(
                {"detail": _("Type de partage et ID de l'entité sont requis.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Créer le partage selon le type
        try:
            if share_type == 'user':
                from django.contrib.auth import get_user_model
                User = get_user_model()
                entity = User.objects.get(pk=entity_id)
                share = DocumentShare.objects.create(
                    document=document,
                    user=entity,
                    access_level=request.data.get('access_level', 'R'),
                    expires_at=request.data.get('expires_at'),
                    notify_on_access=request.data.get('notify_on_access', False),
                    created_by=request.user
                )
            else:
                # Partage avec un groupe (club, fédération, etc.)
                if share_type == 'club':
                    from competitions.models import Club
                    entity = Club.objects.get(pk=entity_id)
                    content_type = ContentType.objects.get_for_model(Club)
                elif share_type == 'federation':
                    from competitions.models import Federation
                    entity = Federation.objects.get(pk=entity_id)
                    content_type = ContentType.objects.get_for_model(Federation)
                elif share_type == 'group':
                    from django.contrib.auth.models import Group
                    entity = Group.objects.get(pk=entity_id)
                    content_type = ContentType.objects.get_for_model(Group)
                else:
                    return Response(
                        {"detail": _("Type de partage non pris en charge.")},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                share = DocumentShare.objects.create(
                    document=document,
                    group_content_type=content_type,
                    group_object_id=entity.pk,
                    access_level=request.data.get('access_level', 'R'),
                    expires_at=request.data.get('expires_at'),
                    notify_on_access=request.data.get('notify_on_access', False),
                    created_by=request.user
                )
            
            serializer = DocumentShareSerializer(share, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def access_logs(self, request, pk=None):
        """Récupère les journaux d'accès d'un document"""
        document = self.get_object()
        
        # Vérifier si l'utilisateur a les permissions pour voir les logs
        if request.user != document.created_by and not request.user.is_superuser:
            return Response(
                {"detail": _("Vous n'avez pas la permission de voir les journaux d'accès de ce document.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        logs = document.access_logs.all().order_by('-timestamp')
        page = self.paginate_queryset(logs)
        if page is not None:
            serializer = DocumentAccessLogSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = DocumentAccessLogSerializer(logs, many=True, context={'request': request})
        return Response(serializer.data)


class DocumentShareViewSet(viewsets.ModelViewSet):
    """API endpoint pour les partages de documents"""
    queryset = DocumentShare.objects.all()
    serializer_class = DocumentShareSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['document', 'user', 'access_level']
    ordering_fields = ['created_at', 'expires_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filtre les partages accessibles à l'utilisateur"""
        user = self.request.user
        
        # Les administrateurs voient tous les partages
        if user.is_superuser or user.is_staff:
            return DocumentShare.objects.all()
        
        # Partages créés par l'utilisateur ou partages où l'utilisateur est le destinataire
        return DocumentShare.objects.filter(
            Q(created_by=user) | Q(user=user)
        )
    
    def perform_create(self, serializer):
        """Ajoute l'utilisateur actuel comme créateur lors de la création"""
        serializer.save(created_by=self.request.user)


class DocumentCommentViewSet(viewsets.ModelViewSet):
    """API endpoint pour les commentaires sur les documents"""
    queryset = DocumentComment.objects.all()
    serializer_class = DocumentCommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['document', 'author', 'parent']
    ordering_fields = ['created_at']
    ordering = ['created_at']
    
    def get_queryset(self):
        """Filtre les commentaires selon les documents accessibles à l'utilisateur"""
        user = self.request.user
        
        # Les administrateurs voient tous les commentaires
        if user.is_superuser or user.is_staff:
            return DocumentComment.objects.all()
        
        # Commentaires sur les documents accessibles à l'utilisateur
        # (ceci dépend de la logique d'accès aux documents)
        document_ids = Document.objects.filter(
            Q(created_by=user) | Q(is_public=True) | 
            Q(shares__user=user)
        ).values_list('id', flat=True).distinct()
        
        return DocumentComment.objects.filter(
            Q(document_id__in=document_ids) | Q(author=user)
        )
    
    def perform_create(self, serializer):
        """Ajoute l'utilisateur actuel comme auteur lors de la création"""
        serializer.save(author=self.request.user)


class DocumentAccessLogViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint pour les journaux d'accès aux documents (lecture seule)"""
    queryset = DocumentAccessLog.objects.all()
    serializer_class = DocumentAccessLogSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewDocumentLogs]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['document', 'user', 'action']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        """Filtre les logs selon les permissions de l'utilisateur"""
        user = self.request.user
        
        # Les administrateurs voient tous les logs
        if user.is_superuser or user.is_staff:
            return DocumentAccessLog.objects.all()
        
        # Logs des documents créés par l'utilisateur
        document_ids = Document.objects.filter(created_by=user).values_list('id', flat=True)
        return DocumentAccessLog.objects.filter(document_id__in=document_ids)