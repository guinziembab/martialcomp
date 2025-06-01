@echo off
echo ===================================
echo Solution definitive pour le formulaire coach
echo ===================================

cd /d C:\martial_hub_django\martialcomp

echo 1. Activation de l'environnement virtuel...
call .venv\Scripts\activate.bat

echo 2. Suppression des migrations problematiques...
del /f /q competitions\migrations\*teaching_place_name*.py 2>nul

echo 3. Creation d'une migration correcte...
python create_fixed_migration.py

echo 4. Application de la migration...
python manage.py migrate

echo 5. Toutes les modifications ont ete appliquees!
echo IMPORTANT: Redemarrez votre serveur Django:
echo   1. Arretez le serveur avec CTRL+C
echo   2. Redemarrez-le avec python manage.py runserver
echo ===================================

pause