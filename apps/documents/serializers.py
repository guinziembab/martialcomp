from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist

from .models import (
    DocumentFolder, DocumentTag, Document, DocumentShare, DocumentAccessLog, 
    DocumentComment, TechnicalDocumentMetadata, GradeDocumentMetadata, 
    CompetitionDocumentMetadata
)

User = get_user_model()


class DocumentTagSerializer(serializers.ModelSerializer):
    """Serializer pour les tags de documents"""
    document_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentTag
        fields = ['id', 'name', 'color', 'document_count']
        read_only_fields = ['id', 'document_count']
    
    def get_document_count(self, obj):
        return obj.documents.count()


class DocumentFolderSerializer(serializers.ModelSerializer):
    """Serializer pour les dossiers de documents"""
    children_count = serializers.SerializerMethodField()
    documents_count = serializers.SerializerMethodField()
    parent_name = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentFolder
        fields = [
            'id', 'name', 'description', 'parent', 'parent_name', 'path', 
            'owner', 'owner_name', 'is_public', 'created_at', 'updated_at',
            'visible_to_admins', 'visible_to_federations', 'visible_to_clubs', 
            'visible_to_practitioners', 'visible_to_judges',
            'children_count', 'documents_count'
        ]
        read_only_fields = ['id', 'path', 'created_at', 'updated_at', 
                           'children_count', 'documents_count', 'parent_name', 'owner_name']
    
    def get_children_count(self, obj):
        return obj.children.count()
    
    def get_documents_count(self, obj):
        return obj.documents.count()
    
    def get_parent_name(self, obj):
        return obj.parent.name if obj.parent else None
    
    def get_owner_name(self, obj):
        return obj.owner.get_full_name() or obj.owner.username if obj.owner else None


class DocumentCommentSerializer(serializers.ModelSerializer):
    """Serializer pour les commentaires de documents"""
    author_name = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentComment
        fields = [
            'id', 'document', 'author', 'author_name', 'content', 
            'created_at', 'updated_at', 'parent', 'replies'
        ]
        read_only_fields = ['id', 'document', 'author', 'author_name', 
                           'created_at', 'updated_at', 'replies']
    
    def get_author_name(self, obj):
        return obj.author.get_full_name() or obj.author.username if obj.author else None
    
    def get_replies(self, obj):
        # Récupérer uniquement les réponses directes
        replies = obj.replies.all()
        if replies:
            return DocumentCommentSerializer(replies, many=True, context=self.context).data
        return []


class DocumentShareSerializer(serializers.ModelSerializer):
    """Serializer pour les partages de documents"""
    created_by_name = serializers.SerializerMethodField()
    shared_with_name = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentShare
        fields = [
            'id', 'document', 'user', 'group_content_type', 'group_object_id',
            'access_level', 'created_at', 'expires_at', 'created_by', 
            'created_by_name', 'notify_on_access', 'shared_with_name'
        ]
        read_only_fields = ['id', 'created_at', 'created_by', 
                           'created_by_name', 'shared_with_name']
    
    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() or obj.created_by.username if obj.created_by else None
    
    def get_shared_with_name(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        elif obj.group_object:
            try:
                return str(obj.group_object)
            except:
                return f"{obj.group_content_type} #{obj.group_object_id}"
        return None


class TechnicalDocumentMetadataSerializer(serializers.ModelSerializer):
    """Serializer pour les métadonnées techniques"""
    discipline_name = serializers.SerializerMethodField()
    level_display = serializers.SerializerMethodField()
    content_type_display = serializers.SerializerMethodField()
    
    class Meta:
        model = TechnicalDocumentMetadata
        fields = [
            'id', 'document', 'discipline', 'discipline_name', 'level', 
            'level_display', 'content_type', 'content_type_display',
            'requirements', 'keywords'
        ]
        read_only_fields = ['id', 'document', 'discipline_name', 
                           'level_display', 'content_type_display']
    
    def get_discipline_name(self, obj):
        return obj.discipline.name if obj.discipline else None
    
    def get_level_display(self, obj):
        return obj.get_level_display() if obj.level else None
    
    def get_content_type_display(self, obj):
        return obj.get_content_type_display() if obj.content_type else None


class GradeDocumentMetadataSerializer(serializers.ModelSerializer):
    """Serializer pour les métadonnées de grade"""
    grade_name = serializers.SerializerMethodField()
    document_type_display = serializers.SerializerMethodField()
    
    class Meta:
        model = GradeDocumentMetadata
        fields = [
            'id', 'document', 'grade', 'grade_name', 'document_type', 
            'document_type_display', 'valid_from', 'valid_until',
            'issuing_authority', 'authorized_by'
        ]
        read_only_fields = ['id', 'document', 'grade_name', 'document_type_display']
    
    def get_grade_name(self, obj):
        return str(obj.grade) if obj.grade else None
    
    def get_document_type_display(self, obj):
        return obj.get_document_type_display() if obj.document_type else None


class CompetitionDocumentMetadataSerializer(serializers.ModelSerializer):
    """Serializer pour les métadonnées de compétition"""
    competition_name = serializers.SerializerMethodField()
    document_type_display = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CompetitionDocumentMetadata
        fields = [
            'id', 'document', 'competition', 'competition_name', 
            'document_type', 'document_type_display', 'category',
            'category_name', 'event_date'
        ]
        read_only_fields = ['id', 'document', 'competition_name', 
                           'document_type_display', 'category_name']
    
    def get_competition_name(self, obj):
        return obj.competition.name if obj.competition else None
    
    def get_document_type_display(self, obj):
        return obj.get_document_type_display() if obj.document_type else None
    
    def get_category_name(self, obj):
        return obj.category.name if obj.category else None


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer pour les documents"""
    created_by_name = serializers.SerializerMethodField()
    modified_by_name = serializers.SerializerMethodField()
    folder_name = serializers.SerializerMethodField()
    document_type_display = serializers.SerializerMethodField()
    file_size_display = serializers.SerializerMethodField()
    tags = DocumentTagSerializer(many=True, read_only=True)
    comments_count = serializers.SerializerMethodField()
    shares_count = serializers.SerializerMethodField()
    version_count = serializers.SerializerMethodField()
    has_technical_metadata = serializers.SerializerMethodField()
    has_grade_metadata = serializers.SerializerMethodField()
    has_competition_metadata = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 'title', 'description', 'file', 'file_size', 'file_size_display',
            'mime_type', 'created_at', 'updated_at', 'created_by', 'created_by_name',
            'modified_by', 'modified_by_name', 'folder', 'folder_name', 'tags',
            'parent', 'version', 'is_latest_version', 'is_public', 'is_template',
            'expiry_date', 'content_type', 'object_id', 'document_type',
            'document_type_display', 'view_count', 'download_count',
            'comments_count', 'shares_count', 'version_count',
            'has_technical_metadata', 'has_grade_metadata', 'has_competition_metadata'
        ]
        read_only_fields = [
            'id', 'file_size', 'file_size_display', 'mime_type', 'created_at', 
            'updated_at', 'created_by', 'created_by_name', 'modified_by', 
            'modified_by_name', 'version', 'is_latest_version', 'view_count', 
            'download_count', 'folder_name', 'document_type_display',
            'comments_count', 'shares_count', 'version_count',
            'has_technical_metadata', 'has_grade_metadata', 'has_competition_metadata'
        ]
    
    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() or obj.created_by.username if obj.created_by else None
    
    def get_modified_by_name(self, obj):
        return obj.modified_by.get_full_name() or obj.modified_by.username if obj.modified_by else None
    
    def get_folder_name(self, obj):
        return obj.folder.name if obj.folder else None
    
    def get_document_type_display(self, obj):
        return obj.get_document_type_display() if obj.document_type else None
    
    def get_file_size_display(self, obj):
        if obj.file_size < 1024:
            return f"{obj.file_size} octets"
        elif obj.file_size < 1024 * 1024:
            return f"{obj.file_size / 1024:.1f} Ko"
        else:
            return f"{obj.file_size / (1024 * 1024):.1f} Mo"
    
    def get_comments_count(self, obj):
        return obj.comments.count()
    
    def get_shares_count(self, obj):
        return obj.shares.count()
    
    def get_version_count(self, obj):
        # Compter toutes les versions du document
        if obj.parent:
            # Chercher le document racine
            root = obj.parent
            while root.parent:
                root = root.parent
            return Document.objects.filter(
                models.Q(id=root.id) | models.Q(parent=root) | 
                models.Q(parent__parent=root) | models.Q(parent__parent__parent=root)
            ).count()
        else:
            # Ce document est la racine ou n'a pas de versions
            return 1 + obj.versions.count()
    
    def get_has_technical_metadata(self, obj):
        try:
            return hasattr(obj, 'technical_metadata') and obj.technical_metadata is not None
        except:
            return False
    
    def get_has_grade_metadata(self, obj):
        try:
            return hasattr(obj, 'grade_metadata') and obj.grade_metadata is not None
        except:
            return False
    
    def get_has_competition_metadata(self, obj):
        try:
            return hasattr(obj, 'competition_metadata') and obj.competition_metadata is not None
        except:
            return False


class DocumentDetailSerializer(DocumentSerializer):
    """Serializer détaillé pour les documents avec toutes les informations associées"""
    technical_metadata = serializers.SerializerMethodField()
    grade_metadata = serializers.SerializerMethodField()
    competition_metadata = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    shares = serializers.SerializerMethodField()
    
    class Meta(DocumentSerializer.Meta):
        fields = DocumentSerializer.Meta.fields + [
            'technical_metadata', 'grade_metadata', 
            'competition_metadata', 'comments', 'shares'
        ]
    
    def get_technical_metadata(self, obj):
        try:
            metadata = obj.technical_metadata
            return TechnicalDocumentMetadataSerializer(metadata, context=self.context).data
        except:
            return None
    
    def get_grade_metadata(self, obj):
        try:
            metadata = obj.grade_metadata
            return GradeDocumentMetadataSerializer(metadata, context=self.context).data
        except:
            return None
    
    def get_competition_metadata(self, obj):
        try:
            metadata = obj.competition_metadata
            return CompetitionDocumentMetadataSerializer(metadata, context=self.context).data
        except:
            return None
    
    def get_comments(self, obj):
        # Récupérer uniquement les commentaires de premier niveau
        comments = obj.comments.filter(parent=None)
        return DocumentCommentSerializer(comments, many=True, context=self.context).data
    
    def get_shares(self, obj):
        # Vérifier si l'utilisateur a les permissions pour voir les partages
        user = self.context.get('request').user if self.context.get('request') else None
        if user and (user.is_superuser or user == obj.created_by):
            return DocumentShareSerializer(obj.shares.all(), many=True, context=self.context).data
        return []


class DocumentAccessLogSerializer(serializers.ModelSerializer):
    """Serializer pour les journaux d'accès aux documents"""
    user_name = serializers.SerializerMethodField()
    document_title = serializers.SerializerMethodField()
    action_display = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentAccessLog
        fields = [
            'id', 'document', 'document_title', 'user', 'user_name', 
            'timestamp', 'action', 'action_display', 'ip_address', 
            'user_agent', 'details'
        ]
        read_only_fields = ['id', 'document', 'document_title', 'user', 
                           'user_name', 'timestamp', 'action_display']
    
    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username if obj.user else None
    
    def get_document_title(self, obj):
        return obj.document.title if obj.document else None
    
    def get_action_display(self, obj):
        return obj.get_action_display() if obj.action else None
