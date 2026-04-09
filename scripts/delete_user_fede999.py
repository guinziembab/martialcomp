#!/usr/bin/env python
"""
Script pour supprimer l'utilisateur FEDE999 et toutes ses données associées.
À exécuter avec: python manage.py shell < scripts/delete_user_fede999.py
"""
import os
import sys
import django

# Setup Django si nécessaire
if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
    django.setup()

from django.contrib.auth import get_user_model
from django.db import connection

User = get_user_model()

username_to_delete = 'FEDE999'

try:
    user = User.objects.get(username=username_to_delete)
    print(f"Utilisateur trouvé: {user.username} (ID: {user.id})")

    # 1. Supprimer les fédérations
    try:
        from apps.competitions.models import Federation
        federations = Federation.objects.filter(owner=user)
        count = federations.count()
        if count > 0:
            federations.delete()
            print(f"  - {count} fédération(s) supprimée(s)")
    except Exception as e:
        print(f"  - Erreur suppression fédérations: {e}")

    # 2. Supprimer le profil utilisateur
    try:
        from apps.competitions.models import UserProfile
        profiles = UserProfile.objects.filter(user=user)
        count = profiles.count()
        if count > 0:
            profiles.delete()
            print(f"  - {count} profil(s) supprimé(s)")
    except Exception as e:
        print(f"  - Erreur suppression profils: {e}")

    # 3. Supprimer les notifications
    try:
        from apps.competitions.models import Notification
        notifications = Notification.objects.filter(user=user)
        count = notifications.count()
        if count > 0:
            notifications.delete()
            print(f"  - {count} notification(s) supprimée(s)")
    except Exception as e:
        print(f"  - Erreur suppression notifications: {e}")

    # 4. Supprimer les OrganizationMember
    try:
        from apps.organizations.models import OrganizationMember
        members = OrganizationMember.objects.filter(user=user)
        count = members.count()
        if count > 0:
            members.delete()
            print(f"  - {count} membre(s) organisation supprimé(s)")
    except Exception as e:
        print(f"  - Erreur suppression membres organisation: {e}")

    # 5. Supprimer l'utilisateur
    user.delete()
    print(f"\n✅ Utilisateur {username_to_delete} supprimé avec succès!")

except User.DoesNotExist:
    print(f"❌ Utilisateur {username_to_delete} non trouvé")
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
