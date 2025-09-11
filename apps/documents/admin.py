from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import (
    DocumentFolder, DocumentTag, Document, DocumentShare, DocumentAccessLog, 
    DocumentComment, TechnicalDocumentMetadata, GradeDocumentMetadata, 
    CompetitionDocumentMetadata
)


class DocumentFolderAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'path', 'owner', 'created_at', 'is_public')
    list_filter = ('is_public', 'visible_to_admins', 'visible_to_federations', 
                  'visible_to_clubs', 'visible_to_practitioners', 'visible_to_judges')
    search_fields = ('name', 'description', 'path')
    readonly_fields = ('path', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'parent', 'path', 'owner', 'is_public')
        }),
        (_('Visibilité par rÃ´le'), {
            'fields': ('visible_to_admins', 'visible_to_federations', 'visible_to_clubs', 
                      'visible_to_practitioners', 'visible_to_judges')
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at')
        }),
    )


class DocumentTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color_display', 'document_count')
    search_fields = ('name',)
    
    def color_display(self, obj):
        return format_html(
            '<span style="background-color: {}; width: 30px; height: 15px; display: inline-block; border: 1px solid #ccc;"></span> {}',
            obj.color, obj.color
        )
    color_display.short_description = _('Couleur')
    
    def document_count(self, obj):
        return obj.documents.count()
    document_count.short_description = _('Nombre de documents')


class DocumentCommentInline(admin.TabularInline):
    model = DocumentComment
    extra = 0
    readonly_fields = ('author', 'created_at', 'updated_at')
    fields = ('author', 'content', 'created_at')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


class DocumentShareInline(admin.TabularInline):
    model = DocumentShare
    extra = 1
    fields = ('user', 'group_content_type', 'group_object_id', 'access_level', 
             'expires_at', 'notify_on_access')


class TechnicalDocumentMetadataInline(admin.StackedInline):
    model = TechnicalDocumentMetadata
    can_delete = False
    fields = ('discipline', 'level', 'content_type', 'requirements', 'keywords')


class GradeDocumentMetadataInline(admin.StackedInline):
    model = GradeDocumentMetadata
    can_delete = False
    fields = ('grade', 'document_type', 'valid_from', 'valid_until', 
             'issuing_authority', 'authorized_by')


class CompetitionDocumentMetadataInline(admin.StackedInline):
    model = CompetitionDocumentMetadata
    can_delete = False
    fields = ('competition', 'document_type', 'category', 'event_date')


class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'document_type', 'folder', 'version', 'created_by', 
                   'created_at', 'file_size_display', 'is_public', 'view_count')
    list_filter = ('document_type', 'is_public', 'is_template', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('file_size', 'mime_type', 'created_at', 'updated_at', 
                      'view_count', 'download_count', 'created_by', 'modified_by',
                      'file_preview')
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'file', 'file_preview')
        }),
        (_('Organisation'), {
            'fields': ('folder', 'tags', 'document_type')
        }),
        (_('ContrÃ´le d\'accès'), {
            'fields': ('is_public', 'is_template', 'expiry_date')
        }),
        (_('Versionnement'), {
            'fields': ('parent', 'version', 'is_latest_version')
        }),
        (_('Métadonnées'), {
            'fields': ('file_size', 'mime_type', 'metadata', 'content_type', 'object_id'),
            'classes': ('collapse',)
        }),
        (_('Statistiques et suivi'), {
            'fields': ('view_count', 'download_count', 'created_at', 'updated_at', 
                      'created_by', 'modified_by'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [
        TechnicalDocumentMetadataInline,
        GradeDocumentMetadataInline,
        CompetitionDocumentMetadataInline,
        DocumentShareInline,
        DocumentCommentInline,
    ]
    
    def file_size_display(self, obj):
        """Affiche la taille du fichier de manière lisible"""
        if obj.file_size < 1024:
            return f"{obj.file_size} octets"
        elif obj.file_size < 1024 * 1024:
            return f"{obj.file_size / 1024:.1f} Ko"
        else:
            return f"{obj.file_size / (1024 * 1024):.1f} Mo"
    file_size_display.short_description = _('Taille')
    
    def file_preview(self, obj):
        """Affiche une prévisualisation du fichier selon son type"""
        if not obj.file:
            return _("Aucun fichier")
        
        # Prévisualisation pour les images
        if obj.mime_type.startswith('image/'):
            return format_html('<img src="{}" style="max-width: 300px; max-height: 200px;" />', obj.file.url)
        
        # Prévisualisation pour les PDF (en utilisant l'objet embed)
        if obj.mime_type == 'application/pdf':
            return format_html('<a href="{0}" target="_blank">{1}</a><br/><embed src="{0}" width="500" height="375">', 
                              obj.file.url, _("Voir le PDF"))
        
        # Lien pour les autres types de fichiers
        return format_html('<a href="{0}" target="_blank">{1}</a>', obj.file.url, _("Télécharger le fichier"))
    file_preview.short_description = _('Prévisualisation')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si c'est un nouveau document
            obj.created_by = request.user
        
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)


class DocumentAccessLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'document', 'ip_address')
    list_filter = ('action', 'timestamp')
    search_fields = ('user__username', 'user__email', 'document__title', 'ip_address')
    readonly_fields = ('document', 'user', 'action', 'timestamp', 'ip_address', 
                      'user_agent', 'details')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


class DocumentCommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'document', 'created_at', 'content_preview')
    list_filter = ('created_at',)
    search_fields = ('author__username', 'author__email', 'document__title', 'content')
    readonly_fields = ('created_at', 'updated_at')
    
    def content_preview(self, obj):
        if len(obj.content) > 50:
            return obj.content[:50] + '...'
        return obj.content
    content_preview.short_description = _('Contenu')


# Enregistrement des modèles dans l'interface d'administration
admin.site.register(DocumentFolder, DocumentFolderAdmin)
admin.site.register(DocumentTag, DocumentTagAdmin)
admin.site.register(Document, DocumentAdmin)
admin.site.register(DocumentShare)
admin.site.register(DocumentAccessLog, DocumentAccessLogAdmin)
admin.site.register(DocumentComment, DocumentCommentAdmin)
