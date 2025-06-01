#!/bin/bash
# Script pour créer la migration du profil coach

cd /mnt/c/martial_hub_django
source venv/Scripts/activate || source venv/bin/activate
cd martialcomp
python manage.py makemigrations competitions -n create_coach_profile_models --empty