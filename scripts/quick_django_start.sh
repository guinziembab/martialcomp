#!/bin/bash

# Script de démarrage rapide Django après récupération SSH
echo "🚀 DÉMARRAGE RAPIDE DJANGO POST-RÉCUPÉRATION"
echo "============================================"

# Se connecter et démarrer Django
ssh root@martialcomp.com << 'EOF'

echo "📋 DIAGNOSTIC RAPIDE"
echo "===================="

# Vérifier processus Django
echo "🔍 Processus Django existants:"
ps aux | grep manage.py || echo "Aucun processus Django"

# Vérifier port 8000
echo "🔍 Port 8000:"
netstat -tlnp | grep :8000 || echo "Port 8000 libre"

# Aller dans le répertoire
cd /var/www/vhosts/martialcomp.com/httpdocs

echo ""
echo "🚀 DÉMARRAGE DJANGO"
echo "==================="

# Nettoyer processus existants
pkill -f manage.py 2>/dev/null || echo "Aucun processus à tuer"

# Activer environnement
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings

# Vérifier Django
echo "🧪 Django check:"
python3 manage.py check

if [ $? -eq 0 ]; then
    echo "✅ Django check réussi"
    
    # Démarrer serveur Django en arrière-plan
    echo "🔄 Démarrage serveur Django..."
    nohup python3 manage.py runserver 0.0.0.0:8000 > /tmp/django_recovery.log 2>&1 &
    
    # Attendre démarrage
    sleep 8
    
    # Vérifier processus
    if ps aux | grep -q "[m]anage.py runserver"; then
        echo "✅ Serveur Django démarré"
        
        # Test local
        echo "🧪 Test local:"
        curl -I http://localhost:8000/ 2>/dev/null | head -1 || echo "❌ Pas de réponse locale"
        
        # Test URLs i18n
        echo "🌐 Test URLs i18n:"
        curl -I http://localhost:8000/fr/ 2>/dev/null | head -1 || echo "❌ URL française non accessible"
        curl -I http://localhost:8000/en/ 2>/dev/null | head -1 || echo "❌ URL anglaise non accessible"
        
    else
        echo "❌ Échec démarrage serveur"
        echo "📋 Logs:"
        cat /tmp/django_recovery.log 2>/dev/null || echo "Pas de logs"
    fi
    
else
    echo "❌ Django check échoué"
fi

echo ""
echo "🔍 STATUT FINAL:"
echo "================"
ps aux | grep manage.py || echo "Aucun processus Django"
netstat -tlnp | grep :8000 || echo "Port 8000 non utilisé"

EOF

echo ""
echo "🌐 TEST URLS PUBLIQUES"
echo "======================"

echo "🔍 Test principal:"
curl -I https://martialcomp.com/ 2>/dev/null | head -1

echo "🔍 Test français:"
curl -I https://martialcomp.com/fr/ 2>/dev/null | head -1

echo "🔍 Test anglais:"
curl -I https://martialcomp.com/en/ 2>/dev/null | head -1

echo ""
echo "📊 RÉSUMÉ"
echo "========="
echo "Si toutes les URLs retournent HTTP 200:"
echo "🎉 SUCCESS - Configuration i18n opérationnelle"
echo ""
echo "Si 502 persiste:"
echo "🔧 Django ne démarre pas - vérifier les logs"
echo ""
echo "🧪 DÉMO DISPONIBLE:"
echo "👤 dojo_sakura_manager / demo2025"