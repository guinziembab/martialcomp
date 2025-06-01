@echo off
echo === Configuration complète du module multitenant ===
echo.

echo 1. Nettoyage du cache Python...
if exist multitenant\__pycache__ (
    rd /s /q multitenant\__pycache__
)
if exist multitenant\migrations\__pycache__ (
    rd /s /q multitenant\migrations\__pycache__
)

echo.
echo 2. Création des migrations...
python manage.py makemigrations multitenant

echo.
echo 3. Affichage des migrations à appliquer...
python manage.py showmigrations multitenant

echo.
echo 4. Application des migrations...
python manage.py migrate multitenant

echo.
echo 5. Ajout du champ is_migrated au modèle Club...
echo    (Cette étape nécessite une migration dans l'app competitions)
python manage.py makemigrations competitions --name add_is_migrated_field

echo.
echo 6. Application de la migration Club...
python manage.py migrate competitions

echo.
echo 7. Vérification finale...
python manage.py migration_status

echo.
echo === Configuration terminée ===
echo.
echo Prochaines étapes :
echo 1. Migrer les clubs existants : python manage.py migrate_existing_clubs
echo 2. Créer un tenant : python manage.py create_tenant
echo 3. Tester l'isolement : python manage.py test_tenant_isolation
pause