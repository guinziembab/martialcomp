#!/usr/bin/env python3
FILE = "/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/practitioner/dashboard.html"

with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

tasks_section = '''
    <!-- Assigned Tasks -->
    {% if user_tasks %}
    <div class="dashboard-section">
        <h2><i class="fas fa-tasks me-2" style="color: #667eea;"></i>{% trans "Mes taches assignees" %}</h2>
        <div style="background: rgba(30,41,59,0.5); border-radius: 10px; overflow: hidden;">
            {% for task in user_tasks %}
            <a href="{% url 'task_management:task_detail' task.id %}" style="display:flex; align-items:center; justify-content:space-between; padding:12px 16px; border-bottom:1px solid rgba(51,65,85,0.5); text-decoration:none; color:#e2e8f0;" onmouseover="this.style.background='rgba(102,126,234,0.1)'" onmouseout="this.style.background=''">
                <div style="display:flex; align-items:center; gap:10px;">
                    {% if task.priority == 'urgent' %}
                        <span style="width:8px; height:8px; border-radius:50%; background:#e91e63; flex-shrink:0;"></span>
                    {% elif task.priority == 'high' %}
                        <span style="width:8px; height:8px; border-radius:50%; background:#ff5722; flex-shrink:0;"></span>
                    {% elif task.priority == 'medium' %}
                        <span style="width:8px; height:8px; border-radius:50%; background:#ff9800; flex-shrink:0;"></span>
                    {% else %}
                        <span style="width:8px; height:8px; border-radius:50%; background:#4caf50; flex-shrink:0;"></span>
                    {% endif %}
                    <div>
                        <div style="font-weight:600;">{{ task.title }}</div>
                        <div style="font-size:0.8rem; color:#94a3b8;">{{ task.board.name }} &middot; {{ task.column.name }}</div>
                    </div>
                </div>
                <div style="text-align:right; flex-shrink:0;">
                    {% if task.due_date %}
                    <span style="font-size:0.8rem; {% if task.is_overdue %}color:#ef4444;{% else %}color:#94a3b8;{% endif %}">
                        <i class="fas fa-calendar-alt me-1"></i>{{ task.due_date|date:"d/m/Y" }}
                    </span>
                    {% endif %}
                </div>
            </a>
            {% endfor %}
        </div>
        <div style="text-align:center; margin-top:10px;">
            <a href="{% url 'task_management:task_list' %}?assigned_to_me=1" style="color:#667eea; font-size:0.85rem;">
                {% trans "Voir toutes mes taches" %} <i class="fas fa-arrow-right ms-1"></i>
            </a>
        </div>
    </div>
    {% endif %}

'''

# Insert before "Activite recente" section
marker = '''    <div class="dashboard-section">
        <h2>{% trans "Activité récente" %}</h2>'''

if marker in content and 'user_tasks' not in content:
    content = content.replace(marker, tasks_section + marker)
    with open(FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print('[OK] Tasks section added before Activity section')
else:
    if 'user_tasks' in content:
        print('[SKIP] Already added')
    else:
        print('[WARN] Activity section marker not found')
