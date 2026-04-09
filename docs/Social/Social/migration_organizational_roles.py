# competitions/migrations/0XXX_create_organizational_roles.py
"""
Migration pour créer les rôles organisationnels par défaut de MartialComp.
Ces rôles correspondent exactement à ceux affichés dans l'interface existante.

À renommer avec le bon numéro de migration avant d'exécuter.
"""

from django.db import migrations


def create_default_roles(apps, schema_editor):
    """
    Crée les rôles organisationnels par défaut.
    Basé sur les rôles visibles dans l'interface:
    - Propriétaire, Administrateur, Gestionnaire, Trésorier,
    - Comptable, Entraîneur, Juge, Membre
    """
    OrganizationalRole = apps.get_model('competitions', 'OrganizationalRole')
    
    # Liste des rôles à créer (ordre = niveau hiérarchique)
    roles = [
        {
            'code': 'owner',
            'name': 'Propriétaire',
            'name_en': 'Owner',
            'category': 'executive',
            'description': 'Tous les droits, peut transférer la propriété',
            'hierarchy_level': 1,
            'icon': 'fa-crown',
            'color': '#FFD700',
            'is_system': True,
            'is_active': True,
            'default_permissions': {
                'permissions': ['*'],
                'can_transfer_ownership': True,
            }
        },
        {
            'code': 'admin',
            'name': 'Administrateur',
            'name_en': 'Administrator',
            'category': 'executive',
            'description': 'Gestion complète sauf transfert propriété',
            'hierarchy_level': 2,
            'icon': 'fa-user-shield',
            'color': '#DC3545',
            'is_system': True,
            'is_active': True,
            'default_permissions': {
                'permissions': [
                    'members.view', 'members.create', 'members.edit', 'members.delete',
                    'members.export', 'members.grades', 'members.import',
                    'competitions.view', 'competitions.create', 'competitions.edit',
                    'competitions.delete', 'competitions.manage', 'competitions.register',
                    'finance.view', 'finance.create', 'finance.edit',
                    'finance.approve', 'finance.export', 'finance.reports',
                    'organization.view', 'organization.edit', 'organization.settings',
                    'roles.view', 'roles.assign',
                    'documents.view', 'documents.create', 'documents.edit', 'documents.delete',
                    'communication.view', 'communication.send', 'communication.manage',
                    'events.view', 'events.create', 'events.edit', 'events.manage',
                    'training.view', 'training.create', 'training.edit', 'training.manage',
                    'shop.view', 'shop.manage', 'shop.orders',
                    'sites.view', 'sites.manage',
                    'reports.view', 'reports.create', 'reports.export',
                ],
                'can_transfer_ownership': False,
            }
        },
        {
            'code': 'manager',
            'name': 'Gestionnaire',
            'name_en': 'Manager',
            'category': 'administrative',
            'description': 'Gestion membres et compétitions',
            'hierarchy_level': 3,
            'icon': 'fa-user-tie',
            'color': '#17A2B8',
            'is_system': True,
            'is_active': True,
            'default_permissions': {
                'permissions': [
                    'members.view', 'members.create', 'members.edit', 'members.export',
                    'competitions.view', 'competitions.create', 'competitions.edit',
                    'competitions.manage', 'competitions.register',
                    'documents.view', 'documents.create',
                    'communication.view', 'communication.send',
                    'events.view', 'events.create', 'events.edit',
                    'reports.view',
                ],
            }
        },
        {
            'code': 'treasurer',
            'name': 'Trésorier',
            'name_en': 'Treasurer',
            'category': 'financial',
            'description': 'Gestion finances et transactions',
            'hierarchy_level': 4,
            'icon': 'fa-coins',
            'color': '#28A745',
            'is_system': True,
            'is_active': True,
            'default_permissions': {
                'permissions': [
                    'members.view',
                    'finance.view', 'finance.create', 'finance.edit',
                    'finance.approve', 'finance.export', 'finance.reports',
                    'reports.view', 'reports.export',
                ],
            }
        },
        {
            'code': 'accountant',
            'name': 'Comptable',
            'name_en': 'Accountant',
            'category': 'financial',
            'description': 'Consultation et export finances',
            'hierarchy_level': 5,
            'icon': 'fa-calculator',
            'color': '#20C997',
            'is_system': True,
            'is_active': True,
            'default_permissions': {
                'permissions': [
                    'members.view',
                    'finance.view', 'finance.export', 'finance.reports',
                    'reports.view', 'reports.export',
                ],
            }
        },
        {
            'code': 'secretary',
            'name': 'Secrétaire',
            'name_en': 'Secretary',
            'category': 'administrative',
            'description': 'Gestion administrative et communication',
            'hierarchy_level': 5,
            'icon': 'fa-user-edit',
            'color': '#6610F2',
            'is_system': True,
            'is_active': True,
            'default_permissions': {
                'permissions': [
                    'members.view', 'members.create', 'members.edit', 'members.export',
                    'documents.view', 'documents.create', 'documents.edit',
                    'communication.view', 'communication.send', 'communication.manage',
                    'events.view', 'events.create',
                ],
            }
        },
        {
            'code': 'coach',
            'name': 'Entraîneur',
            'name_en': 'Coach',
            'category': 'technical',
            'description': 'Gestion cours et pratiquants',
            'hierarchy_level': 6,
            'icon': 'fa-chalkboard-teacher',
            'color': '#6F42C1',
            'is_system': True,
            'is_active': True,
            'default_permissions': {
                'permissions': [
                    'members.view', 'members.grades',
                    'competitions.view', 'competitions.register',
                    'training.view', 'training.create', 'training.edit', 'training.manage',
                    'events.view',
                ],
            }
        },
        {
            'code': 'judge',
            'name': 'Juge',
            'name_en': 'Judge',
            'category': 'technical',
            'description': 'Arbitrage compétitions',
            'hierarchy_level': 7,
            'icon': 'fa-gavel',
            'color': '#FFC107',
            'is_system': True,
            'is_active': True,
            'default_permissions': {
                'permissions': [
                    'members.view',
                    'competitions.view', 'competitions.manage',
                ],
            }
        },
        {
            'code': 'member',
            'name': 'Membre',
            'name_en': 'Member',
            'category': 'operational',
            'description': 'Accès basique au club',
            'hierarchy_level': 10,
            'icon': 'fa-user',
            'color': '#6C757D',
            'is_system': True,
            'is_active': True,
            'default_permissions': {
                'permissions': [
                    'members.view',
                    'competitions.view',
                    'events.view',
                    'training.view',
                    'shop.view',
                ],
            }
        },
    ]
    
    for role_data in roles:
        OrganizationalRole.objects.update_or_create(
            code=role_data['code'],
            defaults=role_data
        )
    
    print(f"✓ {len(roles)} rôles organisationnels créés/mis à jour")


def migrate_existing_administrators(apps, schema_editor):
    """
    Migre les ClubAdministrator existants vers ClubMember.
    """
    ClubAdministrator = apps.get_model('competitions', 'ClubAdministrator')
    ClubMember = apps.get_model('competitions', 'ClubMember')
    OrganizationalRole = apps.get_model('competitions', 'OrganizationalRole')
    
    # Mapping des anciens rôles vers les nouveaux
    role_mapping = {
        'owner': 'owner',
        'admin': 'admin',
        'coach': 'coach',
        'secretary': 'secretary',
    }
    
    migrated = 0
    for admin in ClubAdministrator.objects.all():
        # Trouver le nouveau rôle correspondant
        new_role_code = role_mapping.get(admin.role, 'member')
        try:
            new_role = OrganizationalRole.objects.get(code=new_role_code)
        except OrganizationalRole.DoesNotExist:
            print(f"⚠ Rôle {new_role_code} non trouvé, utilisation de 'member'")
            new_role = OrganizationalRole.objects.get(code='member')
        
        # Créer ou mettre à jour le ClubMember
        member, created = ClubMember.objects.update_or_create(
            user=admin.user,
            club=admin.club,
            defaults={
                'role': new_role,
                'status': 'active',
                'role_assigned_at': admin.created_at,
            }
        )
        
        if created:
            migrated += 1
    
    print(f"✓ {migrated} administrateurs migrés vers ClubMember")


def reverse_migration(apps, schema_editor):
    """Supprime les rôles système (réversible)."""
    OrganizationalRole = apps.get_model('competitions', 'OrganizationalRole')
    deleted, _ = OrganizationalRole.objects.filter(is_system=True).delete()
    print(f"✓ {deleted} rôles système supprimés")


class Migration(migrations.Migration):
    """
    Migration pour créer le système de rôles organisationnels.
    
    IMPORTANT: Avant d'exécuter cette migration:
    1. Renommer ce fichier avec le bon numéro (ex: 0045_create_organizational_roles.py)
    2. Mettre à jour la dépendance ci-dessous
    3. S'assurer que OrganizationalRole et ClubMember existent
    """
    
    dependencies = [
        # MODIFIER ICI: mettre la dernière migration de competitions
        ('competitions', '0001_initial'),  # À MODIFIER
    ]

    operations = [
        migrations.RunPython(
            create_default_roles,
            reverse_migration
        ),
        migrations.RunPython(
            migrate_existing_administrators,
            migrations.RunPython.noop  # Pas de reverse pour la migration des données
        ),
    ]
