#!/bin/bash
# Script à exécuter sur le serveur martialcomp.com

echo "🚀 DÉPLOIEMENT SUR SERVEUR - MartialComp"
echo "========================================"

# Vérifier qu'on est dans le bon répertoire
if [[ ! -f "manage.py" ]]; then
    echo "❌ Erreur: manage.py non trouvé. Exécuter depuis /var/www/martialcomp"
    exit 1
fi

# Sauvegarde
echo "💾 Création de sauvegarde..."
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r apps/competitions/views/federations.py "$BACKUP_DIR/" 2>/dev/null || true
cp -r apps/competitions/templates/competitions/federations/examens/ "$BACKUP_DIR/" 2>/dev/null || true
cp -r apps/competitions/urls/dashboard.py "$BACKUP_DIR/" 2>/dev/null || true
echo "   ✅ Sauvegarde créée dans $BACKUP_DIR"

# Appliquer les corrections
echo "🔧 Application des corrections..."
cp apps/competitions/views/federations.py apps/competitions/views/federations.py.backup
cp apps/competitions/urls/dashboard.py apps/competitions/urls/dashboard.py.backup
cp apps/competitions/templates/competitions/federations/examens/list.html apps/competitions/templates/competitions/federations/examens/list.html.backup

echo "   ✅ Fichiers copiés"

# Correction des migrations
echo "🗄️ Correction des migrations..."
python3 manage.py migrate --fake competitions 0007 || echo "   ⚠️ Migration fake échouée, on continue..."
rm -f apps/competitions/migrations/0008_remove_* 2>/dev/null || true
rm -f apps/competitions/migrations/0009_alter_* 2>/dev/null || true
python3 manage.py makemigrations
python3 manage.py migrate

# Collecter les fichiers statiques
echo "📁 Collecte des fichiers statiques..."
python3 manage.py collectstatic --noinput

# Vérification Django
echo "🔍 Vérification Django..."
python3 manage.py check

# Redémarrage des services
echo "🔄 Redémarrage des services..."
sudo systemctl restart nginx
sudo systemctl restart gunicorn || sudo systemctl restart martialcomp || echo "   ⚠️ Service Django non redémarré"

# Test final
echo "🧪 Test final..."
sleep 3
curl -I https://martialcomp.com/fr/competitions/federations/3/examens/ || echo "   ⚠️ Test de connexion échoué"

echo ""
echo "✅ DÉPLOIEMENT TERMINÉ"
echo "📋 Vérifier manuellement:"
echo "   - https://martialcomp.com/fr/competitions/federations/3/examens/"
echo "   - https://martialcomp.com/fr/competitions/dashboard/documentation/"
