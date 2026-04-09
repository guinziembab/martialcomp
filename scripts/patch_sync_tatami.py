#!/usr/bin/env python3
"""
Synchronize tatami assignment between Programmation pro and Cockpit.

Programmation pro uses: category.assigned_tatami (int) → tatami number
Cockpit uses: aire.categories (M2M) → AireCombat.categories

When assigning in Programmation pro → also add to AireCombat.categories
When assigning in Cockpit → also set category.assigned_tatami
"""

# 1. Patch schedule_api.py - assign_category_to_tatami
filepath1 = "/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/schedule_api.py"
with open(filepath1, "r") as f:
    content1 = f.read()

old1 = """            category.assigned_tatami = int(tatami)
            category.schedule_order = max_order + 1
            category.save()"""

new1 = """            category.assigned_tatami = int(tatami)
            category.schedule_order = max_order + 1
            category.save()

            # Sync with Cockpit: add category to AireCombat if linked
            try:
                from apps.competitions.models.schedule import TatamiSchedule
                ts = TatamiSchedule.objects.filter(
                    competition_schedule__competition=competition,
                    tatami_number=int(tatami)
                ).select_related('aire_combat').first()
                if ts and ts.aire_combat:
                    ts.aire_combat.categories.add(category)
            except Exception:
                pass  # Don't fail if sync fails"""

if old1 in content1:
    content1 = content1.replace(old1, new1, 1)
    with open(filepath1, "w") as f:
        f.write(content1)
    print("schedule_api.py: assign patched OK")
else:
    print("schedule_api.py: assign pattern NOT FOUND")

# Also patch unassign
old1b = """            category.assigned_tatami = None
            category.schedule_order = None
            category.estimated_start_time = None
            category.save()"""

new1b = """            # Sync with Cockpit: remove from AireCombat if linked
            try:
                from apps.competitions.models.schedule import TatamiSchedule
                if category.assigned_tatami:
                    ts = TatamiSchedule.objects.filter(
                        competition_schedule__competition=competition,
                        tatami_number=category.assigned_tatami
                    ).select_related('aire_combat').first()
                    if ts and ts.aire_combat:
                        ts.aire_combat.categories.remove(category)
            except Exception:
                pass

            category.assigned_tatami = None
            category.schedule_order = None
            category.estimated_start_time = None
            category.save()"""

if old1b in content1:
    # Re-read since we already wrote
    with open(filepath1, "r") as f:
        content1 = f.read()
    content1 = content1.replace(old1b, new1b, 1)
    with open(filepath1, "w") as f:
        f.write(content1)
    print("schedule_api.py: unassign patched OK")
else:
    print("schedule_api.py: unassign pattern NOT FOUND")


# 2. Patch cockpit.py - cockpit_assign_category
filepath2 = "/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/management/cockpit.py"
with open(filepath2, "r") as f:
    content2 = f.read()

old2 = """        aire = AireCombat.objects.get(pk=aire_id, competition=competition)
        category = CompetitionCategory.objects.get(pk=category_id, competition=competition)
        aire.categories.add(category)"""

new2 = """        aire = AireCombat.objects.get(pk=aire_id, competition=competition)
        category = CompetitionCategory.objects.get(pk=category_id, competition=competition)
        aire.categories.add(category)

        # Sync with Programmation: set assigned_tatami on category
        try:
            ts = getattr(aire, 'tatami_schedule', None)
            if ts:
                from django.db.models import Max
                max_order = CompetitionCategory.objects.filter(
                    competition=competition,
                    assigned_tatami=ts.tatami_number
                ).aggregate(Max('schedule_order'))['schedule_order__max'] or 0
                category.assigned_tatami = ts.tatami_number
                category.schedule_order = max_order + 1
                category.save(update_fields=['assigned_tatami', 'schedule_order'])
        except Exception:
            pass"""

if old2 in content2:
    content2 = content2.replace(old2, new2, 1)
    print("cockpit.py: assign patched OK")
else:
    print("cockpit.py: assign pattern NOT FOUND")

# Patch cockpit unassign
old2b = """        aire = AireCombat.objects.get(pk=aire_id, competition=competition)
        category = CompetitionCategory.objects.get(pk=category_id, competition=competition)
        aire.categories.remove(category)"""

new2b = """        aire = AireCombat.objects.get(pk=aire_id, competition=competition)
        category = CompetitionCategory.objects.get(pk=category_id, competition=competition)
        aire.categories.remove(category)

        # Sync with Programmation: clear assigned_tatami
        try:
            category.assigned_tatami = None
            category.schedule_order = None
            category.estimated_start_time = None
            category.save(update_fields=['assigned_tatami', 'schedule_order', 'estimated_start_time'])
        except Exception:
            pass"""

if old2b in content2:
    content2 = content2.replace(old2b, new2b, 1)
    print("cockpit.py: unassign patched OK")
else:
    print("cockpit.py: unassign pattern NOT FOUND")

with open(filepath2, "w") as f:
    f.write(content2)

print("DONE - Synchronization patches applied")
