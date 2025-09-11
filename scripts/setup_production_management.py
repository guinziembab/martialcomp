#!/usr/bin/env python3
"""
Script pour mettre en place un système propre de gestion des versions
1. Nettoyage des fichiers temporaires
2. Configuration Git/GitHub
3. Système de backup local
4. Workflow de déploiement
"""
import os
import sys
import glob
import shutil
from datetime import datetime

# Répertoire de production
PROD_DIR = '/var/www/vhosts/martialcomp.com/httpdocs'
os.chdir(PROD_DIR)

def cleanup_production_files():
    """Nettoie les fichiers temporaires et scripts en production"""
    
    print("🧹 NETTOYAGE PRODUCTION")
    print("=======================")
    
    # Patterns de fichiers à nettoyer
    cleanup_patterns = [
        '*.py.backup_*',
        '*.backup_*',
        'fix_*.py',
        'deploy_*.py',
        'debug_*.py',
        'restore_*.py',
        'setup_*.py',
        'script_*.py',
        'test_*.py',
        'correction_*.py',
        'final_*.py',
        'quick_*.py',
        'complete_*.py',
        'urgent_*.py',
        'emergency_*.py',
        'martialcomp*.zip',
        'martialcomp*.tar.gz',
        '*.json',
        '*.md',
        'migration_package_*/',
        'deployment_*/',
        'COMMANDES_*.md',
        'DEPLOIEMENT_*.md',
        'DIAGNOSTIC_*.md',
        'RESOLUTION_*.md',
        'RESULTAT_*.md',
        'SCRIPT_*.md',
        'SOCIAL_AUTH_*.md',
        'SUITE_*.md',
        'TESTS_*.md',
        'TEST_*.md',
        'MULTILINGUAL_*.md',
        '*.sh'
    ]
    
    cleaned_files = []
    protected_files = [
        'manage.py',
        'requirements.txt',
        'venv/',
        'static/',
        'media/',
        'locale/',
        'config/',
        'competitions/',
        'grades/',
        'organizations/',
        'permissions_manager/',
        'finances/',
        'shop/',
        'documents/',
        'multitenant/',
        'family_management/'
    ]
    
    for pattern in cleanup_patterns:
        files = glob.glob(pattern, recursive=True)
        for file_path in files:
            # Vérifier que ce n'est pas un fichier protégé
            is_protected = False
            for protected in protected_files:
                if file_path.startswith(protected):
                    is_protected = True
                    break
            
            if not is_protected:
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        cleaned_files.append(file_path)
                        print(f"✅ Supprimé: {file_path}")
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                        cleaned_files.append(file_path)
                        print(f"✅ Dossier supprimé: {file_path}")
                except Exception as e:
                    print(f"❌ Erreur suppression {file_path}: {e}")
    
    print(f"\n📊 Nettoyage terminé: {len(cleaned_files)} fichiers/dossiers supprimés")
    return len(cleaned_files) > 0

def setup_gitignore():
    """Crée un .gitignore approprié"""
    
    print("\n📝 CRÉATION .gitignore")
    print("======================")
    
    gitignore_content = '''# Fichiers Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Django
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Environnements virtuels
venv/
env/
ENV/
.venv/

# Fichiers de configuration sensibles
.env
.env.local
.env.production
*.key
*.pem
secrets.json

# Fichiers de backup
*.backup
*.backup_*
*.bak
*.old

# Scripts temporaires
fix_*.py
deploy_*.py
debug_*.py
restore_*.py
setup_*.py
script_*.py
test_*.py
correction_*.py
final_*.py
quick_*.py
complete_*.py
urgent_*.py
emergency_*.py

# Archives
*.zip
*.tar.gz
*.tar.bz2

# Documentation temporaire
COMMANDES_*.md
DEPLOIEMENT_*.md
DIAGNOSTIC_*.md
RESOLUTION_*.md

# Fichiers système
.DS_Store
Thumbs.db
*.swp
*.swo

# Médias et statiques (en production)
/media/uploads/
/static/collected/

# Bases de données
*.sqlite3
*.db

# Logs
logs/
*.log

# IDE
.vscode/
.idea/
*.sublime-*

# Certificats SSL
*.crt
*.csr
'''
    
    try:
        with open('.gitignore', 'w', encoding='utf-8') as f:
            f.write(gitignore_content)
        print("✅ .gitignore créé")
        return True
    except Exception as e:
        print(f"❌ Erreur création .gitignore: {e}")
        return False

def initialize_git_repo():
    """Initialise le repository Git"""
    
    print("\n🔧 INITIALISATION GIT")
    print("=====================")
    
    try:
        import subprocess
        
        # Vérifier si Git est déjà initialisé
        if os.path.exists('.git'):
            print("✅ Repository Git déjà initialisé")
        else:
            subprocess.run(['git', 'init'], check=True)
            print("✅ Repository Git initialisé")
        
        # Configuration utilisateur (si pas déjà configuré)
        try:
            subprocess.run(['git', 'config', 'user.name', 'MartialComp Admin'], check=True)
            subprocess.run(['git', 'config', 'user.email', 'admin@martialcomp.com'], check=True)
            print("✅ Configuration Git utilisateur définie")
        except:
            print("⚪ Configuration Git utilisateur déjà définie")
        
        # Ajouter les fichiers du projet
        subprocess.run(['git', 'add', '.'], check=True)
        
        # Commit initial
        commit_message = f"Initial commit - MartialComp {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)
        print("✅ Commit initial créé")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur Git: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur initialisation Git: {e}")
        return False

def create_backup_script():
    """Crée un script de sauvegarde automatique"""
    
    print("\n💾 SCRIPT SAUVEGARDE AUTOMATIQUE")
    print("================================")
    
    backup_script = '''#!/bin/bash
# Script de sauvegarde automatique MartialComp
# Usage: ./backup.sh [message]

DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/tmp/martialcomp_backup_$DATE"
LOCAL_BACKUP="/mnt/c/martial_hub_django/backups"
MESSAGE="${1:-Sauvegarde automatique $DATE}"

echo "📦 SAUVEGARDE MARTIALCOMP - $DATE"
echo "================================="

# Créer commit Git
echo "🔧 Commit Git..."
git add .
git commit -m "$MESSAGE" 2>/dev/null || echo "Rien à commiter"

# Créer archive locale
echo "📁 Création archive..."
mkdir -p "$BACKUP_DIR"

# Copier les fichiers essentiels
cp -r config/ "$BACKUP_DIR/"
cp -r competitions/ "$BACKUP_DIR/"
cp -r grades/ "$BACKUP_DIR/"
cp -r organizations/ "$BACKUP_DIR/"
cp -r permissions_manager/ "$BACKUP_DIR/"
cp -r finances/ "$BACKUP_DIR/"
cp -r shop/ "$BACKUP_DIR/"
cp -r documents/ "$BACKUP_DIR/"
cp -r multitenant/ "$BACKUP_DIR/"
cp -r family_management/ "$BACKUP_DIR/"
cp manage.py "$BACKUP_DIR/"
cp requirements.txt "$BACKUP_DIR/"

# Créer archive
cd /tmp
tar -czf "martialcomp_backup_$DATE.tar.gz" "martialcomp_backup_$DATE/"

# Copier vers PC Windows (si monté)
if [ -d "$LOCAL_BACKUP" ]; then
    echo "💻 Copie vers PC local..."
    mkdir -p "$LOCAL_BACKUP"
    cp "martialcomp_backup_$DATE.tar.gz" "$LOCAL_BACKUP/"
    echo "✅ Sauvegarde copiée: $LOCAL_BACKUP/martialcomp_backup_$DATE.tar.gz"
else
    echo "⚠️ Répertoire PC local non accessible: $LOCAL_BACKUP"
fi

# Nettoyer
rm -rf "$BACKUP_DIR"

echo "✅ Sauvegarde terminée: martialcomp_backup_$DATE.tar.gz"
'''
    
    try:
        with open('backup.sh', 'w', encoding='utf-8') as f:
            f.write(backup_script)
        
        # Rendre exécutable
        os.chmod('backup.sh', 0o755)
        print("✅ Script backup.sh créé")
        return True
        
    except Exception as e:
        print(f"❌ Erreur création script backup: {e}")
        return False

def create_deployment_workflow():
    """Crée un workflow de déploiement"""
    
    print("\n🚀 WORKFLOW DÉPLOIEMENT")
    print("=======================")
    
    deploy_script = '''#!/bin/bash
# Workflow de déploiement MartialComp
# Usage: ./deploy.sh [environment]

ENVIRONMENT="${1:-production}"
DATE=$(date +"%Y%m%d_%H%M%S")

echo "🚀 DÉPLOIEMENT MARTIALCOMP - $ENVIRONMENT"
echo "========================================"

# 1. Sauvegarde avant déploiement
echo "💾 Sauvegarde pré-déploiement..."
./backup.sh "Pre-deployment backup $DATE"

# 2. Tests de base
echo "🧪 Tests de base..."
python3 manage.py check || { echo "❌ Tests échoués"; exit 1; }

# 3. Migrations
echo "📊 Migrations base de données..."
python3 manage.py migrate || { echo "❌ Migrations échouées"; exit 1; }

# 4. Collecte des fichiers statiques
echo "📁 Collecte fichiers statiques..."
python3 manage.py collectstatic --noinput || echo "⚠️ Collectstatic partiel"

# 5. Redémarrage des services
echo "🔄 Redémarrage services..."
pkill -f manage.py
sleep 3
python3 manage.py runserver 0.0.0.0:8000 &

# 6. Vérification
sleep 5
echo "✅ Déploiement terminé"
echo "🌐 Test: curl -I http://localhost:8000/"
curl -I http://localhost:8000/ || echo "⚠️ Service non accessible immédiatement"
'''
    
    try:
        with open('deploy.sh', 'w', encoding='utf-8') as f:
            f.write(deploy_script)
        
        os.chmod('deploy.sh', 0o755)
        print("✅ Script deploy.sh créé")
        return True
        
    except Exception as e:
        print(f"❌ Erreur création script deploy: {e}")
        return False

def create_local_sync_script():
    """Crée un script de synchronisation avec le PC local"""
    
    print("\n💻 SCRIPT SYNCHRONISATION PC")
    print("============================")
    
    # Créer le script pour le serveur
    sync_script = '''#!/bin/bash
# Synchronisation avec PC local Windows
# Usage: ./sync_to_local.sh

LOCAL_PATH="/mnt/c/martial_hub_django/martialcomp"
DATE=$(date +"%Y%m%d_%H%M%S")

echo "💻 SYNCHRONISATION VERS PC LOCAL"
echo "================================"

if [ ! -d "$LOCAL_PATH" ]; then
    echo "❌ Répertoire PC local non accessible: $LOCAL_PATH"
    echo "   Vérifiez que le disque C: est monté"
    exit 1
fi

# Créer sauvegarde sur PC avant sync
if [ -d "$LOCAL_PATH" ]; then
    echo "💾 Sauvegarde version PC locale..."
    cp -r "$LOCAL_PATH" "${LOCAL_PATH}_backup_$DATE" 2>/dev/null || echo "⚠️ Pas de version précédente"
fi

# Synchroniser les fichiers essentiels
echo "🔄 Synchronisation fichiers..."

rsync -av --exclude='venv/' \
          --exclude='__pycache__/' \
          --exclude='*.pyc' \
          --exclude='*.log' \
          --exclude='media/uploads/' \
          --exclude='.git/' \
          ./ "$LOCAL_PATH/"

echo "✅ Synchronisation terminée vers: $LOCAL_PATH"
'''
    
    try:
        with open('sync_to_local.sh', 'w', encoding='utf-8') as f:
            f.write(sync_script)
        
        os.chmod('sync_to_local.sh', 0o755)
        print("✅ Script sync_to_local.sh créé")
        
        # Créer aussi le script pour Windows (PowerShell)
        windows_sync = '''# Script PowerShell pour synchronisation depuis Windows
# Usage: .\sync_from_server.ps1

$SERVER = "root@212.227.78.104"
$REMOTE_PATH = "/var/www/vhosts/martialcomp.com/httpdocs"
$LOCAL_PATH = "C:\\martial_hub_django\\martialcomp"
$DATE = Get-Date -Format "yyyyMMdd_HHmmss"

Write-Host "💻 SYNCHRONISATION DEPUIS SERVEUR" -ForegroundColor Green
Write-Host "=================================="

# Créer sauvegarde locale
if (Test-Path $LOCAL_PATH) {
    Write-Host "💾 Sauvegarde version locale..."
    Copy-Item -Recurse $LOCAL_PATH "${LOCAL_PATH}_backup_$DATE" -ErrorAction SilentlyContinue
}

# Synchronisation avec rsync (WSL nécessaire)
Write-Host "🔄 Synchronisation fichiers..."
wsl rsync -av --exclude='venv/' --exclude='__pycache__/' --exclude='*.pyc' --exclude='*.log' $SERVER:$REMOTE_PATH/ $LOCAL_PATH/

Write-Host "✅ Synchronisation terminée vers: $LOCAL_PATH" -ForegroundColor Green
'''
        
        # Écrire le script Windows dans le répertoire local si accessible
        local_pc_path = '/mnt/c/martial_hub_django'
        if os.path.exists(local_pc_path):
            with open(f'{local_pc_path}/sync_from_server.ps1', 'w', encoding='utf-8') as f:
                f.write(windows_sync)
            print("✅ Script Windows sync_from_server.ps1 créé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur création scripts sync: {e}")
        return False

if __name__ == "__main__":
    print("🏗️ MISE EN PLACE GESTION PRODUCTION PROPRE")
    print("==========================================")
    print(f"📂 Répertoire: {os.getcwd()}")
    
    print("\n🎯 OBJECTIFS:")
    print("   📁 Nettoyer les fichiers temporaires")
    print("   🔧 Configurer Git/GitHub")
    print("   💾 Système de sauvegarde automatique")
    print("   🚀 Workflow de déploiement")
    print("   💻 Synchronisation PC local")
    
    # Exécution des étapes
    success1 = cleanup_production_files()
    success2 = setup_gitignore()
    success3 = initialize_git_repo()
    success4 = create_backup_script()
    success5 = create_deployment_workflow()
    success6 = create_local_sync_script()
    
    print(f"\n📊 RÉSUMÉ CONFIGURATION:")
    print(f"   {'✅' if success1 else '❌'} Nettoyage production")
    print(f"   {'✅' if success2 else '❌'} .gitignore configuré")
    print(f"   {'✅' if success3 else '❌'} Git initialisé")
    print(f"   {'✅' if success4 else '❌'} Script backup")
    print(f"   {'✅' if success5 else '❌'} Workflow déploiement")
    print(f"   {'✅' if success6 else '❌'} Synchronisation PC")
    
    if all([success1, success2, success3, success4, success5, success6]):
        print("\n🎉 CONFIGURATION TERMINÉE!")
        
        print("\n✅ OUTILS DISPONIBLES:")
        print("   💾 ./backup.sh [message] - Sauvegarde complète")
        print("   🚀 ./deploy.sh [env] - Déploiement")
        print("   💻 ./sync_to_local.sh - Sync vers PC")
        print("   🔧 git add/commit/push - Versioning")
        
        print("\n📋 WORKFLOW RECOMMANDÉ:")
        print("   1. Avant modification: ./backup.sh 'Pre-change backup'")
        print("   2. Faire les modifications")
        print("   3. Tester localement")
        print("   4. git add . && git commit -m 'Description'")
        print("   5. ./deploy.sh production")
        print("   6. ./sync_to_local.sh (backup PC)")
        
        print("\n🌐 GITHUB SETUP (manuel):")
        print("   1. Créer repo sur github.com")
        print("   2. git remote add origin https://github.com/user/martialcomp.git")
        print("   3. git branch -M main")
        print("   4. git push -u origin main")
        
    else:
        print("\n⚠️ CONFIGURATION PARTIELLE")
        print("   Certains outils peuvent ne pas fonctionner")
    
    sys.exit(0 if all([success1, success2, success3, success4, success5, success6]) else 1)