#!/bin/bash

################################################################################
# CRÉATION DU PACKAGE FINAL DE CORRECTION PRODUCTION
################################################################################

echo "📦 CRÉATION DU PACKAGE FINAL DE CORRECTION"
echo "==========================================="
echo "Date: $(date)"
echo ""

# Configuration
PACKAGE_NAME="martialcomp_corrections_production_$(date +%Y%m%d_%H%M%S)"
PACKAGE_DIR="/tmp/$PACKAGE_NAME"
ARCHIVE_PATH="/tmp/$PACKAGE_NAME.tar.gz"

echo "📁 Nom du package: $PACKAGE_NAME"
echo "📂 Répertoire: $PACKAGE_DIR"
echo "📦 Archive: $ARCHIVE_PATH"
echo ""

# Créer le répertoire du package
mkdir -p "$PACKAGE_DIR"

echo "📋 COLLECTE DES FICHIERS"
echo "======================="

# Scripts principaux
echo "📝 Copie des scripts principaux..."
cp "deploy_production_corrections_final.sh" "$PACKAGE_DIR/"
cp "validate_production_deployment.py" "$PACKAGE_DIR/"
cp "install_production_corrections.sh" "$PACKAGE_DIR/"
cp "README_CORRECTIONS_PRODUCTION.md" "$PACKAGE_DIR/"

echo "   ✅ Scripts principaux copiés"

# Scripts de diagnostic et utilitaires
echo "📝 Copie des scripts utilitaires..."
if [ -f "fix_notifications_ultimate.py" ]; then
    cp "fix_notifications_ultimate.py" "$PACKAGE_DIR/"
fi
if [ -f "validate_final_system.py" ]; then
    cp "validate_final_system.py" "$PACKAGE_DIR/"
fi

echo "   ✅ Scripts utilitaires copiés"

# Créer un fichier de manifest détaillé
echo "📝 Création du manifest..."

cat > "$PACKAGE_DIR/MANIFEST.txt" << EOF
PACKAGE DE CORRECTIONS PRODUCTION MARTIALCOMP
=============================================

Date de création: $(date)
Version: 1.0 Final
Auteur: Claude Code Assistant

CONTENU DU PACKAGE:
==================

SCRIPTS PRINCIPAUX:
------------------
deploy_production_corrections_final.sh          # Script de déploiement complet
validate_production_deployment.py               # Script de validation post-déploiement
install_production_corrections.sh               # Script d'installation rapide
README_CORRECTIONS_PRODUCTION.md                # Documentation complète

SCRIPTS UTILITAIRES:
-------------------
fix_notifications_ultimate.py                   # Correction ultime des notifications
validate_final_system.py                        # Validation complète du système

CORRECTIONS IMPLÉMENTÉES:
========================

1. SYSTÈME D'ONBOARDING:
   ✅ Logique de redirection corrigée
   ✅ Création automatique de profils utilisateur
   ✅ Gestion des rôles (spectator, participant, club_manager, etc.)
   ✅ Vérification du statut d'onboarding
   ✅ Redirection vers le dashboard approprié

2. SYSTÈME DE NOTIFICATIONS:
   ✅ Modèles complets (Notification, NotificationPreference)
   ✅ Interface utilisateur discrète et professionnelle
   ✅ Types de notifications (info, warning, error, success)
   ✅ Priorités (low, standard, important, critical)
   ✅ Actions personnalisables (URL + texte d'action)
   ✅ API AJAX pour notifications en temps réel
   ✅ Gestion complète (création, lecture, suppression)

3. BASE DE DONNÉES:
   ✅ Structure corrigée (notification_type au lieu de type)
   ✅ Migration automatique des données existantes
   ✅ Index optimisés pour les performances
   ✅ Contraintes de clés étrangères

4. INTERFACE UTILISATEUR:
   ✅ Templates responsive avec Bootstrap
   ✅ Icônes Font Awesome
   ✅ Design professionnel et discret
   ✅ Navigation intuitive

INSTALLATION:
============

MÉTHODE 1 - AUTOMATIQUE (RECOMMANDÉE):
1. Transférer le package sur le serveur
2. Extraire: tar -xzf $PACKAGE_NAME.tar.gz
3. Aller dans le dossier: cd $PACKAGE_NAME
4. Exécuter: ./install_production_corrections.sh
5. Choisir l'option 1 (Installation complète automatique)

MÉTHODE 2 - MANUELLE:
1. Rendre exécutable: chmod +x deploy_production_corrections_final.sh
2. Exécuter: sudo ./deploy_production_corrections_final.sh
3. Valider: python3 validate_production_deployment.py

URLS PRINCIPALES:
================
- Accueil: https://martialcomp.com/fr/
- Administration: https://martialcomp.com/admin/
- Notifications: https://martialcomp.com/fr/competitions/notifications/

COMPTE ADMINISTRATEUR:
=====================
Username: admin
Password: admin123

SUPPORT:
========
En cas de problème:
1. Consulter les logs dans /tmp/
2. Exécuter le script de validation
3. Vérifier les URLs de base
4. Restaurer depuis les sauvegardes si nécessaire

COMPATIBILITÉ:
=============
- Django 3.x et 4.x
- Python 3.8+
- SQLite et PostgreSQL
- Apache et Nginx
- Gunicorn et uWSGI

SÉCURITÉ:
=========
✅ Protection CSRF
✅ Authentification requise
✅ Validation des permissions
✅ Sanitisation des données
✅ Sauvegardes automatiques

TESTS:
======
Tous les scripts incluent une validation automatique:
- Modèles Django
- Structure base de données
- Fonctionnement des vues
- Résolution des URLs
- Création de notifications
- Logique d'onboarding

Le taux de réussite attendu est de 100% pour une installation réussie.
EOF

echo "   ✅ Manifest créé"

# Créer un script de vérification d'intégrité
echo "📝 Création du script de vérification..."

cat > "$PACKAGE_DIR/check_integrity.sh" << 'EOF'
#!/bin/bash

echo "🔍 VÉRIFICATION DE L'INTÉGRITÉ DU PACKAGE"
echo "========================================"

files=(
    "deploy_production_corrections_final.sh"
    "validate_production_deployment.py"
    "install_production_corrections.sh"
    "README_CORRECTIONS_PRODUCTION.md"
    "MANIFEST.txt"
)

missing_files=()
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file (MANQUANT)"
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -eq 0 ]; then
    echo ""
    echo "✅ PACKAGE INTÈGRE - Tous les fichiers sont présents"
    echo ""
    echo "📋 Prochaines étapes:"
    echo "   1. Lire README_CORRECTIONS_PRODUCTION.md"
    echo "   2. Exécuter ./install_production_corrections.sh"
    echo "   3. Choisir l'installation automatique"
    exit 0
else
    echo ""
    echo "❌ PACKAGE INCOMPLET - Fichiers manquants:"
    for file in "${missing_files[@]}"; do
        echo "   - $file"
    done
    echo ""
    echo "⚠️ Veuillez télécharger à nouveau le package complet"
    exit 1
fi
EOF

chmod +x "$PACKAGE_DIR/check_integrity.sh"
echo "   ✅ Script de vérification créé"

# Créer un script de désinstallation
echo "📝 Création du script de désinstallation..."

cat > "$PACKAGE_DIR/uninstall_corrections.sh" << 'EOF'
#!/bin/bash

echo "🗑️ DÉSINSTALLATION DES CORRECTIONS MARTIALCOMP"
echo "=============================================="

PROD_DIR="/var/www/vhosts/martialcomp.com/httpdocs"

if [ ! -d "$PROD_DIR" ]; then
    echo "❌ Répertoire de production non trouvé"
    exit 1
fi

echo "⚠️ ATTENTION: Cette opération va restaurer les fichiers depuis la sauvegarde"
echo ""

# Chercher les sauvegardes
backups=($(ls -d /tmp/backup_production_* 2>/dev/null | sort -r))

if [ ${#backups[@]} -eq 0 ]; then
    echo "❌ Aucune sauvegarde trouvée dans /tmp/"
    exit 1
fi

echo "📋 Sauvegardes disponibles:"
for i in "${!backups[@]}"; do
    echo "   $((i+1)). ${backups[$i]}"
done

read -p "Choisir une sauvegarde (1-${#backups[@]}): " choice

if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "${#backups[@]}" ]; then
    backup_dir="${backups[$((choice-1))]}"
    echo "📂 Utilisation de la sauvegarde: $backup_dir"
else
    echo "❌ Choix invalide"
    exit 1
fi

read -p "Confirmer la restauration? (y/N): " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "Désinstallation annulée"
    exit 0
fi

cd "$PROD_DIR"

echo "🔄 Restauration des fichiers..."

files_to_restore=(
    "competitions/models/users.py"
    "competitions/models/notifications.py"
    "competitions/views/welcome.py"
    "competitions/views/notifications.py"
    "competitions/urls.py"
    "db.sqlite3"
)

for file in "${files_to_restore[@]}"; do
    if [ -f "$backup_dir/$(basename $file)" ]; then
        cp "$backup_dir/$(basename $file)" "$file"
        echo "✅ Restauré: $file"
    else
        echo "⚠️ Sauvegarde non trouvée: $file"
    fi
done

echo "🔄 Redémarrage du serveur..."
pkill -f "python.*manage.py" 2>/dev/null || true
pkill -f "gunicorn" 2>/dev/null || true
sleep 3

nohup python3 manage.py runserver 0.0.0.0:8000 > /tmp/django_restored.log 2>&1 &

echo "✅ Restauration terminée"
echo "📋 Vérifiez que le site fonctionne normalement"
EOF

chmod +x "$PACKAGE_DIR/uninstall_corrections.sh"
echo "   ✅ Script de désinstallation créé"

# Générer les checksums
echo "📝 Génération des checksums..."
cd "$PACKAGE_DIR"
find . -type f -exec sha256sum {} \; > CHECKSUMS.txt
cd - > /dev/null
echo "   ✅ Checksums générés"

# Créer l'archive
echo ""
echo "📦 CRÉATION DE L'ARCHIVE"
echo "======================"

cd /tmp
tar -czf "$ARCHIVE_PATH" "$PACKAGE_NAME"
cd - > /dev/null

if [ -f "$ARCHIVE_PATH" ]; then
    echo "✅ Archive créée avec succès: $ARCHIVE_PATH"
    
    # Calculer la taille
    ARCHIVE_SIZE=$(du -h "$ARCHIVE_PATH" | cut -f1)
    echo "📏 Taille de l'archive: $ARCHIVE_SIZE"
    
    # Générer le checksum de l'archive
    ARCHIVE_CHECKSUM=$(sha256sum "$ARCHIVE_PATH" | cut -d' ' -f1)
    echo "🔒 Checksum SHA256: $ARCHIVE_CHECKSUM"
    
    # Créer un fichier d'informations
    cat > "${ARCHIVE_PATH}.info" << EOF
PACKAGE: $PACKAGE_NAME.tar.gz
TAILLE: $ARCHIVE_SIZE
DATE: $(date)
CHECKSUM: $ARCHIVE_CHECKSUM

INSTALLATION RAPIDE:
1. tar -xzf $PACKAGE_NAME.tar.gz
2. cd $PACKAGE_NAME
3. ./install_production_corrections.sh

CONTENU:
- Scripts de déploiement et validation
- Documentation complète
- Scripts utilitaires
- Vérification d'intégrité
- Script de désinstallation
EOF
    
    echo "📋 Fichier d'informations créé: ${ARCHIVE_PATH}.info"
else
    echo "❌ Erreur lors de la création de l'archive"
    exit 1
fi

# Résumé final
echo ""
echo "📋 RÉSUMÉ DU PACKAGE FINAL"
echo "========================="
echo ""
echo "📦 Package: $PACKAGE_NAME"
echo "📂 Archive: $ARCHIVE_PATH"
echo "📏 Taille: $ARCHIVE_SIZE"
echo "🔒 Checksum: $ARCHIVE_CHECKSUM"
echo ""
echo "📁 Contenu:"
echo "   📜 Scripts de déploiement complets"
echo "   📖 Documentation détaillée"
echo "   🔧 Utilitaires de diagnostic"
echo "   ✅ Vérification d'intégrité"
echo "   🗑️ Script de désinstallation"
echo ""
echo "🚀 INSTRUCTIONS DE DÉPLOIEMENT:"
echo "============================="
echo ""
echo "# 1. Transférer vers le serveur:"
echo "scp $ARCHIVE_PATH user@serveur:/tmp/"
echo ""
echo "# 2. Sur le serveur de production:"
echo "cd /tmp"
echo "tar -xzf $(basename $ARCHIVE_PATH)"
echo "cd $PACKAGE_NAME"
echo "./check_integrity.sh"
echo "./install_production_corrections.sh"
echo ""
echo "🎉 PACKAGE FINAL PRÊT POUR LA PRODUCTION!"

# Proposer de nettoyer
echo ""
read -p "🗑️ Supprimer le répertoire temporaire $PACKAGE_DIR ? (y/N): " cleanup
if [[ $cleanup =~ ^[Yy]$ ]]; then
    rm -rf "$PACKAGE_DIR"
    echo "✅ Répertoire temporaire supprimé"
fi

echo ""
echo "📋 Archive finale disponible: $ARCHIVE_PATH"
echo "📋 Informations: ${ARCHIVE_PATH}.info"
echo "Date: $(date)"