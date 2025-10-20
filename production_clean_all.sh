#!/bin/bash

# Script de nettoyage complet pour repartir de zéro en production
# ⚠️  ATTENTION: Ce script SUPPRIME TOUT! Assurez-vous d'avoir une sauvegarde!

PROD_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
BACKUP_CHECK_FILE="/var/www/vhosts/martialcomp.com/backups/martialcomp_full_backup_*.tar.gz"

echo "🗑️  NETTOYAGE COMPLET PRODUCTION - MartialComp"
echo "=============================================="
echo "📅 Date: $(date)"
echo "📍 Répertoire: $PROD_DIR"
echo ""
echo "⚠️  ⚠️  ⚠️  ATTENTION ⚠️  ⚠️  ⚠️"
echo "Ce script va SUPPRIMER DÉFINITIVEMENT:"
echo "  - TOUT le code source"
echo "  - TOUS les uploads utilisateurs"
echo "  - TOUTES les configurations"
echo "  - TOUS les logs"
echo "  - TOUT le contenu de $PROD_DIR"
echo ""

# Vérification de sécurité
if [ ! -d "$PROD_DIR" ]; then
    echo "❌ Erreur: Le répertoire $PROD_DIR n'existe pas!"
    exit 1
fi

# Vérifier qu'une sauvegarde existe
echo "🔍 Vérification de l'existence d'une sauvegarde..."
if ls $BACKUP_CHECK_FILE 1> /dev/null 2>&1; then
    echo "✅ Sauvegarde trouvée:"
    ls -lh /var/www/vhosts/martialcomp.com/backups/martialcomp_full_backup_*.tar.gz | tail -1
else
    echo "⚠️  AUCUNE SAUVEGARDE TROUVÉE!"
    echo "Il est FORTEMENT recommandé de faire une sauvegarde d'abord."
    echo "Exécutez: ./production_backup_before_clean.sh"
fi

echo ""
echo "Êtes-vous ABSOLUMENT SÛR de vouloir tout supprimer?"
echo "Tapez 'DELETE ALL' (en majuscules) pour confirmer:"
read -r response

if [ "$response" != "DELETE ALL" ]; then
    echo "❌ Nettoyage annulé."
    exit 0
fi

echo ""
echo "Dernière chance. Tapez 'YES' pour procéder:"
read -r final_response

if [ "$final_response" != "YES" ]; then
    echo "❌ Nettoyage annulé."
    exit 0
fi

echo ""
echo "🗑️  Début du nettoyage..."

# Aller dans le répertoire parent pour pouvoir tout supprimer
cd $(dirname $PROD_DIR)

# Option 1: Suppression sélective (plus sûre)
echo ""
echo "Choisir le mode de nettoyage:"
echo "1) Suppression sélective (garde la structure de base)"
echo "2) Suppression totale (supprime TOUT)"
echo ""
echo "Votre choix (1 ou 2):"
read -r mode

if [ "$mode" == "1" ]; then
    echo ""
    echo "📋 Mode: Suppression sélective"
    echo "==============================="
    
    cd $PROD_DIR
    
    # Supprimer les gros éléments non essentiels
    echo "→ Suppression des environnements virtuels..."
    rm -rf venv env .venv virtualenv 2>/dev/null
    
    echo "→ Suppression des archives et backups..."
    find . -type f \( -name "*.tar.gz" -o -name "*.zip" -o -name "*.tar" -o -name "*.bak" -o -name "*.sql" \) -delete 2>/dev/null
    
    echo "→ Suppression des fichiers Python compilés..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
    find . -name "*.pyc" -delete 2>/dev/null
    
    echo "→ Suppression des logs..."
    find . -name "*.log" -delete 2>/dev/null
    
    echo "→ Suppression des bases de données locales..."
    find . -name "*.sqlite3" -o -name "*.db" -delete 2>/dev/null
    
    echo "→ Suppression du dossier .git..."
    rm -rf .git 2>/dev/null
    
    echo "→ Suppression des dossiers de cache..."
    rm -rf .cache .pytest_cache .mypy_cache 2>/dev/null
    
    echo "→ Suppression des fichiers temporaires..."
    find . -name "*~" -o -name "*.tmp" -o -name "*.temp" -delete 2>/dev/null
    
    echo "→ Vidage des dossiers media et staticfiles..."
    rm -rf media/* staticfiles/* 2>/dev/null
    
    echo "→ Suppression des dossiers de développement..."
    rm -rf node_modules .idea .vscode 2>/dev/null
    
    # Créer un fichier marqueur
    echo "Site nettoyé le $(date)" > CLEANED.txt
    
elif [ "$mode" == "2" ]; then
    echo ""
    echo "💀 Mode: Suppression totale"
    echo "============================"
    echo "→ Suppression complète de $PROD_DIR..."
    
    # Supprimer tout le contenu mais garder le dossier
    rm -rf $PROD_DIR/* 2>/dev/null
    rm -rf $PROD_DIR/.[!.]* 2>/dev/null
    
    # Créer un fichier marqueur
    echo "Site complètement supprimé le $(date)" > $PROD_DIR/DELETED.txt
    
else
    echo "❌ Choix invalide. Nettoyage annulé."
    exit 1
fi

echo ""
echo "✅ Nettoyage terminé!"
echo ""

# Afficher l'état final
echo "📊 État après nettoyage:"
echo "========================"
if [ -d "$PROD_DIR" ]; then
    echo "- Espace utilisé: $(du -sh $PROD_DIR 2>/dev/null | cut -f1)"
    echo "- Fichiers restants: $(find $PROD_DIR -type f 2>/dev/null | wc -l)"
    echo "- Dossiers restants: $(find $PROD_DIR -type d 2>/dev/null | wc -l)"
fi

echo ""
echo "🚀 Prochaines étapes:"
echo "====================="
echo "1. Transférer le nouveau package de production"
echo "2. Extraire avec: tar -xzf martialcomp_production_*.tar.gz"
echo "3. Configurer les permissions avec: ./set_plesk_permissions.sh"
echo "4. Installer les dépendances: pip install -r requirements.txt"
echo "5. Configurer les variables d'environnement"
echo "6. Exécuter les migrations: python manage.py migrate"
echo "7. Collecter les fichiers statiques: python manage.py collectstatic"
echo "8. Redémarrer l'application dans Plesk"
echo ""
echo "📝 Note: Les sauvegardes sont dans /var/www/vhosts/martialcomp.com/backups/"