#!/usr/bin/env python3
"""
Fix Programmation pro to:
1. Show all TatamiSchedule entries (not just those with assigned categories)
2. Display aire names instead of 'Tatami N'
"""

# 1. Fix the view to build tatami_numbers from TatamiSchedule
filepath = "/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/competition_management_pro.py"
with open(filepath, "r") as f:
    content = f.read()

old = """    # Liste des tatamis existants (1 à 5 par défaut ou selon les données)
    tatami_numbers = sorted(categories_by_tatami.keys()) if categories_by_tatami else [1, 2, 3]"""

new = """    # Liste des tatamis: depuis les TatamiSchedule liés aux AireCombat
    from apps.competitions.models.schedule import TatamiSchedule, CompetitionSchedule
    tatami_schedules = TatamiSchedule.objects.filter(
        competition_schedule__competition=competition
    ).select_related('aire_combat').order_by('tatami_number')

    if tatami_schedules.exists():
        tatami_numbers = [ts.tatami_number for ts in tatami_schedules]
        tatami_names = {ts.tatami_number: ts.name or (ts.aire_combat.nom if ts.aire_combat else f'Tatami {ts.tatami_number}') for ts in tatami_schedules}
    elif categories_by_tatami:
        tatami_numbers = sorted(categories_by_tatami.keys())
        tatami_names = {n: f'Tatami {n}' for n in tatami_numbers}
    else:
        tatami_numbers = [1, 2, 3]
        tatami_names = {1: 'Tatami 1', 2: 'Tatami 2', 3: 'Tatami 3'}"""

if old in content:
    content = content.replace(old, new, 1)
    print("View: tatami_numbers fixed")
else:
    print("View: tatami_numbers NOT FOUND")

# Add tatami_names to context
old_ctx = "'tatami_numbers': tatami_numbers,"
new_ctx = "'tatami_numbers': tatami_numbers,\n        'tatami_names': tatami_names,"

if old_ctx in content:
    content = content.replace(old_ctx, new_ctx, 1)
    print("View: tatami_names added to context")

with open(filepath, "w") as f:
    f.write(content)

# 2. Fix the template to show aire names
tpl_path = "/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/club/competition_management_pro.html"
with open(tpl_path, "r") as f:
    tpl = f.read()

# Replace tatami header to show name from tatami_names dict
old_tpl = """<h5 class="mb-0"><i class="fas fa-square me-2"></i>{% trans "Tatami" %} {{ tatami_num }}</h5>"""
new_tpl = """<h5 class="mb-0"><i class="fas fa-square me-2"></i>{% for tn, tname in tatami_names.items %}{% if tn == tatami_num %}{{ tname }}{% endif %}{% endfor %}</h5>"""

if old_tpl in tpl:
    tpl = tpl.replace(old_tpl, new_tpl, 1)
    print("Template: tatami header name fixed")
else:
    print("Template: tatami header NOT FOUND")

with open(tpl_path, "w") as f:
    f.write(tpl)

print("DONE")
