@echo off
REM =============================================================================
REM SCRIPT DE DEPLOIEMENT - IMPLEMENTATION MULTI-DEVISES
REM Date: 07-01-2026
REM Serveur: 217.154.24.122 (root)
REM =============================================================================

echo ==============================================
echo DEPLOIEMENT MULTI-DEVISES - MartialComp
echo Date: %date% %time%
echo ==============================================
echo.

set REMOTE=root@217.154.24.122
set REMOTE_PATH=/var/www/martialcomp
set LOCAL_PATH=C:\martial_hub_django\martialcomp

echo [1/5] Creation du backup sur le serveur distant...
ssh %REMOTE% "mkdir -p /var/www/backups/multi_currency_$(date +%%Y%%m%%d_%%H%%M%%S) && cp -rp /var/www/martialcomp/apps/finances/templatetags/finances_tags.py /var/www/martialcomp/apps/finances/context_processors.py /var/www/martialcomp/apps/finances/views/transactions.py /var/www/backups/multi_currency_$(date +%%Y%%m%%d_%%H%%M%%S)/ 2>/dev/null || true"

echo.
echo [2/5] Transfert des fichiers Python...
echo   - finances_tags.py
scp "%LOCAL_PATH%\apps\finances\templatetags\finances_tags.py" %REMOTE%:%REMOTE_PATH%/apps/finances/templatetags/finances_tags.py

echo   - context_processors.py
scp "%LOCAL_PATH%\apps\finances\context_processors.py" %REMOTE%:%REMOTE_PATH%/apps/finances/context_processors.py

echo   - transactions.py
scp "%LOCAL_PATH%\apps\finances\views\transactions.py" %REMOTE%:%REMOTE_PATH%/apps/finances/views/transactions.py

echo.
echo [3/5] Transfert des templates...
echo   - dashboard/index.html
scp "%LOCAL_PATH%\apps\finances\templates\finances\dashboard\index.html" %REMOTE%:%REMOTE_PATH%/apps/finances/templates/finances/dashboard/index.html

echo   - transactions/list.html
scp "%LOCAL_PATH%\apps\finances\templates\finances\transactions\list.html" %REMOTE%:%REMOTE_PATH%/apps/finances/templates/finances/transactions/list.html

echo   - accounts/list.html
scp "%LOCAL_PATH%\apps\finances\templates\finances\accounts\list.html" %REMOTE%:%REMOTE_PATH%/apps/finances/templates/finances/accounts/list.html

echo   - components/summary_card.html
scp "%LOCAL_PATH%\apps\finances\templates\finances\components\summary_card.html" %REMOTE%:%REMOTE_PATH%/apps/finances/templates/finances/components/summary_card.html

echo   - reports/index.html
scp "%LOCAL_PATH%\apps\finances\templates\finances\reports\index.html" %REMOTE%:%REMOTE_PATH%/apps/finances/templates/finances/reports/index.html

echo   - accounts/detail.html
scp "%LOCAL_PATH%\apps\finances\templates\finances\accounts\detail.html" %REMOTE%:%REMOTE_PATH%/apps/finances/templates/finances/accounts/detail.html

echo   - accounts/financial/list.html
scp "%LOCAL_PATH%\apps\finances\templates\finances\accounts\financial\list.html" %REMOTE%:%REMOTE_PATH%/apps/finances/templates/finances/accounts/financial/list.html

echo.
echo [4/5] Redemarrage des services...
ssh %REMOTE% "cd /var/www/martialcomp && source venv/bin/activate && python manage.py collectstatic --noinput 2>/dev/null; systemctl restart gunicorn 2>/dev/null || supervisorctl restart gunicorn 2>/dev/null || pkill -HUP gunicorn; echo 'Services redemarres!'"

echo.
echo [5/5] Verification...
ssh %REMOTE% "systemctl status gunicorn --no-pager 2>/dev/null || ps aux | grep gunicorn | head -2"

echo.
echo ==============================================
echo DEPLOIEMENT TERMINE!
echo ==============================================
echo.
echo Testez la conversion multi-devises:
echo   https://votre-domaine/finances/dashboard/?currency=XOF
echo.
pause
