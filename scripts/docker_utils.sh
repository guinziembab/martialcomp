#!/bin/bash

# Script utilitaire pour les opérations Docker courantes dans MartialComp

SCRIPT_DIR="$(dirname "$0")"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

show_help() {
    echo "Utilitaires Docker pour MartialComp"
    echo ""
    echo "Usage: $0 [COMMANDE] [ENVIRONNEMENT]"
    echo ""
    echo "COMMANDES:"
    echo "  start       Démarrer l'environnement"
    echo "  stop        Arrêter l'environnement"
    echo "  restart     Redémarrer l'environnement"
    echo "  logs        Voir les logs"
    echo "  shell       Ouvrir un shell Django"
    echo "  migrate     Exécuter les migrations"
    echo "  createsuperuser  Créer un superutilisateur"
    echo "  collectstatic    Collecter les fichiers statiques"
    echo "  backup      Créer une sauvegarde de la base de données"
    echo "  clean       Nettoyer les conteneurs et volumes"
    echo "  rebuild     Reconstruire les images"
    echo "  status      Voir le statut des conteneurs"
    echo ""
    echo "ENVIRONNEMENTS:"
    echo "  dev         Développement (par défaut)"
    echo "  staging     Pré-production"
    echo ""
    echo "EXEMPLES:"
    echo "  $0 start dev        # Démarrer l'environnement de développement"
    echo "  $0 logs staging     # Voir les logs de staging"
    echo "  $0 shell dev        # Ouvrir un shell Django en développement"
    echo "  $0 migrate staging  # Exécuter les migrations en staging"
}

get_compose_file() {
    local env=$1
    echo "$PROJECT_DIR/docker/$env/docker-compose.yml"
}

get_settings_module() {
    local env=$1
    case $env in
        "dev")
            echo "config.settings.development"
            ;;
        "staging")
            echo "config.settings.staging"
            ;;
        "prod")
            echo "config.settings.production"
            ;;
        *)
            echo "config.settings.development"
            ;;
    esac
}

run_command() {
    local command=$1
    local env=${2:-dev}
    local compose_file=$(get_compose_file $env)
    local settings=$(get_settings_module $env)
    
    if [ ! -f "$compose_file" ]; then
        echo "Erreur: Fichier docker-compose non trouvé pour l'environnement '$env'"
        echo "Fichier attendu: $compose_file"
        exit 1
    fi
    
    cd "$(dirname "$compose_file")"
    
    case $command in
        "start")
            echo "Démarrage de l'environnement $env..."
            docker-compose up -d
            ;;
        "stop")
            echo "Arrêt de l'environnement $env..."
            docker-compose down
            ;;
        "restart")
            echo "Redémarrage de l'environnement $env..."
            docker-compose restart
            ;;
        "logs")
            docker-compose logs -f
            ;;
        "shell")
            echo "Ouverture du shell Django pour $env..."
            docker-compose exec web python manage.py shell --settings=$settings
            ;;
        "migrate")
            echo "Exécution des migrations pour $env..."
            docker-compose exec web python manage.py migrate --settings=$settings
            ;;
        "createsuperuser")
            echo "Création d'un superutilisateur pour $env..."
            docker-compose exec web python manage.py createsuperuser --settings=$settings
            ;;
        "collectstatic")
            echo "Collecte des fichiers statiques pour $env..."
            docker-compose exec web python manage.py collectstatic --noinput --settings=$settings
            ;;
        "backup")
            echo "Création d'une sauvegarde de la base de données pour $env..."
            backup_file="backup_${env}_$(date +%Y%m%d_%H%M%S).sql"
            docker-compose exec db pg_dump -U martialcomp martialcomp_${env} > "$PROJECT_DIR/$backup_file"
            echo "Sauvegarde créée: $backup_file"
            ;;
        "clean")
            echo "Nettoyage des conteneurs et volumes pour $env..."
            docker-compose down -v
            docker-compose rm -f
            ;;
        "rebuild")
            echo "Reconstruction des images pour $env..."
            docker-compose build --no-cache
            ;;
        "status")
            echo "Statut des conteneurs pour $env:"
            docker-compose ps
            ;;
        *)
            echo "Commande inconnue: $command"
            show_help
            exit 1
            ;;
    esac
}

# Vérifier les arguments
if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

if [ "$1" = "help" ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_help
    exit 0
fi

# Vérifier si Docker est installé
if ! command -v docker &> /dev/null; then
    echo "Erreur: Docker n'est pas installé."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Erreur: Docker Compose n'est pas installé."
    exit 1
fi

# Exécuter la commande
run_command "$1" "$2"