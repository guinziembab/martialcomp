#!/usr/bin/env python3
"""Add column filters to category list view."""

FILE = '/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/club/competition_management_pro.html'

with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# 1. Replace table headers with filter dropdowns
old_headers = '''<thead style="background: rgba(45,55,72,0.8);">
                            <tr>
                                <th style="width:30px;"><input type="checkbox" id="selectAllCategories" onchange="toggleAllCategories(this)"></th>
                                <th>{% trans "Catégorie" %}</th>
                                <th>{% trans "Type" %}</th>
                                <th>{% trans "Genre" %}</th>
                                <th>{% trans "Âge" %}</th>
                                <th style="width:100px;" class="text-center">{% trans "Inscrits" %}</th>
                                <th style="width:100px;" class="text-center">{% trans "Actions" %}</th>
                            </tr>
                        </thead>'''

new_headers = '''<thead style="background: rgba(45,55,72,0.8);">
                            <tr>
                                <th style="width:30px;"><input type="checkbox" id="selectAllCategories" onchange="toggleAllCategories(this)"></th>
                                <th>
                                    {% trans "Catégorie" %}
                                    <div style="margin-top:4px;">
                                        <input type="text" id="filterName" onkeyup="filterCategoryTable()" placeholder="Rechercher..." style="width:100%; padding:2px 6px; font-size:0.75rem; border:1px solid rgba(255,255,255,0.2); border-radius:4px; background:rgba(0,0,0,0.2); color:#e2e8f0;">
                                    </div>
                                </th>
                                <th>
                                    {% trans "Type" %}
                                    <div style="margin-top:4px;">
                                        <select id="filterType" onchange="filterCategoryTable()" style="width:100%; padding:2px 4px; font-size:0.75rem; border:1px solid rgba(255,255,255,0.2); border-radius:4px; background:rgba(0,0,0,0.2); color:#e2e8f0;">
                                            <option value="">{% trans "Tous" %}</option>
                                            {% for type in competition_types %}
                                            <option value="{{ type.name }}">{{ type.name }}</option>
                                            {% endfor %}
                                        </select>
                                    </div>
                                </th>
                                <th>
                                    {% trans "Genre" %}
                                    <div style="margin-top:4px;">
                                        <select id="filterGender" onchange="filterCategoryTable()" style="width:100%; padding:2px 4px; font-size:0.75rem; border:1px solid rgba(255,255,255,0.2); border-radius:4px; background:rgba(0,0,0,0.2); color:#e2e8f0;">
                                            <option value="">{% trans "Tous" %}</option>
                                            <option value="F">F</option>
                                            <option value="M">M</option>
                                            <option value="Mixte">Mixte</option>
                                        </select>
                                    </div>
                                </th>
                                <th>{% trans "Âge" %}</th>
                                <th style="width:100px;" class="text-center">
                                    {% trans "Inscrits" %}
                                    <div style="margin-top:4px;">
                                        <select id="filterCount" onchange="filterCategoryTable()" style="width:100%; padding:2px 4px; font-size:0.75rem; border:1px solid rgba(255,255,255,0.2); border-radius:4px; background:rgba(0,0,0,0.2); color:#e2e8f0;">
                                            <option value="">{% trans "Tous" %}</option>
                                            <option value="0">= 0</option>
                                            <option value="lt3">&lt; 3</option>
                                            <option value="lt5">&lt; 5</option>
                                            <option value="gte5">&ge; 5</option>
                                        </select>
                                    </div>
                                </th>
                                <th style="width:100px;" class="text-center">{% trans "Actions" %}</th>
                            </tr>
                        </thead>'''

if old_headers in content:
    content = content.replace(old_headers, new_headers)
    changes += 1
    print('[OK] Filter headers added')
else:
    print('[WARN] Header pattern not found')

# 2. Add filter JS function
filter_js = """
function filterCategoryTable() {
    var nameFilter = (document.getElementById('filterName').value || '').toLowerCase();
    var typeFilter = document.getElementById('filterType').value;
    var genderFilter = document.getElementById('filterGender').value;
    var countFilter = document.getElementById('filterCount').value;

    var rows = document.querySelectorAll('#categoriesListView tbody tr[data-category-id]');
    var visible = 0;

    rows.forEach(function(row) {
        var cells = row.querySelectorAll('td');
        if (cells.length < 7) return;

        var name = (cells[1].textContent || '').toLowerCase();
        var type = (cells[2].textContent || '').trim();
        var gender = (cells[3].textContent || '').trim();
        var countBadge = row.querySelector('.count-badge');
        var count = countBadge ? parseInt(countBadge.textContent.trim()) : 0;

        var show = true;

        if (nameFilter && name.indexOf(nameFilter) === -1) show = false;
        if (typeFilter && type.indexOf(typeFilter) === -1) show = false;
        if (genderFilter && gender.indexOf(genderFilter) === -1) show = false;
        if (countFilter) {
            if (countFilter === '0' && count !== 0) show = false;
            else if (countFilter === 'lt3' && count >= 3) show = false;
            else if (countFilter === 'lt5' && count >= 5) show = false;
            else if (countFilter === 'gte5' && count < 5) show = false;
        }

        row.style.display = show ? '' : 'none';
        if (show) visible++;
    });
}

"""

marker = 'function showCategoryView('
if 'function filterCategoryTable()' not in content:
    content = content.replace(marker, filter_js + marker)
    changes += 1
    print('[OK] Filter JS function added')
else:
    print('[SKIP] Filter function already exists')

if changes > 0:
    with open(FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'[DONE] {changes} changes')
else:
    print('[DONE] No changes')
