#!/bin/bash
# Créer tous les templates federation avec le nouveau style

echo "================================================"
echo "📄 CRÉATION DES TEMPLATES AVEC ONGLETS"
echo "================================================"
echo ""

ssh martialcomp-production 'cd /var/www/vhosts/martialcomp.com/httpdocs && bash' << 'EOF'

# Template de base pour hériter
cat > apps/competitions/templates/competitions/dashboard/federation_base.html << 'TEMPLATE_EOF'
{% load i18n static %}
<div class="dashboard-container">
  <!-- En-tête avec onglets -->
  <div class="dashboard-header">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h1 class="h3 mb-0">
        <i class="fas fa-building text-primary mr-2"></i>
        {{ federation.name }}
      </h1>
      <span class="badge badge-primary">{% trans "Fédération" %}</span>
    </div>
    
    <!-- Navigation par onglets -->
    <ul class="nav nav-tabs" role="tablist">
      <li class="nav-item">
        <a class="nav-link {% if active_tab == 'dashboard' %}active{% endif %}" href="{% url 'competitions:dashboard:federation_detail' federation.id %}">
          <i class="fas fa-tachometer-alt mr-1"></i> {% trans "Tableau de bord" %}
        </a>
      </li>
      <li class="nav-item">
        <a class="nav-link {% if active_tab == 'clubs' %}active{% endif %}" href="{% url 'competitions:dashboard:federation_manage_clubs' federation.id %}">
          <i class="fas fa-users mr-1"></i> {% trans "Clubs" %}
        </a>
      </li>
      <li class="nav-item">
        <a class="nav-link {% if active_tab == 'competitions' %}active{% endif %}" href="{% url 'competitions:dashboard:federation_manage_competitions' federation.id %}">
          <i class="fas fa-trophy mr-1"></i> {% trans "Compétitions" %}
        </a>
      </li>
      <li class="nav-item">
        <a class="nav-link {% if active_tab == 'practitioners' %}active{% endif %}" href="{% url 'competitions:dashboard:federation_manage_practitioners' federation.id %}">
          <i class="fas fa-user-friends mr-1"></i> {% trans "Pratiquants" %}
        </a>
      </li>
      <li class="nav-item">
        <a class="nav-link {% if active_tab == 'judges' %}active{% endif %}" href="{% url 'competitions:dashboard:federation_manage_judges' federation.id %}">
          <i class="fas fa-gavel mr-1"></i> {% trans "Juges" %}
        </a>
      </li>
      <li class="nav-item">
        <a class="nav-link {% if active_tab == 'licenses' %}active{% endif %}" href="{% url 'competitions:dashboard:federation_manage_licenses' federation.id %}">
          <i class="fas fa-id-card mr-1"></i> {% trans "Licences" %}
        </a>
      </li>
      <li class="nav-item">
        <a class="nav-link {% if active_tab == 'certifications' %}active{% endif %}" href="{% url 'competitions:dashboard:federation_manage_certifications' federation.id %}">
          <i class="fas fa-certificate mr-1"></i> {% trans "Certifications" %}
        </a>
      </li>
      <li class="nav-item">
        <a class="nav-link {% if active_tab == 'reports' %}active{% endif %}" href="{% url 'competitions:dashboard:federation_manage_reports' federation.id %}">
          <i class="fas fa-chart-bar mr-1"></i> {% trans "Rapports" %}
        </a>
      </li>
      <li class="nav-item">
        <a class="nav-link {% if active_tab == 'settings' %}active{% endif %}" href="{% url 'competitions:dashboard:federation_manage_settings' federation.id %}">
          <i class="fas fa-cog mr-1"></i> {% trans "Paramètres" %}
        </a>
      </li>
    </ul>
  </div>

  <!-- Contenu principal -->
  <div class="main-content">
    {% block tab_content %}{% endblock %}
  </div>
</div>
TEMPLATE_EOF

echo "✅ Template de base créé"

# Template Clubs
cat > apps/competitions/templates/competitions/dashboard/federation_clubs.html << 'TEMPLATE_EOF'
{% extends "competitions/dashboard/federation.html" %}
{% load i18n static %}

{% block content %}
{% include "competitions/dashboard/federation_base.html" with active_tab="clubs" %}
{% endblock %}

{% block tab_content %}
<div class="d-flex justify-content-between align-items-center mb-4">
  <h2 class="section-title mb-0">{% trans "Clubs affiliés" %}</h2>
  <button class="btn btn-primary btn-sm">
    <i class="fas fa-plus mr-1"></i> {% trans "Ajouter un club" %}
  </button>
</div>

<!-- Statistiques -->
<div class="row mb-4">
  <div class="col-md-6">
    <div class="stat-card text-center">
      <h3 class="text-primary">{{ total_clubs }}</h3>
      <p class="text-muted mb-0">{% trans "Total des clubs" %}</p>
    </div>
  </div>
  <div class="col-md-6">
    <div class="stat-card text-center">
      <h3 class="text-success">{{ total_practitioners }}</h3>
      <p class="text-muted mb-0">{% trans "Total des pratiquants" %}</p>
    </div>
  </div>
</div>

<!-- Liste des clubs -->
<div class="stat-card">
  {% if clubs_data %}
  <div class="table-responsive">
    <table class="table">
      <thead>
        <tr>
          <th>{% trans "Nom du club" %}</th>
          <th>{% trans "Ville" %}</th>
          <th>{% trans "Pratiquants" %}</th>
          <th>{% trans "Actions" %}</th>
        </tr>
      </thead>
      <tbody>
        {% for club_info in clubs_data %}
        <tr>
          <td>{{ club_info.club.name }}</td>
          <td>{{ club_info.city|default:"-" }}</td>
          <td>
            <span class="badge badge-info">{{ club_info.practitioners_count }}</span>
          </td>
          <td>
            <div class="btn-group btn-group-sm">
              <button class="btn btn-outline-primary" title="{% trans 'Voir' %}">
                <i class="fas fa-eye"></i>
              </button>
              <button class="btn btn-outline-secondary" title="{% trans 'Modifier' %}">
                <i class="fas fa-edit"></i>
              </button>
            </div>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  {% else %}
  <div class="text-center py-5">
    <i class="fas fa-users fa-3x text-muted mb-3"></i>
    <p class="text-muted">{% trans "Aucun club affilié pour le moment." %}</p>
  </div>
  {% endif %}
</div>
{% endblock %}
TEMPLATE_EOF

echo "✅ Template clubs créé"

# Template Compétitions
cat > apps/competitions/templates/competitions/dashboard/federation_competitions.html << 'TEMPLATE_EOF'
{% extends "competitions/dashboard/federation.html" %}
{% load i18n static %}

{% block content %}
{% include "competitions/dashboard/federation_base.html" with active_tab="competitions" %}
{% endblock %}

{% block tab_content %}
<div class="d-flex justify-content-between align-items-center mb-4">
  <h2 class="section-title mb-0">{% trans "Compétitions" %}</h2>
  <button class="btn btn-success btn-sm">
    <i class="fas fa-plus mr-1"></i> {% trans "Nouvelle compétition" %}
  </button>
</div>

<!-- Statistiques -->
<div class="row mb-4">
  <div class="col-md-4">
    <div class="stat-card text-center">
      <h3 class="text-primary">{{ total_competitions }}</h3>
      <p class="text-muted mb-0">{% trans "Total" %}</p>
    </div>
  </div>
  <div class="col-md-4">
    <div class="stat-card text-center">
      <h3 class="text-success">{{ ongoing_competitions.count }}</h3>
      <p class="text-muted mb-0">{% trans "En cours" %}</p>
    </div>
  </div>
  <div class="col-md-4">
    <div class="stat-card text-center">
      <h3 class="text-info">{{ upcoming_competitions.count }}</h3>
      <p class="text-muted mb-0">{% trans "À venir" %}</p>
    </div>
  </div>
</div>

<!-- Compétitions en cours -->
{% if ongoing_competitions %}
<h3 class="h5 mb-3">{% trans "En cours" %}</h3>
<div class="stat-card mb-4">
  <div class="table-responsive">
    <table class="table">
      <thead>
        <tr>
          <th>{% trans "Nom" %}</th>
          <th>{% trans "Dates" %}</th>
          <th>{% trans "Lieu" %}</th>
          <th>{% trans "Actions" %}</th>
        </tr>
      </thead>
      <tbody>
        {% for comp in ongoing_competitions %}
        <tr>
          <td>{{ comp.name }}</td>
          <td>{{ comp.start_date|date:"d/m" }} - {{ comp.end_date|date:"d/m/Y" }}</td>
          <td>{{ comp.location|default:"-" }}</td>
          <td>
            <a href="#" class="btn btn-sm btn-primary">
              <i class="fas fa-eye"></i>
            </a>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
{% endif %}

<!-- Prochaines compétitions -->
<h3 class="h5 mb-3">{% trans "À venir" %}</h3>
<div class="stat-card">
  {% if upcoming_competitions %}
  <div class="table-responsive">
    <table class="table">
      <thead>
        <tr>
          <th>{% trans "Nom" %}</th>
          <th>{% trans "Date" %}</th>
          <th>{% trans "Lieu" %}</th>
          <th>{% trans "Actions" %}</th>
        </tr>
      </thead>
      <tbody>
        {% for comp in upcoming_competitions %}
        <tr>
          <td>{{ comp.name }}</td>
          <td>{{ comp.start_date|date:"d/m/Y" }}</td>
          <td>{{ comp.location|default:"-" }}</td>
          <td>
            <div class="btn-group btn-group-sm">
              <a href="#" class="btn btn-outline-primary">
                <i class="fas fa-eye"></i>
              </a>
              <a href="#" class="btn btn-outline-secondary">
                <i class="fas fa-edit"></i>
              </a>
            </div>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  {% else %}
  <div class="text-center py-4">
    <p class="text-muted">{% trans "Aucune compétition à venir." %}</p>
  </div>
  {% endif %}
</div>
{% endblock %}
TEMPLATE_EOF

echo "✅ Template compétitions créé"

# Template Juges
cat > apps/competitions/templates/competitions/dashboard/federation_judges.html << 'TEMPLATE_EOF'
{% extends "competitions/dashboard/federation.html" %}
{% load i18n static %}

{% block content %}
{% include "competitions/dashboard/federation_base.html" with active_tab="judges" %}
{% endblock %}

{% block tab_content %}
<div class="d-flex justify-content-between align-items-center mb-4">
  <h2 class="section-title mb-0">{% trans "Juges et arbitres" %}</h2>
  <button class="btn btn-warning btn-sm">
    <i class="fas fa-plus mr-1"></i> {% trans "Ajouter un juge" %}
  </button>
</div>

<!-- Statistiques -->
<div class="row mb-4">
  <div class="col-md-4">
    <div class="stat-card text-center">
      <i class="fas fa-gavel fa-2x text-warning mb-2"></i>
      <h3>{{ total_judges }}</h3>
      <p class="text-muted mb-0">{% trans "Total des juges" %}</p>
    </div>
  </div>
  <div class="col-md-8">
    <div class="stat-card">
      <h5 class="mb-3">{% trans "Répartition par niveau" %}</h5>
      <div class="row">
        {% for level, count in level_stats.items %}
        <div class="col-6 mb-2">
          <span class="badge badge-secondary">{{ level }}</span>
          <span class="float-right">{{ count }}</span>
        </div>
        {% endfor %}
      </div>
    </div>
  </div>
</div>

<!-- Liste des juges -->
<div class="stat-card">
  {% if judges %}
  <div class="table-responsive">
    <table class="table">
      <thead>
        <tr>
          <th>{% trans "Nom" %}</th>
          <th>{% trans "Niveau" %}</th>
          <th>{% trans "Spécialité" %}</th>
          <th>{% trans "Statut" %}</th>
          <th>{% trans "Actions" %}</th>
        </tr>
      </thead>
      <tbody>
        {% for judge in judges %}
        <tr>
          <td>{{ judge.user.get_full_name }}</td>
          <td>
            <span class="badge badge-info">{{ judge.get_level_display|default:judge.level }}</span>
          </td>
          <td>{{ judge.specialty|default:"-" }}</td>
          <td>
            {% if judge.is_active %}
            <span class="badge badge-success">{% trans "Actif" %}</span>
            {% else %}
            <span class="badge badge-secondary">{% trans "Inactif" %}</span>
            {% endif %}
          </td>
          <td>
            <div class="btn-group btn-group-sm">
              <button class="btn btn-outline-primary">
                <i class="fas fa-eye"></i>
              </button>
              <button class="btn btn-outline-secondary">
                <i class="fas fa-edit"></i>
              </button>
            </div>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  {% else %}
  <div class="text-center py-5">
    <i class="fas fa-gavel fa-3x text-muted mb-3"></i>
    <p class="text-muted">{% trans "Aucun juge enregistré." %}</p>
  </div>
  {% endif %}
</div>
{% endblock %}
TEMPLATE_EOF

echo "✅ Template juges créé"

# Template Rapports
cat > apps/competitions/templates/competitions/dashboard/federation_reports.html << 'TEMPLATE_EOF'
{% extends "competitions/dashboard/federation.html" %}
{% load i18n static %}

{% block content %}
{% include "competitions/dashboard/federation_base.html" with active_tab="reports" %}
{% endblock %}

{% block tab_content %}
<h2 class="section-title">{% trans "Rapports et statistiques" %}</h2>

<!-- Vue d'ensemble -->
<div class="row mb-4">
  <div class="col-md-3 col-6 mb-3">
    <div class="stat-card text-center">
      <i class="fas fa-users fa-2x text-primary mb-2"></i>
      <h3>{{ stats.clubs_count }}</h3>
      <p class="text-muted mb-0">{% trans "Clubs" %}</p>
    </div>
  </div>
  <div class="col-md-3 col-6 mb-3">
    <div class="stat-card text-center">
      <i class="fas fa-user-friends fa-2x text-success mb-2"></i>
      <h3>{{ stats.practitioners_count }}</h3>
      <p class="text-muted mb-0">{% trans "Pratiquants" %}</p>
    </div>
  </div>
  <div class="col-md-3 col-6 mb-3">
    <div class="stat-card text-center">
      <i class="fas fa-trophy fa-2x text-warning mb-2"></i>
      <h3>{{ stats.competitions_count }}</h3>
      <p class="text-muted mb-0">{% trans "Compétitions" %}</p>
    </div>
  </div>
  <div class="col-md-3 col-6 mb-3">
    <div class="stat-card text-center">
      <i class="fas fa-gavel fa-2x text-info mb-2"></i>
      <h3>{{ stats.judges_count }}</h3>
      <p class="text-muted mb-0">{% trans "Juges" %}</p>
    </div>
  </div>
</div>

<!-- Options d'export -->
<h3 class="h5 mb-3">{% trans "Export des données" %}</h3>
<div class="stat-card">
  <div class="row">
    <div class="col-md-4 mb-3">
      <button class="btn btn-outline-primary btn-block">
        <i class="fas fa-download mr-1"></i> {% trans "Export clubs (CSV)" %}
      </button>
    </div>
    <div class="col-md-4 mb-3">
      <button class="btn btn-outline-success btn-block">
        <i class="fas fa-download mr-1"></i> {% trans "Export pratiquants (Excel)" %}
      </button>
    </div>
    <div class="col-md-4 mb-3">
      <button class="btn btn-outline-info btn-block">
        <i class="fas fa-file-pdf mr-1"></i> {% trans "Rapport complet (PDF)" %}
      </button>
    </div>
  </div>
</div>
{% endblock %}
TEMPLATE_EOF

echo "✅ Tous les templates créés"

echo ""
echo "Redémarrage du service..."
sudo systemctl restart martialcomp

echo "✅ TERMINÉ !"

EOF

echo ""
echo "================================================"
echo "✅ TEMPLATES CRÉÉS AVEC SUCCÈS"
echo "================================================"
echo ""
echo "Tous les templates ont été créés avec :"
echo "- Design avec onglets comme le dashboard club"
echo "- Pas de scroll excessif"
echo "- Navigation intuitive"
echo "- Style moderne et cohérent"