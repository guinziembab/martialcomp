#!/usr/bin/env python
"""
Script pour ajouter les permissions financières à un utilisateur.
Usage: python add_finance_permissions.py <username>
"""
import os
import sys
import django

# Configurer l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType

def add_finance_permissions(username):
    """
    Ajoute toutes les permissions financières à un utilisateur donné.
    
    Args:
        username (str): Nom d'utilisateur
    """
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        print(f"Utilisateur {username} introuvable!")
        return
    
    # Liste des permissions à ajouter
    finance_permissions = Permission.objects.filter(
        content_type__app_label='finances'
    )
    
    # Ajouter les permissions
    for permission in finance_permissions:
        user.user_permissions.add(permission)
    
    user.save()
    
    # Afficher les permissions ajoutées
    print(f"Permissions ajoutées à {username}:")
    for permission in finance_permissions:
        print(f"  - {permission.codename}: {permission.name}")
    
    print(f"\nTotal: {finance_permissions.count()} permissions")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python add_finance_permissions.py <username>")
        sys.exit(1)
    
    add_finance_permissions(sys.argv[1])