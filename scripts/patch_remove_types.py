#!/usr/bin/env python3
"""Fix remove_from_category to also clean up competition_types."""

filepath = "/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/competition_management_pro.py"

with open(filepath, "r") as f:
    content = f.read()

old = """        registration.categories.remove(category)

        return JsonResponse({
            'success': True,
            'message': _("Pratiquant retiré de la catégorie")
        })"""

new = """        registration.categories.remove(category)

        # Si plus aucune catégorie de ce type, retirer le type aussi
        if category.competition_type:
            remaining = registration.categories.filter(competition_type=category.competition_type)
            if not remaining.exists():
                registration.competition_types.remove(category.competition_type)

        return JsonResponse({
            'success': True,
            'message': _("Pratiquant retiré de la catégorie")
        })"""

if old in content:
    content = content.replace(old, new, 1)
    with open(filepath, "w") as f:
        f.write(content)
    print("remove_from_category patched OK")
else:
    print("ERROR: pattern not found")
