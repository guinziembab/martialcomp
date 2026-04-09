#!/bin/bash
# ============================================================
# CONFIGURATION OAUTH GOOGLE ET FACEBOOK EN PRODUCTION
# Date: 2024-12-21
# ============================================================
#
# INSTRUCTIONS:
# 1. Remplacez VOTRE_GOOGLE_CLIENT_SECRET par la vraie valeur
# 2. Exécutez ce script depuis votre machine locale
# ============================================================

set -e

# Configuration SSH
SSH_TARGET="martialcomp-production"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

# ============================================================
# IDENTIFIANTS OAUTH (REMPLACEZ GOOGLE_SECRET)
# ============================================================

# Google OAuth
GOOGLE_CLIENT_ID="243898642746-6tjnpdflrrsetgif0fne7pgs4v66j6j5.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET="VOTRE_GOOGLE_CLIENT_SECRET"  # <-- REMPLACEZ CETTE VALEUR

# Facebook OAuth
FACEBOOK_APP_ID="1415333696343612"
FACEBOOK_APP_SECRET="fd1e66ffcd47958997274808d0c2ec64"

echo "==========================================="
echo "CONFIGURATION OAUTH PRODUCTION"
echo "Date: $(date)"
echo "==========================================="

# Vérification que le secret Google a été remplacé
if [ "$GOOGLE_CLIENT_SECRET" = "VOTRE_GOOGLE_CLIENT_SECRET" ]; then
    echo ""
    echo "⚠️  ERREUR: Vous devez remplacer VOTRE_GOOGLE_CLIENT_SECRET"
    echo "   par la vraie clé secrète Google avant d'exécuter ce script."
    echo ""
    echo "   Pour récupérer la clé:"
    echo "   1. Allez sur https://console.cloud.google.com/apis/credentials"
    echo "   2. Cliquez sur 'MartialComp Web Auth'"
    echo "   3. Copiez le 'Secret client'"
    echo ""
    exit 1
fi

echo ""
echo "1. Sauvegarde du fichier .env actuel..."
echo "----------------------------------------"
ssh ${SSH_TARGET} "cd ${REMOTE_PATH} && cp .env .env.backup_oauth_$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo 'Pas de .env existant'"

echo ""
echo "2. Mise à jour des variables OAuth dans .env..."
echo "----------------------------------------"

ssh ${SSH_TARGET} << REMOTE_SCRIPT
cd ${REMOTE_PATH}

# Créer ou mettre à jour le fichier .env avec les variables OAuth
# Supprimer les anciennes entrées si elles existent
if [ -f .env ]; then
    grep -v "^GOOGLE_CLIENT_ID=" .env | grep -v "^GOOGLE_CLIENT_SECRET=" | grep -v "^FACEBOOK_APP_ID=" | grep -v "^FACEBOOK_APP_SECRET=" > .env.tmp || true
    mv .env.tmp .env
fi

# Ajouter les nouvelles variables OAuth
cat >> .env << 'EOF'

# ============================================================
# OAUTH CONFIGURATION - Added $(date +%Y-%m-%d)
# ============================================================
GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
FACEBOOK_APP_ID=${FACEBOOK_APP_ID}
FACEBOOK_APP_SECRET=${FACEBOOK_APP_SECRET}
EOF

echo "Variables OAuth ajoutées au fichier .env"
REMOTE_SCRIPT

echo ""
echo "3. Vérification de la configuration..."
echo "----------------------------------------"
ssh ${SSH_TARGET} << 'VERIFY'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "Variables OAuth dans .env:"
grep -E "^(GOOGLE_|FACEBOOK_)" .env | sed 's/SECRET=.*/SECRET=***MASKED***/'

VERIFY

echo ""
echo "4. Redémarrage de l'application..."
echo "----------------------------------------"
ssh ${SSH_TARGET} << 'RESTART'
cd /var/www/vhosts/martialcomp.com

# Redémarrer Gunicorn
if systemctl is-active --quiet gunicorn 2>/dev/null; then
    sudo systemctl restart gunicorn
    echo "Gunicorn redémarré via systemctl"
elif [ -f /var/www/vhosts/martialcomp.com/run/gunicorn.pid ]; then
    kill -HUP $(cat /var/www/vhosts/martialcomp.com/run/gunicorn.pid) 2>/dev/null || true
    echo "Signal HUP envoyé à Gunicorn"
else
    # Plesk/Apache - touch wsgi pour reload
    touch /var/www/vhosts/martialcomp.com/httpdocs/config/wsgi.py
    echo "WSGI touché pour reload Apache/mod_wsgi"
fi

# Vider le cache Django si nécessaire
source /var/www/vhosts/martialcomp.com/venv/bin/activate
cd /var/www/vhosts/martialcomp.com/httpdocs
python manage.py clearcache 2>/dev/null || echo "Pas de commande clearcache"

RESTART

echo ""
echo "==========================================="
echo "✅ CONFIGURATION OAUTH TERMINÉE"
echo "==========================================="
echo ""
echo "URLs de callback à vérifier dans les consoles développeur:"
echo ""
echo "Google Cloud Console:"
echo "  https://martialcomp.com/accounts/google/login/callback/"
echo ""
echo "Facebook Developers:"
echo "  https://martialcomp.com/accounts/facebook/login/callback/"
echo ""
echo "Testez la connexion sur: https://martialcomp.com/accounts/login/"
echo "==========================================="
