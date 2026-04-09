#!/bin/bash
# =============================================================================
# DEPLOIEMENT DU MODULE STREAMING HYBRIDE - MartialComp
# =============================================================================
# Date: 2026-01-17
# Description: Script de deploiement du module de streaming integre
# Plateformes supportees: YouTube, Twitch, Vimeo, Facebook Live, Dailymotion
# =============================================================================

set -e  # Arreter en cas d'erreur

echo "=============================================="
echo "DEPLOIEMENT MODULE STREAMING - MartialComp"
echo "=============================================="

# Configuration
REMOTE_HOST="u]r.net"
REMOTE_USER="martialcomp"
REMOTE_PATH="/var/www/martialcomp"
SSH_KEY="~/.ssh/id_rsa"

# Fichiers a deployer
FILES_TO_DEPLOY=(
    # Migration
    "apps/competitions/migrations/0031_add_streaming_fields.py"

    # Models (streaming fields)
    "apps/competitions/models/competitions.py"

    # Forms
    "apps/competitions/forms/streaming.py"

    # Views
    "apps/competitions/views/streaming.py"

    # URLs
    "apps/competitions/urls/streaming.py"
    "apps/competitions/urls/__init__.py"

    # Templates
    "apps/competitions/templates/competitions/streaming/live.html"
    "apps/competitions/templates/competitions/streaming/config.html"

    # Settings (CSP config)
    "config/settings/base.py"

    # Traductions
    "locale/fr/LC_MESSAGES/django.po"
    "locale/en/LC_MESSAGES/django.po"
)

echo ""
echo "1. Verification des fichiers locaux..."
for file in "${FILES_TO_DEPLOY[@]}"; do
    if [ -f "$file" ]; then
        echo "   [OK] $file"
    else
        echo "   [ERREUR] $file manquant!"
        exit 1
    fi
done

echo ""
echo "2. Transfert des fichiers vers le serveur..."
for file in "${FILES_TO_DEPLOY[@]}"; do
    echo "   Transfert: $file"
    scp -i $SSH_KEY "$file" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/$file"
done

echo ""
echo "3. Execution des commandes sur le serveur..."
ssh -i $SSH_KEY "$REMOTE_USER@$REMOTE_HOST" << 'ENDSSH'
cd /var/www/martialcomp

# Activer l'environnement virtuel
source venv/bin/activate

# Appliquer la migration streaming
echo "   Applying streaming migration..."
python manage.py migrate competitions 0031_add_streaming_fields --settings=config.settings.production

# Compiler les traductions
echo "   Compiling translations..."
python manage.py compilemessages --locale=fr --locale=en --settings=config.settings.production || true

# Collecter les fichiers statiques
echo "   Collecting static files..."
python manage.py collectstatic --noinput --settings=config.settings.production

# Redemarrer Gunicorn
echo "   Restarting Gunicorn..."
sudo systemctl restart gunicorn

# Vider le cache Cloudflare (optionnel)
echo "   Purging Cloudflare cache..."
# curl -X POST "https://api.cloudflare.com/client/v4/zones/ZONE_ID/purge_cache" \
#      -H "Authorization: Bearer CF_TOKEN" \
#      -H "Content-Type: application/json" \
#      --data '{"purge_everything":true}'

echo "   Deployment complete!"
ENDSSH

echo ""
echo "=============================================="
echo "DEPLOIEMENT TERMINE AVEC SUCCES"
echo "=============================================="
echo ""
echo "URLs disponibles:"
echo "  - Page Live:   /competitions/streaming/{id}/live/"
echo "  - Config:      /competitions/streaming/{id}/config/"
echo "  - API Config:  /competitions/streaming/api/{id}/"
echo "  - API Public:  /competitions/streaming/api/{id}/public/"
echo "  - API Status:  /competitions/streaming/api/{id}/{start|stop}/"
echo ""
echo "Plateformes supportees:"
echo "  - YouTube (youtube.com/watch, youtu.be, youtube.com/live)"
echo "  - Twitch (twitch.tv/channel)"
echo "  - Vimeo (vimeo.com/video)"
echo "  - Facebook Live (facebook.com/video)"
echo "  - Dailymotion (dailymotion.com/video)"
echo "  - URL personnalisee (embed direct)"
echo ""
