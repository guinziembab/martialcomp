#!/usr/bin/env python3
"""
Script pour finaliser la migration vers le modele Organization unifie
Migre les donnees des modeles legacy Federation et Club vers Organization
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
from django.core.management import call_command

User = get_user_model()

class OrganizationMigrationFinalizer:
    """Finaliseur de migration vers le modele Organization unifie"""
    
    def __init__(self):
        self.migration_stats = {
            'federations_migrated': 0,
            'clubs_migrated': 0,
            'users_updated': 0,
            'errors': 0
        }
        self.errors = []
    
    def check_migration_status(self):
        """Verifie l'etat actuel de la migration"""
        print("Verification de l'etat de la migration...")
        
        try:
            # Verifier les modeles legacy
            from apps.competitions.models.federations import Federation
            from apps.competitions.models.club import Club
            from apps.organizations.models import Organization
            
            # Statistiques des modeles legacy
            federations_count = Federation.objects.count()
            clubs_count = Club.objects.count()
            
            # Statistiques du modele unifie
            organizations_count = Organization.objects.count()
            organizations_with_legacy_id = Organization.objects.filter(
                old_federation_id__isnull=False
            ).count() + Organization.objects.filter(
                old_club_id__isnull=False
            ).count()
            
            print(f"Statistiques de migration:")
            print(f"   Federations legacy: {federations_count}")
            print(f"   Clubs legacy: {clubs_count}")
            print(f"   Organisations unifiees: {organizations_count}")
            print(f"   Organisations avec ID legacy: {organizations_with_legacy_id}")
            
            # Verifier les utilisateurs sans organisation
            try:
                from apps.competitions.models.users import UserProfile
                users_without_org = UserProfile.objects.filter(
                    organization__isnull=True
                ).count()
                print(f"   Utilisateurs sans organisation: {users_without_org}")
            except ImportError:
                print("   Modele UserProfile non disponible")
            
            return {
                'federations': federations_count,
                'clubs': clubs_count,
                'organizations': organizations_count,
                'with_legacy_id': organizations_with_legacy_id
            }
            
        except ImportError as e:
            print(f"Erreur lors de la verification: {e}")
            self.errors.append(f"Erreur verification: {e}")
            return None
    
    def migrate_federations_to_organizations(self):
        """Migre les federations vers le modele Organization"""
        print("\nMigration des federations vers Organization...")
        
        try:
            from apps.competitions.models.federations import Federation
            from apps.organizations.models import Organization
            
            federations = Federation.objects.all()
            
            with transaction.atomic():
                for federation in federations:
                    try:
                        # Verifier si l'organisation existe deja
                        existing_org = Organization.objects.filter(
                            old_federation_id=federation.id
                        ).first()
                        
                        if existing_org:
                            print(f"   Federation {federation.name} deja migree")
                            continue
                        
                        # Creer l'organisation
                        organization = Organization.objects.create(
                            name=federation.name,
                            organization_type='national_federation',
                            description=federation.description or '',
                            address=federation.address or '',
                            phone=federation.phone or '',
                            email=federation.email or '',
                            website=federation.website or '',
                            is_active=federation.is_active,
                            old_federation_id=federation.id,
                            created_at=federation.created_at if hasattr(federation, 'created_at') else datetime.now(),
                            updated_at=federation.updated_at if hasattr(federation, 'updated_at') else datetime.now(),
                        )
                        
                        # Migrer les disciplines si disponibles
                        if hasattr(federation, 'disciplines') and federation.disciplines:
                            organization.disciplines = federation.disciplines
                            organization.save()
                        
                        self.migration_stats['federations_migrated'] += 1
                        print(f"   Migree: {federation.name} -> {organization.name}")
                        
                    except Exception as e:
                        error_msg = f"Erreur migration federation {federation.name}: {e}"
                        print(f"   {error_msg}")
                        self.errors.append(error_msg)
                        self.migration_stats['errors'] += 1
            
        except ImportError as e:
            error_msg = f"Erreur import Federation: {e}"
            print(error_msg)
            self.errors.append(error_msg)
    
    def migrate_clubs_to_organizations(self):
        """Migre les clubs vers le modele Organization"""
        print("\nMigration des clubs vers Organization...")
        
        try:
            from apps.competitions.models.club import Club
            from apps.organizations.models import Organization
            
            clubs = Club.objects.all()
            
            with transaction.atomic():
                for club in clubs:
                    try:
                        # Verifier si l'organisation existe deja
                        existing_org = Organization.objects.filter(
                            old_club_id=club.id
                        ).first()
                        
                        if existing_org:
                            print(f"   Club {club.name} deja migre")
                            continue
                        
                        # Trouver l'organisation parent (federation)
                        parent_org = None
                        if hasattr(club, 'federation') and club.federation:
                            parent_org = Organization.objects.filter(
                                old_federation_id=club.federation.id
                            ).first()
                        
                        # Creer l'organisation
                        organization = Organization.objects.create(
                            name=club.name,
                            organization_type='club',
                            description=club.description or '',
                            address=club.address or '',
                            phone=club.phone or '',
                            email=club.email or '',
                            website=club.website or '',
                            is_active=club.is_active,
                            old_club_id=club.id,
                            parent=parent_org,
                            created_at=club.created_at if hasattr(club, 'created_at') else datetime.now(),
                            updated_at=club.updated_at if hasattr(club, 'updated_at') else datetime.now(),
                        )
                        
                        # Migrer les disciplines si disponibles
                        if hasattr(club, 'disciplines') and club.disciplines:
                            organization.disciplines = club.disciplines
                            organization.save()
                        
                        self.migration_stats['clubs_migrated'] += 1
                        print(f"   Migre: {club.name} -> {organization.name}")
                        
                    except Exception as e:
                        error_msg = f"Erreur migration club {club.name}: {e}"
                        print(f"   {error_msg}")
                        self.errors.append(error_msg)
                        self.migration_stats['errors'] += 1
            
        except ImportError as e:
            error_msg = f"Erreur import Club: {e}"
            print(error_msg)
            self.errors.append(error_msg)
    
    def update_user_organization_references(self):
        """Met a jour les references d'organisation des utilisateurs"""
        print("\nMise a jour des references d'organisation des utilisateurs...")
        
        try:
            from apps.competitions.models.users import UserProfile
            from apps.organizations.models import Organization
            
            # Utilisateurs avec des references legacy
            users_with_legacy_refs = UserProfile.objects.filter(
                organization__isnull=True
            ).select_related('user')
            
            with transaction.atomic():
                for profile in users_with_legacy_refs:
                    try:
                        # Essayer de trouver l'organisation via les references legacy
                        organization = None
                        
                        # Verifier si l'utilisateur a une reference a un club
                        if hasattr(profile, 'club') and profile.club:
                            organization = Organization.objects.filter(
                                old_club_id=profile.club.id
                            ).first()
                        
                        # Si pas trouve, verifier la federation
                        if not organization and hasattr(profile, 'federation') and profile.federation:
                            organization = Organization.objects.filter(
                                old_federation_id=profile.federation.id
                            ).first()
                        
                        # Si toujours pas trouve, utiliser l'organisation par defaut
                        if not organization:
                            organization = Organization.objects.filter(
                                is_active=True
                            ).first()
                        
                        if organization:
                            profile.organization = organization
                            profile.save()
                            
                            # Creer aussi un OrganizationMember
                            from apps.organizations.models import OrganizationMember
                            OrganizationMember.objects.get_or_create(
                                user=profile.user,
                                organization=organization,
                                defaults={
                                    'role': 'member',
                                    'can_manage_members': False,
                                    'can_edit_organization': False,
                                    'can_manage_competitions': False,
                                    'can_view_finances': False,
                                    'can_manage_finances': False,
                                }
                            )
                            
                            self.migration_stats['users_updated'] += 1
                            print(f"   Utilisateur {profile.user.username} -> {organization.name}")
                        
                    except Exception as e:
                        error_msg = f"Erreur mise a jour utilisateur {profile.user.username}: {e}"
                        print(f"   {error_msg}")
                        self.errors.append(error_msg)
                        self.migration_stats['errors'] += 1
            
        except ImportError as e:
            error_msg = f"Erreur import UserProfile: {e}"
            print(error_msg)
            self.errors.append(error_msg)
    
    def create_organization_affiliations(self):
        """Cree les affiliations entre organisations"""
        print("\nCreation des affiliations entre organisations...")
        
        try:
            from apps.organizations.models import Organization, OrganizationAffiliation
            
            # Trouver toutes les organisations
            organizations = Organization.objects.all()
            
            with transaction.atomic():
                for org in organizations:
                    try:
                        # Si l'organisation a un parent, creer l'affiliation
                        if org.parent:
                            affiliation, created = OrganizationAffiliation.objects.get_or_create(
                                parent_organization=org.parent,
                                child_organization=org,
                                defaults={
                                    'affiliation_type': 'hierarchical',
                                    'is_active': True,
                                }
                            )
                            
                            if created:
                                print(f"   Affiliation creee: {org.parent.name} -> {org.name}")
                        
                    except Exception as e:
                        error_msg = f"Erreur creation affiliation pour {org.name}: {e}"
                        print(f"   {error_msg}")
                        self.errors.append(error_msg)
            
        except ImportError as e:
            error_msg = f"Erreur import OrganizationAffiliation: {e}"
            print(error_msg)
            self.errors.append(error_msg)
    
    def cleanup_legacy_references(self):
        """Nettoie les references legacy apres migration complete"""
        print("\nNettoyage des references legacy...")
        
        try:
            # Verifier que toutes les migrations sont completes
            status = self.check_migration_status()
            
            if status and status['federations'] == 0 and status['clubs'] == 0:
                print("   Toutes les donnees legacy ont ete migrees")
                
                # Optionnel: Supprimer les anciens champs des modeles
                # Cette etape doit etre faite avec precaution
                print("   Les champs legacy peuvent maintenant etre supprimes des modeles")
                print("   (Operation manuelle recommandee pour la securite)")
                
            else:
                print("   Des donnees legacy subsistent encore")
                print("   Nettoyage reporte jusqu'a migration complete")
            
        except Exception as e:
            error_msg = f"Erreur lors du nettoyage: {e}"
            print(error_msg)
            self.errors.append(error_msg)
    
    def generate_migration_report(self):
        """Genere un rapport de migration"""
        print("\nGeneration du rapport de migration...")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'migration_stats': self.migration_stats,
            'errors': self.errors,
            'recommendations': []
        }
        
        # Ajouter des recommandations
        if self.migration_stats['errors'] > 0:
            report['recommendations'].append({
                'priority': 'high',
                'action': 'Verifier et corriger les erreurs de migration',
                'details': f"{self.migration_stats['errors']} erreurs rencontrees"
            })
        
        if self.migration_stats['federations_migrated'] > 0 or self.migration_stats['clubs_migrated'] > 0:
            report['recommendations'].append({
                'priority': 'medium',
                'action': 'Tester les fonctionnalites avec les nouvelles organisations',
                'details': 'Verifier que toutes les fonctionnalites marchent avec le modele unifie'
            })
        
        # Sauvegarder le rapport
        import json
        with open('migration_organization_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"   Rapport sauvegarde: migration_organization_report.json")
        return report
    
    def run_migration(self):
        """Execute la migration complete"""
        print("Finalisation de la migration vers le modele Organization unifie...")
        
        # 1. Verifier l'etat actuel
        status = self.check_migration_status()
        if not status:
            print("Impossible de verifier l'etat de la migration")
            return False
        
        # 2. Migrer les federations
        if status['federations'] > 0:
            self.migrate_federations_to_organizations()
        else:
            print("Aucune federation a migrer")
        
        # 3. Migrer les clubs
        if status['clubs'] > 0:
            self.migrate_clubs_to_organizations()
        else:
            print("Aucun club a migrer")
        
        # 4. Mettre a jour les references utilisateur
        self.update_user_organization_references()
        
        # 5. Creer les affiliations
        self.create_organization_affiliations()
        
        # 6. Nettoyer les references legacy
        self.cleanup_legacy_references()
        
        # 7. Generer le rapport
        report = self.generate_migration_report()
        
        # Rapport final
        print(f"\nMigration terminee:")
        print(f"   Federations migrees: {self.migration_stats['federations_migrated']}")
        print(f"   Clubs migres: {self.migration_stats['clubs_migrated']}")
        print(f"   Utilisateurs mis a jour: {self.migration_stats['users_updated']}")
        print(f"   Erreurs: {self.migration_stats['errors']}")
        
        if self.errors:
            print(f"\nErreurs rencontrees:")
            for error in self.errors:
                print(f"   - {error}")
        
        return self.migration_stats['errors'] == 0

def main():
    """Fonction principale"""
    finalizer = OrganizationMigrationFinalizer()
    success = finalizer.run_migration()
    
    if success:
        print("\nMigration reussie!")
        return 0
    else:
        print("\nDes erreurs ont ete rencontrees lors de la migration.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
