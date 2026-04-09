#!/usr/bin/env python3
"""Add delete empty categories button to competition_management_pro.html."""

FILE = '/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/club/competition_management_pro.html'

with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# 1. Add delete empty button after merge button
marker = 'id="btnMergeCategories"'
delete_btn_id = 'id="btnDeleteEmpty"'

if marker in content and delete_btn_id not in content:
    # Find the closing </button> after merge button
    idx = content.index(marker)
    # Find the next </button> after this marker
    close_idx = content.index('</button>', idx) + len('</button>')
    insert_html = '''
                    <button class="btn btn-danger btn-sm" id="btnDeleteEmpty" style="display:none;" onclick="deleteEmptyCategories()">
                        <i class="fas fa-trash me-1"></i>Supprimer vides
                    </button>'''
    content = content[:close_idx] + insert_html + content[close_idx:]
    changes += 1
    print('[OK] Delete empty button added')

# 2. Update updateMergeButton to show delete button for empty categories
old_update = "var btn = document.getElementById('btnMergeCategories');\n    if (btn) btn.style.display = checked >= 2 ? 'inline-block' : 'none';"

new_update = """var mergeBtn = document.getElementById('btnMergeCategories');
    var deleteBtn = document.getElementById('btnDeleteEmpty');
    if (mergeBtn) mergeBtn.style.display = checked.length >= 2 ? 'inline-block' : 'none';
    var hasEmpty = false;
    checked.forEach(function(cb) {
        var row = cb.closest('tr');
        if (row) {
            var badge = row.querySelector('.badge');
            if (badge && badge.textContent.trim() === '0') hasEmpty = true;
        }
    });
    if (deleteBtn) deleteBtn.style.display = (checked.length >= 1 && hasEmpty) ? 'inline-block' : 'none';"""

if old_update in content:
    # Also need to fix the checked variable - it was .length before
    old_checked = "var checked = document.querySelectorAll('.category-select:checked').length;"
    new_checked = "var checked = document.querySelectorAll('.category-select:checked');"
    content = content.replace(old_checked, new_checked)
    content = content.replace(old_update, new_update)
    changes += 1
    print('[OK] updateMergeButton updated')
else:
    print('[SKIP] updateMergeButton already updated or not found')

# 3. Add deleteEmptyCategories function
if 'deleteEmptyCategories' not in content:
    delete_fn = """
function deleteEmptyCategories() {
    var checked = document.querySelectorAll('.category-select:checked');
    var emptyIds = [];
    var emptyNames = [];
    checked.forEach(function(cb) {
        var row = cb.closest('tr');
        if (row) {
            var badge = row.querySelector('.badge');
            if (badge && badge.textContent.trim() === '0') {
                emptyIds.push(cb.value);
                var name = row.querySelector('strong');
                if (name) emptyNames.push(name.textContent);
            }
        }
    });
    if (emptyIds.length === 0) {
        alert('Aucune categorie vide selectionnee.');
        return;
    }
    if (!confirm('Supprimer ' + emptyIds.length + ' categorie(s) vide(s) ?\\n\\n' + emptyNames.join('\\n'))) return;

    var lang = document.documentElement.lang || 'en';
    var promises = emptyIds.map(function(catId) {
        var formData = new FormData();
        formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
        formData.append('category_id', catId);
        return fetch('/' + lang + '/competitions/competitions/' + competitionId + '/categories/delete/', {
            method: 'POST',
            body: formData
        });
    });
    Promise.all(promises).then(function() { location.reload(); }).catch(function() { location.reload(); });
}

"""
    # Insert before mergeSelectedCategories
    merge_marker = 'function mergeSelectedCategories()'
    if merge_marker in content:
        content = content.replace(merge_marker, delete_fn + merge_marker)
        changes += 1
        print('[OK] deleteEmptyCategories function added')
else:
    print('[SKIP] deleteEmptyCategories already exists')

if changes > 0:
    with open(FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'[DONE] {changes} changes applied')
else:
    print('[DONE] No changes needed')
