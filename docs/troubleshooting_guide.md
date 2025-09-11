# Guide de Dépannage MartialComp

Ce guide présente les problèmes courants rencontrés lors du déploiement et de l'exploitation de MartialComp, ainsi que leurs solutions.

## Table des matières

1. [Problèmes de démarrage](#problèmes-de-démarrage)
2. [Pages blanches](#pages-blanches)
3. [Erreurs d'internationalisation](#erreurs-dinternationalisation)
4. [Problèmes de modules manquants](#problèmes-de-modules-manquants)
5. [Erreurs de base de données](#erreurs-de-base-de-données)
6. [Problèmes de performance](#problèmes-de-performance)
7. [Erreurs d'authentification](#erreurs-dauthentification)
8. [Problèmes de fichiers statiques](#problèmes-de-fichiers-statiques)
9. [Erreurs de serveur (500)](#erreurs-de-serveur-500)
10. [Problèmes de connexion à l'administration](#problèmes-de-connexion-à-ladministration)

## Problèmes de démarrage

### Gunicorn ne démarre pas

**Symptômes :**
- Le service Gunicorn refuse de démarrer
- Erreur `exit code 1` dans les logs systemd

**Solutions :**

1. **Vérifier les erreurs dans les logs :**
   ```bash
   sudo journalctl -u gunicorn-martialcomp.service -n 50
   ```

2. **Vérifier les permissions des fichiers :**
   ```bash
   sudo chown -R www-data:www-data /var/www/vhosts/martialcomp.com/
   sudo chmod -R 755 /var/www/vhosts/martialcomp.com/
   sudo chmod 600 /var/www/vhosts/martialcomp.com/.env
   ```

3. **Tester le démarrage manuel :**
   ```bash
   cd /var/www/vhosts/martialcomp.com/httpdocs
   sudo -u www-data ../.venv/bin/gunicorn --check-config --config=gunicorn.conf.py config.wsgi:application
   ```

4. **Vérifier les variables d'environnement :**
   ```bash
   sudo cat /var/www/vhosts/martialcomp.com/.env
   ```
   Assurez-vous que le fichier .env existe et contient les variables requises.

5. **Vérifier l'installation des dépendances :**
   ```bash
   cd /var/www/vhosts/martialcomp.com
   sudo -u www-data .venv/bin/pip install -r httpdocs/requirements.txt
   ```

### Nginx ne sert pas l'application

**Symptômes :**
- Nginx fonctionne mais retourne une erreur 502 Bad Gateway

**Solutions :**

1. **Vérifier la configuration Nginx :**
   ```bash
   sudo nginx -t
   ```

2. **Vérifier que Gunicorn est en cours d'exécution :**
   ```bash
   sudo systemctl status gunicorn-martialcomp.service
   ```

3. **Vérifier la communication entre Nginx et Gunicorn :**
   ```bash
   sudo ss -tuln | grep 8002
   curl -v http://localhost:8002/
   ```

4. **Vérifier les logs Nginx :**
   ```bash
   sudo tail -n 50 /var/www/vhosts/martialcomp.com/logs/nginx-error.log
   ```

5. **Redémarrer les services :**
   ```bash
   sudo systemctl restart gunicorn-martialcomp
   sudo systemctl restart nginx
   ```

## Pages blanches

### Page d'accueil blanche

**Symptômes :**
- La page d'accueil s'affiche complètement blanche
- Pas d'erreur apparente dans les logs

**Solutions :**

1. **Activer temporairement le mode DEBUG :**
   Modifiez `config/settings/production.py` :
   ```python
   DEBUG = True
   ```
   Redémarrez Gunicorn :
   ```bash
   sudo systemctl restart gunicorn-martialcomp
   ```

2. **Vérifier les redirections :**
   ```bash
   curl -v http://localhost:8002/
   ```
   Observez s'il y a des redirections (codes 301, 302) et vers quelles URLs.

3. **Vérifier le template de la page d'accueil :**
   ```bash
   find /var/www/vhosts/martialcomp.com/httpdocs -name "welcome.html"
   ```
   Assurez-vous que le fichier existe et contient du HTML valide.

4. **Tester avec une URL spécifique à une langue :**
   ```bash
   curl -v http://localhost:8002/fr/
   curl -v http://localhost:8002/en/
   ```

5. **Examiner la vue welcome :**
   ```bash
   cat /var/www/vhosts/martialcomp.com/httpdocs/competitions/views/welcome.py
   ```
   Identifiez et corrigez les erreurs potentielles.

6. **Vérifier les middlewares, particulièrement l'internationalisation :**
   ```bash
   grep -A 15 "MIDDLEWARE" /var/www/vhosts/martialcomp.com/httpdocs/config/settings/production.py
   ```

### Pages blanches après connexion

**Symptômes :**
- La connexion fonctionne mais redirige vers une page blanche
- Session authentifiée mais contenu non affiché

**Solutions :**

1. **Vérifier les permissions d'accès :**
   ```python
   # Ajoutez temporairement dans la vue problématique
   def dashboard(request):
       print(f"User: {request.user}, Auth: {request.user.is_authenticated}")
       print(f"User profile: {hasattr(request.user, 'userprofile')}")
       print(f"User roles: {getattr(request.user.userprofile, 'role', None)}")
       # Suite du code...
   ```

2. **Vérifier la redirection post-connexion :**
   Modifiez `settings.py` pour voir la destination de redirection :
   ```python
   LOGIN_REDIRECT_URL = '/some-path/'
   ```

3. **Examiner les décorateurs de vue :**
   Vérifiez si les décorateurs `@login_required` ou personnalisés causent le problème.

4. **Tester avec un utilisateur différent :**
   Créez un nouveau superutilisateur et testez la connexion.

## Erreurs d'internationalisation

### Redirections en boucle

**Symptômes :**
- Redirections infinies entre '/' et '/en/' ou '/fr/'
- Erreur de redirection trop nombreuse dans le navigateur

**Solutions :**

1. **Vérifier la configuration i18n :**
   ```bash
   grep -r "LANGUAGE_CODE\|LANGUAGES\|LOCALE_PATHS\|i18n_patterns\|LocaleMiddleware" /var/www/vhosts/martialcomp.com/httpdocs/config/
   ```

2. **Vérifier l'ordre des middlewares :**
   Assurez-vous que `LocaleMiddleware` est positionné correctement :
   ```python
   MIDDLEWARE = [
       'django.middleware.security.SecurityMiddleware',
       'django.contrib.sessions.middleware.SessionMiddleware',
       'django.middleware.locale.LocaleMiddleware',  # Doit être ici
       'django.middleware.common.CommonMiddleware',
       # ...
   ]
   ```

3. **Vérifier les patterns d'URL :**
   ```bash
   cat /var/www/vhosts/martialcomp.com/httpdocs/config/urls.py
   ```
   Si vous utilisez `i18n_patterns`, assurez-vous qu'il est correctement configuré.

4. **Ajouter une URL de test non-i18n :**
   ```python
   # Dans urls.py, avant les patterns i18n
   urlpatterns = [
       path('test-no-i18n/', lambda request: HttpResponse("Test page"), name='test-no-i18n'),
       # ...
   ]
   ```

5. **Désactiver temporairement l'internationalisation :**
   ```python
   # Dans settings.py
   USE_I18N = False
   MIDDLEWARE = [m for m in MIDDLEWARE if 'LocaleMiddleware' not in m]
   ```

### Erreurs de traduction

**Symptômes :**
- Textes non traduits
- Messages d'erreur au lieu de traductions

**Solutions :**

1. **Vérifier que les fichiers de traduction sont compilés :**
   ```bash
   cd /var/www/vhosts/martialcomp.com/httpdocs
   sudo -u www-data ../.venv/bin/python manage.py compilemessages
   ```

2. **Vérifier les locales système :**
   ```bash
   locale -a
   ```
   Assurez-vous que les locales nécessaires sont installées.

3. **Installer les locales manquantes :**
   ```bash
   sudo apt install -y language-pack-fr language-pack-en
   sudo dpkg-reconfigure locales
   ```

4. **Vérifier les fichiers de traduction :**
   ```bash
   find /var/www/vhosts/martialcomp.com/httpdocs/locale -name "*.mo"
   ```

5. **Reconstruire les fichiers de traduction :**
   ```bash
   cd /var/www/vhosts/martialcomp.com/httpdocs
   sudo -u www-data ../.venv/bin/python manage.py makemessages -a
   sudo -u www-data ../.venv/bin/python manage.py compilemessages
   ```

## Problèmes de modules manquants

### ImportError pour des modules optionnels

**Symptômes :**
- Erreurs `ImportError` dans les logs
- Pages qui ne s'affichent pas à cause de modules manquants

**Solutions :**

1. **Utiliser des imports conditionnels :**
   ```python
   # Au lieu de:
   from grades.models import Grade
   
   # Utilisez:
   try:
      from grades.models import Grade
      HAS_GRADES = True
   except ImportError:
      HAS_GRADES = False
      Grade = None
   ```

2. **Vérifier l'installation des modules optionnels :**
   ```bash
   cd /var/www/vhosts/martialcomp.com/httpdocs
   ls -la  # Vérifier si les modules sont présents
   ```

3. **Ajouter des contournements dans les modèles :**
   ```python
   # Dans les modèles avec ForeignKey vers des modules optionnels
   if 'grades' in settings.INSTALLED_APPS:
       grade = models.ForeignKey('grades.Grade', on_delete=models.SET_NULL, null=True)
   else:
       grade_name = models.CharField(max_length=100, blank=True)
   ```

4. **Modifier les templates pour gérer l'absence de modules :**
   ```django
   {% if 'grades' in INSTALLED_APPS %}
       {# Affichage lié aux grades #}
   {% else %}
       <p>Module de grades non disponible.</p>
   {% endif %}
   ```

5. **Créer des classes fantômes pour les modules manquants :**
   ```python
   # Dans un fichier utils/stubs.py
   class GradeStub:
       """Classe stub pour remplacer Grade quand le module n'est pas disponible."""
       name = "Grade non disponible"
       # ...
   
   # Dans votre code
   try:
       from grades.models import Grade
   except ImportError:
       from utils.stubs import GradeStub as Grade
   ```

### NoReverseMatch pour des URLs de modules manquants

**Symptômes :**
- Erreurs `NoReverseMatch` dans les logs
- Pages qui ne s'affichent pas à cause d'URLs manquantes

**Solutions :**

1. **Utiliser des tags de template conditionnels :**
   ```django
   {% url 'grades:list' as grades_url %}
   {% if grades_url %}
       <a href="{{ grades_url }}">Grades</a>
   {% endif %}
   ```

2. **Créer des fonctions d'aide pour les URLs :**
   ```python
   # Dans utils/urls.py
   def safe_reverse(viewname, *args, **kwargs):
       """Tente de résoudre une URL et retourne # en cas d'échec."""
       try:
           return reverse(viewname, *args, **kwargs)
       except NoReverseMatch:
           return "#"
   
   # Dans les templates
   <a href="{% safe_reverse 'grades:list' %}">Grades</a>
   ```

3. **Vérifier que les URLs sont incluses conditionnellement :**
   ```python
   # Dans config/urls.py
   urlpatterns = [
       # ...
   ]
   
   if 'grades' in settings.INSTALLED_APPS:
       urlpatterns += [
           path('grades/', include('grades.urls', namespace='grades')),
       ]
   ```

4. **Utiliser des blocs try/except dans les vues :**
   ```python
   def dashboard(request):
       context = {}
       try:
           context['grades_url'] = reverse('grades:list')
       except NoReverseMatch:
           context['grades_url'] = None
       return render(request, 'dashboard.html', context)
   ```

## Erreurs de base de données

### Erreurs de migration

**Symptômes :**
- Erreurs lors de l'exécution des migrations
- Tables manquantes ou colonnes manquantes

**Solutions :**

1. **Vérifier l'état des migrations :**
   ```bash
   cd /var/www/vhosts/martialcomp.com/httpdocs
   sudo -u www-data ../.venv/bin/python manage.py showmigrations
   ```

2. **Corriger les migrations en conflit :**
   ```bash
   sudo -u www-data ../.venv/bin/python manage.py migrate --fake app_name zero
   sudo -u www-data ../.venv/bin/python manage.py migrate app_name
   ```

3. **Résoudre les erreurs de dépendance :**
   Si des migrations dépendent de modules manquants, modifiez-les :
   ```python
   # Dans la migration problématique
   operations = [
       migrations.RunPython(
           code=lambda apps, schema_editor: None  # Ne rien faire si le module est absent
       ),
   ]
   ```

4. **Vérifier les contraintes de base de données :**
   ```sql
   -- Via la console PostgreSQL
   \d table_name
   ```
   Vérifiez si les contraintes de clé étrangère posent problème.

5. **Créer une migration de correction :**
   ```bash
   sudo -u www-data ../.venv/bin/python manage.py makemigrations app_name --empty
   ```
   Puis éditez le fichier pour corriger les problèmes spécifiques.

### Erreurs de connexion à la base de données

**Symptômes :**
- Erreurs "could not connect to server"
- Erreurs d'authentification PostgreSQL

**Solutions :**

1. **Vérifier que PostgreSQL est en cours d'exécution :**
   ```bash
   sudo systemctl status postgresql
   ```

2. **Vérifier les paramètres de connexion :**
   ```bash
   sudo cat /var/www/vhosts/martialcomp.com/.env
   ```
   Assurez-vous que les informations de connexion sont correctes.

3. **Tester la connexion manuellement :**
   ```bash
   sudo -u www-data psql -h localhost -U martialcomp -d martialcomp
   ```

4. **Vérifier les permissions PostgreSQL :**
   ```bash
   sudo -u postgres psql -c "\du"
   sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE martialcomp TO martialcomp;"
   ```

5. **Vérifier le fichier pg_hba.conf :**
   ```bash
   sudo cat /etc/postgresql/*/main/pg_hba.conf
   ```
   Assurez-vous que les connexions locales sont autorisées.

## Problèmes de performance

### Temps de réponse lents

**Symptômes :**
- Pages qui mettent longtemps à charger
- Timeouts occasionnels

**Solutions :**

1. **Vérifier l'utilisation des ressources serveur :**
   ```bash
   top
   free -m
   df -h
   ```

2. **Activer le cache de base de données :**
   ```python
   # Dans settings.py
   CACHES = {
       'default': {
           'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
           'LOCATION': '127.0.0.1:11211',
       }
   }
   ```

3. **Optimiser les requêtes de base de données :**
   Utilisez `select_related()` et `prefetch_related()` pour réduire le nombre de requêtes.

4. **Augmenter le nombre de workers Gunicorn :**
   ```python
   # Dans gunicorn.conf.py
   workers = 8  # Ajustez en fonction des ressources serveur
   ```

5. **Utiliser le profilage pour identifier les goulots d'étranglement :**
   ```python
   # Installer django-debug-toolbar en développement
   # Ou utiliser django-silk en production (temporairement)
   ```

### Utilisation excessive de mémoire

**Symptômes :**
- Erreurs "Killed" dans les logs
- Redémarrages fréquents de Gunicorn

**Solutions :**

1. **Limiter la mémoire par worker :**
   ```python
   # Dans gunicorn.conf.py
   max_requests = 1000
   max_requests_jitter = 200
   ```

2. **Surveiller l'utilisation de la mémoire :**
   ```bash
   ps aux | grep gunicorn
   ```

3. **Rechercher les fuites de mémoire :**
   Utilisez des outils comme `memory_profiler` pour identifier les problèmes.

4. **Optimiser les requêtes volumineuses :**
   Utilisez la pagination pour les grandes collections de données.

5. **Ajuster les paramètres de cache :**
   Limitez la taille du cache si nécessaire.

## Erreurs d'authentification

### Problèmes de connexion utilisateur

**Symptômes :**
- Impossibilité de se connecter
- Redirections en boucle après connexion

**Solutions :**

1. **Vérifier les paramètres d'authentification :**
   ```python
   # Dans settings.py
   AUTHENTICATION_BACKENDS = [
       'django.contrib.auth.backends.ModelBackend',
       # Autres backends...
   ]
   ```

2. **Réinitialiser le mot de passe d'un utilisateur :**
   ```bash
   cd /var/www/vhosts/martialcomp.com/httpdocs
   sudo -u www-data ../.venv/bin/python manage.py changepassword admin
   ```

3. **Vérifier les cookies et sessions :**
   ```python
   # Dans settings.py
   SESSION_COOKIE_SECURE = True  # Uniquement pour HTTPS
   SESSION_COOKIE_AGE = 86400  # 24 heures en secondes
   ```

4. **Vérifier les middlewares de session :**
   Assurez-vous que `SessionMiddleware` et `AuthenticationMiddleware` sont activés.

5. **Tester avec un nouvel utilisateur :**
   ```bash
   cd /var/www/vhosts/martialcomp.com/httpdocs
   sudo -u www-data ../.venv/bin/python manage.py createsuperuser
   ```

### Problèmes avec l'authentification sociale

**Symptômes :**
- Erreurs lors de la connexion via Google, Facebook, etc.
- Redirections incorrectes après authentification sociale

**Solutions :**

1. **Vérifier la configuration django-allauth :**
   ```python
   # Dans settings.py
   INSTALLED_APPS = [
       # ...
       'allauth',
       'allauth.account',
       'allauth.socialaccount',
       'allauth.socialaccount.providers.google',
       # ...
   ]
   
   AUTHENTICATION_BACKENDS = [
       # ...
       'allauth.account.auth_backends.AuthenticationBackend',
   ]
   ```

2. **Vérifier les clés API :**
   ```bash
   # Via la console Django
   from allauth.socialaccount.models import SocialApp
   SocialApp.objects.all()
   ```
   Assurez-vous que les clés API sont correctement configurées.

3. **Vérifier les paramètres des fournisseurs sociaux :**
   ```python
   # Dans settings.py
   SOCIALACCOUNT_PROVIDERS = {
       'google': {
           'SCOPE': ['profile', 'email'],
           'AUTH_PARAMS': {'access_type': 'online'}
       }
   }
   ```

4. **Vérifier les redirections :**
   ```python
   # Dans settings.py
   LOGIN_REDIRECT_URL = '/dashboard/'
   ```

5. **Examiner les logs pour les erreurs OAuth :**
   ```bash
   tail -n 100 /var/www/vhosts/martialcomp.com/logs/gunicorn-error.log | grep -i oauth
   ```

## Problèmes de fichiers statiques

### Fichiers statiques non chargés

**Symptômes :**
- Images, CSS ou JavaScript manquants
- Pages mal formatées

**Solutions :**

1. **Vérifier la configuration des fichiers statiques :**
   ```python
   # Dans settings.py
   STATIC_URL = '/static/'
   STATIC_ROOT = '/var/www/vhosts/martialcomp.com/static'
   STATICFILES_DIRS = [
       os.path.join(BASE_DIR, 'static'),
   ]
   ```

2. **Exécuter collectstatic :**
   ```bash
   cd /var/www/vhosts/martialcomp.com/httpdocs
   sudo -u www-data ../.venv/bin/python manage.py collectstatic --noinput
   ```

3. **Vérifier les permissions des fichiers statiques :**
   ```bash
   sudo chown -R www-data:www-data /var/www/vhosts/martialcomp.com/static
   sudo chmod -R 755 /var/www/vhosts/martialcomp.com/static
   ```

4. **Vérifier la configuration Nginx :**
   ```nginx
   location /static/ {
       alias /var/www/vhosts/martialcomp.com/static/;
       expires 30d;
   }
   ```

5. **Tester l'accès direct aux fichiers statiques :**
   ```bash
   curl -I http://martialcomp.com/static/css/main.css
   ```

### Problèmes avec les fichiers média

**Symptômes :**
- Images uploadées non affichées
- Erreurs lors de l'upload de fichiers

**Solutions :**

1. **Vérifier la configuration des fichiers média :**
   ```python
   # Dans settings.py
   MEDIA_URL = '/media/'
   MEDIA_ROOT = '/var/www/vhosts/martialcomp.com/media'
   ```

2. **Vérifier les permissions des fichiers média :**
   ```bash
   sudo chown -R www-data:www-data /var/www/vhosts/martialcomp.com/media
   sudo chmod -R 755 /var/www/vhosts/martialcomp.com/media
   ```

3. **Vérifier la configuration Nginx :**
   ```nginx
   location /media/ {
       alias /var/www/vhosts/martialcomp.com/media/;
   }
   ```

4. **Tester l'upload de fichiers :**
   ```bash
   # Via l'interface admin, essayez d'uploader un fichier
   ```

5. **Vérifier les limitations de taille de fichier :**
   ```nginx
   # Dans Nginx
   client_max_body_size 10M;
   ```

## Erreurs de serveur (500)

### Erreurs 500 générales

**Symptômes :**
- Pages qui renvoient une erreur 500
- Messages "Internal Server Error" dans les logs

**Solutions :**

1. **Activer le mode DEBUG temporairement :**
   ```python
   # Dans settings.py
   DEBUG = True
   ```

2. **Examiner les logs détaillés :**
   ```bash
   tail -n 100 /var/www/vhosts/martialcomp.com/logs/gunicorn-error.log
   ```

3. **Identifier les requêtes problématiques :**
   ```bash
   tail -n 100 /var/www/vhosts/martialcomp.com/logs/nginx-access.log | grep " 500 "
   ```

4. **Vérifier les erreurs dans les middleware :**
   Désactivez temporairement les middleware personnalisés pour isoler le problème.

5. **Tester avec une vue simplifiée :**
   ```python
   # Dans urls.py
   path('test-500/', lambda request: HttpResponse("Test OK"), name='test-500'),
   ```

### Erreurs 500 spécifiques à certaines pages

**Symptômes :**
- Erreurs 500 sur des pages spécifiques
- Fonctionnalités particulières qui échouent

**Solutions :**

1. **Isoler la vue problématique :**
   ```python
   # Dans la vue problématique
   def problematic_view(request):
       try:
           # Code original
           pass
       except Exception as e:
           logger.error(f"Erreur dans problematic_view: {e}")
           return HttpResponse(f"Erreur: {e}", status=500)
   ```

2. **Vérifier les requêtes de base de données :**
   Utilisez `django-debug-toolbar` pour identifier les requêtes problématiques.

3. **Tester avec des données simplifiées :**
   Créez une version simplifiée de la vue qui n'utilise pas de données complexes.

4. **Vérifier les modules tiers :**
   Désactivez temporairement les modules tiers pour identifier les conflits.

5. **Examiner les templates :**
   Vérifiez si les erreurs sont liées à des tags de template ou des filtres.

## Problèmes de connexion à l'administration

### Impossible d'accéder à l'interface d'administration

**Symptômes :**
- Page d'administration inaccessible
- Erreurs lors de la connexion à l'admin

**Solutions :**

1. **Vérifier l'URL d'administration :**
   ```python
   # Dans urls.py
   path('admin/', admin.site.urls),
   ```

2. **Vérifier que l'application admin est activée :**
   ```python
   # Dans settings.py
   INSTALLED_APPS = [
       'django.contrib.admin',
       # ...
   ]
   ```

3. **Vérifier les droits du superutilisateur :**
   ```bash
   # Via la console Django
   from django.contrib.auth.models import User
   user = User.objects.get(username='admin')
   user.is_staff = True
   user.is_superuser = True
   user.save()
   ```

4. **Réinitialiser le mot de passe admin :**
   ```bash
   cd /var/www/vhosts/martialcomp.com/httpdocs
   sudo -u www-data ../.venv/bin/python manage.py changepassword admin
   ```

5. **Vérifier les personnalisations d'administration :**
   ```python
   # Dans admin.py
   # Désactivez temporairement les personnalisations complexes
   ```

### Erreurs dans l'interface d'administration

**Symptômes :**
- Erreurs lors de l'édition d'objets dans l'admin
- Fonctionnalités d'administration qui échouent

**Solutions :**

1. **Vérifier les personnalisations ModelAdmin :**
   ```python
   # Dans admin.py
   # Simplifiez temporairement les classes ModelAdmin
   @admin.register(MyModel)
   class MyModelAdmin(admin.ModelAdmin):
       list_display = ['id', 'name']  # Limitez à des champs simples
   ```

2. **Vérifier les méthodes personnalisées :**
   Désactivez temporairement les méthodes personnalisées dans les classes ModelAdmin.

3. **Vérifier les inlines :**
   Désactivez temporairement les inlines qui pourraient causer des problèmes.

4. **Examiner les logs pendant l'utilisation de l'admin :**
   ```bash
   tail -f /var/www/vhosts/martialcomp.com/logs/gunicorn-error.log
   ```
   Utilisez l'interface d'administration et observez les erreurs.

5. **Tester avec une version simplifiée :**
   Créez une classe ModelAdmin minimale pour tester.

## Conclusion

Ce guide de dépannage couvre les problèmes les plus courants rencontrés lors de l'exploitation de MartialComp. Si vous rencontrez un problème qui n'est pas répertorié ici, n'hésitez pas à consulter les logs détaillés et à suivre une approche systématique de débogage en isolant progressivement la source du problème.

Pour une assistance supplémentaire, contactez l'équipe de support de MartialComp ou consultez la documentation officielle de Django.
