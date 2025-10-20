#\!/bin/bash
# Transférer le template federation.html corrigé en production

echo "================================================"
echo "🚀 TRANSFERT DU TEMPLATE FEDERATION EN PRODUCTION"
echo "================================================"
echo ""

# Créer une archive du template
echo "1️⃣ Préparation du template pour le transfert..."
echo "=============================================="
mkdir -p federation_template_transfer
cp apps/competitions/templates/competitions/dashboard/federation.html federation_template_transfer/

# Créer un script de déploiement
cat > federation_template_transfer/deploy_template.sh << 'DEPLOY_SCRIPT'
#\!/bin/bash
# Script de déploiement du template

echo "Déploiement du template federation.html..."

# Sauvegarder l'ancien template
if [ -f "apps/competitions/templates/competitions/dashboard/federation.html" ]; then
    cp apps/competitions/templates/competitions/dashboard/federation.html \
       apps/competitions/templates/competitions/dashboard/federation.html.backup_$(date +%Y%m%d_%H%M%S)
    echo "✅ Ancien template sauvegardé"
fi

# Copier le nouveau template
cp federation.html apps/competitions/templates/competitions/dashboard/
echo "✅ Nouveau template installé"

# Modifier la vue pour utiliser le template original
sed -i "s/'competitions\/dashboard\/federation_simple.html'/'competitions\/dashboard\/federation.html'/g" \
    apps/competitions/views/dashboard/federations.py
echo "✅ Vue modifiée pour utiliser le template original"

echo "✅ Déploiement terminé"
DEPLOY_SCRIPT

chmod +x federation_template_transfer/deploy_template.sh

# Créer l'archive
tar -czf federation_template_transfer.tar.gz federation_template_transfer/
echo "✅ Archive créée: federation_template_transfer.tar.gz"

echo ""
echo "2️⃣ Transfert vers la production..."
echo "================================="
scp federation_template_transfer.tar.gz martialcomp-production:/tmp/
echo "✅ Archive transférée"

echo ""
echo "3️⃣ Déploiement en production..."
echo "=============================="
ssh martialcomp-production << 'REMOTE_COMMANDS'
cd /var/www/vhosts/martialcomp.com/httpdocs

# Extraire l'archive
tar -xzf /tmp/federation_template_transfer.tar.gz
echo "✅ Archive extraite"

# Exécuter le déploiement
cd federation_template_transfer
bash deploy_template.sh
cd ..

# Nettoyer
rm -rf federation_template_transfer
rm -f /tmp/federation_template_transfer.tar.gz

# Redémarrer le service
sudo systemctl restart martialcomp
echo "✅ Service redémarré"

echo ""
echo "4️⃣ Test du nouveau template..."
echo "============================="
curl -s -o /dev/null -w "Status HTTP: %{http_code}\n" https://martialcomp.com/fr/competitions/dashboard/federation/41/

REMOTE_COMMANDS

echo ""
echo "5️⃣ Test avec session authentifiée..."
echo "==================================="
ssh martialcomp-production << 'REMOTE_TEST'
cd /var/www/vhosts/martialcomp.com/httpdocs
source /var/www/vhosts/martialcomp.com/venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

python3 << 'PYEOF'
import django
django.setup()

from django.test import Client

client = Client()

# Test rapide
if client.login(username='DT_bguinziemba', password='AQWZSX123ok,'):
    resp = client.get('/competitions/dashboard/federation/41/', HTTP_HOST='martialcomp.com', follow=True)
    print(f"✅ Test authentifié: Status {resp.status_code}")
    
    if resp.status_code == 200:
        content = resp.content.decode('utf-8')
        if 'UBLP' in content and 'error' not in content.lower():
            print("✅ Template fonctionne correctement")
        else:
            print("⚠️  Possible problème dans le template")
else:
    print("❌ Échec de connexion")
PYEOF
REMOTE_TEST

echo ""
echo "================================================"
echo "✅ TRANSFERT TERMINÉ"
echo "================================================"

# Nettoyer localement
rm -rf federation_template_transfer
rm -f federation_template_transfer.tar.gz
rm -f federation_dev.html federation_fixed.html urls_list.txt url_mappings.py

