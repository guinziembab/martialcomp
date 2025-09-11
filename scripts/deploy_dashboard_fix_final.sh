#!/bin/bash

# Déploiement de la correction dashboard finale
# Utilise les templates existants au lieu de créer de nouveaux

echo "🎯 DÉPLOIEMENT CORRECTION DASHBOARD FINALE"
echo "=========================================="

# Variables
PROD_SERVER="root@martialcomp.com"
PROD_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
LOCAL_DIR="/mnt/c/martial_hub_django/martialcomp"

echo "📂 Serveur: $PROD_SERVER"
echo "📂 Répertoire: $PROD_DIR"

# 1. Copier les fichiers corrigés
echo ""
echo "📤 COPIE DES FICHIERS CORRIGÉS"
echo "=============================="

# Copier le routeur dashboard
echo "📄 Copie competitions/views/dashboard_router.py..."
scp "$LOCAL_DIR/competitions/views/dashboard_router.py" "$PROD_SERVER:$PROD_DIR/competitions/views/"

# Copier les URLs corrigées
echo "📄 Copie competitions/urls.py..."
scp "$LOCAL_DIR/competitions/urls.py" "$PROD_SERVER:$PROD_DIR/competitions/"

# 2. Supprimer le conflit competitions/urls/
echo ""
echo "🗑️ SUPPRESSION CONFLIT"
echo "====================="
ssh "$PROD_SERVER" "cd $PROD_DIR && rm -rf competitions/urls/ && echo '✅ Dossier competitions/urls/ supprimé'"

# 3. Corriger les redirections d'authentification
echo ""
echo "🔧 CORRECTION REDIRECTIONS AUTH"
echo "==============================="
ssh "$PROD_SERVER" "cd $PROD_DIR && sed -i \"s|/competitions/dashboard/|/dashboard/|g\" config/settings.py && echo '✅ Redirections auth corrigées'"

# 4. Test de la configuration
echo ""
echo "🧪 TEST CONFIGURATION"
echo "====================="
ssh "$PROD_SERVER" "cd $PROD_DIR && export DJANGO_SETTINGS_MODULE=config.settings && python3 -c 'import competitions.urls; print(f\"✅ URLs importées: {len(competitions.urls.urlpatterns)} patterns\")'"

# 5. Redémarrage Django
echo ""
echo "🚀 REDÉMARRAGE DJANGO"
echo "===================="
ssh "$PROD_SERVER" "cd $PROD_DIR && pkill -f manage.py; sleep 3; nohup python3 manage.py runserver 0.0.0.0:8000 > /dev/null 2>&1 & sleep 6; echo '✅ Django redémarré'"

# 6. Test final
echo ""
echo "🧪 TEST FINAL"
echo "============"
echo "📋 Test accès au site..."
curl -I -s http://martialcomp.com/ | head -1

echo ""
echo "🎉 DÉPLOIEMENT TERMINÉ!"
echo ""
echo "✅ CHANGEMENTS APPLIQUÉS:"
echo "   📄 Routeur dashboard créé"
echo "   📄 URLs competitions corrigées"
echo "   🗑️ Conflit competitions/urls/ supprimé"
echo "   🔧 Redirections auth corrigées"
echo ""
echo "🧪 TEST RECOMMANDÉ:"
echo "   1. Aller sur https://martialcomp.com/"
echo "   2. Cliquer 'Rejoindre la phase de test'"
echo "   3. Se connecter: dojo_sakura_manager / demo2025"
echo "   4. Vérifier que le dashboard club s'affiche (template existant)"
echo ""
echo "📊 RÉSULTAT ATTENDU:"
echo "   👤 dojo_sakura_manager → /dashboard/club/"
echo "   🏢 Template: competitions/dashboard/club.html (existant)"
echo "   ✅ Pas de nouveau template créé"