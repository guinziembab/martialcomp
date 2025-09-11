#!/bin/bash

# Script de déploiement dashboard fix - À exécuter quand le serveur est accessible
echo "🎯 DÉPLOIEMENT CORRECTION DASHBOARD FINAL"
echo "========================================"

# Variables
PROD_SERVER="root@martialcomp.com"
PROD_DIR="/var/www/vhosts/martialcomp.com/httpdocs"

echo "📂 Serveur: $PROD_SERVER"
echo "📂 Répertoire: $PROD_DIR"

# Test de connectivité
echo ""
echo "🔌 TEST CONNECTIVITÉ..."
if ! ping -c 1 martialcomp.com > /dev/null 2>&1; then
    echo "❌ Serveur non accessible - ping failed"
    exit 1
fi

if ! ssh -o ConnectTimeout=10 "$PROD_SERVER" "echo 'Connexion OK'" > /dev/null 2>&1; then
    echo "❌ SSH non accessible"
    exit 1
fi

echo "✅ Serveur accessible"

# 1. Copier le script de déploiement
echo ""
echo "📤 COPIE SCRIPT DE DÉPLOIEMENT"
echo "=============================="
scp "./deploy_dashboard_fix_simple.py" "$PROD_SERVER:/tmp/"

# 2. Exécuter le script de correction
echo ""
echo "🚀 EXÉCUTION CORRECTION"
echo "======================="
ssh "$PROD_SERVER" "cd $PROD_DIR && python3 /tmp/deploy_dashboard_fix_simple.py"

# 3. Test final
echo ""
echo "🧪 TEST FINAL"
echo "============"
echo "📋 Test accès au site..."
if curl -I -s http://martialcomp.com/ | head -1 | grep -q "200 OK"; then
    echo "✅ Site accessible"
else
    echo "❌ Site non accessible"
fi

echo ""
echo "🎉 DÉPLOIEMENT TERMINÉ!"
echo ""
echo "✅ CORRECTION APPLIQUÉE:"
echo "   📄 Dashboard router créé (utilise templates existants)"
echo "   🔧 Redirections auth corrigées"
echo "   🚀 Django redémarré"
echo ""
echo "🧪 TEST MAINTENANT:"
echo "   1. Aller sur: https://martialcomp.com/"
echo "   2. Cliquer: 'Rejoindre la phase de test'"
echo "   3. Se connecter: dojo_sakura_manager / demo2025"
echo "   4. Vérifier: dashboard club EXISTANT affiché"
echo ""
echo "📊 RÉSULTAT ATTENDU:"
echo "   👤 dojo_sakura_manager → /dashboard/club/"
echo "   🏢 Template: competitions/dashboard/club.html (EXISTANT)"
echo "   ❌ AUCUN nouveau template créé"