#!/bin/bash
# Script de déploiement des corrections:
# 1. EventDetailAPIView (JWT compatible) pour le détail des événements
# 2. avatar_url au niveau racine pour la photo de profil

echo "=== Déploiement des corrections Event Detail et Photo ==="
echo ""

# Variables - À MODIFIER selon votre configuration
REMOTE_USER="votre_user"
REMOTE_HOST="martialcomp.com"
REMOTE_PATH="/var/www/martialcomp"

echo "Fichiers à déployer:"
echo "  - apps/competitions/api/__init__.py (EventDetailAPIView)"
echo "  - api_auth/views.py (avatar_url au niveau racine)"
echo ""

# Option 1: Déploiement via rsync
echo "Option 1: Via rsync (recommandé)"
echo "rsync -avz apps/competitions/api/__init__.py $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/apps/competitions/api/"
echo "rsync -avz api_auth/views.py $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/api_auth/"
echo ""

# Option 2: Déploiement via scp
echo "Option 2: Via scp"
echo "scp apps/competitions/api/__init__.py $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/apps/competitions/api/"
echo "scp api_auth/views.py $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/api_auth/"
echo ""

# Après déploiement
echo "Après le déploiement, redémarrer le serveur:"
echo "sudo systemctl restart gunicorn"
echo "# ou"
echo "sudo supervisorctl restart martialcomp"
echo ""

echo "=== Résumé des modifications ==="
echo ""
echo "1. EventDetailAPIView (apps/competitions/api/__init__.py)"
echo "   - Nouvelle classe API compatible JWT pour /api/competitions/event-detail/<type>/<id>/"
echo "   - Supporte: competition, exam, club/event/training/seminar/meeting/social"
echo ""
echo "2. UserProfileView (api_auth/views.py)"
echo "   - avatar_url ajouté au niveau racine du payload (en plus de user.avatar_url)"
echo "   - Permet au mobile de trouver l'URL de la photo plus facilement"
echo ""
