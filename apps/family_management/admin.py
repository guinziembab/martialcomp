from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import Family, FamilyMember, FamilyRole, FamilyPaymentGroup, FamilyEvent


@admin.register(FamilyRole)
class FamilyRoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'can_manage_family', 'can_view_all_data', 'can_register_members']
    list_filter = ['can_manage_family', 'can_view_all_data', 'can_register_members']
    search_fields = ['name']


class FamilyMemberInline(admin.TabularInline):
    model = FamilyMember
    extra = 1
    fields = ['practitioner', 'user', 'role', 'can_manage_others', 'can_make_payments', 'is_active']
    readonly_fields = ['joined_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('practitioner', 'user')


class FamilyPaymentGroupInline(admin.TabularInline):
    model = FamilyPaymentGroup
    extra = 0
    fields = ['description', 'total_amount', 'is_paid', 'created_at']
    readonly_fields = ['created_at', 'group_id']


@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = [
        'family_name', 
        'primary_responsible_name',
        'members_count', 
        'total_practitioners',
        'organization',
        'is_active',
        'created_at'
    ]
    list_filter = [
        'is_active', 
        'shared_calendar', 
        'shared_notifications',
        'organization',
        'created_at'
    ]
    search_fields = [
        'family_name', 
        'primary_responsible__first_name',
        'primary_responsible__last_name',
        'billing_email'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        (_('Informations principales'), {
            'fields': ('id', 'family_name', 'primary_responsible', 'organization')
        }),
        (_('Informations de contact'), {
            'fields': ('billing_address', 'billing_phone', 'billing_email')
        }),
        (_('Paramètres de gestion'), {
            'fields': ('shared_calendar', 'shared_notifications', 'is_active')
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [FamilyMemberInline, FamilyPaymentGroupInline]
    
    def primary_responsible_name(self, obj):
        """Affiche le nom du responsable principal"""
        if obj.primary_responsible:
            return f"{obj.primary_responsible.get_full_name()}"
        return "-"
    primary_responsible_name.short_description = _("Responsable principal")
    
    def members_count(self, obj):
        """Affiche le nombre total de membres"""
        count = obj.members.filter(is_active=True).count()
        return format_html(
            '<span style="color: {};">{}</span>',
            'green' if count > 0 else 'red',
            count
        )
    members_count.short_description = _("Membres")
    
    def total_practitioners(self, obj):
        """Affiche le nombre de pratiquants actifs"""
        practitioners = [m for m in obj.get_practitioners()]
        count = len(practitioners)
        return format_html(
            '<span style="color: {};">{}</span>',
            'green' if count > 0 else 'orange',
            count
        )
    total_practitioners.short_description = _("Pratiquants")
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'primary_responsible', 'organization'
        ).prefetch_related('members')


@admin.register(FamilyMember)
class FamilyMemberAdmin(admin.ModelAdmin):
    list_display = [
        'display_name',
        'family_name',
        'role',
        'practitioner_status',
        'permissions_summary',
        'is_active',
        'joined_at'
    ]
    list_filter = [
        'role',
        'is_active',
        'can_manage_others',
        'can_make_payments',
        'share_calendar',
        'receive_family_notifications'
    ]
    search_fields = [
        'family__family_name',
        'practitioner__first_name',
        'practitioner__last_name',
        'user__first_name',
        'user__last_name'
    ]
    readonly_fields = ['joined_at']
    
    fieldsets = (
        (_('Informations principales'), {
            'fields': ('family', 'practitioner', 'user', 'role')
        }),
        (_('Permissions'), {
            'fields': ('can_manage_others', 'can_make_payments')
        }),
        (_('Paramètres de partage'), {
            'fields': ('share_calendar', 'receive_family_notifications')
        }),
        (_('Statut'), {
            'fields': ('is_active', 'joined_at')
        })
    )
    
    def display_name(self, obj):
        """Affiche le nom du membre"""
        name = obj.get_display_name()
        if obj.practitioner and obj.practitioner.status != 'active':
            return format_html('<span style="color: orange;">{}</span>', name)
        return name
    display_name.short_description = _("Nom")
    
    def family_name(self, obj):
        """Affiche le nom de la famille avec lien"""
        url = reverse('admin:family_management_family_change', args=[obj.family.pk])
        return format_html('<a href="{}">{}</a>', url, obj.family.family_name)
    family_name.short_description = _("Famille")
    
    def practitioner_status(self, obj):
        """Affiche le statut du pratiquant"""
        if obj.practitioner:
            status = obj.practitioner.status
            color = {
                'active': 'green',
                'inactive': 'orange', 
                'suspended': 'red',
                'archived': 'gray'
            }.get(status, 'black')
            return format_html(
                '<span style="color: {};">{}</span>', 
                color, 
                obj.practitioner.get_status_display()
            )
        return format_html('<span style="color: gray;">Non pratiquant</span>')
    practitioner_status.short_description = _("Statut pratiquant")
    
    def permissions_summary(self, obj):
        """Résumé des permissions"""
        permissions = []
        if obj.has_permission('manage_family'):
            permissions.append("Gestion")
        if obj.has_permission('make_payments'):
            permissions.append("Paiements")
        if obj.has_permission('register_members'):
            permissions.append("Inscriptions")
        
        if permissions:
            return format_html(
                '<span style="color: blue;">{}</span>', 
                ", ".join(permissions)
            )
        return format_html('<span style="color: gray;">Consultation</span>')
    permissions_summary.short_description = _("Permissions")
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'family', 'practitioner', 'user'
        )


@admin.register(FamilyPaymentGroup)
class FamilyPaymentGroupAdmin(admin.ModelAdmin):
    list_display = [
        'description',
        'family_name',
        'total_amount',
        'payment_status',
        'created_at'
    ]
    list_filter = ['is_paid', 'created_at']
    search_fields = ['description', 'family__family_name']
    readonly_fields = ['group_id', 'created_at']
    
    def family_name(self, obj):
        """Affiche le nom de la famille avec lien"""
        url = reverse('admin:family_management_family_change', args=[obj.family.pk])
        return format_html('<a href="{}">{}</a>', url, obj.family.family_name)
    family_name.short_description = _("Famille")
    
    def payment_status(self, obj):
        """Affiche le statut de paiement"""
        if obj.is_paid:
            return format_html('<span style="color: green;">âœ“ Payé</span>')
        return format_html('<span style="color: red;">â³ En attente</span>')
    payment_status.short_description = _("Statut")


@admin.register(FamilyEvent)
class FamilyEventAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'family_name',
        'start_date',
        'location',
        'members_count',
        'is_private',
        'created_by'
    ]
    list_filter = [
        'is_private',
        'start_date',
        'created_at'
    ]
    search_fields = [
        'title',
        'description',
        'family__family_name',
        'location'
    ]
    readonly_fields = ['created_at']
    filter_horizontal = ['concerned_members']
    
    fieldsets = (
        (_('Informations principales'), {
            'fields': ('title', 'description', 'family')
        }),
        (_('Date et lieu'), {
            'fields': ('start_date', 'end_date', 'location')
        }),
        (_('Participants'), {
            'fields': ('concerned_members',)
        }),
        (_('Paramètres'), {
            'fields': ('is_private', 'created_by', 'created_at')
        })
    )
    
    def family_name(self, obj):
        """Affiche le nom de la famille avec lien"""
        url = reverse('admin:family_management_family_change', args=[obj.family.pk])
        return format_html('<a href="{}">{}</a>', url, obj.family.family_name)
    family_name.short_description = _("Famille")
    
    def members_count(self, obj):
        """Affiche le nombre de membres concernés"""
        count = obj.concerned_members.count()
        return format_html(
            '<span style="color: {};">{} membre(s)</span>',
            'green' if count > 0 else 'gray',
            count
        )
    members_count.short_description = _("Participants")
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'family', 'created_by'
        ).prefetch_related('concerned_members')


# Configuration des titres d'administration
admin.site.site_header = _("Administration MartialComp - Gestion Familiale")
admin.site.site_title = _("MartialComp Admin")
admin.site.index_title = _("Gestion des Familles")
