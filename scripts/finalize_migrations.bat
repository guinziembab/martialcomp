@echo off
echo === Finalisation des migrations ===
echo.

echo 1. Ajout du champ is_migrated au modèle Club...
echo    Vérification si le champ existe déjà...
python check_is_migrated_field.py

echo.
echo 2. Création des nouvelles migrations pour competitions et multitenant...
python manage.py makemigrations

echo.
echo 3. Application des nouvelles migrations...
python manage.py migrate

echo.
echo 4. Vérification de toutes les migrations...
python manage.py showmigrations

echo.
echo 5. Test final avec migration_status...
python manage.py migration_status

echo.
echo 6. Vérification complète du système multitenant...
python verify_multitenant_setup.py

echo.
echo === Terminé ===
echo.
echo Si tout s'est bien passé, vous pouvez maintenant :
echo 1. Décommenter DATABASE_ROUTERS dans config/settings.py
echo 2. Migrer les clubs existants : python manage.py migrate_clubs_to_tenants
echo 3. Créer de nouveaux tenants : python manage.py create_tenant
pause