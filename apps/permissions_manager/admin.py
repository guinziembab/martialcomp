from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

class CustomUserAdmin(BaseUserAdmin):
    """Admin personnalisé pour User avec toutes les fonctionnalités de changement de mot de passe"""
    
    # Fieldsets complets avec gestion du mot de passe
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates importantes', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
    )
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    filter_horizontal = ('groups', 'user_permissions',)
    
    # Assurer que toutes les fonctionnalités de UserAdmin sont disponibles
    change_password_template = None
    
    def get_form(self, request, obj=None, **kwargs):
        """Utiliser le formulaire par défaut Django avec changement de mot de passe"""
        return super().get_form(request, obj, **kwargs)

# Désinscrire l'ancien admin s'il existe
try:
    admin.site.unregister(User)
    print("   SUCCESS: Ancien admin desenregistre")
except admin.sites.NotRegistered:
    print("   WARNING: Aucun admin User a desenregistrer")

# Enregistrer le nouvel admin
admin.site.register(User, CustomUserAdmin)
print("   SUCCESS: CustomUserAdmin avec changement de mot de passe enregistre")

