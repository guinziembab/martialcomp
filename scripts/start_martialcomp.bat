@echo off
echo === MartialComp Development Server ===
cd /d "%~dp0"

echo.
echo Starting MartialComp on port 8001 (working configuration)
echo.
echo URLs to access your application:
echo   Main application: http://127.0.0.1:8001/
echo   Admin interface:  http://127.0.0.1:8001/admin/
echo.
echo Login credentials:
echo   Username: admin
echo   Password: admin123
echo.
echo Press Ctrl+C to stop the server
echo.

python manage.py runserver --settings=config.settings_minimal 127.0.0.1:8001

echo.
echo Server stopped.
pause