@echo off
REM ================================================================
REM SCRIPT DE DIAGNOSTIC MARTIALCOMP - VERSION DEBUG
REM ================================================================
chcp 65001 >nul
echo.
echo ============================================================
echo   DIAGNOSTIC MARTIALCOMP - ENVIRONNEMENT DEV
echo ============================================================
echo.

echo DEBUG: Debut du script
echo DEBUG: Repertoire actuel: %CD%
echo.

REM Test 1: Vérification manage.py
echo [TEST 1] Verification manage.py...
if exist "manage.py" (
    echo ✅ manage.py trouve
) else (
    echo ❌ manage.py NON TROUVE
    echo Contenu du repertoire:
    dir /b
    echo.
    echo ERREUR: Vous devez etre dans le dossier racine du projet Django
    pause
    exit /b 1
)

REM Test 2: Vérification des applications Django
echo [TEST 2] Recherche des applications Django...
set "APPS_DETECTEES=0"
set "DJANGO_APPS=multitenant organizations competitions grades shop finances payment accounts documents"

for %%a in (%DJANGO_APPS%) do (
    if exist "%%a" (
        echo   ✅ %%a trouve
        if exist "%%a\__init__.py" (
            echo      - __init__.py: OUI
        ) else (
            echo      - __init__.py: NON
        )
        if exist "%%a\models.py" (
            echo      - models.py: OUI
        ) else (
            echo      - models.py: NON
        )
        set /a APPS_DETECTEES+=1
    ) else (
        echo   ❌ %%a non trouve
    )
)

echo.
echo RESUME: %APPS_DETECTEES% applications Django detectees
echo.

REM Test 3: Vérification config/settings
echo [TEST 3] Verification configuration...
if exist "config\settings\base.py" (
    echo ✅ config\settings\base.py trouve
    echo Taille du fichier:
    dir "config\settings\base.py" | findstr "base.py"
) else (
    echo ❌ config\settings\base.py NON TROUVE
    echo Structure config:
    if exist "config" (
        dir /b config
    ) else (
        echo   Dossier config n'existe pas !
    )
)

echo.

REM Test 4: Vérification Python
echo [TEST 4] Verification Python...
python --version 2>nul
if errorlevel 1 (
    echo ❌ Python non accessible
) else (
    echo ✅ Python accessible
)

echo.

REM Test 5: Test rapide Django
echo [TEST 5] Test rapide Django...
python -c "import django; print('Django version:', django.get_version())" 2>nul
if errorlevel 1 (
    echo ❌ Django non accessible
) else (
    echo ✅ Django accessible
)

echo.

REM Test 6: Permissions d'écriture
echo [TEST 6] Test permissions ecriture...
echo test > test_write.tmp 2>nul
if exist "test_write.tmp" (
    echo ✅ Permissions ecriture OK
    del test_write.tmp
) else (
    echo ❌ Pas de permissions ecriture
)

echo.
echo ============================================================
echo   DIAGNOSTIC TERMINE
echo ============================================================
echo.
echo Si tous les tests sont ✅, le probleme vient du script principal.
echo Si certains tests sont ❌, corrigez d'abord ces problemes.
echo.
pause