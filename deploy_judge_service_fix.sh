#!/bin/bash
# Script de déploiement pour les corrections JudgeService et template judge_assignments
# Déploie les modifications permettant d'afficher les affectations AdHocJudge

echo "=== Déploiement des corrections JudgeService et Judge Assignments ==="
echo ""

# Configuration
REMOTE_USER="pierrep99"
REMOTE_HOST="martialcomp.com"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

# Fichiers à déployer
FILES=(
    "apps/competitions/services/judge_service.py"
    "apps/competitions/templates/competitions/dashboard/judge_assignments.html"
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
ssh "$REMOTE_USER@$REMOTE_HOST" "sudo systemctl reload gunicorn || sudo systemctl restart gunicorn"
if [ $? -ne 0 ]; then
    echo "✗ ATTENTION: Erreur lors du redémarrage de Gunicorn"
    echo "Tentative avec touch wsgi..."
    ssh "$REMOTE_USER@$REMOTE_HOST" "touch $REMOTE_PATH/config/wsgi.py"
fi
echo "✓ Gunicorn redémarré"
echo ""

# Vider le cache si nécessaire
echo "Vidage du cache Django..."
ssh "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_PATH && source venv/bin/activate && python manage.py clear_cache 2>/dev/null || echo 'Cache clear command not available'"
echo ""

echo "=== Déploiement terminé ==="
echo ""
echo "Corrections appliquées :"
echo "  ✓ JudgeService inclut maintenant les affectations AdHocJudge"
echo "  ✓ Template judge_assignments avec liens cliquables vers feuille de notation"
echo "  ✓ Badges de statut pour les catégories"
echo ""
echo "Testez la page :"
echo "  https://martialcomp.com/fr/competitions/dashboard/judge/assignments/"
