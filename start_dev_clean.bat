@echo off
echo.
echo === Configuration de l'environnement de developpement ===
echo.

REM Definir la variable d'environnement
set DJANGO_SETTINGS_MODULE=config.settings_dev
echo Environment: DJANGO_SETTINGS_MODULE = %DJANGO_SETTINGS_MODULE%

REM Creer la table de cache si elle n'existe pas
echo.
echo --- Creation de la table de cache ---
python manage_dev.py createcachetable session_cache_table 2>nul
if %errorlevel% == 0 (
    echo OK Table de cache creee ou deja existante
) else (
    echo ! Table de cache peut-etre deja existante, on continue...
)

REM Creer les migrations si necessaire  
echo.
echo --- Creation des migrations ---
python manage_dev.py makemigrations
if %errorlevel% == 0 (
    echo OK Migrations creees ou aucune modification detectee
) else (
    echo X Erreur lors de la creation des migrations
)

REM Appliquer les migrations
echo.
echo --- Application des migrations ---
python manage_dev.py migrate
if %errorlevel% == 0 (
    echo OK Migrations appliquees avec succes
) else (
    echo X Erreur lors de l'application des migrations
    echo Veuillez verifier les messages d'erreur ci-dessus
)

REM Demarrer le serveur
echo.
echo --- Demarrage du serveur de developpement ---
echo Serveur disponible sur: http://127.0.0.1:8000/
echo Appuyez sur Ctrl+C pour arreter le serveur
echo.
python manage_dev.py runserver