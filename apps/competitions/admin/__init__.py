# Import all admin modules
try:
  from . import user
  from . import competition
  from . import discipline
  from . import category
  from . import club
  from . import judge
  from . import registration
  from . import federation
  from . import qr_code
  from . import practitioner  # Admin pour les pratiquants avec filtre organisation
  from . import technical_scoring  # BUG #3 FIX: Admin pour les notes des juges
  from . import tutorials
except ImportError as e:
  import logging
  logger = logging.getLogger(__name__)
  logger.error(f"Error importing admin modules: {e}")

# Contact submissions admin
try:
    from django.contrib import admin as _admin
    from apps.competitions.models.contact import ContactSubmission

    @_admin.register(ContactSubmission)
    class ContactSubmissionAdmin(_admin.ModelAdmin):
        list_display = ('name', 'email', 'organization', 'subject',
                        'created_at', 'is_read', 'responded')
        list_filter = ('subject', 'is_read', 'responded', 'created_at')
        search_fields = ('name', 'email', 'organization', 'message')
        readonly_fields = ('created_at',)
        list_editable = ('is_read', 'responded')
        ordering = ('-created_at',)
except Exception:
    pass
