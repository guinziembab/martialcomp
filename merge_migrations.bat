@echo off
echo ===================================
echo Fusion des migrations conflictuelles
echo ===================================

cd /d C:\martial_hub_django\martialcomp

echo 1. Activation de l'environnement virtuel...
call .venv\Scripts\activate.bat

echo 2. Fusion des migrations...
python manage.py makemigrations --merge

echo 3. Application des migrations fusionnées...
python manage.py migrate

echo 4. Toutes les modifications ont été appliquées!
echo IMPORTANT: Redémarrez votre serveur Django:
echo   1. Arrêtez le serveur avec CTRL+C
echo   2. Redémarrez-le avec python manage.py runserver
echo ===================================

pause