#!/usr/bin/env python3
"""
Script pour assigner les utilisateurs aux organisations
Corrige les utilisateurs sans organisation identifies par l'audit
"""

import os
import sys
import django
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

class UserOrganizationAssigner:
    """Assignateur d'utilisateurs aux organisations"""
    
    def __init__(self):
        self.assigned_users = []
        self.errors = []
        self.stats = {
            'total_users': 0,
            'users_without_org': 0,
            'users_assigned': 0,
            'organizations_available': 0
        }
    
    def get_statistics(self):
        """Recupere les statistiques actuelles"""
        try:
            # Statistiques utilisateurs
            total_users = User.objects.count()
            active_users = User.objects.filter(is_active=True).count()
            
            # Utilisateurs sans organisation
            try:
                from apps.competitions.models.users import UserProfile
                users_without_org = UserProfile.objects.filter(
                    organization__isnull=True
                ).count()
            except ImportError:
                users_without_org = 0
            
            # Organisations disponibles
            try:
                from apps.organizations.models import Organization
                organizations_available = Organization.objects.filter(
                    is_active=True
                ).count()
            except ImportError:
                organizations_available = 0
            
            self.stats.update({
                'total_users': total_users,
                'active_users': active_users,
                'users_without_org': users_without_org,
                'organizations_available': organizations_available
            })
            
            print(f"Statistiques actuelles:")
            print(f"   Utilisateurs totaux: {total_users}")
            print(f"   Utilisateurs actifs: {active_users}")
            print(f"   Utilisateurs sans organisation: {users_without_org}")
            print(f"   Organisations disponibles: {organizations_available}")
            
        except Exception as e:
            print(f"Erreur lors de la recuperation des statistiques: {e}")
            self.errors.append(f"Erreur statistiques: {e}")
    
    def assign_users_to_default_organization(self):
        """Assigne les utilisateurs a l'organisation par defaut"""
        try:
            from apps.organizations.models import Organization
            from apps.competitions.models.users import UserProfile
            
            # Trouver l'organisation par defaut (la premiere active)
            default_org = Organization.objects.filter(is_active=True).first()
            
            if not default_org:
                print("Aucune organisation active trouvee")
                return
            
            print(f"Organisation par defaut: {default_org.name}")
            
            # Trouver les utilisateurs sans organisation
            users_without_org = UserProfile.objects.filter(
                organization__isnull=True
            ).select_related('user')
            
            if not users_without_org.exists():
                print("Aucun utilisateur sans organisation trouve")
                return
            
            print(f"Utilisateurs a assigner: {users_without_org.count()}")
            
            # Assigner les utilisateurs
            with transaction.atomic():
                for profile in users_without_org:
                    try:
                        profile.organization = default_org
                        profile.save()
                        
                        # Creer aussi un OrganizationMember
                        from apps.organizations.models import OrganizationMember
                        member, created = OrganizationMember.objects.get_or_create(
                            user=profile.user,
                            organization=default_org,
                            defaults={
                                'role': 'member',
                                'can_manage_members': False,
                                'can_edit_organization': False,
                                'can_manage_competitions': False,
                            }
                        )
                        
                        self.assigned_users.append({
                            'user': profile.user.username,
                            'organization': default_org.name,
                            'member_created': created
                        })
                        
                        print(f"   Assigne: {profile.user.username} -> {default_org.name}")
                        
                    except Exception as e:
                        error_msg = f"Erreur assignation {profile.user.username}: {e}"
                        print(f"   {error_msg}")
                        self.errors.append(error_msg)
            
            self.stats['users_assigned'] = len(self.assigned_users)
            
        except Exception as e:
            error_msg = f"Erreur lors de l'assignation: {e}"
            print(error_msg)
            self.errors.append(error_msg)
    
    def assign_users_to_multiple_organizations(self):
        """Assigne les utilisateurs a differentes organisations de maniere equilibree"""
        try:
            from apps.organizations.models import Organization
            from apps.competitions.models.users import UserProfile
            
            # Trouver toutes les organisations actives
            organizations = list(Organization.objects.filter(is_active=True))
            
            if not organizations:
                print("Aucune organisation active trouvee")
                return
            
            print(f"Organisations disponibles: {len(organizations)}")
            
            # Trouver les utilisateurs sans organisation
            users_without_org = UserProfile.objects.filter(
                organization__isnull=True
            ).select_related('user')
            
            if not users_without_org.exists():
                print("Aucun utilisateur sans organisation trouve")
                return
            
            print(f"Utilisateurs a assigner: {users_without_org.count()}")
            
            # Assigner les utilisateurs de maniere equilibree
            with transaction.atomic():
                for i, profile in enumerate(users_without_org):
                    try:
                        # Selectionner l'organisation de maniere cyclique
                        org = organizations[i % len(organizations)]
                        
                        profile.organization = org
                        profile.save()
                        
                        # Creer aussi un OrganizationMember
                        from apps.organizations.models import OrganizationMember
                        member, created = OrganizationMember.objects.get_or_create(
                            user=profile.user,
                            organization=org,
                            defaults={
                                'role': 'member',
                                'can_manage_members': False,
                                'can_edit_organization': False,
                                'can_manage_competitions': False,
                            }
                        )
                        
                        self.assigned_users.append({
                            'user': profile.user.username,
                            'organization': org.name,
                            'member_created': created
                        })
                        
                        print(f"   Assigne: {profile.user.username} -> {org.name}")
                        
                    except Exception as e:
                        error_msg = f"Erreur assignation {profile.user.username}: {e}"
                        print(f"   {error_msg}")
                        self.errors.append(error_msg)
            
            self.stats['users_assigned'] = len(self.assigned_users)
            
        except Exception as e:
            error_msg = f"Erreur lors de l'assignation multiple: {e}"
            print(error_msg)
            self.errors.append(error_msg)
    
    def create_missing_user_profiles(self):
        """Cree les profils utilisateur manquants"""
        try:
            from apps.competitions.models.users import UserProfile
            
            # Trouver les utilisateurs sans profil
            users_without_profile = []
            for user in User.objects.filter(is_active=True):
                try:
                    UserProfile.objects.get(user=user)
                except UserProfile.DoesNotExist:
                    users_without_profile.append(user)
            
            if not users_without_profile:
                print("Tous les utilisateurs ont deja un profil")
                return
            
            print(f"Utilisateurs sans profil: {len(users_without_profile)}")
            
            # Trouver l'organisation par defaut
            try:
                from apps.organizations.models import Organization
                default_org = Organization.objects.filter(is_active=True).first()
            except ImportError:
                default_org = None
            
            # Creer les profils manquants
            with transaction.atomic():
                for user in users_without_profile:
                    try:
                        profile = UserProfile.objects.create(
                            user=user,
                            organization=default_org,
                            role='participant'  # Role par defaut
                        )
                        
                        print(f"   Profil cree: {user.username}")
                        
                        # Si une organisation par defaut existe, creer aussi un OrganizationMember
                        if default_org:
                            try:
                                from apps.organizations.models import OrganizationMember
                                OrganizationMember.objects.get_or_create(
                                    user=user,
                                    organization=default_org,
                                    defaults={
                                        'role': 'member',
                                        'can_manage_members': False,
                                        'can_edit_organization': False,
                                        'can_manage_competitions': False,
                                    }
                                )
                            except ImportError:
                                pass
                        
                    except Exception as e:
                        error_msg = f"Erreur creation profil {user.username}: {e}"
                        print(f"   {error_msg}")
                        self.errors.append(error_msg)
            
        except Exception as e:
            error_msg = f"Erreur lors de la creation des profils: {e}"
            print(error_msg)
            self.errors.append(error_msg)
    
    def run_assignment(self, strategy='default'):
        """Execute l'assignation selon la strategie choisie"""
        print("Assignation des utilisateurs aux organisations...")
        print(f"Strategie: {strategy}")
        
        # Recuperer les statistiques
        self.get_statistics()
        
        # Creer les profils manquants
        print("\n1. Creation des profils utilisateur manquants...")
        self.create_missing_user_profiles()
        
        # Assigner les utilisateurs
        print("\n2. Assignation des utilisateurs aux organisations...")
        if strategy == 'multiple':
            self.assign_users_to_multiple_organizations()
        else:
            self.assign_users_to_default_organization()
        
        # Rapport final
        print(f"\nAssignation terminee:")
        print(f"   Utilisateurs assignes: {self.stats['users_assigned']}")
        print(f"   Erreurs: {len(self.errors)}")
        
        if self.assigned_users:
            print(f"\nUtilisateurs assignes:")
            for assignment in self.assigned_users:
                print(f"   {assignment['user']} -> {assignment['organization']}")
        
        if self.errors:
            print(f"\nErreurs rencontrees:")
            for error in self.errors:
                print(f"   - {error}")
        
        return self.stats['users_assigned'], len(self.errors)

def main():
    """Fonction principale"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Assigner les utilisateurs aux organisations')
    parser.add_argument('--strategy', choices=['default', 'multiple'], default='default',
                       help='Strategie d\'assignation (default: une organisation, multiple: repartition equilibree)')
    
    args = parser.parse_args()
    
    assigner = UserOrganizationAssigner()
    assigned_count, error_count = assigner.run_assignment(args.strategy)
    
    if error_count == 0:
        print(f"\nAssignation reussie! {assigned_count} utilisateurs assignes.")
        return 0
    else:
        print(f"\n{error_count} erreurs rencontrees. Verifiez les logs.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
