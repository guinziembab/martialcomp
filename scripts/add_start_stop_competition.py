#!/usr/bin/env python3
"""Add Start/Stop competition buttons to schedule overview."""

# === 1. Add views to schedule.py ===
view_path = "/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/management/schedule.py"

with open(view_path, "r") as f:
    view_content = f.read()

# Add start/stop views at the end of the file
start_stop_views = '''

@login_required
@competition_management_permission_required
@require_POST
def start_competition(request, competition_id):
    """Demarre la competition - enregistre l'heure de debut reelle."""
    competition = get_object_or_404(Competition, pk=competition_id)
    competition.status = 'ongoing'
    competition.stream_started_at = timezone.now()
    competition.stream_ended_at = None
    competition.save(update_fields=['status', 'stream_started_at', 'stream_ended_at'])

    # Log the change
    schedule = CompetitionSchedule.objects.filter(competition=competition).first()
    if schedule:
        ScheduleChange.objects.create(
            competition_schedule=schedule,
            change_type='time_change',
            changed_by=request.user,
            description=_("Competition demarree a {}").format(timezone.localtime().strftime('%H:%M'))
        )

    messages.success(request, _("La competition a ete demarree."))
    return redirect('competitions:management:schedule_overview', competition_id=competition_id)


@login_required
@competition_management_permission_required
@require_POST
def stop_competition(request, competition_id):
    """Arrete la competition - enregistre l'heure de fin reelle."""
    competition = get_object_or_404(Competition, pk=competition_id)
    competition.status = 'completed'
    competition.stream_ended_at = timezone.now()
    competition.save(update_fields=['status', 'stream_ended_at'])

    # Log the change
    schedule = CompetitionSchedule.objects.filter(competition=competition).first()
    if schedule:
        ScheduleChange.objects.create(
            competition_schedule=schedule,
            change_type='time_change',
            changed_by=request.user,
            description=_("Competition terminee a {}").format(timezone.localtime().strftime('%H:%M'))
        )

    messages.success(request, _("La competition a ete arretee."))
    return redirect('competitions:management:schedule_overview', competition_id=competition_id)
'''

if 'def start_competition' not in view_content:
    view_content += start_stop_views
    with open(view_path, "w") as f:
        f.write(view_content)
    print("Views added OK")
else:
    print("Views already exist")

# === 2. Add URLs ===
url_path = "/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/urls/management.py"

with open(url_path, "r") as f:
    url_content = f.read()

if 'start_competition' not in url_content:
    # Find the import line for schedule
    url_content = url_content.replace(
        "from apps.competitions.views.management import schedule",
        "from apps.competitions.views.management import schedule"
    )

    # Add URL patterns before the last ]
    last_bracket = url_content.rfind(']')
    if last_bracket != -1:
        new_urls = """
    # Start/Stop competition
    path('<int:competition_id>/start/', schedule.start_competition, name='start_competition'),
    path('<int:competition_id>/stop/', schedule.stop_competition, name='stop_competition'),
"""
        url_content = url_content[:last_bracket] + new_urls + url_content[last_bracket:]
        with open(url_path, "w") as f:
            f.write(url_content)
        print("URLs added OK")
else:
    print("URLs already exist")

# === 3. Patch template to add buttons ===
template_path = "/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/management/schedule.html"

with open(template_path, "r") as f:
    tmpl = f.read()

if 'start_competition' not in tmpl:
    # Add buttons after "Publier" button section
    old_publish = '''{% if not schedule.is_published %}
                    <a href="{% url 'competitions:management:schedule_publish' competition.id %}" class="btn-success-dark" onclick="return confirm('{% trans "Publier le planning ?" %}')">
                        <i class="fas fa-paper-plane me-1"></i>{% trans "Publier" %}
                    </a>
                    {% endif %}'''

    new_publish = '''{% if not schedule.is_published %}
                    <a href="{% url 'competitions:management:schedule_publish' competition.id %}" class="btn-success-dark" onclick="return confirm('{% trans 'Publier le planning ?' %}')">
                        <i class="fas fa-paper-plane me-1"></i>{% trans "Publier" %}
                    </a>
                    {% endif %}
                    {% if competition.status != 'ongoing' and competition.status != 'completed' %}
                    <form method="post" action="{% url 'competitions:management:start_competition' competition.id %}" style="display:inline;">
                        {% csrf_token %}
                        <button type="submit" class="btn btn-success btn-sm" onclick="return confirm('Demarrer la competition ?')">
                            <i class="fas fa-play me-1"></i>{% trans "Demarrer" %}
                        </button>
                    </form>
                    {% elif competition.status == 'ongoing' %}
                    <form method="post" action="{% url 'competitions:management:stop_competition' competition.id %}" style="display:inline;">
                        {% csrf_token %}
                        <button type="submit" class="btn btn-danger btn-sm" onclick="return confirm('Arreter la competition ?')">
                            <i class="fas fa-stop me-1"></i>{% trans "Arreter" %}
                        </button>
                    </form>
                    {% endif %}'''

    if old_publish in tmpl:
        tmpl = tmpl.replace(old_publish, new_publish)
        print("Template buttons added OK (exact match)")
    else:
        # Try simpler replacement
        old_simple = "{% endif %}\n                    <div class=\"dropdown\">"
        new_simple = """{% endif %}
                    {% if competition.status != 'ongoing' and competition.status != 'completed' %}
                    <form method="post" action="{% url 'competitions:management:start_competition' competition.id %}" style="display:inline;">
                        {% csrf_token %}
                        <button type="submit" class="btn btn-success btn-sm" onclick="return confirm('Demarrer la competition ?')">
                            <i class="fas fa-play me-1"></i>{% trans "Demarrer" %}
                        </button>
                    </form>
                    {% elif competition.status == 'ongoing' %}
                    <form method="post" action="{% url 'competitions:management:stop_competition' competition.id %}" style="display:inline;">
                        {% csrf_token %}
                        <button type="submit" class="btn btn-danger btn-sm" onclick="return confirm('Arreter la competition ?')">
                            <i class="fas fa-stop me-1"></i>{% trans "Arreter" %}
                        </button>
                    </form>
                    {% endif %}
                    <div class="dropdown">"""

        if old_simple in tmpl:
            tmpl = tmpl.replace(old_simple, new_simple, 1)
            print("Template buttons added OK (simple match)")
        else:
            print("WARNING: Could not find template insertion point for buttons")

    # Add live duration display in Information section
    old_info = '''<h5 class="mb-0">{% trans "Informations" %}</h5>'''
    new_info = '''<h5 class="mb-0">{% trans "Informations" %}</h5>
                    {% if competition.status == 'ongoing' and competition.stream_started_at %}
                    <span class="badge bg-success" id="liveBadge">
                        <i class="fas fa-circle me-1" style="animation: blink 1s infinite;"></i>LIVE
                    </span>
                    {% elif competition.status == 'completed' and competition.stream_started_at %}
                    <span class="badge bg-secondary">TERMINEE</span>
                    {% endif %}'''

    if old_info in tmpl:
        tmpl = tmpl.replace(old_info, new_info, 1)
        print("Template info badge added OK")

    # Add duration info in the Information card body
    # Find where tatami_count is displayed
    old_tatami_info = '''<td>{{ tatamis.count }}</td>'''
    new_tatami_info = '''<td>{{ tatamis.count }}</td>
                            </tr>
                            {% if competition.stream_started_at %}
                            <tr>
                                <td>{% trans "Debut reel" %}</td>
                                <td>{{ competition.stream_started_at|date:"H:i" }}</td>
                            </tr>
                            {% if competition.stream_ended_at %}
                            <tr>
                                <td>{% trans "Fin reelle" %}</td>
                                <td>{{ competition.stream_ended_at|date:"H:i" }}</td>
                            </tr>
                            <tr>
                                <td><strong>{% trans "Duree reelle" %}</strong></td>
                                <td><strong id="realDuration">{{ competition.stream_started_at|timesince:competition.stream_ended_at }}</strong></td>
                            </tr>
                            {% elif competition.status == 'ongoing' %}
                            <tr>
                                <td><strong>{% trans "Temps ecoule" %}</strong></td>
                                <td><strong id="elapsedTime" data-start="{{ competition.stream_started_at|date:'c' }}">--:--</strong></td>
                            </tr>
                            {% endif %}
                            {% endif %}
                            <tr style="display:none">
                            <td>hidden</td'''

    if old_tatami_info in tmpl:
        tmpl = tmpl.replace(old_tatami_info, new_tatami_info, 1)
        print("Template duration info added OK")
    else:
        print("WARNING: Could not find tatami info for duration insert")

    # Add JS for live elapsed time
    elapsed_js = '''
<style>
@keyframes blink { 0%,100%{opacity:1;} 50%{opacity:0.3;} }
</style>
<script>
(function(){
    var el = document.getElementById('elapsedTime');
    if (!el) return;
    var start = new Date(el.dataset.start);
    function update(){
        var now = new Date();
        var diff = Math.floor((now - start) / 1000);
        var h = Math.floor(diff / 3600);
        var m = Math.floor((diff % 3600) / 60);
        var s = diff % 60;
        el.textContent = (h > 0 ? h + 'h ' : '') + (m < 10 ? '0' : '') + m + ':' + (s < 10 ? '0' : '') + s;
    }
    update();
    setInterval(update, 1000);
})();
</script>
'''

    last_endblock = tmpl.rfind('{% endblock %}')
    if last_endblock != -1:
        tmpl = tmpl[:last_endblock] + elapsed_js + '\n' + tmpl[last_endblock:]
        print("Template JS added OK")

    with open(template_path, "w") as f:
        f.write(tmpl)
    print("Template saved OK")
else:
    print("Template already patched")

print("\nAll done!")
