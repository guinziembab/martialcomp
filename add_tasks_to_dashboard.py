#!/usr/bin/env python3
"""Add assigned tasks section to practitioner dashboard."""

VIEW = "/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/practitioner_dashboard.py"
TEMPLATE = "/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/practitioner/dashboard.html"

# === 1. Add tasks to view context ===
with open(VIEW, 'r', encoding='utf-8') as f:
    view_content = f.read()

# Add task query before context dict
old_context = "    context = {\n        'practitioner': practitioner,"

tasks_query = """    # Get assigned tasks for this user
    user_tasks = []
    try:
        from apps.task_management.models import Task, TaskAssignment
        user_tasks = Task.objects.filter(
            assignments__assignee=request.user,
            assignments__is_active=True
        ).exclude(
            status='done'
        ).select_related('board', 'column').order_by('due_date', '-priority')[:10]
    except Exception:
        pass

    context = {
        'practitioner': practitioner,
        'user_tasks': user_tasks,"""

if 'user_tasks' not in view_content:
    view_content = view_content.replace(old_context, tasks_query)
    with open(VIEW, 'w', encoding='utf-8') as f:
        f.write(view_content)
    print('[OK] Tasks added to dashboard context')
else:
    print('[SKIP] Tasks already in context')

# === 2. Add tasks section to template ===
with open(TEMPLATE, 'r', encoding='utf-8') as f:
    tmpl = f.read()

if 'user_tasks' not in tmpl:
    # Find the "Notifications" section to insert before it
    marker = None
    for m in ['Notifications', 'notifications', 'Orders in progress', 'Commandes']:
        if m in tmpl:
            # Find the card/section containing this text
            idx = tmpl.index(m)
            # Go back to find the start of this section
            section_start = tmpl.rfind('<div class="card', 0, idx)
            if section_start == -1:
                section_start = tmpl.rfind('<div class="col', 0, idx)
            if section_start > 0:
                marker = section_start
                break

    tasks_html = """
        <!-- Assigned Tasks Section -->
        <div class="card mb-4" style="background: var(--card-bg, #1e293b); border: 1px solid var(--border-color, #334155); border-radius: 12px;">
            <div class="card-header d-flex justify-content-between align-items-center" style="background: transparent; border-bottom: 1px solid var(--border-color, #334155);">
                <h5 class="mb-0" style="color: var(--text-primary, #e2e8f0);">
                    <i class="fas fa-tasks me-2" style="color: #667eea;"></i>{% trans "Mes taches" %}
                </h5>
                <a href="{% url 'task_management:task_list' %}?assigned_to_me=1" class="btn btn-outline-info btn-sm">
                    {% trans "Voir tout" %}
                </a>
            </div>
            <div class="card-body" style="padding: 0;">
                {% if user_tasks %}
                <div class="list-group list-group-flush">
                    {% for task in user_tasks %}
                    <a href="{% url 'task_management:task_detail' task.id %}" class="list-group-item list-group-item-action" style="background:transparent; border-color: var(--border-color, #334155); color: var(--text-primary, #e2e8f0); padding: 12px 16px;">
                        <div class="d-flex justify-content-between align-items-start">
                            <div class="d-flex align-items-center gap-2">
                                {% if task.priority == 'urgent' %}
                                    <i class="fas fa-exclamation-triangle" style="color:#e91e63;"></i>
                                {% elif task.priority == 'high' %}
                                    <i class="fas fa-arrow-up" style="color:#ff5722;"></i>
                                {% elif task.priority == 'medium' %}
                                    <i class="fas fa-minus" style="color:#ff9800;"></i>
                                {% else %}
                                    <i class="fas fa-arrow-down" style="color:#4caf50;"></i>
                                {% endif %}
                                <div>
                                    <strong>{{ task.title }}</strong>
                                    <div style="font-size: 0.8rem; color: var(--text-muted, #94a3b8);">
                                        {{ task.board.name }} &middot; {{ task.column.name }}
                                    </div>
                                </div>
                            </div>
                            <div class="text-end">
                                {% if task.due_date %}
                                <small class="{% if task.is_overdue %}text-danger{% else %}text-muted{% endif %}">
                                    <i class="fas fa-calendar-alt me-1"></i>{{ task.due_date|date:"d/m" }}
                                </small>
                                {% endif %}
                            </div>
                        </div>
                    </a>
                    {% endfor %}
                </div>
                {% else %}
                <div class="text-center py-4" style="color: var(--text-muted, #94a3b8);">
                    <i class="fas fa-check-circle fa-2x mb-2" style="display:block; color:#4caf50;"></i>
                    {% trans "Aucune tache en cours" %}
                </div>
                {% endif %}
            </div>
        </div>

"""

    if marker:
        tmpl = tmpl[:marker] + tasks_html + tmpl[marker:]
        with open(TEMPLATE, 'w', encoding='utf-8') as f:
            f.write(tmpl)
        print(f'[OK] Tasks section added to dashboard template (before pos {marker})')
    else:
        print('[WARN] Could not find insertion point in template')
else:
    print('[SKIP] Tasks section already in template')

print('[DONE]')
