#!/bin/bash

# Script de déploiement simple vers la production
# Usage: ./deploy_to_production_simple.sh [SERVER_IP] [USER]

set -e  # Arrêter en cas d'erreur

SERVER_IP=${1:-"votre_ip_serveur"}
USER=${2:-"root"}
PACKAGE_DIR="deployment_package_20250613_192621"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "🚀 DÉPLOIEMENT VERS LA PRODUCTION"
echo "=================================="
echo "🖥️  Serveur: $USER@$SERVER_IP"
echo "📦 Package: $PACKAGE_DIR"
echo "⏰ Timestamp: $TIMESTAMP"
echo

# Vérifier que le package existe
if [ ! -d "$PACKAGE_DIR" ]; then
    echo "❌ Erreur: Package $PACKAGE_DIR non trouvé"
    echo "   Exécutez d'abord: python3 deploy_complete_production_fix.py"
    exit 1
fi

# Vérifier la connectivité SSH (optionnel)
echo "🔍 Test de connectivité SSH..."
if ssh -o ConnectTimeout=10 -o BatchMode=yes "$USER@$SERVER_IP" exit 2>/dev/null; then
    echo "✅ Connexion SSH OK"
else
    echo "⚠️  Impossible de tester la connexion SSH"
    echo "   Continuez seulement si vous êtes sûr des paramètres de connexion"
    read -p "   Continuer quand même ? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Déploiement annulé"
        exit 1
    fi
fi

echo

# 1. Transférer le package
echo "📤 TRANSFERT DU PACKAGE"
echo "======================"
echo "📁 Transfert de $PACKAGE_DIR vers /tmp/ sur le serveur..."

scp -r "$PACKAGE_DIR" "$USER@$SERVER_IP:/tmp/" || {
    echo "❌ Erreur lors du transfert"
    exit 1
}

echo "✅ Package transféré avec succès"
echo

# 2. Exécuter l'installation
echo "🔧 INSTALLATION SUR LE SERVEUR"
echo "=============================="
echo "🚀 Exécution du script d'installation..."

ssh "$USER@$SERVER_IP" "cd /tmp/$PACKAGE_DIR && chmod +x install_production.sh && sudo ./install_production.sh" || {
    echo "❌ Erreur lors de l'installation"
    echo "📋 Commandes de récupération:"
    echo "   ssh $USER@$SERVER_IP"
    echo "   cd /tmp/$PACKAGE_DIR"
    echo "   sudo ./install_production.sh"
    exit 1
}

echo "✅ Installation terminée"
echo

# 3. Validation post-déploiement
echo "🧪 VALIDATION POST-DÉPLOIEMENT"
echo "============================="
echo "🔍 Exécution des tests de validation..."

ssh "$USER@$SERVER_IP" "cd /tmp/$PACKAGE_DIR && python3 validate_production.py" || {
    echo "⚠️  Erreur lors de la validation"
    echo "   Les tests de validation ont échoué, mais le déploiement peut avoir réussi"
    echo "   Vérifiez manuellement le fonctionnement"
}

echo

# 4. Instructions finales
echo "🎉 DÉPLOIEMENT TERMINÉ!"
echo "======================"
echo
echo "📋 PROCHAINES ÉTAPES:"
echo "1. 🧪 Tester l'ajout d'un pratiquant via l'interface web"
echo "2. 📊 Surveiller les logs: ssh $USER@$SERVER_IP 'sudo journalctl -u martialcomp -f'"
echo "3. ✅ Vérifier que l'erreur PostgreSQL n'apparaît plus"
echo
echo "📞 EN CAS DE PROBLÈME:"
echo "1. 🔄 Redémarrer le service: ssh $USER@$SERVER_IP 'sudo systemctl restart martialcomp'"
echo "2. 📁 Restaurer les sauvegardes: ssh $USER@$SERVER_IP 'ls /opt/martialcomp/backups/'"
echo "3. 📋 Consulter les logs: ssh $USER@$SERVER_IP 'sudo journalctl -u martialcomp -f'"
echo
echo "📁 Sauvegardes créées sur le serveur:"
echo "   /opt/martialcomp/backups/fix_$TIMESTAMP/"
echo "   /tmp/$PACKAGE_DIR/"

exit 0