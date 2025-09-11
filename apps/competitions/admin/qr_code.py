from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.utils.safestring import mark_safe

# Import avec gestion d'erreur
try:
    from ..models import PractitionerQRCode, QRCodeScan
except ImportError:
    PractitionerQRCode = None
    QRCodeScan = None
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("Impossible d'importer PractitionerQRCode ou QRCodeScan")


# N'enregistrer que si le modèle existe
if PractitionerQRCode is not None:
    @admin.register(PractitionerQRCode)
    class PractitionerQRCodeAdmin(admin.ModelAdmin):
        list_display = [
            'practitioner', 
            'code_display', 
            'is_active', 
            'is_federation_validated',
            'scan_count',
            'last_scan_date',
            'created_at'
        ]
        
        list_filter = [
            'is_active',
            'is_federation_validated',
            'created_at',
            'last_scan_date'
        ]
        
        search_fields = [
            'practitioner__first_name',
            'practitioner__last_name',
            'practitioner__license_number',
            'code'
        ]
        
        readonly_fields = [
            'code',
            'qr_code_display',
            'scan_count',
            'last_scan_date',
            'created_at',
            'updated_at',
            'federation_validation_date'
        ]
        
        fieldsets = [
            (_('Informations principales'), {
                'fields': ['practitioner', 'code', 'qr_code_display', 'is_active']
            }),
            (_('Validation fédération'), {
                'fields': ['is_federation_validated', 'federation_validation_date']
            }),
            (_('Statistiques'), {
                'fields': ['scan_count', 'last_scan_date']
            }),
            (_('Dates'), {
                'fields': ['created_at', 'updated_at']
            })
        ]
        
        def code_display(self, obj):
            return format_html('<code>{}</code>', obj.code)
        code_display.short_description = _('Code')
        
        def qr_code_display(self, obj):
            if obj.qr_image:
                return format_html(
                    '<img src="{}" style="max-width: 200px; max-height: 200px;">',
                    obj.qr_image.url
                )
            return '-'
        qr_code_display.short_description = _('QR Code')
        
        actions = ['validate_for_federation', 'invalidate_for_federation']
        
        def validate_for_federation(self, request, queryset):
            count = 0
            for qr_code in queryset:
                if qr_code.validate_for_federation():
                    count += 1
            
            self.message_user(
                request,
                _(f"{count} QR codes validés pour la fédération")
            )
        validate_for_federation.short_description = _("Valider pour la fédération")
        
        def invalidate_for_federation(self, request, queryset):
            count = queryset.update(is_federation_validated=False, federation_validation_date=None)
            self.message_user(
                request,
                _(f"{count} QR codes invalidés pour la fédération")
            )
        invalidate_for_federation.short_description = _("Invalider pour la fédération")


if QRCodeScan is not None:
    @admin.register(QRCodeScan)
    class QRCodeScanAdmin(admin.ModelAdmin):
        list_display = [
            'scan_date',
            'practitioner_name',
            'scan_type',
            'scanned_by',
            'location',
            'is_valid',
            'related_event'
        ]
        
        list_filter = [
            'scan_type',
            'is_valid',
            'scan_date',
            'competition',
            'training_session',
            'event'
        ]
        
        search_fields = [
            'qr_code__practitioner__first_name',
            'qr_code__practitioner__last_name',
            'qr_code__practitioner__license_number',
            'scanned_by__username',
            'location'
        ]
        
        readonly_fields = [
            'qr_code',
            'scan_type',
            'scanned_by',
            'scan_date',
            'location',
            'is_valid',
            'validation_message',
            'ip_address',
            'user_agent'
        ]
        
        fieldsets = [
            (_('Informations du scan'), {
                'fields': ['qr_code', 'scan_type', 'scan_date', 'scanned_by', 'location']
            }),
            (_('Validation'), {
                'fields': ['is_valid', 'validation_message']
            }),
            (_('Relations'), {
                'fields': ['competition', 'training_session', 'event']
            }),
            (_('Métadonnées'), {
                'fields': ['ip_address', 'user_agent']
            })
        ]
        
        def practitioner_name(self, obj):
            return obj.qr_code.practitioner.full_name
        practitioner_name.short_description = _('Pratiquant')
        
        def related_event(self, obj):
            if obj.competition:
                return format_html('<i class="fas fa-trophy"></i> {}', obj.competition.name)
            elif obj.training_session:
                return format_html('<i class="fas fa-dumbbell"></i> {}', obj.training_session.training_slot.name)
            elif obj.event:
                return format_html('<i class="fas fa-calendar"></i> {}', obj.event.name)
            return '-'
        related_event.short_description = _('Ã‰vénement lié')
        
        def has_add_permission(self, request):
            # Les scans ne peuvent pas Ãªtre créés manuellement
            return False
        
        def has_change_permission(self, request, obj=None):
            # Les scans ne peuvent pas Ãªtre modifiés
            return False
