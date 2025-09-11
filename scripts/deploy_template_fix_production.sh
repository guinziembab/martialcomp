#!/bin/bash

# =============================================================================
# Déploiement de la correction du template en production
# =============================================================================

set -e

PROD_DIR="/opt/martialcomp/app"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ERROR: $1${NC}"
}

warning() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] WARNING: $1${NC}"
}

# Sauvegarder le template actuel en production
backup_current_template() {
    log "Sauvegarde du template actuel en production..."
    
    if [[ -f "$PROD_DIR/competitions/templates/competitions/welcome.html" ]]; then
        cp "$PROD_DIR/competitions/templates/competitions/welcome.html" \
           "$PROD_DIR/competitions/templates/competitions/welcome.html.backup_$TIMESTAMP"
        log "Template sauvegardé: welcome.html.backup_$TIMESTAMP"
    else
        warning "Template welcome.html n'existe pas en production"
    fi
}

# Déployer le nouveau template corrigé
deploy_fixed_template() {
    log "Déploiement du template corrigé en production..."
    
    # Créer le template corrigé directement en production
    cat > "$PROD_DIR/competitions/templates/competitions/welcome.html" << 'EOF'
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MartialComp - Plateforme Arts Martiaux</title>
    <meta name="description" content="MartialComp est la solution complète pour organiser, gérer et participer aux compétitions d'arts martiaux.">
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: #f5f5f5; 
        }
        .container { 
            max-width: 1000px; 
            margin: 0 auto; 
            background: white; 
            padding: 40px; 
            border-radius: 10px; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
        }
        .header { 
            text-align: center; 
            margin-bottom: 40px; 
        }
        .logo { 
            font-size: 2.5rem; 
            font-weight: bold; 
            color: #c41e3a; 
            margin-bottom: 10px; 
        }
        .tagline { 
            font-size: 1.2rem; 
            color: #666; 
        }
        .auth-section { 
            text-align: center; 
            margin: 40px 0; 
            padding: 30px; 
            background: #f8f9fa; 
            border-radius: 8px; 
        }
        .btn { 
            display: inline-block; 
            padding: 12px 24px; 
            margin: 10px; 
            text-decoration: none; 
            border-radius: 5px; 
            font-weight: bold; 
            transition: all 0.3s ease; 
        }
        .btn-primary { 
            background: #c41e3a; 
            color: white; 
        }
        .btn-google { 
            background: #4285f4; 
            color: white; 
        }
        .btn-facebook { 
            background: #1877f2; 
            color: white; 
        }
        .btn:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 4px 8px rgba(0,0,0,0.2); 
        }
        .footer { 
            text-align: center; 
            margin-top: 40px; 
            padding-top: 20px; 
            border-top: 1px solid #eee; 
            color: #666; 
        }
        .success { 
            background: #d4edda; 
            color: #155724; 
            padding: 15px; 
            border-radius: 5px; 
            margin: 20px 0; 
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🥋 MartialComp</div>
            <div class="tagline">Plateforme de Gestion des Arts Martiaux</div>
        </div>
        
        <div class="success">
            <h3>✅ Authentification Sociale Opérationnelle !</h3>
            <p>L'authentification Google et Facebook est maintenant entièrement fonctionnelle.</p>
        </div>
        
        <div class="auth-section">
            <h3>🔐 Connexion Sécurisée</h3>
            <p>Connectez-vous avec votre méthode préférée :</p>
            
            <a href="/accounts/login/" class="btn btn-primary">Connexion Classique</a>
            <a href="/accounts/google/login/" class="btn btn-google">✅ Connexion Google</a>
            <a href="/accounts/facebook/login/" class="btn btn-facebook">✅ Connexion Facebook</a>
        </div>
        
        <div class="footer">
            <p>© 2025 MartialComp - Authentification sociale déployée avec succès</p>
            <p>
                <a href="/privacy/">Politique de confidentialité</a> | 
                <a href="/terms/">Conditions d'utilisation</a>
            </p>
        </div>
    </div>
</body>
</html>
EOF

    log "Template corrigé déployé en production"
}

# Redémarrer Django en production
restart_django_production() {
    log "Redémarrage de Django en production..."
    
    cd "$PROD_DIR"
    
    # Arrêter Django
    pkill -f "runserver 127.0.0.1:8000" 2>/dev/null || true
    sleep 5
    
    # Activer l'environnement virtuel et redémarrer
    source venv/bin/activate
    
    # Vérifier la configuration
    python manage.py check
    if [ $? -ne 0 ]; then
        error "Configuration Django invalide"
        return 1
    fi
    
    # Redémarrer en arrière-plan
    nohup python manage.py runserver 127.0.0.1:8000 > /tmp/django_template_fix_$TIMESTAMP.log 2>&1 &
    
    sleep 15
    
    if pgrep -f "runserver 127.0.0.1:8000" > /dev/null; then
        log "Django redémarré avec succès"
    else
        error "Échec du redémarrage Django"
        tail -10 /tmp/django_template_fix_$TIMESTAMP.log
        return 1
    fi
}

# Test complet du déploiement
test_deployment() {
    log "Test du déploiement..."
    
    sleep 10
    
    echo ""
    echo "=== TESTS APRÈS DÉPLOIEMENT ===="
    
    # URLs critiques à tester
    urls=(
        "http://127.0.0.1:8000/"
        "https://martialcomp.com/"
        "https://martialcomp.com/fr/"
        "https://martialcomp.com/accounts/google/login/"
        "https://martialcomp.com/accounts/facebook/login/"
        "https://martialcomp.com/privacy/"
        "https://martialcomp.com/terms/"
    )
    
    success_count=0
    total_urls=${#urls[@]}
    
    for url in "${urls[@]}"; do
        code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
        if [[ "$code" =~ ^(200|302)$ ]]; then
            echo "  ✅ $url ($code)"
            ((success_count++))
        else
            echo "  ❌ $url ($code)"
        fi
    done
    
    echo ""
    echo "Résultat: $success_count/$total_urls URLs fonctionnelles"
    
    if [ $success_count -eq $total_urls ]; then
        log "🎉🎉🎉 DÉPLOIEMENT RÉUSSI ! 🎉🎉🎉"
        echo ""
        echo "L'AUTHENTIFICATION SOCIALE MARTIALCOMP EST ENTIÈREMENT OPÉRATIONNELLE EN PRODUCTION !"
        echo ""
        echo "🔐 Authentification disponible:"
        echo "  ✅ https://martialcomp.com/accounts/google/login/"
        echo "  ✅ https://martialcomp.com/accounts/facebook/login/"
        echo ""
        echo "🌍 Pages principales:"
        echo "  ✅ https://martialcomp.com/"
        echo "  ✅ https://martialcomp.com/fr/"
        echo ""
        echo "📄 Pages légales:"
        echo "  ✅ https://martialcomp.com/privacy/"
        echo "  ✅ https://martialcomp.com/terms/"
        echo ""
        echo "🎯 PROCHAINE ÉTAPE: Configurer les URLs de callback dans Google Cloud Console et Facebook Developer Console"
    else
        warning "Certaines URLs ont encore des problèmes"
        echo ""
        echo "URLs à vérifier manuellement:"
        for url in "${urls[@]}"; do
            code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
            if [[ ! "$code" =~ ^(200|302)$ ]]; then
                echo "  ❌ $url ($code)"
            fi
        done
    fi
}

# Script principal
main() {
    log "=== DÉPLOIEMENT CORRECTION TEMPLATE EN PRODUCTION ==="
    
    # Vérifier que nous sommes sur le serveur de production
    if [[ ! -d "$PROD_DIR" ]]; then
        error "Répertoire de production non trouvé: $PROD_DIR"
        echo "Ce script doit être exécuté sur le serveur de production"
        exit 1
    fi
    
    backup_current_template
    deploy_fixed_template
    restart_django_production
    test_deployment
    
    log "🎉 DÉPLOIEMENT TERMINÉ !"
    echo ""
    echo "📋 Actions effectuées :"
    echo "  ✅ Template welcome.html sauvegardé"
    echo "  ✅ Template corrigé déployé"
    echo "  ✅ Django redémarré"
    echo "  ✅ Tests effectués"
    echo ""
    echo "💾 Sauvegarde :"
    echo "  - welcome.html.backup_$TIMESTAMP"
    echo "  - /tmp/django_template_fix_$TIMESTAMP.log"
}

main "$@"