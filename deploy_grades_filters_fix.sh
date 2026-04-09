#!/bin/bash
# Script de déploiement pour corriger les filtres et bulk-assignment

echo "=== Déploiement des corrections pour les grades ==="
echo ""

# Définir les variables
REMOTE_HOST="martialcomp-production"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

# Fichiers à déployer
FILES_TO_DEPLOY=(
    "apps/grades/views/bulk.py"
)

echo "Fichiers à déployer:"
for file in "${FILES_TO_DEPLOY[@]}"; do
    echo "  - $file"
done
echo ""

# Copier les fichiers
echo "Copie des fichiers vers le serveur..."
for file in "${FILES_TO_DEPLOY[@]}"; do
    echo -n "  Copie de $file... "
    scp "$file" "$REMOTE_HOST:$REMOTE_PATH/$file" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "OK"
    else
        echo "ERREUR"
        exit 1
    fi
done

# Corrections directes sur le serveur pour les templates
echo ""
echo "Application des corrections sur les templates..."

ssh "$REMOTE_HOST" << 'EOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

# Correction 1: Dashboard grades - Corriger la comparaison de discipline
echo "  Correction du template dashboard.html..."
sudo sed -i 's/{% if discipline.id|stringformat:"s" == selected_discipline %}/{% if discipline.id|stringformat:"s" == selected_discipline|stringformat:"s" %}/g' apps/grades/templates/grades/dashboard.html

# Correction 2: Exam list - Corriger la comparaison bizarre
echo "  Correction du template exam_list.html..."
sudo sed -i 's/{% if selected_discipline == discipline.id|stringformat:"i" %}/{% if selected_discipline|stringformat:"s" == discipline.id|stringformat:"s" %}/g' apps/grades/templates/grades/exam_list.html

echo ""
echo "Corrections appliquées!"
EOF

echo ""
echo "Redémarrage de Gunicorn..."
ssh "$REMOTE_HOST" "sudo systemctl restart martialcomp.service"

echo ""
echo "=== Déploiement terminé ==="
echo ""
echo "Vérifications à faire :"
echo "1. https://martialcomp.com/fr/grades/bulk-assignment/ - Devrait fonctionner sans erreur 500"
echo "2. https://martialcomp.com/fr/grades/dashboard/ - Les filtres discipline devraient fonctionner"
echo "3. https://martialcomp.com/fr/grades/exam/ - Les filtres devraient fonctionner"