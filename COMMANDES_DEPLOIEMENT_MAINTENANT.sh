#!/bin/bash
# Commandes de déploiement - Correction {% trans %} JavaScript
# À exécuter MAINTENANT pour déployer la correction

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║        DÉPLOIEMENT - Correction {% trans %} JavaScript        ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================
# OPTION 1 : DÉPLOIEMENT AUTOMATIQUE (RECOMMANDÉ)
# ============================================================

echo "🚀 OPTION 1 : Déploiement Automatique"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Exécutez cette commande :"
echo ""
echo "  ./deploy_js_trans_fix_20251026.sh"
echo ""
echo "Le script va :"
echo "  ✅ Vérifier le fichier local"
echo "  ✅ Créer une sauvegarde sur le serveur"
echo "  ✅ Copier le fichier corrigé"
echo "  ✅ Collecter les fichiers statiques"
echo "  ✅ Redémarrer les services"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo ""

# ============================================================
# OPTION 2 : DÉPLOIEMENT MANUEL
# ============================================================

echo "🔧 OPTION 2 : Déploiement Manuel"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Si vous préférez déployer manuellement, suivez ces étapes :"
echo ""

# Étape 1
echo "📋 ÉTAPE 1 : Vérification locale"
echo "────────────────────────────────────────────────────────────"
echo ""
echo "  grep -c \"'{% trans\" apps/competitions/templates/competitions/dashboard/club.html"
echo ""
echo "  Résultat attendu : 0"
echo ""

# Étape 2
echo "📦 ÉTAPE 2 : Connexion au serveur et sauvegarde"
echo "────────────────────────────────────────────────────────────"
echo ""
echo "  ssh root@martialcomp.com"
echo "  cd /var/www/martialcomp"
echo "  mkdir -p backups"
echo "  cp apps/competitions/templates/competitions/dashboard/club.html \\"
echo "     backups/club_html_backup_\$(date +%Y%m%d_%H%M%S).html"
echo "  exit"
echo ""

# Étape 3
echo "📤 ÉTAPE 3 : Copie du fichier (depuis votre machine locale)"
echo "────────────────────────────────────────────────────────────"
echo ""
echo "  scp apps/competitions/templates/competitions/dashboard/club.html \\"
echo "      root@martialcomp.com:/var/www/martialcomp/apps/competitions/templates/competitions/dashboard/club.html"
echo ""

# Étape 4
echo "🔄 ÉTAPE 4 : Redémarrage des services (sur le serveur)"
echo "────────────────────────────────────────────────────────────"
echo ""
echo "  ssh root@martialcomp.com"
echo "  cd /var/www/martialcomp"
echo "  source venv/bin/activate"
echo "  python3 manage.py collectstatic --noinput"
echo "  sudo systemctl restart gunicorn"
echo "  sudo systemctl reload nginx"
echo "  exit"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo ""

# ============================================================
# TESTS APRÈS DÉPLOIEMENT
# ============================================================

echo "🧪 TESTS APRÈS DÉPLOIEMENT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Ouvrir le site :"
echo "   https://martialcomp.com/fr/competitions/dashboard/club/"
echo ""
echo "2. Vider le cache du navigateur :"
echo "   Appuyez sur Ctrl+Shift+F5 (ou Ctrl+F5)"
echo ""
echo "3. Ouvrir la console JavaScript :"
echo "   Appuyez sur F12"
echo "   Cliquez sur l'onglet 'Console'"
echo ""
echo "4. Tester la page Pratiquants :"
echo "   Cliquez sur l'onglet 'Pratiquants'"
echo ""
echo "5. Vérifier :"
echo "   ✅ Pas d'erreur 'Uncaught SyntaxError' dans la console"
echo "   ✅ Âge affiché : '59 ans' (pas '-')"
echo "   ✅ Logs de débogage visibles : '[AGE DEBUG] ...'"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo ""

# ============================================================
# RÉSULTAT ATTENDU
# ============================================================

echo "📊 RÉSULTAT ATTENDU DANS LA CONSOLE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  🔍 [AGE DEBUG] DOMContentLoaded déclenché"
echo "  🔍 [AGE DEBUG] calculateAges() appelé"
echo "  🔍 [AGE DEBUG] Nombre d elements .age-display trouvés: 1"
echo "    Element 0: <span class=\"age-display\" data-birth-date=\"1966-03-12\">"
echo "      - data-birth-date: 1966-03-12"
echo "      → Calcul pour: 1966-03-12"
echo "        Date valide, calcul en cours..."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo ""

# ============================================================
# EN CAS DE PROBLÈME
# ============================================================

echo "⚠️  EN CAS DE PROBLÈME"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Restaurer la sauvegarde :"
echo ""
echo "  ssh root@martialcomp.com"
echo "  cd /var/www/martialcomp"
echo "  ls -lh backups/  # Trouver le nom de la sauvegarde"
echo "  cp backups/club_html_backup_YYYYMMDD_HHMMSS.html \\"
echo "     apps/competitions/templates/competitions/dashboard/club.html"
echo "  sudo systemctl restart gunicorn"
echo "  sudo systemctl reload nginx"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo ""

# ============================================================
# DOCUMENTATION
# ============================================================

echo "📚 DOCUMENTATION DISPONIBLE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  📄 INSTRUCTIONS_DEPLOIEMENT_TRANS_FIX.md"
echo "     → Instructions détaillées (7.1 KB)"
echo ""
echo "  📄 RAPPORT_CORRECTION_TRANS_JS_20251026.md"
echo "     → Rapport complet de la correction (12 KB)"
echo ""
echo "  📄 RESUME_CORRECTION_TRANS_20251026.md"
echo "     → Résumé exécutif (2.7 KB)"
echo ""
echo "  📄 CORRECTION_APPLIQUEE_MAINTENANT.txt"
echo "     → Résumé visuel"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo ""

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║              🎉 PRÊT À DÉPLOYER - BONNE CHANCE ! 🚀           ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
