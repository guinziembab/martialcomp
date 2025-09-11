@echo off
echo === Starting MartialComp on Alternative Port ===
cd /d "%~dp0"

echo Testing different ports to avoid conflicts...
echo.

echo Starting on port 8001...
echo URL: http://127.0.0.1:8001/
echo Admin: http://127.0.0.1:8001/admin/
echo.
echo If this doesn't work, try port 8002 or 8003
echo.

python manage.py runserver --settings=config.settings_minimal 127.0.0.1:8001

pause