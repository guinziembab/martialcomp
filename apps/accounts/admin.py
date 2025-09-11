from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User
from django.contrib.admin.utils import unquote
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.db import ProgrammingError


class UserAdmin(DjangoUserAdmin):
    """Custom UserAdmin that gracefully handles missing optional related tables
    when building the delete confirmation page.

    This specifically catches the case where the finances TemporaryAccess table
    is not yet present, avoiding a hard 500 during delete_view.
    """

    def delete_view(self, request, object_id, extra_context=None):
        try:
            return super().delete_view(request, object_id, extra_context=extra_context)
        except ProgrammingError as exc:  # psycopg2.errors.UndefinedTable wrapped by Django
            message = str(exc)
            if 'finances_temporaryaccess' in message:
                # Fallback: proceed with a simplified confirmation that does not
                # attempt to enumerate related objects from the missing table.
                obj = self.get_object(request, unquote(object_id))
                if obj is None:
                    return HttpResponseRedirect(reverse('admin:auth_user_changelist'))

                if request.method == 'POST':
                    # Perform deletion without building the related objects tree
                    self.log_deletion(request, obj, str(obj))
                    obj.delete()
                    return HttpResponseRedirect(reverse('admin:auth_user_changelist'))

                context = {
                    **self.admin_site.each_context(request),
                    'title': _('Êtes-vous sûr ?'),
                    'object': obj,
                    'object_id': object_id,
                    'opts': self.model._meta,
                    # Provide empty structures so the default template renders
                    'deleted_objects': [],
                    'perms_lacking': [],
                    'protected': [],
                }
                return TemplateResponse(request, 'admin/delete_confirmation.html', context)
            # If it is a different DB error, re-raise
            raise


# Replace the default User admin with our custom one
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass
admin.site.register(User, UserAdmin)
