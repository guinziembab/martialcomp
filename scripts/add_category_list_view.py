#!/usr/bin/env python3
"""Add category list view to competition_management_pro.html on production."""

TEMPLATE = '/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/club/competition_management_pro.html'
VIEW = '/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/competition_management_pro.py'

import shutil

def fix():
    # Backup
    shutil.copy2(TEMPLATE, TEMPLATE + '.backup_listview')
    print("[OK] Template backup created")

    with open(TEMPLATE, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Replace the categories tab header to add toggle + merge button
    old_header = '''<div class="d-flex justify-content-between align-items-center mb-4">
                <h3>{% trans "Catégories de la compétition" %}</h3>
                <button class="btn btn-success" data-bs-toggle="modal" data-bs-target="#categoryModal">
                    <i class="fas fa-plus me-2"></i>{% trans "Ajouter une catégorie" %}
                </button>
            </div>

            <div class="row">'''

    new_header = '''<div class="d-flex justify-content-between align-items-center mb-4">
                <h3>{% trans "Catégories de la compétition" %}</h3>
                <div class="d-flex align-items-center gap-2">
                    <div class="btn-group btn-group-sm" id="categoryViewToggle">
                        <button class="btn btn-outline-secondary active" onclick="showCategoryView('card')" title="Vue cartes">
                            <i class="fas fa-th-large"></i>
                        </button>
                        <button class="btn btn-outline-secondary" onclick="showCategoryView('list')" title="Vue liste">
                            <i class="fas fa-list"></i>
                        </button>
                    </div>
                    <button class="btn btn-warning btn-sm" id="btnMergeCategories" style="display:none;" onclick="mergeSelectedCategories()">
                        <i class="fas fa-compress-arrows-alt me-1"></i>{% trans "Fusionner" %}
                    </button>
                    <button class="btn btn-success btn-sm" data-bs-toggle="modal" data-bs-target="#categoryModal">
                        <i class="fas fa-plus me-1"></i>{% trans "Ajouter" %}
                    </button>
                </div>
            </div>

            <!-- List View -->
            <div id="categoriesListView" style="display:none;" class="mb-4">
                <div class="table-responsive">
                    <table class="table table-hover table-sm" style="color: var(--text-primary, #e2e8f0);">
                        <thead style="background: rgba(45,55,72,0.8);">
                            <tr>
                                <th style="width:30px;"><input type="checkbox" id="selectAllCategories" onchange="toggleAllCategories(this)"></th>
                                <th>{% trans "Catégorie" %}</th>
                                <th>{% trans "Type" %}</th>
                                <th>{% trans "Genre" %}</th>
                                <th>{% trans "Âge" %}</th>
                                <th style="width:100px;" class="text-center">{% trans "Inscrits" %}</th>
                                <th style="width:100px;" class="text-center">{% trans "Actions" %}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for category in categories %}
                            <tr data-category-id="{{ category.id }}">
                                <td><input type="checkbox" class="category-select" value="{{ category.id }}" onchange="updateMergeButton()"></td>
                                <td><strong>{{ category.name }}</strong></td>
                                <td>
                                    {% if category.competition_type %}
                                    <span class="badge bg-info" style="font-size:0.75rem;">{{ category.competition_type.name }}</span>
                                    {% else %}-{% endif %}
                                </td>
                                <td>
                                    {% if category.gender == 'male' %}<i class="fas fa-mars text-primary"></i> M
                                    {% elif category.gender == 'female' %}<i class="fas fa-venus text-danger"></i> F
                                    {% elif category.gender == 'mixed' %}<i class="fas fa-venus-mars text-warning"></i> Mixte
                                    {% else %}-{% endif %}
                                </td>
                                <td>
                                    {% if category.min_age or category.max_age %}
                                        {{ category.min_age|default:"" }}{% if category.min_age and category.max_age %}-{% endif %}{{ category.max_age|default:"" }} ans
                                    {% else %}-{% endif %}
                                </td>
                                <td class="text-center">
                                    <span class="badge {% if category.practitioners_count < 3 %}bg-danger{% elif category.practitioners_count < 5 %}bg-warning text-dark{% else %}bg-success{% endif %}" style="font-size:0.85rem; min-width:30px;">
                                        {{ category.practitioners_count }}
                                    </span>
                                </td>
                                <td class="text-center">
                                    <button class="btn btn-sm btn-outline-primary btn-edit-category me-1"
                                        data-category-id="{{ category.id }}"
                                        data-category-name="{{ category.name|escapejs }}"
                                        data-category-type="{{ category.competition_type_id|default:'' }}"
                                        data-category-gender="{% if category.gender == 'male' %}M{% elif category.gender == 'female' %}F{% else %}{% endif %}"
                                        data-category-min-age="{{ category.min_age|default:'' }}"
                                        data-category-max-age="{{ category.max_age|default:'' }}"
                                        data-category-min-weight="{{ category.min_weight|default:'' }}"
                                        data-category-max-weight="{{ category.max_weight|default:'' }}"
                                        data-category-min-grade="{{ category.min_grade|default:'' }}"
                                        data-category-max-grade="{{ category.max_grade|default:'' }}"
                                        data-category-max-participants="{{ category.max_participants|default:'' }}"
                                        title="{% trans 'Modifier' %}">
                                        <i class="fas fa-edit"></i>
                                    </button>
                                    <button class="btn btn-sm btn-outline-danger btn-delete-category"
                                        data-category-id="{{ category.id }}"
                                        data-category-name="{{ category.name|escapejs }}"
                                        title="{% trans 'Supprimer' %}">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </td>
                            </tr>
                            {% empty %}
                            <tr><td colspan="7" class="text-center text-muted">{% trans "Aucune catégorie" %}</td></tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Card View -->
            <div id="categoriesCardView" class="row">'''

    if old_header in content:
        content = content.replace(old_header, new_header)
        print("[OK] Categories header + list view added")
    else:
        print("[WARN] Header pattern not found")

    # 2. Add the JS functions before the last </script> or at end of script block
    js_code = '''
// === Category List/Card Toggle ===
function showCategoryView(view) {
    var cardView = document.getElementById('categoriesCardView');
    var listView = document.getElementById('categoriesListView');
    var buttons = document.querySelectorAll('#categoryViewToggle .btn');

    if (view === 'list') {
        if (cardView) cardView.style.display = 'none';
        if (listView) listView.style.display = 'block';
        buttons[0].classList.remove('active');
        buttons[1].classList.add('active');
    } else {
        if (cardView) cardView.style.display = 'flex';
        if (listView) listView.style.display = 'none';
        buttons[0].classList.add('active');
        buttons[1].classList.remove('active');
    }
}

function toggleAllCategories(checkbox) {
    document.querySelectorAll('.category-select').forEach(function(cb) {
        cb.checked = checkbox.checked;
    });
    updateMergeButton();
}

function updateMergeButton() {
    var checked = document.querySelectorAll('.category-select:checked').length;
    var btn = document.getElementById('btnMergeCategories');
    if (btn) btn.style.display = checked >= 2 ? 'inline-block' : 'none';
}

function mergeSelectedCategories() {
    var checked = document.querySelectorAll('.category-select:checked');
    if (checked.length < 2) {
        alert('Selectionnez au moins 2 categories a fusionner.');
        return;
    }

    var ids = [];
    var names = [];
    checked.forEach(function(cb) {
        ids.push(cb.value);
        var row = cb.closest('tr');
        if (row) names.push(row.querySelector('strong').textContent);
    });

    var msg = 'Fusionner les categories suivantes ?\\n\\n' + names.join('\\n') + '\\n\\nLes pratiquants seront regroupes dans la premiere categorie selectionnee.';
    if (!confirm(msg)) return;

    var formData = new FormData();
    ids.forEach(function(id) { formData.append('category_ids', id); });
    formData.append('target_category_id', ids[0]);
    formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);

    var lang = document.documentElement.lang || 'en';
    fetch('/' + lang + '/competitions/competitions/' + competitionId + '/categories/merge/', {
        method: 'POST',
        body: formData
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.success || data.status === 'success') {
            location.reload();
        } else {
            alert(data.error || data.message || 'Erreur lors de la fusion');
        }
    })
    .catch(function(e) { alert('Erreur: ' + e.message); });
}
'''

    # Find the last </script> before {% endblock %}
    # Insert JS before the closing
    insert_marker = '// === Category List/Card Toggle ==='
    if insert_marker not in content:
        # Find the last </script> tag
        last_script_pos = content.rfind('</script>')
        if last_script_pos > 0:
            content = content[:last_script_pos] + js_code + '\n</script>' + content[last_script_pos + len('</script>'):]
            print("[OK] JS functions added")
        else:
            print("[WARN] Could not find </script> to insert JS")
    else:
        print("[SKIP] JS already added")

    with open(TEMPLATE, 'w', encoding='utf-8') as f:
        f.write(content)

    print("\n[DONE] Category list view added to template.")

if __name__ == '__main__':
    fix()
