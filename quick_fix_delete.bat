@echo off
echo 🚀 Correction rapide - Suppression d'événements...

REM Activer l'environnement virtuel
call .venv\Scripts\activate.bat

echo ✅ Environnement virtuel activé
echo 📍 Répertoire: %cd%

REM Configurer Django pour PostgreSQL
set DJANGO_SETTINGS_MODULE=config.settings_postgres

echo 📋 Configuration: PostgreSQL
echo.

REM Correction rapide
echo === Correction EventSurvey ===
python quick_fix_eventsurvey.py

echo.
echo === Terminé ===
echo La suppression d'événements devrait maintenant fonctionner
echo Testez: http://127.0.0.1:8000/competitions/events/
pause