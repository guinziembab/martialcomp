@echo off
echo Starting MartialComp Django Server on port 8888...
cd /d C:\martial_hub_django\martialcomp
python manage.py runserver 127.0.0.1:8888
pause