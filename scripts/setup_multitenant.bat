@echo off
echo === CONFIGURATION MULTI-TENANT ===
echo.

echo 1. Creation des migrations...
python manage.py makemigrations multitenant

echo.
echo 2. Creation des migrations pour competitions...
python manage.py makemigrations competitions

echo.
echo 3. Application des migrations...
:: Appliquer d'abord les migrations de multitenant
python manage.py migrate multitenant

:: Puis les autres migrations
python manage.py migrate

echo.
echo 4. Verification de l'etat...
python manage.py migration_status

echo.
echo === Configuration terminee ===
pause