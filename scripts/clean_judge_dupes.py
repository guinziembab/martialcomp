#!/usr/bin/env python3
"""Clean duplicate JudgeAssignments."""
import os, django
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.production"
django.setup()

from apps.competitions.models.judges import JudgeAssignment
from django.db.models import Count

dupes = JudgeAssignment.objects.values("user_id", "category_id").annotate(cnt=Count("id")).filter(cnt__gt=1)
deleted = 0
for d in dupes:
    uid = d["user_id"]
    cid = d["category_id"]
    assignments = list(JudgeAssignment.objects.filter(user_id=uid, category_id=cid).order_by("id"))
    # Keep chief_judge if exists, otherwise first
    keep = assignments[0]
    for a in assignments:
        if a.assignment_type == "chief_judge":
            keep = a
            break
    for a in assignments:
        if a.id != keep.id:
            print("Deleting: id=%d user=%d cat=%d type=%s" % (a.id, uid, cid, a.assignment_type))
            a.delete()
            deleted += 1
print("Cleaned %d duplicates" % deleted)
