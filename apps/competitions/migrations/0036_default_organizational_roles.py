# Data migration to create default organizational roles
# Social Auth and Organizational Roles implementation

from django.db import migrations


DEFAULT_ROLES = [
    {
        'code': 'owner',
        'name': 'Propriétaire',
        'description': 'Propriétaire du club/organisation - Tous les droits',
        'hierarchy_level': 0,
        'permissions': [
            'members.view', 'members.add', 'members.edit', 'members.delete', 'members.export',
            'finance.view', 'finance.add', 'finance.edit', 'finance.delete', 'finance.approve', 'finance.export',
            'events.view', 'events.add', 'events.edit', 'events.delete', 'events.manage',
            'competitions.view', 'competitions.add', 'competitions.edit', 'competitions.delete', 'competitions.manage',
            'communications.view', 'communications.send', 'communications.manage',
            'documents.view', 'documents.add', 'documents.edit', 'documents.delete',
            'settings.view', 'settings.edit',
            'roles.view', 'roles.assign', 'roles.manage',
            'reports.view', 'reports.export',
            'grades.view', 'grades.assign', 'grades.manage',
            'schedule.view', 'schedule.edit', 'schedule.manage',
            'admin.access',
        ],
    },
    {
        'code': 'admin',
        'name': 'Administrateur',
        'description': 'Administrateur du club - Droits étendus sauf suppression',
        'hierarchy_level': 1,
        'permissions': [
            'members.view', 'members.add', 'members.edit', 'members.export',
            'finance.view', 'finance.add', 'finance.edit', 'finance.approve', 'finance.export',
            'events.view', 'events.add', 'events.edit', 'events.manage',
            'competitions.view', 'competitions.add', 'competitions.edit', 'competitions.manage',
            'communications.view', 'communications.send', 'communications.manage',
            'documents.view', 'documents.add', 'documents.edit',
            'settings.view', 'settings.edit',
            'roles.view', 'roles.assign',
            'reports.view', 'reports.export',
            'grades.view', 'grades.assign', 'grades.manage',
            'schedule.view', 'schedule.edit', 'schedule.manage',
            'admin.access',
        ],
    },
    {
        'code': 'manager',
        'name': 'Gestionnaire',
        'description': 'Responsable de la gestion quotidienne',
        'hierarchy_level': 2,
        'permissions': [
            'members.view', 'members.add', 'members.edit',
            'finance.view',
            'events.view', 'events.add', 'events.edit',
            'competitions.view', 'competitions.add', 'competitions.edit',
            'communications.view', 'communications.send',
            'documents.view', 'documents.add',
            'reports.view',
            'grades.view',
            'schedule.view', 'schedule.edit',
        ],
    },
    {
        'code': 'treasurer',
        'name': 'Trésorier',
        'description': 'Responsable des finances',
        'hierarchy_level': 3,
        'permissions': [
            'members.view',
            'finance.view', 'finance.add', 'finance.edit', 'finance.approve', 'finance.export',
            'reports.view', 'reports.export',
        ],
    },
    {
        'code': 'accountant',
        'name': 'Comptable',
        'description': 'Assistant comptable',
        'hierarchy_level': 4,
        'permissions': [
            'members.view',
            'finance.view', 'finance.add', 'finance.edit',
            'reports.view',
        ],
    },
    {
        'code': 'secretary',
        'name': 'Secrétaire',
        'description': 'Secrétariat administratif',
        'hierarchy_level': 4,
        'permissions': [
            'members.view', 'members.add', 'members.edit',
            'events.view', 'events.add',
            'communications.view', 'communications.send',
            'documents.view', 'documents.add', 'documents.edit',
            'schedule.view', 'schedule.edit',
        ],
    },
    {
        'code': 'coach',
        'name': 'Coach/Entraîneur',
        'description': 'Responsable technique des entraînements',
        'hierarchy_level': 5,
        'permissions': [
            'members.view',
            'events.view',
            'competitions.view',
            'communications.view', 'communications.send',
            'grades.view', 'grades.assign',
            'schedule.view',
        ],
    },
    {
        'code': 'judge',
        'name': 'Juge/Arbitre',
        'description': 'Juge officiel pour les compétitions',
        'hierarchy_level': 6,
        'permissions': [
            'members.view',
            'competitions.view',
            'grades.view',
        ],
    },
    {
        'code': 'member',
        'name': 'Membre',
        'description': 'Membre standard du club',
        'hierarchy_level': 10,
        'permissions': [
            'members.view',
            'events.view',
            'competitions.view',
            'communications.view',
            'grades.view',
            'schedule.view',
        ],
    },
]


def create_default_roles(apps, schema_editor):
    OrganizationalRole = apps.get_model('competitions', 'OrganizationalRole')

    for role_data in DEFAULT_ROLES:
        OrganizationalRole.objects.get_or_create(
            code=role_data['code'],
            defaults={
                'name': role_data['name'],
                'description': role_data['description'],
                'hierarchy_level': role_data['hierarchy_level'],
                'permissions': role_data['permissions'],
                'is_active': True,
            }
        )


def remove_default_roles(apps, schema_editor):
    OrganizationalRole = apps.get_model('competitions', 'OrganizationalRole')
    codes = [role['code'] for role in DEFAULT_ROLES]
    OrganizationalRole.objects.filter(code__in=codes).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0035_organizational_roles'),
    ]

    operations = [
        migrations.RunPython(create_default_roles, remove_default_roles),
    ]
