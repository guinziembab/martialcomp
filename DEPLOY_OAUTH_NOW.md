# Déploiement OAuth Google & Facebook - INSTRUCTIONS

## Identifiants configurés

| Provider | Client ID | Secret |
|----------|-----------|--------|
| **Google** | `246820300466-up5bbhd2199t9ekep3sa4jmhtto12tel.apps.googleusercontent.com` | `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` |
| **Facebook** | `1415333696343612` | `fd1e66ffcd47958997274808d0c2ec64` |

---

## Étape 1 : Connexion SSH au serveur

```bash
ssh pierrep99@martialcomp.com
```

---

## Étape 2 : Configurer OAuth via Django Shell

```bash
cd /var/www/vhosts/martialcomp.com/httpdocs
source ../venv/bin/activate

python manage.py shell
```

Puis copiez-collez ce code dans le shell Django :

```python
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

# Récupérer ou créer le site
site, _ = Site.objects.get_or_create(id=1, defaults={'domain': 'martialcomp.com', 'name': 'MartialComp'})
site.domain = 'martialcomp.com'
site.name = 'MartialComp'
site.save()
print(f"Site: {site.domain}")

# Configuration Google OAuth
google_app, created = SocialApp.objects.update_or_create(
    provider='google',
    defaults={
        'name': 'Google',
        'client_id': '246820300466-up5bbhd2199t9ekep3sa4jmhtto12tel.apps.googleusercontent.com',
        'secret': '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',
    }
)
google_app.sites.add(site)
print(f"Google OAuth: {'créé' if created else 'mis à jour'}")

# Configuration Facebook OAuth
fb_app, created = SocialApp.objects.update_or_create(
    provider='facebook',
    defaults={
        'name': 'Facebook',
        'client_id': '1415333696343612',
        'secret': 'fd1e66ffcd47958997274808d0c2ec64',
    }
)
fb_app.sites.add(site)
print(f"Facebook OAuth: {'créé' if created else 'mis à jour'}")

# Vérification
print("\n=== Applications OAuth configurées ===")
for app in SocialApp.objects.all():
    sites = ", ".join([s.domain for s in app.sites.all()])
    print(f"  {app.provider}: {app.name} -> {sites}")

exit()
```

---

## Étape 3 : Redémarrer l'application

```bash
# Toucher le fichier WSGI pour recharger
touch /var/www/vhosts/martialcomp.com/httpdocs/config/wsgi.py

# OU si Gunicorn est utilisé
sudo systemctl restart gunicorn 2>/dev/null || echo "Pas de systemd gunicorn"
```

---

## Étape 4 : Tester

1. Allez sur https://martialcomp.com/accounts/login/
2. Cliquez sur **"Continuer avec Google"**
3. Cliquez sur **"Continuer avec Facebook"**

---

## Vérification des URIs de callback

### Google Cloud Console
Vérifiez que cette URI est dans les "URIs de redirection autorisés" :
```
https://martialcomp.com/accounts/google/login/callback/
```

### Facebook Developers
Allez dans **Paramètres > Facebook Login > Paramètres** et ajoutez :
```
https://martialcomp.com/accounts/facebook/login/callback/
```

---

## En cas de problème

Si vous voyez "redirect_uri_mismatch" :
- Vérifiez que l'URI de callback est exactement comme indiqué ci-dessus
- Attendez quelques minutes après modification (Google peut prendre du temps)

Si vous voyez "App not setup" (Facebook) :
- Allez dans Facebook Developers > Paramètres > Basique
- Vérifiez que l'app est en mode "Live" (pas "Development")
- Ajoutez le domaine `martialcomp.com` dans "Domaines de l'application"
