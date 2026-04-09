# Rapport de Test en Développement - 24 novembre 2024

## Statut: Serveur de développement ACTIF

Le serveur Django de développement est maintenant en cours d'exécution sur **http://localhost:8080**

```
✅ Serveur démarré sur le port 8080
✅ Environment: development
✅ StatReloader actif (rechargement automatique)
```

## Tests à effectuer IMMÉDIATEMENT

### Test 1: Vérifier l'absence d'erreur JavaScript en local

1. **Ouvrir votre navigateur web**
2. **Accéder à**: http://localhost:8080/en/competitions/club/practitioners/88/edit/

   ⚠️ **Note**: Si le praticien ID 88 n'existe pas en développement, vous pouvez:
   - Créer un nouveau praticien via le dashboard
   - OU accéder à la liste: http://localhost:8080/en/competitions/dashboard/club/
   - OU utiliser un autre ID de praticien existant

3. **Ouvrir la console JavaScript** (F12)
4. **Vérifier**: Y a-t-il l'erreur `Uncaught SyntaxError: missing ) after argument list`?

### Résultats possibles

#### Scénario A: ✅ PAS d'erreur JavaScript en local
**Signification:** Le code est correct en local, le problème est spécifique à la production

**Causes probables:**
1. **Cache de templates Django en production** qui n'est pas vidé malgré Passenger restart
2. **Fichier base.html en double** quelque part en production
3. **CDN ou proxy cache** (Nginx/Apache) qui sert l'ancienne version
4. **Collectstatic** qui copie une ancienne version du template

**Action à prendre:**
→ Exécuter le script de diagnostic: `bash DIAGNOSTIC_COMPARE_BASE_HTML.sh`
→ Forcer le vidage complet des caches: `bash FORCE_CLEAR_ALL_CACHES_PRODUCTION.sh`
→ Redémarrer Apache/Nginx en production

#### Scénario B: ❌ L'erreur JavaScript APPARAÎT en local
**Signification:** Il reste un problème dans notre code source

**Causes probables:**
1. Il existe un **AUTRE Django URL tag** problématique quelque part
2. L'erreur vient d'un **autre fichier template** (modal, include, etc.)
3. Les corrections dans base.html sont **incomplètes**

**Action à prendre:**
→ Analyser la ligne exacte de l'erreur dans le code source (View Source)
→ Chercher TOUS les Django URL tags dans du JavaScript
→ Corriger les erreurs trouvées

### Test 2: Vérifier le bouton "Générer" fonctionne en local

1. Sur la page du praticien, **remplir les champs**:
   - Date de naissance
   - Nom de famille
   - Au moins une discipline

2. **Cliquer sur le bouton "Générer"**

3. **Vérifier**:
   - Un numéro de licence apparaît-il?
   - Format attendu: `DISC-YYYY-CLUB-XXXX` (ex: `QKD-1990-0001-MA5K7T`)

4. **Si le bouton ne fonctionne pas**:
   - Ouvrir la console (F12) → Onglet Network
   - Cliquer sur "Générer"
   - Vérifier que la requête POST est envoyée à `/en/competitions/api/generate-license-number/`
   - Vérifier la réponse du serveur (200 OK avec JSON ou erreur?)

### Test 3: Vérifier le mode jour/nuit fonctionne en local

1. **Accéder au dashboard club**: http://localhost:8080/en/competitions/dashboard/club/

2. **Chercher le bouton toggle** ☀️/🌙 (en haut à droite)

3. **Cliquer dessus** et vérifier:
   - Le thème bascule entre clair et sombre
   - Après rechargement (F5), le thème persiste

---

## Comparaison Local vs Production

### Fichiers vérifiés en LOCAL ✅

1. **base.html** (lignes 231, 340, 358)
   ```javascript
   const currentLang = document.documentElement.lang || 'en';
   ```
   ✅ 3 corrections présentes

2. **practitioner_form.html** (ligne 1209)
   ```javascript
   const apiUrl = '/en/competitions/api/generate-license-number/'.replace('/en/', '/' + document.documentElement.lang + '/');
   ```
   ✅ Correction présente

3. **registration_api.py**
   ✅ Fonction `generate_license_number_api` implémentée

4. **urls/__init__.py** et **urls/club.py**
   ✅ Route API enregistrée

5. **dashboard/club.html**
   ✅ Mode jour/nuit implémenté

### Fichiers vérifiés en PRODUCTION ✅ (selon grep)

Le grep sur le serveur de production a confirmé que:
- Les 3 lignes avec `const currentLang` sont présentes (231, 340, 358)
- La date de modification du fichier base.html correspond au transfert SCP

**MAIS le navigateur voit toujours l'ancienne version!**

---

## Hypothèses principales

### 🎯 Hypothèse #1: Cache de templates Django (TRÈS PROBABLE)
Django compile les templates en bytecode Python et les met en cache. Le simple `touch tmp/restart.txt` de Passenger ne suffit peut-être pas à vider ce cache.

**Solution:**
```bash
bash FORCE_CLEAR_ALL_CACHES_PRODUCTION.sh
```

### 🎯 Hypothèse #2: Collectstatic copie les templates (POSSIBLE)
Si `python manage.py collectstatic` copie les templates HTML vers un répertoire STATIC, et que Nginx/Apache sert ces fichiers statiques, alors nos modifications ne seront jamais prises en compte.

**Vérification:**
```bash
grep -r "STATICFILES_DIRS\|TEMPLATES" config/settings/production.py
```

### 🎯 Hypothèse #3: Il existe plusieurs base.html (POSSIBLE)
Django cherche les templates dans l'ordre défini par `TEMPLATES['DIRS']` dans settings.py. S'il y a plusieurs `base.html`, Django pourrait charger le mauvais.

**Vérification:**
```bash
ssh pierrep99@martialcomp.com "find /var/www/vhosts/martialcomp.com -name 'base.html' -type f 2>/dev/null"
```

### 🎯 Hypothèse #4: Cache Nginx/Apache ou CDN (POSSIBLE)
Plesk configure souvent un cache au niveau du serveur web (Nginx en reverse proxy devant Apache, ou mod_cache Apache).

**Solution:**
```bash
ssh pierrep99@martialcomp.com "sudo systemctl restart apache2 && sudo systemctl restart nginx"
```

---

## Actions prioritaires MAINTENANT

### ✅ Étape 1: Tester en local (EN COURS)
Le serveur de développement est actif sur http://localhost:8080

**Vous devez maintenant:**
1. Ouvrir votre navigateur
2. Tester les 3 fonctionnalités (erreur JS, bouton Générer, mode jour/nuit)
3. Noter les résultats

### ⏳ Étape 2: Diagnostic production (SI LOCAL FONCTIONNE)
Si tout fonctionne en local mais pas en production, exécuter:

```bash
bash DIAGNOSTIC_COMPARE_BASE_HTML.sh
```

Ce script va:
- Comparer base.html local vs production ligne par ligne
- Vérifier qu'il n'y a qu'un seul base.html
- Chercher les anciens Django URL tags
- Vérifier l'état des caches

### ⏳ Étape 3: Forcer le vidage de TOUS les caches production
```bash
bash FORCE_CLEAR_ALL_CACHES_PRODUCTION.sh
```

Ce script va:
- Vider le cache Python (__pycache__)
- Vider le cache Django
- Supprimer les sessions
- Redémarrer Passenger 3 fois
- Optionnel: Vider le cache Plesk

### ⏳ Étape 4: Redémarrage complet du serveur web (DERNIER RECOURS)
```bash
ssh pierrep99@martialcomp.com "sudo systemctl restart apache2 && sudo systemctl restart nginx"
```

---

## Checklist de diagnostic

- [ ] Serveur de développement actif sur http://localhost:8080
- [ ] Page praticien accessible en local
- [ ] Pas d'erreur JavaScript en local (vérifier console F12)
- [ ] Bouton "Générer" fonctionne en local
- [ ] Mode jour/nuit fonctionne en local
- [ ] Diagnostic base.html local vs production exécuté
- [ ] Un seul fichier base.html trouvé en production
- [ ] Tous les caches vidés en production
- [ ] Passenger redémarré en production
- [ ] Apache/Nginx redémarré en production
- [ ] Cache navigateur vidé (Ctrl+Shift+Delete)
- [ ] Test en navigation privée effectué

---

## Logs à surveiller en production

Si l'erreur persiste après tous les tests:

```bash
# Logs Django
ssh pierrep99@martialcomp.com "tail -f /var/www/vhosts/martialcomp.com/httpdocs/logs/django.log"

# Logs Apache
ssh pierrep99@martialcomp.com "tail -f /var/log/apache2/error.log"

# Logs Nginx
ssh pierrep99@martialcomp.com "tail -f /var/log/nginx/error.log"

# Logs Passenger
ssh pierrep99@martialcomp.com "tail -f /var/log/passenger/passenger.log"
```

---

**Créé le:** 24 novembre 2024
**Serveur dev actif:** ✅ Port 8080
**Prochaine étape:** Tester en local dans le navigateur
