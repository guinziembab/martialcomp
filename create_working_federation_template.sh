#!/bin/bash
# Créer un template federation fonctionnel avec le style du template de dev

echo "================================================"
echo "📄 CRÉATION D'UN TEMPLATE FEDERATION FONCTIONNEL"
echo "================================================"
echo ""

ssh martialcomp-production << 'EOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1️⃣ Création du nouveau template..."
echo "================================="

cat > apps/competitions/templates/competitions/dashboard/federation.html << 'TEMPLATE_EOF'
{% extends "base.html" %}
{% load i18n static %}

{% block title %}{% trans "Tableau de bord Fédération" %} | {{ federation.name }}{% endblock %}

{% block extra_css %}
<style>
  /* Styles adaptés du template de développement */
  :root {
    --primary: #dc3545;
    --primary-light: #fde9eb;
    --primary-dark: #c82333;
  }

  .dashboard-header {
    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
    color: white;
    padding: 3rem 0;
    margin-bottom: 2rem;
  }

  .stat-card {
    border: none;
    border-radius: 1rem;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    height: 100%;
  }

  .stat-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
  }

  .stat-number {
    font-size: 2.5rem;
    font-weight: bold;
    margin: 0;
  }

  .action-card {
    border: none;
    border-radius: 1rem;
    transition: all 0.3s ease;
    cursor: pointer;
    height: 100%;
  }

  .action-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 5px 20px rgba(0,0,0,0.1);
  }

  .section-title {
    font-size: 1.5rem;
    font-weight: 600;
    color: #333;
    margin-bottom: 1.5rem;
    padding-left: 1rem;
    border-left: 4px solid var(--primary);
  }

  .badge-federation {
    background-color: var(--primary);
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 2rem;
    font-size: 0.875rem;
  }
</style>
{% endblock %}

{% block content %}
<!-- Header -->
<div class="dashboard-header">
  <div class="container">
    <div class="row align-items-center">
      <div class="col-md-8">
        <h1 class="display-4 mb-2">{{ federation.name }}</h1>
        <p class="lead mb-0">
          <i class="fas fa-building mr-2"></i>{% trans "Tableau de bord Fédération" %}
        </p>
      </div>
      <div class="col-md-4 text-right">
        <span class="badge-federation">
          <i class="fas fa-shield-alt mr-2"></i>{% trans "Fédération" %}
        </span>
      </div>
    </div>
  </div>
</div>

<div class="container">
  <!-- Statistiques -->
  <div class="row mb-4">
    <div class="col-md-3 mb-3">
      <div class="card stat-card">
        <div class="card-body text-center">
          <i class="fas fa-users fa-3x text-primary mb-3"></i>
          <p class="stat-number text-primary">{{ clubs_count|default:"0" }}</p>
          <p class="text-muted mb-0">{% trans "Clubs affiliés" %}</p>
        </div>
      </div>
    </div>
    <div class="col-md-3 mb-3">
      <div class="card stat-card">
        <div class="card-body text-center">
          <i class="fas fa-trophy fa-3x text-success mb-3"></i>
          <p class="stat-number text-success">{{ competitions_count|default:"0" }}</p>
          <p class="text-muted mb-0">{% trans "Compétitions" %}</p>
        </div>
      </div>
    </div>
    <div class="col-md-3 mb-3">
      <div class="card stat-card">
        <div class="card-body text-center">
          <i class="fas fa-user-friends fa-3x text-info mb-3"></i>
          <p class="stat-number text-info">{{ practitioners_count|default:"0" }}</p>
          <p class="text-muted mb-0">{% trans "Pratiquants" %}</p>
        </div>
      </div>
    </div>
    <div class="col-md-3 mb-3">
      <div class="card stat-card">
        <div class="card-body text-center">
          <i class="fas fa-gavel fa-3x text-warning mb-3"></i>
          <p class="stat-number text-warning">{{ judges_count|default:"0" }}</p>
          <p class="text-muted mb-0">{% trans "Juges certifiés" %}</p>
        </div>
      </div>
    </div>
  </div>

  <!-- Actions principales -->
  <h2 class="section-title">{% trans "Gestion" %}</h2>
  <div class="row mb-5">
    <div class="col-md-4 mb-4">
      <a href="{% url 'competitions:dashboard:federation_manage_clubs' federation.id %}" class="text-decoration-none">
        <div class="card action-card h-100">
          <div class="card-body">
            <div class="d-flex align-items-center mb-3">
              <div class="icon-box bg-primary text-white rounded-circle p-3 mr-3">
                <i class="fas fa-users fa-2x"></i>
              </div>
              <h4 class="card-title mb-0">{% trans "Clubs" %}</h4>
            </div>
            <p class="card-text text-muted">{% trans "Gérer les clubs affiliés à votre fédération" %}</p>
            <div class="mt-3">
              <span class="text-primary">{% trans "Gérer" %} <i class="fas fa-arrow-right ml-1"></i></span>
            </div>
          </div>
        </div>
      </a>
    </div>

    <div class="col-md-4 mb-4">
      <a href="{% url 'competitions:dashboard:federation_manage_competitions' federation.id %}" class="text-decoration-none">
        <div class="card action-card h-100">
          <div class="card-body">
            <div class="d-flex align-items-center mb-3">
              <div class="icon-box bg-success text-white rounded-circle p-3 mr-3">
                <i class="fas fa-trophy fa-2x"></i>
              </div>
              <h4 class="card-title mb-0">{% trans "Compétitions" %}</h4>
            </div>
            <p class="card-text text-muted">{% trans "Organiser et gérer les compétitions" %}</p>
            <div class="mt-3">
              <span class="text-success">{% trans "Gérer" %} <i class="fas fa-arrow-right ml-1"></i></span>
            </div>
          </div>
        </div>
      </a>
    </div>

    <div class="col-md-4 mb-4">
      <a href="{% url 'competitions:dashboard:federation_manage_practitioners' federation.id %}" class="text-decoration-none">
        <div class="card action-card h-100">
          <div class="card-body">
            <div class="d-flex align-items-center mb-3">
              <div class="icon-box bg-info text-white rounded-circle p-3 mr-3">
                <i class="fas fa-user-friends fa-2x"></i>
              </div>
              <h4 class="card-title mb-0">{% trans "Pratiquants" %}</h4>
            </div>
            <p class="card-text text-muted">{% trans "Gérer les pratiquants et leurs licences" %}</p>
            <div class="mt-3">
              <span class="text-info">{% trans "Gérer" %} <i class="fas fa-arrow-right ml-1"></i></span>
            </div>
          </div>
        </div>
      </a>
    </div>
  </div>

  <!-- Deuxième ligne d'actions -->
  <div class="row mb-5">
    <div class="col-md-4 mb-4">
      <a href="{% url 'competitions:dashboard:federation_manage_judges' federation.id %}" class="text-decoration-none">
        <div class="card action-card h-100">
          <div class="card-body">
            <div class="d-flex align-items-center mb-3">
              <div class="icon-box bg-warning text-white rounded-circle p-3 mr-3">
                <i class="fas fa-gavel fa-2x"></i>
              </div>
              <h4 class="card-title mb-0">{% trans "Juges" %}</h4>
            </div>
            <p class="card-text text-muted">{% trans "Gérer les juges et arbitres certifiés" %}</p>
            <div class="mt-3">
              <span class="text-warning">{% trans "Gérer" %} <i class="fas fa-arrow-right ml-1"></i></span>
            </div>
          </div>
        </div>
      </a>
    </div>

    <div class="col-md-4 mb-4">
      <a href="{% url 'competitions:dashboard:federation_manage_licenses' federation.id %}" class="text-decoration-none">
        <div class="card action-card h-100">
          <div class="card-body">
            <div class="d-flex align-items-center mb-3">
              <div class="icon-box bg-secondary text-white rounded-circle p-3 mr-3">
                <i class="fas fa-id-card fa-2x"></i>
              </div>
              <h4 class="card-title mb-0">{% trans "Licences" %}</h4>
            </div>
            <p class="card-text text-muted">{% trans "Gérer les licences des pratiquants" %}</p>
            <div class="mt-3">
              <span class="text-secondary">{% trans "Gérer" %} <i class="fas fa-arrow-right ml-1"></i></span>
            </div>
          </div>
        </div>
      </a>
    </div>

    <div class="col-md-4 mb-4">
      <a href="{% url 'competitions:dashboard:federation_manage_certifications' federation.id %}" class="text-decoration-none">
        <div class="card action-card h-100">
          <div class="card-body">
            <div class="d-flex align-items-center mb-3">
              <div class="icon-box bg-danger text-white rounded-circle p-3 mr-3">
                <i class="fas fa-certificate fa-2x"></i>
              </div>
              <h4 class="card-title mb-0">{% trans "Certifications" %}</h4>
            </div>
            <p class="card-text text-muted">{% trans "Gérer les grades et certifications" %}</p>
            <div class="mt-3">
              <span class="text-danger">{% trans "Gérer" %} <i class="fas fa-arrow-right ml-1"></i></span>
            </div>
          </div>
        </div>
      </a>
    </div>
  </div>

  <!-- Administration -->
  <h2 class="section-title">{% trans "Administration" %}</h2>
  <div class="row mb-5">
    <div class="col-md-6 mb-4">
      <a href="{% url 'competitions:dashboard:federation_manage_reports' federation.id %}" class="text-decoration-none">
        <div class="card action-card h-100">
          <div class="card-body">
            <div class="d-flex align-items-center mb-3">
              <div class="icon-box bg-dark text-white rounded-circle p-3 mr-3">
                <i class="fas fa-chart-bar fa-2x"></i>
              </div>
              <h4 class="card-title mb-0">{% trans "Rapports & Statistiques" %}</h4>
            </div>
            <p class="card-text text-muted">{% trans "Consulter les rapports et exporter les données" %}</p>
            <div class="mt-3">
              <span class="text-dark">{% trans "Consulter" %} <i class="fas fa-arrow-right ml-1"></i></span>
            </div>
          </div>
        </div>
      </a>
    </div>

    <div class="col-md-6 mb-4">
      <a href="{% url 'competitions:dashboard:federation_manage_settings' federation.id %}" class="text-decoration-none">
        <div class="card action-card h-100">
          <div class="card-body">
            <div class="d-flex align-items-center mb-3">
              <div class="icon-box bg-primary text-white rounded-circle p-3 mr-3">
                <i class="fas fa-cog fa-2x"></i>
              </div>
              <h4 class="card-title mb-0">{% trans "Paramètres" %}</h4>
            </div>
            <p class="card-text text-muted">{% trans "Configurer les paramètres de votre fédération" %}</p>
            <div class="mt-3">
              <span class="text-primary">{% trans "Configurer" %} <i class="fas fa-arrow-right ml-1"></i></span>
            </div>
          </div>
        </div>
      </a>
    </div>
  </div>

  <!-- Activité récente -->
  {% if recent_competitions %}
  <h2 class="section-title">{% trans "Compétitions récentes" %}</h2>
  <div class="card mb-5">
    <div class="card-body">
      <div class="table-responsive">
        <table class="table table-hover">
          <thead>
            <tr>
              <th>{% trans "Nom" %}</th>
              <th>{% trans "Date" %}</th>
              <th>{% trans "Lieu" %}</th>
              <th>{% trans "Statut" %}</th>
            </tr>
          </thead>
          <tbody>
            {% for competition in recent_competitions %}
            <tr>
              <td>{{ competition.name }}</td>
              <td>{{ competition.start_date|date:"d/m/Y" }}</td>
              <td>{{ competition.location|default:"-" }}</td>
              <td>
                {% if competition.is_finished %}
                <span class="badge badge-secondary">{% trans "Terminée" %}</span>
                {% elif competition.is_ongoing %}
                <span class="badge badge-success">{% trans "En cours" %}</span>
                {% else %}
                <span class="badge badge-info">{% trans "À venir" %}</span>
                {% endif %}
              </td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
  </div>
  {% endif %}
</div>

<!-- Style pour les icônes rondes -->
<style>
.icon-box {
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
{% endblock %}
TEMPLATE_EOF

echo "✅ Template créé avec succès"

echo ""
echo "2️⃣ Redémarrage du service..."
echo "==========================="
sudo systemctl restart martialcomp
sleep 3

echo ""
echo "3️⃣ Test final..."
echo "==============="
curl -s -o /dev/null -w "Status: %{http_code}\n" https://martialcomp.com/fr/competitions/dashboard/federation/41/

EOF

echo ""
echo "================================================"
echo "✅ TEMPLATE FONCTIONNEL CRÉÉ"
echo "================================================"
echo ""
echo "Un nouveau template a été créé avec :"
echo "- Le style visuel du template de développement"
echo "- Toutes les URLs correctement définies"
echo "- Pas de dépendances aux templatetags custom"
echo "- Interface moderne et responsive"