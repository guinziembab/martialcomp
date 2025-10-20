#!/bin/bash
# Script simple pour exécuter la correction en une seule commande

echo "================================================"
echo "🚀 CORRECTION DISCIPLINES FÉDÉRATION - SIMPLIFIÉ"
echo "================================================"
echo ""

# Vérifier que nous avons le script de correction
if [ ! -f "fix_federation_disciplines_production_final.sh" ]; then
    echo "❌ Erreur: fix_federation_disciplines_production_final.sh non trouvé"
    echo "Assurez-vous d'être dans le bon répertoire"
    exit 1
fi

echo "📦 Transfert du script vers le serveur de production..."
scp fix_federation_disciplines_production_final.sh martialcomp-production:/home/martialc/

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors du transfert SCP"
    exit 1
fi

echo "✅ Script transféré avec succès"
echo ""
echo "🔧 Exécution de la correction sur le serveur..."
echo ""

# Exécuter le script sur le serveur distant
ssh martialcomp-production 'cd /home/martialc && chmod +x fix_federation_disciplines_production_final.sh && sudo ./fix_federation_disciplines_production_final.sh'

if [ $? -eq 0 ]; then
    echo ""
    echo "================================================"
    echo "✅ CORRECTION APPLIQUÉE AVEC SUCCÈS!"
    echo "================================================"
    echo ""
    echo "🎯 Actions suivantes:"
    echo "1. Ouvrir https://app.martialcomp.com"
    echo "2. Se connecter ou créer un compte"
    echo "3. Aller sur https://app.martialcomp.com/competitions/onboarding/federation/"
    echo "4. Vérifier que les cases à cocher des disciplines s'affichent"
    echo ""
else
    echo ""
    echo "❌ Une erreur s'est produite lors de l'exécution"
    echo "Connectez-vous manuellement pour vérifier:"
    echo "ssh martialcomp-production"
    echo "cd /home/martialc"
    echo "sudo ./fix_federation_disciplines_production_final.sh"
fi