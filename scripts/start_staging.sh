#!/bin/bash

# Se placer dans le répertoire du projet
cd "$(dirname "$0")/.."

# Vérifier si Docker est installé
if ! command -v docker &> /dev/null; then
    echo "Docker n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

# Vérifier si Docker Compose est installé
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

# Vérifier si Docker est en cours d'exécution
if ! docker info &> /dev/null; then
    echo "Docker n'est pas en cours d'exécution. Veuillez le démarrer d'abord."
    exit 1
fi

# Charger les variables d'environnement
if [ -f "docker/staging/.env" ]; then
    source docker/staging/.env
else
    echo "Fichier .env manquant. Veuillez le créer d'abord dans docker/staging/.env"
    echo "Exemple de contenu :"
    echo "DJANGO_SECRET_KEY=votre_cle_secrete_staging"
    echo "DB_PASSWORD=stagingpassword"
    exit 1
fi

echo "=== Démarrage de l'environnement de pré-production MartialComp ==="

# Démarrer l'environnement de pré-production
cd docker/staging
echo "Construction et démarrage des conteneurs..."
docker-compose up -d --build

# Attendre que la base de données soit prête
echo "Attente de la disponibilité de la base de données..."
sleep 20

# Vérifier si les conteneurs sont en cours d'exécution
if ! docker-compose ps | grep -q "Up"; then
    echo "Erreur: Les conteneurs ne sont pas en cours d'exécution."
    docker-compose logs
    exit 1
fi

# Exécuter les migrations
echo "Exécution des migrations..."
docker-compose exec web python manage.py migrate --settings=config.settings.staging

# Créer les répertoires logs s'ils n'existent pas
docker-compose exec web mkdir -p /app/logs

# Collecter les fichiers statiques
echo "Collecte des fichiers statiques..."
docker-compose exec web python manage.py collectstatic --noinput --settings=config.settings.staging

echo ""
echo "=== Environnement de pré-production prêt ! ==="
echo "Accédez à http://localhost dans votre navigateur."
echo ""
echo "Commandes utiles :"
echo "  Voir les logs: docker-compose logs -f"
echo "  Arrêter: docker-compose down"
echo "  Shell Django: docker-compose exec web python manage.py shell"
echo "  Importer des données: ./scripts/import_prod_data.sh <dump_db> <backup_media>"