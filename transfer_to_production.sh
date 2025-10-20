#!/bin/bash

# Script de transfert des corrections vers le serveur de production
# À adapter selon votre méthode de connexion au serveur

echo "🚀 TRANSFERT DES CORRECTIONS VERS LA PRODUCTION"
echo "==============================================="

# Configuration (à adapter selon votre serveur)
SERVER_HOST="martialcomp.com"
SERVER_USER="root"  # À adapter selon votre utilisateur
SERVER_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

echo "📋 Configuration:"
echo "   Serveur: $SERVER_HOST"
echo "   Utilisateur: $SERVER_USER"
echo "   Chemin: $SERVER_PATH"
echo ""

# Vérifier que le package existe
if [ ! -d "production_fix_package" ]; then
    echo "❌ Erreur: Le dossier production_fix_package n'existe pas"
    echo "   Exécutez d'abord la création du package"
    exit 1
fi

echo "📦 Package trouvé: production_fix_package/"
echo ""

# Créer l'archive pour le transfert
echo "📦 Création de l'archive..."
tar -czf practitioner_fix_$(date +%Y%m%d_%H%M%S).tar.gz production_fix_package/
ARCHIVE_NAME="practitioner_fix_$(date +%Y%m%d_%H%M%S).tar.gz"

if [ $? -eq 0 ]; then
    echo "✅ Archive créée: $ARCHIVE_NAME"
else
    echo "❌ Erreur lors de la création de l'archive"
    exit 1
fi

echo ""
echo "🚀 OPTIONS DE TRANSFERT:"
echo "========================"
echo ""
echo "1. Transfert par SCP (recommandé)"
echo "   scp $ARCHIVE_NAME $SERVER_USER@$SERVER_HOST:/tmp/"
echo "   ssh $SERVER_USER@$SERVER_HOST 'cd $SERVER_PATH && tar -xzf /tmp/$ARCHIVE_NAME'"
echo ""
echo "2. Transfert par SFTP"
echo "   sftp $SERVER_USER@$SERVER_HOST"
echo "   put $ARCHIVE_NAME"
echo "   cd $SERVER_PATH"
echo "   tar -xzf $ARCHIVE_NAME"
echo ""
echo "3. Upload via Plesk File Manager"
echo "   - Se connecter à Plesk"
echo "   - Aller dans Fichiers → httpdocs"
echo "   - Uploader $ARCHIVE_NAME"
echo "   - Extraire l'archive"
echo ""
echo "4. Création directe sur le serveur"
echo "   ssh $SERVER_USER@$SERVER_HOST"
echo "   # Créer les fichiers manuellement"
echo ""

# Proposer l'exécution automatique
read -p "🤔 Voulez-vous exécuter le transfert automatique par SCP ? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Début du transfert automatique..."
    
    # Transfert par SCP
    echo "📤 Transfert de l'archive..."
    scp "$ARCHIVE_NAME" "$SERVER_USER@$SERVER_HOST:/tmp/"
    
    if [ $? -eq 0 ]; then
        echo "✅ Archive transférée avec succès"
        
        # Extraction sur le serveur
        echo "📦 Extraction sur le serveur..."
        ssh "$SERVER_USER@$SERVER_HOST" "cd $SERVER_PATH && tar -xzf /tmp/$ARCHIVE_NAME"
        
        if [ $? -eq 0 ]; then
            echo "✅ Archive extraite avec succès"
            
            # Exécution du script d'installation
            echo "🔧 Exécution du script d'installation..."
            ssh "$SERVER_USER@$SERVER_HOST" "cd $SERVER_PATH/production_fix_package && chmod +x install_production_fix.sh && ./install_production_fix.sh"
            
            if [ $? -eq 0 ]; then
                echo "🎉 INSTALLATION TERMINÉE AVEC SUCCÈS!"
                echo ""
                echo "✅ Corrections appliquées:"
                echo "   - Middleware Django BlockPractitionerMiddleware"
                echo "   - Redirection Apache (.htaccess)"
                echo "   - Désinscription du modèle Practitioner de l'admin"
                echo ""
                echo "🧪 Tests à effectuer:"
                echo "   1. https://martialcomp.com/fr/admin/competitions/practitioner/"
                echo "   2. https://martialcomp.com/fr/admin/"
                echo ""
                echo "📊 Monitoring:"
                echo "   ssh $SERVER_USER@$SERVER_HOST 'tail -f /var/log/apache2/error.log'"
            else
                echo "❌ Erreur lors de l'installation"
                echo "   Connectez-vous manuellement pour diagnostiquer:"
                echo "   ssh $SERVER_USER@$SERVER_HOST"
            fi
        else
            echo "❌ Erreur lors de l'extraction"
        fi
    else
        echo "❌ Erreur lors du transfert"
        echo "   Vérifiez votre connexion SSH et les permissions"
    fi
else
    echo "📋 Instructions manuelles:"
    echo ""
    echo "1. Transférez l'archive $ARCHIVE_NAME sur le serveur"
    echo "2. Extrayez-la dans $SERVER_PATH"
    echo "3. Exécutez: cd production_fix_package && ./install_production_fix.sh"
    echo ""
    echo "📞 En cas de problème, consultez README_DEPLOYMENT.md"
fi

echo ""
echo "📁 Fichiers créés:"
echo "   - $ARCHIVE_NAME (archive à transférer)"
echo "   - production_fix_package/ (dossier source)"
echo "   - README_DEPLOYMENT.md (guide détaillé)"