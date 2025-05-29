@echo off
echo === Correction finale du module multitenant ===
echo.

echo 1. Vérification que DATABASE_ROUTERS est commenté...
echo    Si ce n'est pas fait, commentez DATABASE_ROUTERS dans config/settings.py
echo    Appuyez sur une touche quand c'est fait...
pause

echo.
echo 2. Correction complète du router...
python fix_router_complete.py

echo.
echo 3. Nettoyage du cache Python...
if exist multitenant\__pycache__ rd /s /q multitenant\__pycache__
if exist multitenant\migrations\__pycache__ rd /s /q multitenant\migrations\__pycache__

echo.
echo 4. Création des migrations multitenant...
python manage.py makemigrations multitenant --noinput

echo.
echo 5. Application des migrations multitenant...
python manage.py migrate multitenant --noinput

echo.
echo 6. Création des autres migrations...
python manage.py makemigrations --noinput

echo.
echo 7. Application de toutes les migrations...
python manage.py migrate --noinput

echo.
echo 8. Test des migrations...
python manage.py showmigrations multitenant

echo.
echo 9. Réactivation du router...
echo    IMPORTANT: Décommentez DATABASE_ROUTERS dans config/settings.py
echo    Appuyez sur une touche quand c'est fait...
pause

echo.
echo === Terminé ===
echo.
echo Pour vérifier que tout fonctionne :
echo 1. python manage.py showmigrations
echo 2. python manage.py migration_status
pause