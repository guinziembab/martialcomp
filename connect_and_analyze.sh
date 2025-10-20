#!/bin/bash
# Script pour se connecter et analyser la structure

echo "🔍 Connexion au serveur de production pour analyse..."
echo ""

# Commandes à exécuter sur le serveur distant
ssh martialcomp-production << 'REMOTE_COMMANDS'
echo "================================================"
echo "🔍 ANALYSE DE LA STRUCTURE DU SERVEUR"
echo "================================================"
echo ""

# 1. Informations de base
echo "1️⃣ INFORMATIONS DE BASE"
echo "======================="
echo "Utilisateur: $(whoami)"
echo "Home: $HOME"
echo "PWD: $(pwd)"
echo "Hostname: $(hostname)"
echo ""

# 2. Recherche du projet
echo "2️⃣ RECHERCHE DU PROJET DJANGO"
echo "============================="

# Chercher manage.py
echo "Recherche de manage.py..."
find /home -name "manage.py" -type f 2>/dev/null | grep -v "permission denied" | head -5
find /var/www -name "manage.py" -type f 2>/dev/null | grep -v "permission denied" | head -5
find /opt -name "manage.py" -type f 2>/dev/null | grep -v "permission denied" | head -5

# Chercher des indices du projet
echo ""
echo "Recherche de répertoires martialcomp..."
find / -type d -name "*martial*" 2>/dev/null | grep -v "permission denied" | grep -v "/proc" | head -10

echo ""

# 3. Vérifier les répertoires home
echo "3️⃣ CONTENU DU RÉPERTOIRE HOME"
echo "============================="
ls -la ~/ | head -20

echo ""

# 4. Vérifier /var/www
echo "4️⃣ CONTENU DE /var/www"
echo "======================"
if [ -d "/var/www" ]; then
    ls -la /var/www/ | head -10
    if [ -d "/var/www/vhosts" ]; then
        echo ""
        echo "Contenu de /var/www/vhosts:"
        ls -la /var/www/vhosts/ | head -10
    fi
fi

echo ""

# 5. Processus Python/Django
echo "5️⃣ PROCESSUS PYTHON/DJANGO"
echo "========================="
ps aux | grep -E "python|django|gunicorn|passenger" | grep -v grep | head -5

echo ""
echo "================================================"
echo "✅ ANALYSE TERMINÉE"
echo "================================================"
REMOTE_COMMANDS