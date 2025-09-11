# 🚀 Migration Production → Local - Guide Complet

## 📊 État Actuel (Sauvegardé)

✅ **Sauvegarde complète effectuée** dans `backup_dev_20250630_211015/`
- 24 utilisateurs, 4 fédérations, 3 clubs
- Configuration développement fonctionnelle
- Système d'onboarding opérationnel
- Authentification avec quelques problèmes (raison de la migration)

## 🎯 Objectif

Rapatrier la **configuration de production stable** et les **données réelles** pour résoudre les problèmes d'authentification/enregistrement.

## 📋 Options de Migration

### 🔧 Option 1 : Migration SSH Automatique (Recommandée)

Si vous avez accès SSH au serveur de production :

```bash
chmod +x migrate_production_to_local.sh
./migrate_production_to_local.sh
```

Le script vous demandera :
- Adresse du serveur (ex: `user@server.com`)
- Chemin du projet (ex: `/home/user/martialcomp`)

### 📥 Option 2 : Migration Manuelle

Si pas d'accès SSH direct :

1. **Consultez les instructions** :
   ```bash
   cat production_manual_20250630_211751/INSTRUCTIONS_MIGRATION.md
   ```

2. **Sur le serveur de production**, exécutez :
   ```bash
   cd /chemin/vers/martialcomp
   python3 manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission > production_data_$(date +%Y%m%d_%H%M%S).json
   ```

3. **Téléchargez ces fichiers** vers `production_manual_20250630_211751/` :
   - `config/settings.py` → `settings_prod.py`
   - `config/urls.py` → `urls_prod.py`
   - `requirements.txt` → `requirements_prod.txt`
   - `production_data_*.json`
   - `competitions/models/` (dossier complet)
   - `competitions/views/auth.py`
   - `competitions/views/custom_login.py`
   - `competitions/signals.py`
   - `competitions/templates/competitions/welcome.html`
   - `competitions/migrations/`

4. **Appliquez la configuration** :
   ```bash
   cd production_manual_20250630_211751
   ./apply_production_config.sh
   ```

## 🔍 Vérification Avant Migration

```bash
python3 check_system_status.py
```

## ⚠️  Points Importants

### 🛡️ Sécurité
- ✅ Sauvegarde automatique créée
- ✅ Script de restauration disponible
- ✅ Aucune perte de données possible

### 🔧 Adaptations Nécessaires

Après migration, **vérifiez/adaptez** dans `config/settings.py` :

```python
# Base de données (garder local)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'martialcomp_db',
        'USER': 'postgres',
        'PASSWORD': 'votre_password_local',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Mode debug (garder True pour local)
DEBUG = True

# Hosts autorisés
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# URLs de base
BASE_URL = 'http://127.0.0.1:8000'
```

### 📦 Dependencies

Après migration, installez les nouveaux requirements :
```bash
pip install -r requirements.txt
```

## 🧪 Tests Post-Migration

1. **Démarrage serveur** :
   ```bash
   python3 manage.py runserver
   ```

2. **Tests authentification** :
   - Connexion admin : `bguinziemba` / `mot_de_passe_prod`
   - Inscription nouvel utilisateur
   - Processus onboarding complet

3. **Vérification données** :
   ```bash
   python3 check_system_status.py
   ```

## 🔙 Restauration en Cas de Problème

Si la migration pose problème :

```bash
./restore_dev_backup.sh
```

Cela restaurera :
- ✅ Configuration précédente
- ✅ Données précédentes  
- ✅ État fonctionnel

## 📞 Support

En cas de problème :

1. **Vérifiez les logs** :
   ```bash
   python3 manage.py runserver
   # Consultez les erreurs dans la console
   ```

2. **Consultez les sauvegardes** :
   - `backup_dev_20250630_211015/` - État développement
   - `production_manual_*/` - Données production

3. **Restaurez si nécessaire** :
   ```bash
   ./restore_dev_backup.sh
   ```

## 🎯 Résultat Attendu

Après migration réussie :
- ✅ Authentification/enregistrement stable
- ✅ Configuration production éprouvée
- ✅ Données réelles de production
- ✅ Système d'onboarding fonctionnel
- ✅ Possibilité de restauration

---

## 🚀 Commandes de Démarrage

### Migration SSH :
```bash
./migrate_production_to_local.sh
```

### Migration Manuelle :
```bash
cat production_manual_20250630_211751/INSTRUCTIONS_MIGRATION.md
```

### Vérification :
```bash
python3 check_system_status.py
```

### Restauration :
```bash
./restore_dev_backup.sh
```