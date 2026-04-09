#!/usr/bin/env python3
FILE = '/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/club/competition_management_pro.html'

with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

fn = '''function deleteEmptyCategories() {
    var checked = document.querySelectorAll('.category-select:checked');
    var emptyIds = [];
    var emptyNames = [];
    checked.forEach(function(cb) {
        var row = cb.closest('tr');
        if (row) {
            var badge = row.querySelector('.count-badge');
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
    var csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    var deleted = 0;
    var total = emptyIds.length;

    emptyIds.forEach(function(catId) {
        var formData = new FormData();
        formData.append('csrfmiddlewaretoken', csrfToken);
        formData.append('category_id', catId);
        fetch('/' + lang + '/competitions/competitions/' + competitionId + '/categories/delete/', {
            method: 'POST',
            body: formData
        })
        .then(function(r) { return r.text(); })
        .then(function() {
            deleted++;
            if (deleted >= total) location.reload();
        })
        .catch(function() {
            deleted++;
            if (deleted >= total) location.reload();
        });
    });
}

'''

marker = 'function clearSelection()'
if 'function deleteEmptyCategories()' not in content:
    content = content.replace(marker, fn + marker)
    with open(FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print('[OK] deleteEmptyCategories function added')
else:
    print('[SKIP] already exists')
