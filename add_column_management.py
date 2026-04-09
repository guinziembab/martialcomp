#!/usr/bin/env python3
"""Add column management UI (add/rename/delete) to kanban board."""

TEMPLATE = '/var/www/vhosts/martialcomp.com/httpdocs/apps/task_management/templates/task_management/kanban/kanban_board.html'
VIEWS = '/var/www/vhosts/martialcomp.com/httpdocs/apps/task_management/views/boards.py'
URLS = '/var/www/vhosts/martialcomp.com/httpdocs/apps/task_management/urls.py'

import shutil

def fix():
    # === 1. Add column_rename view ===
    with open(VIEWS, 'r', encoding='utf-8') as f:
        views_content = f.read()

    if 'def column_rename' not in views_content:
        rename_view = '''

@login_required
@require_POST
def column_rename(request, board_id, column_id):
    """Rename a column via AJAX"""
    board = get_object_or_404(Board, id=board_id)
    column = get_object_or_404(Column, id=column_id, board=board)

    if not check_board_access(request.user, board, 'edit'):
        return JsonResponse({'success': False, 'error': 'Permission insuffisante'}, status=403)

    import json
    try:
        data = json.loads(request.body)
        new_name = data.get('name', '').strip()
        if not new_name:
            return JsonResponse({'success': False, 'error': 'Nom requis'}, status=400)
        column.name = new_name
        column.save(update_fields=['name'])
        return JsonResponse({'success': True, 'name': new_name})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

'''
        # Insert before board_export
        marker = '@login_required\ndef board_export('
        if marker in views_content:
            views_content = views_content.replace(marker, rename_view + marker)
            with open(VIEWS, 'w', encoding='utf-8') as f:
                f.write(views_content)
            print('[OK] column_rename view added')
        else:
            print('[WARN] Could not find insertion point for rename view')
    else:
        print('[SKIP] column_rename already exists')

    # === 2. Add URL for column_rename ===
    with open(URLS, 'r', encoding='utf-8') as f:
        urls_content = f.read()

    if 'column_rename' not in urls_content:
        old_url = "path('boards/<int:board_id>/columns/<int:column_id>/delete/', views.column_delete, name='column_delete'),"
        new_url = old_url + "\n    path('boards/<int:board_id>/columns/<int:column_id>/rename/', views.column_rename, name='column_rename'),"
        urls_content = urls_content.replace(old_url, new_url)
        with open(URLS, 'w', encoding='utf-8') as f:
            f.write(urls_content)
        print('[OK] column_rename URL added')
    else:
        print('[SKIP] column_rename URL already exists')

    # === 3. Update kanban template ===
    shutil.copy2(TEMPLATE, TEMPLATE + '.backup_colmgmt')

    with open(TEMPLATE, 'r', encoding='utf-8') as f:
        content = f.read()

    # 3a. Add rename and delete options to column dropdown
    old_dropdown = '''<button class="dropdown-item" onclick="editColumnWip({{ column.id }}, {{ column.wip_limit|default:'null' }})">
                                    <i class="fas fa-limit me-2"></i>{% trans "Limite WIP" %}
                                </button>'''

    new_dropdown = '''<button class="dropdown-item" onclick="renameColumn({{ column.id }}, '{{ column.name|escapejs }}')">
                                    <i class="fas fa-edit me-2"></i>{% trans "Renommer" %}
                                </button>
                                <button class="dropdown-item" onclick="editColumnWip({{ column.id }}, {{ column.wip_limit|default:'null' }})">
                                    <i class="fas fa-tachometer-alt me-2"></i>{% trans "Limite WIP" %}
                                </button>
                                <div class="dropdown-divider"></div>
                                <button class="dropdown-item text-danger" onclick="deleteColumn({{ column.id }}, '{{ column.name|escapejs }}', {{ column.task_count }})">
                                    <i class="fas fa-trash me-2"></i>{% trans "Supprimer" %}
                                </button>'''

    if old_dropdown in content:
        content = content.replace(old_dropdown, new_dropdown)
        print('[OK] Column dropdown updated with rename/delete')
    else:
        print('[WARN] Column dropdown pattern not found')

    # 3b. Add "Add column" button after the last column
    old_end = '</div> <!-- kanban-board -->'
    if old_end not in content:
        # Try alternative
        old_end = '    </div>\n    <!-- kanban-board -->'

    # Find the closing of kanban-board div
    kanban_board_marker = 'class="kanban-board"'
    if kanban_board_marker in content and 'addColumnBtn' not in content:
        # Find end of kanban columns loop
        endfor_marker = '{% endfor %}\n            </div>'
        if endfor_marker in content:
            add_col_html = '''{% endfor %}

                <!-- Add Column Button -->
                {% if can_admin %}
                <div class="kanban-column" style="min-width:250px; max-width:250px; opacity:0.6;">
                    <div class="kanban-column-header" style="cursor:pointer; text-align:center; padding:20px;" onclick="addNewColumn()" id="addColumnBtn">
                        <i class="fas fa-plus-circle fa-2x" style="color: #667eea;"></i>
                        <div style="margin-top:8px; color:#667eea; font-weight:600;">{% trans "Ajouter une phase" %}</div>
                    </div>
                </div>
                {% endif %}
            </div>'''
            content = content.replace(endfor_marker, add_col_html)
            print('[OK] Add column button added')
        else:
            print('[WARN] endfor marker not found')
    else:
        print('[SKIP] Add column button already exists or kanban-board not found')

    # 3c. Add JS functions for column management
    column_js = '''
// === Column Management ===
function renameColumn(columnId, currentName) {
    var newName = prompt('Renommer la colonne:', currentName);
    if (!newName || newName === currentName) return;

    var csrfToken = '';
    var cookieMatch = document.cookie.match(/csrftoken=([^;]+)/);
    if (cookieMatch) csrfToken = cookieMatch[1];

    fetch(window.location.pathname.replace('/kanban/', '/columns/' + columnId + '/rename/'), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({name: newName})
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.success) location.reload();
        else alert('Erreur: ' + (data.error || 'Echec'));
    })
    .catch(function(e) { alert('Erreur: ' + e.message); });
}

function deleteColumn(columnId, columnName, taskCount) {
    if (taskCount > 0) {
        alert('Impossible de supprimer la colonne "' + columnName + '" car elle contient ' + taskCount + ' tache(s). Deplacez-les d\\'abord.');
        return;
    }
    if (!confirm('Supprimer la colonne "' + columnName + '" ?')) return;

    var csrfToken = '';
    var cookieMatch = document.cookie.match(/csrftoken=([^;]+)/);
    if (cookieMatch) csrfToken = cookieMatch[1];

    fetch(window.location.pathname.replace('/kanban/', '/columns/' + columnId + '/delete/'), {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.success) location.reload();
        else alert('Erreur: ' + (data.error || 'Echec'));
    })
    .catch(function(e) { alert('Erreur: ' + e.message); });
}

function addNewColumn() {
    var name = prompt('Nom de la nouvelle phase:');
    if (!name) return;

    var csrfToken = '';
    var cookieMatch = document.cookie.match(/csrftoken=([^;]+)/);
    if (cookieMatch) csrfToken = cookieMatch[1];

    var formData = new FormData();
    formData.append('name', name);
    formData.append('csrfmiddlewaretoken', csrfToken);

    fetch(window.location.pathname.replace('/kanban/', '/columns/'), {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken
        },
        body: formData
    })
    .then(function(r) {
        if (r.redirected || r.ok) location.reload();
        else alert('Erreur lors de la creation');
    })
    .catch(function(e) { alert('Erreur: ' + e.message); });
}
'''

    if 'function renameColumn' not in content:
        # Insert before </script> at the end
        last_script = content.rfind('</script>')
        if last_script > 0:
            content = content[:last_script] + column_js + '\n</script>' + content[last_script + len('</script>'):]
            print('[OK] Column management JS added')
    else:
        print('[SKIP] Column JS already exists')

    with open(TEMPLATE, 'w', encoding='utf-8') as f:
        f.write(content)

    print('\n[DONE] Column management UI added.')

if __name__ == '__main__':
    fix()
