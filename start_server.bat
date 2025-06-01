@echo off
echo === Starting MartialComp Development Server ===
cd /d "%~dp0"
echo Current directory: %CD%

echo.
echo Checking Python environment...
python --version
if errorlevel 1 (
    echo ERROR: Python not found. Make sure your virtual environment is activated.
    pause
    exit /b 1
)

echo.
echo Checking database...
if exist "db.sqlite3" (
    echo ✅ Database file exists: db.sqlite3
) else (
    echo ❌ Database file missing: db.sqlite3
    echo Please run migrations first.
    pause
    exit /b 1
)

echo.
echo Testing Django configuration...
python -c "import os; os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings_minimal'; import django; django.setup(); from django.contrib.auth.models import User; print(f'✅ Django OK - {User.objects.count()} users found')"
if errorlevel 1 (
    echo ❌ Django configuration test failed
    pause
    exit /b 1
)

echo.
echo Starting Django development server...
echo Open your browser to: http://127.0.0.1:8000/
echo Press Ctrl+C to stop the server
echo.

python manage.py runserver --settings=config.settings_minimal 127.0.0.1:8000

echo.
echo Server stopped.
pause