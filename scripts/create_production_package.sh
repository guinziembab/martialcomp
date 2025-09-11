#!/bin/bash

################################################################################
# CRÉATION DU PACKAGE DE CORRECTION PRODUCTION
# Onboarding & Notifications - Version 1.0
################################################################################

echo "📦 CRÉATION DU PACKAGE DE CORRECTION PRODUCTION"
echo "==============================================="
echo "Date: $(date)"
echo ""

# Configuration
PACKAGE_NAME="martialcomp_onboarding_notifications_fix_$(date +%Y%m%d_%H%M%S)"
PACKAGE_DIR="/tmp/$PACKAGE_NAME"
ARCHIVE_PATH="/tmp/$PACKAGE_NAME.tar.gz"

echo "📁 Nom du package: $PACKAGE_NAME"
echo "📂 Répertoire: $PACKAGE_DIR"
echo "📦 Archive: $ARCHIVE_PATH"
echo ""

# Créer le répertoire du package
mkdir -p "$PACKAGE_DIR"

echo "📋 COLLECTE DES FICHIERS DU PACKAGE"
echo "=================================="

# 1. Scripts principaux
echo "📝 Copie des scripts principaux..."
cp "deploy_production_onboarding_notifications.sh" "$PACKAGE_DIR/"
cp "validate_onboarding_notifications_deployment.py" "$PACKAGE_DIR/"
cp "README_DEPLOYMENT_ONBOARDING_NOTIFICATIONS.md" "$PACKAGE_DIR/"

echo "   ✅ Scripts de déploiement copiés"

# 2. Fichiers de modèles (exemples)
echo "📝 Copie des exemples de modèles..."
mkdir -p "$PACKAGE_DIR/examples/models"

# Copier les modèles actuels comme exemples
if [ -f "competitions/models/users.py" ]; then
    cp "competitions/models/users.py" "$PACKAGE_DIR/examples/models/users.py.example"
fi

if [ -f "competitions/models/notifications.py" ]; then
    cp "competitions/models/notifications.py" "$PACKAGE_DIR/examples/models/notifications.py.example"
fi

echo "   ✅ Modèles d'exemple copiés"

# 3. Fichiers de vues (exemples)
echo "📝 Copie des exemples de vues..."
mkdir -p "$PACKAGE_DIR/examples/views"

if [ -f "competitions/views/welcome.py" ]; then
    cp "competitions/views/welcome.py" "$PACKAGE_DIR/examples/views/welcome.py.example"
fi

if [ -f "competitions/views/notifications.py" ]; then
    cp "competitions/views/notifications.py" "$PACKAGE_DIR/examples/views/notifications.py.example"
fi

echo "   ✅ Vues d'exemple copiées"

# 4. Templates (exemples)
echo "📝 Copie des exemples de templates..."
mkdir -p "$PACKAGE_DIR/examples/templates/competitions/notifications"

if [ -f "competitions/templates/competitions/notifications/list.html" ]; then
    cp "competitions/templates/competitions/notifications/list.html" "$PACKAGE_DIR/examples/templates/competitions/notifications/list.html.example"
fi

echo "   ✅ Templates d'exemple copiés"

# 5. Configuration URLs (exemples)
echo "📝 Copie des exemples de configuration URLs..."
mkdir -p "$PACKAGE_DIR/examples/urls"

if [ -f "competitions/urls/notifications.py" ]; then
    cp "competitions/urls/notifications.py" "$PACKAGE_DIR/examples/urls/notifications.py.example"
fi

echo "   ✅ Configuration URLs d'exemple copiée"

# 6. Créer un fichier de manifest
echo "📝 Création du manifest..."

cat > "$PACKAGE_DIR/MANIFEST.txt" << EOF
PACKAGE DE CORRECTION PRODUCTION - ONBOARDING & NOTIFICATIONS
=============================================================

Date de création: $(date)
Version: 1.0
Auteur: Claude Code

CONTENU DU PACKAGE:
==================

SCRIPTS PRINCIPAUX:
- deploy_production_onboarding_notifications.sh     # Script de déploiement principal
- validate_onboarding_notifications_deployment.py   # Script de validation
- README_DEPLOYMENT_ONBOARDING_NOTIFICATIONS.md     # Documentation complète

EXEMPLES DE FICHIERS:
- examples/models/users.py.example                  # Modèle UserProfile corrigé
- examples/models/notifications.py.example          # Modèles Notification et NotificationPreference
- examples/views/welcome.py.example                 # Vue welcome avec logique d'onboarding
- examples/views/notifications.py.example           # Vues pour le système de notifications
- examples/templates/competitions/notifications/    # Templates pour les notifications
- examples/urls/notifications.py.example            # Configuration URLs notifications

INSTRUCTIONS:
=============

1. Transférer le package sur le serveur de production
2. Extraire l'archive : tar -xzf $PACKAGE_NAME.tar.gz
3. Exécuter : chmod +x deploy_production_onboarding_notifications.sh
4. Lancer le déploiement : sudo ./deploy_production_onboarding_notifications.sh
5. Valider : python3 validate_onboarding_notifications_deployment.py

CORRECTIONS APPORTÉES:
=====================

✅ Processus d'onboarding cassé corrigé
✅ Système de notifications discret implémenté
✅ Logique de redirection basée sur les rôles
✅ Interface professionnelle avec icône de cloche
✅ API AJAX pour notifications en temps réel
✅ Gestion complète des notifications (CRUD)
✅ Comptes de test automatiquement créés
✅ Validation post-déploiement automatisée

URLS AJOUTÉES:
=============

- /fr/competitions/notifications/                   # Liste des notifications
- /fr/competitions/notifications/api/               # API AJAX
- /fr/competitions/notifications/mark-read/<id>/    # Marquer comme lu
- /fr/competitions/notifications/mark-all-read/     # Tout marquer comme lu

COMPTES DE TEST:
===============

- admin / admin123               (Spectateur - Onboarding terminé)
- club_manager_test / test123    (Manager - Nécessite onboarding)
- participant_test / test123     (Participant - Onboarding terminé)

SUPPORT:
========

En cas de problème, vérifier les logs:
- /tmp/deploy_onboarding_notifications_YYYYMMDD_HHMMSS.log
- /tmp/django_onboarding_notifications.log

Fichiers de sauvegarde disponibles dans:
- /tmp/backup_YYYYMMDD_HHMMSS/
EOF

echo "   ✅ Manifest créé"

# 7. Créer un script d'installation rapide
echo "📝 Création du script d'installation rapide..."

cat > "$PACKAGE_DIR/quick_install.sh" << 'EOF'
#!/bin/bash

echo "🚀 INSTALLATION RAPIDE - CORRECTIONS ONBOARDING & NOTIFICATIONS"
echo "=============================================================="

# Vérifications préliminaires
if [ ! -d "/var/www/vhosts/martialcomp.com/httpdocs" ]; then
    echo "❌ Répertoire de production non trouvé"
    echo "📋 Veuillez ajuster le chemin dans le script deploy_production_onboarding_notifications.sh"
    exit 1
fi

# Rendre les scripts exécutables
chmod +x deploy_production_onboarding_notifications.sh
chmod +x validate_onboarding_notifications_deployment.py

echo "✅ Scripts rendus exécutables"

# Proposer l'exécution du déploiement
echo ""
echo "🔧 Prêt pour le déploiement!"
echo ""
echo "Options:"
echo "1. Lancer le déploiement maintenant"
echo "2. Afficher les instructions manuelles"
echo "3. Quitter"
echo ""

read -p "Votre choix (1-3): " choice

case $choice in
    1)
        echo "🚀 Lancement du déploiement..."
        sudo ./deploy_production_onboarding_notifications.sh
        
        if [ $? -eq 0 ]; then
            echo ""
            echo "✅ Déploiement terminé!"
            echo "🔍 Lancement de la validation..."
            cd /var/www/vhosts/martialcomp.com/httpdocs
            python3 "$(pwd)/validate_onboarding_notifications_deployment.py"
        else
            echo "❌ Erreur lors du déploiement"
        fi
        ;;
    2)
        echo ""
        echo "📋 INSTRUCTIONS MANUELLES:"
        echo "========================="
        echo ""
        echo "1. Exécuter le déploiement:"
        echo "   sudo ./deploy_production_onboarding_notifications.sh"
        echo ""
        echo "2. Valider l'installation:"
        echo "   cd /var/www/vhosts/martialcomp.com/httpdocs"
        echo "   python3 ./validate_onboarding_notifications_deployment.py"
        echo ""
        echo "3. Tester les URLs:"
        echo "   - https://martialcomp.com/fr/"
        echo "   - https://martialcomp.com/admin/"
        echo "   - https://martialcomp.com/fr/competitions/notifications/"
        echo ""
        echo "4. Se connecter avec les comptes de test:"
        echo "   - admin / admin123"
        echo "   - club_manager_test / test123"
        echo "   - participant_test / test123"
        ;;
    3)
        echo "👋 Installation annulée"
        ;;
    *)
        echo "❌ Option invalide"
        ;;
esac
EOF

chmod +x "$PACKAGE_DIR/quick_install.sh"
echo "   ✅ Script d'installation rapide créé"

# 8. Créer un checksum pour vérifier l'intégrité
echo "📝 Génération des checksums..."
cd "$PACKAGE_DIR"
find . -type f -exec sha256sum {} \; > CHECKSUMS.txt
cd - > /dev/null
echo "   ✅ Checksums générés"

# 9. Créer l'archive
echo ""
echo "📦 CRÉATION DE L'ARCHIVE"
echo "======================="

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
else
    echo "❌ Erreur lors de la création de l'archive"
    exit 1
fi

# 10. Résumé final
echo ""
echo "📋 RÉSUMÉ DU PACKAGE"
echo "==================="
echo ""
echo "📦 Package: $PACKAGE_NAME"
echo "📂 Archive: $ARCHIVE_PATH"
echo "📏 Taille: $ARCHIVE_SIZE"
echo "🔒 Checksum: $ARCHIVE_CHECKSUM"
echo ""
echo "📁 Contenu du package:"
echo "   📜 Scripts de déploiement et validation"
echo "   📖 Documentation complète"
echo "   📝 Exemples de tous les fichiers modifiés"
echo "   🚀 Script d'installation rapide"
echo "   ✅ Checksums d'intégrité"
echo ""
echo "🔗 INSTRUCTIONS DE TRANSFERT:"
echo "============================="
echo ""
echo "# Transférer vers le serveur de production:"
echo "scp $ARCHIVE_PATH user@serveur:/tmp/"
echo ""
echo "# Sur le serveur de production:"
echo "cd /tmp"
echo "tar -xzf $(basename $ARCHIVE_PATH)"
echo "cd $PACKAGE_NAME"
echo "./quick_install.sh"
echo ""
echo "🎉 PACKAGE DE CORRECTION PRÊT POUR LA PRODUCTION!"

# Nettoyage optionnel du répertoire temporaire
echo ""
read -p "🗑️ Supprimer le répertoire temporaire $PACKAGE_DIR ? (y/N): " cleanup
if [[ $cleanup =~ ^[Yy]$ ]]; then
    rm -rf "$PACKAGE_DIR"
    echo "✅ Répertoire temporaire supprimé"
fi

echo ""
echo "📋 Archive finale disponible: $ARCHIVE_PATH"
echo "Date: $(date)"