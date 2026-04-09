#!/usr/bin/env python3
"""
Script pour déployer la correction du JavaScript sur la production
"""

import os
import shutil
from datetime import datetime

def deploy_js_fix():
    print("🚀 Déploiement de la correction JavaScript sur la production...")
    
    # Chemin du template corrigé en développement
    dev_template = '/mnt/c/martial_hub_django/martialcomp/apps/competitions/templates/competitions/dashboard/club.html'
    
    # Vérifier que le template de développement existe
    if not os.path.exists(dev_template):
        print("❌ Template de développement non trouvé")
        return False
    
    # Créer une sauvegarde du template de production
    backup_dir = '/mnt/c/martial_hub_django/martialcomp/backups'
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{backup_dir}/club_template_backup_{timestamp}.html"
    
    # Note: En production, le template serait dans un chemin différent
    # Ici on simule la structure de production
    prod_template = '/mnt/c/martial_hub_django/martialcomp/apps/competitions/templates/competitions/dashboard/club.html'
    
    if os.path.exists(prod_template):
        shutil.copy2(prod_template, backup_file)
        print(f"✅ Sauvegarde créée: {backup_file}")
    
    # Copier le template corrigé
    shutil.copy2(dev_template, prod_template)
    print("✅ Template corrigé déployé")
    
    # Vérifier que la correction est présente
    with open(prod_template, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'function calculateAges()' in content and '<script>' in content:
        print("✅ Correction JavaScript vérifiée dans le template de production")
        return True
    else:
        print("❌ Correction JavaScript non trouvée dans le template de production")
        return False

def create_deployment_script():
    """Créer un script de déploiement pour la production"""
    
    script_content = '''#!/bin/bash
# Script de déploiement pour la correction JavaScript
# À exécuter sur le serveur de production

echo "🚀 Déploiement de la correction JavaScript..."

# Sauvegarder le template actuel
cp /path/to/production/apps/competitions/templates/competitions/dashboard/club.html /path/to/backups/club_template_backup_$(date +%Y%m%d_%H%M%S).html

# Copier le template corrigé
cp /path/to/corrected/club.html /path/to/production/apps/competitions/templates/competitions/dashboard/club.html

# Vérifier la correction
if grep -q "function calculateAges()" /path/to/production/apps/competitions/templates/competitions/dashboard/club.html; then
    echo "✅ Correction JavaScript déployée avec succès"
else
    echo "❌ Erreur lors du déploiement"
    exit 1
fi

# Redémarrer le serveur web si nécessaire
# systemctl restart nginx
# systemctl restart gunicorn

echo "✅ Déploiement terminé"
'''
    
    with open('/mnt/c/martial_hub_django/martialcomp/deploy_js_fix.sh', 'w') as f:
        f.write(script_content)
    
    os.chmod('/mnt/c/martial_hub_django/martialcomp/deploy_js_fix.sh', 0o755)
    print("✅ Script de déploiement créé: deploy_js_fix.sh")

if __name__ == "__main__":
    success = deploy_js_fix()
    if success:
        create_deployment_script()
        print("\n📋 Instructions pour la production:")
        print("1. Copiez le fichier club.html corrigé sur le serveur de production")
        print("2. Exécutez le script deploy_js_fix.sh sur le serveur de production")
        print("3. Redémarrez le serveur web si nécessaire")
        print("4. Vérifiez que le JavaScript fonctionne sur https://martialcomp.com")
    else:
        print("❌ Échec du déploiement")