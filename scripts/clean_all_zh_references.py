#!/usr/bin/env python3
"""
Script pour nettoyer toutes les références aux codes de langue problématiques
"""

import os
import re
import sys

def clean_file(file_path):
    """Nettoie un fichier des codes de langue problématiques"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Codes problématiques à supprimer
        problematic_codes = ['zh', 'am', 'zu', 'yo']
        
        # Remplacer les codes problématiques
        for code in problematic_codes:
            # Remplacer dans les listes de langues
            content = re.sub(rf"'{code}'", "", content)
            content = re.sub(rf'"{code}"', "", content)
            content = re.sub(rf"'{code}-hans'", "'zh-hans'", content)
            content = re.sub(rf'"{code}-hans"', '"zh-hans"', content)
            
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
            print(f"⏭️ Pas de changement: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur avec {file_path}: {e}")
        return False

def main():
    """Fonction principale"""
    print("🧹 NETTOYAGE DES RÉFÉRENCES PROBLÉMATIQUES")
    print("=" * 50)
    
    # Fichiers critiques à nettoyer
    critical_files = [
        '/var/www/vhosts/martialcomp.com/httpdocs/complete_translations.py',
        '/var/www/vhosts/martialcomp.com/httpdocs/smart_translate.py',
        '/var/www/vhosts/martialcomp.com/httpdocs/fix_languages.py',
        '/var/www/vhosts/martialcomp.com/httpdocs/check_languages.py',
        '/var/www/vhosts/martialcomp.com/httpdocs/translation_service.py',
        '/var/www/vhosts/martialcomp.com/httpdocs/config/translation_service.py',
        '/var/www/vhosts/martialcomp.com/httpdocs/scripts/update_translations.py',
        '/var/www/vhosts/martialcomp.com/httpdocs/scripts/multilingual_implementation_summary.py',
    ]
    
    cleaned_count = 0
    
    for file_path in critical_files:
        if os.path.exists(file_path):
            if clean_file(file_path):
                cleaned_count += 1
    
    print(f"\n📊 Résumé: {cleaned_count} fichiers nettoyés")
    
    if cleaned_count > 0:
        print("\n🔄 Redémarrage de gunicorn...")
        os.system("pkill -f gunicorn")
        import time
        time.sleep(3)
        os.system("cd /var/www/vhosts/martialcomp.com/httpdocs && sudo -u www-data .venv/bin/gunicorn --bind 127.0.0.1:8002 --workers 2 --timeout 30 --access-logfile logs/gunicorn_access.log --error-logfile logs/gunicorn_error.log --log-level info config.wsgi:application --daemon")
        print("✅ Gunicorn redémarré")
    
    print("\n🎯 NETTOYAGE TERMINÉ!")
    print("🌐 Testez maintenant l'interface admin")

if __name__ == "__main__":
    main() 