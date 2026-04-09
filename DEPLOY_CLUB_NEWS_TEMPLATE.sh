#!/bin/bash
# Script de deploiement - Section Actualites pour le template Club
# Date: 2026-01-09

echo "=== Deploiement Section Actualites Club ==="
echo ""

# Configuration
REMOTE_USER="pierrep99"
REMOTE_HOST="martialcomp.com"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

# Fichiers a deployer
FILES=(
    "apps/competitions/views/organization_sites.py"
    "apps/competitions/templates/organizations/sites/club_template.html"
)

echo "Fichiers a deployer:"
for file in "${FILES[@]}"; do
    echo "  - $file"
done
echo ""

# Deployer chaque fichier
for file in "${FILES[@]}"; do
    echo "Deploiement: $file"
    if [ -f "$file" ]; then
        scp "$file" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/$file"
        if [ $? -eq 0 ]; then
            echo "  ✓ OK"
        else
            echo "  ✗ ERREUR"
        fi
    else
        echo "  ✗ Fichier non trouve"
    fi
done

echo ""
echo "Redemarrage du serveur..."
ssh "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_PATH && sudo systemctl restart gunicorn"

echo ""
echo "=== Deploiement termine ==="
echo ""
echo "Modifications deployees:"
echo "  1. organization_sites.py - Ajout de recent_news dans get_club_context()"
echo "  2. club_template.html - Ajout de la section Actualites avec:"
echo "     - Lien 'Actualites' dans la navigation"
echo "     - Section HTML affichant les news"
echo "     - Styles CSS pour les cartes news"
echo ""
echo "Testez sur: https://martialcomp.com/org/song-phuong/"
