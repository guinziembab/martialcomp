#!/bin/bash

# Script d'installation d'urgence pour le serveur de production

echo "=== INSTALLATION D'URGENCE - Configuration Production ==="
echo ""

cd /var/www/vhosts/martialcomp.com/httpdocs

# 1. Créer le fichier .env.production s'il n'existe pas
echo "1. Création du fichier .env.production..."
if [ ! -f ".env.production" ]; then
    cat > .env.production << 'EOF'
# ===========================================
# CONFIGURATION DE PRODUCTION MARTIALCOMP
# ===========================================

# SÉCURITÉ - CRITIQUE
DEBUG=False
SECRET_KEY=^Y=pM(pbcEJ(AMce3v^RuxlT1k3TG%*hX9IGoSV_&t5#1i!sZf
ALLOWED_HOSTS=martialcomp.com,www.martialcomp.com,212.227.78.104

# BASE DE DONNÉES POSTGRESQL
DB_ENGINE=django.db.backends.postgresql
DB_NAME=martialcomp_db
DB_USER=martialcomp_user
DB_PASSWORD=AQWZSX123ok,
DB_HOST=localhost
DB_PORT=5432

# CONFIGURATION MULTI-TENANT
DEFAULT_TENANT_DOMAIN=martialcomp.com
PUBLIC_DOMAINS=martialcomp.com,www.martialcomp.com
EOF
    chown www-data:www-data .env.production
    chmod 600 .env.production
    echo "✓ .env.production créé"
else
    echo "✓ .env.production existe déjà"
fi

# 2. Vérifier l'environnement virtuel Python
echo ""
echo "2. Recherche de l'environnement virtuel Python..."
VENV_PATHS=(
    "/var/www/vhosts/martialcomp.com/venv"
    "/var/www/vhosts/martialcomp.com/httpdocs/venv"
    "/home/*/venv"
    "/opt/venv"
    "/usr/local/venv"
)

VENV_FOUND=""
for path in "${VENV_PATHS[@]}"; do
    if [ -d "$path" ]; then
        VENV_FOUND="$path"
        echo "✓ Environnement virtuel trouvé : $VENV_FOUND"
        break
    fi
done

if [ -z "$VENV_FOUND" ]; then
    echo "⚠️  Aucun environnement virtuel trouvé"
    echo "Recherche de l'installation système de Django..."
    
    # Vérifier si Django est installé au niveau système
    if python3 -m pip show django >/dev/null 2>&1; then
        echo "✓ Django trouvé dans l'installation système"
    else
        echo "✗ Django n'est pas installé"
        echo ""
        echo "ATTENTION : Django doit être installé. Options :"
        echo "1. Créer un environnement virtuel :"
        echo "   python3 -m venv /var/www/vhosts/martialcomp.com/venv"
        echo "   source /var/www/vhosts/martialcomp.com/venv/bin/activate"
        echo "   pip install -r requirements.txt"
        echo ""
        echo "2. Ou installer Django au niveau système (non recommandé) :"
        echo "   apt-get update && apt-get install python3-django"
    fi
else
    # Activer l'environnement virtuel dans passenger_wsgi.py
    echo ""
    echo "3. Mise à jour de passenger_wsgi.py pour utiliser l'environnement virtuel..."
    
    # Sauvegarder l'ancien fichier
    cp passenger_wsgi.py passenger_wsgi.py.backup_$(date +%Y%m%d_%H%M%S)
    
    # Créer le nouveau passenger_wsgi.py
    cat > passenger_wsgi.py << EOF
import sys
import os

# Activer l'environnement virtuel
VENV_PATH = '$VENV_FOUND'
PYTHON_BIN = os.path.join(VENV_PATH, 'bin/python3')
if os.path.exists(PYTHON_BIN):
    # Activer l'environnement virtuel
    activate_env = os.path.join(VENV_PATH, 'bin/activate_this.py')
    if os.path.exists(activate_env):
        with open(activate_env) as f:
            code = compile(f.read(), activate_env, 'exec')
            exec(code, dict(__file__=activate_env))
    else:
        # Alternative si activate_this.py n'existe pas
        sys.path.insert(0, os.path.join(VENV_PATH, 'lib/python3.11/site-packages'))

# Ajouter le chemin du projet au path Python
sys.path.insert(0, '/var/www/vhosts/martialcomp.com/httpdocs')

# Charger manuellement les variables d'environnement depuis .env.production
env_path = '/var/www/vhosts/martialcomp.com/httpdocs/.env.production'
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# Définir explicitement le module de settings Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

# Importer l'application WSGI Django
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# CORRECTION DE L'ERREUR DISCIPLINE - IMPORT DU SCRIPT DE CORRECTION
try:
    import wsgi_startup_fix
    print("✅ Script de correction Discipline importé avec succès")
except Exception as e:
    print(f"⚠️ Erreur import script de correction: {e}")
EOF
    
    chown www-data:www-data passenger_wsgi.py
    chmod 644 passenger_wsgi.py
    echo "✓ passenger_wsgi.py mis à jour"
fi

# 4. Créer wsgi_startup_fix.py
echo ""
echo "4. Création de wsgi_startup_fix.py..."
cat > wsgi_startup_fix.py << 'EOF'
# Placeholder pour éviter l'erreur d'import
print("wsgi_startup_fix.py chargé")
EOF
chown www-data:www-data wsgi_startup_fix.py
chmod 644 wsgi_startup_fix.py

# 5. Vérifier requirements.txt
echo ""
echo "5. Vérification de requirements.txt..."
if [ -f "requirements.txt" ]; then
    echo "✓ requirements.txt trouvé"
    echo "Pour installer les dépendances :"
    if [ -n "$VENV_FOUND" ]; then
        echo "source $VENV_FOUND/bin/activate && pip install -r requirements.txt"
    else
        echo "python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    fi
else
    echo "⚠️  requirements.txt non trouvé"
fi

# 6. Redémarrer Apache
echo ""
echo "6. Redémarrage d'Apache..."
systemctl restart apache2

echo ""
echo "=== CONFIGURATION TERMINÉE ==="
echo ""
echo "PROCHAINES ÉTAPES IMPORTANTES :"
echo "1. Vérifier que Django est installé dans l'environnement virtuel"
echo "2. Exécuter les migrations : python3 manage.py migrate --settings=config.settings.production"
echo "3. Collecter les fichiers statiques : python3 manage.py collectstatic --settings=config.settings.production --noinput"
echo "4. Vérifier les logs : tail -f /var/log/apache2/error.log"