#!/bin/bash
# Script complet pour redémarrer Gunicorn en production avec la configuration corrigée (PYTHONPATH)

PRODUCTION_SERVER="martialcomp-production"
PRODUCTION_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

echo "🔄 REDÉMARRAGE DE GUNICORN EN PRODUCTION"
echo "=========================================="
echo ""

# Fonction pour exécuter sur le serveur de production
restart_on_server() {
    echo "📡 Connexion au serveur de production..."
    
    ssh "$PRODUCTION_SERVER" << 'EOF'
        set -e
        
        PRODUCTION_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
        cd "$PRODUCTION_PATH"
        
        echo "🛑 Arrêt des processus Gunicorn existants..."
        pkill -f gunicorn || true
        sleep 3
        
        # Vérifier qu'aucun processus ne reste
        if pgrep -f gunicorn > /dev/null; then
            echo "⚠️  Forçage de l'arrêt des processus restants..."
            pkill -9 -f gunicorn
            sleep 2
        fi
        
        echo "✅ Tous les processus Gunicorn ont été arrêtés"
        
        # Vérifier que le fichier de configuration existe
        if [ ! -f "$PRODUCTION_PATH/gunicorn.conf.py" ]; then
            echo "❌ Erreur: gunicorn.conf.py introuvable"
            exit 1
        fi
        
        echo "🚀 Démarrage de Gunicorn avec la configuration complète..."
        
        # Démarrer Gunicorn avec le fichier de configuration qui inclut PYTHONPATH
        sudo -u www-data .venv/bin/gunicorn \
            -c gunicorn.conf.py \
            config.wsgi:application \
            --daemon
        
        if [ $? -eq 0 ]; then
            echo "✅ Gunicorn démarré avec succès"
        else
            echo "❌ Erreur lors du démarrage de Gunicorn"
            exit 1
        fi
        
        # Attendre que Gunicorn démarre
        echo "⏳ Attente du démarrage complet (5 secondes)..."
        sleep 5
        
        # Vérifier que Gunicorn fonctionne
        echo "🔍 Vérification du fonctionnement..."
        
        # Vérifier les processus
        PROCESS_COUNT=$(pgrep -f gunicorn | wc -l)
        if [ "$PROCESS_COUNT" -gt 0 ]; then
            echo "✅ Processus Gunicorn actifs: $PROCESS_COUNT"
        else
            echo "❌ Aucun processus Gunicorn trouvé"
            exit 1
        fi
        
        # Vérifier le port
        if netstat -tlnp 2>/dev/null | grep -q ":8002" || ss -tlnp 2>/dev/null | grep -q ":8002"; then
            echo "✅ Port 8002 est en écoute"
        else
            echo "⚠️  Port 8002 non détecté (peut prendre quelques secondes)"
        fi
        
        echo ""
        echo "📊 État des processus Gunicorn:"
        ps aux | grep gunicorn | grep -v grep | head -5
        
        echo ""
        echo "✅ REDÉMARRAGE TERMINÉ AVEC SUCCÈS!"
        echo "🌐 Gunicorn est accessible sur http://127.0.0.1:8002"
EOF

    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Redémarrage réussi!"
        return 0
    else
        echo ""
        echo "❌ Erreur lors du redémarrage"
        return 1
    fi
}

# Vérifier si on est directement sur le serveur de production
if [ -d "$PRODUCTION_PATH" ]; then
    echo "📍 Exécution locale sur le serveur de production..."
    PRODUCTION_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
    cd "$PRODUCTION_PATH"
    
    echo "🛑 Arrêt des processus Gunicorn existants..."
    pkill -f gunicorn || true
    sleep 3
    
    # Vérifier qu'aucun processus ne reste
    if pgrep -f gunicorn > /dev/null; then
        echo "⚠️  Forçage de l'arrêt des processus restants..."
        pkill -9 -f gunicorn
        sleep 2
    fi
    
    echo "✅ Tous les processus Gunicorn ont été arrêtés"
    
    # Vérifier que le fichier de configuration existe
    if [ ! -f "$PRODUCTION_PATH/gunicorn.conf.py" ]; then
        echo "❌ Erreur: gunicorn.conf.py introuvable"
        exit 1
    fi
    
    echo "🚀 Démarrage de Gunicorn avec la configuration complète..."
    
    # Démarrer Gunicorn avec le fichier de configuration qui inclut PYTHONPATH
    sudo -u www-data .venv/bin/gunicorn \
        -c gunicorn.conf.py \
        config.wsgi:application \
        --daemon
    
    if [ $? -eq 0 ]; then
        echo "✅ Gunicorn démarré avec succès"
    else
        echo "❌ Erreur lors du démarrage de Gunicorn"
        exit 1
    fi
    
    # Attendre que Gunicorn démarre
    echo "⏳ Attente du démarrage complet (5 secondes)..."
    sleep 5
    
    # Vérifier que Gunicorn fonctionne
    echo "🔍 Vérification du fonctionnement..."
    
    # Vérifier les processus
    PROCESS_COUNT=$(pgrep -f gunicorn | wc -l)
    if [ "$PROCESS_COUNT" -gt 0 ]; then
        echo "✅ Processus Gunicorn actifs: $PROCESS_COUNT"
    else
        echo "❌ Aucun processus Gunicorn trouvé"
        exit 1
    fi
    
    # Vérifier le port
    if netstat -tlnp 2>/dev/null | grep -q ":8002" || ss -tlnp 2>/dev/null | grep -q ":8002"; then
        echo "✅ Port 8002 est en écoute"
    else
        echo "⚠️  Port 8002 non détecté (peut prendre quelques secondes)"
    fi
    
    echo ""
    echo "📊 État des processus Gunicorn:"
    ps aux | grep gunicorn | grep -v grep | head -5
    
    echo ""
    echo "✅ REDÉMARRAGE TERMINÉ AVEC SUCCÈS!"
    echo "🌐 Gunicorn est accessible sur http://127.0.0.1:8002"
    
else
    # Exécuter via SSH
    restart_on_server
fi

echo ""
echo "💡 Pour vérifier que tout fonctionne correctement, exécutez:"
echo "   python3 scripts/verify_gunicorn_production.py"
