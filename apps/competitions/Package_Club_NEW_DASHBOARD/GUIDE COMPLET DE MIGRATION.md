# 🚀 GUIDE DE MIGRATION - Dashboard Club v2.0.0

## 📋 TABLE DES MATIÈRES
1. [Préparation](#preparation)
2. [Sauvegarde](#sauvegarde)
3. [Installation des nouveaux fichiers](#installation)
4. [Migration du template](#migration-template)
5. [Tests & Validation](#tests)
6. [Rollback (en cas de problème)](#rollback)

---

## 1️⃣ PRÉPARATION {#preparation}

### Prérequis
- ✅ Accès SSH au serveur de production
- ✅ Accès FTP/SFTP (WinSCP)
- ✅ Droits d'écriture sur les répertoires static/ et templates/
- ✅ Accès à la console Django

### Environnement de test recommandé
Testez d'abord sur un environnement de développement/staging avant la production.

---

## 2️⃣ SAUVEGARDE {#sauvegarde}

### A. Sauvegarde des fichiers actuels
```bash
# Connexion SSH
ssh user@martialcomp.com

# Créer un répertoire de sauvegarde
mkdir -p /home/martialcomp/backups/club_dashboard_v1_$(date +%Y%m%d_%H%M%S)

# Sauvegarder le template actuel
cp /home/martialcomp/templates/dashboard/club.html \
   /home/martialcomp/backups/club_dashboard_v1_$(date +%Y%m%d_%H%M%S)/

# Sauvegarder les fichiers static si existants
cp -r /home/martialcomp/static/js/club_* \
   /home/martialcomp/backups/club_dashboard_v1_$(date +%Y%m%d_%H%M%S)/ 2>/dev/null || true

cp -r /home/martialcomp/static/css/club_* \
   /home/martialcomp/backups/club_dashboard_v1_$(date +%Y%m%d_%H%M%S)/ 2>/dev/null || true
```

### B. Sauvegarde base de données (précaution)
```bash
# Dump PostgreSQL
pg_dump -U martialcomp_user -d martialcomp_db > \
   /home/martialcomp/backups/db_backup_$(date +%Y%m%d_%H%M%S).sql
```

---

## 3️⃣ INSTALLATION DES NOUVEAUX FICHIERS {#installation}

### A. Structure des répertoires
```bash
# Créer les répertoires nécessaires
mkdir -p /home/martialcomp/static/js/dashboard/
mkdir -p /home/martialcomp/static/css/dashboard/
```

### B. Upload des fichiers JavaScript

**Via WinSCP ou SFTP:**

1. **club_dashboard_core.js** → `/home/martialcomp/static/js/dashboard/club_dashboard_core.js`
2. **club_dashboard_bulk.js** → `/home/martialcomp/static/js/dashboard/club_dashboard_bulk.js`
3. **club_dashboard_import.js** → `/home/martialcomp/static/js/dashboard/club_dashboard_import.js`

**Via SSH (si fichiers sur serveur local):**
```bash
# Copier les fichiers
cp club_dashboard_core.js /home/martialcomp/static/js/dashboard/
cp club_dashboard_bulk.js /home/martialcomp/static/js/dashboard/
cp club_dashboard_import.js /home/martialcomp/static/js/dashboard/

# Vérifier les permissions
chmod 644 /home/martialcomp/static/js/dashboard/*.js
```

### C. Upload du fichier CSS
```bash
cp club_dashboard.css /home/martialcomp/static/css/dashboard/
chmod 644 /home/martialcomp/static/css/dashboard/club_dashboard.css
```

### D. Collectstatic Django
```bash
cd /home/martialcomp/
python manage.py collectstatic --noinput
```

---

## 4️⃣ MIGRATION DU TEMPLATE {#migration-template}

### A. Créer le nouveau template optimisé

Le template club.html optimisé doit suivre cette structure:
```django
{% extends "base.html" %}
{% load i18n %}
{% load static %}
{% load custom_filters %}

{% block title %}{% trans "Tableau de bord" %}{% if club %} | {{ club.name }}{% endif %}{% endblock %}

{% block extra_css %}
<!-- CSS externe optimisé -->
<link rel="stylesheet" href="{% static 'css/dashboard/club_dashboard.css' %}">
{% endblock %}

{% block content %}
<!-- CONTENU HTML DU DASHBOARD -->
<!-- Voir section suivante pour le HTML optimisé -->
{% endblock %}

{% block extra_js %}
<!-- URLs Django pour JavaScript -->
<script>
const DJANGO_URLS = {
    practitioner_delete: "{% url 'competitions:club:practitioner_delete' practitioner_id=0 %}",
    practitioner_toggle_status: "{% url 'competitions:club:practitioner_toggle_status' pk=0 %}",
    import_export: "{% url 'competitions:club:import_export' %}",
    import_export_ajax: "{% url 'competitions:club:import_export_ajax' %}",
    available_competitions: "{% url 'competitions:club:available_competitions' %}",
    bulk_registration_process: "{% url 'competitions:club:bulk_registration_process' %}"
};

const DJANGO_TRANS = {
    desactiver: "{% trans 'Désactiver' %}",
    activer: "{% trans 'Activer' %}",
    actif: "{% trans 'Actif' %}",
    inactif: "{% trans 'Inactif' %}",
    confirmDelete: "{% trans 'Êtes-vous sûr de vouloir supprimer ce pratiquant ?' %}",
    deleteSuccess: "{% trans 'Pratiquant supprimé avec succès' %}",
    deleteError: "{% trans 'Erreur lors de la suppression' %}",
    statusError: "{% trans 'Erreur lors du changement de statut' %}"
};
</script>

<!-- Modules JavaScript externes -->
<script src="{% static 'js/dashboard/club_dashboard_core.js' %}"></script>
<script src="{% static 'js/dashboard/club_dashboard_bulk.js' %}"></script>
<script src="{% static 'js/dashboard/club_dashboard_import.js' %}"></script>

<!-- Initialisation -->
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Initialiser le dashboard principal
    ClubDashboard.init(DJANGO_URLS, DJANGO_TRANS);
    
    // Initialiser les modules
    BulkRegistration.init(DJANGO_URLS, DJANGO_TRANS);
    CSVImport.init(DJANGO_URLS, DJANGO_TRANS);
    
    console.log('✅ Dashboard Club v2.0.0 initialisé');
});
</script>
{% endblock %}
```

### B. Points critiques à vérifier dans le HTML

**1. IDs des boutons (CORRECTION MAJEURE):**
```html
<!-- ✅ CORRECT - IDs avec tirets -->
<button type="button" class="btn btn-success btn-sm me-2" id="import-csv-btn">
    <i class="fas fa-file-import"></i> {% trans "Import CSV" %}
</button>

<button type="button" class="btn btn-info btn-sm me-2" id="bulk-registration-btn">
    <i class="fas fa-trophy"></i> {% trans "Inscription en masse" %}
</button>

<!-- ❌ ANCIEN - Ne plus utiliser -->
<!-- <button id="importCsvBtn"> -->
<!-- <button id="bulkRegistrationBtn"> -->
```

**2. Structure des checkboxes pratiquants:**
```html
<input type="checkbox" 
       class="practitioner-checkbox" 
       value="{{ practitioner.id }}"
       data-name="{{ practitioner.full_name }}"
       id="practitioner-{{ practitioner.id }}">
```

**3. Checkbox "Tout sélectionner":**
```html
<input type="checkbox" 
       id="select-all-practitioners"
       class="form-check-input">
```

### C. Upload du nouveau template
```bash
# Copier le nouveau template
cp club_optimized.html /home/martialcomp/templates/dashboard/club.html

# Vérifier les permissions
chmod 644 /home/martialcomp/templates/dashboard/club.html
```

### D. Vérifier l'encodage UTF-8
```bash
# Vérifier que le fichier est bien en UTF-8
file -i /home/martialcomp/templates/dashboard/club.html
# Devrait afficher: text/html; charset=utf-8

# Si ce n'est pas UTF-8, convertir:
iconv -f ISO-8859-1 -t UTF-8 club.html > club_utf8.html
```

---

## 5️⃣ TESTS & VALIDATION {#tests}

### A. Checklist de tests fonctionnels

| Fonctionnalité | Test | Statut |
|---------------|------|--------|
| **Navigation onglets** | Cliquer sur tous les onglets | ⬜ |
| **Persistance onglet** | Rafraîchir la page | ⬜ |
| **Import CSV** | Cliquer sur bouton "Import CSV" | ⬜ |
| **Sélection fichier** | Sélectionner un fichier .csv | ⬜ |
| **Upload CSV** | Uploader un fichier valide | ⬜ |
| **Validation format** | Tenter .txt (doit être refusé) | ⬜ |
| **Inscription en masse - Modal** | Cliquer sur "Inscription en masse" | ⬜ |
| **Sélection pratiquants** | Cocher des pratiquants | ⬜ |
| **Tout sélectionner** | Cocher/décocher "Tout sélectionner" | ⬜ |
| **Choix compétition** | Sélectionner une compétition | ⬜ |
| **Inscription** | Valider l'inscription | ⬜ |
| **Suppression pratiquant** | Supprimer un pratiquant | ⬜ |
| **Toggle statut** | Activer/désactiver pratiquant | ⬜ |
| **QR Code download** | Télécharger un QR code | ⬜ |
| **Calcul âges** | Vérifier affichage âges | ⬜ |
| **Responsive mobile** | Tester sur mobile | ⬜ |
| **Alertes** | Vérifier affichage alertes | ⬜ |

### B. Tests dans la console navigateur
```javascript
// Ouvrir la console (F12) et tester:

// 1. Vérifier que les modules sont chargés
console.log(ClubDashboard);
console.log(BulkRegistration);
console.log(CSVImport);

// 2. Vérifier l'initialisation
console.log(ClubDashboard.state.initialized); // devrait afficher: true

// 3. Tester une alerte
ClubDashboard.showAlert('Test de message', 'success');

// 4. Vérifier les URLs
console.log(ClubDashboard.urls);

// 5. Tester le calcul des âges
ClubDashboard.calculateAges();
```

### C. Monitoring des erreurs
```bash
# Surveiller les logs Django en temps réel
tail -f /home/martialcomp/logs/django.log

# Surveiller les logs Apache/Nginx
tail -f /var/log/apache2/error.log
# ou
tail -f /var/log/nginx/error.log
```

### D. Test de charge (optionnel)
```bash
# Installer Apache Bench si pas déjà fait
sudo apt-get install apache2-utils

# Test de charge basique
ab -n 100 -c 10 https://martialcomp.com/dashboard/club/
```

---

## 6️⃣ ROLLBACK (en cas de problème) {#rollback}

### A. Restauration rapide

Si vous rencontrez des problèmes critiques:
```bash
# Trouver le répertoire de backup
BACKUP_DIR=$(ls -td /home/martialcomp/backups/club_dashboard_v1_* | head -1)

# Restaurer l'ancien template
cp $BACKUP_DIR/club.html /home/martialcomp/templates/dashboard/club.html

# Redémarrer Django
sudo systemctl restart gunicorn
# ou
touch /home/martialcomp/reload
```

### B. Rollback complet
```bash
# Restaurer tous les fichiers
cp $BACKUP_DIR/club.html /home/martialcomp/templates/dashboard/

# Supprimer les nouveaux fichiers JS/CSS
rm -f /home/martialcomp/static/js/dashboard/club_dashboard_*
rm -f /home/martialcomp/static/css/dashboard/club_dashboard.css

# Recollect static
python manage.py collectstatic --noinput

# Redémarrer
sudo systemctl restart gunicorn
```

---

## 7️⃣ POST-MIGRATION

### A. Optimisations recommandées

**1. Minification des fichiers (production):**
```bash
# Installer uglify-js pour minifier
npm install -g uglify-js
npm install -g clean-css-cli

# Minifier JavaScript
uglifyjs club_dashboard_core.js -c -m -o club_dashboard_core.min.js
uglifyjs club_dashboard_bulk.js -c -m -o club_dashboard_bulk.min.js
uglifyjs club_dashboard_import.js -c -m -o club_dashboard_import.min.js

# Minifier CSS
cleancss -o club_dashboard.min.css club_dashboard.css
```

**2. Configuration de cache:**

Dans `settings.py`:
```python
# Cache des fichiers static
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# Headers de cache
MIDDLEWARE += [
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
]

CACHE_MIDDLEWARE_SECONDS = 3600  # 1 heure
```

**3. Compression Gzip:**
```bash
# Dans Apache config (.htaccess ou httpd.conf)
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/html text/plain text/xml text/css text/javascript application/javascript
</IfModule>
```

### B. Monitoring continu

**1. Installer Sentry (optionnel mais recommandé):**
```python
# Dans settings.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="YOUR_SENTRY_DSN",
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,
)
```

**2. Logs structurés:**
```python
# Dans settings.py - Configuration logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/home/martialcomp/logs/dashboard.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'dashboard': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

---

## 8️⃣ TROUBLESHOOTING

### Problèmes courants et solutions

| Problème | Cause probable | Solution |
|----------|---------------|----------|
| Boutons ne répondent pas | IDs incorrects | Vérifier que les IDs sont `import-csv-btn` et `bulk-registration-btn` |
| Erreur 404 sur fichiers JS | Collectstatic pas lancé | Lancer `python manage.py collectstatic` |
| Caractères bizarres (Ã©, Ã ) | Encodage non UTF-8 | Reconvertir le fichier en UTF-8 avec `iconv` |
| Modal ne s'ouvre pas | Bootstrap pas chargé | Vérifier que Bootstrap 5 est dans `base.html` |
| Compétitions non chargées | URL incorrecte | Vérifier `available_competitions` dans DJANGO_URLS |
| Âges non calculés | Script non initialisé | Vérifier la console pour erreurs JS |
| CSS ne s'applique pas | Cache navigateur | Faire Ctrl+F5 ou vider le cache |
| Erreur CSRF | Token manquant | Vérifier `{% csrf_token %}` dans les formulaires |

### Commandes de diagnostic
```bash
# Vérifier les fichiers static
python manage.py findstatic js/dashboard/club_dashboard_core.js

# Vérifier les templates
python manage.py check --deploy

# Tester les URLs
python manage.py show_urls | grep club

# Vérifier les permissions
ls -la /home/martialcomp/static/js/dashboard/
ls -la /home/martialcomp/templates/dashboard/club.html
```

---

## 9️⃣ CONTACT & SUPPORT

En cas de problème persistant:

1. **Vérifier les logs:** `/home/martialcomp/logs/`
2. **Console navigateur:** Rechercher les erreurs JavaScript (F12)
3. **Sentry:** Consulter les erreurs capturées
4. **Documentation:** Relire ce guide attentivement

---

## ✅ CHECKLIST FINALE

Avant de considérer la migration terminée:

- [ ] Tous les fichiers sont uploadés
- [ ] Collectstatic exécuté avec succès
- [ ] Template optimisé en place
- [ ] Encodage UTF-8 vérifié
- [ ] Tests fonctionnels passés (voir section 5A)
- [ ] Tests sur mobile effectués
- [ ] Logs vérifiés (pas d'erreurs)
- [ ] Performance acceptable (temps de chargement < 2s)
- [ ] Backup effectué et testé
- [ ] Documentation mise à jour

---

**VERSION DU GUIDE:** 2.0.0  
**DATE:** 2024-11-17  
**AUTEUR:** Assistant Claude pour MartialComp