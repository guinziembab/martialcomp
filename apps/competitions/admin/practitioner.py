"""
Admin pour les Practitioners avec filtres et actions pour corriger les organisations manquantes.
"""
from django.contrib import admin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.db.models import Q

from apps.competitions.models import Practitioner, Club
from apps.organizations.models import Organization


class OrganizationNullFilter(admin.SimpleListFilter):
    """Filtre pour afficher les pratiquants sans organisation."""
    title = _('Organisation')
    parameter_name = 'has_organization'

    def lookups(self, request, model_admin):
        return (
            ('no', _('Sans organisation')),
            ('yes', _('Avec organisation')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'no':
            return queryset.filter(organization__isnull=True)
        if self.value() == 'yes':
            return queryset.filter(organization__isnull=False)
        return queryset


class ClubFilter(admin.SimpleListFilter):
    """Filtre pour afficher les pratiquants par club."""
    title = _('Club')
    parameter_name = 'club'

    def lookups(self, request, model_admin):
        """Retourne la liste des clubs avec leur nombre de pratiquants."""
        clubs = Club.objects.filter(
            organization__isnull=False,
            is_active=True
        ).select_related('organization').order_by('name')

        return [(club.id, f"{club.name}") for club in clubs]

    def queryset(self, request, queryset):
        if self.value():
            try:
                club = Club.objects.get(id=self.value())
                if club.organization:
                    return queryset.filter(organization=club.organization)
            except Club.DoesNotExist:
                pass
        return queryset


@admin.register(Practitioner)
class PractitionerAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'last_name', 'first_name', 'birth_date',
        'organization_display', 'user_display', 'status'
    ]
    list_filter = [ClubFilter, OrganizationNullFilter, 'status', 'gender', 'primary_discipline']
    search_fields = ['first_name', 'last_name', 'user__username', 'user__email']
    list_per_page = 50
    raw_id_fields = ['user', 'organization', 'grade', 'primary_discipline']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['last_name', 'first_name']

    actions = [
        'assign_organization_from_club',
        'assign_to_organization',
        'show_practitioners_without_org',
    ]

    fieldsets = (
        (_('Informations personnelles'), {
            'fields': ('first_name', 'last_name', 'birth_date', 'gender', 'status', 'photo')
        }),
        (_('Compte utilisateur'), {
            'fields': ('user',),
            'classes': ('collapse',)
        }),
        (_('Organisation'), {
            'fields': ('organization',),
            'description': _('Organisation a laquelle le pratiquant est rattache.')
        }),
        (_('Disciplines et grades'), {
            'fields': ('primary_discipline', 'grade', 'grade_text'),
            'classes': ('collapse',)
        }),
        (_('Dates'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def organization_display(self, obj):
        """Affiche l'organisation avec un indicateur visuel."""
        if obj.organization:
            return format_html(
                '<span style="color: green;">{}</span>',
                obj.organization.name
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">AUCUNE</span>'
        )
    organization_display.short_description = _('Organisation')
    organization_display.admin_order_field = 'organization__name'

    def user_display(self, obj):
        """Affiche le compte utilisateur associe."""
        if obj.user:
            return obj.user.username
        return format_html('<span style="color: orange;">-</span>')
    user_display.short_description = _('Utilisateur')
    user_display.admin_order_field = 'user__username'

    @admin.action(description=_('Assigner organisation depuis le club du proprietaire'))
    def assign_organization_from_club(self, request, queryset):
        """
        Pour chaque pratiquant selectionne, tente de trouver le club
        de l'utilisateur associe et assigne son organisation.
        """
        updated = 0
        errors = []

        for practitioner in queryset.filter(organization__isnull=True):
            if practitioner.user:
                # Chercher le club dont l'utilisateur est proprietaire
                club = Club.objects.filter(owner=practitioner.user).first()
                if club:
                    if club.organization:
                        practitioner.organization = club.organization
                        practitioner.save(update_fields=['organization'])
                        updated += 1
                    else:
                        # Le club n'a pas d'organisation - en creer une
                        from apps.competitions.views.club.import_export import get_organization_from_club
                        org = get_organization_from_club(club)
                        if org:
                            practitioner.organization = org
                            practitioner.save(update_fields=['organization'])
                            updated += 1
                        else:
                            errors.append(f'{practitioner}: Club "{club.name}" sans organisation')
                else:
                    errors.append(f'{practitioner}: Pas de club trouve')
            else:
                errors.append(f'{practitioner}: Pas d\'utilisateur associe')

        if updated:
            self.message_user(
                request,
                _('%(count)d pratiquant(s) mis a jour.') % {'count': updated},
                messages.SUCCESS
            )

        if errors:
            self.message_user(
                request,
                _('%(count)d erreur(s): %(errors)s') % {
                    'count': len(errors),
                    'errors': '; '.join(errors[:5])
                },
                messages.WARNING
            )

    @admin.action(description=_('Assigner a une organisation specifique'))
    def assign_to_organization(self, request, queryset):
        """
        Cette action necessite une page intermediaire pour choisir l'organisation.
        Pour l'instant, elle liste les organisations disponibles.
        """
        # Compter les pratiquants sans organisation
        count = queryset.filter(organization__isnull=True).count()

        # Lister les organisations disponibles
        orgs = Organization.objects.filter(is_active=True).values_list('id', 'name')[:10]
        org_list = ', '.join([f'ID {id}: {name}' for id, name in orgs])

        self.message_user(
            request,
            _('%(count)d pratiquant(s) sans organisation. '
              'Utilisez la commande: python manage.py fix_practitioners_organization --fix --org-id=ID. '
              'Organisations: %(orgs)s') % {'count': count, 'orgs': org_list},
            messages.INFO
        )

    @admin.action(description=_('Afficher le diagnostic'))
    def show_practitioners_without_org(self, request, queryset):
        """Affiche un diagnostic des pratiquants sans organisation."""
        total = Practitioner.objects.count()
        without_org = Practitioner.objects.filter(organization__isnull=True).count()

        self.message_user(
            request,
            _('Statistiques: %(without)d pratiquants sans organisation sur %(total)d total (%(pct).1f%%). '
              'Utilisez le filtre "Sans organisation" pour les voir.') % {
                'without': without_org,
                'total': total,
                'pct': (without_org / total * 100) if total > 0 else 0
            },
            messages.INFO
        )

    def get_queryset(self, request):
        """Optimise les requetes avec select_related."""
        return super().get_queryset(request).select_related(
            'user', 'organization', 'primary_discipline', 'grade'
        )

    def changelist_view(self, request, extra_context=None):
        """Ajoute des statistiques au changelist."""
        extra_context = extra_context or {}

        # Compter les pratiquants sans organisation
        without_org = Practitioner.objects.filter(organization__isnull=True).count()
        if without_org > 0:
            extra_context['without_org_count'] = without_org

        return super().changelist_view(request, extra_context=extra_context)
