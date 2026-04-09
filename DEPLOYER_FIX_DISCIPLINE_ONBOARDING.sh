#!/bin/bash
# =============================================================================
# CORRECTION BUG ASSIGNATION AUTOMATIQUE DISCIPLINE AIKIDO
# Date: 2025-11-26
# =============================================================================
#
# PROBLÈME IDENTIFIÉ:
# -------------------
# Lors de la création d'un nouveau club via l'onboarding, la discipline "Aïkido"
# (ID 75) est automatiquement assignée même si l'utilisateur ne sélectionne
# aucune discipline.
#
# CAUSE:
# ------
# Le template club_creation.html contenait une condition problématique:
#   {% if discipline.id in form.disciplines.value or discipline in form.instance.disciplines.all %}checked{% endif %}
#
# Cette condition pouvait pré-cocher des checkboxes de manière inattendue car:
# 1. form.disciplines n'existe pas dans ClubCreationForm
# 2. form.instance.disciplines.all sur une instance non sauvegardée a un comportement imprévisible
#
# SOLUTION:
# ---------
# Supprimer complètement la condition "checked" du template pour que les
# checkboxes ne soient jamais pré-cochées lors de la création d'un nouveau club.
#
# =============================================================================

echo "=== CORRECTION BUG DISCIPLINE AIKIDO - PRODUCTION ==="
echo "Date: $(date)"
echo ""

# Configuration
PRODUCTION_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
VENV_PATH="/var/www/vhosts/martialcomp.com/venv"
TEMPLATE_PATH="apps/competitions/templates/competitions/onboarding/club_creation.html"

# 1. Se connecter au serveur (à exécuter manuellement)
echo "=== ÉTAPE 1: Connexion au serveur ==="
echo "Exécutez: ssh root@martialcomp.com"
echo ""

# 2. Créer un backup
echo "=== ÉTAPE 2: Créer un backup du fichier ==="
echo "cd $PRODUCTION_PATH"
echo "cp $TEMPLATE_PATH ${TEMPLATE_PATH}.backup_\$(date +%Y%m%d_%H%M%S)"
echo ""

# 3. Vérifier le contenu actuel
echo "=== ÉTAPE 3: Vérifier le contenu actuel ==="
echo "grep -n 'checked' $TEMPLATE_PATH"
echo ""

# 4. Appliquer la correction
echo "=== ÉTAPE 4: Appliquer la correction ==="
echo "# Remplacer les lignes problématiques avec sed:"
echo ""
cat << 'EOF'
# Rechercher et remplacer la section disciplines dans le template:
# L'ancienne version avait cette condition sur la ligne 556:
#   {% if discipline.id in form.disciplines.value or discipline in form.instance.disciplines.all %}checked{% endif %}
#
# La nouvelle version supprime complètement cette condition:

sed -i 's/{% if discipline.id in form.disciplines.value or discipline in form.instance.disciplines.all %}checked{% endif %}//g' apps/competitions/templates/competitions/onboarding/club_creation.html

# Ou pour une correction plus précise, utilisez nano:
nano apps/competitions/templates/competitions/onboarding/club_creation.html

# Trouvez la ligne (environ 555-556) qui ressemble à:
#   <input type="checkbox" name="disciplines" value="{{ discipline.id }}"
#          class="form-check-input" id="discipline_{{ discipline.id }}"
#          {% if discipline.id in form.disciplines.value or discipline in form.instance.disciplines.all %}checked{% endif %}>
#
# Et remplacez-la par:
#   <input type="checkbox" name="disciplines" value="{{ discipline.id }}"
#          class="form-check-input" id="discipline_{{ discipline.id }}"
#          autocomplete="off">

EOF

echo ""

# 5. Vérifier la correction
echo "=== ÉTAPE 5: Vérifier la correction ==="
echo "grep -n 'checked' $TEMPLATE_PATH"
echo "# Devrait ne plus afficher la ligne avec 'discipline.id in form.disciplines.value'"
echo ""

# 6. Redémarrer gunicorn
echo "=== ÉTAPE 6: Redémarrer gunicorn ==="
echo "pkill -f gunicorn"
echo "cd $PRODUCTION_PATH && $VENV_PATH/bin/gunicorn --workers 3 --bind 127.0.0.1:8888 config.wsgi:application --daemon"
echo ""

# 7. Vérifier que gunicorn fonctionne
echo "=== ÉTAPE 7: Vérifier gunicorn ==="
echo "ps aux | grep gunicorn"
echo "curl -I http://127.0.0.1:8888/health/ 2>/dev/null | head -5"
echo ""

# 8. Test de validation
echo "=== ÉTAPE 8: Test de validation ==="
echo "# Créer un nouveau compte test et vérifier que:"
echo "# 1. Les checkboxes de disciplines ne sont pas pré-cochées"
echo "# 2. Aucune discipline n'est assignée si on n'en sélectionne pas"
echo "# 3. Les disciplines sélectionnées sont bien assignées"
echo ""

echo "=== FIN DU SCRIPT ==="
echo ""
echo "COMMANDES RAPIDES À COPIER-COLLER:"
echo "=================================="
cat << 'COMMANDS'
# Tout en une commande (après SSH):
cd /var/www/vhosts/martialcomp.com/httpdocs && \
cp apps/competitions/templates/competitions/onboarding/club_creation.html apps/competitions/templates/competitions/onboarding/club_creation.html.backup_$(date +%Y%m%d_%H%M%S) && \
sed -i 's/{% if discipline.id in form.disciplines.value or discipline in form.instance.disciplines.all %}checked{% endif %}//g' apps/competitions/templates/competitions/onboarding/club_creation.html && \
pkill -f gunicorn && \
/var/www/vhosts/martialcomp.com/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8888 config.wsgi:application --daemon && \
echo "Correction appliquée avec succès!"
COMMANDS
