#!/bin/bash

# Script d'urgence - Démarrage immédiat MartialComp sur port 8080
# Pour Ionos - Port 80 non disponible

echo "🚨 DÉMARRAGE D'URGENCE MARTIALCOMP - PORT 8080"
echo "=============================================="

# Répertoires
PROJECT_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
LOG_DIR="/var/www/vhosts/martialcomp.com/logs"

# Créer les logs
mkdir -p "$LOG_DIR"
chown -R www-data:www-data "$LOG_DIR" 2>/dev/null || true

# Aller dans le projet
cd "$PROJECT_DIR"

echo "📁 Répertoire: $(pwd)"

# Vérifier l'environnement virtuel
if [ ! -f "venv/bin/activate" ]; then
    echo "❌ Environnement virtuel introuvable dans: $PROJECT_DIR/venv/"
    echo "Recherche alternative..."
    
    if [ -f "../venv/bin/activate" ]; then
        echo "✅ Trouvé dans ../venv/"
        source ../venv/bin/activate
    elif [ -f ".venv/bin/activate" ]; then
        echo "✅ Trouvé dans .venv/"
        source .venv/bin/activate
    else
        echo "❌ Aucun environnement virtuel trouvé"
        echo "Tentative sans environnement virtuel..."
    fi
else
    echo "✅ Activation environnement virtuel"
    source venv/bin/activate
fi

# Vérifier Python et Django
echo "🐍 Version Python: $(python --version)"
echo "🔧 Test Django:"
python -c "import django; print(f'Django {django.get_version()}')" || echo "❌ Django non accessible"

# Arrêter les processus existants
echo "🛑 Arrêt des processus Django existants..."
pkill -f "manage.py runserver" 2>/dev/null || true
pkill -f "gunicorn" 2>/dev/null || true
fuser -k 8080/tcp 2>/dev/null || true

sleep 3

# Vérifier que le port est libre
if netstat -tlnp | grep :8080 >/dev/null 2>&1; then
    echo "⚠️  Port 8080 encore occupé, forçage..."
    fuser -k 8080/tcp 2>/dev/null || true
    sleep 2
fi

# Ouvrir le firewall pour le port 8080
echo "🔥 Ouverture firewall port 8080..."
iptables -I INPUT -p tcp --dport 8080 -j ACCEPT 2>/dev/null || echo "⚠️  Impossible d'ouvrir le firewall"

# Configuration Django minimale
export DJANGO_SETTINGS_MODULE=config.settings
export PYTHONPATH="$PROJECT_DIR"

# Test rapide de la configuration
echo "⚙️  Test configuration Django..."
python manage.py check --deploy 2>/dev/null || echo "⚠️  Problème de configuration détecté"

# Collecte des fichiers statiques rapide
echo "📦 Collecte fichiers statiques..."
python manage.py collectstatic --noinput --clear 2>/dev/null || echo "⚠️  Échec collectstatic"

# Démarrage Django sur port 8080
echo "🚀 DÉMARRAGE DJANGO SUR PORT 8080..."
echo "Logs: $LOG_DIR/emergency_8080.log"

nohup python manage.py runserver 0.0.0.0:8080 > "$LOG_DIR/emergency_8080.log" 2>&1 &
DJANGO_PID=$!

echo "🔄 PID Django: $DJANGO_PID"

# Attendre le démarrage
echo "⏳ Attente démarrage (10 secondes)..."
sleep 10

# Vérifier que Django fonctionne
if ps -p $DJANGO_PID > /dev/null 2>&1; then
    echo "✅ Django démarré avec succès!"
    
    # Test de connectivité locale
    if curl -s http://localhost:8080/ > /dev/null 2>&1; then
        echo "✅ Django répond localement"
    else
        echo "⚠️  Django ne répond pas localement"
    fi
    
    # Afficher les informations d'accès
    echo ""
    echo "🌐 ACCÈS À L'APPLICATION:"
    echo "========================================="
    echo "URL principale: http://martialcomp.com:8080"
    echo "URL locale: http://localhost:8080"
    echo "IP directe: http://212.227.78.104:8080"
    echo ""
    echo "📊 INFORMATIONS SYSTÈME:"
    echo "PID: $DJANGO_PID"
    echo "Port: 8080"
    echo "Logs: $LOG_DIR/emergency_8080.log"
    echo ""
    echo "🔍 COMMANDES DE CONTRÔLE:"
    echo "Arrêter: kill $DJANGO_PID"
    echo "Statut: ps -p $DJANGO_PID"
    echo "Logs: tail -f $LOG_DIR/emergency_8080.log"
    echo ""
    
    # Test depuis l'extérieur (à faire manuellement)
    echo "🌍 TEST EXTERNE (à exécuter depuis votre machine):"
    echo "curl -I http://martialcomp.com:8080/"
    echo ""
    
else
    echo "❌ Échec démarrage Django"
    echo "Logs d'erreur:"
    cat "$LOG_DIR/emergency_8080.log" 2>/dev/null || echo "Pas de logs disponibles"
    exit 1
fi

# Afficher les processus Django actifs
echo "📋 PROCESSUS DJANGO ACTIFS:"
ps aux | grep -E "(manage\.py|django)" | grep -v grep

echo ""
echo "✅ DÉMARRAGE D'URGENCE TERMINÉ AVEC SUCCÈS!"
echo "L'application devrait être accessible via: http://martialcomp.com:8080" 