@echo off
echo === Configuration finale du système multitenant ===
echo.

echo 1. Ajout du champ is_migrated au modèle Club...
python add_is_migrated_to_club.py

echo.
echo 2. Création des nouvelles migrations...
python manage.py makemigrations

echo.
echo 3. Application des migrations...
python manage.py migrate

echo.
echo 4. Vérification de toutes les migrations...
python manage.py showmigrations

echo.
echo 5. Vérification complète du système...
python verify_multitenant_setup.py

echo.
echo 6. Test final avec migration_status...
python manage.py migration_status

echo.
echo === Configuration terminée ===
echo.
echo IMPORTANT : 
echo 1. Décommentez DATABASE_ROUTERS dans config/settings.py si ce n'est pas déjà fait
echo 2. Redémarrez votre serveur Django
echo.
echo Vous pouvez maintenant :
echo - Migrer les clubs : python manage.py migrate_clubs_to_tenants
echo - Créer de nouveaux tenants : python manage.py create_tenant
echo - Tester l'isolement : python manage.py test_tenant_isolation
pause