# -*- coding: utf-8 -*-
"""
Configuration de l'administration Django pour le système d'adhésion
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from apps.core.isolation import OrganizationSecureAdminMixin

from .models import (
    MembershipPackage, MembershipSubscription, MembershipWorkflow,
    OnlineMembershipForm, MembershipFormSubmission, MembershipAlert
)


@admin.register(MembershipPackage)
class MembershipPackageAdmin(OrganizationSecureAdminMixin, admin.ModelAdmin):
    list_display = [
        'name', 'organization', 'category', 'package_type', 
        'base_price', 'currency', 'is_active', 'is_featured'
    ]
    list_filter = [
        'organization', 'category', 'package_type', 'is_active', 
        'is_featured', 'auto_renewal'
    ]
    search_fields = ['name', 'description', 'organization__name']
    filter_horizontal = ['disciplines']
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': (
                'organization', 'name', 'description', 'category', 'package_type'
            )
        }),
        (_('Configuration tarifaire'), {
            'fields': (
                'base_price', 'currency'
            )
        }),
        (_('Avantages inclus'), {
            'fields': (
                'disciplines', 'max_sessions_per_week', 
                'includes_competitions', 'includes_seminars', 'includes_equipment'
            )
        }),
        (_('Restrictions d\'âge'), {
            'fields': ('min_age', 'max_age'),
            'classes': ('collapse',)
        }),
        (_('Configuration'), {
            'fields': (
                'auto_renewal', 'grace_period_days', 'is_active', 
                'is_featured', 'sort_order'
            )
        })
    )
    
    ordering = ['organization', 'sort_order', 'name']


@admin.register(MembershipSubscription)
class MembershipSubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'practitioner', 'package', 'status', 'start_date', 
        'end_date', 'price_paid', 'currency', 'auto_renew'
    ]
    list_filter = [
        'status', 'auto_renew', 'package__organization', 
        'package__category', 'created_at'
    ]
    search_fields = [
        'practitioner__first_name', 'practitioner__last_name', 
        'practitioner__user__email', 'package__name'
    ]
    filter_horizontal = ['custom_disciplines']
    
    fieldsets = (
        (_('Souscription'), {
            'fields': ('practitioner', 'package')
        }),
        (_('Période d\'adhésion'), {
            'fields': ('start_date', 'end_date', 'renewal_date', 'status', 'auto_renew')
        }),
        (_('Facturation'), {
            'fields': ('price_paid', 'currency')
        }),
        (_('Personnalisation'), {
            'fields': ('custom_disciplines', 'notes'),
            'classes': ('collapse',)
        }),
        (_('Méta-données'), {
            'fields': ('created_by',),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'practitioner', 'package', 'package__organization'
        )


@admin.register(MembershipWorkflow)
class MembershipWorkflowAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'organization', 'trigger_type', 'action_type', 
        'trigger_days_before', 'is_active'
    ]
    list_filter = [
        'organization', 'trigger_type', 'action_type', 'is_active'
    ]
    search_fields = ['name', 'description', 'organization__name']
    filter_horizontal = ['applicable_packages']
    
    fieldsets = (
        (_('Informations générales'), {
            'fields': ('organization', 'name', 'description')
        }),
        (_('Configuration du déclencheur'), {
            'fields': ('trigger_type', 'trigger_days_before')
        }),
        (_('Configuration de l\'action'), {
            'fields': ('action_type', 'action_content')
        }),
        (_('Conditions d\'application'), {
            'fields': ('applicable_packages', 'is_active')
        })
    )
    
    ordering = ['organization', 'trigger_type', 'trigger_days_before']


@admin.register(OnlineMembershipForm)
class OnlineMembershipFormAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'organization', 'form_type', 'is_active', 
        'is_public', 'created_at'
    ]
    list_filter = [
        'organization', 'form_type', 'is_active', 'is_public', 
        'require_medical_certificate'
    ]
    search_fields = ['name', 'title', 'organization__name', 'slug']
    filter_horizontal = ['available_packages']
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        (_('Configuration de base'), {
            'fields': (
                'organization', 'name', 'slug', 'form_type'
            )
        }),
        (_('Contenu affiché'), {
            'fields': (
                'title', 'description', 'welcome_message', 'success_message'
            )
        }),
        (_('Packages disponibles'), {
            'fields': ('available_packages',)
        }),
        (_('Options de collecte'), {
            'fields': (
                'require_medical_certificate', 'collect_emergency_contact',
                'collect_experience_level', 'allow_payment_plans'
            )
        }),
        (_('Configuration d\'accès'), {
            'fields': (
                'is_active', 'is_public', 'max_submissions_per_day'
            )
        })
    )
    
    ordering = ['-created_at']

    def view_form_url(self, obj):
        if obj.slug:
            url = obj.get_absolute_url()
            return format_html('<a href="{}" target="_blank">{}</a>', url, url)
        return "-"
    view_form_url.short_description = _('Voir le formulaire')


@admin.register(MembershipFormSubmission)
class MembershipFormSubmissionAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 'email', 'selected_package', 'status', 
        'created_at', 'processed_by'
    ]
    list_filter = [
        'status', 'form__organization', 'selected_package', 'created_at'
    ]
    search_fields = [
        'first_name', 'last_name', 'email', 'phone',
        'selected_package__name'
    ]
    
    fieldsets = (
        (_('Formulaire et package'), {
            'fields': ('form', 'selected_package')
        }),
        (_('Informations personnelles'), {
            'fields': (
                'first_name', 'last_name', 'email', 'phone', 'date_of_birth'
            )
        }),
        (_('Contact d\'urgence'), {
            'fields': ('emergency_contact_name', 'emergency_contact_phone'),
            'classes': ('collapse',)
        }),
        (_('Données personnalisées'), {
            'fields': ('form_data',),
            'classes': ('collapse',)
        }),
        (_('Traitement'), {
            'fields': (
                'status', 'processed_by', 'processing_notes', 'created_subscription'
            )
        })
    )
    
    readonly_fields = ['created_at', 'updated_at', 'form_data']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'form', 'selected_package', 'processed_by', 'created_subscription'
        )

    def view_submission_detail(self, obj):
        """Lien vers le détail de la soumission"""
        url = reverse('admin:membership_membershipformsubmission_change', args=[obj.pk])
        return format_html('<a href="{}">Voir détails</a>', url)
    view_submission_detail.short_description = _('Détails')


@admin.register(MembershipAlert)
class MembershipAlertAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'subscription', 'alert_type', 'priority', 
        'is_resolved', 'notification_sent', 'created_at'
    ]
    list_filter = [
        'alert_type', 'priority', 'is_resolved', 'notification_sent',
        'subscription__package__organization', 'created_at'
    ]
    search_fields = [
        'title', 'message', 'subscription__practitioner__first_name',
        'subscription__practitioner__last_name'
    ]
    
    fieldsets = (
        (_('Alerte'), {
            'fields': ('subscription', 'alert_type', 'priority', 'title', 'message')
        }),
        (_('Traitement'), {
            'fields': ('is_resolved', 'resolved_at', 'resolved_by')
        }),
        (_('Notification'), {
            'fields': ('notification_sent', 'notification_sent_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'subscription', 'subscription__practitioner', 
            'subscription__package', 'resolved_by'
        )

    def resolve_alert(self, request, queryset):
        """Action pour résoudre les alertes sélectionnées"""
        from django.utils import timezone
        
        updated = queryset.filter(is_resolved=False).update(
            is_resolved=True,
            resolved_at=timezone.now(),
            resolved_by=request.user
        )
        
        self.message_user(
            request, 
            _('%(count)d alerte(s) marquée(s) comme résolue(s).') % {'count': updated}
        )
    resolve_alert.short_description = _('Marquer comme résolu')

    actions = ['resolve_alert']


# Configurations supplémentaires pour l'admin
admin.site.site_header = _('Administration MartialComp - Système d\'Adhésion')
admin.site.site_title = _('MartialComp Admin')
admin.site.index_title = _('Gestion des Adhésions')