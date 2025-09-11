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
    verbose_name_plural = _('Profil Utilisateur')
    verbose_name = _('Profil')
    fk_name = 'user'
    fields = ('role', 'onboarding_completed', 'onboarding_step', 'organization')
    
    # Assurez-vous que le profil est toujours visible
    def has_add_permission(self, request, obj=None):
        return True
    
    def has_change_permission(self, request, obj=None):
        return True
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Personnalise les champs de cle etrangere dans le formulaire."""
        if db_field.name == "organization":
            # Remplacer par une sélection d'organisations de type club
            try:
                from apps.competitions.models import Club
                kwargs["queryset"] = Club.objects.all().order_by('name')
            except ImportError:
                pass
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline, )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_role_display', 'get_organizations', 'edit_profile_link')
    list_select_related = ('profile', )
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'profile__role')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'profile__role')
    
    def get_object(self, request, object_id, from_field=None):
        """S'assurer qu'un profil existe pour l'utilisateur."""
        obj = super().get_object(request, object_id, from_field)
        if obj:
            # Créer le profil s'il n'existe pas
            try:
                profile = obj.profile
            except UserProfile.DoesNotExist:
                profile = UserProfile.objects.create(
                    user=obj,
                    role='spectator',  # Rôle par défaut
                    onboarding_completed=False
                )
                print(f"[OK] Profil créé pour {obj.username} avec rôle: {profile.role}")
        return obj

    def get_role_display(self, instance):
        """Affiche le rôle de l'utilisateur en format lisible."""
        try:
            profile = getattr(instance, 'profile', None)
            if not profile or not hasattr(profile, 'role') or not profile.role:
                return "-"
                
            # Afficher le rôle brut pour le débogage
            print(f"DEBUG: Rôle brut pour {instance.username}: {profile.role}")
                
            # Dictionnaire des rôles à afficher
            role_display = {
                'admin': _("Administrateur"),
                'club_manager': _("Responsable de club"),
                'federation_admin': _("Responsable de fédération"),
                'judge': _("Juge/Arbitre"),
                'referee': _("Arbitre"),
                'participant': _("Participant"),
                'coach': _("Coach"),
                'spectator': _("Spectateur"),
                'event_manager': _("Gestionnaire d'événements")
            }
            
            # Retourner le libellé du rôle ou le rôle brut si non trouvé
            return role_display.get(profile.role, profile.role)
        except Exception as e:
            print(f"ERREUR dans get_role_display pour {instance.username}: {str(e)}")
            return "Erreur"
    
    get_role_display.short_description = _('Rôle')
    get_role_display.admin_order_field = 'profile__role'
    
    def get_organizations(self, instance):
        """Affiche les organisations associées à l'utilisateur."""
        try:
            # Chercher dans les modèles OrganizationMember
            from apps.organizations.models import OrganizationMember
            memberships = OrganizationMember.objects.filter(
                user=instance, 
                is_active=True
            ).select_related('organization')
            
            if not memberships.exists():
                # Chercher dans les modèles ClubAdministrator et FederationAdministrator pour compatibilité
                try:
                    from apps.competitions.models import ClubAdministrator, FederationAdministrator
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
                
                # Vérifier le profil utilisateur pour organization
                profile = getattr(instance, 'profile', None)
                if profile and hasattr(profile, 'organization') and profile.organization:
                    return profile.organization.name
                
                return "-"
            
            return ", ".join([m.organization.name for m in memberships])
        except Exception:
            return "-"
    
    get_organizations.short_description = _('Organisations')
    
    def edit_profile_link(self, instance):
        """Lien pour éditer directement le profil."""
        try:
            profile = getattr(instance, 'profile', None)
            if profile:
                from django.urls import reverse
                from django.utils.html import format_html
                url = reverse('admin:competitions_userprofile_change', args=[profile.pk])
                return format_html('<a href="{}" target="_blank">?? Éditer Profil</a>', url)
            else:
                # Proposer de créer le profil
                return format_html('<span style="color: red;">[ERREUR] Pas de profil</span>')
        except Exception:
            return "Erreur"
    
    edit_profile_link.short_description = _('Profil')
    edit_profile_link.allow_tags = True

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)
    
    # Actions admin pour changer les rôles rapidement
    def make_judge(self, request, queryset):
        """Transformer les utilisateurs sélectionnés en juges."""
        updated = 0
        for user in queryset:
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={'role': 'judge', 'onboarding_completed': True}
            )
            if not created:
                profile.role = 'judge'
                profile.onboarding_completed = True
                profile.save()
            updated += 1
        
        self.message_user(
            request,
            f"{updated} utilisateur(s) transformé(s) en juge(s)."
        )
    make_judge.short_description = "Transformer en juge(s)"
    
    def make_spectator(self, request, queryset):
        """Transformer les utilisateurs sélectionnés en spectateurs."""
        updated = 0
        for user in queryset:
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={'role': 'spectator', 'onboarding_completed': True}
            )
            if not created:
                profile.role = 'spectator'
                profile.onboarding_completed = True
                profile.save()
            updated += 1
        
        self.message_user(
            request,
            f"{updated} utilisateur(s) transformé(s) en spectateur(s)."
        )
    make_spectator.short_description = "Transformer en spectateur(s)"
    
    def make_federation_admin(self, request, queryset):
        """Transformer les utilisateurs sélectionnés en admins de fédération."""
        updated = 0
        for user in queryset:
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={'role': 'federation_admin', 'onboarding_completed': True}
            )
            if not created:
                profile.role = 'federation_admin'
                profile.onboarding_completed = True
                profile.save()
            updated += 1
        
        self.message_user(
            request,
            f"{updated} utilisateur(s) transformé(s) en admin(s) de fédération."
        )
    make_federation_admin.short_description = "Transformer en admin(s) de fédération"
    
    def make_coach(self, request, queryset):
        """Transformer les utilisateurs sélectionnés en coaches."""
        updated = 0
        for user in queryset:
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={'role': 'coach', 'onboarding_completed': True, 'onboarding_step': 'completed'}
            )
            if not created:
                profile.role = 'coach'
                profile.onboarding_completed = True
                profile.onboarding_step = 'completed'
                profile.save()
            updated += 1
        
        self.message_user(
            request,
            f"{updated} utilisateur(s) transformé(s) en coach(s)."
        )
    make_coach.short_description = "Transformer en coach(s)"
    
    def make_club_manager(self, request, queryset):
        """Transformer les utilisateurs sélectionnés en responsables de club."""
        updated = 0
        for user in queryset:
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={'role': 'club_manager', 'onboarding_completed': True, 'onboarding_step': 'completed'}
            )
            if not created:
                profile.role = 'club_manager'
                profile.onboarding_completed = True
                profile.onboarding_step = 'completed'
                profile.save()
            updated += 1
        
        self.message_user(
            request,
            f"{updated} utilisateur(s) transformé(s) en responsable(s) de club."
        )
    make_club_manager.short_description = "Transformer en responsable(s) de club"
    
    def make_participant(self, request, queryset):
        """Transformer les utilisateurs sélectionnés en participants."""
        updated = 0
        for user in queryset:
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={'role': 'participant', 'onboarding_completed': True, 'onboarding_step': 'completed'}
            )
            if not created:
                profile.role = 'participant'
                profile.onboarding_completed = True
                profile.onboarding_step = 'completed'
                profile.save()
            updated += 1
        
        self.message_user(
            request,
            f"{updated} utilisateur(s) transformé(s) en participant(s)."
        )
    make_participant.short_description = "Transformer en participant(s)"
    
    def complete_onboarding(self, request, queryset):
        """Marquer l'onboarding comme terminé pour les utilisateurs sélectionnés."""
        updated = 0
        for user in queryset:
            try:
                profile = user.profile
                if not profile.onboarding_completed:
                    profile.onboarding_completed = True
                    profile.onboarding_step = 'completed'
                    profile.save()
                    updated += 1
            except UserProfile.DoesNotExist:
                # Créer un profil si nécessaire
                UserProfile.objects.create(
                    user=user,
                    role='spectator',
                    onboarding_completed=True,
                    onboarding_step='completed'
                )
                updated += 1
        
        self.message_user(
            request,
            f"Onboarding terminé pour {updated} utilisateur(s)."
        )
    complete_onboarding.short_description = "Terminer l'onboarding"
    
    actions = ['make_judge', 'make_spectator', 'make_federation_admin', 'make_coach', 'make_club_manager', 'make_participant', 'complete_onboarding']

# Unregister the default UserAdmin and register our custom one
try:
    admin.site.unregister(User)
    print("[OK] Ancien admin désenregistré")
except admin.sites.NotRegistered:
    print("?? L'admin User n'était pas enregistré")

# Enregistrer notre admin utilisateur personnalisé
admin.site.register(User, CustomUserAdmin)
print("[OK] CustomUserAdmin avec changement de mot de passe enregistré")

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
        try:
            from apps.organizations.models import OrganizationType
            return [(choice, label) for choice, label in OrganizationType.choices]
        except (ImportError, AttributeError):
            return []
    
    def queryset(self, request, queryset):
        if self.value():
            # Trouver les utilisateurs associés aux organisations de ce type
            try:
                from apps.organizations.models import OrganizationMember, Organization
                org_ids = Organization.objects.filter(organization_type=self.value()).values_list('id', flat=True)
                user_ids = OrganizationMember.objects.filter(organization_id__in=org_ids).values_list('user_id', flat=True)
                return queryset.filter(user_id__in=user_ids)
            except (ImportError, Exception):
                return queryset
        return queryset

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'display_role', 'onboarding_completed', 'get_organizations', 'edit_user_link', 'get_dashboard_link'
    )
    list_filter = (UserRoleFilter, 'onboarding_completed', 'onboarding_step', OrganizationTypeFilter)
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'role')
    readonly_fields = ('onboarding_step',)
    list_editable = ('onboarding_completed',)  # Permet l'édition rapide
    
    # Actions pour changer rapidement les rôles
    def make_coach_profile(self, request, queryset):
        """Changer le rôle en coach."""
        updated = queryset.update(role='coach', onboarding_completed=True, onboarding_step='completed')
        self.message_user(request, f"{updated} profil(s) changé(s) vers coach.")
    make_coach_profile.short_description = "Changer en coach"
    
    def make_judge_profile(self, request, queryset):
        """Changer le rôle en juge."""
        updated = queryset.update(role='judge', onboarding_completed=True, onboarding_step='completed')
        self.message_user(request, f"{updated} profil(s) changé(s) vers juge.")
    make_judge_profile.short_description = "Changer en juge"
    
    def make_spectator_profile(self, request, queryset):
        """Changer le rôle en spectateur."""
        updated = queryset.update(role='spectator', onboarding_completed=True, onboarding_step='completed')
        self.message_user(request, f"{updated} profil(s) changé(s) vers spectateur.")
    make_spectator_profile.short_description = "Changer en spectateur"
    
    def make_federation_admin_profile(self, request, queryset):
        """Changer le rôle en admin de fédération."""
        updated = queryset.update(role='federation_admin', onboarding_completed=True, onboarding_step='completed')
        self.message_user(request, f"{updated} profil(s) changé(s) vers admin de fédération.")
    make_federation_admin_profile.short_description = "Changer en admin de fédération"
    
    def make_club_manager_profile(self, request, queryset):
        """Changer le rôle en responsable de club."""
        updated = queryset.update(role='club_manager', onboarding_completed=True, onboarding_step='completed')
        self.message_user(request, f"{updated} profil(s) changé(s) vers responsable de club.")
    make_club_manager_profile.short_description = "Changer en responsable de club"
    
    def complete_onboarding_profile(self, request, queryset):
        """Terminer l'onboarding."""
        updated = queryset.update(onboarding_completed=True, onboarding_step='completed')
        self.message_user(request, f"Onboarding terminé pour {updated} profil(s).")
    complete_onboarding_profile.short_description = "Terminer l'onboarding"
    
    actions = [
        'make_coach_profile', 'make_judge_profile', 'make_spectator_profile', 
        'make_federation_admin_profile', 'make_club_manager_profile', 'complete_onboarding_profile'
    ]
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('user', 'role', 'onboarding_completed', 'onboarding_step')
        }),
        (_('Associations'), {
            'fields': ('organization',),
            'classes': ('collapse',)
        }),
    )
    
    def display_role(self, obj):
        if not hasattr(obj, 'role') or not obj.role:
            return 'N/A'
        
        # Dictionnaire des rôles à afficher
        role_display = {
            'admin': _("Administrateur"),
            'club_manager': _("Responsable de club"),
            'federation_admin': _("Responsable de fédération"),
            'judge': _("Juge/Arbitre"),
            'referee': _("Arbitre"),
            'participant': _("Participant"),
            'coach': _("Coach"),
            'spectator': _("Spectateur"),
            'event_manager': _("Gestionnaire d'événements")
        }
        
        # Retourner le libellé du rôle ou le rôle brut si non trouvé
        return role_display.get(obj.role, obj.role)
        
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
            from apps.organizations.models import OrganizationMember
            memberships = OrganizationMember.objects.filter(
                user=obj.user, 
                is_active=True
            ).select_related('organization')
            
            if not memberships.exists():
                # Vérifier si le profil a une organization
                if hasattr(obj, 'organization') and obj.organization:
                    return obj.organization.name
                return "-"
            
            return ", ".join([m.organization.name for m in memberships])
        except Exception:
            return "-"
    
    get_organizations.short_description = _('Organisations')
    
    def edit_user_link(self, obj):
        """Lien pour éditer l'utilisateur associé."""
        try:
            from django.urls import reverse
            from django.utils.html import format_html
            url = reverse('admin:auth_user_change', args=[obj.user.pk])
            return format_html('<a href="{}" target="_blank">?? Éditer Utilisateur</a>', url)
        except Exception:
            return "Erreur"
    
    edit_user_link.short_description = _('Utilisateur')
    edit_user_link.allow_tags = True
    
    def get_dashboard_link(self, obj):
        """Lien direct vers le dashboard de l'utilisateur selon son rôle."""
        if not obj or not obj.role:
            return "N/A"
            
        dashboard_urls = {
            'coach': 'competitions:dashboard:coach_multidiscipline',
            'judge': 'competitions:dashboard:referee', 
            'referee': 'competitions:dashboard:referee',
            'spectator': 'competitions:dashboard:spectator',
            'federation_admin': 'competitions:dashboard:federations',
            'club_manager': 'competitions:dashboard:club',
            'participant': 'competitions:dashboard:participant',
            'admin': 'competitions:dashboard:admin'
        }
        
        url_name = dashboard_urls.get(obj.role)
        if url_name:
            try:
                from django.urls import reverse
                from django.utils.html import format_html
                url = reverse(url_name)
                return format_html('<a href="{}" target="_blank" class="button">?? Dashboard {}</a>', url, obj.role.title())
            except Exception as e:
                return f"Erreur: {e}"
        return "Pas de dashboard"
    get_dashboard_link.short_description = 'Dashboard'
    get_dashboard_link.allow_tags = True
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Personnalise les champs de clé étrangère dans le formulaire."""
        if db_field.name == "organization":
            # Remplacer par une sélection d'organisations de type club
            try:
                from apps.competitions.models import Club
                kwargs["queryset"] = Club.objects.all().order_by('name')
            except Exception:
                pass
        return super().formfield_for_foreignkey(db_field, request, **kwargs)




