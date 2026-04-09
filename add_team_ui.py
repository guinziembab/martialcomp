#!/usr/bin/env python3
"""Add team management UI: create team button, assign practitioners, remove button."""

FILE = "/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/combat/liste_equipes_par_categorie.html"

import shutil
shutil.copy2(FILE, FILE + '.backup_teamui')

with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# 1. Add "Create Team" button in each category header
old_header = '''<h5 class="mb-3" style="color: var(--text-primary);"><i class="fas fa-users me-2"></i>{% translate "Équipes" %}</h5>'''

new_header = '''<div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="mb-0" style="color: var(--text-primary);"><i class="fas fa-users me-2"></i>{% translate "Équipes" %}</h5>
                <button class="btn btn-sm btn-success" onclick="createTeamInCategory({{ category.id }}, '{{ category.name|escapejs }}')">
                    <i class="fas fa-plus me-1"></i>{% translate "Créer une équipe" %}
                </button>
            </div>'''

if old_header in content:
    content = content.replace(old_header, new_header)
    changes += 1
    print('[OK] Create team button added to team sections')

# Also add create button when NO teams exist yet
old_no_teams = '''{% if category.registrations.all %}
            <h5 class="mb-3 {% if category.equipes_combat.all %}mt-4{% endif %}" style="color: var(--text-primary);"><i class="fas fa-user me-2"></i>{% translate "Participants individuels" %}</h5>'''

new_no_teams = '''{% if not category.equipes_combat.all %}
            <div class="mb-3">
                <button class="btn btn-sm btn-success" onclick="createTeamInCategory({{ category.id }}, '{{ category.name|escapejs }}')">
                    <i class="fas fa-plus me-1"></i>{% translate "Créer une équipe" %}
                </button>
            </div>
            {% endif %}
            {% if category.registrations.all %}
            <h5 class="mb-3 {% if category.equipes_combat.all %}mt-4{% endif %}" style="color: var(--text-primary);"><i class="fas fa-user me-2"></i>{% translate "Participants individuels" %}</h5>'''

if old_no_teams in content:
    content = content.replace(old_no_teams, new_no_teams)
    changes += 1
    print('[OK] Create team button added for categories without teams')

# 2. Add "Assign to team" and "Remove" buttons to individual practitioner cards
old_practitioner_actions = '''<div class="team-actions">
                        <a href="{% url 'competitions:club:practitioner_detail' pk=registration.practitioner.id %}" class="btn-team btn-team-primary">
                            <i class="fas fa-eye"></i> {% translate "Voir" %}
                        </a>'''

new_practitioner_actions = '''<div class="team-actions" style="display:flex; gap:4px; flex-wrap:wrap;">
                        <button class="btn-team btn-team-outline" style="font-size:0.75rem; padding:4px 8px; border-color:#667eea; color:#667eea;" onclick="assignToTeam({{ registration.practitioner.id }}, '{{ registration.practitioner.full_name|escapejs }}', {{ category.id }})">
                            <i class="fas fa-user-plus"></i> {% translate "Affecter" %}
                        </button>
                        <button class="btn-team" style="font-size:0.75rem; padding:4px 8px; background:#ef4444; color:#fff; border:none; border-radius:6px;" onclick="removePractitioner({{ registration.id }}, '{{ registration.practitioner.full_name|escapejs }}')">
                            <i class="fas fa-user-minus"></i> {% translate "Retirer" %}
                        </button>
                        <a href="{% url 'competitions:club:practitioner_detail' pk=registration.practitioner.id %}" class="btn-team btn-team-primary" style="font-size:0.75rem; padding:4px 8px;">
                            <i class="fas fa-eye"></i>
                        </a>'''

content = content.replace(old_practitioner_actions, new_practitioner_actions)
changes += 1
print('[OK] Assign + Remove buttons added to practitioner cards')

# 3. Add team member cards with drag handle in team cards
old_team_members = '''<div class="team-members">
                        <i class="fas fa-user-friends"></i>
                        <span class="count">{{ equipe.membres.count }}</span> {% translate "membres" %}
                    </div>'''

new_team_members = '''<div class="team-members" data-team-id="{{ equipe.id }}" style="cursor:pointer;" onclick="toggleTeamMembers(this)">
                        <i class="fas fa-user-friends"></i>
                        <span class="count">{{ equipe.membres.count }}</span> {% translate "membres" %}
                        <i class="fas fa-chevron-down ms-1" style="font-size:0.7rem;"></i>
                    </div>
                    <div class="team-members-list" style="display:none; margin-top:8px; padding:4px 0; border-top:1px solid rgba(51,65,85,0.3);">
                        {% for membre in equipe.memberships.all %}
                        <div style="display:flex; justify-content:space-between; align-items:center; padding:3px 6px; font-size:0.8rem;">
                            <span>
                                {% if membre.est_remplacant %}<span style="color:#ff9800;">(R)</span>{% else %}<span style="color:#4caf50;">(T)</span>{% endif %}
                                {{ membre.pratiquant.full_name }}
                            </span>
                            <button class="btn btn-sm p-0" style="color:#ef4444; background:none; border:none;" onclick="event.stopPropagation(); removeTeamMember({{ membre.id }}, '{{ membre.pratiquant.full_name|escapejs }}', {{ equipe.id }})" title="Retirer">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                        {% empty %}
                        <div style="padding:6px; text-align:center; color:#94a3b8; font-size:0.8rem;">{% translate "Aucun membre" %}</div>
                        {% endfor %}
                    </div>'''

if old_team_members in content:
    content = content.replace(old_team_members, new_team_members)
    changes += 1
    print('[OK] Expandable team members list added')

# 4. Add JavaScript functions at the end of the file
js_code = '''
<script>
var competitionId = {{ competition.id }};
var lang = document.documentElement.lang || 'fr';

function getCSRF() {
    var match = document.cookie.match(/csrftoken=([^;]+)/);
    if (match) return match[1];
    var el = document.querySelector('[name=csrfmiddlewaretoken]');
    return el ? el.value : '';
}

function toggleTeamMembers(el) {
    var list = el.nextElementSibling;
    if (list) {
        list.style.display = list.style.display === 'none' ? 'block' : 'none';
    }
}

function createTeamInCategory(categoryId, categoryName) {
    var name = prompt('Nom de la nouvelle equipe pour "' + categoryName + '":');
    if (!name) return;

    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/' + lang + '/competitions/club/competition-teams/' + competitionId + '/create/', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('X-CSRFToken', getCSRF());
    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
    xhr.onload = function() {
        try {
            var data = JSON.parse(xhr.responseText);
            if (data.success) {
                alert('Equipe "' + name + '" creee avec succes!');
                location.reload();
            } else {
                alert('Erreur: ' + (data.error || data.message || 'Echec'));
            }
        } catch(e) {
            alert('Erreur: ' + xhr.responseText.substring(0, 200));
        }
    };
    xhr.onerror = function() { alert('Erreur reseau'); };
    xhr.send(JSON.stringify({name: name, category_id: categoryId}));
}

function assignToTeam(practitionerId, practitionerName, categoryId) {
    // Get teams in this category
    var teamCards = document.querySelectorAll('[data-team-id]');
    var teams = [];
    // Collect teams from the same category section
    var categorySection = document.querySelector('#category-' + categoryId);
    if (categorySection) {
        categorySection.querySelectorAll('[data-team-id]').forEach(function(el) {
            var card = el.closest('.team-card');
            if (card) {
                var nameEl = card.querySelector('.team-name');
                teams.push({id: el.getAttribute('data-team-id'), name: nameEl ? nameEl.textContent.trim() : 'Equipe'});
            }
        });
    }

    if (teams.length === 0) {
        alert('Aucune equipe dans cette categorie. Creez-en une d\'abord.');
        return;
    }

    var msg = 'Affecter ' + practitionerName + ' a quelle equipe ?\\n\\n';
    teams.forEach(function(t, i) { msg += (i+1) + '. ' + t.name + '\\n'; });
    var choice = prompt(msg + '\\nEntrez le numero:');
    if (!choice) return;

    var idx = parseInt(choice) - 1;
    if (idx < 0 || idx >= teams.length) { alert('Choix invalide'); return; }

    var teamId = teams[idx].id;
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/' + lang + '/competitions/club/competition-teams/' + competitionId + '/teams/' + teamId + '/add-member/', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('X-CSRFToken', getCSRF());
    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
    xhr.onload = function() {
        try {
            var data = JSON.parse(xhr.responseText);
            if (data.success) {
                location.reload();
            } else {
                alert('Erreur: ' + (data.error || data.message || 'Echec'));
            }
        } catch(e) {
            alert('Erreur: ' + xhr.responseText.substring(0, 200));
        }
    };
    xhr.send(JSON.stringify({practitioner_id: practitionerId, is_substitute: false}));
}

function removeTeamMember(membreId, memberName, equipeId) {
    if (!confirm('Retirer ' + memberName + ' de l\\'equipe ?')) return;

    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/' + lang + '/competitions/combat/membres/' + membreId + '/supprimer/', true);
    xhr.setRequestHeader('X-CSRFToken', getCSRF());
    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
    xhr.onload = function() { location.reload(); };
    xhr.send('');
}

function removePractitioner(registrationId, practitionerName) {
    if (!confirm('Retirer ' + practitionerName + ' de la competition ?')) return;

    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/' + lang + '/competitions/club/registration-api/unregister/' + registrationId + '/', true);
    xhr.setRequestHeader('X-CSRFToken', getCSRF());
    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
    xhr.onload = function() { location.reload(); };
    xhr.send('');
}
</script>
'''

if 'function createTeamInCategory' not in content:
    # Insert before </body> or at the end
    end_marker = '{% endblock %}'
    last_endblock = content.rfind(end_marker)
    if last_endblock > 0:
        content = content[:last_endblock] + js_code + '\n' + content[last_endblock:]
        changes += 1
        print('[OK] JavaScript functions added')

if changes > 0:
    with open(FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'[DONE] {changes} changes applied')
else:
    print('[DONE] No changes needed')
