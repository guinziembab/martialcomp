# 📝 Création du Script de Correction Directement en Production

## 🔧 Étapes à suivre sur le serveur

### **1. Connexion au serveur**
```bash
ssh root@martialcomp.com
```

### **2. Créer le script avec vi**
```bash
cd /root
vi fix-database-quick.sh
```

### **3. Dans vi, appuyez sur `i` pour entrer en mode insertion, puis copiez-collez le contenu suivant :**

```bash
#!/bin/bash
# Correction rapide du problème de base de données PostgreSQL

echo "=== CORRECTION RAPIDE DE LA BASE DE DONNÉES ==="

# 1. Vérifier PostgreSQL
echo "🔍 Vérification de PostgreSQL..."
systemctl status postgresql --no-pager -l

# 2. Recréer l'utilisateur PostgreSQL
echo "👤 Recréation de l'utilisateur PostgreSQL..."
sudo -u postgres psql << 'EOF'
-- Supprimer l'utilisateur s'il existe
DROP USER IF EXISTS martialcomp_user;

-- Créer l'utilisateur avec le bon mot de passe
CREATE USER martialcomp_user WITH PASSWORD 'MartialComp2025Production!';

-- Créer la base de données
DROP DATABASE IF EXISTS martialcomp_db;
CREATE DATABASE martialcomp_db OWNER martialcomp_user;

-- Privilèges
GRANT ALL PRIVILEGES ON DATABASE martialcomp_db TO martialcomp_user;
ALTER USER martialcomp_user CREATEDB;

-- Vérifier
\du martialcomp_user
\l martialcomp_db
EOF

# 3. Tester la connexion
echo "🧪 Test de connexion..."
PGPASSWORD="MartialComp2025Production!" psql -h localhost -U martialcomp_user -d martialcomp_db -c "SELECT version();"

if [ $? -eq 0 ]; then
    echo "✅ Connexion à la base de données réussie!"
else
    echo "❌ Échec de la connexion à la base de données"
    exit 1
fi

# 4. Créer/corriger le fichier .env
echo "📝 Création du fichier .env..."
cd /var/www/vhosts/martialcomp.com/httpdocs

cat > .env << 'EOF'
DEBUG=False
SECRET_KEY=django-martialcomp-production-secret-key-very-long-and-secure-2025-with-more-than-50-characters
ALLOWED_HOSTS=martialcomp.com,www.martialcomp.com,212.227.78.104,127.0.0.1,localhost

# Base de données PostgreSQL
POSTGRES_DB=martialcomp_db
POSTGRES_USER=martialcomp_user
POSTGRES_PASSWORD=MartialComp2025Production!
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Configuration de sécurité (temporairement désactivée pour HTTP)
CSRF_COOKIE_SECURE=False
SESSION_COOKIE_SECURE=False
SECURE_BROWSER_XSS_FILTER=True
SECURE_CONTENT_TYPE_NOSNIFF=True

# Configuration email
EMAIL_HOST_USER=noreply@martialcomp.com
EMAIL_HOST_PASSWORD=your_email_password
DEFAULT_FROM_EMAIL=noreply@martialcomp.com
EOF

echo "✅ Fichier .env créé"

# 5. Test Django
echo "🧪 Test de la configuration Django..."
cd /var/www/vhosts/martialcomp.com/httpdocs
source .venv/bin/activate

# Installer python-decouple si nécessaire
pip install python-decouple

# Tester la configuration
python manage.py check --settings=config.settings.production

if [ $? -eq 0 ]; then
    echo "✅ Configuration Django OK"
else
    echo "❌ Problème avec la configuration Django"
    exit 1
fi

# 6. Appliquer les migrations
echo "🔄 Application des migrations..."
python manage.py migrate --settings=config.settings.production

if [ $? -eq 0 ]; then
    echo "✅ Migrations appliquées avec succès"
else
    echo "❌ Problème avec les migrations"
    exit 1
fi

# 7. Collecter les fichiers statiques
echo "📦 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput --settings=config.settings.production

echo ""
echo "✅ CORRECTION TERMINÉE AVEC SUCCÈS!"
echo "📝 Vous pouvez maintenant tester:"
echo "   python manage.py runserver 127.0.0.1:8001 --settings=config.settings.production"
```

### **4. Sauvegarder et quitter vi**
- Appuyez sur `Esc` pour sortir du mode insertion
- Tapez `:wq` puis `Enter` pour sauvegarder et quitter

### **5. Rendre le script exécutable**
```bash
chmod +x /root/fix-database-quick.sh
```

### **6. Vérifier que le script est créé**
```bash
ls -la /root/fix-database-quick.sh
```

### **7. Exécuter le script**
```bash
/root/fix-database-quick.sh
```

## 🚀 Commandes complètes à exécuter une fois connecté

```bash
# Créer le script
vi /root/fix-database-quick.sh

# Après avoir collé le contenu et sauvegardé :
chmod +x /root/fix-database-quick.sh

# Exécuter la correction
/root/fix-database-quick.sh
```

## 📋 Aide-mémoire vi

- `i` : Entrer en mode insertion
- `Esc` : Sortir du mode insertion
- `:wq` : Sauvegarder et quitter
- `:q!` : Quitter sans sauvegarder (si erreur)

Le script va corriger automatiquement :
- La configuration PostgreSQL
- Le fichier .env avec les bonnes variables
- Les migrations Django
- Les fichiers statiques