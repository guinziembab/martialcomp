#!/usr/bin/env python
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from django.contrib.auth.models import User

print("=== UTILISATEURS EXISTANTS ===")
users = User.objects.all()

if users.exists():
    for user in users:
        print(f"ID: {user.id}")
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        print(f"Prénom: {user.first_name}")
        print(f"Nom: {user.last_name}")
        print(f"Superuser: {user.is_superuser}")
        print(f"Staff: {user.is_staff}")
        print(f"Actif: {user.is_active}")
        print(f"Date création: {user.date_joined}")
        print("-" * 50)
else:
    print("Aucun utilisateur trouvé dans la base de données.") 