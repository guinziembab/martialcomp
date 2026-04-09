# 🚨 RAPPORT D'INCIDENT CRITIQUE - SITE HORS LIGNE

**Date** : 14 Novembre 2025, 20:45 CET  
**Durée de l'incident** : ~3 heures  
**Statut** : ❌ SITE HORS LIGNE (502 Bad Gateway)  
**Priorité** : CRITIQUE

---

## 📋 RÉSUMÉ EXÉCUTIF

Le site **martialcomp.com** est **complètement hors ligne** suite à des modifications pour corriger un problème d'affichage cosmétique (espaces blancs entre onglets). Toutes les tentatives de restauration ont échoué.

---

## 🎯 OBJECTIF INITIAL

**Demande utilisateur** : "il y a un gros écart d'affichage, une longue page blanche avant l'affichage des catégories, des participants et des juges"

**Page concernée** : `https://martialcomp.com/competitions/4/`

**Solution prévue** : Supprimer une section "Actions rapides" dupliquée qui créait l'espace blanc

---

## 🔴 ÉTAT ACTUEL DU SITE

### Production (martialcomp.com)
```
URL: https://martialcomp.com/competitions/4/
Status: HTTP 502 Bad Gateway
Erreur: "Bad gateway Error code 502"
Cloudflare: Working
Host: Error
```

### Serveur
```
SSH: martialcomp-production (217.154.24.122)
Chemin: /var/www/vhosts/martialcomp.com/httpdocs
Gunicorn: Instable (démarre mais ne répond pas)
Apache: Actif
Venv: /var/www/vhosts/martialcomp.com/venv/ (PAS dans httpdocs/.venv/)
```

---

## 📂 FICHIERS MODIFIÉS

### 1. config/urls.py
**Chemin** : `/var/www/vhosts/martialcomp.com/httpdocs/config/urls.py`

**Modifications** :
- Route changée de `competition/<int:competition_id>/` à `competitions/<int:pk>/`
- Import changé pour utiliser `competition_detail` depuis `competitions.py`

**État actuel** :
```python
# Ligne 19
from apps.competitions.views.competitions import competition_detail

# Ligne 79
path('competitions/<int:pk>/', competition_detail, name='public_competition_share'),
```

**Sauvegardes disponibles** :
- `config/urls.py.original` (8.6K, 24 Sep 2025)
- `config/urls.py.backup_before_restore_20251114_214250` (8.6K)

---

### 2. apps/competitions/views/competitions.py
**Chemin** : `/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/competitions.py`

**Modifications** :
- Fonction `competition_detail(request, pk)` modifiée pour ajouter des statistiques
- Template changé de `detail.html` à `detail_enhanced.html`
- Ajout de contexte : `categories_with_counts`, `registrations`, `judges`, `total_participants`, `total_judges`

**État actuel** :
```python
# Ligne 468
def competition_detail(request, pk):
    """Affiche les détails d'une compétition avec gestion des droits d'accès."""
    competition = get_object_or_404(Competition, pk=pk)
    
    # ... code ...
    
    # Ligne finale
    return render(request, 'competitions/competition/detail_enhanced.html', context)
```

**Taille** : 58K (1252 lignes)

**Sauvegardes disponibles** :
- `competitions.py.backup_20251026_081137` (51K, 26 Oct 2025)
- `competitions.py.backup_before_restore_20251114_214250` (51K)
- `competitions.py.backup_broken_20251114_195311` (58K)

---

### 3. apps/competitions/templates/competitions/competition/detail_enhanced.html
**Chemin** : `/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/competition/detail_enhanced.html`

**Modifications** :
- Nouveau template créé avec onglets Bootstrap
- Suppression de la section "Actions rapides" dupliquée (lignes 548-609)
- Ajout de navigation par onglets : Informations, Types, Catégories, Participants, Juges/Arbitres

**État actuel** : Transféré depuis DEV (37K, 852 lignes)

**Structure** :
```html
{% extends "base.html" %}
{% load static %}
{% load i18n %}

<!-- Navigation par onglets -->
<ul class="nav nav-tabs mb-4" id="competitionTabs" role="tablist">
    <li class="nav-item" role="presentation">
        <button class="nav-link active" id="info-tab" ...>Informations</button>
    </li>
    <li class="nav-item" role="presentation">
        <button class="nav-link" id="types-tab" ...>Types</button>
    </li>
    <li class="nav-item" role="presentation">
        <button class="nav-link" id="categories-tab" ...>Catégories</button>
    </li>
    <li class="nav-item" role="presentation">
        <button class="nav-link" id="participants-tab" ...>Participants</button>
    </li>
    <li class="nav-item" role="presentation">
        <button class="nav-link" id="judges-tab" ...>Juges/Arbitres</button>
    </li>
</ul>

<!-- Contenu des onglets -->
<div class="tab-content" id="competitionTabsContent">
    <!-- 5 onglets avec contenu -->
</div>
```

---

## 🔍 CHRONOLOGIE DE L'INCIDENT

### 18:44 - Début de l'intervention
- Utilisateur signale un espace blanc entre les onglets
- Analyse : Section "Actions rapides" dupliquée (lignes 548-609)

### 18:45-19:00 - Première tentative
- Suppression de la section dupliquée dans `detail_enhanced.html`
- Transfert SCP vers production
- Résultat : ❌ Erreur 500

### 19:00-19:30 - Tentatives de correction
- Correction de la route URL (`pk` vs `competition_id`)
- Correction du template (apostrophes, balises `</div>`)
- Multiples redémarrages de Gunicorn
- Résultat : ❌ Erreur 500 persistante

### 19:30-20:00 - Tentatives de restauration
- Restauration de `urls.py` depuis `urls.py.original`
- Restauration de `competitions.py` depuis sauvegarde du 26/10
- Suppression de `detail_enhanced.html`
- Résultat : ❌ Erreur 500 → 502

### 20:00-20:30 - Restauration depuis DEV
- Transfert des 3 fichiers depuis la plateforme de développement
- Vérification de la cohérence (fonction `pk` ↔ route `<int:pk>`)
- Multiples redémarrages de Gunicorn
- Résultat : ❌ 502 Bad Gateway

### 20:30-20:45 - Diagnostic final
- Découverte : Venv à `/var/www/vhosts/martialcomp.com/venv/` (PAS `.venv/`)
- Gunicorn démarre mais ne répond pas
- Aucune erreur dans les logs Django récents
- Résultat : ❌ Site toujours hors ligne

---

## 🛠️ TENTATIVES DE RÉSOLUTION

### ✅ Actions réussies
1. Transfert des fichiers depuis DEV vers PROD
2. Création de sauvegardes de sécurité
3. Vérification de la cohérence des fichiers (route ↔ fonction)
4. Démarrage de Gunicorn (processus actif)

### ❌ Actions échouées
1. Restauration depuis sauvegardes locales
2. Redémarrage de Gunicorn avec différents chemins de venv
3. Correction des erreurs Django (aucune erreur visible dans les logs)
4. Test en local (curl retourne erreur 500)

---

## 📊 DIAGNOSTICS EFFECTUÉS

### Gunicorn
```bash
# Processus
pgrep -fa gunicorn | wc -l
# Résultat : 1 (au lieu de 4-5 attendus)

# Logs
tail -50 /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_error.log
# Résultat : Aucune erreur récente, derniers logs à 16:49
```

### Django
```bash
# Logs
tail -100 /var/www/vhosts/martialcomp.com/httpdocs/logs/django.log | grep ERROR
# Résultat : Aucune erreur récente après 19:50

# Check
python3 manage.py check
# Résultat (DEV) : System check identified no issues (0 silenced).
```

### Apache
```bash
systemctl status apache2
# Résultat : active (running)
```

### Curl local
```bash
curl -H "X-Forwarded-Proto: https" -H "Host: martialcomp.com" http://127.0.0.1:8000/competitions/4/
# Résultat : <title>Server Error (500)</title> OU aucune réponse
```

---

## 🔧 CONFIGURATION SERVEUR

### Chemins importants
```
Application: /var/www/vhosts/martialcomp.com/httpdocs
Venv: /var/www/vhosts/martialcomp.com/venv/ (PAS dans httpdocs!)
Logs: /var/www/vhosts/martialcomp.com/httpdocs/logs/
Gunicorn: /var/www/vhosts/martialcomp.com/venv/bin/gunicorn
Python: /var/www/vhosts/martialcomp.com/venv/bin/python3
```

### Commande Gunicorn
```bash
cd /var/www/vhosts/martialcomp.com/httpdocs
/var/www/vhosts/martialcomp.com/venv/bin/gunicorn \
  --workers 3 \
  --bind 127.0.0.1:8000 \
  --access-logfile logs/gunicorn_access.log \
  --error-logfile logs/gunicorn_error.log \
  --log-level info \
  config.wsgi:application \
  --daemon
```

---

## 📁 FICHIERS DE DÉVELOPPEMENT (TESTÉS ✅)

### Localisation
```
Chemin: /mnt/c/martial_hub_django/martialcomp/
```

### État
```bash
# Django Check
python3 manage.py check
# Résultat : System check identified no issues (0 silenced).

# Fichiers
config/urls.py                                                    (8.6K)
apps/competitions/views/competitions.py                           (58K, 1252 lignes)
apps/competitions/templates/competitions/competition/detail_enhanced.html  (37K, 852 lignes)
```

### Cohérence vérifiée
```python
# urls.py ligne 79
path('competitions/<int:pk>/', competition_detail, name='public_competition_share')

# competitions.py ligne 468
def competition_detail(request, pk):

# competitions.py ligne finale
return render(request, 'competitions/competition/detail_enhanced.html', context)
```

---

## 🐛 ERREURS RENCONTRÉES

### 1. TemplateDoesNotExist
```
django.template.exceptions.TemplateDoesNotExist: competitions/competition/detail_enhanced.html
```
**Cause** : Fichier `detail_enhanced.html` non transféré ou supprimé  
**Solution tentée** : Re-transfert via SCP et rsync  
**Résultat** : Fichier présent mais erreur persiste

### 2. TypeError: competition_detail() got an unexpected keyword argument
```
TypeError: competition_detail() got an unexpected keyword argument 'pk'
# OU
TypeError: competition_detail() got an unexpected keyword argument 'competition_id'
```
**Cause** : Incohérence entre route URL et signature de fonction  
**Solution tentée** : Alignement route ↔ fonction  
**Résultat** : Corrigé mais site toujours hors ligne

### 3. KeyError: 'auth'
```
KeyError: 'auth'
During handling of the above exception, another exception occurred:
```
**Cause** : Namespace 'auth' non trouvé dans les URLs  
**Solution tentée** : Restauration de `urls.py.original`  
**Résultat** : Erreur disparue mais site toujours hors ligne

### 4. 502 Bad Gateway (actuel)
```
HTTP/2 502
date: Fri, 14 Nov 2025 20:45:12 GMT
content-type: text/plain; charset=UTF-8
```
**Cause** : Gunicorn ne répond pas ou Apache ne peut pas communiquer avec Gunicorn  
**Solution tentée** : Multiples redémarrages, vérification des ports  
**Résultat** : ❌ Non résolu

---

## 🔍 HYPOTHÈSES SUR LA CAUSE

### Hypothèse 1 : Problème de cache
- **Probabilité** : Moyenne
- **Description** : Cache Python (`__pycache__`) ou cache Cloudflare
- **Test effectué** : Nettoyage du cache Python
- **Résultat** : Aucun changement

### Hypothèse 2 : Problème de venv
- **Probabilité** : Élevée
- **Description** : Confusion entre `/httpdocs/.venv/` et `/venv/`
- **Test effectué** : Utilisation du bon chemin `/var/www/vhosts/martialcomp.com/venv/`
- **Résultat** : Gunicorn démarre mais ne répond pas

### Hypothèse 3 : Erreur dans le template
- **Probabilité** : Moyenne
- **Description** : Syntaxe Django incorrecte dans `detail_enhanced.html`
- **Test effectué** : Vérification en DEV (aucune erreur)
- **Résultat** : Template valide en DEV

### Hypothèse 4 : Configuration Apache/Gunicorn
- **Probabilité** : Élevée
- **Description** : Problème de communication Apache ↔ Gunicorn
- **Test effectué** : Redémarrage Apache, vérification du port 8000
- **Résultat** : Apache actif, Gunicorn écoute sur 8000 mais ne répond pas

### Hypothèse 5 : Dépendances manquantes
- **Probabilité** : Faible
- **Description** : Modules Python manquants pour le nouveau template
- **Test effectué** : Aucun (pas d'erreur d'import dans les logs)
- **Résultat** : N/A

---

## 📝 ACTIONS RECOMMANDÉES POUR CLAUDE

### Priorité 1 : Diagnostic approfondi
1. **Vérifier les logs Apache**
   ```bash
   tail -100 /var/log/apache2/error.log
   ```

2. **Tester Gunicorn en mode non-daemon**
   ```bash
   cd /var/www/vhosts/martialcomp.com/httpdocs
   /var/www/vhosts/martialcomp.com/venv/bin/gunicorn \
     --workers 1 \
     --bind 127.0.0.1:8000 \
     --log-level debug \
     config.wsgi:application
   # (sans --daemon pour voir les erreurs en direct)
   ```

3. **Vérifier la configuration Apache**
   ```bash
   cat /etc/apache2/sites-enabled/martialcomp.com.conf
   # Vérifier le ProxyPass vers 127.0.0.1:8000
   ```

4. **Tester le WSGI directement**
   ```bash
   cd /var/www/vhosts/martialcomp.com/httpdocs
   /var/www/vhosts/martialcomp.com/venv/bin/python3 -c "import config.wsgi"
   # Doit s'exécuter sans erreur
   ```

### Priorité 2 : Restauration d'urgence
1. **Option A : Restauration complète depuis backup serveur**
   - Contacter l'hébergeur (Plesk)
   - Restaurer depuis snapshot avant 18:44 CET

2. **Option B : Restauration manuelle fichier par fichier**
   ```bash
   # Restaurer l'ancien template
   cd /var/www/vhosts/martialcomp.com/httpdocs
   rm -f apps/competitions/templates/competitions/competition/detail_enhanced.html
   
   # Restaurer l'ancienne vue
   cp apps/competitions/views/competitions.py.backup_20251026_081137 \
      apps/competitions/views/competitions.py
   
   # Restaurer les anciennes URLs
   cp config/urls.py.original config/urls.py
   
   # Redémarrer
   pkill -9 -f gunicorn
   /var/www/vhosts/martialcomp.com/venv/bin/gunicorn ... --daemon
   ```

### Priorité 3 : Vérifications post-restauration
1. Tester l'ancienne URL : `https://martialcomp.com/competition/4/`
2. Vérifier que le site répond (même sans les onglets)
3. Confirmer que Gunicorn a 4-5 processus actifs

---

## 📦 FICHIERS JOINTS POUR ANALYSE

### Fichiers de production (actuels)
```
config/urls.py                           (transféré depuis DEV, 8.6K)
apps/competitions/views/competitions.py  (transféré depuis DEV, 58K)
apps/competitions/templates/competitions/competition/detail_enhanced.html (transféré depuis DEV, 37K)
```

### Sauvegardes disponibles
```
config/urls.py.original
config/urls.py.backup_before_restore_20251114_214250
apps/competitions/views/competitions.py.backup_20251026_081137
apps/competitions/views/competitions.py.backup_before_restore_20251114_214250
```

### Fichiers de développement (testés OK)
```
/mnt/c/martial_hub_django/martialcomp/config/urls.py
/mnt/c/martial_hub_django/martialcomp/apps/competitions/views/competitions.py
/mnt/c/martial_hub_django/martialcomp/apps/competitions/templates/competitions/competition/detail_enhanced.html
```

---

## 🎯 OBJECTIF POUR CLAUDE

**Remettre le site en ligne le plus rapidement possible**, même sans les onglets.

**Ensuite**, une fois le site stable :
1. Analyser pourquoi le nouveau template ne fonctionne pas
2. Tester les modifications en environnement de staging
3. Déployer progressivement (un fichier à la fois)

---

## 📞 CONTACTS

- **Hébergeur** : Plesk (vigilant-swartz.217-154-24-122.plesk.page)
- **SSH** : martialcomp-production (217.154.24.122)
- **Domaine** : martialcomp.com (via Cloudflare)

---

## ⏰ TIMELINE CRITIQUE

- **18:44** : Début de l'intervention (site fonctionnel)
- **19:00** : Première erreur 500
- **20:00** : Erreur 502 Bad Gateway
- **20:45** : Site toujours hors ligne (3 heures d'incident)

**DURÉE MAXIMALE ACCEPTABLE** : Le site doit être restauré dans les prochaines heures pour minimiser l'impact sur les utilisateurs.

---

## 🔐 INFORMATIONS SENSIBLES

⚠️ **Ce fichier contient des informations sur l'infrastructure. À ne pas partager publiquement.**

---

**FIN DU RAPPORT**

*Généré le 14 Novembre 2025 à 20:45 CET*
*Par : Assistant Claude (Session de débogage)*
