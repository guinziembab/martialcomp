#!/bin/bash

################################################################################
# SCRIPT D'INSTALLATION RAPIDE - CORRECTIONS PRODUCTION
################################################################################

echo "🚀 INSTALLATION RAPIDE DES CORRECTIONS MARTIALCOMP"
echo "================================================="
echo ""

# Vérifications préliminaires
if [ ! -f "deploy_production_corrections_final.sh" ]; then
    echo "❌ Script deploy_production_corrections_final.sh non trouvé"
    echo "📋 Assurez-vous d'être dans le bon répertoire"
    exit 1
fi

if [ ! -f "validate_production_deployment.py" ]; then
    echo "❌ Script validate_production_deployment.py non trouvé"
    exit 1
fi

# Vérifier si on est sur le serveur de production
if [ ! -d "/var/www/vhosts/martialcomp.com/httpdocs" ]; then
    echo "⚠️ Répertoire de production non détecté"
    echo "📋 Ce script est conçu pour le serveur de production"
    echo ""
    read -p "Voulez-vous continuer quand même? (y/N): " continue_anyway
    if [[ ! $continue_anyway =~ ^[Yy]$ ]]; then
        echo "Installation annulée"
        exit 0
    fi
fi

echo "📋 INFORMATIONS:"
echo "   📂 Répertoire de production: /var/www/vhosts/martialcomp.com/httpdocs"
echo "   📝 Scripts disponibles:"
echo "      - deploy_production_corrections_final.sh"
echo "      - validate_production_deployment.py"
echo ""

# Rendre les scripts exécutables
chmod +x deploy_production_corrections_final.sh
chmod +x validate_production_deployment.py

echo "✅ Scripts rendus exécutables"
echo ""

# Menu d'options
echo "🔧 OPTIONS D'INSTALLATION:"
echo "========================="
echo ""
echo "1. Installation complète automatique (recommandé)"
echo "2. Installation manuelle étape par étape"
echo "3. Validation uniquement (si déjà installé)"
echo "4. Afficher les instructions manuelles"
echo "5. Quitter"
echo ""

read -p "Votre choix (1-5): " choice

case $choice in
    1)
        echo ""
        echo "🚀 INSTALLATION COMPLÈTE AUTOMATIQUE"
        echo "===================================="
        echo ""
        echo "📋 Cette installation va:"
        echo "   ✅ Sauvegarder les fichiers existants"
        echo "   ✅ Corriger le système d'onboarding"
        echo "   ✅ Implémenter le système de notifications"
        echo "   ✅ Mettre à jour la base de données"
        echo "   ✅ Redémarrer le serveur"
        echo "   ✅ Valider le déploiement"
        echo ""
        
        read -p "Confirmer l'installation? (y/N): " confirm
        if [[ $confirm =~ ^[Yy]$ ]]; then
            echo ""
            echo "🔄 Début de l'installation..."
            
            # Exécuter le déploiement
            sudo ./deploy_production_corrections_final.sh
            
            if [ $? -eq 0 ]; then
                echo ""
                echo "✅ Déploiement terminé!"
                echo "🔍 Lancement de la validation..."
                echo ""
                
                # Changer vers le répertoire de production pour la validation
                cd /var/www/vhosts/martialcomp.com/httpdocs
                
                # Exécuter la validation
                python3 "$(dirname "$0")/validate_production_deployment.py"
                
                if [ $? -eq 0 ]; then
                    echo ""
                    echo "🎉 INSTALLATION RÉUSSIE AVEC SUCCÈS!"
                    echo ""
                    echo "🌐 Votre site est maintenant accessible:"
                    echo "   🏠 https://martialcomp.com/fr/"
                    echo "   🔧 https://martialcomp.com/admin/"
                    echo ""
                    echo "🔐 Compte administrateur:"
                    echo "   👤 Username: admin"
                    echo "   🔑 Password: admin123"
                else
                    echo ""
                    echo "⚠️ Installation terminée avec des avertissements"
                    echo "📋 Consultez les logs pour plus de détails"
                fi
            else
                echo ""
                echo "❌ Erreur lors du déploiement"
                echo "📋 Consultez les logs pour diagnostiquer le problème"
            fi
        else
            echo "Installation annulée"
        fi
        ;;
        
    2)
        echo ""
        echo "🔧 INSTALLATION MANUELLE"
        echo "======================="
        echo ""
        echo "Étapes à suivre:"
        echo ""
        echo "1. Exécuter le déploiement:"
        echo "   sudo ./deploy_production_corrections_final.sh"
        echo ""
        echo "2. Attendre la fin du déploiement"
        echo ""
        echo "3. Valider l'installation:"
        echo "   cd /var/www/vhosts/martialcomp.com/httpdocs"
        echo "   python3 $(pwd)/validate_production_deployment.py"
        echo ""
        echo "4. Tester les URLs:"
        echo "   - https://martialcomp.com/fr/"
        echo "   - https://martialcomp.com/admin/"
        echo ""
        ;;
        
    3)
        echo ""
        echo "🔍 VALIDATION UNIQUEMENT"
        echo "======================"
        echo ""
        
        cd /var/www/vhosts/martialcomp.com/httpdocs
        python3 "$(dirname "$0")/validate_production_deployment.py"
        ;;
        
    4)
        echo ""
        echo "📋 INSTRUCTIONS MANUELLES COMPLÈTES"
        echo "=================================="
        echo ""
        echo "PRÉREQUIS:"
        echo "- Accès SSH au serveur de production"
        echo "- Droits sudo"
        echo "- Environnement virtuel Python activé"
        echo ""
        echo "ÉTAPES:"
        echo ""
        echo "1. Transférer les fichiers sur le serveur:"
        echo "   scp deploy_production_corrections_final.sh user@serveur:/tmp/"
        echo "   scp validate_production_deployment.py user@serveur:/tmp/"
        echo ""
        echo "2. Se connecter au serveur:"
        echo "   ssh user@serveur"
        echo ""
        echo "3. Rendre les scripts exécutables:"
        echo "   chmod +x /tmp/deploy_production_corrections_final.sh"
        echo "   chmod +x /tmp/validate_production_deployment.py"
        echo ""
        echo "4. Exécuter le déploiement:"
        echo "   sudo /tmp/deploy_production_corrections_final.sh"
        echo ""
        echo "5. Valider l'installation:"
        echo "   cd /var/www/vhosts/martialcomp.com/httpdocs"
        echo "   python3 /tmp/validate_production_deployment.py"
        echo ""
        echo "6. Tester le site:"
        echo "   - Ouvrir https://martialcomp.com/fr/"
        echo "   - Se connecter sur https://martialcomp.com/admin/"
        echo "   - Utiliser: admin / admin123"
        echo ""
        echo "EN CAS DE PROBLÈME:"
        echo "- Consulter les logs dans /tmp/"
        echo "- Restaurer depuis la sauvegarde si nécessaire"
        echo "- Contacter le support technique"
        echo ""
        ;;
        
    5)
        echo "Installation annulée"
        exit 0
        ;;
        
    *)
        echo "❌ Option invalide"
        exit 1
        ;;
esac

echo ""
echo "📋 INFORMATIONS UTILES:"
echo "====================="
echo ""
echo "📁 Logs d'installation: /tmp/production_correction_*.log"
echo "💾 Sauvegardes: /tmp/backup_production_*/"
echo "📝 Serveur Django: /tmp/django_production_corrected.log"
echo ""
echo "🔗 URLs importantes:"
echo "   🏠 Site principal: https://martialcomp.com/fr/"
echo "   🔧 Administration: https://martialcomp.com/admin/"
echo "   🔔 Notifications: https://martialcomp.com/fr/competitions/notifications/"
echo ""
echo "Date: $(date)"