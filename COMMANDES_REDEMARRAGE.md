# Commandes pour redémarrer le serveur de production

## Méthode 1 : Via SSH (recommandé)

```bash
# Se connecter au serveur
ssh pierrep99@martialcomp.com

# Redémarrer Gunicorn
sudo systemctl restart gunicorn

# Vérifier le statut
sudo systemctl status gunicorn
```

## Méthode 2 : Script automatique

```bash
./REDEMARRER_SERVEUR_PRODUCTION.sh
```

## Méthode 3 : Redémarrage via pkill (si systemctl ne fonctionne pas)

```bash
ssh pierrep99@martialcomp.com "sudo pkill -HUP gunicorn"
```

## Méthode 4 : Rechargement automatique (touch wsgi.py)

```bash
ssh pierrep99@martialcomp.com "touch /var/www/vhosts/martialcomp.com/httpdocs/config/wsgi.py"
```

## Méthode 5 : Redémarrage complet (si nécessaire)

```bash
ssh pierrep99@martialcomp.com
sudo systemctl stop gunicorn
sudo systemctl start gunicorn
sudo systemctl status gunicorn
```

## Vérifier que le serveur fonctionne

```bash
# Vérifier les processus Gunicorn
ssh pierrep99@martialcomp.com "ps aux | grep gunicorn"

# Vérifier les logs
ssh pierrep99@martialcomp.com "tail -f /var/log/django/martialcomp.log"

# Tester l'URL
curl -I https://martialcomp.com
```

## En cas de problème

### Trouver le nom exact du service

```bash
ssh pierrep99@martialcomp.com
sudo systemctl list-units | grep -i django
sudo systemctl list-units | grep -i gunicorn
sudo systemctl list-units | grep -i martial
sudo systemctl list-units | grep -i python
```

### Vérifier les logs d'erreur

```bash
# Logs systemd
ssh pierrep99@martialcomp.com "journalctl -u gunicorn -n 50"

# Logs Django
ssh pierrep99@martialcomp.com "tail -100 /var/log/django/martialcomp.log"

# Logs Nginx
ssh pierrep99@martialcomp.com "tail -100 /var/log/nginx/error.log"
```

### Redémarrer Nginx si nécessaire

```bash
ssh pierrep99@martialcomp.com "sudo systemctl restart nginx"
```

## Notes importantes

- ⚠️ Le redémarrage peut prendre quelques secondes
- ⚠️ Les utilisateurs connectés peuvent être déconnectés brièvement
- ⚠️ Vérifier toujours le statut après le redémarrage
- ⚠️ En cas d'erreur, consulter les logs immédiatement
