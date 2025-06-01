#!/usr/bin/env python
import os
import django
import re
import csv

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.apps import apps
from django.db import models
from django.db.models.fields.related import ForeignKey, ManyToManyField

def is_organization_related(model):
    """Vérifie si un modèle a une relation avec une organisation"""
    for field in model._meta.get_fields():
        # Vérifier les champs ForeignKey directs
        if isinstance(field, ForeignKey) and field.name in [
            'organization', 'federation', 'club', 'tenant',
            'organizing_organization', 'organizer', 'owner_organization'
        ]:
            return True
            
        # Vérifier les relations inverses
        if field.is_relation and not field.auto_created:
            related_name = field.name
            if related_name in ['organization', 'federation', 'club']:
                return True
    
    return False

def analyze_models():
    """Analyse tous les modèles de l'application pour l'isolation organisationnelle"""
    results = []
    
    # Ne pas inclure les modèles système ou d'autorisation
    excluded_apps = ['auth', 'contenttypes', 'sessions', 'admin', 'django']
    
    for model in apps.get_models():
        app_label = model._meta.app_label
        
        # Ignorer les modèles des applications système
        if app_label in excluded_apps:
            continue
            
        # Vérifier si c'est un modèle abstrait
        if model._meta.abstract:
            continue
        
        # Analyser le modèle
        has_org_relation = is_organization_related(model)
        
        # Déterminer si le modèle devrait avoir une relation organisationnelle
        # (heuristique basique - à affiner)
        needs_org_relation = not (
            model._meta.model_name.lower().startswith('abstract') or
            'reference' in model._meta.model_name.lower() or
            model._meta.model_name.lower() in ['user', 'group', 'permission']
        )
        
        # Créer une entrée pour les résultats
        results.append({
            'app': app_label,
            'model': model._meta.model_name,
            'has_org_relation': has_org_relation,
            'needs_org_relation': needs_org_relation,
            'risk_level': 'Critique' if needs_org_relation and not has_org_relation else 'OK'
        })
    
    return results

def save_results(results):
    """Sauvegarde les résultats dans un fichier CSV"""
    with open('model_isolation_audit.csv', 'w', newline='') as f:
        fieldnames = ['app', 'model', 'has_org_relation', 'needs_org_relation', 'risk_level']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        writer.writeheader()
        for result in results:
            writer.writerow(result)
            
    print(f"Résultats sauvegardés dans model_isolation_audit.csv")
    
    # Afficher un résumé
    total = len(results)
    missing_isolation = sum(1 for r in results if r['risk_level'] == 'Critique')
    
    print(f"\nRésumé de l'audit:")
    print(f"Modèles analysés: {total}")
    print(f"Modèles sans isolation organisationnelle: {missing_isolation} ({missing_isolation/total*100:.1f}%)")
    print("Modèles critiques sans isolation:")
    
    for result in results:
        if result['risk_level'] == 'Critique':
            print(f"- {result['app']}.{result['model']}")

if __name__ == "__main__":
    print("Démarrage de l'audit d'isolation organisationnelle des modèles...")
    results = analyze_models()
    save_results(results)