@echo off
REM Script pour réparer tous les problèmes liés à l'internationalisation

echo.
echo =================================================
echo Réparation de l'internationalisation MartialComp
echo =================================================
echo.

REM Activer l'environnement virtuel si existant
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo * Environnement virtuel activé
) else (
    echo AVERTISSEMENT: Environnement virtuel non trouvé
)

echo.
echo ÉTAPE 1: Sauvegarde des fichiers existants
echo ---------------------------------------
echo.

REM Créer un dossier de sauvegarde avec horodatage
set TIMESTAMP=%date:~6,4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%
set TIMESTAMP=%TIMESTAMP: =0%
set BACKUP_DIR=locale_backup_%TIMESTAMP%

if not exist %BACKUP_DIR% (
    mkdir %BACKUP_DIR%
    echo * Dossier de sauvegarde créé: %BACKUP_DIR%
)

REM Copier tous les fichiers de traduction dans la sauvegarde
xcopy /E /I /Y locale %BACKUP_DIR%\locale
echo * Fichiers de traduction sauvegardés

echo.
echo ÉTAPE 2: Installation de polib
echo -------------------------
echo.

python -m pip install polib
echo * Bibliothèque polib installée ou déjà présente

echo.
echo ÉTAPE 3: Correction des problèmes d'encodage
echo --------------------------------------
echo.

python fix_encoding.py fr
echo.

echo ÉTAPE 4: Correction des fichiers MO corrompus
echo ---------------------------------------
echo.

python fix_corrupted_mo.py fr
echo.

echo ÉTAPE 5: Recompilation de tous les fichiers de traduction
echo -------------------------------------------------
echo.

python recompile_translations.py
echo.

echo ÉTAPE 6: Vérification des traductions
echo -------------------------------
echo.

python debug_translations.py
echo.

echo =================================================
echo RÉPARATION TERMINÉE
echo =================================================
echo.
echo Les problèmes d'internationalisation devraient être résolus.
echo Vous pouvez maintenant démarrer votre serveur Django:
echo.
echo    python manage.py runserver
echo.

pause