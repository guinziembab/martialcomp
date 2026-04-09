#!/bin/bash
# Script de déploiement pour corriger le problème de logout

echo "=== Déploiement de la correction du logout ==="
echo ""

# Configuration
PRODUCTION_SERVER="martialcomp-production"
PRODUCTION_PATH="/var/www/martialcomp.com"

# 1. Créer l'archive des fichiers à déployer
echo "1. Création de l'archive..."
tar -czf logout_fix_deploy.tar.gz \
    apps/competitions/views/auth.py \
    apps/competitions/adapters.py \
    debug_logout_production.py

echo "   Archive créée: logout_fix_deploy.tar.gz"

# 2. Instructions de déploiement
echo ""
echo "2. Instructions pour le déploiement:"
echo ""
echo "   a) Transférer l'archive sur le serveur:"
echo "      scp logout_fix_deploy.tar.gz $PRODUCTION_SERVER:~/"
echo ""
echo "   b) Se connecter au serveur:"
echo "      ssh $PRODUCTION_SERVER"
echo ""
echo "   c) Sur le serveur, exécuter:"
cat << 'REMOTE_SCRIPT'
      # Aller dans le répertoire de l'application
      cd /var/www/martialcomp.com
      
      # Créer une sauvegarde
      sudo mkdir -p backups/logout_fix_$(date +%Y%m%d_%H%M%S)
      sudo cp apps/competitions/views/auth.py backups/logout_fix_$(date +%Y%m%d_%H%M%S)/
      sudo cp apps/competitions/adapters.py backups/logout_fix_$(date +%Y%m%d_%H%M%S)/
      
      # Extraire l'archive
      sudo tar -xzf ~/logout_fix_deploy.tar.gz
      
      # Corriger les permissions
      sudo chown -R www-data:www-data apps/competitions/views/auth.py
      sudo chown -R www-data:www-data apps/competitions/adapters.py
      
      # Déboguer le problème
      sudo -u www-data python3 debug_logout_production.py
      
      # Redémarrer l'application
      sudo systemctl restart gunicorn
      sudo systemctl restart apache2
      
      # Vérifier les logs
      sudo tail -f /var/log/apache2/error.log
REMOTE_SCRIPT

echo ""
echo "3. Vérifications importantes:"
echo "   - Le template base.html utilise bien {% url 'account_logout' %}"
echo "   - L'adaptateur MartialCompAccountAdapter.get_logout_redirect_url() est configuré"
echo "   - La vue auth.logout_view redirige vers /{langue}/?no_redirect=1"
echo ""
echo "4. Test après déploiement:"
echo "   - Se connecter sur https://martialcomp.com"
echo "   - Cliquer sur le bouton de déconnexion"
echo "   - Vérifier qu'on arrive sur la page d'accueil et non sur Django admin"
echo ""
echo "=== Script terminé ==="