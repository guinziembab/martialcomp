#!/bin/bash
# Script pour analyser la structure du serveur de production

echo "================================================"
echo "🔍 ANALYSE DE LA STRUCTURE DU SERVEUR PRODUCTION"
echo "================================================"
echo ""
echo "Date: $(date)"
echo ""

# 1. Identifier l'utilisateur actuel
echo "1️⃣ UTILISATEUR ET ENVIRONNEMENT"
echo "================================"
echo "Utilisateur actuel: $(whoami)"
echo "Répertoire home: $HOME"
echo "Répertoire actuel: $(pwd)"
echo ""

# 2. Chercher le répertoire du projet
echo "2️⃣ RECHERCHE DU PROJET MARTIALCOMP"
echo "==================================="

# Chercher dans les emplacements courants
POSSIBLE_PATHS=(
    "/home/martialcomp"
    "/var/www/martialcomp"
    "/var/www/vhosts/martialcomp.com"
    "/var/www/vhosts/martialcomp.com/httpdocs"
    "/opt/martialcomp"
    "/srv/martialcomp"
    "$HOME/martialcomp"
    "$HOME/httpdocs"
    "$HOME/public_html"
    "$HOME/www"
)

PROJECT_DIR=""
for path in "${POSSIBLE_PATHS[@]}"; do
    if [ -d "$path" ]; then
        echo "✅ Trouvé: $path"
        # Vérifier si c'est le projet Django
        if [ -f "$path/manage.py" ]; then
            echo "   ✅ manage.py trouvé - C'est le projet Django!"
            PROJECT_DIR="$path"
            break
        elif [ -f "$path/httpdocs/manage.py" ]; then
            echo "   ✅ manage.py trouvé dans httpdocs"
            PROJECT_DIR="$path/httpdocs"
            break
        fi
    fi
done

if [ -z "$PROJECT_DIR" ]; then
    echo "❌ Projet Django non trouvé dans les emplacements standards"
    echo ""
    echo "Recherche étendue..."
    find / -name "manage.py" -type f 2>/dev/null | grep -E "(martialcomp|martial)" | head -5
fi

echo ""

# 3. Analyser la structure du projet
if [ ! -z "$PROJECT_DIR" ]; then
    echo "3️⃣ STRUCTURE DU PROJET"
    echo "======================"
    echo "Répertoire du projet: $PROJECT_DIR"
    echo ""
    
    cd "$PROJECT_DIR"
    
    echo "📁 Contenu du répertoire principal:"
    ls -la | head -10
    echo ""
    
    echo "📁 Structure apps/competitions:"
    if [ -d "apps/competitions" ]; then
        echo "✅ apps/competitions existe"
        ls -la apps/competitions/forms/ 2>/dev/null | grep onboarding
        ls -la apps/competitions/views/onboarding/ 2>/dev/null | head -5
    else
        echo "❌ apps/competitions non trouvé"
    fi
    echo ""
fi

# 4. Vérifier les permissions
echo "4️⃣ PERMISSIONS ET PROPRIÉTAIRE"
echo "=============================="
if [ ! -z "$PROJECT_DIR" ]; then
    echo "Propriétaire du projet:"
    ls -ld "$PROJECT_DIR" | awk '{print $3":"$4}'
    echo ""
    echo "Permissions sur manage.py:"
    ls -la "$PROJECT_DIR/manage.py" 2>/dev/null
fi
echo ""

# 5. Chercher les répertoires de backup
echo "5️⃣ RÉPERTOIRES DE BACKUP"
echo "========================"
BACKUP_DIRS=(
    "/home/backups"
    "/var/backups"
    "$HOME/backups"
    "/backup"
    "/opt/backup"
)

for dir in "${BACKUP_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "✅ Trouvé: $dir"
    fi
done
echo ""

# 6. Configuration du serveur web
echo "6️⃣ CONFIGURATION SERVEUR WEB"
echo "============================"

# Apache
if command -v apache2 &> /dev/null; then
    echo "✅ Apache2 installé"
    # Chercher les sites activés
    if [ -d "/etc/apache2/sites-enabled" ]; then
        echo "Sites Apache activés:"
        ls -la /etc/apache2/sites-enabled/ | grep -v "total"
    fi
fi

# Nginx
if command -v nginx &> /dev/null; then
    echo "✅ Nginx installé"
    if [ -d "/etc/nginx/sites-enabled" ]; then
        echo "Sites Nginx activés:"
        ls -la /etc/nginx/sites-enabled/ | grep -v "total"
    fi
fi

# Passenger
if [ -f "$PROJECT_DIR/passenger_wsgi.py" ] || [ -f "$PROJECT_DIR/tmp/restart.txt" ]; then
    echo "✅ Passenger détecté"
fi

echo ""

# 7. Python et Django
echo "7️⃣ ENVIRONNEMENT PYTHON"
echo "======================="
echo "Python version: $(python3 --version 2>&1)"
echo "Pip version: $(pip3 --version 2>&1 | head -1)"

# Chercher les environnements virtuels
echo ""
echo "Environnements virtuels potentiels:"
find "$PROJECT_DIR" -maxdepth 2 -name "venv" -o -name "env" -o -name ".venv" -o -name "virtualenv" 2>/dev/null | head -5

echo ""

# 8. Résumé
echo "8️⃣ RÉSUMÉ"
echo "========="
if [ ! -z "$PROJECT_DIR" ]; then
    echo "✅ Projet trouvé: $PROJECT_DIR"
    echo "✅ Pour y accéder: cd $PROJECT_DIR"
else
    echo "❌ Projet non trouvé automatiquement"
    echo "➡️  Cherchez manuellement avec: find / -name 'manage.py' 2>/dev/null"
fi

echo ""
echo "================================================"
echo "✅ ANALYSE TERMINÉE"
echo "================================================"