#!/usr/bin/env python
"""
Script pour auditer l'isolation organisationnelle dans le code.
Ce script détecte les violations potentielles du principe d'isolation.

Utilisation:
    python security/scripts/audit_isolation.py [--fix] [--report=path/to/report.md]

Options:
    --fix       Tente de corriger automatiquement certaines violations
    --report    Génère un rapport dans le fichier spécifié
"""

import os
import re
import sys
import ast
import argparse
from datetime import datetime
from pathlib import Path

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
IGNORE_DIRS = [
    "migrations", "__pycache__", "venv", "env", "static", "media", 
    "node_modules", ".git", ".idea", ".vscode"
]
MODELS_DIR = "competitions/models"
VIEWS_DIR = "competitions/views"
URLS_DIR = "competitions/urls"
UTILS_DIR = "competitions/utils"

# Motifs Ã  rechercher
PATTERNS = {
    "objects_all": r"\.objects\.all\(\)",
    "filter_without_org": r"\.objects\.filter\([^)]*\)",
    "get_without_org": r"\.objects\.get\([^)]*\)",
    "exclude_without_org": r"\.objects\.exclude\([^)]*\)",
}

# Modèles qui devraient hériter de OrganizationScopedModel
MODELS_REQUIRING_ISOLATION = [
    "Club", "Federation", "Competition", "Category", "Practitioner",
    "Judge", "CompetitionResult", "Registration", "Training"
]

# Statistiques
stats = {
    "files_scanned": 0,
    "files_with_violations": 0,
    "total_violations": 0,
    "violations_by_type": {},
    "models_missing_isolation": [],
    "views_missing_decorator": [],
}

def should_ignore(path):
    """Vérifie si un chemin doit Ãªtre ignoré."""
    for ignore_dir in IGNORE_DIRS:
        if f"/{ignore_dir}/" in str(path) or str(path).endswith(f"/{ignore_dir}"):
            return True
    return False

def scan_python_file(file_path, fix=False):
    """Analyse un fichier Python pour détecter les violations d'isolation."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    violations = []
    
    # Rechercher les motifs suspects
    for pattern_name, pattern in PATTERNS.items():
        matches = re.finditer(pattern, content)
        for match in matches:
            line_start = content[:match.start()].count('\n') + 1
            line_end = content[:match.end()].count('\n') + 1
            context_before = content.split('\n')[max(0, line_start-3):line_start]
            context_after = content.split('\n')[line_end:min(len(content.split('\n')), line_end+3)]
            
            # Vérifier si l'organisation est mentionnée
            match_text = match.group(0)
            if pattern_name != "objects_all" and ("organization" in match_text or 
                                                 "club" in match_text or 
                                                 "federation" in match_text or
                                                 "for_user" in match_text or
                                                 "for_organization" in match_text):
                continue
            
            violations.append({
                "type": pattern_name,
                "line": line_start,
                "text": match.group(0),
                "context_before": '\n'.join(context_before),
                "context_after": '\n'.join(context_after),
                "fix_suggestion": get_fix_suggestion(pattern_name, match.group(0))
            })
    
    return violations

def scan_model_file(file_path):
    """Analyse un fichier de modèle pour vérifier l'héritage d'OrganizationScopedModel."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return {"error": "Erreur de syntaxe lors de l'analyse du fichier"}
    
    models_missing_isolation = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            class_name = node.name
            if class_name in MODELS_REQUIRING_ISOLATION:
                has_organization_scoped = False
                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id == "OrganizationScopedModel":
                        has_organization_scoped = True
                        break
                    elif isinstance(base, ast.Attribute) and base.attr == "OrganizationScopedModel":
                        has_organization_scoped = True
                        break
                
                if not has_organization_scoped:
                    models_missing_isolation.append({
                        "class_name": class_name,
                        "file": file_path,
                        "line": node.lineno,
                    })
    
    return models_missing_isolation

def scan_view_file(file_path):
    """Analyse un fichier de vue pour vérifier l'utilisation des décorateurs d'isolation."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return {"error": "Erreur de syntaxe lors de l'analyse du fichier"}
    
    views_missing_decorator = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Vérifier si la fonction a le paramètre request
            has_request_param = any(arg.arg == 'request' for arg in node.args.args)
            if has_request_param:
                # Vérifier si la fonction a un des décorateurs d'isolation
                has_isolation_decorator = False
                for decorator in node.decorator_list:
                    decorator_name = None
                    if isinstance(decorator, ast.Name):
                        decorator_name = decorator.id
                    elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
                        decorator_name = decorator.func.id
                    elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                        decorator_name = decorator.func.attr
                    
                    if decorator_name in ["require_organization_access", "organization_isolated_view", 
                                         "mark_view_as_organization_isolated"]:
                        has_isolation_decorator = True
                        break
                
                if not has_isolation_decorator:
                    # Vérifier si la fonction utilise filter_queryset_for_user
                    uses_filter_function = "filter_queryset_for_user" in content
                    
                    # Si la fonction n'a pas de décorateur d'isolation et n'utilise pas filter_queryset_for_user
                    if not uses_filter_function:
                        views_missing_decorator.append({
                            "function_name": node.name,
                            "file": file_path,
                            "line": node.lineno,
                        })
    
    return views_missing_decorator

def get_fix_suggestion(pattern_name, match_text):
    """Génère une suggestion pour corriger une violation."""
    if pattern_name == "objects_all":
        return match_text.replace(".all()", ".filter(organization=request.user.organization)")
    elif pattern_name == "filter_without_org":
        # Ajouter organization=request.user.organization aux filtres
        if "(" in match_text and ")" in match_text:
            params = match_text[match_text.find("(")+1:match_text.rfind(")")]
            if params.strip():
                return match_text.replace(params, params + ", organization=request.user.organization")
            else:
                return match_text.replace("()", "(organization=request.user.organization)")
        return match_text
    return None

def generate_report(results, output_file=None):
    """Génère un rapport des violations trouvées."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""# Rapport d'Audit d'Isolation Organisationnelle

Date: {now}

## Résumé

- Fichiers analysés: {stats['files_scanned']}
- Fichiers avec violations: {stats['files_with_violations']}
- Total des violations: {stats['total_violations']}

## Violations par Type

"""
    
    for vtype, count in stats['violations_by_type'].items():
        report += f"- {vtype}: {count}\n"
    
    report += f"""
## Modèles sans Isolation Organisationnelle

{len(stats['models_missing_isolation'])} modèles ne sont pas correctement isolés:

"""
    
    for model in stats['models_missing_isolation']:
        report += f"- {model['class_name']} ({os.path.relpath(model['file'], PROJECT_ROOT)}:{model['line']})\n"
    
    report += f"""
## Vues sans Décorateur d'Isolation

{len(stats['views_missing_decorator'])} vues n'utilisent pas de décorateur d'isolation:

"""
    
    for view in stats['views_missing_decorator']:
        report += f"- {view['function_name']} ({os.path.relpath(view['file'], PROJECT_ROOT)}:{view['line']})\n"
    
    report += """
## Détail des Violations

"""
    
    for file_path, violations in results.items():
        if violations:
            report += f"### {os.path.relpath(file_path, PROJECT_ROOT)}\n\n"
            for v in violations:
                report += f"- Ligne {v['line']}: {v['type']} - `{v['text']}`\n"
                if v['context_before']:
                    report += "  Contexte avant:\n"
                    report += f"  ```python\n  {v['context_before']}\n  ```\n"
                if v['context_after']:
                    report += "  Contexte après:\n"
                    report += f"  ```python\n  {v['context_after']}\n  ```\n"
                if v['fix_suggestion']:
                    report += f"  Suggestion: `{v['fix_suggestion']}`\n"
                report += "\n"
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"Rapport généré: {output_file}")
    else:
        print(report)

def main():
    parser = argparse.ArgumentParser(description="Audit d'isolation organisationnelle")
    parser.add_argument("--fix", action="store_true", help="Tente de corriger automatiquement les violations")
    parser.add_argument("--report", help="Chemin du fichier de rapport")
    args = parser.parse_args()
    
    results = {}
    
    # Analyser les fichiers Python du projet
    for root, dirs, files in os.walk(PROJECT_ROOT):
        root_path = Path(root)
        if should_ignore(root_path):
            continue
            
        for file in files:
            if file.endswith('.py'):
                file_path = root_path / file
                stats['files_scanned'] += 1
                
                # Analyse standard
                violations = scan_python_file(file_path, args.fix)
                
                # Analyse spécifique pour les modèles
                if MODELS_DIR in str(file_path):
                    models_issues = scan_model_file(file_path)
                    if isinstance(models_issues, list):
                        stats['models_missing_isolation'].extend(models_issues)
                
                # Analyse spécifique pour les vues
                if VIEWS_DIR in str(file_path) or UTILS_DIR in str(file_path):
                    views_issues = scan_view_file(file_path)
                    if isinstance(views_issues, list):
                        stats['views_missing_decorator'].extend(views_issues)
                
                # Enregistrer les violations
                if violations:
                    results[file_path] = violations
                    stats['files_with_violations'] += 1
                    stats['total_violations'] += len(violations)
                    
                    for v in violations:
                        vtype = v['type']
                        if vtype in stats['violations_by_type']:
                            stats['violations_by_type'][vtype] += 1
                        else:
                            stats['violations_by_type'][vtype] = 1
    
    # Générer le rapport
    generate_report(results, args.report)

if __name__ == "__main__":
    main()
