#!/bin/bash
echo "=== Application des migrations multitenant ==="
echo

echo "1. Vérification de la structure des fichiers..."
if [ -f "multitenant/migrate_existing_clubs.py" ]; then
    echo "   ATTENTION: migrate_existing_clubs.py trouvé dans le mauvais emplacement!"
    echo "   Exécutez d'abord fix_multitenant_migrations.sh"
    exit 1
fi

echo
echo "2. Création des migrations si nécessaire..."
python manage.py makemigrations multitenant --noinput

echo
echo "3. Application des migrations..."
python manage.py migrate multitenant

echo
echo "4. Vérification du statut..."
python manage.py migration_status

echo
echo "=== Terminé ==="
echo
echo "Pour migrer les clubs existants, utilisez:"
echo "  python manage.py migrate_existing_clubs"
echo
echo "Pour créer un nouveau tenant, utilisez:"
echo "  python manage.py create_tenant"