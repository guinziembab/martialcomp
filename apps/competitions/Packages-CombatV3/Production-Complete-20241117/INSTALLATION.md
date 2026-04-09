# 📦 Guide d'Installation - Package Production Complet

## 🎯 Vue d'Ensemble

Ce package contient **TOUTES** les modifications de la journée du 17 novembre 2024 :
- Interface Combat V3 complète et fonctionnelle
- Template Poule Professionnel amélioré
- Toutes les corrections techniques

## 📋 Prérequis

- Serveur de production accessible via SSH
- Accès root ou sudo pour redémarrer les services
- Python 3.x installé
- Django 5.1+ installé

## 🚀 Installation Rapide

### Étape 1 : Se connecter au serveur

```bash
ssh martialcomp-production
cd /mnt/c/martial_hub_django/martialcomp
```

### Étape 2 : Exécuter le script

```bash
bash apps/competitions/Packages-CombatV3/Production-Complete-20241117/DEPLOY.sh
```

C'est tout ! Le script fait tout automatiquement.

## 📝 Installation Manuelle (si nécessaire)

### 1. Sauvegarder les fichiers

```bash
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# Templates
cp apps/competitions/templates/competitions/combat/*.html $BACKUP_DIR/

# Vues et URLs
cp apps/competitions/views/combat.py $BACKUP_DIR/
cp apps/competitions/urls/combat.py $BACKUP_DIR/

# Config
cp config/wsgi.py $BACKUP_DIR/
cp config/urls.py $BACKUP_DIR/
cp apps/competitions/templatetags/combat_filters.py $BACKUP_DIR/
```

### 2. Copier les fichiers du package

```bash
PACKAGE="apps/competitions/Packages-CombatV3/Production-Complete-20241117"

# Templates
cp $PACKAGE/templates/competitions/combat/*.html \
   apps/competitions/templates/competitions/combat/

# Nouveaux fichiers API
cp $PACKAGE/views/combat_api_views.py apps/competitions/
cp $PACKAGE/urls/combat_api_urls.py apps/competitions/

# Config
cp $PACKAGE/config/wsgi.py config/
cp $PACKAGE/templatetags/combat_filters.py \
   apps/competitions/templatetags/
```

### 3. Appliquer les modifications

Voir les fichiers de patch dans le package :
- `views/combat_patches.txt` - Modifications pour views/combat.py
- `urls/combat_urls_patch.py` - Modifications pour urls/combat.py
- `config/urls_patch.py` - Modifications pour config/urls.py

### 4. Créer le répertoire des drapeaux

```bash
mkdir -p static/images/flags
```

### 5. Redémarrer le serveur

```bash
sudo systemctl restart gunicorn
# ou
sudo supervisorctl restart gunicorn
```

## ✅ Vérification

1. **Interface Combat** : `/en/competitions/combat/combats/<id>/interface-v2/`
2. **Template Poule** : `/en/competitions/combat/poules/<id>/`
3. **API** : Vérifier les logs pour les appels API

## 🔄 Rollback

```bash
BACKUP_DIR="backups/YYYYMMDD_HHMMSS"  # Remplacer
cp $BACKUP_DIR/*.html apps/competitions/templates/competitions/combat/
# ... (voir README.md pour la liste complète)
sudo systemctl restart gunicorn
```
