#!/bin/bash

# Script de déploiement des corrections urgentes pour le problème Practitioner
# À exécuter sur le serveur de production

echo "🚨 DÉPLOIEMENT DES CORRECTIONS URGENTES - PRACTITIONER FIX"
echo "=========================================================="

# Vérifier qu'on est sur le serveur de production
if [ ! -d "/var/www/vhosts/martialcomp.com/httpdocs" ]; then
    echo "❌ Erreur: Ce script doit être exécuté sur le serveur de production"
    exit 1
fi

# Aller dans le répertoire de production
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "📁 Répertoire de travail: $(pwd)"

# 1. Vérifier que le middleware existe
if [ -f "apps/core/middleware/block_practitioner.py" ]; then
    echo "✅ Middleware BlockPractitionerMiddleware trouvé"
else
    echo "❌ Middleware BlockPractitionerMiddleware manquant"
    exit 1
fi

# 2. Vérifier que les settings sont modifiés
if grep -q "BlockPractitionerMiddleware" config/settings/production.py; then
    echo "✅ Middleware ajouté dans les settings de production"
else
    echo "❌ Middleware non trouvé dans les settings"
    exit 1
fi

# 3. Ajouter la redirection Apache (.htaccess)
echo "📝 Ajout des redirections Apache..."

# Sauvegarder l'ancien .htaccess
if [ -f ".htaccess" ]; then
    cp .htaccess .htaccess.backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ Sauvegarde de .htaccess créée"
fi

# Ajouter les redirections
cat >> .htaccess << 'EOF'

# URGENT FIX - Redirection des URLs practitioner
RedirectMatch 301 ^/fr/admin/competitions/practitioner/?.*$ /fr/admin/
RedirectMatch 301 ^/en/admin/competitions/practitioner/?.*$ /en/admin/
RedirectMatch 301 ^/admin/competitions/practitioner/?.*$ /admin/
EOF

echo "✅ Redirections Apache ajoutées"

# 4. Redémarrer Apache
echo "🔄 Redémarrage d'Apache..."
systemctl restart apache2

if [ $? -eq 0 ]; then
    echo "✅ Apache redémarré avec succès"
else
    echo "❌ Erreur lors du redémarrage d'Apache"
    exit 1
fi

# 5. Tester la configuration Django
echo "🧪 Test de la configuration Django..."
python manage.py check --settings=config.settings.production

if [ $? -eq 0 ]; then
    echo "✅ Configuration Django valide"
else
    echo "❌ Erreur dans la configuration Django"
    exit 1
fi

# 6. Vérifier les logs
echo "📊 Vérification des logs..."
tail -n 20 /var/log/apache2/error.log | grep -i practitioner || echo "Aucune erreur practitioner récente"

echo ""
echo "🎉 DÉPLOIEMENT TERMINÉ AVEC SUCCÈS!"
echo "=================================="
echo ""
echo "✅ Solutions implémentées:"
echo "   - Middleware Django BlockPractitionerMiddleware"
echo "   - Redirection Apache (.htaccess)"
echo "   - Désinscription du modèle Practitioner de l'admin"
echo ""
echo "🧪 Tests à effectuer:"
echo "   1. Accéder à https://martialcomp.com/fr/admin/competitions/practitioner/"
echo "   2. Vérifier la redirection vers /fr/admin/"
echo "   3. Contrôler les logs pour confirmer le blocage"
echo ""
echo "📞 En cas de problème, vérifier:"
echo "   - Les logs Apache: /var/log/apache2/error.log"
echo "   - Les logs Django: /var/log/django/martialcomp.log"
echo "   - Le statut Apache: systemctl status apache2"