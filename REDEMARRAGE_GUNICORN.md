# Redémarrage de Gunicorn - Production

## Date : 12 novembre 2024 - 21:27 UTC

## Problème initial
- Erreur 502 Bad Gateway
- Service systemd en échec (start-limit-hit)
- Aucun processus Gunicorn en cours d'exécution
- Port 8888 non en écoute

## Actions effectuées

1. ✅ Réinitialisation du compteur systemd
   ```bash
   systemctl reset-failed martialcomp-gunicorn.service
   ```

2. ✅ Arrêt des anciens processus Gunicorn
   ```bash
   pkill -f 'gunicorn.*config.wsgi'
   ```

3. ✅ Démarrage de Gunicorn en mode daemon
   - Utilisation de la commande exacte du script `start_gunicorn.sh`
   - Mode daemon activé
   - Variables d'environnement définies
   - 3 workers, port 127.0.0.1:8888

## Commande de démarrage

```bash
cd /var/www/vhosts/martialcomp.com/httpdocs
export DJANGO_ENV=production
export DJANGO_SETTINGS_MODULE=config.settings
export DB_NAME=martialcomp_db
export DB_USER=martialcomp_user
export DB_PASSWORD='AQWZSX123ok,'
export DB_HOST=localhost
export DB_PORT=5432

/var/www/vhosts/martialcomp.com/venv/bin/gunicorn \
  --workers 3 \
  --bind 127.0.0.1:8888 \
  --access-logfile logs/gunicorn_access.log \
  --error-logfile logs/gunicorn_error.log \
  --log-level info \
  config.wsgi:application \
  --daemon
```

## Vérifications

- ✅ Processus Gunicorn en cours d'exécution
- ✅ Port 8888 en écoute
- ✅ Réponse HTTP depuis localhost

## Statut

✅ **Gunicorn redémarré avec succès**

L'erreur 502 Bad Gateway devrait être résolue. Le serveur web (Nginx/Apache) peut maintenant communiquer avec Gunicorn sur le port 8888.
