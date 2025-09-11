#!/usr/bin/env python3
"""
Audit de l'isolation organisationnelle dans MartialComp
Analyse les modèles Django pour identifier les relations avec les entités organisationnelles
"""

import os
import sys
import re
from collections import defaultdict

# Configuration du chemin Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append('/mnt/c/martial_hub_django/martialcomp')

import django
django.setup()

from django.apps import apps
from django.db import models
from django.db.models.fields import related


class OrganizationalIsolationAudit:
    def __init__(self):
        self.organizational_entities = [
            'organization',
            'discipline', 
            'federation',
            'club'
        ]
        
        self.target_apps = [
            'competitions',
            'grades', 
            'family_management',
            'finances',
            'organizations',
            'multitenant',
            'shop',
            'documents'
        ]
        
        self.results = {
            'models_with_isolation': [],
            'models_without_isolation': [],
            'problematic_models': [],
            'organizational_relations': defaultdict(list),
            'summary': {}
        }

    def analyze_model(self, model):
        """Analyse un modèle pour identifier les relations organisationnelles"""
        model_info = {
            'app': model._meta.app_label,
            'name': model.__name__,
            'fields': [],
            'has_organization_relation': False,
            'has_discipline_relation': False,
            'has_federation_relation': False,
            'has_club_relation': False,
            'many_to_many_relations': [],
            'foreign_key_relations': [],
            'isolation_status': 'NONE'
        }

        # Analyser tous les champs du modèle
        for field in model._meta.get_fields():
            field_info = self.analyze_field(field)
            if field_info:
                model_info['fields'].append(field_info)
                
                # Marquer les relations organisationnelles
                if 'organization' in field_info['name'].lower():
                    model_info['has_organization_relation'] = True
                if 'discipline' in field_info['name'].lower():
                    model_info['has_discipline_relation'] = True
                if 'federation' in field_info['name'].lower():
                    model_info['has_federation_relation'] = True
                if 'club' in field_info['name'].lower():
                    model_info['has_club_relation'] = True
                
                # Collecter les relations par type
                if field_info['type'] == 'ManyToManyField':
                    model_info['many_to_many_relations'].append(field_info)
                elif field_info['type'] == 'ForeignKey':
                    model_info['foreign_key_relations'].append(field_info)

        # Déterminer le statut d'isolation
        model_info['isolation_status'] = self.determine_isolation_status(model_info)
        
        return model_info

    def analyze_field(self, field):
        """Analyse un champ pour identifier les relations organisationnelles"""
        if not isinstance(field, (related.ForeignKey, related.ManyToManyField, related.OneToOneField)):
            return None
            
        field_info = {
            'name': field.name,
            'type': field.__class__.__name__,
            'related_model': None,
            'is_organizational': False
        }
        
        # Obtenir le modèle lié
        try:
            if hasattr(field, 'related_model') and field.related_model:
                field_info['related_model'] = f"{field.related_model._meta.app_label}.{field.related_model.__name__}"
            elif hasattr(field, 'target_field'):
                field_info['related_model'] = f"{field.target_field.model._meta.app_label}.{field.target_field.model.__name__}"
        except:
            field_info['related_model'] = 'Unknown'

        # Vérifier si c'est une relation organisationnelle
        for entity in self.organizational_entities:
            if (entity in field.name.lower() or 
                (field_info['related_model'] and entity in field_info['related_model'].lower())):
                field_info['is_organizational'] = True
                break
                
        return field_info

    def determine_isolation_status(self, model_info):
        """Détermine le statut d'isolation d'un modèle"""
        has_any_org_relation = (
            model_info['has_organization_relation'] or
            model_info['has_discipline_relation'] or
            model_info['has_federation_relation'] or
            model_info['has_club_relation']
        )
        
        # Si le modèle a une relation directe avec Organization
        if model_info['has_organization_relation']:
            return 'GOOD_ISOLATION'
        
        # Si le modèle a des relations avec d'anciennes entités mais pas avec Organization
        elif has_any_org_relation:
            return 'LEGACY_ISOLATION'
        
        # Si le modèle devrait avoir une isolation mais n'en a pas
        elif self.should_have_isolation(model_info):
            return 'MISSING_ISOLATION'
        
        # Modèles qui n'ont pas besoin d'isolation organisationnelle
        else:
            return 'NO_ISOLATION_NEEDED'

    def should_have_isolation(self, model_info):
        """Détermine si un modèle devrait avoir une isolation organisationnelle"""
        model_name = model_info['name'].lower()
        app_name = model_info['app'].lower()
        
        # Modèles qui devraient généralement avoir une isolation
        should_isolate_patterns = [
            'practitioner', 'competition', 'event', 'training', 'grade', 'exam',
            'registration', 'payment', 'invoice', 'transaction', 'certificate',
            'document', 'product', 'order', 'cart', 'family', 'member'
        ]
        
        # Modèles système qui n'ont pas besoin d'isolation
        system_patterns = [
            'user', 'permission', 'contenttype', 'session', 'migration',
            'logentry', 'tenant', 'domain', 'subscriptiontier'
        ]
        
        # Vérifier les modèles système d'abord
        for pattern in system_patterns:
            if pattern in model_name:
                return False
        
        # Vérifier si le modèle devrait être isolé
        for pattern in should_isolate_patterns:
            if pattern in model_name:
                return True
                
        # Si c'est dans certaines applications, il devrait probablement être isolé
        if app_name in ['competitions', 'finances', 'family_management', 'shop', 'documents']:
            # Sauf s'il s'agit de modèles de configuration
            config_patterns = ['category', 'type', 'template', 'config', 'setting']
            for pattern in config_patterns:
                if pattern in model_name:
                    return False
            return True
            
        return False

    def run_audit(self):
        """Exécute l'audit complet"""
        print("=== AUDIT DE L'ISOLATION ORGANISATIONNELLE ===\n")
        
        for app_name in self.target_apps:
            try:
                app = apps.get_app_config(app_name)
                print(f"Analyse de l'application: {app_name}")
                
                for model in app.get_models():
                    model_info = self.analyze_model(model)
                    
                    # Classer les modèles selon leur statut
                    if model_info['isolation_status'] == 'GOOD_ISOLATION':
                        self.results['models_with_isolation'].append(model_info)
                    elif model_info['isolation_status'] == 'MISSING_ISOLATION':
                        self.results['models_without_isolation'].append(model_info)
                    elif model_info['isolation_status'] == 'LEGACY_ISOLATION':
                        self.results['problematic_models'].append(model_info)
                    
                    # Enregistrer les relations organisationnelles
                    for field in model_info['fields']:
                        if field['is_organizational']:
                            self.results['organizational_relations'][f"{app_name}.{model_info['name']}"].append(field)
                            
            except Exception as e:
                print(f"Erreur lors de l'analyse de {app_name}: {e}")
        
        self.generate_report()

    def generate_report(self):
        """Génère le rapport d'audit"""
        print("\n" + "="*80)
        print("RAPPORT D'AUDIT DE L'ISOLATION ORGANISATIONNELLE")
        print("="*80)
        
        # Résumé général
        total_models = (len(self.results['models_with_isolation']) + 
                       len(self.results['models_without_isolation']) + 
                       len(self.results['problematic_models']))
        
        print(f"\n📊 RÉSUMÉ GÉNÉRAL:")
        print(f"   Total de modèles analysés: {total_models}")
        print(f"   ✅ Modèles avec bonne isolation: {len(self.results['models_with_isolation'])}")
        print(f"   ⚠️  Modèles avec isolation héritée: {len(self.results['problematic_models'])}")
        print(f"   ❌ Modèles sans isolation requis: {len(self.results['models_without_isolation'])}")
        
        # Détail des modèles avec bonne isolation
        print(f"\n✅ MODÈLES AVEC BONNE ISOLATION ({len(self.results['models_with_isolation'])}):")
        print("-" * 50)
        for model in self.results['models_with_isolation']:
            org_fields = [f for f in model['fields'] if 'organization' in f['name'].lower()]
            org_field_names = [f['name'] for f in org_fields]
            print(f"   {model['app']}.{model['name']} → {', '.join(org_field_names)}")
        
        # Détail des modèles avec isolation héritée/problématique
        print(f"\n⚠️  MODÈLES AVEC ISOLATION HÉRITÉE ({len(self.results['problematic_models'])}):")
        print("-" * 50)
        for model in self.results['problematic_models']:
            relations = []
            if model['has_federation_relation']:
                relations.append('federation')
            if model['has_club_relation']:
                relations.append('club')
            if model['has_discipline_relation']:
                relations.append('discipline')
            print(f"   {model['app']}.{model['name']} → {', '.join(relations)} (LEGACY)")
        
        # Détail des modèles sans isolation
        print(f"\n❌ MODÈLES SANS ISOLATION REQUIS ({len(self.results['models_without_isolation'])}):")
        print("-" * 50)
        for model in self.results['models_without_isolation']:
            print(f"   {model['app']}.{model['name']} → AUCUNE ISOLATION")
        
        # Relations ManyToMany organisationnelles
        print(f"\n🔗 RELATIONS MANY-TO-MANY ORGANISATIONNELLES:")
        print("-" * 50)
        for model_name, fields in self.results['organizational_relations'].items():
            m2m_fields = [f for f in fields if f['type'] == 'ManyToManyField']
            if m2m_fields:
                for field in m2m_fields:
                    print(f"   {model_name}.{field['name']} → {field['related_model']}")
        
        # Recommandations
        print(f"\n💡 RECOMMANDATIONS:")
        print("-" * 50)
        
        if self.results['models_without_isolation']:
            print("1. URGENT - Ajouter l'isolation organisationnelle:")
            for model in self.results['models_without_isolation']:
                print(f"   - {model['app']}.{model['name']}: Ajouter un champ 'organization'")
        
        if self.results['problematic_models']:
            print("\n2. MIGRATION - Migrer vers le nouveau système d'organisation:")
            for model in self.results['problematic_models']:
                print(f"   - {model['app']}.{model['name']}: Migrer les relations héritées vers 'organization'")
        
        print("\n3. VÉRIFICATIONS - Relations ManyToMany:")
        m2m_count = sum(1 for fields in self.results['organizational_relations'].values() 
                       for f in fields if f['type'] == 'ManyToManyField')
        if m2m_count > 0:
            print(f"   - Vérifier {m2m_count} relations ManyToMany pour l'isolation correcte")
        
        # Scores d'isolation par application
        print(f"\n📈 SCORES D'ISOLATION PAR APPLICATION:")
        print("-" * 50)
        app_scores = defaultdict(lambda: {'good': 0, 'legacy': 0, 'missing': 0, 'total': 0})
        
        for model in self.results['models_with_isolation']:
            app_scores[model['app']]['good'] += 1
            app_scores[model['app']]['total'] += 1
            
        for model in self.results['problematic_models']:
            app_scores[model['app']]['legacy'] += 1
            app_scores[model['app']]['total'] += 1
            
        for model in self.results['models_without_isolation']:
            app_scores[model['app']]['missing'] += 1
            app_scores[model['app']]['total'] += 1
        
        for app, scores in app_scores.items():
            if scores['total'] > 0:
                good_pct = (scores['good'] / scores['total']) * 100
                status = "🟢" if good_pct >= 80 else "🟡" if good_pct >= 50 else "🔴"
                print(f"   {status} {app}: {good_pct:.1f}% ({scores['good']}/{scores['total']} modèles)")


if __name__ == "__main__":
    audit = OrganizationalIsolationAudit()
    audit.run_audit()