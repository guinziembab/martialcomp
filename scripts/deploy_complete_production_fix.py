#!/usr/bin/env python3
"""
Script de déploiement complet pour la production
Applique toutes les corrections nécessaires pour résoudre l'erreur PostgreSQL
"""
import os
import shutil
import subprocess
import sys
from datetime import datetime

def create_deployment_package():
    """Crée un package de déploiement avec tous les fichiers nécessaires"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    package_dir = f"deployment_package_{timestamp}"
    
    print("📦 CRÉATION DU PACKAGE DE DÉPLOIEMENT")
    print("=" * 45)
    
    os.makedirs(package_dir, exist_ok=True)
    
    # Fichiers critiques à déployer
    critical_files = [
        "competitions/models/practitioners.py",
        "competitions/migrations/0008_fix_family_fields_null.py",
        "competitions/signals.py",
        "grades/signals.py"
    ]
    
    copied_files = []
    
    for file_path in critical_files:
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
    
    # Créer un script d'installation pour la production
    install_script = f"""#!/bin/bash
# Script d'installation automatique pour la production
# Généré le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

echo "🚀 INSTALLATION DES CORRECTIONS EN PRODUCTION"
echo "=============================================="

# Arrêter le service Django
echo "🔄 Arrêt du service Django..."
sudo systemctl stop martialcomp

# Sauvegardes
BACKUP_DIR="/opt/martialcomp/backups/fix_{timestamp}"
mkdir -p "$BACKUP_DIR"

echo "💾 Création des sauvegardes..."
"""

    # Ajouter les commandes de sauvegarde et copie
    for file_path in copied_files:
        prod_path = f"/opt/martialcomp/app/{file_path}"
        install_script += f"""
# Sauvegarder {file_path}
if [ -f "{prod_path}" ]; then
    cp "{prod_path}" "$BACKUP_DIR/"
    echo "✅ Sauvegardé: {file_path}"
fi

# Copier le nouveau fichier
cp "{file_path}" "{prod_path}"
echo "✅ Mis à jour: {file_path}"
"""

    install_script += """
# Appliquer les migrations
echo "🔄 Application des migrations..."
cd /opt/martialcomp/app
python3 manage.py migrate

# Redémarrer le service
echo "🔄 Redémarrage du service Django..."
sudo systemctl start martialcomp

# Vérifier le statut
echo "📊 Vérification du statut..."
sudo systemctl status martialcomp

echo "✅ Installation terminée!"
echo "📋 Testez maintenant l'ajout d'un pratiquant sur l'interface web"
echo "📁 Sauvegardes disponibles dans: $BACKUP_DIR"
"""

    # Écrire le script d'installation
    install_script_path = os.path.join(package_dir, "install_production.sh")
    with open(install_script_path, 'w') as f:
        f.write(install_script)
    
    # Rendre le script exécutable
    os.chmod(install_script_path, 0o755)
    
    print(f"✅ Package créé: {package_dir}/")
    print(f"✅ Script d'installation: {install_script_path}")
    
    return package_dir

def create_manual_deployment_commands():
    """Crée une liste de commandes manuelles pour le déploiement"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    commands = f"""
# COMMANDES DE DÉPLOIEMENT MANUEL - {timestamp}
# ===============================================

# 1. SE CONNECTER AU SERVEUR DE PRODUCTION
ssh votre_serveur_production

# 2. SAUVEGARDER LES FICHIERS ACTUELS
sudo mkdir -p /opt/martialcomp/backups/fix_{timestamp}
sudo cp /opt/martialcomp/app/competitions/models/practitioners.py /opt/martialcomp/backups/fix_{timestamp}/
sudo cp /opt/martialcomp/app/competitions/signals.py /opt/martialcomp/backups/fix_{timestamp}/
sudo cp /opt/martialcomp/app/grades/signals.py /opt/martialcomp/backups/fix_{timestamp}/

# 3. ARRÊTER LE SERVICE DJANGO
sudo systemctl stop martialcomp

# 4. COPIER LES FICHIERS CORRIGÉS (depuis votre machine locale)
# Utilisez scp ou rsync pour transférer les fichiers suivants:
# - competitions/models/practitioners.py
# - competitions/migrations/0008_fix_family_fields_null.py  
# - competitions/signals.py
# - grades/signals.py

# 5. APPLIQUER LES MIGRATIONS
cd /opt/martialcomp/app
python3 manage.py migrate

# 6. REDÉMARRER LE SERVICE
sudo systemctl start martialcomp

# 7. VÉRIFIER LE STATUT
sudo systemctl status martialcomp

# 8. SURVEILLER LES LOGS
sudo journalctl -u martialcomp -f

# 9. TESTER L'AJOUT D'UN PRATIQUANT
# Aller sur l'interface web et tester la création d'un pratiquant
"""
    
    with open(f"deployment_commands_{timestamp}.txt", 'w') as f:
        f.write(commands)
    
    print(f"📋 Commandes manuelles sauvegardées: deployment_commands_{timestamp}.txt")

def validate_local_changes():
    """Valide que toutes les corrections sont présentes localement"""
    print("🔍 VALIDATION DES CORRECTIONS LOCALES")
    print("=" * 40)
    
    checks = []
    
    # Vérifier le modèle Practitioner
    model_file = "competitions/models/practitioners.py"
    if os.path.exists(model_file):
        with open(model_file, 'r') as f:
            content = f.read()
            if 'family_role' in content and 'null=True' in content:
                checks.append(("✅", "Modèle Practitioner: champs famille avec null=True"))
            else:
                checks.append(("❌", "Modèle Practitioner: corrections manquantes"))
    else:
        checks.append(("❌", "Modèle Practitioner: fichier manquant"))
    
    # Vérifier la migration
    migration_file = "competitions/migrations/0008_fix_family_fields_null.py"
    if os.path.exists(migration_file):
        checks.append(("✅", "Migration 0008: présente"))
    else:
        checks.append(("❌", "Migration 0008: manquante"))
    
    # Vérifier les signaux competitions
    signals_file = "competitions/signals.py"
    if os.path.exists(signals_file):
        with open(signals_file, 'r') as f:
            content = f.read()
            if 'bool(True)' in content and 'bool(False)' in content:
                checks.append(("✅", "Signaux competitions: corrections bool() présentes"))
            else:
                checks.append(("⚠️ ", "Signaux competitions: corrections bool() à vérifier"))
    else:
        checks.append(("❌", "Signaux competitions: fichier manquant"))
    
    # Vérifier les signaux grades
    grades_signals = "grades/signals.py"
    if os.path.exists(grades_signals):
        with open(grades_signals, 'r') as f:
            content = f.read()
            if 'bool(True)' in content:
                checks.append(("✅", "Signaux grades: corrections bool() présentes"))
            else:
                checks.append(("⚠️ ", "Signaux grades: corrections bool() à vérifier"))
    else:
        checks.append(("❌", "Signaux grades: fichier manquant"))
    
    # Afficher les résultats
    for status, message in checks:
        print(f"{status} {message}")
    
    # Déterminer si tout est prêt
    all_good = all(check[0] == "✅" for check in checks)
    
    if all_good:
        print("\n🎉 TOUTES LES CORRECTIONS SONT PRÊTES POUR LE DÉPLOIEMENT!")
        return True
    else:
        print("\n⚠️  CERTAINES CORRECTIONS SONT MANQUANTES")
        return False

def main():
    print("🚀 PRÉPARATION DU DÉPLOIEMENT EN PRODUCTION")
    print("=" * 50)
    print("🎯 Objectif: Déployer la correction de l'erreur PostgreSQL")
    print("📋 Action: Préparer tous les fichiers et instructions")
    print()
    
    # Vérifier qu'on est à la racine du projet
    if not os.path.exists("manage.py"):
        print("❌ Erreur: Ce script doit être exécuté à la racine du projet Django")
        return
    
    # 1. Valider les corrections locales
    if not validate_local_changes():
        print("\n❌ Les corrections ne sont pas complètes localement")
        print("   Exécutez d'abord les scripts de correction locaux")
        return
    
    print()
    
    # 2. Créer le package de déploiement
    package_dir = create_deployment_package()
    print()
    
    # 3. Créer les commandes manuelles
    create_manual_deployment_commands()
    print()
    
    # 4. Instructions finales
    print("=" * 50)
    print("📋 INSTRUCTIONS DE DÉPLOIEMENT")
    print("=" * 30)
    print()
    print("OPTION 1 - DÉPLOIEMENT AUTOMATIQUE:")
    print("1. 📁 Transférer le package complet sur le serveur:")
    print(f"   scp -r {package_dir}/ user@serveur:/tmp/")
    print("2. 🔧 Exécuter le script d'installation:")
    print(f"   ssh user@serveur 'cd /tmp/{package_dir} && sudo ./install_production.sh'")
    print()
    print("OPTION 2 - DÉPLOIEMENT MANUEL:")
    print("1. 📋 Suivre les commandes dans le fichier deployment_commands_*.txt")
    print("2. 📁 Transférer manuellement chaque fichier")
    print("3. 🔄 Appliquer les migrations et redémarrer")
    print()
    print("🎯 TESTS POST-DÉPLOIEMENT:")
    print("1. ✅ Vérifier que le service Django démarre")
    print("2. 🧪 Tester l'ajout d'un pratiquant via l'interface web")
    print("3. 📊 Surveiller les logs pour confirmer l'absence d'erreurs")
    print()
    print("📞 EN CAS DE PROBLÈME:")
    print("- Restaurer les sauvegardes depuis /opt/martialcomp/backups/")
    print("- Redémarrer le service: sudo systemctl restart martialcomp")
    print("- Consulter les logs: sudo journalctl -u martialcomp -f")

if __name__ == "__main__":
    main()