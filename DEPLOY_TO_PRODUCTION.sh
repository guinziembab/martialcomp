#!/bin/bash
# Script de déploiement des corrections en production

echo "📤 DÉPLOIEMENT DES CORRECTIONS EN PRODUCTION"
echo "==========================================="

# Transfert des scripts de diagnostic et correction
echo "1️⃣ Transfert du script de diagnostic..."
scp check_disciplines_production.py martialcomp-production:/tmp/

echo "2️⃣ Transfert du script de correction..."
scp fix_disciplines_production.py martialcomp-production:/tmp/

echo "3️⃣ Transfert du script rapide..."
scp quick_fix_disciplines.sh martialcomp-production:/tmp/

echo "4️⃣ Transfert de la documentation..."
scp RUNBOOK_PRODUCTION_FIX.md martialcomp-production:/tmp/

echo ""
echo "✅ Transfert terminé!"
echo ""
echo "==========================================="
echo "PROCHAINES ÉTAPES SUR LE SERVEUR:"
echo "==========================================="
echo ""
echo "# Se connecter au serveur"
echo "ssh martialcomp-production"
echo ""
echo "# Option 1: Diagnostic d'abord"
echo "cd /var/www/vhosts/martialcomp.com/httpdocs"
echo "source venv/bin/activate"
echo "python /tmp/check_disciplines_production.py"
echo ""
echo "# Option 2: Correction directe (recommandé)"
echo "chmod +x /tmp/quick_fix_disciplines.sh"
echo "cd /var/www/vhosts/martialcomp.com/httpdocs"
echo "bash /tmp/quick_fix_disciplines.sh"
echo ""
echo "# Option 3: Correction manuelle complète"
echo "cd /var/www/vhosts/martialcomp.com/httpdocs"
echo "source venv/bin/activate"
echo "python /tmp/fix_disciplines_production.py"
echo ""
echo "==========================================="