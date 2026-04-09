#!/bin/bash
# Script de deploiement pour les templates Resultats et Podium
# Theme sombre harmonise + Podium festif avec confettis

echo "=== Deploiement Templates Resultats & Podium ==="
echo ""

# Configuration
SSH_ALIAS="martialcomp-production"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

# Fichiers a deployer
FILES=(
    "apps/competitions/templates/competitions/management/category_results.html"
    "apps/competitions/templates/competitions/management/podium_view.html"
)

echo "Fichiers a deployer:"
for FILE in "${FILES[@]}"; do
    echo "  - $FILE"
done
echo ""

# Verifier que les fichiers locaux existent
echo "Verification des fichiers locaux..."
for FILE in "${FILES[@]}"; do
    if [ ! -f "$FILE" ]; then
        echo "ERREUR: Le fichier $FILE n'existe pas localement"
        exit 1
    fi
    echo "OK $FILE existe"
done
echo ""

# Copier les fichiers vers la production
echo "Copie des fichiers vers la production..."
for FILE in "${FILES[@]}"; do
    echo "  Copie de $FILE..."
    scp "$FILE" "$SSH_ALIAS:$REMOTE_PATH/$FILE"
    if [ $? -ne 0 ]; then
        echo "ERREUR: Impossible de copier $FILE"
        exit 1
    fi
    echo "  OK $FILE copie"
done
echo ""

# Redemarrer Gunicorn
echo "Redemarrage de Gunicorn..."
ssh "$SSH_ALIAS" "pkill -HUP gunicorn || sudo systemctl reload gunicorn 2>/dev/null || touch $REMOTE_PATH/config/wsgi.py"
echo "OK Gunicorn redemarre"
echo ""

echo "=== Deploiement termine ==="
echo ""
echo "CORRECTIONS APPLIQUEES :"
echo ""
echo "  TEMPLATE RESULTATS (category_results.html):"
echo "    - CORRIGE: Theme sombre applique (etait blanc/clair)"
echo "    - Variables CSS :root pour coherence"
echo "    - Badges de rang avec effet lumineux (or, argent, bronze)"
echo "    - Tableau des resultats avec hover effects"
echo "    - Modal d'export avec theme sombre"
echo ""
echo "  TEMPLATE PODIUM (podium_view.html):"
echo "    - CORRIGE: Trophee deplace dans l'en-tete (ne chevauche plus le gagnant)"
echo "    - CORRIGE: Ex-aequo bronze - un seul affiche sur le podium"
echo "    - CORRIGE: Logos des clubs affiches dans les cartes medailles"
echo "    - Scores retires des blocs podium (nombre seulement)"
echo "    - Design festif avec confettis animes"
echo "    - Etoiles scintillantes en arriere-plan"
echo "    - Podiums avec effets lumineux (glow)"
echo "    - Mode plein ecran pour affichage public"
echo ""
echo "Testez les pages :"
echo "  Resultats: https://martialcomp.com/fr/competitions/management/scoring/4/category/13/results/"
echo "  Podium: https://martialcomp.com/fr/competitions/management/4/results/category/13/podium/"
echo ""
