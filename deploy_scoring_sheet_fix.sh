#!/bin/bash
# Script de déploiement pour les corrections de la feuille de notation (scoring_sheet)
# Corrections UI: Photo cliquable, Nom cliquable, Boutons T1/T2 fonctionnels

echo "=== Déploiement des corrections Feuille de Notation V2 ==="
echo ""

# Configuration - Utiliser pierrep99@martialcomp.com directement
REMOTE_USER="pierrep99"
REMOTE_HOST="martialcomp.com"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

# Fichiers à déployer
FILES=(
    "apps/competitions/templates/competitions/technical_scoring/scoring_sheet.html"
    "apps/competitions/views/technical_scoring.py"
)

echo "Fichiers à déployer:"
for FILE in "${FILES[@]}"; do
    echo "  - $FILE"
done
echo ""

# Vérifier que les fichiers locaux existent
echo "Vérification des fichiers locaux..."
for FILE in "${FILES[@]}"; do
    if [ ! -f "$FILE" ]; then
        echo "ERREUR: Le fichier $FILE n'existe pas localement"
        exit 1
    fi
    echo "✓ $FILE existe"
done
echo ""

# Copier les fichiers vers la production
echo "Copie des fichiers vers la production..."
for FILE in "${FILES[@]}"; do
    echo "  Copie de $FILE..."
    scp "$FILE" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/$FILE"
    if [ $? -ne 0 ]; then
        echo "✗ ERREUR: Impossible de copier $FILE"
        exit 1
    fi
    echo "  ✓ $FILE copié"
done
echo ""

# Redémarrer Gunicorn
echo "Redémarrage de Gunicorn..."
ssh "$REMOTE_USER@$REMOTE_HOST" "pkill -HUP gunicorn || sudo systemctl reload gunicorn 2>/dev/null || touch $REMOTE_PATH/config/wsgi.py"
echo "✓ Gunicorn redémarré"
echo ""

echo "=== Déploiement terminé ==="
echo ""
echo "Corrections appliquées :"
echo "  ✓ Photo du pratiquant CLIQUABLE pour noter"
echo "  ✓ Nom du pratiquant CLIQUABLE pour noter"
echo "  ✓ Bouton T1 corrigé avec fallback si Bootstrap absent"
echo "  ✓ Debug logs ajoutés pour diagnostic"
echo "  ✓ Modal simple en fallback si pavé numérique indisponible"
echo ""
echo "Testez la feuille de notation :"
echo "  https://martialcomp.com/fr/competitions/technical-scoring/sheet/category/13/"
