@echo off
echo === Correction complète des migrations ===
echo.

echo 1. Correction des champs dupliqués...
python fix_duplicate_fields.py

echo.
echo 2. Marquer la migration 0002 comme déjà appliquée...
python manage.py migrate multitenant 0002_add_customization_fields --fake

echo.
echo 3. Application des autres migrations multitenant...
python manage.py migrate multitenant

echo.
echo 4. Application de toutes les migrations...
python manage.py migrate

echo.
echo 5. Vérification finale...
python manage.py showmigrations

echo.
echo 6. Test de migration_status...
python manage.py migration_status

echo.
echo === Terminé ===
pause