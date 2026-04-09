#!/bin/bash
# Script de deploiement - Correction du filtrage des pratiquants par organisation
# Date: 2026-01-07
# Probleme: Le dropdown des pratiquants affichait les membres de tous les clubs
#           au lieu de filtrer par l'organisation de l'utilisateur

set -e

REMOTE_USER="martialc"
REMOTE_HOST="vps-af24e24f.vps.ovh.net"
REMOTE_PATH="/home/martialc/public_html/martialcomp"
LOCAL_FILE="apps/finances/forms/transaction_forms.py"

echo "=== Deploiement de la correction du filtrage des pratiquants ==="

# 1. Copier le fichier corrige
echo "1. Copie du fichier corrige..."
scp "$LOCAL_FILE" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/${LOCAL_FILE}"

# 2. Redemarrer Gunicorn
echo "2. Redemarrage de Gunicorn..."
ssh "${REMOTE_USER}@${REMOTE_HOST}" << 'EOF'
cd /home/martialc/public_html/martialcomp
source venv/bin/activate

# Redemarrer gunicorn
pkill -HUP gunicorn || echo "Signal HUP envoye"

# Ou si systemd est utilise:
# sudo systemctl restart gunicorn

echo "Gunicorn redemarre."
EOF

echo ""
echo "=== Deploiement termine ==="
echo ""
echo "La correction appliquee:"
echo "- Le dropdown 'Membre associe' affiche maintenant uniquement les pratiquants"
echo "  de votre organisation KHIPHAP (et non plus KhiphapGL ou autres clubs)"
echo ""
echo "Testez en modifiant une transaction sur https://martialcomp.com/en/finances/transactions/"
