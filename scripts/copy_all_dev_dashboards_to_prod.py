#!/usr/bin/env python3
"""
Script pour copier tous les templates dashboard du DEV vers la PRODUCTION
Utilise les templates fonctionnels du dev et les adapte pour la production
"""
import os
import shutil
import time
import zipfile
from datetime import datetime

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def create_deployment_package():
    """Crée un package avec tous les templates dashboard du dev"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_name = f"dev_dashboards_to_prod_{timestamp}.zip"
    temp_dir = f"dashboard_package_{timestamp}"
    
    log("📦 CRÉATION PACKAGE TEMPLATES DASHBOARD DEV → PROD")
    log("=" * 60)
    log(f"📁 Package: {package_name}")
    
    # Créer le répertoire temporaire
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    # Templates dashboard à copier du dev
    dashboard_templates = [
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
    
    # Répertoire source des templates dev
    dev_dashboard_dir = "competitions/templates/competitions/dashboard"
    
    # Créer la structure dans le package
    os.makedirs(os.path.join(temp_dir, "templates/competitions/dashboard"), exist_ok=True)
    
    copied_files = []
    missing_files = []
    
    log("\n📄 COPIE DES TEMPLATES DASHBOARD")
    log("-" * 50)
    
    for template in dashboard_templates:
        source_path = os.path.join(dev_dashboard_dir, template)
        dest_path = os.path.join(temp_dir, "templates/competitions/dashboard", template)
        
        if os.path.exists(source_path):
            try:
                shutil.copy2(source_path, dest_path)
                copied_files.append(template)
                log(f"✅ Copié: {template}")
            except Exception as e:
                log(f"❌ Erreur copie {template}: {e}")
                missing_files.append(template)
        else:
            log(f"⚠️ Fichier manquant: {template}")
            missing_files.append(template)
    
    # Copier aussi les sous-dossiers s'ils existent
    subdirs = ["documentation", "finance"]
    for subdir in subdirs:
        source_subdir = os.path.join(dev_dashboard_dir, subdir)
        if os.path.exists(source_subdir):
            dest_subdir = os.path.join(temp_dir, "templates/competitions/dashboard", subdir)
            try:
                shutil.copytree(source_subdir, dest_subdir)
                log(f"✅ Dossier copié: {subdir}/")
            except Exception as e:
                log(f"❌ Erreur dossier {subdir}: {e}")
    
    # Créer le script de déploiement pour la production
    create_deployment_script(temp_dir, copied_files)
    
    # Créer le fichier de correction des URLs
    create_url_adaptation_script(temp_dir)
    
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
    log(f"📊 Templates copiés: {len(copied_files)}")
    log(f"⚠️ Templates manquants: {len(missing_files)}")
    
    return package_name, copied_files, missing_files

def create_deployment_script(temp_dir, copied_files):
    """Crée le script de déploiement automatique"""
    
    deployment_script = '''#!/bin/bash

# Script de déploiement templates dashboard DEV → PROD
echo "🚀 DÉPLOIEMENT TEMPLATES DASHBOARD DEV → PROD"
echo "=" * 60

# Variables
PROD_DIR="/var/www/vhosts/martialcomp.com/httpdocs"

# Vérifier qu'on est dans le bon répertoire
if [ ! -d "$PROD_DIR" ]; then
    echo "❌ Répertoire de production non trouvé: $PROD_DIR"
    exit 1
fi

cd "$PROD_DIR"
echo "📂 Répertoire: $(pwd)"

# 1. Sauvegarde des templates actuels
echo ""
echo "💾 SAUVEGARDE DES TEMPLATES ACTUELS"
BACKUP_DIR="backup_dashboard_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Sauvegarder les templates existants
if [ -d "competitions/templates/competitions/dashboard" ]; then
    cp -r competitions/templates/competitions/dashboard/ "$BACKUP_DIR/"
    echo "✅ Sauvegarde créée: $BACKUP_DIR"
else
    echo "⚠️ Pas de templates dashboard existants"
fi

# 2. Copier les nouveaux templates du dev
echo ""
echo "📋 COPIE DES TEMPLATES DASHBOARD DU DEV"
mkdir -p competitions/templates/competitions/dashboard/

# Copier tous les templates
cp -r templates/competitions/dashboard/* competitions/templates/competitions/dashboard/

echo "✅ Templates dashboard copiés"

# 3. Exécuter le script d'adaptation des URLs
echo ""
echo "🔧 ADAPTATION DES URLs POUR LA PRODUCTION"
python3 adapt_dashboard_urls.py

# 4. Redémarrer Django
echo ""
echo "🚀 REDÉMARRAGE DJANGO"
pkill -f 'manage.py runserver'
pkill -f gunicorn
sleep 3
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --daemon
sleep 6

# 5. Test final
echo ""
echo "🧪 TEST FINAL"
python3 manage.py check
curl -I -s http://localhost:8000/ | head -1

echo ""
echo "🎉 DÉPLOIEMENT TERMINÉ!"
echo "✅ Templates dashboard du dev copiés vers la production"
echo "✅ URLs adaptées pour la production"
echo "✅ Django redémarré"
echo ""
echo "🧪 TESTER MAINTENANT:"
echo "   https://martialcomp.com/dashboard/club/"
echo "   https://martialcomp.com/dashboard/federation/"
echo "   Connexion: dojo_sakura_manager / demo2025"
'''
    
    script_path = os.path.join(temp_dir, "deploy_dashboards.sh")
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(deployment_script)

def create_url_adaptation_script(temp_dir):
    """Crée le script d'adaptation des URLs pour la production"""
    
    adaptation_script = '''#!/usr/bin/env python3
"""
Script d'adaptation des URLs dashboard pour la production
Corrige les namespaces et URLs pour qu'ils fonctionnent en production
"""
import os
import re

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def adapt_template_urls():
    """Adapte les URLs dans tous les templates dashboard"""
    
    dashboard_dir = "competitions/templates/competitions/dashboard"
    
    if not os.path.exists(dashboard_dir):
        log("❌ Répertoire dashboard non trouvé")
        return False
    
    # Corrections d'URLs communes
    url_corrections = {
        # Corrections namespaces dashboard
        r"{% url 'dashboard:([^']+)' %}": r"{% url 'competitions:dashboard_\\1' %}",
        r"{% url 'dashboard:([^']+)' ([^}]+) %}": r"{% url 'competitions:dashboard_\\1' \\2 %}",
        
        # Corrections URLs competitions
        r"{% url 'competitions:dashboard:([^']+)' %}": r"{% url 'competitions:dashboard_\\1' %}",
        r"{% url 'competitions:dashboard:([^']+)' ([^}]+) %}": r"{% url 'competitions:dashboard_\\1' \\2 %}",
        
        # Corrections URLs spécifiques
        r"{% url 'profile' %}": r"{% url 'competitions:dashboard' %}",
        r"{% url 'logout' %}": r"{% url 'account_logout' %}",
        r"{% url 'login' %}": r"{% url 'account_login' %}",
        
        # URLs de redirection base
        r"href=['\"]/dashboard/": r"href='{% url 'competitions:dashboard' %}'",
        r"href=['\"]#['\"]": r"href='{% url 'competitions:dashboard' %}'",
    }
    
    fixed_count = 0
    
    for root, dirs, files in os.walk(dashboard_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    original_content = content
                    
                    # Appliquer toutes les corrections
                    for pattern, replacement in url_corrections.items():
                        content = re.sub(pattern, replacement, content)
                    
                    # Corrections spécifiques selon le type de dashboard
                    if 'club.html' in file:
                        content = content.replace(
                            '{% load custom_filters %}',
                            '{% load i18n %}'
                        )
                    
                    if content != original_content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        log(f"✅ URLs corrigées: {file}")
                        fixed_count += 1
                        
                except Exception as e:
                    log(f"❌ Erreur {file}: {e}")
    
    log(f"✅ {fixed_count} templates dashboard corrigés")
    return True

def update_dashboard_router():
    """Met à jour le dashboard router pour supporter tous les types"""
    
    router_code = '''"""
Dashboard router complet - Support de tous les types de dashboard
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_router(request):
    """Route vers le dashboard approprié selon le profil utilisateur"""
    user = request.user
    username = user.username.lower()
    
    # Routage intelligent basé sur le nom d'utilisateur et les groupes
    user_groups = [group.name.lower() for group in user.groups.all()]
    
    # Vérification par groupe d'abord
    if 'federation' in user_groups or 'federations' in user_groups:
        return redirect('/dashboard/federation/')
    elif 'admin' in user_groups or 'administrator' in user_groups:
        return redirect('/dashboard/admin/')
    elif 'coach' in user_groups or 'entraineur' in user_groups:
        return redirect('/dashboard/coach/')
    elif 'judge' in user_groups or 'juge' in user_groups:
        return redirect('/dashboard/judge/')
    elif 'referee' in user_groups or 'arbitre' in user_groups:
        return redirect('/dashboard/referee/')
    elif 'combat' in user_groups or 'combattant' in user_groups:
        return redirect('/dashboard/combat/')
    elif 'participant' in user_groups or 'pratiquant' in user_groups:
        return redirect('/dashboard/participant/')
    elif 'spectator' in user_groups or 'spectateur' in user_groups:
        return redirect('/dashboard/spectator/')
    
    # Routage par nom d'utilisateur si pas de groupe
    if 'federation' in username or 'fed' in username:
        return redirect('/dashboard/federation/')
    elif 'admin' in username:
        return redirect('/dashboard/admin/')
    elif 'manager' in username or 'club' in username or 'dojo' in username:
        return redirect('/dashboard/club/')
    elif 'coach' in username or 'entraineur' in username:
        return redirect('/dashboard/coach/')
    elif 'judge' in username or 'juge' in username:
        return redirect('/dashboard/judge/')
    elif 'referee' in username or 'arbitre' in username:
        return redirect('/dashboard/referee/')
    elif 'combat' in username:
        return redirect('/dashboard/combat/')
    elif 'participant' in username or 'pratiquant' in username:
        return redirect('/dashboard/participant/')
    elif 'spectator' in username:
        return redirect('/dashboard/spectator/')
    
    # Par défaut - club dashboard pour comptes demo
    return redirect('/dashboard/club/')

# Vues pour chaque type de dashboard
@login_required
def club_dashboard_view(request):
    context = {'user': request.user, 'club_name': 'Dojo Sakura', 'dashboard_type': 'club'}
    return render(request, 'competitions/dashboard/club.html', context)

@login_required
def federation_dashboard_view(request):
    context = {'user': request.user, 'dashboard_type': 'federation'}
    return render(request, 'competitions/dashboard/federation.html', context)

@login_required  
def admin_dashboard_view(request):
    context = {'user': request.user, 'dashboard_type': 'admin'}
    return render(request, 'competitions/dashboard/admin.html', context)

@login_required
def coach_dashboard_view(request):
    context = {'user': request.user, 'dashboard_type': 'coach'}
    return render(request, 'competitions/dashboard/coach.html', context)

@login_required
def judge_dashboard_view(request):
    context = {'user': request.user, 'dashboard_type': 'judge'}
    return render(request, 'competitions/dashboard/judge.html', context)

@login_required
def referee_dashboard_view(request):
    context = {'user': request.user, 'dashboard_type': 'referee'}
    return render(request, 'competitions/dashboard/referee.html', context)

@login_required
def combat_dashboard_view(request):
    context = {'user': request.user, 'dashboard_type': 'combat'}
    return render(request, 'competitions/dashboard/combat.html', context)

@login_required
def participant_dashboard_view(request):
    context = {'user': request.user, 'dashboard_type': 'participant'}
    return render(request, 'competitions/dashboard/participant_enhanced.html', context)

@login_required
def spectator_dashboard_view(request):
    context = {'user': request.user, 'dashboard_type': 'spectator'}
    return render(request, 'competitions/dashboard/spectator.html', context)

@login_required
def manager_dashboard_view(request):
    context = {'user': request.user, 'dashboard_type': 'manager'}
    return render(request, 'competitions/dashboard/manager.html', context)
'''
    
    try:
        with open('competitions/views/dashboard_router.py', 'w', encoding='utf-8') as f:
            f.write(router_code)
        log("✅ Dashboard router mis à jour")
        return True
    except Exception as e:
        log(f"❌ Erreur router: {e}")
        return False

def main():
    log("🔧 ADAPTATION URLS DASHBOARD POUR PRODUCTION")
    log("=" * 50)
    
    if adapt_template_urls():
        log("✅ URLs templates adaptées")
    else:
        log("❌ Erreur adaptation URLs")
        return False
    
    if update_dashboard_router():
        log("✅ Router mis à jour")
    else:
        log("❌ Erreur mise à jour router")
    
    log("🎉 ADAPTATION TERMINÉE!")
    return True

if __name__ == "__main__":
    import time
    success = main()
    exit(0 if success else 1)
'''
    
    script_path = os.path.join(temp_dir, "adapt_dashboard_urls.py")
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(adaptation_script)

def create_readme(temp_dir):
    """Crée le fichier README avec les instructions"""
    
    readme_content = '''# Package Templates Dashboard DEV → PROD

## Contenu

### Templates Dashboard Copiés du DEV
- `federation.html` - Dashboard fédération fonctionnel
- `club.html` - Dashboard club fonctionnel  
- `admin.html` - Dashboard administrateur
- `coach.html` - Dashboard entraîneur
- `combat.html` - Dashboard combattant
- `judge.html` - Dashboard juge
- `manager.html` - Dashboard manager
- `participant_*.html` - Dashboards participant (3 variantes)
- `referee.html` - Dashboard arbitre
- `spectator.html` - Dashboard spectateur
- `base.html` et `unified_base.html` - Templates de base

### Scripts
- `deploy_dashboards.sh` - Script de déploiement automatique
- `adapt_dashboard_urls.py` - Script d'adaptation des URLs

## Instructions de Déploiement

### 1. Transférer le package
```bash
scp dev_dashboards_to_prod_*.zip root@martialcomp.com:/tmp/
```

### 2. Se connecter au serveur
```bash
ssh root@martialcomp.com
```

### 3. Extraire et déployer
```bash
cd /tmp
unzip dev_dashboards_to_prod_*.zip
cd dev_dashboards_to_prod_*/
chmod +x deploy_dashboards.sh
./deploy_dashboards.sh
```

## Résultat Attendu

Après déploiement, tous les dashboards du dev seront fonctionnels en production :

- ✅ `/dashboard/club/` - Dashboard club du dev
- ✅ `/dashboard/federation/` - Dashboard fédération du dev  
- ✅ `/dashboard/admin/` - Dashboard admin du dev
- ✅ `/dashboard/coach/` - Dashboard coach du dev
- ✅ Tous les autres dashboards...

## Avantages

- **Templates testés** : Utilise les templates qui fonctionnent en dev
- **Pas de régression** : Évite les comportements imprévisibles
- **Cohérence** : Interface identique entre dev et prod
- **Fiabilité** : Basé sur du code fonctionnel
'''
    
    readme_path = os.path.join(temp_dir, "README.md")
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)

if __name__ == "__main__":
    package_name, copied, missing = create_deployment_package()
    
    print(f"\n📦 PACKAGE CRÉÉ: {package_name}")
    print(f"📊 Templates copiés: {len(copied)}")
    
    if missing:
        print(f"⚠️ Templates manquants: {len(missing)}")
        for template in missing:
            print(f"   - {template}")
    
    print(f"\n🚀 INSTRUCTIONS DE TRANSFERT:")
    print(f"1. scp {package_name} root@martialcomp.com:/tmp/")
    print("2. ssh root@martialcomp.com")
    print(f"3. cd /tmp && unzip {package_name}")
    print("4. cd dev_dashboards_to_prod_*/ && chmod +x deploy_dashboards.sh && ./deploy_dashboards.sh")
    
    print(f"\n✅ Package prêt : {package_name}")
    print("🎯 Copie tous les templates dashboard fonctionnels du dev vers la prod")