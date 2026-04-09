#!/bin/bash
# Script de déploiement des corrections pour le problème 403

echo "=== Déploiement des corrections 403 ==="

# Configuration
REMOTE_HOST="root@martialcomp.com"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

# Création d'une archive avec tous les fichiers modifiés
echo "1. Création de l'archive des fichiers modifiés..."
tar -czf fix_403_bundle.tar.gz \
  apps/competitions/views/club/practitioners.py \
  apps/competitions/views/club/test_permissions.py \
  apps/competitions/urls/club.py \
  patch_practitioners.py \
  fix_practitioner_403.sh

# Tentative de copie via SCP avec timeout réduit
echo "2. Tentative de copie via SCP..."
scp -o ConnectTimeout=30 -o ServerAliveInterval=15 fix_403_bundle.tar.gz $REMOTE_HOST:$REMOTE_PATH/ 2>/dev/null

if [ $? -ne 0 ]; then
    echo "SCP a échoué. Essai avec une méthode alternative..."
    
    # Méthode alternative : créer un script d'installation à copier-coller
    echo "3. Création d'un script d'installation manuel..."
    cat > manual_deploy_403.txt << 'EOF'
# === INSTRUCTIONS DE DÉPLOIEMENT MANUEL ===
# 
# 1. Connectez-vous au serveur : ssh root@martialcomp.com
# 2. Allez dans le dossier du projet : cd /var/www/vhosts/martialcomp.com/httpdocs
# 3. Créez une sauvegarde : 
#    mkdir -p backups/fix_403_$(date +%Y%m%d_%H%M%S)
#    cp apps/competitions/views/club/practitioners.py backups/fix_403_$(date +%Y%m%d_%H%M%S)/
#    cp apps/competitions/urls/club.py backups/fix_403_$(date +%Y%m%d_%H%M%S)/
# 
# 4. Créez le fichier test_permissions.py :
#    nano apps/competitions/views/club/test_permissions.py
#    # Copiez le contenu ci-dessous
# 
# 5. Modifiez apps/competitions/urls/club.py :
#    - Ajoutez après la ligne 33 : from apps.competitions.views.club.test_permissions import test_permissions_view
#    - Ajoutez avant la dernière ligne ] : path('test-permissions/', test_permissions_view, name='test_permissions'),
# 
# 6. Appliquez le patch practitioners.py (voir contenu ci-dessous)
# 
# 7. Redémarrez le service : systemctl restart martialcomp.service
# 
# === CONTENU test_permissions.py ===
EOF
    cat apps/competitions/views/club/test_permissions.py >> manual_deploy_403.txt
    
    echo "" >> manual_deploy_403.txt
    echo "# === FIN test_permissions.py ===" >> manual_deploy_403.txt
    echo "" >> manual_deploy_403.txt
    echo "# === MODIFICATION practitioners.py ===" >> manual_deploy_403.txt
    echo "# Dans la fonction practitioner_create, remplacez tout le contenu par :" >> manual_deploy_403.txt
    echo "" >> manual_deploy_403.txt
    
    # Extraire juste la fonction practitioner_create du fichier
    sed -n '/@login_required/,/^@login_required\|^def\|^class/p' apps/competitions/views/club/practitioners.py | head -n -1 >> manual_deploy_403.txt
    
    echo "" >> manual_deploy_403.txt
    echo "=== Instructions créées dans manual_deploy_403.txt ==="
    echo "Consultez ce fichier pour les instructions de déploiement manuel."
else
    echo "Archive copiée avec succès!"
    
    # Commandes à exécuter sur le serveur
    cat > remote_deploy.sh << 'EOF'
#!/bin/bash
cd /var/www/vhosts/martialcomp.com/httpdocs
echo "Extraction de l'archive..."
tar -xzf fix_403_bundle.tar.gz

echo "Application du patch..."
if [ -f patch_practitioners.py ]; then
    python patch_practitioners.py
else
    echo "patch_practitioners.py non trouvé, application manuelle nécessaire"
fi

echo "Redémarrage du service..."
systemctl restart martialcomp.service

echo "Nettoyage..."
rm -f fix_403_bundle.tar.gz patch_practitioners.py fix_practitioner_403.sh

echo "Déploiement terminé!"
EOF

    echo "3. Exécution du déploiement sur le serveur..."
    ssh -o ConnectTimeout=30 $REMOTE_HOST "cd $REMOTE_PATH && bash -s" < remote_deploy.sh
fi

echo "=== Fin du déploiement ==="
echo ""
echo "URLs de test :"
echo "- https://martialcomp.com/fr/competitions/club/test-permissions/"
echo "- https://martialcomp.com/fr/competitions/club/practitioners/add/"