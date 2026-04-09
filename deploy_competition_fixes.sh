#!/bin/bash
# Script de déploiement des corrections pour les compétitions

echo "=== Déploiement des corrections pour les compétitions ==="
echo ""

# Configuration
PRODUCTION_SERVER="martialcomp-production"
PRODUCTION_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

# 1. Créer l'archive
echo "1. Création de l'archive..."
tar -czf competition_fixes.tar.gz \
    apps/competitions/views/competitions.py \
    apps/competitions/templates/competitions/dashboard/club.html

echo "   Archive créée: competition_fixes.tar.gz"

# 2. Transférer sur le serveur
echo ""
echo "2. Transfert vers le serveur de production..."
scp competition_fixes.tar.gz $PRODUCTION_SERVER:~/

# 3. Instructions pour le déploiement
echo ""
echo "3. Connexion au serveur et application des corrections..."
ssh $PRODUCTION_SERVER << 'REMOTE_COMMANDS'
cd /var/www/vhosts/martialcomp.com/httpdocs

# Créer une sauvegarde
echo "   - Création de la sauvegarde..."
sudo mkdir -p backups/competition_fixes_$(date +%Y%m%d_%H%M%S)
sudo cp apps/competitions/views/competitions.py backups/competition_fixes_$(date +%Y%m%d_%H%M%S)/
sudo cp apps/competitions/templates/competitions/dashboard/club.html backups/competition_fixes_$(date +%Y%m%d_%H%M%S)/

# Extraire l'archive
echo "   - Extraction des fichiers..."
sudo tar -xzf ~/competition_fixes.tar.gz

# Corriger les permissions
echo "   - Correction des permissions..."
sudo chown -R www-data:www-data apps/competitions/views/competitions.py
sudo chown -R www-data:www-data apps/competitions/templates/competitions/dashboard/club.html

# Nettoyer les fichiers Python compilés
echo "   - Nettoyage des fichiers compilés..."
sudo find apps/competitions/views -name "*.pyc" -delete
sudo find apps/competitions/views/__pycache__ -type f -delete 2>/dev/null

# Redémarrer les services
echo "   - Redémarrage des services..."
sudo kill -HUP $(ps aux | grep gunicorn | grep -v grep | awk '{print $2}' | head -1)
sudo systemctl restart apache2

echo "   ✓ Déploiement terminé"
REMOTE_COMMANDS

echo ""
echo "=== Déploiement terminé ==="
echo ""
echo "Résumé des corrections:"
echo "1. ✓ Le bouton 'Éditer' est maintenant visible dans le dropdown des actions"
echo "2. ✓ L'erreur 500 sur la vue détail a été corrigée"
echo "   - Gestion du cas où JudgeAssignment n'existe pas"
echo "   - Import conditionnel et utilisation sécurisée"
echo ""
echo "Test:"
echo "- Aller sur https://martialcomp.com/fr/competitions/dashboard/club/"
echo "- Onglet 'Compétitions' → Le bouton 'Éditer' est dans le menu dropdown"
echo "- Cliquer sur 'Vue' → La page détail doit s'afficher sans erreur"

# Nettoyer
rm -f competition_fixes.tar.gz