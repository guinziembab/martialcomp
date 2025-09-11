@echo off
echo === Création forcée des tables api_auth dans PostgreSQL ===

cd /d "C:\martial_hub_django\martialcomp"

echo.
echo 1. Activation de l'environnement virtuel...
call .venv\Scripts\activate.bat

echo.
echo 2. Vérification de la connexion PostgreSQL...
python -c "import psycopg2; conn = psycopg2.connect(host='localhost', database='martialcomp', user='postgres', password='postgres'); print('✅ Connexion PostgreSQL OK'); conn.close()"

echo.
echo 3. Création forcée des tables...
python force_create_api_auth_tables.py

echo.
echo 4. Test final d'accès à l'admin...
echo Ouvrez votre navigateur et allez à : http://127.0.0.1:8000/admin/api_auth/deviceregistration/

echo.
echo === Terminé ===
pause