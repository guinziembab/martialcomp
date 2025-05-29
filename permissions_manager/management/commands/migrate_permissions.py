# permissions_manager/management/commands/migrate_permissions.py

from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from permissions_manager.models import Permission, Role, UserRoleAssignment
from competitions.models import Federation, Club
from competitions.models.administrators import FederationAdministrator, ClubAdministrator

class Command(BaseCommand):
    help = 'Migre les données des administrateurs existants vers le nouveau système de rôles'

    def create_default_permissions(self):
        """Crée les permissions par défaut"""
        # Club permissions
        club_permissions = [
            ('club.view', 'Voir les détails du club', 'Club'),
            ('club.edit', 'Modifier les informations du club', 'Club'),
            ('club.delete', 'Supprimer le club', 'Club'),
            ('club.manage_members', 'Gérer les membres du club', 'Club'),
            ('club.manage_practitioners', 'Gérer les pratiquants du club', 'Club'),
            ('club.assign_roles', 'Attribuer des rôles dans le club', 'Club'),
            ('club.manage_competitions', 'Gérer les compétitions du club', 'Club'),
            ('club.register_competition', 'Inscrire le club à des compétitions', 'Club'),
            ('club.manage_grades', 'Gérer les grades des membres', 'Club'),
        ]
        
        # Federation permissions
        federation_permissions = [
            ('federation.view', 'Voir les détails de la fédération', 'Federation'),
            ('federation.edit', 'Modifier les informations de la fédération', 'Federation'),
            ('federation.delete', 'Supprimer la fédération', 'Federation'),
            ('federation.manage_clubs', 'Gérer les clubs affiliés', 'Federation'),
            ('federation.manage_members', 'Gérer les membres de la fédération', 'Federation'),
            ('federation.assign_roles', 'Attribuer des rôles dans la fédération', 'Federation'),
            ('federation.create_competition', 'Créer des compétitions', 'Federation'),
            ('federation.manage_competitions', 'Gérer les compétitions', 'Federation'),
            ('federation.assign_judges', 'Assigner des juges aux compétitions', 'Federation'),
            ('federation.manage_grades', 'Gérer le système de grades', 'Federation'),
        ]
        
        # Judge permissions
        judge_permissions = [
            ('judge.view_assignments', 'Voir ses assignations', 'Judge'),
            ('judge.score_performance', 'Noter les performances', 'Judge'),
            ('judge.validate_grades', 'Valider des passages de grades', 'Judge'),
            ('judge.edit_profile', 'Modifier son profil de juge', 'Judge'),
            ('judge.view_results', 'Voir les résultats des compétitions', 'Judge'),
        ]
        
        # Coach permissions
        coach_permissions = [
            ('coach.manage_students', 'Gérer ses élèves', 'Coach'),
            ('coach.register_competition', 'Inscrire des élèves aux compétitions', 'Coach'),
            ('coach.view_results', 'Voir les résultats de ses élèves', 'Coach'),
            ('coach.recommend_grade', 'Recommander des passages de grades', 'Coach'),
            ('coach.edit_profile', 'Modifier son profil de coach', 'Coach'),
        ]
        
        # Participant permissions
        participant_permissions = [
            ('participant.register_competition', "S'inscrire à des compétitions", 'Participant'),
            ('participant.view_results', 'Voir ses résultats', 'Participant'),
            ('participant.edit_profile', 'Modifier son profil', 'Participant'),
        ]
        
        # Permission management permissions
        permission_permissions = [
            ('permission.view_role', 'Voir les rôles', 'Permission'),
            ('permission.add_role', 'Ajouter des rôles', 'Permission'),
            ('permission.change_role', 'Modifier des rôles', 'Permission'),
            ('permission.delete_role', 'Supprimer des rôles', 'Permission'),
            ('permission.view_userroleassignment', 'Voir les attributions de rôles', 'Permission'),
            ('permission.add_userroleassignment', 'Attribuer des rôles', 'Permission'),
            ('permission.change_userroleassignment', 'Modifier des attributions de rôles', 'Permission'),
            ('permission.delete_userroleassignment', 'Supprimer des attributions de rôles', 'Permission'),
        ]
        
        all_permissions = (
            club_permissions + 
            federation_permissions + 
            judge_permissions + 
            coach_permissions + 
            participant_permissions +
            permission_permissions
        )
        
        created_count = 0
        for code, name, category in all_permissions:
            permission, created = Permission.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'category': category
                }
            )
            if created:
                created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} permissions'))
    
    def create_default_roles(self):
        """Crée les rôles par défaut avec leurs permissions"""
        # Club roles
        club_roles = [
            {
                'name': 'Propriétaire de club',
                'description': 'Accès complet à la gestion du club',
                'context_type': 'club',
                'is_system_role': True,
                'permissions': [
                    'club.view', 'club.edit', 'club.delete',
                    'club.manage_members', 'club.manage_practitioners',
                    'club.assign_roles', 'club.manage_competitions',
                    'club.register_competition', 'club.manage_grades'
                ]
            },
            {
                'name': 'Administrateur de club',
                'description': 'Gestion du club sans droit de suppression',
                'context_type': 'club',
                'is_system_role': True,
                'permissions': [
                    'club.view', 'club.edit',
                    'club.manage_members', 'club.manage_practitioners',
                    'club.assign_roles', 'club.manage_competitions',
                    'club.register_competition', 'club.manage_grades'
                ]
            },
            {
                'name': 'Coach de club',
                'description': 'Gestion des pratiquants et inscriptions',
                'context_type': 'club',
                'is_system_role': True,
                'permissions': [
                    'club.view', 'coach.manage_students',
                    'coach.register_competition', 'coach.view_results',
                    'coach.recommend_grade', 'coach.edit_profile',
                    'club.manage_practitioners'
                ]
            }
        ]
        
        # Federation roles
        federation_roles = [
            {
                'name': 'Président de fédération',
                'description': 'Accès complet à la gestion de la fédération',
                'context_type': 'federation',
                'is_system_role': True,
                'permissions': [
                    'federation.view', 'federation.edit', 'federation.delete',
                    'federation.manage_clubs', 'federation.manage_members',
                    'federation.assign_roles', 'federation.create_competition',
                    'federation.manage_competitions', 'federation.assign_judges',
                    'federation.manage_grades'
                ]
            },
            {
                'name': 'Administrateur de fédération',
                'description': 'Gestion de la fédération sans droit de suppression',
                'context_type': 'federation',
                'is_system_role': True,
                'permissions': [
                    'federation.view', 'federation.edit',
                    'federation.manage_clubs', 'federation.manage_members',
                    'federation.assign_roles', 'federation.create_competition',
                    'federation.manage_competitions', 'federation.assign_judges',
                    'federation.manage_grades'
                ]
            }
        ]
        
        all_roles = club_roles + federation_roles
        
        created_count = 0
        for role_data in all_roles:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                context_type=role_data['context_type'],
                defaults={
                    'description': role_data['description'],
                    'is_system_role': role_data['is_system_role']
                }
            )
            
            # Assigner les permissions
            if created or not role.permissions.exists():
                permission_codes = role_data['permissions']
                permissions = Permission.objects.filter(code__in=permission_codes)
                role.permissions.set(permissions)
                created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} roles'))
    
    def migrate_federation_administrators(self):
        """Migre les administrateurs de fédérations vers le nouveau système"""
        federation_content_type = ContentType.objects.get_for_model(Federation)
        president_role = Role.objects.get(name='Président de fédération')
        admin_role = Role.objects.get(name='Administrateur de fédération')
        
        migrated_count = 0
        
        for fed_admin in FederationAdministrator.objects.all():
            # Déterminer le rôle en fonction du flag is_primary
            role = president_role if fed_admin.is_primary else admin_role
            
            # Créer l'affectation de rôle
            assignment, created = UserRoleAssignment.objects.get_or_create(
                user=fed_admin.user,
                role=role,
                content_type=federation_content_type,
                object_id=fed_admin.federation.id,
                defaults={
                    'start_date': timezone.now().date(),
                    'is_active': True
                }
            )
            
            if created:
                migrated_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Migrated {migrated_count} federation administrators'))
    
    def migrate_club_administrators(self):
        """Migre les administrateurs de clubs vers le nouveau système"""
        club_content_type = ContentType.objects.get_for_model(Club)
        owner_role = Role.objects.get(name='Propriétaire de club')
        admin_role = Role.objects.get(name='Administrateur de club')
        coach_role = Role.objects.get(name='Coach de club')
        
        migrated_count = 0
        
        for club_admin in ClubAdministrator.objects.all():
            # Déterminer le rôle en fonction du rôle dans l'ancien système
            if club_admin.role == 'owner':
                role = owner_role
            elif club_admin.role == 'admin':
                role = admin_role
            elif club_admin.role == 'coach':
                role = coach_role
            else:
                # Rôle administratif par défaut
                role = admin_role
            
            # Créer l'affectation de rôle
            assignment, created = UserRoleAssignment.objects.get_or_create(
                user=club_admin.user,
                role=role,
                content_type=club_content_type,
                object_id=club_admin.club.id,
                defaults={
                    'start_date': timezone.now().date(),
                    'is_active': True,
                    'is_primary': club_admin.is_primary
                }
            )
            
            if created:
                migrated_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Migrated {migrated_count} club administrators'))
    
    def handle(self, *args, **options):
        with transaction.atomic():
            self.stdout.write('Starting permission system migration...')
            
            # Créer les permissions par défaut
            self.create_default_permissions()
            
            # Créer les rôles par défaut
            self.create_default_roles()
            
            # Migrer les administrateurs de fédérations
            self.migrate_federation_administrators()
            
            # Migrer les administrateurs de clubs
            self.migrate_club_administrators()
            
            self.stdout.write(self.style.SUCCESS('Migration completed successfully!'))