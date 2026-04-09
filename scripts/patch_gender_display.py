#!/usr/bin/env python3
"""Add gender text display to practitioner items in drag & drop list."""

filepath = "/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/club/competition_management_pro.html"

with open(filepath, "r") as f:
    content = f.read()

# Replace the practitioner-details div to include gender
old = '''                                        <div class="practitioner-details text-truncate">
                                            {% if reg.practitioner.age %}<span class="age-info">{{ reg.practitioner.age }} {% trans "ans" %}</span>{% endif %}
                                            {% if reg.practitioner.age and reg.practitioner.current_grade %}<span class="mx-1">\u2022</span>{% endif %}
                                            {% if reg.practitioner.current_grade %}<span class="grade-info">{{ reg.practitioner.current_grade.name }}</span>{% endif %}
                                        </div>'''

new = '''                                        <div class="practitioner-details text-truncate">
                                            {% if reg.practitioner.age %}<span class="age-info">{{ reg.practitioner.age }} {% trans "ans" %}</span>{% endif %}
                                            {% if reg.practitioner.age and reg.practitioner.current_grade %}<span class="mx-1">\u2022</span>{% endif %}
                                            {% if reg.practitioner.current_grade %}<span class="grade-info">{{ reg.practitioner.current_grade.name }}</span>{% endif %}
                                            {% if reg.practitioner.gender %}<span class="mx-1">\u2022</span><span class="gender-info" style="font-weight:600;{% if reg.practitioner.gender == 'M' %}color:#3498db{% elif reg.practitioner.gender == 'F' %}color:#e91e63{% endif %}">{% if reg.practitioner.gender == 'M' %}M{% elif reg.practitioner.gender == 'F' %}F{% else %}{{ reg.practitioner.gender }}{% endif %}</span>{% endif %}
                                        </div>'''

count = content.count(old)
if count > 0:
    content = content.replace(old, new, 1)
    print(f"Replaced practitioner-details ({count} found, replaced 1)")
else:
    print("ERROR: pattern not found")

with open(filepath, "w") as f:
    f.write(content)
print("DONE")
