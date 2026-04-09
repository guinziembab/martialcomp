#!/usr/bin/env python3
tpl_path = "/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/club/competition_management_pro.html"
with open(tpl_path, "r") as f:
    tpl = f.read()

old = """                    <a href="{% url 'competitions:club:competition_registration_form' competition_id=competition.id %}" class="btn btn-success">
                        <i class="fas fa-user-plus me-2"></i>{% trans "Inscrire" %}
                    </a>"""

new = """                    <a href="{% url 'competitions:club:competition_registration_form' competition_id=competition.id %}" class="btn btn-success me-2">
                        <i class="fas fa-user-plus me-2"></i>{% trans "Inscrire" %}
                    </a>
                    <a href="{% url 'competitions:club:export_competition_pdf' competition.id %}" target="_blank" class="btn btn-outline-info" title="Export PDF">
                        <i class="fas fa-file-pdf me-1"></i>PDF
                    </a>"""

if old in tpl:
    tpl = tpl.replace(old, new, 1)
    with open(tpl_path, "w") as f:
        f.write(tpl)
    print("PDF button added")
else:
    print("Pattern not found")
