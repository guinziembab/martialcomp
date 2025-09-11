@echo off
echo ===================================
echo Solution simplifiee pour le formulaire coach
echo ===================================

cd /d C:\martial_hub_django\martialcomp

echo 1. Activation de l'environnement virtuel...
call .venv\Scripts\activate.bat

echo 2. Creation d'une nouvelle migration...
python fix_or_create_migration.py

echo 3. Application de la migration...
python manage.py migrate

echo 4. Toutes les modifications ont ete appliquees!
echo IMPORTANT: Redemarrez votre serveur Django:
echo   1. Arretez le serveur avec CTRL+C
echo   2. Redemarrez-le avec python manage.py runserver
echo ===================================

pause