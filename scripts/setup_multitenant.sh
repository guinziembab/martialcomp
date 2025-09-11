#!/bin/bash

echo "=== CONFIGURATION MULTI-TENANT ==="
echo

# 1. Créer les migrations pour multitenant si nécessaire
echo "1. Création des migrations..."
python manage.py makemigrations multitenant

echo
echo "2. Création des migrations pour competitions..."
python manage.py makemigrations competitions

echo
echo "3. Application des migrations..."
# Appliquer d'abord les migrations de multitenant
python manage.py migrate multitenant

# Puis les autres migrations
python manage.py migrate

echo
echo "4. Vérification de l'état..."
python manage.py migration_status

echo
echo "=== Configuration terminée ==="