#!/bin/bash

# Script pour définir les permissions correctes sur un serveur Plesk
# À exécuter sur le serveur de production après extraction du package

HTTPDOCS="/var/www/vhosts/martialcomp.com/httpdocs"
PLESK_USER="martialcomp"  # Remplacer par l'utilisateur réel Plesk
PLESK_GROUP="psacln"      # Groupe par défaut Plesk

echo "🔒 Configuration des permissions pour Plesk..."
echo "📍 Répertoire: $HTTPDOCS"
echo "👤 Utilisateur: $PLESK_USER:$PLESK_GROUP"
echo ""

# Vérifier que nous sommes dans le bon répertoire
if [ ! -d "$HTTPDOCS" ]; then
    echo "❌ Erreur: Le répertoire $HTTPDOCS n'existe pas!"
    exit 1
fi

cd $HTTPDOCS

# 1. Changer le propriétaire de tous les fichiers
echo "👥 Attribution des propriétaires..."
sudo chown -R $PLESK_USER:$PLESK_GROUP .

# 2. Permissions de base (lecture pour tous, écriture pour propriétaire)
echo "📁 Configuration des permissions de base..."
find . -type d -exec chmod 755 {} \;
find . -type f -exec chmod 644 {} \;

# 3. Permissions spéciales pour les scripts Python
echo "🐍 Permissions pour les fichiers Python..."
find . -name "*.py" -exec chmod 644 {} \;
chmod 755 manage.py

# 4. Dossiers avec écriture (media, logs, staticfiles)
echo "✏️  Permissions d'écriture pour les dossiers de données..."
chmod -R 775 media/
chmod -R 775 logs/
chmod -R 775 staticfiles/

# 5. Protection des fichiers sensibles
echo "🔐 Protection des fichiers sensibles..."
if [ -f ".env" ]; then
    chmod 600 .env
fi
if [ -f ".env.production" ]; then
    chmod 600 .env.production
fi

# 6. Permissions pour Passenger
echo "🚂 Configuration Passenger..."
if [ -f "passenger_wsgi.py" ]; then
    chmod 644 passenger_wsgi.py
fi

# 7. S'assurer que les dossiers nécessaires existent
echo "📂 Création des dossiers manquants..."
mkdir -p media logs staticfiles
chmod 775 media logs staticfiles

echo ""
echo "✅ Permissions configurées avec succès!"
echo ""
echo "📋 Résumé:"
echo "   - Propriétaire: $PLESK_USER:$PLESK_GROUP"
echo "   - Dossiers: 755"
echo "   - Fichiers: 644"
echo "   - Dossiers avec écriture: 775 (media/, logs/, staticfiles/)"
echo "   - manage.py: 755 (exécutable)"
echo ""
echo "⚠️  Notes importantes:"
echo "   1. Vérifiez que l'utilisateur $PLESK_USER existe"
echo "   2. Redémarrez l'application dans Plesk après ces changements"
echo "   3. Testez l'upload de fichiers pour vérifier les permissions"