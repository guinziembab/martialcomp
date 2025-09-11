#!/usr/bin/env python3
"""
Script d'audit d'isolation des données dans les vues Django
Vérifie que toutes les vues respectent le principe d'isolation organisationnelle
"""

import os
import sys
import django
import re
from pathlib import Path
from collections import defaultdict

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

class IsolationAuditor:
    """Auditeur d'isolation des données dans les vues"""
    
    def __init__(self):
        self.report = {
            'views_analyzed': 0,
            'views_with_isolation': 0,
            'views_without_isolation': 0,
            'critical_issues': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Patterns à rechercher
        self.isolation_patterns = [
            r'\.filter\(.*organization.*\)',
            r'\.filter\(.*club.*\)',
            r'\.filter\(.*federation.*\)',
            r'for_organization\(',
            r'is_accessible_by\(',
            r'check_access\(',
        ]
        
        self.dangerous_patterns = [
            r'\.objects\.all\(\)',
            r'\.objects\.filter\(\)',
            r'Model\.objects\.all\(\)',
            r'Model\.objects\.filter\(\)',
        ]
        
        self.organization_models = [
            'Organization',
            'Club', 
            'Federation',
            'Competition',
            'Participant',
            'Judge',
            'Coach',
            'Member',
        ]
    
    def scan_views_directory(self, directory='.'):
        """Scanne un répertoire pour trouver les vues Django"""
        views_files = []
        
        for root, dirs, files in os.walk(directory):
            # Ignorer les répertoires non pertinents
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['venv', 'env', 'node_modules', '__pycache__']]
            
            for file in files:
                if file.endswith('.py') and any(pattern in file.lower() for pattern in ['view', 'api']):
                    views_files.append(os.path.join(root, file))
        
        return views_files
    
    def analyze_file(self, file_path):
        """Analyse un fichier pour détecter les problèmes d'isolation"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.report['views_analyzed'] += 1
            
            # Détecter les vues Django
            view_classes = self.extract_view_classes(content)
            
            issues = []
            has_isolation = False
            
            for view_class in view_classes:
                view_issues = self.analyze_view_class(view_class, file_path)
                issues.extend(view_issues)
                
                if any(pattern in view_class for pattern in self.isolation_patterns):
                    has_isolation = True
            
            # Vérifier les patterns dangereux
            dangerous_queries = self.find_dangerous_queries(content, file_path)
            issues.extend(dangerous_queries)
            
            if has_isolation:
                self.report['views_with_isolation'] += 1
            else:
                self.report['views_without_isolation'] += 1
                if issues:
                    self.report['critical_issues'].append({
                        'file': file_path,
                        'issues': issues
                    })
                else:
                    self.report['warnings'].append({
                        'file': file_path,
                        'message': 'Aucune isolation détectée'
                    })
            
            return issues
            
        except Exception as e:
            print(f"Erreur lors de l'analyse de {file_path}: {e}")
            return []
    
    def extract_view_classes(self, content):
        """Extrait les classes de vues Django du contenu"""
        view_patterns = [
            r'class\s+\w+View\w*\s*\([^)]*\):',
            r'class\s+\w+APIView\w*\s*\([^)]*\):',
            r'class\s+\w+ViewSet\w*\s*\([^)]*\):',
        ]
        
        view_classes = []
        for pattern in view_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                # Extraire le contexte autour de la classe
                start = max(0, match.start() - 200)
                end = min(len(content), match.end() + 500)
                view_classes.append(content[start:end])
        
        return view_classes
    
    def analyze_view_class(self, view_content, file_path):
        """Analyse une classe de vue spécifique"""
        issues = []
        
        # Vérifier les méthodes de requête
        query_methods = ['get_queryset', 'list', 'retrieve', 'create', 'update', 'destroy']
        
        for method in query_methods:
            method_pattern = rf'def\s+{method}\s*\([^)]*\):'
            if re.search(method_pattern, view_content):
                # Vérifier si la méthode a une isolation
                if not any(pattern in view_content for pattern in self.isolation_patterns):
                    issues.append(f"Méthode {method} sans isolation détectée")
        
        # Vérifier les querysets directs
        for model in self.organization_models:
            pattern = rf'{model}\.objects\.all\(\)'
            if re.search(pattern, view_content):
                issues.append(f"Queryset {model}.objects.all() sans filtrage détecté")
        
        return issues
    
    def find_dangerous_queries(self, content, file_path):
        """Trouve les requêtes dangereuses sans isolation"""
        issues = []
        
        for pattern in self.dangerous_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                # Vérifier le contexte
                start = max(0, match.start() - 100)
                end = min(len(content), match.end() + 100)
                context = content[start:end]
                
                # Ignorer si c'est dans un commentaire ou une docstring
                if not self.is_in_comment_or_docstring(content, match.start()):
                    # Vérifier si c'est dans un contexte d'organisation
                    if any(org_model in context for org_model in self.organization_models):
                        issues.append(f"Requête dangereuse: {match.group()} dans {file_path}")
        
        return issues
    
    def is_in_comment_or_docstring(self, content, position):
        """Vérifie si une position est dans un commentaire ou docstring"""
        # Vérifier les commentaires #
        line_start = content.rfind('\n', 0, position) + 1
        line_content = content[line_start:position]
        if '#' in line_content:
            return True
        
        # Vérifier les docstrings
        docstring_patterns = [
            r'"""[\s\S]*?"""',
            r"'''[\s\S]*?'''",
        ]
        
        for pattern in docstring_patterns:
            for match in re.finditer(pattern, content):
                if match.start() <= position <= match.end():
                    return True
        
        return False
    
    def generate_recommendations(self):
        """Génère des recommandations basées sur l'analyse"""
        total_views = self.report['views_analyzed']
        isolated_views = self.report['views_with_isolation']
        non_isolated_views = self.report['views_without_isolation']
        
        isolation_rate = (isolated_views / total_views * 100) if total_views > 0 else 0
        
        self.report['recommendations'] = []
        
        if isolation_rate < 80:
            self.report['recommendations'].append({
                'priority': 'critical',
                'action': f'Améliorer l\'isolation des vues (taux actuel: {isolation_rate:.1f}%)',
                'impact': 'Sécurité des données'
            })
        
        if self.report['critical_issues']:
            self.report['recommendations'].append({
                'priority': 'critical',
                'action': f'Corriger {len(self.report["critical_issues"])} problèmes d\'isolation critiques',
                'impact': 'Sécurité et conformité'
            })
        
        if non_isolated_views > 0:
            self.report['recommendations'].append({
                'priority': 'high',
                'action': f'Ajouter l\'isolation à {non_isolated_views} vues',
                'impact': 'Protection des données'
            })
    
    def print_report(self):
        """Affiche le rapport d'analyse"""
        print("\n" + "="*70)
        print("🔍 RAPPORT D'AUDIT D'ISOLATION DES VUES")
        print("="*70)
        
        print(f"\n📊 STATISTIQUES:")
        print(f"   Vues analysées: {self.report['views_analyzed']}")
        print(f"   Vues avec isolation: {self.report['views_with_isolation']}")
        print(f"   Vues sans isolation: {self.report['views_without_isolation']}")
        
        if self.report['views_analyzed'] > 0:
            isolation_rate = (self.report['views_with_isolation'] / self.report['views_analyzed']) * 100
            print(f"   Taux d'isolation: {isolation_rate:.1f}%")
        
        if self.report['critical_issues']:
            print(f"\n🚨 PROBLÈMES CRITIQUES ({len(self.report['critical_issues'])}):")
            for issue in self.report['critical_issues']:
                print(f"   📁 {issue['file']}")
                for problem in issue['issues']:
                    print(f"      ⚠️ {problem}")
        
        if self.report['warnings']:
            print(f"\n⚠️ AVERTISSEMENTS ({len(self.report['warnings'])}):")
            for warning in self.report['warnings']:
                print(f"   📁 {warning['file']}: {warning['message']}")
        
        if self.report['recommendations']:
            print(f"\n💡 RECOMMANDATIONS ({len(self.report['recommendations'])}):")
            for rec in self.report['recommendations']:
                print(f"   [{rec['priority'].upper()}] {rec['action']}")
                print(f"      Impact: {rec['impact']}")
        
        print("\n" + "="*70)
    
    def run_audit(self, directory='.'):
        """Exécute l'audit complet"""
        print("🔍 Démarrage de l'audit d'isolation des vues...")
        
        views_files = self.scan_views_directory(directory)
        print(f"📁 {len(views_files)} fichiers de vues trouvés")
        
        for file_path in views_files:
            self.analyze_file(file_path)
        
        self.generate_recommendations()
        self.print_report()
        
        return self.report

def main():
    """Fonction principale"""
    auditor = IsolationAuditor()
    report = auditor.run_audit()
    
    # Sauvegarder le rapport
    import json
    with open('audit_isolation_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n📄 Rapport sauvegardé dans: audit_isolation_report.json")
    
    return report

if __name__ == "__main__":
    main()
