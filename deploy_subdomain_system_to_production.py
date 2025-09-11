#!/usr/bin/env python3
"""
Déploiement du système de création automatique des sous-domaines vers la production
MartialComp - Correction production après validation dev
"""

import os
from pathlib import Path

def create_production_deployment_script():
    """Crée le script de déploiement pour la production."""
    
    script_content = '''#!/bin/bash
# Script de déploiement du système de sous-domaines automatiques
# MartialComp - Production

echo "🚀 DÉPLOIEMENT SYSTÈME SOUS-DOMAINES AUTOMATIQUES"
echo "================================================="
echo "✅ Système validé en développement"
echo

# Variables
PRODUCTION_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
BACKUP_DIR="$PRODUCTION_DIR/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

cd "$PRODUCTION_DIR"
source .venv/bin/activate

echo "1. SAUVEGARDE FICHIER SIGNALS ACTUEL..."
cp apps/competitions/signals.py "$BACKUP_DIR/signals_backup_$TIMESTAMP.py"
echo "✓ Sauvegarde créée"

echo
echo "2. RÉACTIVATION DU SIGNAL DE CRÉATION SOUS-DOMAINES..."

# Chercher et remplacer la ligne désactivée
sed -i 's/^# @receiver(post_save, sender=.organizations.Organization.)/@receiver(post_save, sender=.organizations.Organization.)/g' apps/competitions/signals.py
sed -i 's/def ensure_organization_site_creation_disabled/def ensure_organization_site_creation_enabled/g' apps/competitions/signals.py

# Vérifier la modification
if grep -q "@receiver(post_save, sender='organizations.Organization')" apps/competitions/signals.py; then
    echo "✅ Signal réactivé avec succès"
else
    echo "❌ Échec réactivation signal"
    echo "Restauration..."
    cp "$BACKUP_DIR/signals_backup_$TIMESTAMP.py" apps/competitions/signals.py
    exit 1
fi

echo
echo "3. VÉRIFICATION DJANGO..."
python manage.py check --settings=config.settings.production
if [ $? -eq 0 ]; then
    echo "✅ Configuration Django valide"
else
    echo "❌ Erreur configuration Django - Restauration"
    cp "$BACKUP_DIR/signals_backup_$TIMESTAMP.py" apps/competitions/signals.py
    exit 1
fi

echo
echo "4. CRÉATION SCRIPT DE TEST PRODUCTION..."
cat > test_production_subdomains.py << 'SCRIPT_EOF'
import os, sys, django
sys.path.insert(0, '/var/www/vhosts/martialcomp.com/httpdocs')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from apps.competitions.models import Club
from apps.organizations.models import Organization
from apps.multitenant.models import Tenant

def test_existing_clubs():
    """Test des clubs existants sans sous-domaines."""
    print("🔍 DIAGNOSTIC CLUBS PRODUCTION")
    print("=" * 40)
    
    clubs = Club.objects.filter(is_active=True)
    clubs_without_subdomains = []
    
    for club in clubs:
        if club.organization:
            tenant = Tenant.objects.filter(name__icontains=club.organization.name).first()
            if not tenant:
                clubs_without_subdomains.append(club)
                print(f"❌ {club.name} → Aucun sous-domaine")
            else:
                print(f"✅ {club.name} → {tenant.domain}")
        else:
            clubs_without_subdomains.append(club)
            print(f"⚠️ {club.name} → Aucune organisation")
    
    print(f"\\n📊 Clubs sans sous-domaine: {len(clubs_without_subdomains)}")
    
    # Proposition de correction pour BGA Test 1 spécifiquement
    bga_test = clubs_without_subdomains[0] if clubs_without_subdomains else None
    if bga_test and 'bga' in bga_test.name.lower():
        print(f"\\n🔧 CORRECTION BGA TEST 1...")
        try:
            if not bga_test.organization:
                bga_test.save()  # Déclenche création organisation
            
            if bga_test.organization:
                from apps.competitions.utils.subdomain_generator import create_organization_tenant
                tenant = create_organization_tenant(bga_test.organization)
                print(f"✅ Sous-domaine créé: {tenant.domain}")
            else:
                print("❌ Impossible de créer organisation")
        except Exception as e:
            print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    test_existing_clubs()
SCRIPT_EOF

echo "✅ Script de test créé"

echo
echo "5. REDÉMARRAGE SERVICES..."
sudo systemctl reload apache2
echo "✅ Apache redémarré"

echo
echo "6. TEST IMMÉDIAT..."
python test_production_subdomains.py

echo
echo "🎉 DÉPLOIEMENT TERMINÉ!"
echo
echo "ÉTAPES SUIVANTES:"
echo "1. Tester: python test_production_subdomains.py"
echo "2. Créer nouveau club pour vérifier automatisation"
echo "3. Vérifier: https://club_bgatest1.martialcomp.com/"
echo
echo "En cas de problème:"
echo "cp $BACKUP_DIR/signals_backup_$TIMESTAMP.py apps/competitions/signals.py"
echo "sudo systemctl reload apache2"
'''

    with open('/mnt/c/martial_hub_django/martialcomp/deploy_subdomains_to_production.sh', 'w') as f:
        f.write(script_content)
    
    print("✅ Script de déploiement production créé")
    print("📄 Fichier: deploy_subdomains_to_production.sh")

def create_production_fix_script():
    """Crée le script spécifique pour corriger BGA Test 1."""
    
    fix_script = '''#!/usr/bin/env python3
"""
Correction spécifique pour BGA Test 1 (club_bgatest1)
"""

import os, sys, django
sys.path.insert(0, '/var/www/vhosts/martialcomp.com/httpdocs')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from apps.competitions.models import Club
from apps.multitenant.models import Tenant

def fix_bga_test_subdomain():
    """Correction spécifique pour BGA Test 1."""
    print("🔧 CORRECTION BGA TEST 1")
    print("=" * 30)
    
    try:
        # Chercher le club BGA Test 1
        club = Club.objects.filter(name__icontains='bga').first()
        if not club:
            print("❌ Club BGA Test 1 non trouvé")
            return
        
        print(f"✓ Club trouvé: {club.name}")
        print(f"  Organisation: {club.organization}")
        
        # S'assurer qu'une organisation existe
        if not club.organization:
            print("  Création organisation...")
            club.save()  # Déclenche la création de l'organisation
        
        if club.organization:
            # Vérifier si un tenant existe déjà
            existing_tenant = Tenant.objects.filter(
                name__icontains=club.organization.name
            ).first()
            
            if existing_tenant:
                print(f"✅ Sous-domaine existant: {existing_tenant.domain}")
            else:
                print("  Création sous-domaine...")
                from apps.competitions.utils.subdomain_generator import create_organization_tenant
                tenant = create_organization_tenant(club.organization)
                print(f"✅ Sous-domaine créé: {tenant.domain}")
        else:
            print("❌ Impossible de créer l'organisation")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_bga_test_subdomain()
'''
    
    with open('/mnt/c/martial_hub_django/martialcomp/fix_bga_test_subdomain.py', 'w') as f:
        f.write(fix_script)
    
    print("✅ Script correction BGA Test 1 créé")
    print("📄 Fichier: fix_bga_test_subdomain.py")

def main():
    """Crée tous les scripts de déploiement."""
    print("📦 CRÉATION SCRIPTS DÉPLOIEMENT PRODUCTION")
    print("=" * 50)
    
    create_production_deployment_script()
    create_production_fix_script()
    
    print("\n🎯 SCRIPTS CRÉÉS AVEC SUCCÈS!")
    print("\nÉTAPES DE DÉPLOIEMENT:")
    print("1. Transférer les scripts vers le serveur")
    print("2. Exécuter: chmod +x deploy_subdomains_to_production.sh")
    print("3. Exécuter: ./deploy_subdomains_to_production.sh")
    print("4. Tester: python fix_bga_test_subdomain.py")
    print("\n✅ Le système de sous-domaines automatiques sera opérationnel!")

if __name__ == "__main__":
    main()