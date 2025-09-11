#!/usr/bin/env python3
"""
Script simple pour supprimer toutes les références à 'zh' dans tous les fichiers
"""

import os
import re
import sys

def remove_zh_from_file(file_path):
    """Supprime toutes les références à 'zh' dans un fichier"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Supprimer toutes les références à 'zh' (sauf zh-hans)
        content = re.sub(r"'zh'", "", content)
        content = re.sub(r'"zh"', "", content)
        content = re.sub(r"'zh,'", "", content)
        content = re.sub(r'",zh"', "", content)
        content = re.sub(r"'zh\s*'", "", content)
        content = re.sub(r'"zh\s*"', "", content)
        
        # Nettoyer les virgules en double
        content = re.sub(r',\s*,', ',', content)
        content = re.sub(r'\[\s*,', '[', content)
        content = re.sub(r',\s*\]', ']', content)
        
        # Si le contenu a changé, sauvegarder
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Nettoyé: {file_path}")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ Erreur avec {file_path}: {e}")
        return False

def main():
    """Fonction principale"""
    print("🧹 SUPPRESSION DE TOUTES LES RÉFÉRENCES À 'zh'")
    print("=" * 50)
    
    # Répertoire du projet
    project_dir = '/var/www/vhosts/martialcomp.com/httpdocs'
    
    # Extensions de fichiers à traiter
    extensions = ['.py', '.html', '.txt', '.md', '.json', '.yml', '.yaml']
    
    cleaned_count = 0
    
    # Parcourir tous les fichiers
    for root, dirs, files in os.walk(project_dir):
        # Ignorer les dossiers système
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.venv', 'venv', 'node_modules']]
        
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                if remove_zh_from_file(file_path):
                    cleaned_count += 1
    
    print(f"\n📊 Résumé: {cleaned_count} fichiers nettoyés")
    
    if cleaned_count > 0:
        print("\n🔄 Redémarrage de gunicorn...")
        os.system("pkill -f gunicorn")
        import time
        time.sleep(3)
        os.system("cd /var/www/vhosts/martialcomp.com/httpdocs && sudo -u www-data .venv/bin/gunicorn --bind 127.0.0.1:8002 --workers 2 --timeout 30 --access-logfile logs/gunicorn_access.log --error-logfile logs/gunicorn_error.log --log-level info config.wsgi:application --daemon")
        print("✅ Gunicorn redémarré")
    
    print("\n🎯 SUPPRESSION TERMINÉE!")
    print("🌐 Testez maintenant l'interface admin")

if __name__ == "__main__":
    main() 