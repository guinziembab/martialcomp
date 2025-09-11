@echo off
echo === MartialComp Test Server ===
cd /d "%~dp0"

echo.
echo This will start Django with a special test page to verify everything works.
echo.

echo Setting up test configuration...
set DJANGO_SETTINGS_MODULE=config.settings_test

echo.
echo Adding required apps to test settings...
python -c "
import sys, os
sys.path.append('.')
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings_minimal'
import django
django.setup()
from django.contrib.auth.models import User
print('Database test: {} users found'.format(User.objects.count()))
"

if errorlevel 1 (
    echo ERROR: Database test failed
    pause
    exit /b 1
)

echo.
echo Starting test server on port 8002...
echo.
echo IMPORTANT: Open your browser to:
echo   http://127.0.0.1:8002/
echo   http://localhost:8002/
echo.
echo DO NOT use https:// - only http://
echo.

python manage.py runserver --settings=config.settings_minimal 127.0.0.1:8002

pause