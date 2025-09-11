#!/bin/bash

# Script de test rapide pour ports alternatifs sur Ionos
# Test depuis le serveur local pour vérifier accessibilité

echo "=== Test Ports Alternatifs MartialComp ==="

PROJECT_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
LOG_DIR="/var/www/vhosts/martialcomp.com/logs"

# Test si Django peut démarrer sur différents ports
test_django_ports() {
    echo "1. Test des ports disponibles..."
    
    cd $PROJECT_DIR
    source venv/bin/activate
    
    for PORT in 8080 8081 8082 3000 9000; do
        echo "Test port $PORT..."
        
        # Arrêter processus existants sur ce port
        fuser -k $PORT/tcp 2>/dev/null || true
        sleep 2
        
        # Tenter démarrage Django
        timeout 10 python manage.py runserver 0.0.0.0:$PORT > $LOG_DIR/test_port_$PORT.log 2>&1 &
        PID=$!
        
        sleep 5
        
        # Test connectivité
        if curl -s http://localhost:$PORT/ > /dev/null; then
            echo "✅ Port $PORT - Django fonctionne"
            kill $PID 2>/dev/null || true
        else
            echo "❌ Port $PORT - Échec"
            if [ -f $LOG_DIR/test_port_$PORT.log ]; then
                echo "   Erreur: $(tail -1 $LOG_DIR/test_port_$PORT.log)"
            fi
        fi
    done
}

# Test connectivité externe (depuis autre machine)
test_external_connectivity() {
    echo ""
    echo "2. Test connectivité externe..."
    echo "À exécuter depuis votre machine locale:"
    echo ""
    
    for PORT in 8080 8081 8082; do
        echo "curl -I http://martialcomp.com:$PORT/"
    done
    
    echo ""
    echo "Si ces commandes échouent, le port n'est pas accessible depuis l'extérieur"
}

# Démarrage Django sur le meilleur port disponible
start_best_port() {
    echo ""
    echo "3. Démarrage sur le meilleur port..."
    
    cd $PROJECT_DIR
    source venv/bin/activate
    
    # Essayer port 8080 en premier
    if ! netstat -tlnp | grep :8080 > /dev/null; then
        echo "Démarrage Django sur port 8080..."
        nohup python manage.py runserver 0.0.0.0:8080 > $LOG_DIR/django_8080.log 2>&1 &
        
        sleep 5
        
        if curl -s http://localhost:8080/ > /dev/null; then
            echo "✅ Django démarré avec succès sur port 8080"
            echo "🌐 URL: http://martialcomp.com:8080"
            echo "📋 PID: $(pgrep -f 'runserver 0.0.0.0:8080')"
            echo "📄 Logs: $LOG_DIR/django_8080.log"
            
            # Afficher les premières lignes du log
            echo ""
            echo "Premières lignes du log:"
            head -10 $LOG_DIR/django_8080.log
        else
            echo "❌ Échec démarrage sur port 8080"
            echo "Log d'erreur:"
            cat $LOG_DIR/django_8080.log
        fi
    else
        echo "Port 8080 déjà utilisé"
    fi
}

# Information système
show_system_info() {
    echo ""
    echo "4. Informations système..."
    echo "Processus Django actifs:"
    ps aux | grep manage.py | grep -v grep
    
    echo ""
    echo "Ports en écoute:"
    netstat -tlnp | grep -E ":(80|8080|8081|8082|3000|9000)"
    
    echo ""
    echo "Espace disque:"
    df -h /var/www/vhosts/martialcomp.com/
}

# Instructions pour Plesk
show_plesk_instructions() {
    echo ""
    echo "5. Configuration dans Plesk..."
    echo ""
    echo "OPTION A - Redirection de port:"
    echo "1. Aller dans Plesk -> Domaines -> martialcomp.com -> Redirection"
    echo "2. Type: Port personnalisé"
    echo "3. Port source: 80, Port destination: 8080"
    echo ""
    echo "OPTION B - Proxy pass:"
    echo "1. Aller dans Plesk -> Domaines -> martialcomp.com -> Configuration supplémentaire"
    echo "2. Directives Nginx/Apache"
    echo "3. Ajouter: proxy_pass http://127.0.0.1:8080;"
    echo ""
    echo "OPTION C - Sous-domaine:"
    echo "1. Créer sous-domaine: app.martialcomp.com"
    echo "2. Pointer vers port 8080"
    echo "3. URL finale: http://app.martialcomp.com:8080"
}

# Exécution principale
main() {
    # Créer répertoire logs
    mkdir -p $LOG_DIR
    chown -R www-data:www-data $LOG_DIR
    
    # Tests
    test_django_ports
    test_external_connectivity
    start_best_port
    show_system_info
    show_plesk_instructions
    
    echo ""
    echo "=== Test terminé ==="
    echo "Django devrait être accessible sur: http://martialcomp.com:8080"
}

# Lancer le script
main 