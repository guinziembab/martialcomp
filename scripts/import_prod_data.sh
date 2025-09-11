#!/bin/bash

# Se placer dans le répertoire du projet
cd "$(dirname "$0")/.."

# Vérifier les arguments
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <chemin_dump_db> <chemin_backup_media>"
    echo "Exemple: $0 ./prod_backup.dump ./media_backup.tar.gz"
    exit 1
fi

DB_DUMP=$1
MEDIA_BACKUP=$2

# Vérifier si les fichiers existent
if [ ! -f "$DB_DUMP" ]; then
    echo "Le fichier de dump de la base de données n'existe pas: $DB_DUMP"
    exit 1
fi

if [ ! -f "$MEDIA_BACKUP" ]; then
    echo "Le fichier de backup des médias n'existe pas: $MEDIA_BACKUP"
    exit 1
fi

# Vérifier si l'environnement de pré-production est en cours d'exécution
cd docker/staging
if ! docker-compose ps | grep -q "Up"; then
    echo "L'environnement de pré-production n'est pas en cours d'exécution."
    echo "Démarrez-le d'abord avec: ./scripts/start_staging.sh"
    exit 1
fi

echo "=== Importation des données de production dans l'environnement de staging ==="

# Arrêter les services web et nginx pour éviter les conflits
echo "Arrêt des services web et nginx..."
docker-compose stop web nginx

# Restaurer la base de données
echo "Restauration de la base de données..."
# Copier le dump dans le conteneur
docker cp "../../$DB_DUMP" $(docker-compose ps -q db):/tmp/prod_backup.dump

# Supprimer et recréer la base de données
docker-compose exec db bash -c "dropdb -U martialcomp martialcomp_staging --if-exists"
docker-compose exec db bash -c "createdb -U martialcomp martialcomp_staging"

# Restaurer le dump
docker-compose exec db bash -c "pg_restore -U martialcomp -d martialcomp_staging /tmp/prod_backup.dump"

if [ $? -eq 0 ]; then
    echo "✓ Base de données restaurée avec succès"
else
    echo "✗ Erreur lors de la restauration de la base de données"
    exit 1
fi

# Extraire et copier les fichiers media
echo "Restauration des fichiers media..."
mkdir -p temp_media
tar -xzf "../../$MEDIA_BACKUP" -C temp_media

# Supprimer les anciens fichiers media et copier les nouveaux
docker-compose exec web bash -c "rm -rf /app/media/*"
docker cp temp_media/. $(docker-compose ps -q web):/app/media/
rm -rf temp_media

if [ $? -eq 0 ]; then
    echo "✓ Fichiers media restaurés avec succès"
else
    echo "✗ Erreur lors de la restauration des fichiers media"
fi

# Redémarrer les services
echo "Redémarrage des services..."
docker-compose start web nginx

# Attendre que les services soient prêts
sleep 10

# Exécuter les migrations si nécessaire
echo "Vérification et application des migrations..."
docker-compose exec web python manage.py migrate --settings=config.settings.staging

echo ""
echo "=== Importation des données de production terminée ! ==="
echo "L'environnement de staging contient maintenant les données de production."
echo "Accédez à http://localhost pour vérifier."