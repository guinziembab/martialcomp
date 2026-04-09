#!/bin/bash
# Script de deploiement pour la vue "Equipes par Categorie"
# Theme sombre + Vue groupee par categorie

echo "=== Deploiement Vue Equipes par Categorie ==="
echo ""

# Configuration
SSH_ALIAS="martialcomp-production"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

# Fichiers a deployer
FILES=(
    "apps/competitions/models/combat.py"
    "apps/competitions/views/combat.py"
    "apps/competitions/forms/combat_forms.py"
    "apps/competitions/urls/combat.py"
    "apps/competitions/templates/competitions/combat/base.html"
    "apps/competitions/templates/competitions/combat/liste_equipes.html"
    "apps/competitions/templates/competitions/combat/liste_equipes_par_categorie.html"
    "apps/competitions/templates/competitions/combat/select_competition_equipes.html"
    "apps/competitions/templates/competitions/combat/detail_equipe.html"
    "apps/competitions/templates/competitions/combat/form_equipe.html"
    "apps/competitions/templates/competitions/combat/form_membre_equipe.html"
    "apps/competitions/templates/competitions/combat/liste_poules.html"
    "apps/competitions/templates/competitions/combat/detail_poule.html"
    "apps/competitions/templates/competitions/combat/generer_poules.html"
    "apps/competitions/templates/competitions/combat/liste_combats.html"
    "apps/competitions/templates/competitions/combat/form_combat.html"
    "apps/competitions/migrations/0016_add_category_to_equipe.py"
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

    # Creer le dossier de destination si necessaire
    REMOTE_DIR=$(dirname "$REMOTE_PATH/$FILE")
    ssh "$SSH_ALIAS" "mkdir -p $REMOTE_DIR"

    scp "$FILE" "$SSH_ALIAS:$REMOTE_PATH/$FILE"
    if [ $? -ne 0 ]; then
        echo "ERREUR: Impossible de copier $FILE"
        exit 1
    fi
    echo "  OK $FILE copie"
done
echo ""

# Executer les migrations
echo "Execution des migrations..."
ssh "$SSH_ALIAS" "cd $REMOTE_PATH && python3 manage.py migrate competitions --no-input"
if [ $? -ne 0 ]; then
    echo "AVERTISSEMENT: Migration echouee, verifier manuellement"
else
    echo "OK Migrations executees"
fi
echo ""

# Redemarrer Gunicorn
echo "Redemarrage de Gunicorn..."
ssh "$SSH_ALIAS" "pkill -HUP gunicorn || sudo systemctl reload gunicorn 2>/dev/null || touch $REMOTE_PATH/config/wsgi.py"
echo "OK Gunicorn redemarre"
echo ""

echo "=== Deploiement termine ==="
echo ""
echo "NOUVELLES FONCTIONNALITES :"
echo ""
echo "  VUE EQUIPES PAR CATEGORIE:"
echo "    - Nouvelle URL: /fr/competitions/combat/equipes/par-categorie/competition/<id>/"
echo "    - Equipes groupees par categorie pour une competition specifique"
echo "    - Statistiques: total equipes, categories, non-assignees"
echo "    - Planification des combats par categorie"
echo ""
echo "  FILTRAGE PAR COMPETITION:"
echo "    - Les equipes sont maintenant filtrees par competition"
echo "    - Page de selection de competition si aucune n'est specifiee"
echo "    - Plus de melange entre les competitions"
echo ""
echo "  THEME SOMBRE APPLIQUE:"
echo "    - Page liste des equipes"
echo "    - Page equipes par categorie"
echo "    - Page selection de competition"
echo "    - Page detail equipe"
echo "    - Page formulaire equipe (modifier)"
echo "    - Page ajout membre equipe"
echo "    - Page liste des poules"
echo "    - Page detail poule"
echo "    - Page generation automatique des poules"
echo "    - Page liste des combats (tableau de bord)"
echo "    - Page formulaire creation/modification combat"
echo "    - Template de base combat avec sidebar"
echo "    - Variables CSS coherentes"
echo ""
echo "  NOUVEAU CHAMP CATEGORY:"
echo "    - Les equipes peuvent etre assignees a une categorie"
echo "    - Formulaire mis a jour avec selection de categorie"
echo "    - API pour charger les categories dynamiquement"
echo ""
echo "  CORRECTION URLs POULES (conflit resolu):"
echo "    - /fr/competitions/combat/poules/competition/<id>/ -> liste des poules"
echo "    - /fr/competitions/combat/poules/detail/<id>/ -> detail d'une poule"
echo "    - /fr/competitions/combat/poules/competition/<id>/creer/ -> creer une poule"
echo "    - /fr/competitions/combat/poules/detail/<id>/modifier/ -> modifier une poule"
echo "    - /fr/competitions/combat/poules/detail/<id>/supprimer/ -> supprimer une poule"
echo "    - /fr/competitions/combat/poules/competition/<id>/generer/ -> generer des poules"
echo "    - /fr/competitions/combat/poules/detail/<id>/suivi/ -> suivi d'une poule"
echo ""
echo "Testez la page :"
echo "  https://martialcomp.com/fr/competitions/combat/equipes/"
echo "  (Vous serez invite a selectionner une competition)"
echo ""
