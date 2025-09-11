# INSTRUCTIONS DE DÉPLOIEMENT MANUEL

## 🎯 Objectif
Corriger l'erreur 500 sur https://martialcomp.com/fr/competitions/federations/3/examens/

## 📦 Contenu du Package
- `apps/competitions/views/federations.py` - Vue corrigée avec gestion d'erreurs
- `apps/competitions/templates/competitions/federations/examens/list.html` - Template corrigé
- `apps/competitions/urls/dashboard.py` - URLs corrigées
- `deploy_on_server.sh` - Script de déploiement automatique

## 🚀 Étapes de Déploiement

### 1. Transférer le package sur le serveur
```bash
# Depuis votre machine locale
scp -r deployment_package_* root@martialcomp.com:/tmp/

# Ou utiliser votre méthode de transfert préférée
```

### 2. Se connecter au serveur et appliquer
```bash
# Connexion au serveur
ssh root@martialcomp.com

# Aller dans le répertoire de l'application
cd /var/www/martialcomp

# Copier les fichiers du package
cp -r /tmp/deployment_package_*/apps/* apps/
cp /tmp/deployment_package_*/fix_all_issues_production.py .

# Exécuter le script de déploiement
chmod +x /tmp/deployment_package_*/deploy_on_server.sh
/tmp/deployment_package_*/deploy_on_server.sh
```

### 3. Vérification
- Tester: https://martialcomp.com/fr/competitions/federations/3/examens/
- Code attendu: 200 (OK) ou 302 (redirection si non connecté)

## 🔍 En Cas de Problème
```bash
# Voir les logs
tail -f /var/log/django/martialcomp.log
tail -f /var/log/nginx/error.log

# Restaurer la sauvegarde si nécessaire
cd /var/www/martialcomp
cp backup_*/federations.py apps/competitions/views/
systemctl restart gunicorn
```

## ✅ Fichiers Corrigés
- **federations.py**: Gestion d'erreurs améliorée pour les examens
- **list.html**: Template corrigé avec bonne extension et blocks
- **dashboard.py**: URL pattern manquant ajouté
