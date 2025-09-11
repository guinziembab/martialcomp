@echo off
REM Script automatique de traduction PO vers arabe
REM MartialComp - Traduction batch Windows

echo ================================================
echo    TRADUCTEUR AUTOMATIQUE PO VERS ARABE
echo              MartialComp 2025
echo ================================================
echo.

REM Vérifier Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python non installé ou non trouvé dans PATH
    echo 💡 Installez Python depuis https://python.org
    pause
    exit /b 1
)

echo ✅ Python détecté
echo.

REM Aller dans le répertoire du script
cd /d "%~dp0"
echo 📁 Répertoire de travail: %CD%

REM Installer les dépendances
echo.
echo 📦 Installation des dépendances...
pip install polib requests --quiet
if errorlevel 1 (
    echo ❌ Erreur lors de l'installation des dépendances
    pause
    exit /b 1
)

echo ✅ Dépendances installées
echo.

REM Exécuter le script de traduction
echo 🚀 Lancement de la traduction automatique...
echo.
python translate_po_to_arabic.py

REM Vérifier le résultat
if errorlevel 1 (
    echo.
    echo ❌ Erreur lors de la traduction
    echo 📋 Vérifiez les messages d'erreur ci-dessus
) else (
    echo.
    echo ✅ Traduction terminée avec succès!
    echo.
    echo 📁 Fichiers générés:
    echo    - locale\ar\LC_MESSAGES\django.po (traduit)
    echo    - locale\ar\LC_MESSAGES\django.mo (compilé)
    echo    - locale\ar\LC_MESSAGES\django.po.backup (sauvegarde)
)

echo.
echo ================================================
echo         TRADUCTION TERMINÉE
echo ================================================
pause