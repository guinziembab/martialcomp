# Plan de test en développement local

## Objectif
Tester en local pour comprendre pourquoi l'erreur JavaScript persiste en production malgré les corrections.

## Situation actuelle

### ✅ Confirmé en LOCAL
- Les 3 corrections JavaScript sont présentes dans `base.html` (lignes 231, 340, 358)
- Le code `practitioner_form.html` est correct (ligne 1209)
- L'API `generate_license_number_api` est implémentée

### ❌ Problème PRODUCTION
- L'erreur JavaScript persiste: `Uncaught SyntaxError: missing ) after argument list (at edit/:2570:5)`
- Le bouton "Générer" ne fonctionne pas
- Vérifications serveur montrent que les corrections sont présentes, mais le navigateur voit toujours l'ancien code

## Hypothèses à tester

### Hypothèse 1: Cache du template Django en production
**Cause possible:** Django compile et met en cache les templates. Passenger ne recharge pas correctement le cache malgré `touch tmp/restart.txt`.

**Test local:**
```bash
# 1. Lancer le serveur de développement
python manage.py runserver 8080 --settings=config.settings.development

# 2. Accéder à la page de test
http://localhost:8080/en/competitions/club/practitioners/88/edit/

# 3. Vérifier dans la console (F12) si l'erreur JavaScript apparaît
```

**Résultat attendu:**
- Si l'erreur n'apparaît PAS en local → Le problème est spécifique à la production (cache, CDN, ou configuration serveur)
- Si l'erreur APPARAÎT en local → Le problème est dans notre code (il reste des Django URL tags quelque part)

### Hypothèse 2: Il existe un AUTRE fichier base.html en production
**Cause possible:** Il pourrait y avoir plusieurs fichiers `base.html` dans différents répertoires, et Django charge le mauvais.

**Test en production:**
```bash
ssh pierrep99@martialcomp.com "find /var/www/vhosts/martialcomp.com -name 'base.html' -type f 2>/dev/null"
```

**Résultat attendu:**
- Devrait trouver UN SEUL fichier: `/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/base.html`
- Si plusieurs fichiers → Django pourrait charger le mauvais

### Hypothèse 3: Collectstatic n'a pas été exécuté
**Cause possible:** Si les templates sont copiés vers un répertoire STATIC, ils ne seront pas mis à jour.

**Test en production:**
```bash
ssh pierrep99@martialcomp.com "cd /var/www/vhosts/martialcomp.com/httpdocs && python3 manage.py collectstatic --noinput"
```

**Résultat attendu:**
- Les templates HTML ne devraient PAS être collectés (seulement CSS/JS/images)
- Si des templates sont copiés → C'est peut-être la source du problème

### Hypothèse 4: Un CDN ou proxy cache sert l'ancienne version
**Cause possible:** Plesk pourrait avoir un cache Nginx/Apache ou un CDN qui sert l'ancienne version du HTML.

**Test:**
```bash
# Vérifier la configuration Nginx/Apache pour le caching
ssh pierrep99@martialcomp.com "grep -r 'proxy_cache\|cache_control' /etc/nginx/ /etc/apache2/ 2>/dev/null"
```

**Solution si confirmé:**
- Vider le cache Nginx: `nginx -s reload`
- Vider le cache Apache: `systemctl restart apache2`
- Ou utiliser l'interface Plesk: Domains → Reload web configuration

### Hypothèse 5: L'erreur vient d'un AUTRE fichier template
**Cause possible:** La ligne 2570 pourrait être dans un AUTRE template qui est également inclus, comme un modal ou un include.

**Test local:**
```bash
# Chercher tous les Django URL tags dans du JavaScript
grep -r "{% url" apps/competitions/templates/ | grep -v ".pyc" | grep -E "(fetch|const|let|var)" | head -20
```

## Actions à prendre MAINTENANT

### 1. Test immédiat en développement local

```bash
cd c:\martial_hub_django\martialcomp

# Lancer le serveur (si ce n'est pas déjà fait)
python manage.py runserver 8080 --settings=config.settings.development

# Créer un compte test si nécessaire
python manage.py createsuperuser --settings=config.settings.development

# Accéder à l'URL problématique
# http://localhost:8080/en/competitions/club/practitioners/88/edit/
```

### 2. Analyse du HTML rendu en production

```bash
# Télécharger le HTML rendu depuis la production
curl -u "username:password" "https://martialcomp.com/en/competitions/club/practitioners/88/edit/" > production_rendered.html

# Chercher la ligne 2570 exacte
sed -n '2560,2580p' production_rendered.html

# Chercher les Django URL tags qui n'auraient pas été rendus
grep "{% url" production_rendered.html
```

### 3. Forcer un redémarrage COMPLET du serveur web

```bash
bash FORCE_CLEAR_ALL_CACHES_PRODUCTION.sh

# Puis redémarrer Apache/Nginx
ssh pierrep99@martialcomp.com "sudo systemctl restart apache2 || sudo systemctl restart nginx"
```

## Résumé

**Ce que nous savons:**
- ✅ Le code local est correct
- ✅ Le serveur montre que le code est correct
- ❌ Le navigateur voit toujours l'ancien code

**Ce que nous devons découvrir:**
- Où Django charge-t-il réellement ses templates en production?
- Y a-t-il un cache de templates quelque part?
- Y a-t-il un CDN ou proxy qui sert l'ancienne version?

**Prochaine étape:**
Tester EN LOCAL pour confirmer que le code fonctionne sans erreur JavaScript.
