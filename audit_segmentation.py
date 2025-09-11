#!/usr/bin/env python3
"""
Script d'audit de segmentation pour la plateforme MartialComp
Analyse la segmentation utilisateur et organisationnelle
"""

import os
import sys
import django
from datetime import datetime
from collections import defaultdict, Counter

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import connection
from django.db.models import Count, Q
from apps.organizations.models import Organization, OrganizationMember, OrganizationRole
from apps.competitions.models.users import UserProfile
from apps.competitions.models.federations import Federation
from apps.competitions.models.club import Club
from apps.permissions_manager.models import Permission, Role, UserRoleAssignment

User = get_user_model()

class SegmentationAuditor:
    """Auditeur de segmentation pour MartialComp"""
    
    def __init__(self):
        self.report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {},
            'details': {},
            'issues': [],
            'recommendations': []
        }
    
    def run_full_audit(self):
        """Exécute un audit complet de la segmentation"""
        print("🔍 Démarrage de l'audit de segmentation...")
        
        self.audit_organizations()
        self.audit_users()
        self.audit_permissions()
        self.audit_data_isolation()
        self.audit_migration_status()
        self.generate_recommendations()
        
        return self.report
    
    def audit_organizations(self):
        """Audit des organisations"""
        print("📊 Audit des organisations...")
        
        # Statistiques générales
        total_orgs = Organization.objects.count()
        orgs_by_type = Organization.objects.values('organization_type').annotate(
            count=Count('id')
        )
        
        # Organisations actives
        active_orgs = Organization.objects.filter(is_active=True).count()
        
        # Hiérarchies
        orgs_with_parents = Organization.objects.filter(
            parent_affiliations__isnull=False
        ).distinct().count()
        
        orgs_with_children = Organization.objects.filter(
            child_affiliations__isnull=False
        ).distinct().count()
        
        self.report['details']['organizations'] = {
            'total': total_orgs,
            'active': active_orgs,
            'by_type': list(orgs_by_type),
            'with_parents': orgs_with_parents,
            'with_children': orgs_with_children,
            'orphaned': total_orgs - active_orgs
        }
        
        # Détection des problèmes
        if total_orgs - active_orgs > 0:
            self.report['issues'].append({
                'type': 'warning',
                'category': 'organizations',
                'message': f"{total_orgs - active_orgs} organisations inactives détectées"
            })
    
    def audit_users(self):
        """Audit des utilisateurs et rôles"""
        print("👥 Audit des utilisateurs...")
        
        # Statistiques utilisateurs
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        
        # Utilisateurs avec profils
        users_with_profiles = UserProfile.objects.count()
        users_without_profiles = total_users - users_with_profiles
        
        # Distribution des rôles
        role_distribution = UserProfile.objects.values('role').annotate(
            count=Count('id')
        )
        
        # Utilisateurs par organisation
        users_per_org = OrganizationMember.objects.values('organization__name').annotate(
            user_count=Count('user', distinct=True)
        )
        
        # Rôles organisationnels
        org_role_distribution = OrganizationMember.objects.values('role').annotate(
            count=Count('id')
        )
        
        self.report['details']['users'] = {
            'total': total_users,
            'active': active_users,
            'with_profiles': users_with_profiles,
            'without_profiles': users_without_profiles,
            'role_distribution': list(role_distribution),
            'users_per_org': list(users_per_org),
            'org_role_distribution': list(org_role_distribution)
        }
        
        # Détection des problèmes
        if users_without_profiles > 0:
            self.report['issues'].append({
                'type': 'critical',
                'category': 'users',
                'message': f"{users_without_profiles} utilisateurs sans profil détectés"
            })
    
    def audit_permissions(self):
        """Audit du système de permissions"""
        print("🔐 Audit des permissions...")
        
        # Statistiques permissions
        total_permissions = Permission.objects.count()
        total_roles = Role.objects.count()
        total_assignments = UserRoleAssignment.objects.count()
        
        # Permissions par catégorie
        permissions_by_category = Permission.objects.values('category').annotate(
            count=Count('id')
        )
        
        # Rôles par contexte
        roles_by_context = Role.objects.values('context_type').annotate(
            count=Count('id')
        )
        
        # Assignations actives
        active_assignments = UserRoleAssignment.objects.filter(is_active=True).count()
        
        # Utilisateurs avec permissions
        users_with_permissions = UserRoleAssignment.objects.values('user').distinct().count()
        
        self.report['details']['permissions'] = {
            'total_permissions': total_permissions,
            'total_roles': total_roles,
            'total_assignments': total_assignments,
            'active_assignments': active_assignments,
            'permissions_by_category': list(permissions_by_category),
            'roles_by_context': list(roles_by_context),
            'users_with_permissions': users_with_permissions
        }
        
        # Détection des problèmes
        if total_assignments - active_assignments > 0:
            self.report['issues'].append({
                'type': 'warning',
                'category': 'permissions',
                'message': f"{total_assignments - active_assignments} assignations de rôles inactives"
            })
    
    def audit_data_isolation(self):
        """Audit de l'isolation des données"""
        print("🛡️ Audit de l'isolation des données...")
        
        # Vérifier les modèles avec isolation
        isolation_issues = []
        
        # Vérifier les requêtes sans filtrage organisationnel
        with connection.cursor() as cursor:
            # Compter les modèles qui devraient avoir une isolation
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE '%organization%'
            """)
            org_related_tables = cursor.fetchone()[0]
        
        # Vérifier les utilisateurs sans organisation
        users_without_org = UserProfile.objects.filter(
            organization__isnull=True
        ).count()
        
        # Vérifier les membres d'organisation orphelins
        orphaned_members = OrganizationMember.objects.filter(
            organization__isnull=True
        ).count()
        
        self.report['details']['isolation'] = {
            'org_related_tables': org_related_tables,
            'users_without_org': users_without_org,
            'orphaned_members': orphaned_members
        }
        
        # Détection des problèmes
        if users_without_org > 0:
            isolation_issues.append(f"{users_without_org} utilisateurs sans organisation")
        
        if orphaned_members > 0:
            isolation_issues.append(f"{orphaned_members} membres d'organisation orphelins")
        
        if isolation_issues:
            self.report['issues'].append({
                'type': 'critical',
                'category': 'isolation',
                'message': f"Problèmes d'isolation détectés: {'; '.join(isolation_issues)}"
            })
    
    def audit_migration_status(self):
        """Audit du statut de migration"""
        print("🔄 Audit du statut de migration...")
        
        # Compter les anciens modèles
        old_federations = Federation.objects.count()
        old_clubs = Club.objects.count()
        
        # Compter les nouvelles organisations
        new_organizations = Organization.objects.count()
        
        # Vérifier les références mixtes
        mixed_references = 0
        
        # Utilisateurs avec références vers anciens modèles
        users_with_old_refs = UserProfile.objects.filter(
            Q(organization__isnull=False) & 
            Q(organization__old_federation_id__isnull=False) |
            Q(organization__old_club_id__isnull=False)
        ).count()
        
        self.report['details']['migration'] = {
            'old_federations': old_federations,
            'old_clubs': old_clubs,
            'new_organizations': new_organizations,
            'users_with_old_refs': users_with_old_refs,
            'migration_progress': (new_organizations / (old_federations + old_clubs + 1)) * 100
        }
        
        # Détection des problèmes
        if old_federations > 0 or old_clubs > 0:
            self.report['issues'].append({
                'type': 'critical',
                'category': 'migration',
                'message': f"Migration incomplète: {old_federations} fédérations et {old_clubs} clubs anciens encore présents"
            })
    
    def generate_recommendations(self):
        """Génère des recommandations basées sur l'audit"""
        print("💡 Génération des recommandations...")
        
        recommendations = []
        
        # Recommandations basées sur les problèmes détectés
        for issue in self.report['issues']:
            if issue['category'] == 'users' and 'sans profil' in issue['message']:
                recommendations.append({
                    'priority': 'high',
                    'category': 'users',
                    'action': 'Créer des profils pour tous les utilisateurs',
                    'impact': 'Sécurité et fonctionnalité'
                })
            
            elif issue['category'] == 'migration':
                recommendations.append({
                    'priority': 'critical',
                    'category': 'migration',
                    'action': 'Finaliser la migration vers le modèle Organization unifié',
                    'impact': 'Stabilité et maintenance'
                })
            
            elif issue['category'] == 'isolation':
                recommendations.append({
                    'priority': 'critical',
                    'category': 'isolation',
                    'action': 'Corriger les problèmes d\'isolation des données',
                    'impact': 'Sécurité et confidentialité'
                })
        
        # Recommandations générales
        if self.report['details']['permissions']['total_permissions'] > 50:
            recommendations.append({
                'priority': 'medium',
                'category': 'permissions',
                'action': 'Simplifier le système de permissions',
                'impact': 'Maintenabilité'
            })
        
        self.report['recommendations'] = recommendations
    
    def print_summary(self):
        """Affiche un résumé de l'audit"""
        print("\n" + "="*60)
        print("📋 RÉSUMÉ DE L'AUDIT DE SEGMENTATION")
        print("="*60)
        
        # Organisations
        orgs = self.report['details']['organizations']
        print(f"\n🏢 ORGANISATIONS:")
        print(f"   Total: {orgs['total']}")
        print(f"   Actives: {orgs['active']}")
        print(f"   Avec hiérarchie: {orgs['with_parents']}")
        
        # Utilisateurs
        users = self.report['details']['users']
        print(f"\n👥 UTILISATEURS:")
        print(f"   Total: {users['total']}")
        print(f"   Actifs: {users['active']}")
        print(f"   Avec profil: {users['with_profiles']}")
        
        # Permissions
        perms = self.report['details']['permissions']
        print(f"\n🔐 PERMISSIONS:")
        print(f"   Permissions: {perms['total_permissions']}")
        print(f"   Rôles: {perms['total_roles']}")
        print(f"   Assignations actives: {perms['active_assignments']}")
        
        # Migration
        migration = self.report['details']['migration']
        print(f"\n🔄 MIGRATION:")
        print(f"   Progression: {migration['migration_progress']:.1f}%")
        print(f"   Anciens modèles: {migration['old_federations'] + migration['old_clubs']}")
        
        # Problèmes
        if self.report['issues']:
            print(f"\n⚠️ PROBLÈMES DÉTECTÉS ({len(self.report['issues'])}):")
            for issue in self.report['issues']:
                print(f"   [{issue['type'].upper()}] {issue['message']}")
        
        # Recommandations
        if self.report['recommendations']:
            print(f"\n💡 RECOMMANDATIONS ({len(self.report['recommendations'])}):")
            for rec in self.report['recommendations']:
                print(f"   [{rec['priority'].upper()}] {rec['action']}")
        
        print("\n" + "="*60)

def main():
    """Fonction principale"""
    auditor = SegmentationAuditor()
    report = auditor.run_full_audit()
    auditor.print_summary()
    
    # Sauvegarder le rapport
    import json
    with open('audit_segmentation_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n📄 Rapport sauvegardé dans: audit_segmentation_report.json")
    
    return report

if __name__ == "__main__":
    main()
