#!/usr/bin/env python3
"""
Script d'audit de segmentation simplifié pour la plateforme MartialComp
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
        """Execute un audit complet de la segmentation"""
        print("Démarrage de l'audit de segmentation...")
        
        self.audit_organizations()
        self.audit_users()
        self.audit_data_isolation()
        self.generate_recommendations()
        
        return self.report
    
    def audit_organizations(self):
        """Audit des organisations"""
        print("Audit des organisations...")
        
        try:
            # Importer les modèles
            from apps.organizations.models import Organization, OrganizationMember
            
            # Statistiques générales
            total_orgs = Organization.objects.count()
            active_orgs = Organization.objects.filter(is_active=True).count()
            
            # Organisations par type
            orgs_by_type = Organization.objects.values('organization_type').annotate(
                count=Count('id')
            )
            
            self.report['details']['organizations'] = {
                'total': total_orgs,
                'active': active_orgs,
                'by_type': list(orgs_by_type),
                'orphaned': total_orgs - active_orgs
            }
            
            # Detection des problemes
            if total_orgs - active_orgs > 0:
                self.report['issues'].append({
                    'type': 'warning',
                    'category': 'organizations',
                    'message': f"{total_orgs - active_orgs} organisations inactives detectees"
                })
                
        except Exception as e:
            print(f"Erreur lors de l'audit des organisations: {e}")
            self.report['issues'].append({
                'type': 'error',
                'category': 'organizations',
                'message': f"Erreur d'audit: {str(e)}"
            })
    
    def audit_users(self):
        """Audit des utilisateurs et roles"""
        print("Audit des utilisateurs...")
        
        try:
            # Statistiques utilisateurs
            total_users = User.objects.count()
            active_users = User.objects.filter(is_active=True).count()
            
            # Utilisateurs avec profils
            try:
                from apps.competitions.models.users import UserProfile
                users_with_profiles = UserProfile.objects.count()
                users_without_profiles = total_users - users_with_profiles
                
                # Distribution des roles
                role_distribution = UserProfile.objects.values('role').annotate(
                    count=Count('id')
                )
                
                self.report['details']['users'] = {
                    'total': total_users,
                    'active': active_users,
                    'with_profiles': users_with_profiles,
                    'without_profiles': users_without_profiles,
                    'role_distribution': list(role_distribution)
                }
                
                # Detection des problemes
                if users_without_profiles > 0:
                    self.report['issues'].append({
                        'type': 'critical',
                        'category': 'users',
                        'message': f"{users_without_profiles} utilisateurs sans profil detectes"
                    })
                    
            except ImportError:
                print("Modele UserProfile non trouve")
                self.report['details']['users'] = {
                    'total': total_users,
                    'active': active_users,
                    'with_profiles': 0,
                    'without_profiles': total_users,
                    'role_distribution': []
                }
                
        except Exception as e:
            print(f"Erreur lors de l'audit des utilisateurs: {e}")
            self.report['issues'].append({
                'type': 'error',
                'category': 'users',
                'message': f"Erreur d'audit: {str(e)}"
            })
    
    def audit_data_isolation(self):
        """Audit de l'isolation des donnees"""
        print("Audit de l'isolation des donnees...")
        
        try:
            # Verifier les utilisateurs sans organisation
            try:
                from apps.competitions.models.users import UserProfile
                users_without_org = UserProfile.objects.filter(
                    organization__isnull=True
                ).count()
                
                # Verifier les membres d'organisation orphelins
                from apps.organizations.models import OrganizationMember
                orphaned_members = OrganizationMember.objects.filter(
                    organization__isnull=True
                ).count()
                
                self.report['details']['isolation'] = {
                    'users_without_org': users_without_org,
                    'orphaned_members': orphaned_members
                }
                
                # Detection des problemes
                isolation_issues = []
                if users_without_org > 0:
                    isolation_issues.append(f"{users_without_org} utilisateurs sans organisation")
                
                if orphaned_members > 0:
                    isolation_issues.append(f"{orphaned_members} membres d'organisation orphelins")
                
                if isolation_issues:
                    self.report['issues'].append({
                        'type': 'critical',
                        'category': 'isolation',
                        'message': f"Problemes d'isolation detectes: {'; '.join(isolation_issues)}"
                    })
                    
            except ImportError:
                print("Modeles d'organisation non trouves")
                self.report['details']['isolation'] = {
                    'users_without_org': 0,
                    'orphaned_members': 0
                }
                
        except Exception as e:
            print(f"Erreur lors de l'audit d'isolation: {e}")
            self.report['issues'].append({
                'type': 'error',
                'category': 'isolation',
                'message': f"Erreur d'audit: {str(e)}"
            })
    
    def generate_recommendations(self):
        """Genere des recommandations basees sur l'audit"""
        print("Generation des recommandations...")
        
        recommendations = []
        
        # Recommandations basees sur les problemes detectes
        for issue in self.report['issues']:
            if issue['category'] == 'users' and 'sans profil' in issue['message']:
                recommendations.append({
                    'priority': 'high',
                    'category': 'users',
                    'action': 'Creer des profils pour tous les utilisateurs',
                    'impact': 'Securite et fonctionnalite'
                })
            
            elif issue['category'] == 'isolation':
                recommendations.append({
                    'priority': 'critical',
                    'category': 'isolation',
                    'action': 'Corriger les problemes d\'isolation des donnees',
                    'impact': 'Securite et confidentialite'
                })
        
        # Recommandations generales
        if 'users' in self.report['details']:
            users = self.report['details']['users']
            if users.get('without_profiles', 0) > 0:
                recommendations.append({
                    'priority': 'high',
                    'category': 'users',
                    'action': 'Implementer un systeme de profils automatique',
                    'impact': 'Completude des donnees'
                })
        
        self.report['recommendations'] = recommendations
    
    def print_summary(self):
        """Affiche un resume de l'audit"""
        print("\n" + "="*60)
        print("RESUME DE L'AUDIT DE SEGMENTATION")
        print("="*60)
        
        # Organisations
        if 'organizations' in self.report['details']:
            orgs = self.report['details']['organizations']
            print(f"\nORGANISATIONS:")
            print(f"   Total: {orgs['total']}")
            print(f"   Actives: {orgs['active']}")
        
        # Utilisateurs
        if 'users' in self.report['details']:
            users = self.report['details']['users']
            print(f"\nUTILISATEURS:")
            print(f"   Total: {users['total']}")
            print(f"   Actifs: {users['active']}")
            print(f"   Avec profil: {users['with_profiles']}")
        
        # Isolation
        if 'isolation' in self.report['details']:
            iso = self.report['details']['isolation']
            print(f"\nISOLATION:")
            print(f"   Utilisateurs sans organisation: {iso['users_without_org']}")
            print(f"   Membres orphelins: {iso['orphaned_members']}")
        
        # Problemes
        if self.report['issues']:
            print(f"\nPROBLEMES DETECTES ({len(self.report['issues'])}):")
            for issue in self.report['issues']:
                print(f"   [{issue['type'].upper()}] {issue['message']}")
        
        # Recommandations
        if self.report['recommendations']:
            print(f"\nRECOMMANDATIONS ({len(self.report['recommendations'])}):")
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
    
    print(f"\nRapport sauvegarde dans: audit_segmentation_report.json")
    
    return report

if __name__ == "__main__":
    main()
