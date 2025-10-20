@echo off
echo Starting MartialComp Django Server...
cd /d C:\martial_hub_django\martialcomp
python manage.py runserver 0.0.0.0:8000
pause