from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

try:
    from ..models import UserProfile
except ImportError:
    # Importation directe si l'importation via __init__.py échoue
    from ..models.users import UserProfile

# User and UserProfile Admin
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = _('Profil')
    fk_name = 'user'
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Personnalise les champs de clé étrangère dans le formulaire."""
        if db_field.name == "club":
            # Remplacer par une sélection d'organisations de type club
            from organizations.models import Organization
            kwargs["queryset"] = Organization.objects.filter(
                organization_type__in=['club', 'academy']
            ).order_by('name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline, )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_roles', 'get_organizations')
    list_select_related = ('profile', )

    def get_roles(self, instance):
        """Affiche les rôles de l'utilisateur."""
        profile = getattr(instance, 'profile', None)
        if not profile:
            return "-"
        
        # Accéder au rôle depuis le profil utilisateur
        role = getattr(profile, 'role', None)
        if not role:
            return "-"
            
        roles = []
        
        role_mapping = {
            'admin': "Admin",
            'club_manager': "Club Manager",
            'referee': "Referee",
            'judge': "Judge",
            'participant': "Participant",
            'spectator': "Spectator",
            'coach': "Coach",
            'event_manager': "Event Manager",
            'federation_admin': "Federation Admin"
        }
        
        # Ajouter le rôle principal s'il existe dans le mapping
        if role in role_mapping:
            roles.append(role_mapping[role])
        
        # Pour referee/judge qui peuvent partager une logique
        if role in ['referee', 'judge']:
            roles.append("Referee/Judge")
        
        return ", ".join(roles) if roles else "-"
    
    get_roles.short_description = _('Rôles')
    
    def get_organizations(self, instance):
        """Affiche les organisations associées à l'utilisateur."""
        try:
            # Chercher dans les modèles OrganizationMember
            from organizations.models import OrganizationMember
            memberships = OrganizationMember.objects.filter(
                user=instance, 
                is_active=True
            ).select_related('organization')
            
            if not memberships.exists():
                # Chercher dans les modèles ClubAdministrator et FederationAdministrator pour compatibilité
                try:
                    from competitions.models import ClubAdministrator, FederationAdministrator
                    club_admins = ClubAdministrator.objects.filter(user=instance)
                    fed_admins = FederationAdministrator.objects.filter(user=instance)
                    
                    orgs = []
                    for admin in club_admins:
                        if hasattr(admin, 'organization') and admin.organization:
                            orgs.append(admin.organization.name)
                    
                    for admin in fed_admins:
                        if hasattr(admin, 'organization') and admin.organization:
                            orgs.append(admin.organization.name)
                    
                    return ", ".join(orgs) if orgs else "-"
                except (ImportError, Exception):
                    pass
                
                # Vérifier le profil utilisateur pour club
                profile = getattr(instance, 'profile', None)
                if profile and hasattr(profile, 'club') and profile.club:
                    return profile.club.name
                
                return "-"
            
            return ", ".join([m.organization.name for m in memberships])
        except Exception:
            return "-"
    
    get_organizations.short_description = _('Organisations')

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)

# Unregister the default UserAdmin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

class UserRoleFilter(admin.SimpleListFilter):
    title = _('Rôle')
    parameter_name = 'role'
    
    def lookups(self, request, model_admin):
        return [
            ('admin', _('Administrateur')),
            ('federation_admin', _('Admin Fédération')),
            ('club_manager', _('Responsable de club')),
            ('referee', _('Arbitre')),
            ('judge', _('Juge')),
            ('participant', _('Participant')),
            ('spectator', _('Spectateur')),
            ('coach', _('Coach')),
            ('event_manager', _('Gestionnaire d\'événements'))
        ]
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(role=self.value())
        return queryset

class OrganizationTypeFilter(admin.SimpleListFilter):
    """Filtre pour le type d'organisation associée à l'utilisateur."""
    title = _('Type d\'organisation')
    parameter_name = 'organization_type'
    
    def lookups(self, request, model_admin):
        from organizations.models import OrganizationType
        return [(choice, label) for choice, label in OrganizationType.choices]
    
    def queryset(self, request, queryset):
        if self.value():
            # Trouver les utilisateurs associés aux organisations de ce type
            from organizations.models import OrganizationMember, Organization
            org_ids = Organization.objects.filter(organization_type=self.value()).values_list('id', flat=True)
            user_ids = OrganizationMember.objects.filter(organization_id__in=org_ids).values_list('user_id', flat=True)
            return queryset.filter(user_id__in=user_ids)
        return queryset

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'display_role', 'display_is_admin', 'display_is_federation_admin', 
        'display_is_club_manager', 'display_is_referee', 'display_is_participant', 
        'display_is_spectator', 'onboarding_completed', 'get_organizations'
    )
    list_filter = (UserRoleFilter, 'onboarding_completed', OrganizationTypeFilter)
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    
    def display_role(self, obj):
        return obj.role if hasattr(obj, 'role') else 'N/A'
    display_role.short_description = _('Rôle')
    
    def display_is_admin(self, obj):
        return obj.role == 'admin' if hasattr(obj, 'role') else False
    display_is_admin.boolean = True
    display_is_admin.short_description = _('Admin')
    
    def display_is_federation_admin(self, obj):
        return obj.role == 'federation_admin' if hasattr(obj, 'role') else False
    display_is_federation_admin.boolean = True
    display_is_federation_admin.short_description = _('Admin Fédération')
    
    def display_is_club_manager(self, obj):
        return obj.role == 'club_manager' if hasattr(obj, 'role') else False
    display_is_club_manager.boolean = True
    display_is_club_manager.short_description = _('Responsable de club')
    
    def display_is_referee(self, obj):
        role = getattr(obj, 'role', None)
        return role == 'referee' or role == 'judge'
    display_is_referee.boolean = True
    display_is_referee.short_description = _('Arbitre/Juge')
    
    def display_is_participant(self, obj):
        return obj.role == 'participant' if hasattr(obj, 'role') else False
    display_is_participant.boolean = True
    display_is_participant.short_description = _('Participant')
    
    def display_is_spectator(self, obj):
        return obj.role == 'spectator' if hasattr(obj, 'role') else False
    display_is_spectator.boolean = True
    display_is_spectator.short_description = _('Spectateur')
    
    def get_organizations(self, obj):
        """Affiche les organisations associées à l'utilisateur."""
        try:
            # Chercher dans les modèles OrganizationMember
            from organizations.models import OrganizationMember
            memberships = OrganizationMember.objects.filter(
                user=obj.user, 
                is_active=True
            ).select_related('organization')
            
            if not memberships.exists():
                # Vérifier si le profil a un club
                if hasattr(obj, 'club') and obj.club:
                    return obj.club.name
                return "-"
            
            return ", ".join([m.organization.name for m in memberships])
        except Exception:
            return "-"
    
    get_organizations.short_description = _('Organisations')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Personnalise les champs de clé étrangère dans le formulaire."""
        if db_field.name == "club":
            # Remplacer par une sélection d'organisations de type club
            from organizations.models import Organization
            kwargs["queryset"] = Organization.objects.filter(
                organization_type__in=['club', 'academy']
            ).order_by('name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)