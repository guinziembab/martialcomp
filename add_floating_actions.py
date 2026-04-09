#!/usr/bin/env python3
"""Add floating action bar for category selection."""

FILE = '/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/club/competition_management_pro.html'

with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# Add floating bar HTML before the list view table
floating_bar = '''
            <!-- Floating action bar for selected categories -->
            <div id="categoryActionBar" style="display:none; position:fixed; bottom:20px; left:50%; transform:translateX(-50%); z-index:1040; background:#1e293b; border:2px solid #C9A227; border-radius:12px; padding:10px 20px; box-shadow:0 8px 32px rgba(0,0,0,0.4); display:none;">
                <div class="d-flex align-items-center gap-3">
                    <span id="selectedCount" style="color:#C9A227; font-weight:bold;">0 selectionnees</span>
                    <button class="btn btn-warning btn-sm" id="floatMerge" onclick="mergeSelectedCategories()" style="display:none;">
                        <i class="fas fa-compress-arrows-alt me-1"></i>Fusionner
                    </button>
                    <button class="btn btn-danger btn-sm" id="floatDelete" onclick="deleteEmptyCategories()" style="display:none;">
                        <i class="fas fa-trash me-1"></i>Supprimer vides
                    </button>
                    <button class="btn btn-outline-secondary btn-sm" onclick="clearSelection()">
                        <i class="fas fa-times me-1"></i>Annuler
                    </button>
                </div>
            </div>
'''

marker = '<div id="categoriesListView"'
if marker in content and 'categoryActionBar' not in content:
    content = content.replace(marker, floating_bar + '\n            ' + marker)
    print('[OK] Floating action bar added')

# Update the JS updateMergeButton to also update floating bar
old_fn_end = "if (deleteBtn) deleteBtn.style.display = (checked.length >= 1 && hasEmpty) ? 'inline-block' : 'none';\n}"

new_fn_end = """if (deleteBtn) deleteBtn.style.display = (checked.length >= 1 && hasEmpty) ? 'inline-block' : 'none';

    // Update floating bar
    var actionBar = document.getElementById('categoryActionBar');
    var floatMerge = document.getElementById('floatMerge');
    var floatDelete = document.getElementById('floatDelete');
    var countEl = document.getElementById('selectedCount');
    if (actionBar) {
        if (checked.length > 0) {
            actionBar.style.display = 'block';
            if (countEl) countEl.textContent = checked.length + ' selectionnee(s)';
            if (floatMerge) floatMerge.style.display = checked.length >= 2 ? 'inline-block' : 'none';
            if (floatDelete) floatDelete.style.display = hasEmpty ? 'inline-block' : 'none';
        } else {
            actionBar.style.display = 'none';
        }
    }
}"""

if old_fn_end in content:
    content = content.replace(old_fn_end, new_fn_end)
    print('[OK] Floating bar JS updated')

# Add clearSelection function
if 'function clearSelection()' not in content:
    clear_fn = """
function clearSelection() {
    document.querySelectorAll('.category-select').forEach(function(cb) { cb.checked = false; });
    var selectAll = document.getElementById('selectAllCategories');
    if (selectAll) selectAll.checked = false;
    updateMergeButton();
}

"""
    merge_marker = 'function mergeSelectedCategories()'
    if merge_marker in content:
        content = content.replace(merge_marker, clear_fn + merge_marker)
        print('[OK] clearSelection function added')

with open(FILE, 'w', encoding='utf-8') as f:
    f.write(content)
print('[DONE]')
