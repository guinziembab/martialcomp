#!/usr/bin/env python
import os
import re
import csv
from pathlib import Path

def scan_views_files():
    """Scanne les fichiers de vues pour trouver les filtres non sécurisés"""
    results = []
    
    # Obtenir le chemin du projet
    project_root = Path(__file__).parent
    
    # Trouver tous les fichiers Python
    python_files = project_root.glob("**/*.py")
    
    # Motifs à rechercher
    patterns = {
        'objects_all': r'\.objects\.all\(\)',
        'filter_without_org': r'\.objects\.filter\([^)]*\)',
        'get_queryset_unsafe': r'def get_queryset\([^)]*\):\s*[^\n]*\s*return\s+[^\.]*\.objects'
    }
    
    for py_file in python_files:
        # Ignorer les migrations, tests et fichiers générés
        if any(part in str(py_file) for part in [
            'migrations', '__pycache__', 'tests', 'settings'
        ]):
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Vérifier si c'est probablement un fichier de vues
                is_view_file = (
                    'class' in content and 
                    ('View' in content or 'APIView' in content or 'ViewSet' in content) or
                    'def ' in content and 'request' in content
                )
                
                if not is_view_file:
                    continue
                
                line_number = 1
                for line in content.split('\n'):
                    for pattern_name, pattern in patterns.items():
                        matches = re.search(pattern, line)
                        if matches:
                            # Vérifier si la ligne contient déjà un filtre organisationnel
                            has_org_filter = (
                                'organization=' in line or 
                                'club=' in line or
                                'federation=' in line or
                                'tenant=' in line or
                                'for_organization' in line or
                                'for_user' in line
                            )
                            
                            if not has_org_filter:
                                # On a trouvé une ligne potentiellement non sécurisée
                                results.append({
                                    'file': str(py_file.relative_to(project_root)),
                                    'line': line_number,
                                    'code': line.strip(),
                                    'pattern': pattern_name,
                                    'risk_level': 'Critique' if 'objects.all()' in line else 'Élevé'
                                })
                    
                    line_number += 1
        except Exception as e:
            print(f"Erreur lors de l'analyse de {py_file}: {e}")
    
    return results

def save_results(results):
    """Sauvegarde les résultats dans un fichier CSV"""
    with open('views_isolation_audit.csv', 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['file', 'line', 'code', 'pattern', 'risk_level']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        writer.writeheader()
        for result in results:
            writer.writerow(result)
            
    print(f"Résultats sauvegardés dans views_isolation_audit.csv")
    
    # Afficher un résumé
    total = len(results)
    critical = sum(1 for r in results if r['risk_level'] == 'Critique')
    high = sum(1 for r in results if r['risk_level'] == 'Élevé')
    
    print(f"\nRésumé de l'audit des vues:")
    print(f"Problèmes potentiels trouvés: {total}")
    print(f"Risque critique: {critical}")
    print(f"Risque élevé: {high}")
    
    # Afficher les 10 premiers problèmes critiques
    if critical > 0:
        print("\nExemples de problèmes critiques:")
        for result in results:
            if result['risk_level'] == 'Critique':
                print(f"- {result['file']}:{result['line']} - {result['code']}")
                if len(result['code']) > 80:
                    print(f"  {result['code'][:80]}...")
                else:
                    print(f"  {result['code']}")
                
                # Afficher au maximum 10 exemples
                critical -= 1
                if critical == 0:
                    break

if __name__ == "__main__":
    print("Démarrage de l'audit d'isolation organisationnelle des vues...")
    results = scan_views_files()
    save_results(results)