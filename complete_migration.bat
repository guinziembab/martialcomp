@echo off
REM ================================================================
REM SCRIPT DE CORRECTION - APPLICATIONS MANQUANTES
REM ================================================================
echo.
echo ============================================================
echo   CORRECTION - MIGRATION DES APPLICATIONS MANQUANTES
echo ============================================================
echo.

REM Vérification que nous sommes dans le bon répertoire
if not exist "manage.py" (
    echo ❌ ERREUR: manage.py non trouvé
    pause
    exit /b 1
)

if not exist "apps" (
    echo ❌ ERREUR: Dossier apps/ non trouvé
    echo Exécutez d'abord le script de réorganisation principal
    pause
    exit /b 1
)

echo ✅ Environnement vérifié
echo 📁 Répertoire: %CD%
echo.

echo [1/3] Vérification des applications existantes dans apps/...
echo Applications déjà migrées:
for /d %%d in (apps\*) do echo   ✅ %%~nxd

echo.

echo [2/3] Recherche et migration des applications manquantes...
set "MIGRATED=0"
set "MISSING_APPS=shop family_management security permissions_manager payment finances accounts"

for %%a in (%MISSING_APPS%) do (
    if exist "%%a" (
        echo.
        echo Application trouvée: %%a
        
        REM Vérifier la structure de l'application
        if exist "%%a\__init__.py" (
            echo   ✅ __init__.py: OUI
        ) else (
            echo   ⚠️ __init__.py: NON - Création automatique
            echo # %%a application > "%%a\__init__.py"
        )
        
        if exist "%%a\models.py" (
            echo   ✅ models.py: OUI
        ) else (
            echo   ⚠️ models.py: NON
        )
        
        if exist "%%a\apps.py" (
            echo   ✅ apps.py: OUI
        ) else (
            echo   ⚠️ apps.py: NON - Création automatique
            (
                echo from django.apps import AppConfig
                echo.
                echo class %%aConfig^(AppConfig^):
                echo     default_auto_field = 'django.db.models.BigAutoField'
                echo     name = '%%a'
            ) > "%%a\apps.py"
        )
        
        REM Migration vers apps/
        echo   🔄 Migration %%a → apps\%%a
        move "%%a" "apps\" >nul 2>&1
        if exist "apps\%%a" (
            echo   ✅ Migration réussie
            set /a MIGRATED+=1
        ) else (
            echo   ❌ Échec migration
        )
    ) else (
        echo ❌ %%a: Non trouvé dans la racine
    )
)

echo.
echo ✅ %MIGRATED% applications supplémentaires migrées
echo.

echo [3/3] Vérification finale de la structure apps/...
echo.
echo 📁 STRUCTURE FINALE apps/:
for /d %%d in (apps\*) do (
    echo   📱 %%~nxd
    if exist "apps\%%~nxd\__init__.py" (
        echo      ✅ __init__.py
    ) else (
        echo      ❌ __init__.py manquant
    )
    if exist "apps\%%~nxd\models.py" (
        echo      ✅ models.py
    ) else (
        echo      ⚠️ models.py manquant
    )
)

echo.
echo ============================================================
echo   🎉 CORRECTION TERMINÉE !
echo ============================================================
echo.
echo 📊 RÉSUMÉ:
echo   • Applications dans apps/: 
for /d %%d in (apps\*) do echo     - %%~nxd
echo.
echo 🔄 PROCHAINES ÉTAPES:
echo   1. Vérifiez config\settings\base.py
echo   2. Ajustez INSTALLED_APPS pour inclure toutes les apps
echo   3. Testez: python manage.py check
echo   4. Si OK: python manage.py runserver
echo.
echo 📝 INSTALLED_APPS suggéré:
echo INSTALLED_APPS = [
echo     # Django core apps...
echo     'multitenant',
echo     'organizations',
echo     'competitions',
echo     'grades',
echo     'documents',
echo     'accounts',
if exist "apps\shop" echo     'shop',
if exist "apps\family_management" echo     'family_management',
if exist "apps\security" echo     'security',
if exist "apps\permissions_manager" echo     'permissions_manager',
if exist "apps\payment" echo     'payment',
if exist "apps\finances" echo     'finances',
echo ]
echo.
pause