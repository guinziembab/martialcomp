from django.contrib import admin
from apps.competitions.models. import OrganizationTemplate

@admin.register(OrganizationTemplate)
class OrganizationTemplateAdmin(admin.ModelAdmin):
    list_display = ['organization', 'theme', 'created_at', 'updated_at']
    list_filter = ['theme', 'show_social_links', 'show_videos', 'show_gallery']
    search_fields = ['organization__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Organisation', {
            'fields': ('organization',)
        }),
        ('Thème et couleurs', {
            'fields': ('theme', 'primary_color', 'secondary_color', 'accent_color', 'background_color')
        }),
        ('Contenu principal', {
            'fields': ('hero_title', 'hero_subtitle', 'about_title', 'about_content')
        }),
        ('Liens sociaux', {
            'fields': ('website_url', 'facebook_url', 'instagram_url', 'youtube_url')
        }),
        ('Vidéos', {
            'fields': (
                'video_1_url', 'video_1_title',
                'video_2_url', 'video_2_title',
                'video_3_url', 'video_3_title'
            )
        }),
        ('Images', {
            'fields': (
                'image_1_url', 'image_1_alt',
                'image_2_url', 'image_2_alt',
                'image_3_url', 'image_3_alt',
                'image_4_url', 'image_4_alt',
                'image_5_url', 'image_5_alt'
            )
        }),
        ('Options d\'affichage', {
            'fields': ('show_social_links', 'show_videos', 'show_gallery')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization') 

