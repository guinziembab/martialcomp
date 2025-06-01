@echo off
echo === Correction complète du module multitenant ===
echo.

echo 1. Correction du router multitenant...
python fix_multitenant_router.py

echo.
echo 2. Désactivation temporaire du router dans les settings...
echo    IMPORTANT: Commentez temporairement DATABASE_ROUTERS dans settings.py
echo    Appuyez sur une touche quand c'est fait...
pause

echo.
echo 3. Déplacement des fichiers non-migration...
if exist multitenant\migrations\progressive_migration.py (
    mkdir multitenant\scripts 2>nul
    move multitenant\migrations\progressive_migration.py multitenant\scripts\progressive_migration.py
    echo    - progressive_migration.py déplacé
)

echo.
echo 4. Nettoyage du cache...
if exist multitenant\__pycache__ rd /s /q multitenant\__pycache__
if exist multitenant\migrations\__pycache__ rd /s /q multitenant\migrations\__pycache__

echo.
echo 5. Création des tables Django de base...
python manage.py migrate --noinput

echo.
echo 6. Création des migrations multitenant...
python manage.py makemigrations multitenant --noinput

echo.
echo 7. Application des migrations multitenant...
python manage.py migrate multitenant --noinput

echo.
echo 8. Réactivation du router...
echo    IMPORTANT: Décommentez DATABASE_ROUTERS dans settings.py
echo    Appuyez sur une touche quand c'est fait...
pause

echo.
echo 9. Test final...
python manage.py showmigrations multitenant

echo.
echo === Terminé ===
echo.
echo Si tout s'est bien passé, vous pouvez maintenant :
echo 1. Exécuter: python manage.py migration_status
echo 2. Migrer les clubs: python manage.py migrate_existing_clubs
pause