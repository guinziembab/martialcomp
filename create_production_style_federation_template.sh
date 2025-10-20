#!/bin/bash

echo "=== Création d'un template federation.html style production ==="
echo ""

# Créer un backup du template actuel
cp /mnt/c/martial_hub_django/martialcomp/apps/competitions/templates/competitions/dashboard/federation.html \
   /mnt/c/martial_hub_django/martialcomp/apps/competitions/templates/competitions/dashboard/federation.html.backup_$(date +%Y%m%d_%H%M%S)

# Créer le nouveau template avec des liens directs
cat > /mnt/c/martial_hub_django/martialcomp/apps/competitions/templates/competitions/dashboard/federation_production_style.html << 'EOF'
{% extends "base.html" %}
{% load i18n %}
{% load static %}
{% load custom_filters %}
{% load family_badges %}

{% block title %}{% trans "Tableau de bord Fédération" %} | {{ federation.name }}{% endblock %}

{% block extra_css %}
<style>
  /* Variables de couleur - FÉDÉRATION */
  :root {
    --primary: #dc3545;
    --primary-light: #fde9eb;
    --primary-dark: #c82333;
    --secondary: #6c757d;
    --success: #28a745;
    --info: #17a2b8;
    --warning: #ffc107;
    --danger: #dc3545;
  }

  .dashboard-container {
    padding: 2rem;
    background-color: #f5f7fa;
    min-height: calc(100vh - 56px);
  }

  .dashboard-header {
    background: white;
    padding: 2rem;
    border-radius: 10px;
    margin-bottom: 2rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  }

  .management-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
  }

  .management-card {
    background: white;
    border-radius: 10px;
    padding: 1.5rem;
    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    transition: transform 0.3s, box-shadow 0.3s;
  }

  .management-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
  }

  .management-link {
    display: flex;
    align-items: center;
    text-decoration: none;
    color: inherit;
  }

  .management-icon {
    font-size: 2.5rem;
    margin-right: 1.5rem;
    color: var(--primary);
  }

  .management-content h3 {
    margin: 0;
    font-size: 1.25rem;
    color: #333;
  }

  .management-content p {
    margin: 0.5rem 0 0 0;
    color: #6c757d;
    font-size: 0.9rem;
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
  }

  .stat-card {
    background: white;
    border-radius: 10px;
    padding: 1.5rem;
    text-align: center;
    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
  }

  .stat-value {
    font-size: 2rem;
    font-weight: bold;
    color: var(--primary);
  }

  .stat-label {
    color: #6c757d;
    font-size: 0.9rem;
    margin-top: 0.5rem;
  }
</style>
{% endblock %}

{% block content %}
<div class="dashboard-container">
  <!-- En-tête du dashboard -->
  <div class="dashboard-header">
    <div class="d-flex justify-content-between align-items-center">
      <div>
        <h1>{{ federation.name }}</h1>
        <p class="text-muted mb-0">{% trans "Tableau de bord Fédération" %}</p>
      </div>
      <div>
        {% if federation.logo %}
        <img src="{{ federation.logo.url }}" alt="{{ federation.name }}" style="height: 60px;">
        {% endif %}
      </div>
    </div>
  </div>

  <!-- Statistiques -->
  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-value">{{ clubs_count }}</div>
      <div class="stat-label">{% trans "Clubs" %}</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">{{ practitioners_count }}</div>
      <div class="stat-label">{% trans "Pratiquants" %}</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">{{ competitions_count }}</div>
      <div class="stat-label">{% trans "Compétitions" %}</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">{{ disciplines|length }}</div>
      <div class="stat-label">{% trans "Disciplines" %}</div>
    </div>
  </div>

  <!-- Grille de gestion -->
  <h2 class="mb-4">{% trans "Gestion" %}</h2>
  <div class="management-grid">
    <div class="management-card">
      <a href="{% url 'competitions:dashboard:federation_manage_clubs' federation.id %}" class="management-link">
        <i class="fas fa-building management-icon"></i>
        <div class="management-content">
          <h3>{% trans "Clubs" %}</h3>
          <p>{% trans "Gérer les clubs affiliés" %}</p>
        </div>
      </a>
    </div>

    <div class="management-card">
      <a href="{% url 'competitions:dashboard:federation_manage_competitions' federation.id %}" class="management-link">
        <i class="fas fa-trophy management-icon"></i>
        <div class="management-content">
          <h3>{% trans "Compétitions" %}</h3>
          <p>{% trans "Organiser et gérer les compétitions" %}</p>
        </div>
      </a>
    </div>

    <div class="management-card">
      <a href="{% url 'competitions:dashboard:federation_manage_practitioners' federation.id %}" class="management-link">
        <i class="fas fa-users management-icon"></i>
        <div class="management-content">
          <h3>{% trans "Pratiquants" %}</h3>
          <p>{% trans "Gérer les pratiquants" %}</p>
        </div>
      </a>
    </div>

    <div class="management-card">
      <a href="{% url 'competitions:dashboard:federation_manage_judges' federation.id %}" class="management-link">
        <i class="fas fa-gavel management-icon"></i>
        <div class="management-content">
          <h3>{% trans "Juges" %}</h3>
          <p>{% trans "Gérer les juges et arbitres" %}</p>
        </div>
      </a>
    </div>

    <div class="management-card">
      <a href="{% url 'competitions:dashboard:federation_manage_licenses' federation.id %}" class="management-link">
        <i class="fas fa-id-card management-icon"></i>
        <div class="management-content">
          <h3>{% trans "Licences" %}</h3>
          <p>{% trans "Gérer les licences fédérales" %}</p>
        </div>
      </a>
    </div>

    <div class="management-card">
      <a href="{% url 'competitions:dashboard:federation_manage_certifications' federation.id %}" class="management-link">
        <i class="fas fa-certificate management-icon"></i>
        <div class="management-content">
          <h3>{% trans "Certifications" %}</h3>
          <p>{% trans "Gérer les certifications" %}</p>
        </div>
      </a>
    </div>

    <div class="management-card">
      <a href="{% url 'competitions:dashboard:federation_manage_reports' federation.id %}" class="management-link">
        <i class="fas fa-chart-bar management-icon"></i>
        <div class="management-content">
          <h3>{% trans "Rapports" %}</h3>
          <p>{% trans "Statistiques et rapports" %}</p>
        </div>
      </a>
    </div>

    <div class="management-card">
      <a href="{% url 'competitions:dashboard:federation_manage_settings' federation.id %}" class="management-link">
        <i class="fas fa-cog management-icon"></i>
        <div class="management-content">
          <h3>{% trans "Paramètres" %}</h3>
          <p>{% trans "Configuration de la fédération" %}</p>
        </div>
      </a>
    </div>
  </div>

  <!-- Compétitions récentes -->
  {% if upcoming_competitions or recent_competitions %}
  <div class="row mt-4">
    {% if upcoming_competitions %}
    <div class="col-md-6">
      <div class="card">
        <div class="card-header">
          <h5 class="mb-0">{% trans "Compétitions à venir" %}</h5>
        </div>
        <div class="card-body">
          <ul class="list-unstyled">
            {% for competition in upcoming_competitions %}
            <li class="mb-2">
              <a href="{% url 'competitions:competition_detail' competition.id %}">
                {{ competition.name }}
              </a>
              <small class="text-muted d-block">{{ competition.start_date|date:"d/m/Y" }}</small>
            </li>
            {% endfor %}
          </ul>
        </div>
      </div>
    </div>
    {% endif %}

    {% if recent_competitions %}
    <div class="col-md-6">
      <div class="card">
        <div class="card-header">
          <h5 class="mb-0">{% trans "Compétitions récentes" %}</h5>
        </div>
        <div class="card-body">
          <ul class="list-unstyled">
            {% for competition in recent_competitions %}
            <li class="mb-2">
              <a href="{% url 'competitions:competition_detail' competition.id %}">
                {{ competition.name }}
              </a>
              <small class="text-muted d-block">{{ competition.end_date|date:"d/m/Y" }}</small>
            </li>
            {% endfor %}
          </ul>
        </div>
      </div>
    </div>
    {% endif %}
  </div>
  {% endif %}
</div>
{% endblock %}
EOF

echo "Template créé: federation_production_style.html"
echo ""
echo "Pour utiliser ce template, modifiez la vue federation_dashboard dans federations.py"
echo "Changez la ligne:"
echo "    return render(request, 'competitions/dashboard/federation.html', context)"
echo "Par:"
echo "    return render(request, 'competitions/dashboard/federation_production_style.html', context)"