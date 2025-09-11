#!/usr/bin/env python3
"""
Script simple pour copier tous les templates dashboard du DEV vers la PRODUCTION
"""
import os
import shutil
import time
import zipfile
from datetime import datetime

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_name = f"dev_dashboards_to_prod_{timestamp}.zip"
    temp_dir = f"dashboard_package_{timestamp}"
    
    log("📦 CRÉATION PACKAGE TEMPLATES DASHBOARD DEV → PROD")
    log("=" * 60)
    
    # Créer le répertoire temporaire
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    # Templates à copier
    templates = [
        "federation.html",
        "club.html", 
        "admin.html",
        "coach.html",
        "combat.html",
        "judge.html",
        "manager.html",
        "participant_competitions.html",
        "participant_enhanced.html", 
        "participant_profile.html",
        "referee.html",
        "spectator.html",
        "base.html",
        "unified_base.html"
    ]
    
    # Répertoire source
    source_dir = "competitions/templates/competitions/dashboard"
    dest_dir = os.path.join(temp_dir, "templates/competitions/dashboard")
    os.makedirs(dest_dir, exist_ok=True)
    
    copied = []
    
    log("\n📄 COPIE DES TEMPLATES")
    for template in templates:
        source_path = os.path.join(source_dir, template)
        dest_path = os.path.join(dest_dir, template)
        
        if os.path.exists(source_path):
            try:
                shutil.copy2(source_path, dest_path)
                copied.append(template)
                log(f"✅ {template}")
            except Exception as e:
                log(f"❌ {template}: {e}")
        else:
            log(f"⚠️ Manquant: {template}")
    
    # Copier les sous-dossiers
    for subdir in ["documentation", "finance"]:
        source_subdir = os.path.join(source_dir, subdir)
        if os.path.exists(source_subdir):
            dest_subdir = os.path.join(dest_dir, subdir)
            try:
                shutil.copytree(source_subdir, dest_subdir)
                log(f"✅ Dossier: {subdir}/")
            except:
                pass
    
    # Script de déploiement
    deploy_script = '''#!/bin/bash
echo "🚀 DÉPLOIEMENT TEMPLATES DASHBOARD"
PROD_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
cd "$PROD_DIR"

# Sauvegarde
BACKUP_DIR="backup_dashboard_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
if [ -d "competitions/templates/competitions/dashboard" ]; then
    cp -r competitions/templates/competitions/dashboard/ "$BACKUP_DIR/"
    echo "✅ Sauvegarde: $BACKUP_DIR"
fi

# Copie
mkdir -p competitions/templates/competitions/
cp -r templates/competitions/dashboard competitions/templates/competitions/
echo "✅ Templates copiés"

# Redémarrage
pkill -f gunicorn
sleep 3
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --daemon
sleep 6
echo "✅ Django redémarré"

curl -I -s http://localhost:8000/ | head -1
echo "🎉 Déploiement terminé!"
'''
    
    with open(os.path.join(temp_dir, "deploy.sh"), 'w') as f:
        f.write(deploy_script)
    
    # README
    readme = f'''# Templates Dashboard DEV → PROD

## Contenu
{len(copied)} templates dashboard du dev copiés :
''' + '\n'.join([f"- {t}" for t in copied]) + '''

## Déploiement
1. scp {package_name} root@martialcomp.com:/tmp/
2. ssh root@martialcomp.com
3. cd /tmp && unzip {package_name}
4. cd dashboard_package_*/ && chmod +x deploy.sh && ./deploy.sh

## Test
- https://martialcomp.com/dashboard/club/
- https://martialcomp.com/dashboard/federation/
- Connexion: dojo_sakura_manager / demo2025
'''
    
    with open(os.path.join(temp_dir, "README.md"), 'w') as f:
        f.write(readme)
    
    # Créer le ZIP
    with zipfile.ZipFile(package_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arc_path = os.path.relpath(file_path, temp_dir)
                zipf.write(file_path, arc_path)
    
    # Nettoyer
    shutil.rmtree(temp_dir)
    
    log(f"\n🎉 PACKAGE CRÉÉ: {package_name}")
    log(f"📊 Templates copiés: {len(copied)}")
    
    print(f"\n🚀 COMMANDES DE DÉPLOIEMENT:")
    print(f"scp {package_name} root@martialcomp.com:/tmp/")
    print("ssh root@martialcomp.com")
    print(f"cd /tmp && unzip {package_name}")
    print("cd dashboard_package_*/ && chmod +x deploy.sh && ./deploy.sh")
    
    return package_name

if __name__ == "__main__":
    main()