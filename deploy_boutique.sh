#!/bin/bash
# =============================================================================
# DEPLOIEMENT - Ajout Boutique dans Acces Rapide
# =============================================================================
# Ce script ajoute une 5eme carte "Boutique" dans la section QR codes du site public
#
# Fichiers modifies:
#   - apps/competitions/templates/organizations/sites/club_template.html
#   - apps/competitions/utils/qr_generator_enhanced.py
#
# Utilisation: ./deploy_boutique.sh
# =============================================================================

echo "==========================================="
echo "  DEPLOIEMENT BOUTIQUE CLUB"
echo "==========================================="
echo ""

# 1. Deployer le template avec la carte Boutique
echo "[1/3] Deploiement du template club_template.html..."
scp apps/competitions/templates/organizations/sites/club_template.html martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/organizations/sites/
if [ $? -eq 0 ]; then
    echo "  OK: Template deploye"
else
    echo "  ERREUR: Echec du deploiement template"
    exit 1
fi

# 2. Deployer le generateur de QR codes
echo ""
echo "[2/3] Deploiement de qr_generator_enhanced.py..."
scp apps/competitions/utils/qr_generator_enhanced.py martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/utils/
if [ $? -eq 0 ]; then
    echo "  OK: QR generator deploye"
else
    echo "  ERREUR: Echec du deploiement QR generator"
    exit 1
fi

# 3. Redemarrer gunicorn
echo ""
echo "[3/3] Redemarrage de gunicorn..."
ssh martialcomp-production "pkill -HUP -f 'gunicorn.*config.wsgi'"
if [ $? -eq 0 ]; then
    echo "  OK: Gunicorn redemarre"
else
    echo "  ATTENTION: Verifiez gunicorn manuellement"
fi

echo ""
echo "==========================================="
echo "  DEPLOIEMENT TERMINE"
echo "==========================================="
echo ""
echo "NOUVELLE FONCTIONNALITE:"
echo "  - Carte 'Boutique' ajoutee dans la section Acces Rapide"
echo "  - QR code boutique genere automatiquement"
echo ""
echo "TEST:"
echo "  1. Allez sur https://martialcomp.com/org/khiphap/"
echo "  2. Descendez jusqu'a la section 'Acces Rapide'"
echo "  3. Verifiez que la carte 'Boutique' apparait"
echo ""
