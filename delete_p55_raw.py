#!/usr/bin/env python
"""Delete practitioner 55 via raw SQL to bypass cascade issues"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from django.db import connection

# First verify practitioner 55 exists and has no important relations
from apps.competitions.models import Practitioner

try:
    p55 = Practitioner.objects.get(id=55)
    print(f"Found Practitioner 55: {p55.first_name} {p55.last_name}")
    print(f"User linked: {p55.user_id}")

    # Double-check no competition data is linked
    poules = p55.poules_individuelles.count()
    print(f"Poules: {poules}")

    if poules == 0 and p55.user_id is None:
        print()
        print("Safe to delete - no user linked and no poules")
        print("Deleting related records first...")

        cursor = connection.cursor()

        # Delete from related tables first
        related_tables = [
            "competitions_practitioner_disciplines",
            "grades_practitionergrade",
        ]

        for table in related_tables:
            try:
                cursor.execute(f"DELETE FROM {table} WHERE practitioner_id = 55")
                print(f"  Cleaned {table}")
            except Exception as e:
                print(f"  Skip {table}: {str(e)[:50]}")

        print("Deleting practitioner 55...")
        cursor.execute("DELETE FROM competitions_practitioner WHERE id = 55")

        # Verify deletion
        try:
            Practitioner.objects.get(id=55)
            print("ERROR: Practitioner 55 still exists")
        except Practitioner.DoesNotExist:
            print("SUCCESS: Practitioner 55 deleted!")
    else:
        print("WARNING: Cannot delete - has user or poules")

except Practitioner.DoesNotExist:
    print("Practitioner 55 already deleted or does not exist")
