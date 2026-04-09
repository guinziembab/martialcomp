#!/usr/bin/env python3
"""Add tasks section at the TOP of participant dashboard, right after stat cards."""

FILE = "/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/dashboard/participant.html"

with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the previously added section (near Payment tracking)
if '<!-- Mes taches assignees -->' in content:
    # Find and remove the old section
    start = content.index('<!-- Mes taches assignees -->')
    # Find the end - look for the next <!-- or section start
    end = content.index('{% endif %}\n\n', start) + len('{% endif %}\n\n')
    content = content[:start] + content[end:]
    print('[OK] Removed old tasks section')

# Insert right after stat cards, before the main content row
marker = '''        <div class="row">
            <!-- Section principale -->
            <div class="col-lg-8">
                <!-- Prochaines compétitions -->'''

tasks_section = '''        <!-- MES TACHES ASSIGNEES - Visible immediatement -->
        {% if user_tasks %}
        <div class="row mb-3">
            <div class="col-12">
                <div class="dashboard-card fade-in" style="border-left: 4px solid #667eea;">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h2 style="font-size:1.1rem; margin:0; display:flex; align-items:center; gap:8px;">
                            <i class="fas fa-tasks" style="color:#667eea;"></i> {% trans "Mes taches" %}
                            <span class="badge" style="background:#667eea; font-size:0.7rem;">{{ user_tasks|length }}</span>
                        </h2>
                        <a href="/{{ LANGUAGE_CODE }}/task-management/tasks/?assigned_to_me=1" class="btn btn-sm btn-outline-info">{% trans "Voir tout" %}</a>
                    </div>
                    <div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap:10px; padding:15px;">
                        {% for task in user_tasks %}
                        <a href="/{{ LANGUAGE_CODE }}/task-management/tasks/{{ task.id }}/" style="display:flex; align-items:center; gap:10px; padding:10px 12px; background:rgba(30,41,59,0.5); border-radius:8px; text-decoration:none; color:#e2e8f0; border-left:3px solid {% if task.priority == 'urgent' %}#e91e63{% elif task.priority == 'high' %}#ff5722{% elif task.priority == 'medium' %}#ff9800{% else %}#4caf50{% endif %};" onmouseover="this.style.background='rgba(102,126,234,0.15)'" onmouseout="this.style.background='rgba(30,41,59,0.5)'">
                            <div style="flex:1; min-width:0;">
                                <div style="font-weight:600; font-size:0.85rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{{ task.title }}</div>
                                <div style="font-size:0.7rem; color:#94a3b8;">{{ task.board.name }} &middot; {{ task.column.name }}</div>
                            </div>
                            {% if task.due_date %}
                            <span style="font-size:0.7rem; flex-shrink:0; {% if task.is_overdue %}color:#ef4444; font-weight:bold;{% else %}color:#94a3b8;{% endif %}">
                                {{ task.due_date|date:"d/m" }}
                            </span>
                            {% endif %}
                        </a>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>
        {% endif %}

'''

if marker in content and '<!-- MES TACHES ASSIGNEES' not in content:
    content = content.replace(marker, tasks_section + marker)
    with open(FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print('[OK] Tasks section added at TOP of dashboard')
else:
    if '<!-- MES TACHES ASSIGNEES' in content:
        print('[SKIP] Already added at top')
    else:
        print('[WARN] Marker not found')

print('[DONE]')
