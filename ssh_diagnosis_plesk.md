# Diagnostic et Résolution SSH via Plesk

## 1. Diagnostic du problème

Le message "Connection refused" indique que :
- Le service SSH (sshd) est arrêté
- Le firewall bloque le port 22
- Le serveur a peut-être atteint la limite de connexions SSH échouées

## 2. Actions via Plesk

### A. Vérifier le service SSH
1. Connectez-vous à Plesk (https://martialcomp.com:8443)
2. Allez dans **Tools & Settings** → **Services Management**
3. Cherchez "SSH Server" ou "sshd"
4. Vérifiez son statut et redémarrez-le si nécessaire

### B. Vérifier le Firewall
1. Dans Plesk : **Tools & Settings** → **Firewall**
2. Vérifiez que le port 22 (SSH) est ouvert
3. Si non, ajoutez une règle pour autoriser SSH

### C. Alternative : Terminal Web Plesk
1. Dans Plesk : **Tools & Settings** → **SSH Terminal** (ou Web Terminal)
2. Cela vous donnera accès au serveur sans SSH

### D. Depuis le Terminal Web, exécutez :
```bash
# Vérifier le statut SSH
systemctl status sshd

# Redémarrer SSH
systemctl restart sshd

# Vérifier les logs
tail -n 50 /var/log/auth.log
tail -n 50 /var/log/secure

# Vérifier le firewall
iptables -L -n | grep 22
```

## 3. Solution alternative pour le déploiement

### Via le gestionnaire de fichiers Plesk :
1. **File Manager** dans Plesk
2. Naviguez vers `/var/www/martialcomp`
3. Uploadez directement les fichiers :
   - `api/urls.py`
   - `api_auth/views.py`
   - `api_auth/models.py`
   - `api_auth/serializers.py`
   - `api_auth/urls.py`
4. Uploadez et extrayez `apps.tar.gz`

### Puis dans le Terminal Web :
```bash
cd /var/www/martialcomp
python manage.py collectstatic --noinput
python manage.py migrate
systemctl restart gunicorn
systemctl restart nginx
```

## 4. Débloquer SSH (si bloqué par fail2ban)

Si vous avez fail2ban installé :
```bash
# Vérifier les IPs bannies
fail2ban-client status sshd

# Débloquer votre IP
fail2ban-client unban YOUR_IP_ADDRESS

# Ou désactiver temporairement fail2ban
systemctl stop fail2ban
```

## 5. Port SSH alternatif

Il est possible que SSH soit configuré sur un port différent. Vérifiez :
```bash
grep Port /etc/ssh/sshd_config
```

## 6. Vérification rapide

Essayez aussi :
```bash
# Tester différents ports courants
ssh -p 2222 root@martialcomp.com
ssh -p 2022 root@martialcomp.com
ssh -p 22022 root@martialcomp.com
```