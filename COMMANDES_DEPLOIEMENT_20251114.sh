#!/bin/bash
# Commandes de déploiement pour la correction du Competition Management
# Date: 2025-11-14

echo "=========================================="
echo "DÉPLOIEMENT - Competition Management Fix"
echo "=========================================="
echo ""
echo "Exécutez ces commandes sur le serveur de production:"
echo ""

cat << 'EOF'
# ============================================
# ÉTAPE 1: Connexion au serveur
# ============================================
ssh martialcomp-production

# ============================================
# ÉTAPE 2: Navigation vers le projet
# ============================================
cd /home/martialcomp/martialcomp

# ============================================
# ÉTAPE 3: Activation de l'environnement virtuel
# ============================================
source venv/bin/activate

# ============================================
# ÉTAPE 4: Vérification de la branche actuelle
# ============================================
git branch --show-current
# Devrait afficher: fix/federation-dashboard

# ============================================
# ÉTAPE 5: Récupération des modifications
# ============================================
git fetch origin
git pull origin fix/federation-dashboard

# ============================================
# ÉTAPE 6: Vérification des fichiers modifiés
# ============================================
echo "Fichiers modifiés:"
git log -1 --name-only --oneline

# ============================================
# ÉTAPE 7: Vérification de la syntaxe Python
# ============================================
python -m py_compile apps/competitions/views/competition_management_pro.py
echo "✓ Syntaxe Python OK"

# ============================================
# ÉTAPE 8: Collecte des fichiers statiques
# ============================================
python manage.py collectstatic --noinput

# ============================================
# ÉTAPE 9: Vérification des URLs
# ============================================
python manage.py show_urls | grep -E "api_get_competition_types|api_get_competition_categories"
# Devrait afficher les 2 nouvelles URLs

# ============================================
# ÉTAPE 10: Redémarrage de Gunicorn
# ============================================
sudo systemctl restart gunicorn

# Attendre 3 secondes
sleep 3

# Vérifier le statut
sudo systemctl status gunicorn --no-pager

# ============================================
# ÉTAPE 11: Rechargement de Nginx
# ============================================
sudo systemctl reload nginx

# ============================================
# ÉTAPE 12: Vérification des logs
# ============================================
echo ""
echo "Dernières lignes des logs Gunicorn:"
sudo journalctl -u gunicorn -n 30 --no-pager

# ============================================
# ÉTAPE 13: Test des APIs
# ============================================
echo ""
echo "Test de l'API Types:"
curl -I https://martialcomp.com/en/competitions/club/api/competitions/4/types/list/

echo ""
echo "Test de l'API Catégories:"
curl -I https://martialcomp.com/en/competitions/club/api/competitions/4/categories/list/

# ============================================
# ÉTAPE 14: Surveillance des logs en temps réel
# ============================================
echo ""
echo "Surveillance des logs (Ctrl+C pour arrêter):"
sudo journalctl -u gunicorn -f

EOF

echo ""
echo "=========================================="
echo "FIN DES COMMANDES"
echo "=========================================="
echo ""
echo "Alternative: Utiliser le script automatique"
echo "./deploy_fix_competition_management.sh"
echo ""
