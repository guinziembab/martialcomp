#!/usr/bin/env python
"""Complete cleanup of duplicate practitioner 55 - transfer remaining data to 40"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from apps.competitions.models import Practitioner

# Get both practitioners
p40 = Practitioner.objects.get(id=40)
p55 = Practitioner.objects.get(id=55)

print("=== Cleanup Practitioner 55 ===")
print(f"Target: {p40.first_name} {p40.last_name} (ID=40)")
print(f"Source: {p55.first_name} {p55.last_name} (ID=55)")
print()

# Transfer poules_individuelles (ManyToMany - need to use add/remove)
poules = list(p55.poules_individuelles.all())
print(f"Poules individuelles to transfer: {len(poules)}")
for poule in poules:
    print(f"  - Transferring poule {poule.id}: {poule}")
    # Add p40 to the poule if not already there
    if not poule.pratiquants.filter(id=p40.id).exists():
        poule.pratiquants.add(p40)
        print(f"    Added practitioner 40 to poule")
    # Remove p55 from the poule
    poule.pratiquants.remove(p55)
    print(f"    Removed practitioner 55 from poule")

# Verify transfer
remaining_poules = p55.poules_individuelles.count()
print(f"  Remaining poules for p55: {remaining_poules}")

# Transfer performances (ForeignKey)
performances = list(p55.performances.all())
print(f"Performances to transfer: {len(performances)}")
for perf in performances:
    print(f"  - Transferring performance {perf.id}")
    perf.practitioner = p40
    perf.save()

# Transfer grade_history (ForeignKey)
try:
    grade_histories = list(p55.grade_history.all())
    print(f"Grade histories to transfer: {len(grade_histories)}")
    for gh in grade_histories:
        print(f"  - Transferring grade history {gh.id}")
        gh.practitioner = p40
        gh.save()
except Exception as e:
    print(f"Grade history error: {e}")

# Refresh from database
p55.refresh_from_db()

# Check remaining related objects
print()
print("=== Remaining related objects for Practitioner 55 ===")
remaining = False
for rel in p55._meta.related_objects:
    related_name = rel.get_accessor_name()
    try:
        related_manager = getattr(p55, related_name)
        count = related_manager.count()
        if count > 0:
            print(f"{related_name}: {count}")
            remaining = True
    except Exception:
        pass  # Skip errors from missing tables

if not remaining:
    print("No remaining related objects - safe to delete")
    print()
    print("Deleting Practitioner 55...")
    try:
        p55.delete()
        print("SUCCESS: Practitioner 55 deleted!")
    except Exception as e:
        print(f"ERROR deleting: {e}")
else:
    print()
    print("WARNING: Still has related objects, cannot delete safely")
