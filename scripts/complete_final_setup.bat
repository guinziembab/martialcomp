@echo off
echo === Configuration finale complète ===
echo.

echo 1. Ajout des colonnes manquantes directement dans la BD...
python add_missing_columns.py

echo.
echo 2. Marquage des migrations comme appliquées...
echo    - Multitenant 0004...
python manage.py migrate multitenant 0004_remove_tenant_logo_remove_tenant_primary_color_and_more --fake

echo.
echo    - Competitions 0013...
python manage.py migrate competitions 0013_alter_club_country_alter_club_tenant --fake

echo.
echo 3. Vérification de toutes les migrations...
python manage.py showmigrations

echo.
echo 4. Test final du système...
python manage.py migration_status

echo.
echo === Configuration terminée ===
echo.
echo Le système multitenant est maintenant configuré !
echo.
echo Prochaines étapes :
echo 1. Décommentez DATABASE_ROUTERS dans config/settings.py
echo 2. Redémarrez votre serveur Django
echo 3. Migrez les clubs : python manage.py migrate_clubs_to_tenants
echo 4. Créez de nouveaux tenants : python manage.py create_tenant
pause