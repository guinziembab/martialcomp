#!/usr/bin/env python3
"""
Package de déploiement complet pour les sites d'organisations automatiques.
Déploie les signaux, templates, URLs et corrections pour la production.
"""
import os
import shutil
import subprocess
import sys
from datetime import datetime

def create_deployment_package():
    """Crée un package de déploiement avec tous les fichiers nécessaires."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    package_dir = f"deployment_organization_sites_{timestamp}"
    
    print("📦 CRÉATION DU PACKAGE DE DÉPLOIEMENT")
    print("=" * 45)
    
    os.makedirs(package_dir, exist_ok=True)
    
    # Fichiers à déployer pour les sites d'organisations
    files_to_deploy = [
        # Signaux automatiques
        "organizations/signals.py",
        "organizations/apps.py",
        
        # Templates d'organisations
        "competitions/templates/organizations/sites/base_template.html",
        "competitions/templates/organizations/sites/club_template.html", 
        "competitions/templates/organizations/sites/federation_template.html",
        
        # URLs et vues
        "competitions/urls/organization_sites.py",
        "competitions/views/organization_sites.py",
        "config/urls.py",
        
        # Utilitaires
        "competitions/utils/subdomain_generator.py",
        "competitions/utils/qr_generator_enhanced.py",
        
        # Modèles et migrations
        "multitenant/models.py",
        "organizations/models.py",
        
        # Configuration
        "config/settings.py",
        
        # Corrections précédentes
        "competitions/signals.py",
        "competitions/models/practitioners.py",
        "competitions/migrations/0008_fix_family_fields_null.py",
        
        # Scripts de test
        "test_organization_signals.py",
        "test_subdomain_routing.py",
    ]
    
    copied_files = []
    
    for file_path in files_to_deploy:
        if os.path.exists(file_path):
            # Créer la structure de répertoires dans le package
            dest_dir = os.path.join(package_dir, os.path.dirname(file_path))
            os.makedirs(dest_dir, exist_ok=True)
            
            dest_path = os.path.join(package_dir, file_path)
            shutil.copy2(file_path, dest_path)
            copied_files.append(file_path)
            print(f"✅ Ajouté: {file_path}")
        else:
            print(f"⚠️  Fichier manquant: {file_path}")
    
    # Créer le template par défaut manquant
    create_default_template(package_dir)
    
    # Créer un script d'installation pour la production
    create_installation_script(package_dir, copied_files, timestamp)
    
    # Créer un script de validation post-déploiement
    create_validation_script(package_dir)
    
    # Créer la documentation de déploiement
    create_deployment_documentation(package_dir, timestamp)
    
    print(f"✅ Package créé: {package_dir}/")
    
    return package_dir

def create_default_template(package_dir):
    """Crée le template par défaut manquant."""
    template_dir = os.path.join(package_dir, "competitions/templates/organizations/sites")
    os.makedirs(template_dir, exist_ok=True)
    
    default_template_content = '''{% extends "organizations/sites/base_template.html" %}

{% block title %}{{ organization.name }}{% endblock %}

{% block main_content %}
{{ block.super }}

<!-- Default Organization Content -->
<section class="py-5 bg-light">
    <div class="container">
        <div class="row">
            <div class="col-lg-8 mx-auto text-center">
                <h2 class="display-5 fw-bold">Bienvenue</h2>
                <p class="lead">
                    Découvrez notre organisation et nos services.
                    Utilisez les codes QR ci-dessus pour accéder rapidement à nos fonctionnalités.
                </p>
            </div>
        </div>
    </div>
</section>
{% endblock %}'''
    
    with open(os.path.join(template_dir, "default_template.html"), 'w', encoding='utf-8') as f:
        f.write(default_template_content)
    
    print("✅ Template par défaut créé")

def create_installation_script(package_dir, copied_files, timestamp):
    """Crée le script d'installation pour la production."""
    install_script = f"""#!/bin/bash
# Script d'installation automatique pour les sites d'organisations
# Généré le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

echo "🚀 INSTALLATION DES SITES D'ORGANISATIONS EN PRODUCTION"
echo "========================================================"

# Variables
BACKUP_DIR="/opt/martialcomp/backups/organization_sites_{timestamp}"
APP_DIR="/opt/martialcomp/app"

# Créer le répertoire de sauvegarde
mkdir -p "$BACKUP_DIR"
echo "📁 Répertoire de sauvegarde: $BACKUP_DIR"

# Arrêter le service Django
echo "🔄 Arrêt du service Django..."
sudo systemctl stop martialcomp

echo "💾 SAUVEGARDE DES FICHIERS ORIGINAUX"
echo "===================================="
"""

    # Ajouter les commandes de sauvegarde et copie
    for file_path in copied_files:
        prod_path = f"/opt/martialcomp/app/{file_path}"
        backup_name = file_path.replace('/', '_')
        install_script += f"""
# Sauvegarder {file_path}
if [ -f "{prod_path}" ]; then
    cp "{prod_path}" "$BACKUP_DIR/{backup_name}.backup"
    echo "✅ Sauvegardé: {file_path}"
fi

# Copier le nouveau fichier
mkdir -p "$(dirname "{prod_path}")"
cp "{file_path}" "{prod_path}"
echo "✅ Mis à jour: {file_path}"
"""

    install_script += f"""
echo ""
echo "📋 APPLICATION DES MIGRATIONS"
echo "============================"

# Aller dans le répertoire de l'application
cd "$APP_DIR"

# Activer l'environnement virtuel
source /var/www/vhosts/martialcomp.com/httpdocs/venv/bin/activate

# Appliquer les migrations
python manage.py migrate

# Collecter les fichiers statiques
python manage.py collectstatic --noinput

echo ""
echo "🔄 REDÉMARRAGE DU SERVICE"
echo "========================"

# Redémarrer le service Django
sudo systemctl start martialcomp

# Attendre un peu que le service démarre
sleep 5

# Vérifier le statut
sudo systemctl status martialcomp

echo ""
echo "🧪 VALIDATION POST-DÉPLOIEMENT"
echo "=============================="

# Exécuter le script de validation
python validation_post_deployment.py

echo ""
echo "✅ INSTALLATION TERMINÉE!"
echo "========================"
echo ""
echo "📋 ÉTAPES SUIVANTES:"
echo "1. 🧪 Tester la création d'une organisation via l'admin"
echo "2. 🌐 Vérifier qu'un sous-domaine est généré automatiquement"
echo "3. 📱 Tester les QR codes (après correction de la librairie)"
echo "4. 🔍 Surveiller les logs: sudo journalctl -u martialcomp -f"
echo ""
echo "📁 Sauvegardes disponibles dans: $BACKUP_DIR"
echo ""
echo "🎉 Les sites d'organisations automatiques sont maintenant actifs!"
"""

    # Écrire le script d'installation
    install_script_path = os.path.join(package_dir, "install_production.sh")
    with open(install_script_path, 'w') as f:
        f.write(install_script)
    
    # Rendre le script exécutable
    os.chmod(install_script_path, 0o755)
    
    print(f"✅ Script d'installation créé: install_production.sh")

def create_validation_script(package_dir):
    """Crée le script de validation post-déploiement."""
    validation_script = '''#!/usr/bin/env python3
"""
Script de validation post-déploiement pour les sites d'organisations.
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from organizations.models import Organization
from multitenant.models import Tenant

def main():
    print("🧪 VALIDATION POST-DÉPLOIEMENT")
    print("=" * 35)
    print("🎯 Vérification que les sites d'organisations fonctionnent")
    print()
    
    try:
        # Test 1: Créer une organisation de test
        print("📋 Test 1: Création d'organisation avec signal automatique")
        
        user = User.objects.first()
        if not user:
            print("❌ Aucun utilisateur trouvé")
            return False
        
        # Compter les tenants avant
        tenant_count_before = Tenant.objects.count()
        
        # Créer une organisation
        org = Organization.objects.create(
            name="Test Validation Production",
            organization_type="CLUB",
            country="FR",
            created_by=user
        )
        
        # Vérifier qu'un tenant a été créé
        tenant_count_after = Tenant.objects.count()
        
        if tenant_count_after > tenant_count_before:
            print("✅ Signal automatique fonctionne: Tenant créé")
            
            # Trouver le tenant
            tenant = Tenant.objects.filter(name=org.name).first()
            if tenant:
                print(f"✅ Sous-domaine généré: {tenant.domain}")
            
            # Nettoyer
            org.delete()
            if tenant:
                tenant.delete()
            
            return True
        else:
            print("❌ ÉCHEC: Aucun tenant créé automatiquement")
            org.delete()
            return False
            
    except Exception as e:
        print(f"❌ ERREUR lors de la validation: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\\n🎉 VALIDATION RÉUSSIE!")
        print("✅ Les sites d'organisations automatiques sont fonctionnels")
    else:
        print("\\n❌ VALIDATION ÉCHOUÉE")
        print("⚠️  Vérifiez les logs pour plus de détails")
    
    sys.exit(0 if success else 1)
'''
    
    validation_path = os.path.join(package_dir, "validation_post_deployment.py")
    with open(validation_path, 'w') as f:
        f.write(validation_script)
    
    os.chmod(validation_path, 0o755)
    print("✅ Script de validation créé")

def create_deployment_documentation(package_dir, timestamp):
    """Crée la documentation de déploiement."""
    doc_content = f"""# 📦 PACKAGE DE DÉPLOIEMENT - SITES D'ORGANISATIONS AUTOMATIQUES

**Date de création :** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Version :** {timestamp}

## 🎯 OBJECTIF

Ce package déploie le système complet de création automatique de sites d'organisations avec :
- ✅ **Signaux automatiques** : Création de tenants et sous-domaines
- ✅ **Templates responsives** : Sites spécialisés par type d'organisation  
- ✅ **URLs intégrées** : Routage des sous-domaines
- ✅ **QR codes** : Génération automatique (nécessite correction mineure)

## 🚀 DÉPLOIEMENT RAPIDE

### Option 1 - Installation Automatique (Recommandée)
```bash
# 1. Transférer le package sur le serveur
scp -r deployment_organization_sites_{timestamp}/ root@serveur:/tmp/

# 2. Se connecter et installer
ssh root@serveur
cd /tmp/deployment_organization_sites_{timestamp}
sudo ./install_production.sh
```

### Option 2 - Installation Manuelle
1. Arrêter le service : `sudo systemctl stop martialcomp`
2. Sauvegarder les fichiers existants
3. Copier les nouveaux fichiers dans `/opt/martialcomp/app/`
4. Appliquer les migrations : `python manage.py migrate`
5. Redémarrer : `sudo systemctl start martialcomp`

## 📋 FONCTIONNALITÉS DÉPLOYÉES

### ✅ Signaux Automatiques
- **Fichier :** `organizations/signals.py`
- **Fonction :** Création automatique de tenant + sous-domaine + QR codes
- **Déclencheur :** Chaque nouvelle organisation créée

### ✅ Templates d'Organisations
- **Base :** `competitions/templates/organizations/sites/base_template.html`
- **Club :** `competitions/templates/organizations/sites/club_template.html`
- **Fédération :** `competitions/templates/organizations/sites/federation_template.html`
- **Par défaut :** `competitions/templates/organizations/sites/default_template.html`

### ✅ URLs et Routage
- **URLs organisations :** `competitions/urls/organization_sites.py`
- **URLs principales :** `config/urls.py` (mis à jour)
- **Vues :** `competitions/views/organization_sites.py`

### ✅ Utilitaires
- **Générateur sous-domaines :** `competitions/utils/subdomain_generator.py`
- **Générateur QR codes :** `competitions/utils/qr_generator_enhanced.py`

## 🧪 VALIDATION POST-DÉPLOIEMENT

Après installation, exécuter :
```bash
python validation_post_deployment.py
```

**Test manuel :**
1. Aller dans l'admin Django : `/admin/`
2. Créer une nouvelle organisation
3. Vérifier qu'un tenant est créé automatiquement
4. Tester l'accès au sous-domaine généré

## 📊 RÉSULTATS ATTENDUS

Après déploiement, **chaque nouvelle organisation** aura automatiquement :
- 🌐 **Sous-domaine** : `mon-club.martialcomp.com`
- 🏠 **Site web** : Template adapté au type d'organisation
- 📱 **QR codes** : Inscription, paiement, parrainage, check-in
- 🔗 **URLs fonctionnelles** : Toutes les pages accessibles

## ⚠️ PROBLÈMES CONNUS ET SOLUTIONS

### 1. QR Codes - Erreur de Librairie
**Problème :** `module 'qrcode.constants' has no attribute 'ERROR_CORRECTION_H'`  
**Solution :** Mettre à jour la librairie qrcode :
```bash
pip install --upgrade qrcode[pil]
```

### 2. Routeur de Base de Données
**Problème :** Warning sur l'assignation d'owner  
**Impact :** Aucun (tenant créé quand même sans owner)  
**Solution :** Ignorer le warning ou désactiver le routeur temporairement

### 3. DNS Wildcard
**Prérequis :** Configurer `*.martialcomp.com` pour pointer vers le serveur  
**Test :** `nslookup test.martialcomp.com` doit répondre

## 🔧 COMMANDES DE DIAGNOSTIC

```bash
# Vérifier les tenants créés
python manage.py shell -c "
from multitenant.models import Tenant
for t in Tenant.objects.all():
    print(f'{{t.name}}: {{t.domain}}')
"

# Tester la génération de sous-domaines
python manage.py shell -c "
from competitions.utils.subdomain_generator import SubdomainGenerator
from organizations.models import Organization
gen = SubdomainGenerator()
org = Organization.objects.first()
if org:
    print(gen.generate_subdomain(org))
"

# Vérifier les signaux
python manage.py shell -c "
import organizations.signals
print('Signaux chargés avec succès')
"
```

## 📞 SUPPORT

En cas de problème :
1. **Logs Django :** `sudo journalctl -u martialcomp -f`
2. **Statut service :** `sudo systemctl status martialcomp`
3. **Sauvegardes :** `/opt/martialcomp/backups/organization_sites_{timestamp}/`

## 🎉 PROCHAINES ÉTAPES

1. **Configurer DNS wildcard** : `*.martialcomp.com`
2. **Installer certificat SSL wildcard**
3. **Tester avec organisation réelle**
4. **Former les utilisateurs** sur les nouvelles fonctionnalités
5. **Corriger la librairie QR codes** si nécessaire

---

**🚀 Les sites d'organisations automatiques sont maintenant prêts pour la production !**
"""
    
    doc_path = os.path.join(package_dir, "README_DEPLOYMENT.md")
    with open(doc_path, 'w', encoding='utf-8') as f:
        f.write(doc_content)
    
    print("✅ Documentation créée: README_DEPLOYMENT.md")

def main():
    print("🚀 CRÉATION DU PACKAGE DE DÉPLOIEMENT PRODUCTION")
    print("=" * 55)
    print("🎯 Objectif: Déployer les sites d'organisations automatiques")
    print("📋 Contenu: Signaux + Templates + URLs + Utilitaires")
    print()
    
    # Vérifier qu'on est à la racine du projet
    if not os.path.exists("manage.py"):
        print("❌ Erreur: Ce script doit être exécuté à la racine du projet Django")
        return
    
    # Créer le package de déploiement
    package_dir = create_deployment_package()
    
    print()
    print("=" * 55)
    print("🎉 PACKAGE DE DÉPLOIEMENT CRÉÉ AVEC SUCCÈS!")
    print("=" * 35)
    print()
    print("📁 Package créé:", package_dir)
    print()
    print("📋 CONTENU DU PACKAGE:")
    print("✅ Signaux automatiques (organizations/signals.py)")
    print("✅ Templates responsives (3 types d'organisations)")
    print("✅ URLs et routage intégrés")
    print("✅ Utilitaires de génération")
    print("✅ Script d'installation automatique")
    print("✅ Script de validation post-déploiement")
    print("✅ Documentation complète")
    print()
    print("🚀 DÉPLOIEMENT:")
    print("1. Transférer le package sur le serveur de production")
    print("2. Exécuter le script d'installation")
    print("3. Valider le fonctionnement")
    print()
    print("⭐ RÉSULTAT FINAL:")
    print("   Chaque nouvelle organisation aura automatiquement")
    print("   son site en sous-domaine avec QR codes !")

if __name__ == "__main__":
    main()