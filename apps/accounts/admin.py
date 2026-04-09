from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User
from django.contrib.admin.utils import unquote
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.db import ProgrammingError, connection
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)


def clean_user_related_data(user_id):
    """
    Nettoie les donnees liees a un utilisateur avant suppression.
    Utilise du SQL brut pour eviter les erreurs de modele.
    """
    tables_to_clean = [
        ('api_auth_refreshtoken', 'user_id'),
        ('competitions_notification', 'user_id'),
    ]

    cleaned = []
    with connection.cursor() as cursor:
        for table, column in tables_to_clean:
            try:
                cursor.execute(f"DELETE FROM {table} WHERE {column} = %s", [user_id])
                if cursor.rowcount > 0:
                    cleaned.append(f"{table}: {cursor.rowcount}")
            except Exception as e:
                logger.debug(f"Table {table} cleanup skipped: {e}")

    return cleaned


class UserAdmin(DjangoUserAdmin):
    """Custom UserAdmin that gracefully handles missing or problematic related tables
    when building the delete confirmation page.

    Handles:
    - finances_temporaryaccess missing table
    - api_auth_refreshtoken.tenant column mismatch
    - Other database schema issues
    """

    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    actions = ['safe_delete_users']

    def delete_view(self, request, object_id, extra_context=None):
        try:
            return super().delete_view(request, object_id, extra_context=extra_context)
        except ProgrammingError as exc:
            message = str(exc)
            # Handle known problematic tables/columns
            known_issues = [
                'finances_temporaryaccess',
                'api_auth_refreshtoken.tenant',
                'api_auth_refreshtoken',
            ]

            if any(issue in message for issue in known_issues):
                obj = self.get_object(request, unquote(object_id))
                if obj is None:
                    return HttpResponseRedirect(reverse('admin:auth_user_changelist'))

                if request.method == 'POST':
                    try:
                        # Clean related data first
                        cleaned = clean_user_related_data(obj.id)
                        if cleaned:
                            logger.info(f"Cleaned before delete: {', '.join(cleaned)}")

                        # Log and delete
                        self.log_deletion(request, obj, str(obj))
                        obj.delete()
                        messages.success(request, f"Utilisateur {obj.username} supprime avec succes.")
                    except Exception as e:
                        messages.error(request, f"Erreur lors de la suppression: {e}")
                        logger.error(f"Delete error for user {obj.id}: {e}")
                    return HttpResponseRedirect(reverse('admin:auth_user_changelist'))

                context = {
                    **self.admin_site.each_context(request),
                    'title': _('Etes-vous sur ?'),
                    'object': obj,
                    'object_id': object_id,
                    'opts': self.model._meta,
                    'deleted_objects': [f"Utilisateur: {obj.username} ({obj.email})"],
                    'perms_lacking': [],
                    'protected': [],
                    'model_count': {'Utilisateur': 1},
                }
                return TemplateResponse(request, 'admin/delete_confirmation.html', context)
            raise
        except Exception as exc:
            # Catch any other exception during delete view
            logger.error(f"Unexpected error in delete_view: {exc}")
            obj = self.get_object(request, unquote(object_id))
            if obj and request.method == 'POST':
                try:
                    cleaned = clean_user_related_data(obj.id)
                    self.log_deletion(request, obj, str(obj))
                    obj.delete()
                    messages.success(request, f"Utilisateur {obj.username} supprime.")
                    return HttpResponseRedirect(reverse('admin:auth_user_changelist'))
                except Exception as e:
                    messages.error(request, f"Impossible de supprimer: {e}")
            raise

    @admin.action(description="Supprimer les utilisateurs selectionnes (securise)")
    def safe_delete_users(self, request, queryset):
        """Action de suppression securisee qui nettoie les relations problematiques."""
        deleted = 0
        errors = []

        for user in queryset:
            if user.is_superuser:
                errors.append(f"{user.username}: superuser protege")
                continue
            try:
                clean_user_related_data(user.id)
                username = user.username
                user.delete()
                deleted += 1
                logger.info(f"User {username} deleted via safe_delete_users")
            except Exception as e:
                errors.append(f"{user.username}: {str(e)[:50]}")
                logger.error(f"Failed to delete user {user.id}: {e}")

        if deleted:
            messages.success(request, f"{deleted} utilisateur(s) supprime(s).")
        if errors:
            messages.warning(request, f"Erreurs: {'; '.join(errors[:3])}")


# Replace the default User admin with our custom one
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass
admin.site.register(User, UserAdmin)
