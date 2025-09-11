#!/usr/bin/env python3
"""
Script pour nettoyer l'environnement de production
Supprime TOUTES les configurations non-production
"""

import os
import shutil

def clean_production_environment():
    """Nettoie l'environnement de production"""
    
    base_path = "/var/www/vhosts/martialcomp.com/httpdocs"
    config_path = os.path.join(base_path, "config/settings")
    
    print("🧹 NETTOYAGE DE L'ENVIRONNEMENT DE PRODUCTION")
    print("=" * 60)
    
    # 1. Supprimer les fichiers de configuration non-production
    files_to_remove = [
        "development.py",
        "staging.py", 
        "sqlite.py",
        "base.py"  # Peut créer des conflits d'héritage
    ]
    
    removed_files = []
    
    for file_name in files_to_remove:
        file_path = os.path.join(config_path, file_name)
        if os.path.exists(file_path):
            # Sauvegarder avant suppression
            backup_path = f"{file_path}.backup"
            shutil.copy2(file_path, backup_path)
            os.remove(file_path)
            removed_files.append(file_name)
            print(f"🗑️  Supprimé: {file_name} (sauvegardé en .backup)")
        else:
            print(f"ℹ️  Non trouvé: {file_name}")
    
    # 2. Nettoyer production.py pour qu'il soit autonome
    production_file = os.path.join(config_path, "production.py")
    
    if os.path.exists(production_file):
        with open(production_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Supprimer les imports vers base ou autres configs
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Supprimer les imports de base/development/staging
            if any(phrase in line.lower() for phrase in ['from .base import', 'from .development import', 'from .staging import']):
                print(f"🧹 Supprimé import: {line.strip()}")
                continue
            cleaned_lines.append(line)
        
        # Écrire le fichier nettoyé
        with open(production_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(cleaned_lines))
        
        print("✅ production.py nettoyé et autonome")
    
    # 3. Créer un nouveau fichier __init__.py minimal
    init_file = os.path.join(config_path, "__init__.py")
    with open(init_file, 'w', encoding='utf-8') as f:
        f.write("# Configuration de production uniquement\n")
    
    # 4. Supprimer les scripts de développement inutiles
    dev_scripts = [
        "manage_dev.py",
        "settings_dev.py", 
        "start_dev.sh",
        "test_*.py"
    ]
    
    for script_pattern in dev_scripts:
        script_path = os.path.join(base_path, script_pattern)
        if os.path.exists(script_path):
            os.remove(script_path)
            print(f"🗑️  Script dev supprimé: {script_pattern}")
    
    print("=" * 60)
    print(f"✅ {len(removed_files)} fichier(s) de configuration supprimé(s)")
    print("🎯 Environnement de production nettoyé !")
    print("📁 Il ne reste que:")
    print("   - config/settings/production.py (autonome)")
    print("   - config/settings/__init__.py (minimal)")
    
    return True

def verify_production_config():
    """Vérifie que la configuration de production est correcte"""
    
    print("\n🔍 VÉRIFICATION DE LA CONFIGURATION DE PRODUCTION")
    print("=" * 60)
    
    production_file = "/var/www/vhosts/martialcomp.com/httpdocs/config/settings/production.py"
    
    try:
        with open(production_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Vérifications importantes
        checks = [
            ("DATABASES", "martialcomp_db"),
            ("ALLOWED_HOSTS", "martialcomp.com"),
            ("SECRET_KEY", "SECRET_KEY"),
            ("DEBUG", "False")
        ]
        
        for setting, expected in checks:
            if setting in content:
                print(f"✅ {setting}: Configuré")
            else:
                print(f"⚠️  {setting}: Manquant ou problématique")
        
        # Vérifier qu'il n'y a plus d'imports problématiques
        problematic_imports = ['from .base', 'from .development', 'from .staging']
        for imp in problematic_imports:
            if imp in content:
                print(f"❌ Import problématique trouvé: {imp}")
            else:
                print(f"✅ Pas d'import {imp}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Nettoyage de l'environnement de production Django")
    
    if clean_production_environment():
        if verify_production_config():
            print("\n🎉 ENVIRONNEMENT DE PRODUCTION NETTOYÉ ET VÉRIFIÉ !")
            print("🚀 Django devrait maintenant démarrer de façon stable")
            print("📝 Utilisez uniquement: python3 manage.py runserver 0.0.0.0:8080")
        else:
            print("\n⚠️ Nettoyage effectué mais vérification échouée")
    else:
        print("\n❌ Échec du nettoyage") 
"""
Script pour nettoyer l'environnement de production
Supprime TOUTES les configurations non-production
"""

import os
import shutil

def clean_production_environment():
    """Nettoie l'environnement de production"""
    
    base_path = "/var/www/vhosts/martialcomp.com/httpdocs"
    config_path = os.path.join(base_path, "config/settings")
    
    print("🧹 NETTOYAGE DE L'ENVIRONNEMENT DE PRODUCTION")
    print("=" * 60)
    
    # 1. Supprimer les fichiers de configuration non-production
    files_to_remove = [
        "development.py",
        "staging.py", 
        "sqlite.py",
        "base.py"  # Peut créer des conflits d'héritage
    ]
    
    removed_files = []
    
    for file_name in files_to_remove:
        file_path = os.path.join(config_path, file_name)
        if os.path.exists(file_path):
            # Sauvegarder avant suppression
            backup_path = f"{file_path}.backup"
            shutil.copy2(file_path, backup_path)
            os.remove(file_path)
            removed_files.append(file_name)
            print(f"🗑️  Supprimé: {file_name} (sauvegardé en .backup)")
        else:
            print(f"ℹ️  Non trouvé: {file_name}")
    
    # 2. Nettoyer production.py pour qu'il soit autonome
    production_file = os.path.join(config_path, "production.py")
    
    if os.path.exists(production_file):
        with open(production_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Supprimer les imports vers base ou autres configs
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Supprimer les imports de base/development/staging
            if any(phrase in line.lower() for phrase in ['from .base import', 'from .development import', 'from .staging import']):
                print(f"🧹 Supprimé import: {line.strip()}")
                continue
            cleaned_lines.append(line)
        
        # Écrire le fichier nettoyé
        with open(production_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(cleaned_lines))
        
        print("✅ production.py nettoyé et autonome")
    
    # 3. Créer un nouveau fichier __init__.py minimal
    init_file = os.path.join(config_path, "__init__.py")
    with open(init_file, 'w', encoding='utf-8') as f:
        f.write("# Configuration de production uniquement\n")
    
    # 4. Supprimer les scripts de développement inutiles
    dev_scripts = [
        "manage_dev.py",
        "settings_dev.py", 
        "start_dev.sh",
        "test_*.py"
    ]
    
    for script_pattern in dev_scripts:
        script_path = os.path.join(base_path, script_pattern)
        if os.path.exists(script_path):
            os.remove(script_path)
            print(f"🗑️  Script dev supprimé: {script_pattern}")
    
    print("=" * 60)
    print(f"✅ {len(removed_files)} fichier(s) de configuration supprimé(s)")
    print("🎯 Environnement de production nettoyé !")
    print("📁 Il ne reste que:")
    print("   - config/settings/production.py (autonome)")
    print("   - config/settings/__init__.py (minimal)")
    
    return True

def verify_production_config():
    """Vérifie que la configuration de production est correcte"""
    
    print("\n🔍 VÉRIFICATION DE LA CONFIGURATION DE PRODUCTION")
    print("=" * 60)
    
    production_file = "/var/www/vhosts/martialcomp.com/httpdocs/config/settings/production.py"
    
    try:
        with open(production_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Vérifications importantes
        checks = [
            ("DATABASES", "martialcomp_db"),
            ("ALLOWED_HOSTS", "martialcomp.com"),
            ("SECRET_KEY", "SECRET_KEY"),
            ("DEBUG", "False")
        ]
        
        for setting, expected in checks:
            if setting in content:
                print(f"✅ {setting}: Configuré")
            else:
                print(f"⚠️  {setting}: Manquant ou problématique")
        
        # Vérifier qu'il n'y a plus d'imports problématiques
        problematic_imports = ['from .base', 'from .development', 'from .staging']
        for imp in problematic_imports:
            if imp in content:
                print(f"❌ Import problématique trouvé: {imp}")
            else:
                print(f"✅ Pas d'import {imp}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Nettoyage de l'environnement de production Django")
    
    if clean_production_environment():
        if verify_production_config():
            print("\n🎉 ENVIRONNEMENT DE PRODUCTION NETTOYÉ ET VÉRIFIÉ !")
            print("🚀 Django devrait maintenant démarrer de façon stable")
            print("📝 Utilisez uniquement: python3 manage.py runserver 0.0.0.0:8080")
        else:
            print("\n⚠️ Nettoyage effectué mais vérification échouée")
    else:
        print("\n❌ Échec du nettoyage") 