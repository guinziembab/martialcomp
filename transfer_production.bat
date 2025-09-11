@echo off
REM Script de transfert vers la production - MartialComp
REM Transfert des corrections vers root@martialcomp.com

echo ========================================
echo TRANSFERT VERS LA PRODUCTION - MARTIALCOMP
echo ========================================

REM Vérification des fichiers à transférer
echo.
echo Fichiers à transférer :
if exist "deploy_production.py" (
    echo [OK] deploy_production.py
) else (
    echo [ERREUR] deploy_production.py manquant
)

if exist "rollback_production.py" (
    echo [OK] rollback_production.py
) else (
    echo [ERREUR] rollback_production.py manquant
)

if exist "verify_production.py" (
    echo [OK] verify_production.py
) else (
    echo [ERREUR] verify_production.py manquant
)

if exist "GUIDE_DEPLOIEMENT_PRODUCTION.md" (
    echo [OK] GUIDE_DEPLOIEMENT_PRODUCTION.md
) else (
    echo [ERREUR] GUIDE_DEPLOIEMENT_PRODUCTION.md manquant
)

if exist "env.production.example" (
    echo [OK] env.production.example
) else (
    echo [ERREUR] env.production.example manquant
)

REM Création du package de transfert
echo.
echo Creation du package de transfert...
set TIMESTAMP=%date:~10,4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set TRANSFER_PACKAGE=martialcomp_production_transfer_%TIMESTAMP%.tar.gz

REM Créer le package tar.gz
tar -czf %TRANSFER_PACKAGE% --exclude=*.pyc --exclude=__pycache__ --exclude=.git --exclude=venv --exclude=env --exclude=*.log --exclude=backup_* --exclude=*.sqlite3 .

if exist "%TRANSFER_PACKAGE%" (
    echo [OK] Package cree: %TRANSFER_PACKAGE%
) else (
    echo [ERREUR] Echec de la creation du package
    goto :error
)

REM Instructions de transfert
echo.
echo ========================================
echo INSTRUCTIONS DE TRANSFERT
echo ========================================
echo.
echo 1. TRANSFERT AUTOMATIQUE (recommandé):
echo ----------------------------------------
echo scp %TRANSFER_PACKAGE% root@martialcomp.com:/tmp/
echo ssh root@martialcomp.com 'cd /var/www/martialcomp && tar -xzf /tmp/%TRANSFER_PACKAGE% && rm /tmp/%TRANSFER_PACKAGE%'
echo.
echo 2. TRANSFERT MANUEL (alternative):
echo -----------------------------------
echo scp -r . root@martialcomp.com:/var/www/martialcomp/
echo.
echo ========================================
echo INSTRUCTIONS POST-TRANSFERT
echo ========================================
echo.
echo 1. Se connecter au serveur:
echo    ssh root@martialcomp.com
echo.
echo 2. Aller dans le repertoire:
echo    cd /var/www/martialcomp
echo.
echo 3. Configurer l'environnement:
echo    cp env.production.example .env.production
echo    nano .env.production
echo.
echo 4. Installer Redis:
echo    sudo apt update && sudo apt install redis-server
echo    sudo systemctl start redis && sudo systemctl enable redis
echo.
echo 5. Lancer le deploiement:
echo    python deploy_production.py
echo.
echo 6. Verifier le deploiement:
echo    python verify_production.py
echo.
echo ========================================
echo TRANSFERT PRET !
echo ========================================
echo.
echo Package cree: %TRANSFER_PACKAGE%
echo.
echo Prochaines etapes:
echo 1. Transférer le package vers le serveur
echo 2. Se connecter au serveur
echo 3. Extraire et configurer
echo 4. Lancer le deploiement
echo.
echo Support: Consultez GUIDE_DEPLOIEMENT_PRODUCTION.md
echo.
pause
goto :end

:error
echo.
echo [ERREUR] Une erreur s'est produite
pause
exit /b 1

:end
echo.
echo Transfert termine !
pause
