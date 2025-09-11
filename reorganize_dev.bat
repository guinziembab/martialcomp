@echo off
REM ================================================================
REM SCRIPT SIMPLIFIE DE REORGANISATION MARTIALCOMP - DEV WINDOWS
REM ================================================================
echo.
echo ============================================================
echo   REORGANISATION MARTIALCOMP - VERSION SIMPLIFIEE
echo ============================================================
echo.

REM Vérification de base
if not exist "manage.py" (
    echo ERREUR: manage.py non trouve dans %CD%
    echo Veuillez placer ce script dans le dossier racine du projet
    pause
    exit /b 1
)

echo ✅ Projet Django detecte: %CD%
echo.

REM Créer timestamp pour sauvegarde
set "timestamp=%date:~6,4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "timestamp=%timestamp: =0%"
set "BACKUP_DIR=backup_%timestamp%"

echo [1/5] Creation sauvegarde: %BACKUP_DIR%
mkdir "%BACKUP_DIR%" 2>nul
if exist "config\settings\base.py" copy "config\settings\base.py" "%BACKUP_DIR%\" >nul
echo ✅ Sauvegarde creee
echo.

echo [2/5] Creation nouvelle structure...
mkdir apps 2>nul
mkdir scripts 2>nul  
mkdir archives 2>nul
echo ✅ Dossiers crees: apps, scripts, archives
echo.

echo [3/5] Migration des applications Django...
set MOVED=0

if exist "multitenant" (
    if exist "multitenant\__init__.py" (
        move "multitenant" "apps\" >nul 2>&1 && echo ✅ multitenant migre && set /a MOVED+=1
    ) else (
        echo ⚠️ multitenant: pas d'__init__.py
    )
) else (
    echo - multitenant: non trouve
)

if exist "organizations" (
    if exist "organizations\__init__.py" (
        move "organizations" "apps\" >nul 2>&1 && echo ✅ organizations migre && set /a MOVED+=1
    ) else (
        echo ⚠️ organizations: pas d'__init__.py
    )
) else (
    echo - organizations: non trouve
)

if exist "competitions" (
    if exist "competitions\__init__.py" (
        move "competitions" "apps\" >nul 2>&1 && echo ✅ competitions migre && set /a MOVED+=1
    ) else (
        echo ⚠️ competitions: pas d'__init__.py
    )
) else (
    echo - competitions: non trouve
)

if exist "grades" (
    if exist "grades\__init__.py" (
        move "grades" "apps\" >nul 2>&1 && echo ✅ grades migre && set /a MOVED+=1
    ) else (
        echo ⚠️ grades: pas d'__init__.py
    )
) else (
    echo - grades: non trouve
)

if exist "accounts" (
    if exist "accounts\__init__.py" (
        move "accounts" "apps\" >nul 2>&1 && echo ✅ accounts migre && set /a MOVED+=1
    ) else (
        echo ⚠️ accounts: pas d'__init__.py
    )
) else (
    echo - accounts: non trouve
)

if exist "documents" (
    if exist "documents\__init__.py" (
        move "documents" "apps\" >nul 2>&1 && echo ✅ documents migre && set /a MOVED+=1
    ) else (
        echo ⚠️ documents: pas d'__init__.py
    )
) else (
    echo - documents: non trouve
)

echo.
echo ✅ %MOVED% applications migrees vers apps/
echo.

echo [4/5] Migration des scripts et archives...
for /d %%d in (deployment*) do (
    if exist "%%d" move "%%d" "archives\" >nul 2>&1 && echo ✅ %%d archive
)

for %%f in (*.sh cleanup*.py debug*.py) do (
    if exist "%%f" move "%%f" "scripts\" >nul 2>&1 && echo ✅ %%f vers scripts
)

echo ✅ Nettoyage termine
echo.

echo [5/5] Mise a jour configuration Django...
if exist "config\settings\base.py" (
    findstr "sys.path.append" "config\settings\base.py" >nul
    if errorlevel 1 (
        echo ⚠️ Configuration apps/ manquante - modification necessaire
        echo.
        echo IMPORTANT: Ajoutez ces lignes dans config\settings\base.py:
        echo.
        echo import sys
        echo sys.path.append(str(BASE_DIR / 'apps'^)^)
        echo.
        echo Et dans INSTALLED_APPS, utilisez:
        echo 'multitenant',
        echo 'organizations', 
        echo 'competitions',
        echo 'grades',
        echo 'accounts',
        echo 'documents',
        echo.
    ) else (
        echo ✅ Configuration apps/ deja presente
    )
) else (
    echo ❌ config\settings\base.py non trouve
)

echo.
echo ============================================================
echo   🎉 REORGANISATION TERMINEE !
echo ============================================================
echo.
echo NOUVELLE STRUCTURE:
if exist "apps" (
    echo 📁 apps\:
    for /d %%d in (apps\*) do echo   📱 %%~nxd
)
echo.
echo 📁 scripts\: Scripts de maintenance
echo 📁 archives\: Anciens deployments
echo.
echo 💾 SAUVEGARDE: %BACKUP_DIR%\
echo.
echo PROCHAINES ETAPES:
echo 1. Verifiez config\settings\base.py
echo 2. Testez: python manage.py check
echo 3. Si OK: python manage.py runserver
echo.
pause