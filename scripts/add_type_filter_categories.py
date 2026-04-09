#!/usr/bin/env python3
"""Add competition type filter to the by-category view."""

# 1. Add competition_types to the view context
view_path = "/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/combat.py"
with open(view_path) as f:
    vc = f.read()

# Add competition_types to context before the return render
old_ctx = "context['total_registrations'] = CompetitionRegistration.objects.filter(competition=competition).count()"
new_ctx = """context['total_registrations'] = CompetitionRegistration.objects.filter(competition=competition).count()
    context['competition_types'] = competition.competition_types.all()"""

if old_ctx in vc and "context['competition_types']" not in vc:
    vc = vc.replace(old_ctx, new_ctx)
    with open(view_path, 'w') as f:
        f.write(vc)
    print("View context updated OK")
else:
    print("View already has competition_types or pattern not found")

# 2. Add data-type-id to category sections and type filter UI
tmpl_path = "/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/combat/liste_equipes_par_categorie.html"
with open(tmpl_path) as f:
    tc = f.read()

# 2a. Add data-type-id to category-section divs
old_cat_div = '{% for category in categories %}\n<div class="category-section">'
new_cat_div = '{% for category in categories %}\n<div class="category-section" data-type-id="{% if category.competition_type %}{{ category.competition_type.id }}{% endif %}" data-type-name="{% if category.competition_type %}{{ category.competition_type.name }}{% endif %}">'

if old_cat_div in tc and 'data-type-id' not in tc:
    tc = tc.replace(old_cat_div, new_cat_div)
    print("Category section data-type-id added OK")
else:
    print("Category section already has data-type-id or pattern not found")

# 2b. Add filter buttons before "Tout ouvrir" buttons
old_buttons = '''<div class="d-flex justify-content-end mb-3 gap-2">
    <button class="btn btn-sm btn-outline-secondary" onclick="expandAllCategories()">'''

new_buttons = '''<!-- Competition Type Filter -->
{% if competition_types %}
<div class="d-flex flex-wrap gap-2 mb-3 align-items-center">
    <span style="color:var(--text-secondary);font-size:0.85rem;font-weight:600;">
        <i class="fas fa-filter me-1"></i>{% translate "Type:" %}
    </span>
    <button class="btn btn-sm btn-outline-primary type-filter-btn active" onclick="filterByType('all', this)">
        {% translate "Tous" %}
    </button>
    {% for ct in competition_types %}
    <button class="btn btn-sm btn-outline-primary type-filter-btn" onclick="filterByType('{{ ct.id }}', this)">
        {{ ct.name }}
    </button>
    {% endfor %}
</div>
{% endif %}

<div class="d-flex justify-content-end mb-3 gap-2">
    <button class="btn btn-sm btn-outline-secondary" onclick="expandAllCategories()">'''

if old_buttons in tc:
    tc = tc.replace(old_buttons, new_buttons)
    print("Filter buttons added OK")
else:
    print("Filter buttons pattern not found")

# 2c. Add JS for filtering
filter_js = '''
<script>
function filterByType(typeId, btn) {
    // Update active button
    document.querySelectorAll('.type-filter-btn').forEach(function(b) {
        b.classList.remove('active');
        b.classList.remove('btn-primary');
        b.classList.add('btn-outline-primary');
    });
    btn.classList.add('active');
    btn.classList.remove('btn-outline-primary');
    btn.classList.add('btn-primary');

    // Filter categories
    document.querySelectorAll('.category-section[data-type-id]').forEach(function(section) {
        if (typeId === 'all' || section.dataset.typeId === typeId) {
            section.style.display = '';
        } else {
            section.style.display = 'none';
        }
    });

    // Update count
    var visible = document.querySelectorAll('.category-section[data-type-id]:not([style*="display: none"])').length;
    var total = document.querySelectorAll('.category-section[data-type-id]').length;
    var counter = document.getElementById('filteredCount');
    if (counter) {
        counter.textContent = typeId === 'all' ? total : visible + '/' + total;
    }
}
</script>
'''

# Insert before the last endblock
last_endblock = tc.rfind('{% endblock %}')
if last_endblock != -1 and 'filterByType' not in tc:
    tc = tc[:last_endblock] + filter_js + '\n' + tc[last_endblock:]
    print("Filter JS added OK")
else:
    print("Filter JS already exists or endblock not found")

with open(tmpl_path, 'w') as f:
    f.write(tc)
print("Template saved OK")
