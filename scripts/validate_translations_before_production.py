#!/usr/bin/env python3
"""
Script de validation des traductions avant déploiement en production
Vérifications de compatibilité et d'intégrité
"""

import os
import sys
import django
import subprocess
from pathlib import Path
import json
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

def setup_django():
    """Configure Django"""
    try:
        django.setup()
        return True
    except Exception as e:
        print(f"❌ Erreur Django setup: {e}")
        return False

def check_translation_completeness():
    """Vérifie la complétude des traductions prioritaires"""
    print("\n🔍 VÉRIFICATION DE LA COMPLÉTUDE DES TRADUCTIONS")
    print("=" * 55)
    
    priority_languages = ['en', 'es', 'it', 'de']
    results = {}
    
    try:
        import polib
    except ImportError:
        print("❌ polib non disponible - installation requise")
        return False
    
    for lang in priority_languages:
        po_path = f"locale/{lang}/LC_MESSAGES/django.po"
        
        if not os.path.exists(po_path):
            print(f"❌ {lang}: Fichier PO manquant")
            results[lang] = {'status': 'missing', 'percentage': 0}
            continue
        
        try:
            po = polib.pofile(po_path)
            total_entries = len(po)
            translated_entries = len([entry for entry in po if entry.msgstr.strip()])
            
            if total_entries > 0:
                percentage = (translated_entries / total_entries) * 100
                status = 'complete' if percentage >= 90 else 'partial' if percentage >= 50 else 'incomplete'
                
                results[lang] = {
                    'status': status,
                    'percentage': percentage,
                    'translated': translated_entries,
                    'total': total_entries
                }
                
                icon = '✅' if percentage >= 90 else '⚠️' if percentage >= 50 else '❌'
                print(f"{icon} {lang}: {translated_entries}/{total_entries} ({percentage:.1f}%)")
            else:
                results[lang] = {'status': 'empty', 'percentage': 0}
                print(f"❌ {lang}: Fichier vide")
                
        except Exception as e:
            print(f"❌ {lang}: Erreur lecture - {e}")
            results[lang] = {'status': 'error', 'percentage': 0}
    
    return results

def check_production_compatibility():
    """Vérifie la compatibilité avec la production"""
    print("\n🔧 VÉRIFICATION DE LA COMPATIBILITÉ PRODUCTION")
    print("=" * 50)
    
    checks = {
        'settings_production': False,
        'nginx_config': False,
        'gunicorn_config': False,
        'deployment_scripts': False,
        'locale_structure': False
    }
    
    # Vérifier settings de production
    if os.path.exists('config/settings_production_final.py'):
        checks['settings_production'] = True
        print("✅ Fichier settings de production présent")
    else:
        print("❌ Fichier settings de production manquant")
    
    # Vérifier config Nginx
    nginx_files = ['nginx_production_config.conf', 'nginx_martialcomp.conf']
    for nginx_file in nginx_files:
        if os.path.exists(nginx_file):
            checks['nginx_config'] = True
            print(f"✅ Configuration Nginx trouvée: {nginx_file}")
            break
    
    if not checks['nginx_config']:
        print("❌ Configuration Nginx manquante")
    
    # Vérifier config Gunicorn
    if os.path.exists('gunicorn_production_config.py'):
        checks['gunicorn_config'] = True
        print("✅ Configuration Gunicorn présente")
    else:
        print("❌ Configuration Gunicorn manquante")
    
    # Vérifier scripts de déploiement
    deployment_files = ['deploy_translations_production.sh', 'deploy_production.sh']
    for deploy_file in deployment_files:
        if os.path.exists(deploy_file):
            checks['deployment_scripts'] = True
            print(f"✅ Script de déploiement trouvé: {deploy_file}")
            break
    
    if not checks['deployment_scripts']:
        print("❌ Scripts de déploiement manquants")
    
    # Vérifier structure locale
    if os.path.exists('locale') and os.path.isdir('locale'):
        locale_dirs = [d for d in os.listdir('locale') if os.path.isdir(f'locale/{d}')]
        if len(locale_dirs) >= 4:  # Au moins 4 langues
            checks['locale_structure'] = True
            print(f"✅ Structure locale correcte ({len(locale_dirs)} langues)")
        else:
            print(f"⚠️ Structure locale partielle ({len(locale_dirs)} langues)")
    else:
        print("❌ Répertoire locale manquant")
    
    return checks

def check_django_config():
    """Vérifie la configuration Django pour i18n"""
    print("\n⚙️ VÉRIFICATION DE LA CONFIGURATION DJANGO")
    print("=" * 45)
    
    try:
        from django.conf import settings
        
        # Vérifier USE_I18N
        if getattr(settings, 'USE_I18N', False):
            print("✅ USE_I18N activé")
        else:
            print("❌ USE_I18N non activé")
            return False
        
        # Vérifier LANGUAGES
        languages = getattr(settings, 'LANGUAGES', [])
        if len(languages) >= 4:
            print(f"✅ LANGUAGES configuré ({len(languages)} langues)")
        else:
            print(f"⚠️ LANGUAGES partiellement configuré ({len(languages)} langues)")
        
        # Vérifier LOCALE_PATHS
        locale_paths = getattr(settings, 'LOCALE_PATHS', [])
        if locale_paths:
            print("✅ LOCALE_PATHS configuré")
        else:
            print("❌ LOCALE_PATHS non configuré")
        
        # Vérifier middleware
        middleware = getattr(settings, 'MIDDLEWARE', [])
        if 'django.middleware.locale.LocaleMiddleware' in middleware:
            print("✅ LocaleMiddleware présent")
        else:
            print("❌ LocaleMiddleware manquant")
        
        # Vérifier apps de traduction
        installed_apps = getattr(settings, 'INSTALLED_APPS', [])
        if 'rosetta' in installed_apps:
            print("✅ django-rosetta installé")
        else:
            print("⚠️ django-rosetta non installé")
        
        if 'modeltranslation' in installed_apps:
            print("✅ django-modeltranslation installé")
        else:
            print("⚠️ django-modeltranslation non installé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur vérification Django: {e}")
        return False

def test_translation_system():
    """Test fonctionnel du système de traduction"""
    print("\n🧪 TEST FONCTIONNEL DU SYSTÈME DE TRADUCTION")
    print("=" * 45)
    
    try:
        from django.utils.translation import activate, gettext as _
        
        # Test base français
        activate('fr')
        fr_text = _("Accueil")
        print(f"Français: '{fr_text}'")
        
        # Test anglais
        activate('en')
        en_text = _("Accueil")
        print(f"Anglais: '{en_text}'")
        
        # Test espagnol
        activate('es')
        es_text = _("Accueil")
        print(f"Espagnol: '{es_text}'")
        
        # Vérifier que les traductions sont différentes
        if fr_text != en_text and en_text != es_text:
            print("✅ Système de traduction fonctionnel")
            return True
        else:
            print("❌ Traductions identiques - système non fonctionnel")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test traduction: {e}")
        return False

def check_template_readiness():
    """Vérifie que les templates sont prêts pour i18n"""
    print("\n📄 VÉRIFICATION DES TEMPLATES")
    print("=" * 35)
    
    template_count = 0
    i18n_count = 0
    missing_i18n = []
    
    # Parcourir les templates
    for root, dirs, files in os.walk('.'):
        # Ignorer certains dossiers
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'staticfiles', 'media']]
        
        for file in files:
            if file.endswith('.html'):
                template_count += 1
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if '{% load i18n %}' in content or '{% trans ' in content:
                            i18n_count += 1
                        else:
                            missing_i18n.append(file_path)
                except:
                    pass
    
    percentage = (i18n_count / template_count * 100) if template_count > 0 else 0
    
    print(f"📊 Templates total: {template_count}")
    print(f"✅ Templates i18n: {i18n_count} ({percentage:.1f}%)")
    print(f"⚠️ Templates sans i18n: {len(missing_i18n)}")
    
    if len(missing_i18n) <= 10:  # Afficher quelques exemples
        for template in missing_i18n[:5]:
            print(f"   - {template}")
        if len(missing_i18n) > 5:
            print(f"   ... et {len(missing_i18n) - 5} autres")
    
    return percentage >= 80  # 80% minimum requis

def generate_production_checklist():
    """Génère une checklist pour la production"""
    print("\n📋 CHECKLIST POUR LE DÉPLOIEMENT PRODUCTION")
    print("=" * 45)
    
    checklist = [
        "□ Compiler toutes les traductions (makemessages + compilemessages)",
        "□ Tester les URLs multilingues localement",
        "□ Vérifier l'interface Rosetta",
        "□ Sauvegarder la configuration de production actuelle",
        "□ Déployer le script deploy_translations_production.sh",
        "□ Tester les URLs en production après déploiement",
        "□ Vérifier les logs de déploiement",
        "□ Tester le changement de langue en production",
        "□ Valider les performances (temps de chargement)",
        "□ Informer les utilisateurs des nouvelles langues disponibles"
    ]
    
    for item in checklist:
        print(f"  {item}")
    
    return checklist

def create_deployment_report():
    """Crée un rapport de déploiement"""
    print("\n📊 GÉNÉRATION DU RAPPORT DE DÉPLOIEMENT")
    print("=" * 45)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'validation_status': 'pending',
        'translation_completeness': {},
        'compatibility_checks': {},
        'django_config': False,
        'translation_system': False,
        'template_readiness': False,
        'recommendations': []
    }
    
    # Collecter les résultats
    report['translation_completeness'] = check_translation_completeness()
    report['compatibility_checks'] = check_production_compatibility()
    report['django_config'] = check_django_config()
    report['translation_system'] = test_translation_system()
    report['template_readiness'] = check_template_readiness()
    
    # Déterminer le statut global
    all_checks = [
        report['django_config'],
        report['translation_system'],
        report['template_readiness']
    ]
    
    if all(all_checks):
        report['validation_status'] = 'ready'
        print("✅ Système prêt pour le déploiement en production")
    elif any(all_checks):
        report['validation_status'] = 'partial'
        print("⚠️ Système partiellement prêt - vérifications requises")
        report['recommendations'].append("Résoudre les problèmes de configuration avant déploiement")
    else:
        report['validation_status'] = 'not_ready'
        print("❌ Système non prêt pour la production")
        report['recommendations'].append("Configuration majeure requise avant déploiement")
    
    # Sauvegarder le rapport
    with open('translation_validation_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"📄 Rapport sauvegardé: translation_validation_report.json")
    
    return report

def main():
    """Fonction principale"""
    print("🌍 VALIDATION DES TRADUCTIONS POUR PRODUCTION")
    print("=" * 50)
    
    # Configuration Django
    if not setup_django():
        sys.exit(1)
    
    # Exécuter toutes les vérifications
    create_deployment_report()
    generate_production_checklist()
    
    print("\n🏁 VALIDATION TERMINÉE")
    print("Consultez le fichier translation_validation_report.json pour les détails")

if __name__ == '__main__':
    main()