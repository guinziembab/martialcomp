# Configuration Email IONOS - MartialComp

## Problème Identifié

Les emails ne sont pas envoyés car les credentials SMTP IONOS sont invalides.

**Erreur actuelle:**
```
SASL authentication failed; server smtp.ionos.fr said: 535 Authentication credentials invalid
```

## Actions Requises

### 1. Mettre à jour le mot de passe IONOS

Le mot de passe actuel `MartialComp2024!` pour le compte `noreply@martialcomp.com` est rejeté par IONOS.

**Actions à effectuer:**

1. Connectez-vous à votre espace IONOS : https://my.ionos.fr/
2. Allez dans **Email & Office** > **Gérer les boîtes email**
3. Sélectionnez `noreply@martialcomp.com`
4. Changez le mot de passe ou notez le mot de passe actuel correct

### 2. Mettre à jour les fichiers de configuration

#### A. Fichier .env sur le serveur

```bash
ssh martialcomp-production
nano /var/www/vhosts/martialcomp.com/httpdocs/.env
```

Modifiez la ligne:
```
EMAIL_HOST_PASSWORD=NOUVEAU_MOT_DE_PASSE
```

#### B. Configuration Postfix SASL

Le serveur Postfix utilise aussi ces credentials pour relayer les emails.

```bash
# Éditer le fichier de credentials SASL
sudo nano /etc/postfix/sasl_passwd

# Mettre à jour les lignes avec le nouveau mot de passe:
[smtp.ionos.fr]:587 noreply@martialcomp.com:NOUVEAU_MOT_DE_PASSE
[smtp.ionos.com]:587 noreply@martialcomp.com:NOUVEAU_MOT_DE_PASSE
smtp.ionos.fr noreply@martialcomp.com:NOUVEAU_MOT_DE_PASSE

# Régénérer la base de données hashée
sudo postmap /etc/postfix/sasl_passwd

# Redémarrer Postfix
sudo systemctl restart postfix
```

### 3. Tester l'envoi d'email

```bash
cd /var/www/vhosts/martialcomp.com
source venv/bin/activate
cd httpdocs

# Charger les variables d'environnement
export $(grep -v '^#' .env | xargs)
export DJANGO_SETTINGS_MODULE=config.settings.production

# Tester l'envoi
python -c "
from django.core.mail import send_mail
from django.conf import settings
result = send_mail(
    'Test Email MartialComp',
    'Ceci est un test pour vérifier que les emails fonctionnent.',
    settings.DEFAULT_FROM_EMAIL,
    ['votre-email@test.com'],
    fail_silently=False,
)
print(f'Résultat: {result}')
"
```

### 4. Vérifier les logs

```bash
# Logs Postfix
sudo tail -f /var/log/mail.log

# Logs Django
tail -f /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_error.log
```

## Configuration Actuelle

### Fichiers concernés:

1. **`/var/www/vhosts/martialcomp.com/httpdocs/.env`**
   - Variables EMAIL_* pour Django

2. **`/etc/postfix/sasl_passwd`**
   - Credentials SASL pour Postfix

3. **`/etc/postfix/main.cf`**
   - Configuration générale Postfix (relayhost = smtp.ionos.fr:587)

### Paramètres email dans .env:

```
EMAIL_HOST=smtp.ionos.fr
EMAIL_PORT=587
EMAIL_HOST_USER=noreply@martialcomp.com
EMAIL_HOST_PASSWORD=<MOT_DE_PASSE_À_CORRIGER>
DEFAULT_FROM_EMAIL=MartialComp <noreply@martialcomp.com>
SERVER_EMAIL=noreply@martialcomp.com
ADMIN_EMAIL=bertrand.guinziemba@gmail.com
```

## Système de Notifications

Le système de notification a été mis à jour pour envoyer automatiquement des emails dans les cas suivants:

1. **Attribution de rôle** - L'utilisateur reçoit un email quand:
   - Sa demande de rôle est soumise (en attente)
   - Sa demande est approuvée
   - Sa demande est refusée

2. **Notifications admin** - Les administrateurs reçoivent un email quand:
   - Une nouvelle demande de rôle nécessite validation

3. **Assignation de juge** - Le juge reçoit un email quand:
   - Il est assigné à une compétition

### Templates email créés:

- `role_assignment_pending.html` - Demande en attente
- `role_assignment_approved.html` - Rôle approuvé
- `role_assignment_rejected.html` - Demande refusée
- `admin_pending_approval.html` - Notification admin

## Support

En cas de problème, vérifiez:
1. Le mot de passe IONOS est correct
2. Le compte n'est pas bloqué/suspendu
3. Les ports 587 (SMTP TLS) sont ouverts
4. Les logs Postfix et Django pour plus de détails
