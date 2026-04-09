#!/usr/bin/env python3
FILE = "/var/www/vhosts/martialcomp.com/httpdocs/apps/task_management/templates/task_management/kanban/kanban_board.html"

with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

old = '''    <a href="{% url 'task_management:kanban_fullscreen' board.id %}"
       class="btn btn-outline-secondary" data-toggle="tooltip" title="{% trans 'Plein écran' %}">
        <i class="fas fa-expand"></i>
    </a>'''

new = '''    <a href="{% url 'task_management:task_list' %}?board={{ board.id }}"
       class="btn btn-outline-info" data-bs-toggle="tooltip" title="{% trans 'Vue Liste' %}">
        <i class="fas fa-list"></i>
    </a>
    <a href="{% url 'task_management:kanban_fullscreen' board.id %}"
       class="btn btn-outline-secondary" data-bs-toggle="tooltip" title="{% trans 'Plein écran' %}">
        <i class="fas fa-expand"></i>
    </a>'''

if old in content:
    content = content.replace(old, new)
    with open(FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print('[OK] List view button added')
else:
    print('[WARN] Pattern not found')
