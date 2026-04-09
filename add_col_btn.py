#!/usr/bin/env python3
FILE = "/var/www/vhosts/martialcomp.com/httpdocs/apps/task_management/templates/task_management/kanban/kanban_board.html"

with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

old = """        {% endfor %}
    </div>
</div>

<!-- Task Detail Modal -->"""

new = """        {% endfor %}

        {% if can_admin %}
        <div class="kanban-column" style="min-width:220px; max-width:220px; flex-shrink:0;">
            <div style="cursor:pointer; text-align:center; padding:30px 20px; border:2px dashed rgba(102,126,234,0.4); border-radius:8px; margin:5px;" onclick="addNewColumn()">
                <i class="fas fa-plus-circle fa-2x" style="color: #667eea;"></i>
                <div style="margin-top:8px; color:#667eea; font-weight:600;">Ajouter une phase</div>
            </div>
        </div>
        {% endif %}
    </div>
</div>

<!-- Task Detail Modal -->"""

if old in content and 'Ajouter une phase' not in content:
    content = content.replace(old, new)
    with open(FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print('[OK] Add column button added')
else:
    print('[SKIP] Already exists or pattern not found')
