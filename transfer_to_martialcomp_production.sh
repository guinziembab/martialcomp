#!/bin/bash

echo "🚀 Transfert vers martialcomp-production"
echo "========================================"

# Variables
PACKAGE_FILE="federation_production_package_20251015_172243_v2.tar.gz"
REMOTE_HOST="martialcomp-production"
REMOTE_USER="${REMOTE_USER:-}"  # Utilise la variable d'environnement si définie

# Vérifier que le package existe
if [ ! -f "$PACKAGE_FILE" ]; then
    echo "❌ Erreur: Le package $PACKAGE_FILE n'existe pas!"
    exit 1
fi

echo "📦 Package à transférer: $PACKAGE_FILE"
echo "🎯 Destination: $REMOTE_HOST"
echo ""

# Demander le chemin de destination sur le serveur
echo "📍 Où voulez-vous copier le package sur le serveur?"
echo "   (Par défaut: /home/\$USER/)"
read -p "Chemin distant: " REMOTE_PATH
REMOTE_PATH=${REMOTE_PATH:-/home/\$USER/}

# Construire la commande SCP
if [ -n "$REMOTE_USER" ]; then
    SCP_CMD="scp $PACKAGE_FILE ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}"
else
    SCP_CMD="scp $PACKAGE_FILE ${REMOTE_HOST}:${REMOTE_PATH}"
fi

echo ""
echo "📤 Transfert en cours..."
echo "   Commande: $SCP_CMD"
echo ""

# Exécuter le transfert
$SCP_CMD

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Transfert réussi!"
    echo ""
    echo "📝 Prochaines étapes sur le serveur:"
    echo ""
    echo "1. Se connecter au serveur:"
    echo "   ssh $REMOTE_HOST"
    echo ""
    echo "2. Extraire le package:"
    echo "   cd $REMOTE_PATH"
    echo "   tar -xzf $PACKAGE_FILE"
    echo ""
    echo "3. Aller dans le dossier extrait:"
    echo "   cd federation_production_package_20251015_172243"
    echo ""
    echo "4. Vérifier le contenu:"
    echo "   ls -la"
    echo ""
    echo "5. Se déplacer vers le projet Django:"
    echo "   cd /chemin/vers/martialcomp  # Adapter selon votre installation"
    echo ""
    echo "6. Exécuter le déploiement:"
    echo "   bash ${REMOTE_PATH}federation_production_package_20251015_172243/deploy_production.sh"
    echo ""
    echo "7. Redémarrer les services:"
    echo "   sudo systemctl restart apache2  # ou gunicorn"
    echo ""
    
    # Proposer de se connecter directement
    echo "💡 Voulez-vous vous connecter au serveur maintenant? (y/n)"
    read -p "> " CONNECT_NOW
    
    if [[ $CONNECT_NOW =~ ^[Yy]$ ]]; then
        echo ""
        echo "🔌 Connexion au serveur..."
        ssh $REMOTE_HOST
    fi
else
    echo ""
    echo "❌ Erreur lors du transfert!"
    echo ""
    echo "Vérifiez:"
    echo "- Que vous avez accès SSH au serveur"
    echo "- Que le nom d'hôte 'martialcomp-production' est configuré dans ~/.ssh/config"
    echo "- Que vous avez les permissions d'écriture dans $REMOTE_PATH"
fi