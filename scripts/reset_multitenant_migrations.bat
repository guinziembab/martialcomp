@echo off
echo === Réinitialisation complète des migrations multitenant ===
echo.

echo 1. Suppression de toutes les tables multitenant...
python manage.py dbshell -c "DROP TABLE IF EXISTS multitenant_tenant CASCADE;"
python manage.py dbshell -c "DROP TABLE IF EXISTS multitenant_domain CASCADE;"
python manage.py dbshell -c "DROP TABLE IF EXISTS multitenant_tenantfeature CASCADE;"
python manage.py dbshell -c "DROP TABLE IF EXISTS multitenant_paymentmethod CASCADE;"
python manage.py dbshell -c "DROP TABLE IF EXISTS multitenant_tenantpayment CASCADE;"
python manage.py dbshell -c "DROP TABLE IF EXISTS multitenant_tenantsubscription CASCADE;"

echo.
echo 2. Suppression de l'historique des migrations...
python manage.py dbshell -c "DELETE FROM django_migrations WHERE app = 'multitenant';"

echo.
echo 3. Correction de la migration 0003...
python fix_migration_003.py

echo.
echo 4. Application de toutes les migrations multitenant...
python manage.py migrate multitenant

echo.
echo 5. Vérification...
python manage.py showmigrations multitenant

echo.
echo 6. Test final...
python manage.py migration_status

echo.
echo === Terminé ===
pause