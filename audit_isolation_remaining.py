#!/usr/bin/env python3
"""
Script d'audit des vues restantes sans isolation
Identifie les prochaines priorités pour l'implémentation de l'isolation
"""

import os
import re
import json
from pathlib import Path

def audit_remaining_views():
    """Audite les vues restantes sans isolation"""
    
    print("🔍 AUDIT DES VUES RESTANTES SANS ISOLATION")
    print("=" * 60)
    
    # Fichiers déjà corrigés
    corrected_files = [
        "apps/documents/api_views.py",
        "apps/task_management/api.py",
        "apps/competitions/api.py"
    ]
    
    # Fichiers prioritaires à examiner
    priority_files = [
        "apps/competitions/views/api.py",
        "apps/competitions/views/grades_api.py", 
        "apps/competitions/views/register_view.py",
        "apps/accounts/views.py",
        "apps/family_management/views.py",
        "apps/finances/api.py",
        "apps/finances/rest_api.py",
        "apps/grades/api.py",
        "apps/grades/views/api.py",
        "apps/organizations/views/api.py",
        "apps/payment/views.py",
        "apps/permissions_manager/views.py",
        "apps/shop/api.py"
    ]
    
    results = {
        "corrected_files": [],
        "priority_files_analysis": [],
        "other_files_to_check": [],
        "recommendations": []
    }
    
    # Analyser les fichiers prioritaires
    print("\n📋 ANALYSE DES FICHIERS PRIORITAIRES")
    print("-" * 40)
    
    for file_path in priority_files:
        if os.path.exists(file_path):
            analysis = analyze_file_isolation(file_path)
            results["priority_files_analysis"].append(analysis)
            
            if analysis["has_isolation"]:
                print(f"✅ {file_path} - Isolation présente")
            else:
                print(f"❌ {file_path} - Isolation manquante ({analysis['view_count']} vues)")
        else:
            print(f"⚠️  {file_path} - Fichier non trouvé")
    
    # Chercher d'autres fichiers avec des vues
    print("\n🔍 RECHERCHE D'AUTRES FICHIERS AVEC DES VUES")
    print("-" * 40)
    
    apps_dir = Path("apps")
    if apps_dir.exists():
        for app_dir in apps_dir.iterdir():
            if app_dir.is_dir() and not app_dir.name.startswith('.'):
                for py_file in app_dir.rglob("*.py"):
                    if py_file.name in ["views.py", "api.py", "api_views.py"]:
                        file_path = str(py_file)
                        if file_path not in corrected_files and file_path not in priority_files:
                            analysis = analyze_file_isolation(file_path)
                            if analysis["view_count"] > 0:
                                results["other_files_to_check"].append(analysis)
                                print(f"📁 {file_path} - {analysis['view_count']} vues détectées")
    
    # Générer les recommandations
    print("\n💡 RECOMMANDATIONS")
    print("-" * 40)
    
    # Compter les vues sans isolation
    total_views_without_isolation = sum(
        analysis["view_count"] for analysis in results["priority_files_analysis"]
        if not analysis["has_isolation"]
    )
    
    print(f"📊 Total des vues sans isolation dans les fichiers prioritaires : {total_views_without_isolation}")
    
    # Recommandations par priorité
    high_priority = []
    medium_priority = []
    low_priority = []
    
    for analysis in results["priority_files_analysis"]:
        if not analysis["has_isolation"]:
            if analysis["file_path"].startswith(("apps/competitions", "apps/accounts", "apps/finances")):
                high_priority.append(analysis)
            elif analysis["file_path"].startswith(("apps/grades", "apps/organizations")):
                medium_priority.append(analysis)
            else:
                low_priority.append(analysis)
    
    print(f"\n🚨 PRIORITÉ HAUTE ({len(high_priority)} fichiers)")
    for analysis in high_priority:
        print(f"   - {analysis['file_path']} ({analysis['view_count']} vues)")
    
    print(f"\n⚠️  PRIORITÉ MOYENNE ({len(medium_priority)} fichiers)")
    for analysis in medium_priority:
        print(f"   - {analysis['file_path']} ({analysis['view_count']} vues)")
    
    print(f"\nℹ️  PRIORITÉ BASSE ({len(low_priority)} fichiers)")
    for analysis in low_priority:
        print(f"   - {analysis['file_path']} ({analysis['view_count']} vues)")
    
    # Sauvegarder les résultats
    results["summary"] = {
        "total_priority_files": len(priority_files),
        "total_views_without_isolation": total_views_without_isolation,
        "high_priority_count": len(high_priority),
        "medium_priority_count": len(medium_priority),
        "low_priority_count": len(low_priority)
    }
    
    with open("audit_isolation_remaining_report.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Rapport détaillé sauvegardé dans : audit_isolation_remaining_report.json")
    
    return results

def analyze_file_isolation(file_path):
    """Analyse l'isolation d'un fichier"""
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return {
            "file_path": file_path,
            "error": str(e),
            "has_isolation": False,
            "view_count": 0
        }
    
    # Compter les vues
    view_patterns = [
        r'class\s+\w+ViewSet\s*\(',
        r'class\s+\w+View\s*\(',
        r'class\s+\w+APIView\s*\(',
        r'def\s+\w+\(.*request.*\):',
    ]
    
    view_count = 0
    for pattern in view_patterns:
        matches = re.findall(pattern, content)
        view_count += len(matches)
    
    # Vérifier la présence d'isolation
    isolation_patterns = [
        r'OrganizationIsolationMixin',
        r'get_organization_queryset',
        r'filter_by_organization',
        r'require_organization_access'
    ]
    
    has_isolation = any(
        re.search(pattern, content) 
        for pattern in isolation_patterns
    )
    
    return {
        "file_path": file_path,
        "has_isolation": has_isolation,
        "view_count": view_count,
        "isolation_methods": [
            pattern for pattern in isolation_patterns 
            if re.search(pattern, content)
        ]
    }

if __name__ == "__main__":
    results = audit_remaining_views()
    
    print("\n" + "=" * 60)
    print("🎯 PROCHAINES ACTIONS RECOMMANDÉES")
    print("=" * 60)
    
    print("1. Commencer par les fichiers de PRIORITÉ HAUTE")
    print("2. Implémenter l'isolation sur les vues de compétitions")
    print("3. Sécuriser les vues de gestion des utilisateurs")
    print("4. Protéger les vues financières")
    print("5. Créer des tests automatisés pour valider l'isolation")
    
    print(f"\n📊 Résumé : {results['summary']['total_views_without_isolation']} vues à sécuriser")
    print("🚀 Prêt pour la Phase 2 du plan d'action !")
