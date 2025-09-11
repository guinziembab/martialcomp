# 🚀 Plan de Migration Production - Structure apps/

## 📋 Vue d'ensemble

**Objectif :** Migrer la production de l'ancienne structure vers la nouvelle structure `apps/` sans interruption de service.

**Infrastructure actuelle :**
- Serveur : IONOS Debian
- Web : Nginx + Gunicorn
- BDD : PostgreSQL
- Cache : Redis
- Path : `/var/www/vhosts/martialcomp.com/httpdocs`

---

## 🎯 Phase 1 : Préparation et Sauvegarde (30 min)

### ✅ 1.1 Sauvegarde Complète
```bash
# Connexion au serveur de production
ssh user@martialcomp.com

# Créer le dossier de sauvegarde
sudo mkdir -p /var/backups/martialcomp/migration_$(date +%Y%m%d_%H%M%S)
cd /var/backups/martialcomp/migration_$(date +%Y%m%d_%H%M%S)

# Sauvegarde du code source
sudo tar -czf code_backup.tar.gz -C /var/www/vhosts/martialcomp.com httpdocs/

# Sauvegarde de la base de données
sudo -u postgres pg_dump martialcomp > martialcomp_backup.sql

# Sauvegarde des fichiers média
sudo tar -czf media_backup.tar.gz -C /var/www/vhosts/martialcomp.com media/

# Sauvegarde de la configuration
sudo cp -r /etc/nginx/conf.d/martialcomp.com.conf ./
sudo cp /etc/systemd/system/martialcomp.service ./
```

### ✅ 1.2 Test de l'Environnement Actuel
```bash
# Vérifier l'état des services
sudo systemctl status martialcomp
sudo systemctl status nginx
sudo systemctl status postgresql
sudo systemctl status redis

# Test de connectivité
curl -f https://martialcomp.com/health/ || echo "Service DOWN"

# Vérifier les logs
sudo tail -f /var/www/vhosts/martialcomp.com/logs/django.log
```

---

## 🔄 Phase 2 : Préparation de la Nouvelle Structure (45 min)

### ✅ 2.1 Création de la Structure apps/
```bash
# Aller dans le répertoire de production
cd /var/www/vhosts/martialcomp.com/httpdocs

# Créer le dossier apps temporaire
sudo mkdir -p apps_new

# Identifier les applications actuelles à migrer
APPS=(
    "competitions" "organizations" "multitenant" "grades"
    "finances" "shop" "documents" "family_management"
    "permissions_manager" "payment" "accounts" "security"
)
```

### ✅ 2.2 Migration des Applications
```bash
# Déplacer chaque application vers apps_new/
for app in "${APPS[@]}"; do
    if [ -d "$app" ]; then
        echo "Migration de $app vers apps_new/"
        sudo mv "$app" "apps_new/"
        
        # Créer un __init__.py propre
        echo "# $app application" | sudo tee "apps_new/$app/__init__.py"
        
        echo "✅ $app migré"
    else
        echo "⚠️ $app non trouvé"
    fi
done
```

### ✅ 2.3 Mise à Jour de la Configuration
```bash
# Sauvegarder l'ancien base.py
sudo cp config/settings/base.py config/settings/base.py.backup_migration

# Mettre à jour le sys.path dans base.py
sudo sed -i "/sys.path.append/c\\sys.path.append(str(BASE_DIR / 'apps'))" config/settings/base.py

# Mettre à jour INSTALLED_APPS (remplacer les références .apps.Config)
sudo sed -i "s/'grades.apps.GradesConfig'/'grades'/g" config/settings/base.py
```

---

## 🧪 Phase 3 : Tests en Mode Maintenance (30 min)

### ✅ 3.1 Activation du Mode Maintenance
```bash
# Créer une page de maintenance temporaire
sudo cat > /var/www/vhosts/martialcomp.com/httpdocs/maintenance.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Maintenance - MartialComp</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial; text-align: center; padding: 50px; }
        .container { max-width: 600px; margin: 0 auto; }
        .logo { color: #e74c3c; font-size: 2em; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🥋 MartialComp</div>
        <h1>Maintenance en cours</h1>
        <p>Nous mettons à jour notre plateforme pour vous offrir une meilleure expérience.</p>
        <p><strong>Durée estimée :</strong> 15 minutes</p>
        <p>Merci de votre patience !</p>
    </div>
</body>
</html>
EOF

# Rediriger temporairement vers la page de maintenance (dans Nginx)
sudo sed -i '/location \/ {/a\    return 503;' /etc/nginx/conf.d/martialcomp.com.conf
sudo sed -i '/server {/a\    error_page 503 /maintenance.html;\n    location = /maintenance.html {\n        root /var/www/vhosts/martialcomp.com/httpdocs;\n        internal;\n    }' /etc/nginx/conf.d/martialcomp.com.conf

# Recharger Nginx
sudo systemctl reload nginx
```

### ✅ 3.2 Tests de la Nouvelle Structure
```bash
# Arrêter l'ancien service
sudo systemctl stop martialcomp

# Renommer les dossiers (basculement)
sudo mv apps apps_old_backup
sudo mv apps_new apps

# Activer l'environnement virtuel
source /var/www/vhosts/martialcomp.com/.venv/bin/activate

# Test de configuration Django
python manage.py check

# Test des migrations
python manage.py migrate --dry-run

# Test de collecte des statiques
python manage.py collectstatic --dry-run
```

---

## 🚀 Phase 4 : Déploiement et Validation (20 min)

### ✅ 4.1 Déploiement Final
```bash
# Si les tests passent, redémarrer le service
sudo systemctl start martialcomp

# Vérifier le statut
sudo systemctl status martialcomp

# Test de fonctionnement interne
curl -f http://localhost:8000/health/ || echo "Service DOWN"

# Retirer le mode maintenance de Nginx
sudo sed -i '/return 503;/d' /etc/nginx/conf.d/martialcomp.com.conf
sudo sed -i '/error_page 503/,/}/d' /etc/nginx/conf.d/martialcomp.com.conf

# Recharger Nginx
sudo systemctl reload nginx
```

### ✅ 4.2 Tests de Validation
```bash
# Test complet de la plateforme
curl -f https://martialcomp.com/ || echo "Site DOWN"
curl -f https://martialcomp.com/fr/competitions/dashboard/ || echo "Dashboard DOWN"

# Vérifier les logs
sudo tail -f /var/www/vhosts/martialcomp.com/logs/django.log

# Test de connexion utilisateur
# (test manuel dans le navigateur)
```

---

## 🔧 Phase 5 : Nettoyage et Optimisation (15 min)

### ✅ 5.1 Nettoyage
```bash
# Supprimer les anciens caches Python
sudo find /var/www/vhosts/martialcomp.com/httpdocs -name "__pycache__" -type d -exec rm -rf {} +
sudo find /var/www/vhosts/martialcomp.com/httpdocs -name "*.pyc" -delete

# Redémarrer tous les services pour une base propre
sudo systemctl restart martialcomp
sudo systemctl restart nginx
sudo systemctl restart redis
```

### ✅ 5.2 Vérification Finale
```bash
# Tests complets automatisés
python manage.py check --deploy
python manage.py test competitions --keepdb

# Vérifier les métriques de performance
curl -w "@curl-format.txt" -o /dev/null -s https://martialcomp.com/
```

---

## 📊 Phase 6 : Monitoring Post-Migration (Continue)

### ✅ 6.1 Surveillance
```bash
# Surveiller les logs en temps réel
sudo tail -f /var/www/vhosts/martialcomp.com/logs/django.log &
sudo tail -f /var/log/nginx/error.log &

# Monitoring des performances
htop
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :8000
```

### ✅ 6.2 Tests Utilisateur
- [ ] Connexion utilisateur
- [ ] Navigation dashboard
- [ ] Création de compétition
- [ ] Gestion des participants
- [ ] API endpoints
- [ ] Multilinguisme

---

## 🚨 Plan de Rollback (En cas de problème)

```bash
# ROLLBACK COMPLET en cas d'urgence

# 1. Réactiver la maintenance
sudo sed -i '/location \/ {/a\    return 503;' /etc/nginx/conf.d/martialcomp.com.conf
sudo systemctl reload nginx

# 2. Arrêter le nouveau service
sudo systemctl stop martialcomp

# 3. Restaurer l'ancienne structure
sudo rm -rf apps
sudo mv apps_old_backup apps

# 4. Restaurer l'ancienne configuration
sudo cp config/settings/base.py.backup_migration config/settings/base.py

# 5. Redémarrer l'ancien service
sudo systemctl start martialcomp

# 6. Désactiver la maintenance
sudo sed -i '/return 503;/d' /etc/nginx/conf.d/martialcomp.com.conf
sudo systemctl reload nginx

# 7. Vérification
curl -f https://martialcomp.com/
```

---

## 📋 Checklist de Migration

### Pré-Migration
- [ ] ✅ Sauvegarde complète effectuée
- [ ] ✅ Tests de l'environnement actuel
- [ ] ✅ Plan de rollback préparé
- [ ] ✅ Notification aux utilisateurs (optionnel)

### Migration
- [ ] ✅ Mode maintenance activé
- [ ] ✅ Structure apps/ créée
- [ ] ✅ Applications migrées
- [ ] ✅ Configuration mise à jour
- [ ] ✅ Tests réussis

### Post-Migration
- [ ] ✅ Mode maintenance désactivé
- [ ] ✅ Services redémarrés
- [ ] ✅ Tests fonctionnels validés
- [ ] ✅ Monitoring actif
- [ ] ✅ Performance vérifiée

---

## 🎯 Résultat Attendu

**Structure finale en production :**

```
/var/www/vhosts/martialcomp.com/httpdocs/
├── manage.py
├── config/
│   ├── settings/
│   ├── urls.py
│   └── wsgi.py
├── apps/                    ← 🎯 NOUVELLE STRUCTURE
│   ├── competitions/
│   ├── organizations/
│   ├── multitenant/
│   ├── grades/
│   ├── finances/
│   ├── shop/
│   ├── documents/
│   ├── family_management/
│   ├── permissions_manager/
│   ├── payment/
│   ├── accounts/
│   └── security/
├── static/
├── media/
├── locale/
└── requirements.txt
```

**✅ Production identique au développement**
**✅ Maintenance minimale (< 20 minutes)**
**✅ Rollback possible à tout moment**
**✅ Zéro perte de données**