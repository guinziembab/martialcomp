@echo off
echo === Gestion des migrations problématiques ===
echo.

echo 1. Marquage de la migration 0004 comme déjà appliquée...
python manage.py migrate multitenant 0004_remove_tenant_logo_remove_tenant_primary_color_and_more --fake

echo.
echo 2. Application de la migration competitions...
python manage.py migrate competitions 0013_alter_club_country_alter_club_tenant

echo.
echo 3. Vérification de l'état des migrations...
python manage.py showmigrations

echo.
echo 4. Création du champ is_migrated s'il n'existe pas...
python manage.py dbshell -c "ALTER TABLE competitions_club ADD COLUMN IF NOT EXISTS is_migrated BOOLEAN DEFAULT FALSE;"

echo.
echo 5. Test final...
python manage.py migration_status

echo.
echo === Terminé ===
pause