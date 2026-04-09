#!/usr/bin/env python3
"""Fix assign_to_category to also set competition_types automatically."""

filepath = "/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/competition_management_pro.py"

with open(filepath, "r") as f:
    content = f.read()

# Add competition_types auto-assignment after categories.add
old = """        # Assigner à la catégorie
        registration.categories.add(category)"""

new = """        # Assigner à la catégorie
        registration.categories.add(category)

        # Auto-assigner le type de compétition correspondant
        if category.competition_type and not registration.competition_types.filter(id=category.competition_type.id).exists():
            registration.competition_types.add(category.competition_type)"""

if old in content:
    content = content.replace(old, new, 1)
    with open(filepath, "w") as f:
        f.write(content)
    print("assign_to_category patched OK")
else:
    print("ERROR: pattern not found")
