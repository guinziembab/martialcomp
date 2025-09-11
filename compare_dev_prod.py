#!/usr/bin/env python
"""
Script de Comparaison Configuration Dev vs Prod - MartialComp (Version Corrigée)
Gère les erreurs de variables d'environnement et fournit une analyse partielle.
"""

import os
import sys
import importlib
from datetime import datetime
import json

class SafeConfigComparison:
    """Analyseur de configuration sécurisé pour Dev vs Prod"""
    
    def __init__(self):
        self.report = {
            'timestamp': datetime.now().isoformat(),
            'config_status': {},
            'partial_analysis': {},
            'recommendations': [],
            'env_issues': []
        }
        
        # Paramètres analysables même sans variables d'environnement
        self.safe_settings = [
            'DEBUG',
            'LOGIN_REDIRECT_URL', 
            'LOGOUT_REDIRECT_URL',
            'ACCOUNT_LOGIN_REDIRECT_URL',
            'ACCOUNT_SIGNUP_REDIRECT_URL',
            'ACCOUNT_EMAIL_VERIFICATION',
            'ACCOUNT_EMAIL_REQUIRED',
            'ACCOUNT_USERNAME_REQUIRED',
            'MIDDLEWARE',
            'INSTALLED_APPS',
            'SESSION_COOKIE_AGE',
            'SESSION_SAVE_EVERY_REQUEST',
            'SESSION_EXPIRE_AT_BROWSER_CLOSE'
        ]
    
    def safe_load_settings(self, module_name):
        """Charge les paramètres en gérant les erreurs d'environnement"""
        print(f"📥 Tentative de chargement: {module_name}")
        
        try:
            # Sauvegarder l'état actuel de Django
            original_settings = None
            if 'django.conf' in sys.modules:
                from django.conf import settings
                if settings.configured:
                    original_settings = settings
            
            # Tenter le chargement
            module = importlib.import_module(module_name)
            
            # Extraire les paramètres disponibles
            extracted_settings = {}
            for setting in self.safe_settings:
                if hasattr(module, setting):
                    try:
                        value = getattr(module, setting)
                        extracted_settings[setting] = value
                    except Exception as e:
                        extracted_settings[setting] = f"❌ Erreur: {str(e)}"
                else:
                    extracted_settings[setting] = "⚠️ NON DÉFINI"
            
            print(f"✅ {module_name}: Chargé avec succès ({len(extracted_settings)} paramètres)")
            return {'status': 'success', 'settings': extracted_settings}
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ {module_name}: Erreur - {error_msg}")
            
            # Analyser le type d'erreur
            if 'not found' in error_msg.lower() or 'undefined' in error_msg.lower():
                missing_vars = self.extract_missing_env_vars(error_msg)
                return {
                    'status': 'env_error',
                    'error': error_msg,
                    'missing_env_vars': missing_vars,
                    'settings': {}
                }
            else:
                return {
                    'status': 'import_error', 
                    'error': error_msg,
                    'settings': {}
                }
    
    def extract_missing_env_vars(self, error_msg):
        """Extrait les variables d'environnement manquantes du message d'erreur"""
        missing_vars = []
        
        # Patterns communs pour les variables manquantes
        common_vars = [
            'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_HOST',
            'SECRET_KEY', 'EMAIL_HOST_PASSWORD', 'DEEPL_API_KEY',
            'GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET',
            'FACEBOOK_APP_ID', 'FACEBOOK_APP_SECRET'
        ]
        
        for var in common_vars:
            if var in error_msg:
                missing_vars.append(var)
        
        return missing_vars
    
    def analyze_configurations(self):
        """Analyse comparative intelligente des configurations"""
        print("🔍 ANALYSE COMPARATIVE DEV vs PROD")
        print("="*60)
        
        # Charger les configurations
        dev_result = self.safe_load_settings('config.settings.development')
        prod_result = self.safe_load_settings('config.settings.production')
        base_result = self.safe_load_settings('config.settings.base')
        
        self.report['config_status'] = {
            'development': dev_result['status'],
            'production': prod_result['status'], 
            'base': base_result['status']
        }
        
        # Analyser selon les résultats
        if dev_result['status'] == 'success':
            dev_settings = dev_result['settings']
            
            if prod_result['status'] == 'success':
                # Comparaison complète possible
                prod_settings = prod_result['settings']
                self.full_comparison(dev_settings, prod_settings)
            else:
                # Analyse partielle basée sur dev + erreurs prod
                self.partial_analysis(dev_settings, prod_result)
        else:
            print("❌ Impossible de charger la configuration de développement")
            return
        
        return self.report
    
    def full_comparison(self, dev_settings, prod_settings):
        """Comparaison complète quand les deux configs sont chargées"""
        print(f"\n🎯 COMPARAISON COMPLÈTE POSSIBLE")
        
        differences = {}
        critical_issues = 0
        
        for setting in self.safe_settings:
            dev_val = dev_settings.get(setting, "⚠️ NON DÉFINI")
            prod_val = prod_settings.get(setting, "⚠️ NON DÉFINI")
            
            if dev_val != prod_val:
                impact = self.assess_impact(setting, dev_val, prod_val)
                differences[setting] = {
                    'dev': dev_val,
                    'prod': prod_val,
                    'impact': impact
                }
                
                if '🚨' in impact:
                    critical_issues += 1
        
        self.report['partial_analysis'] = {
            'type': 'full_comparison',
            'differences': differences,
            'critical_issues': critical_issues
        }
        
        # Afficher les résultats
        self.print_differences(differences)
    
    def partial_analysis(self, dev_settings, prod_result):
        """Analyse partielle quand prod ne peut pas être chargé"""
        print(f"\n⚠️  ANALYSE PARTIELLE - Configuration prod non accessible")
        print(f"Erreur prod: {prod_result.get('error', 'Inconnue')}")
        
        # Analyser la configuration dev pour détecter des problèmes potentiels
        analysis = {
            'type': 'partial_dev_only',
            'dev_settings': dev_settings,
            'prod_error': prod_result.get('error'),
            'missing_env_vars': prod_result.get('missing_env_vars', []),
            'potential_issues': []
        }
        
        # Analyser les paramètres de dev pour des valeurs suspectes
        critical_settings = ['LOGIN_REDIRECT_URL', 'ACCOUNT_EMAIL_VERIFICATION', 'MIDDLEWARE']
        
        for setting in critical_settings:
            if setting in dev_settings:
                value = dev_settings[setting]
                
                if setting == 'LOGIN_REDIRECT_URL':
                    if '/onboarding/' in str(value):
                        analysis['potential_issues'].append({
                            'setting': setting,
                            'issue': 'Redirection vers onboarding peut causer des boucles',
                            'recommendation': 'Vérifier si prod a la même valeur'
                        })
                
                elif setting == 'MIDDLEWARE' and isinstance(value, list):
                    if any('OnboardingRedirectMiddleware' in mw for mw in value):
                        analysis['potential_issues'].append({
                            'setting': setting,
                            'issue': 'OnboardingRedirectMiddleware présent',
                            'recommendation': 'Vérifier la logique de ce middleware'
                        })
        
        self.report['partial_analysis'] = analysis
        
        # Afficher l'analyse partielle
        self.print_partial_analysis(analysis)
    
    def assess_impact(self, setting, dev_val, prod_val):
        """Évalue l'impact d'une différence"""
        if setting == 'LOGIN_REDIRECT_URL':
            if '/onboarding/' in str(prod_val) and '/dashboard/' in str(dev_val):
                return "🚨 CRITIQUE - Risque de boucle de redirection"
            elif dev_val != prod_val:
                return "⚠️ ÉLEVÉ - Redirection différente"
        
        elif setting == 'ACCOUNT_EMAIL_VERIFICATION':
            if prod_val in ['mandatory', 'required'] and dev_val in ['optional', 'none']:
                return "⚠️ ÉLEVÉ - Peut bloquer connexions en prod"
        
        elif setting == 'MIDDLEWARE':
            if isinstance(prod_val, list) and any('OnboardingRedirectMiddleware' in mw for mw in prod_val):
                return "⚠️ ÉLEVÉ - Middleware complexe actif"
        
        elif setting == 'DEBUG':
            if dev_val == True and prod_val == False:
                return "✅ NORMAL - DEBUG désactivé en prod"
        
        return "🔵 MOYEN - Différence à vérifier"
    
    def print_differences(self, differences):
        """Affiche les différences trouvées"""
        print(f"\n📊 DIFFÉRENCES DÉTECTÉES: {len(differences)}")
        
        if not differences:
            print("✅ Aucune différence dans les paramètres comparables")
            return
        
        critical_count = sum(1 for d in differences.values() if '🚨' in d['impact'])
        print(f"├── Problèmes critiques: {critical_count}")
        print(f"└── Total des différences: {len(differences)}")
        
        for setting, diff in differences.items():
            print(f"\n🔧 {setting}")
            print(f"   Dev:    {diff['dev']}")
            print(f"   Prod:   {diff['prod']}") 
            print(f"   Impact: {diff['impact']}")
    
    def print_partial_analysis(self, analysis):
        """Affiche l'analyse partielle"""
        print(f"\n📊 ANALYSE DE LA CONFIGURATION DÉVELOPPEMENT")
        print(f"├── Variables d'env manquantes: {len(analysis.get('missing_env_vars', []))}")
        print(f"└── Problèmes potentiels détectés: {len(analysis.get('potential_issues', []))}")
        
        # Variables d'environnement manquantes
        missing_vars = analysis.get('missing_env_vars', [])
        if missing_vars:
            print(f"\n❌ VARIABLES D'ENVIRONNEMENT MANQUANTES:")
            for var in missing_vars:
                print(f"   - {var}")
        
        # Problèmes potentiels
        issues = analysis.get('potential_issues', [])
        if issues:
            print(f"\n⚠️  PROBLÈMES POTENTIELS DANS DEV:")
            for issue in issues:
                print(f"   🔧 {issue['setting']}: {issue['issue']}")
                print(f"      💡 {issue['recommendation']}")
    
    def generate_recommendations(self):
        """Génère des recommandations basées sur l'analyse"""
        recommendations = []
        
        analysis = self.report.get('partial_analysis', {})
        
        # Recommandations basées sur les erreurs d'environnement
        if analysis.get('missing_env_vars'):
            recommendations.append({
                'priority': 'ÉLEVÉ',
                'category': 'Configuration Environnement',
                'issue': 'Variables d\'environnement manquantes pour prod',
                'action': 'Créer fichier .env.example avec les variables requises',
                'details': f"Variables manquantes: {', '.join(analysis['missing_env_vars'])}"
            })
        
        # Recommandations basées sur l'analyse partielle
        for issue in analysis.get('potential_issues', []):
            if 'OnboardingRedirectMiddleware' in issue['issue']:
                recommendations.append({
                    'priority': 'CRITIQUE',
                    'category': 'Middleware',
                    'issue': 'OnboardingRedirectMiddleware potentiellement problématique',
                    'action': 'Désactiver temporairement ou simplifier la logique',
                    'details': 'Middleware complexe source probable des boucles'
                })
            
            elif 'boucle' in issue['issue']:
                recommendations.append({
                    'priority': 'CRITIQUE',
                    'category': 'Redirection',
                    'issue': 'LOGIN_REDIRECT_URL potentiellement problématique',
                    'action': 'Changer vers /dashboard/ en production',
                    'details': 'Éviter les redirections vers /onboarding/'
                })
        
        # Recommandations basées sur les différences
        if analysis.get('type') == 'full_comparison':
            differences = analysis.get('differences', {})
            
            for setting, diff in differences.items():
                if '🚨 CRITIQUE' in diff['impact']:
                    recommendations.append({
                        'priority': 'CRITIQUE',
                        'category': 'Configuration',
                        'issue': f'{setting} cause des problèmes critiques',
                        'action': f'Synchroniser prod sur dev: {diff["dev"]}',
                        'details': diff['impact']
                    })
        
        self.report['recommendations'] = recommendations
        return recommendations
    
    def print_recommendations(self, recommendations):
        """Affiche les recommandations"""
        if not recommendations:
            print("\n✅ Aucune recommandation - Configuration semble correcte")
            return
        
        print(f"\n💡 RECOMMANDATIONS ({len(recommendations)})")
        
        critical_recs = [r for r in recommendations if r['priority'] == 'CRITIQUE']
        if critical_recs:
            print(f"\n🚨 ACTIONS CRITIQUES ({len(critical_recs)}):")
            for i, rec in enumerate(critical_recs, 1):
                print(f"\n{i}. [{rec['category']}] {rec['issue']}")
                print(f"   Action: {rec['action']}")
                print(f"   Détail: {rec['details']}")
        
        other_recs = [r for r in recommendations if r['priority'] != 'CRITIQUE']
        if other_recs:
            print(f"\n⚠️  AUTRES RECOMMANDATIONS ({len(other_recs)}):")
            for i, rec in enumerate(other_recs, 1):
                print(f"\n{i}. [{rec['category']}] {rec['issue']}")
                print(f"   Action: {rec['action']}")
    
    def create_env_example(self, missing_vars):
        """Crée un fichier .env.example avec les variables manquantes"""
        if not missing_vars:
            return
        
        env_content = [
            "# Fichier .env.example généré automatiquement",
            f"# Généré le {datetime.now().isoformat()}",
            "# Copiez vers .env et remplissez les valeurs",
            "",
            "# Variables de base de données",
        ]
        
        for var in missing_vars:
            if 'POSTGRES' in var:
                env_content.append(f"{var}=")
            elif 'SECRET' in var:
                env_content.append(f"{var}=your-secret-key-here")
            elif 'EMAIL' in var:
                env_content.append(f"{var}=")
            elif 'API' in var:
                env_content.append(f"{var}=your-api-key-here")
            else:
                env_content.append(f"{var}=")
        
        try:
            with open('.env.example', 'w') as f:
                f.write('\n'.join(env_content))
            print(f"\n📄 Fichier .env.example créé avec {len(missing_vars)} variables")
        except Exception as e:
            print(f"\n❌ Erreur création .env.example: {e}")

def main():
    """Fonction principale corrigée"""
    print("🚀 ANALYSE COMPARATIVE DEV vs PROD (Version Sécurisée)")
    print("="*60)
    
    analyzer = SafeConfigComparison()
    
    # Analyser les configurations
    analyzer.analyze_configurations()
    
    # Générer et afficher les recommandations
    recommendations = analyzer.generate_recommendations()
    analyzer.print_recommendations(recommendations)
    
    # Créer .env.example si nécessaire
    analysis = analyzer.report.get('partial_analysis', {})
    missing_vars = analysis.get('missing_env_vars', [])
    if missing_vars:
        analyzer.create_env_example(missing_vars)
    
    # Sauvegarder le rapport
    try:
        with open('config_analysis_report.json', 'w', encoding='utf-8') as f:
            json.dump(analyzer.report, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n💾 Rapport sauvegardé: config_analysis_report.json")
    except Exception as e:
        print(f"\n⚠️ Erreur sauvegarde: {e}")
    
    print(f"\n🎉 Analyse terminée - {datetime.now()}")
    
    # Résumé final
    status = analyzer.report['config_status']
    if status['production'] != 'success':
        print(f"\n📋 RÉSUMÉ:")
        print(f"├── Dev: {'✅' if status['development'] == 'success' else '❌'}")
        print(f"├── Prod: ❌ (Variables d'environnement)")
        print(f"└── Recommandations: {len(recommendations)}")
        print(f"\n💡 SOLUTION IMMÉDIATE: Configurer les variables d'environnement manquantes")

if __name__ == "__main__":
    if not os.path.exists('manage.py'):
        print("❌ Erreur: Exécuter depuis la racine du projet Django")
        sys.exit(1)
    
    main()