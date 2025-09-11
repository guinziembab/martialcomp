# 🌍 MIGRATION MULTILINGUE MARTIALCOMP

## 📦 Contenu du Package

Ce package contient tous les éléments nécessaires pour migrer le système multilingue de MartialComp vers la production.

### 🎯 Fonctionnalités Incluses

- ✅ **16 langues supportées**
- ✅ **Page d'accueil redesignée** avec sélecteur de langue
- ✅ **Interface Rosetta** pour gérer les traductions
- ✅ **Configuration Django i18n complète**
- ✅ **Scripts d'automatisation**

### 📁 Structure du Package

```
migration_package/
├── config/                 # Fichiers de configuration
│   ├── settings_patch.py   # Modifications pour settings.py
│   ├── urls_patch.py       # Modifications pour urls.py
│   └── requirements_multilingual.txt
├── locale/                 # Fichiers de traduction (16 langues)
│   ├── fr/LC_MESSAGES/
│   ├── en/LC_MESSAGES/
│   └── ... (14 autres langues)
├── templates/              # Templates modifiés
│   └── welcome.html        # Page d'accueil redesignée
├── scripts/                # Scripts d'automatisation
│   ├── backup.sh          # Backup avant migration
│   ├── deploy.sh          # Déploiement automatique
│   ├── test.sh            # Tests post-déploiement
│   └── compile_translations.py
└── docs/                   # Documentation
    └── README.md          # Ce fichier
```

## 🚀 Procédure de Migration (Étape par Étape)

### 1. 💾 BACKUP (OBLIGATOIRE)

```bash
# Exécuter le script de backup
chmod +x scripts/backup.sh
./scripts/backup.sh
```

### 2. 📦 INSTALLATION

```bash
# Installer les packages requis
pip install -r config/requirements_multilingual.txt
```

### 3. ⚙️ CONFIGURATION

#### A. Modifier settings.py
Ajoutez le contenu de `config/settings_patch.py` à votre `settings.py` de production.

#### B. Modifier urls.py
Ajoutez le contenu de `config/urls_patch.py` à votre `urls.py` principal.

### 4. 📂 COPIE DES FICHIERS

```bash
# Copier les fichiers de traduction
cp -r locale/ /path/to/your/project/

# Copier le template redesigné
cp templates/welcome.html /path/to/your/project/competitions/templates/competitions/

# Copier les scripts utilitaires
cp scripts/compile_translations.py /path/to/your/project/
```

### 5. 🗄️ MIGRATIONS

```bash
# Appliquer les migrations modeltranslation
python manage.py makemigrations
python manage.py migrate
```

### 6. 🌍 COMPILATION DES TRADUCTIONS

```bash
# Compiler les traductions
python manage.py compilemessages

# OU utiliser le script personnalisé
python compile_translations.py
```

### 7. 📦 FICHIERS STATIQUES

```bash
# Collecter les fichiers statiques
python manage.py collectstatic --noinput
```

### 8. 🔄 REDÉMARRAGE

```bash
# Redémarrer le serveur (selon votre setup)
sudo systemctl restart your-app
# OU
sudo supervisorctl restart your-app
# OU
pkill -f "python.*manage.py.*runserver"
python manage.py runserver
```

### 9. 🧪 TESTS

```bash
# Exécuter les tests automatiques
chmod +x scripts/test.sh
./scripts/test.sh
```

## 🔍 Vérifications Post-Migration

### URLs à Tester

- ✅ **Page d'accueil** : `https://your-domain.com/`
- ✅ **Admin** : `https://your-domain.com/admin/`
- ✅ **Admin avec langue** : `https://your-domain.com/fr/admin/`
- ✅ **Rosetta** : `https://your-domain.com/rosetta/`
- ✅ **Sélecteur de langue** : `https://your-domain.com/set-language/`

### Vérifications Manuelles

1. **Connexion Admin** : Connectez-vous à l'administration
2. **Interface Rosetta** : Accédez à `/rosetta/` (authentification requise)
3. **Sélecteur de langue** : Testez le changement de langue sur la page d'accueil
4. **Responsive design** : Vérifiez l'affichage mobile
5. **Performance** : Vérifiez que les temps de réponse sont normaux

## 🚨 Rollback (En Cas de Problème)

Si la migration pose des problèmes :

```bash
# 1. Arrêter le serveur
sudo systemctl stop your-app

# 2. Restaurer le backup
BACKUP_DIR="backup_YYYYMMDD_HHMMSS"  # Remplacer par votre backup
cp -r "../$BACKUP_DIR/project/" .

# 3. Restaurer la base de données (si nécessaire)
cp "../$BACKUP_DIR/db.sqlite3" .

# 4. Redémarrer
sudo systemctl start your-app
```

## 📞 Support et Dépannage

### Problèmes Courants

1. **Erreur 500** : Vérifiez les logs Django
2. **Traductions non visibles** : Vérifiez que `compilemessages` a été exécuté
3. **URLs en 404** : Vérifiez la configuration `i18n_patterns`
4. **Rosetta inaccessible** : Vérifiez que l'utilisateur est admin

### Logs à Consulter

```bash
# Logs Django (selon votre setup)
tail -f /path/to/your/logs/django.log

# Logs du serveur web
tail -f /var/log/nginx/error.log  # Nginx
tail -f /var/log/apache2/error.log  # Apache
```

## 🎉 Félicitations !

Une fois la migration terminée, vous disposez d'un système multilingue complet avec :

- 🌍 **16 langues** supportées
- 🎨 **Design moderne** et responsive
- 🔧 **Interface de gestion** des traductions
- 📊 **Dashboard** de statistiques
- 🚀 **Performance optimisée**

Votre instance MartialComp est maintenant prête pour une audience internationale ! 🌏
