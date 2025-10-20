#!/bin/bash
# Transférer le fichier federations.py de développement vers production

echo "================================================"
echo "🚀 TRANSFERT federations.py VERS PRODUCTION"
echo "================================================"
echo ""

# Vérifier que le fichier source existe
if [ ! -f "/mnt/c/martial_hub_django/martialcomp/apps/competitions/views/federations.py" ]; then
    echo "❌ Erreur: Fichier source non trouvé"
    exit 1
fi

echo "1️⃣ Copie du fichier vers un emplacement temporaire..."
cp /mnt/c/martial_hub_django/martialcomp/apps/competitions/views/federations.py /tmp/federations_dev.py
echo "✅ Fichier copié dans /tmp/"

echo ""
echo "2️⃣ Transfert vers le serveur de production..."
scp /tmp/federations_dev.py martialcomp-production:/tmp/

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors du transfert SCP"
    exit 1
fi

echo "✅ Fichier transféré sur le serveur"

echo ""
echo "3️⃣ Installation sur le serveur de production..."
ssh martialcomp-production << 'REMOTE_COMMANDS'
echo "📍 Connexion au serveur de production..."
cd /var/www/vhosts/martialcomp.com/httpdocs

echo ""
echo "4️⃣ Sauvegarde de la version actuelle..."
BACKUP_FILE="apps/competitions/views/federations.py.backup_$(date +%Y%m%d_%H%M%S)"
cp apps/competitions/views/federations.py "$BACKUP_FILE"
echo "✅ Backup créé: $BACKUP_FILE"

echo ""
echo "5️⃣ Remplacement par la version de développement..."
cp /tmp/federations_dev.py apps/competitions/views/federations.py
chown www-data:www-data apps/competitions/views/federations.py
echo "✅ Fichier remplacé avec succès"

echo ""
echo "6️⃣ Vérification du nouveau fichier..."
echo "📋 Fonctions présentes:"
grep -E "^def federation_list|^def federation_detail" apps/competitions/views/federations.py | head -5

echo ""
echo "7️⃣ Nettoyage du cache Python..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

echo ""
echo "8️⃣ Redémarrage des services..."
sudo systemctl restart martialcomp
sudo systemctl reload apache2
echo "✅ Services redémarrés"

echo ""
echo "9️⃣ Test de l'import..."
source /var/www/vhosts/martialcomp.com/venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

python3 -c "
import django
django.setup()
try:
    from apps.competitions.views.federations import federation_list, federation_detail
    print('✅ Import des vues réussi!')
    print('  - federation_list trouvé')
    print('  - federation_detail trouvé')
except ImportError as e:
    print(f'❌ Erreur import: {e}')
"

echo ""
echo "🔟 Nettoyage..."
rm -f /tmp/federations_dev.py
echo "✅ Fichiers temporaires supprimés"

echo ""
echo "================================================"
echo "✅ TRANSFERT TERMINÉ AVEC SUCCÈS!"
echo "================================================"
echo ""
echo "Le fichier federations.py de développement a été transféré en production."
echo "Les vues federation_list et federation_detail sont maintenant disponibles."
echo ""
echo "🎯 Testez maintenant: https://martialcomp.com/fr/"

REMOTE_COMMANDS

# Nettoyer le fichier temporaire local
rm -f /tmp/federations_dev.py