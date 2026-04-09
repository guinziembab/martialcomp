#!/usr/bin/env python3
"""Fix the category count badge to show per-tatami count."""

tpl_path = "/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/club/competition_management_pro.html"
with open(tpl_path, "r") as f:
    tpl = f.read()

# Replace the badge that uses categories_by_tatami dict length
old = """                                <span class="badge bg-light text-dark">
                                    {% with categories_by_tatami|default:'' as cats %}
                                        {% if cats %}{{ cats|length }}{% else %}0{% endif %}
                                    {% endwith %} {% trans "catégories" %}
                                </span>"""

new = """                                <span class="badge bg-light text-dark tatami-cat-count" data-tatami="{{ tatami_num }}">
                                    <span class="cat-count-num">0</span> {% trans "catégories" %}
                                </span>"""

if old in tpl:
    tpl = tpl.replace(old, new, 1)
    print("Badge fixed")
else:
    print("Badge pattern NOT FOUND")

# Add a small JS to count categories per tatami after page load
js_count = """
<script>
// Count categories per tatami for badge display
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.tatami-card').forEach(function(card) {
        var tatamiNum = card.dataset.tatami;
        var catItems = card.querySelectorAll('.schedule-category-item');
        var badge = card.querySelector('.cat-count-num');
        if (badge) badge.textContent = catItems.length;
    });
});
</script>
"""

# Insert before the last {% endblock %}
last_endblock = tpl.rfind("{% endblock %}")
if last_endblock != -1:
    tpl = tpl[:last_endblock] + js_count + "\n" + tpl[last_endblock:]
    print("JS counter added")

with open(tpl_path, "w") as f:
    f.write(tpl)
print("DONE")
