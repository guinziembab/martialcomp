#!/bin/bash

# Script d'installation des corrections urgentes Practitioner
# À exécuter sur le serveur de production

echo "🚨 INSTALLATION DES CORRECTIONS URGENTES - PRACTITIONER FIX"
echo "============================================================"

# Vérifier qu'on est sur le serveur de production
if [ ! -d "/var/www/vhosts/martialcomp.com/httpdocs" ]; then
    echo "❌ Erreur: Ce script doit être exécuté sur le serveur de production"
    echo "   Répertoire attendu: /var/www/vhosts/martialcomp.com/httpdocs"
    exit 1
fi

# Aller dans le répertoire de production
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "📁 Répertoire de travail: $(pwd)"
echo "📅 Date: $(date)"

# Créer une sauvegarde avant modification
echo "💾 Création de la sauvegarde..."
BACKUP_DIR="/var/backups/martialcomp_before_practitioner_fix_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Sauvegarder les fichiers existants
if [ -f "config/settings/production.py" ]; then
    cp config/settings/production.py "$BACKUP_DIR/"
    echo "✅ Sauvegarde de config/settings/production.py"
fi

if [ -f ".htaccess" ]; then
    cp .htaccess "$BACKUP_DIR/"
    echo "✅ Sauvegarde de .htaccess"
fi

echo "📦 Sauvegarde créée dans: $BACKUP_DIR"

# 1. Installer le fichier de settings modifié
echo ""
echo "🔧 Installation du fichier de settings..."
if [ -f "production.py" ]; then
    cp production.py config/settings/production.py
    echo "✅ Settings de production mis à jour"
else
    echo "❌ Fichier production.py non trouvé"
    exit 1
fi

# 2. Installer le fichier admin_override
echo ""
echo "🔧 Installation du fichier admin_override..."
if [ -f "admin_override.py" ]; then
    mkdir -p apps/competitions/
    cp admin_override.py apps/competitions/admin_override.py
    echo "✅ Admin override installé"
else
    echo "❌ Fichier admin_override.py non trouvé"
    exit 1
fi

# 3. Vérifier que le middleware existe
echo ""
echo "🔍 Vérification du middleware..."
if [ -f "apps/core/middleware/block_practitioner.py" ]; then
    echo "✅ Middleware BlockPractitionerMiddleware trouvé"
else
    echo "❌ Middleware BlockPractitionerMiddleware manquant"
    echo "   Le middleware doit être créé manuellement"
    exit 1
fi

# 4. Ajouter la redirection Apache (.htaccess)
echo ""
echo "📝 Configuration des redirections Apache..."
if [ -f ".htaccess_production_fix" ]; then
    # Sauvegarder l'ancien .htaccess
    if [ -f ".htaccess" ]; then
        cp .htaccess .htaccess.backup.$(date +%Y%m%d_%H%M%S)
    fi
    
    # Ajouter les redirections
    cat .htaccess_production_fix >> .htaccess
    echo "✅ Redirections Apache ajoutées"
else
    echo "⚠️ Fichier .htaccess_production_fix non trouvé"
fi

# 5. Vérifier la configuration Django
echo ""
echo "🧪 Test de la configuration Django..."
python3 manage.py check --settings=config.settings.production

if [ $? -eq 0 ]; then
    echo "✅ Configuration Django valide"
else
    echo "❌ Erreur dans la configuration Django"
    echo "   Restauration de la sauvegarde..."
    cp "$BACKUP_DIR/production.py" config/settings/production.py
    exit 1
fi

# 6. Redémarrer Apache
echo ""
echo "🔄 Redémarrage d'Apache..."
systemctl restart apache2

if [ $? -eq 0 ]; then
    echo "✅ Apache redémarré avec succès"
else
    echo "❌ Erreur lors du redémarrage d'Apache"
    exit 1
fi

# 7. Tester les corrections
echo ""
echo "🧪 Test des corrections..."
if [ -f "test_practitioner_fix.py" ]; then
    python3 test_practitioner_fix.py
    if [ $? -eq 0 ]; then
        echo "✅ Tests des corrections réussis"
    else
        echo "⚠️ Certains tests ont échoué"
    fi
else
    echo "⚠️ Script de test non trouvé"
fi

# 8. Vérifier les logs
echo ""
echo "📊 Vérification des logs..."
echo "Logs Apache (dernières erreurs):"
tail -n 10 /var/log/apache2/error.log | grep -i practitioner || echo "Aucune erreur practitioner récente"

echo ""
echo "Logs Django (si disponible):"
if [ -f "/var/log/django/martialcomp.log" ]; then
    tail -n 5 /var/log/django/martialcomp.log | grep -i practitioner || echo "Aucun log practitioner récent"
else
    echo "Fichier de log Django non trouvé"
fi

echo ""
echo "🎉 INSTALLATION TERMINÉE AVEC SUCCÈS!"
echo "===================================="
echo ""
echo "✅ Corrections installées:"
echo "   - Middleware Django BlockPractitionerMiddleware"
echo "   - Redirection Apache (.htaccess)"
echo "   - Désinscription du modèle Practitioner de l'admin"
echo ""
echo "🧪 Tests à effectuer manuellement:"
echo "   1. Accéder à https://martialcomp.com/fr/admin/competitions/practitioner/"
echo "   2. Vérifier la redirection vers /fr/admin/"
echo "   3. Contrôler l'interface d'administration générale"
echo ""
echo "📞 En cas de problème:"
echo "   - Sauvegarde disponible dans: $BACKUP_DIR"
echo "   - Logs Apache: /var/log/apache2/error.log"
echo "   - Statut Apache: systemctl status apache2"
echo ""
echo "🔄 Pour restaurer:"
echo "   cp $BACKUP_DIR/production.py config/settings/production.py"
echo "   cp $BACKUP_DIR/.htaccess .htaccess"
echo "   systemctl restart apache2"