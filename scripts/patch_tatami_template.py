#!/usr/bin/env python3
"""
Fix the Programmation pro template to properly display categories per tatami.

The issue: categories_by_tatami is a dict {tatami_num: [cat_list]}, but the template
iterates it wrong. We need to pass a flat list and filter by tatami_num in template.
"""

# Fix the view to pass a flat list of all assigned categories instead of a dict
filepath = "/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/competition_management_pro.py"
with open(filepath, "r") as f:
    content = f.read()

# Add assigned_categories_flat to context (flat list of all assigned cats)
old_ctx = "'tatami_names': tatami_names,"
new_ctx = """'tatami_names': tatami_names,
        'assigned_categories_flat': [cat for cats in categories_by_tatami.values() for cat in cats],"""

if old_ctx in content:
    content = content.replace(old_ctx, new_ctx, 1)
    with open(filepath, "w") as f:
        f.write(content)
    print("View: added assigned_categories_flat to context")
else:
    print("View: context pattern NOT FOUND")

# Fix the template to use assigned_categories_flat
tpl_path = "/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/club/competition_management_pro.html"
with open(tpl_path, "r") as f:
    tpl = f.read()

# Replace the iteration over categories_by_tatami with assigned_categories_flat
old_tpl = """{% for cat in categories_by_tatami|default_if_none:'' %}
                                    {% if cat.assigned_tatami == tatami_num %}"""
new_tpl = """{% for cat in assigned_categories_flat %}
                                    {% if cat.assigned_tatami == tatami_num %}"""

if old_tpl in tpl:
    tpl = tpl.replace(old_tpl, new_tpl, 1)
    with open(tpl_path, "w") as f:
        f.write(tpl)
    print("Template: iteration fixed")
else:
    print("Template: pattern NOT FOUND, trying alternate...")
    # Maybe the filter is slightly different
    import re
    pattern = r'\{%\s*for\s+cat\s+in\s+categories_by_tatami[^%]*%\}'
    match = re.search(pattern, tpl)
    if match:
        old_match = match.group()
        tpl = tpl.replace(old_match, '{% for cat in assigned_categories_flat %}', 1)
        with open(tpl_path, "w") as f:
            f.write(tpl)
        print(f"Template: replaced '{old_match}' with assigned_categories_flat iteration")
    else:
        print("Template: no match found at all")

print("DONE")
