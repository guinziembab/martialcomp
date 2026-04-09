#!/bin/bash
# ================================================================
# Script de déploiement des corrections thème dark/gold + FieldDoesNotExist
# Date: 2024-11-30
# ================================================================

echo "=== Déploiement des corrections thème dark/gold + FieldDoesNotExist ==="
echo ""

# Configuration - Utilisation de l'alias SSH martialcomp-production
SSH_HOST="martialcomp-production"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

# Fichiers à transférer
declare -a FILES=(
    "apps/competitions/templates/competitions/competition/detail_enhanced.html"
    "apps/competitions/templates/competitions/management/results_dashboard.html"
    "apps/competitions/templates/competitions/management/club_results.html"
    "apps/competitions/templates/competitions/management/medals_report.html"
    "apps/competitions/views/management/results.py"
)

echo "Fichiers à transférer:"
for file in "${FILES[@]}"; do
    echo "  - $file"
done
echo ""

# Vérification des fichiers locaux
echo "Vérification des fichiers locaux..."
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file existe"
    else
        echo "✗ ERREUR: $file n'existe pas!"
        exit 1
    fi
done
echo ""

# Test de connexion SSH
echo "Test de connexion SSH avec l'alias martialcomp-production..."
ssh -o ConnectTimeout=10 "$SSH_HOST" "echo 'Connexion OK'" 2>/dev/null

if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  Connexion SSH impossible automatiquement."
    echo ""
    echo "Exécutez manuellement les commandes suivantes:"
    echo "=============================================="
    echo ""
    for file in "${FILES[@]}"; do
        echo "scp \"$file\" $SSH_HOST:$REMOTE_PATH/$file"
    done
    echo ""
    echo "# Puis redémarrez le serveur:"
    echo "ssh $SSH_HOST \"cd $REMOTE_PATH && sudo systemctl restart martialcomp || sudo service apache2 reload\""
    echo ""
    exit 1
fi

# Transfert des fichiers
echo ""
echo "Transfert des fichiers vers la production..."
for file in "${FILES[@]}"; do
    echo "Transfert de $file..."
    scp "$file" "$SSH_HOST:$REMOTE_PATH/$file"

    if [ $? -eq 0 ]; then
        echo "  ✓ Transféré avec succès"
    else
        echo "  ✗ ERREUR lors du transfert"
    fi
done

# Redémarrage du serveur
echo ""
echo "Redémarrage du serveur..."
ssh "$SSH_HOST" "cd $REMOTE_PATH && sudo systemctl restart martialcomp 2>/dev/null || sudo service apache2 reload 2>/dev/null || echo 'Redémarrage manuel requis'"

echo ""
echo "=== Déploiement terminé ==="
echo ""
echo "Corrections déployées:"
echo "1. detail_enhanced.html - Correction JavaScript + bouton Voir les résultats"
echo "2. results_dashboard.html - Thème dark/gold harmonisé"
echo "3. club_results.html - Thème dark/gold harmonisé"
echo "4. medals_report.html - Thème dark/gold harmonisé"
echo "5. results.py - Correction FieldDoesNotExist (registration_status au lieu de status)"
echo ""
echo "Testez les pages:"
echo "- https://martialcomp.com/fr/competitions/3/"
echo "- https://martialcomp.com/fr/competitions/management/3/results/"
echo "- https://martialcomp.com/fr/competitions/management/3/results/club/"
echo "- https://martialcomp.com/fr/competitions/management/3/results/medals/"
echo "- Bouton 'Publier tous les résultats'"
