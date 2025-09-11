@echo off
echo === Nettoyage complet des migrations multitenant ===
echo.

echo 1. Déplacement des fichiers non-migration...
if exist multitenant\migrations\progressive_migration.py (
    mkdir multitenant\scripts 2>nul
    move multitenant\migrations\progressive_migration.py multitenant\scripts\progressive_migration.py
    echo    - progressive_migration.py déplacé vers scripts/
)

echo.
echo 2. Correction du router...
python fix_multitenant_router.py

echo.
echo 3. Nettoyage du cache Python...
if exist multitenant\__pycache__ rd /s /q multitenant\__pycache__
if exist multitenant\migrations\__pycache__ rd /s /q multitenant\migrations\__pycache__

echo.
echo 4. Création des migrations...
python manage.py makemigrations multitenant --noinput

echo.
echo 5. Application des migrations...
python manage.py migrate multitenant --noinput

echo.
echo 6. Vérification...
python manage.py showmigrations multitenant

echo.
echo === Terminé ===
pause