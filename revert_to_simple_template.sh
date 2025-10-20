#\!/bin/bash
# Revenir au template simple qui fonctionne

echo "================================================"
echo "🔧 RETOUR AU TEMPLATE SIMPLE FONCTIONNEL"
echo "================================================"
echo ""

ssh martialcomp-production << 'REMOTE_COMMANDS'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1️⃣ Retour au template simple..."
echo "=============================="
sed -i "s/'competitions\/dashboard\/federation\.html'/'competitions\/dashboard\/federation_simple.html'/g" \
    apps/competitions/views/dashboard/federations.py

echo "✅ Vue modifiée pour utiliser federation_simple.html"

echo ""
echo "2️⃣ Vérification du contenu du template simple..."
echo "=============================================="
echo "📋 Template simple actuel:"
cat apps/competitions/templates/competitions/dashboard/federation_simple.html  < /dev/null |  head -20

echo ""
echo "3️⃣ Amélioration du template simple..."
echo "===================================="
# Ajouter plus de contenu au template simple
cat > apps/competitions/templates/competitions/dashboard/federation_simple.html << 'TEMPLATE_EOF'
{% extends "base.html" %}
{% load i18n static %}

{% block title %}{{ title }} - {{ federation.name }}{% endblock %}

{% block extra_css %}
<style>
.dashboard-card {
    transition: transform 0.2s;
    height: 100%;
}
.dashboard-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}
.stat-number {
    font-size: 2.5rem;
    font-weight: bold;
    color: #007bff;
}
.section-header {
    border-bottom: 3px solid #007bff;
    padding-bottom: 10px;
    margin-bottom: 20px;
}
</style>
{% endblock %}

{% block content %}
<div class="container-fluid mt-4">
    <div class="row mb-4">
        <div class="col-12">
            <h1 class="h2 section-header">
                <i class="fas fa-building"></i> {{ federation.name }}
                <small class="text-muted">- {% trans "Tableau de bord Fédération" %}</small>
            </h1>
        </div>
    </div>

    <\!-- Statistiques -->
    <div class="row mb-4">
        <div class="col-md-3 mb-3">
            <div class="card dashboard-card text-center">
                <div class="card-body">
                    <i class="fas fa-users fa-3x text-primary mb-3"></i>
                    <h5 class="card-title">{% trans "Clubs" %}</h5>
                    <p class="stat-number">{{ clubs_count|default:"0" }}</p>
                </div>
            </div>
        </div>
        <div class="col-md-3 mb-3">
            <div class="card dashboard-card text-center">
                <div class="card-body">
                    <i class="fas fa-trophy fa-3x text-success mb-3"></i>
                    <h5 class="card-title">{% trans "Compétitions" %}</h5>
                    <p class="stat-number">{{ competitions_count|default:"0" }}</p>
                </div>
            </div>
        </div>
        <div class="col-md-3 mb-3">
            <div class="card dashboard-card text-center">
                <div class="card-body">
                    <i class="fas fa-user-friends fa-3x text-info mb-3"></i>
                    <h5 class="card-title">{% trans "Pratiquants" %}</h5>
                    <p class="stat-number">{{ practitioners_count|default:"0" }}</p>
                </div>
            </div>
        </div>
        <div class="col-md-3 mb-3">
            <div class="card dashboard-card text-center">
                <div class="card-body">
                    <i class="fas fa-gavel fa-3x text-warning mb-3"></i>
                    <h5 class="card-title">{% trans "Juges" %}</h5>
                    <p class="stat-number">{{ judges_count|default:"0" }}</p>
                </div>
            </div>
        </div>
    </div>

    <\!-- Actions rapides -->
    <div class="row mb-4">
        <div class="col-12">
            <h2 class="h4 section-header">{% trans "Actions rapides" %}</h2>
        </div>
    </div>
    
    <div class="row mb-4">
        <div class="col-md-4 mb-3">
            <div class="card dashboard-card">
                <div class="card-body">
                    <h5 class="card-title">
                        <i class="fas fa-plus-circle"></i> {% trans "Gérer les clubs" %}
                    </h5>
                    <p class="card-text">{% trans "Ajouter, modifier ou supprimer des clubs de votre fédération." %}</p>
                    <a href="{% url 'competitions:dashboard:federation_manage_clubs' federation.id %}" class="btn btn-primary">
                        {% trans "Gérer" %}
                    </a>
                </div>
            </div>
        </div>
        <div class="col-md-4 mb-3">
            <div class="card dashboard-card">
                <div class="card-body">
                    <h5 class="card-title">
                        <i class="fas fa-calendar-plus"></i> {% trans "Gérer les compétitions" %}
                    </h5>
                    <p class="card-text">{% trans "Organiser et gérer les compétitions de votre fédération." %}</p>
                    <a href="{% url 'competitions:dashboard:federation_manage_competitions' federation.id %}" class="btn btn-primary">
                        {% trans "Gérer" %}
                    </a>
                </div>
            </div>
        </div>
        <div class="col-md-4 mb-3">
            <div class="card dashboard-card">
                <div class="card-body">
                    <h5 class="card-title">
                        <i class="fas fa-certificate"></i> {% trans "Gérer les certifications" %}
                    </h5>
                    <p class="card-text">{% trans "Gérer les grades et certifications des pratiquants." %}</p>
                    <a href="{% url 'competitions:dashboard:federation_manage_certifications' federation.id %}" class="btn btn-primary">
                        {% trans "Gérer" %}
                    </a>
                </div>
            </div>
        </div>
    </div>

    <\!-- Informations de la fédération -->
    <div class="row">
        <div class="col-12">
            <h2 class="h4 section-header">{% trans "Informations" %}</h2>
        </div>
    </div>
    
    <div class="row">
        <div class="col-md-6">
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">{% trans "Détails de la fédération" %}</h5>
                    <dl class="row">
                        <dt class="col-sm-4">{% trans "Nom" %}:</dt>
                        <dd class="col-sm-8">{{ federation.name }}</dd>
                        
                        {% if federation.description %}
                        <dt class="col-sm-4">{% trans "Description" %}:</dt>
                        <dd class="col-sm-8">{{ federation.description|truncatewords:20 }}</dd>
                        {% endif %}
                        
                        {% if federation.contact_email %}
                        <dt class="col-sm-4">{% trans "Email" %}:</dt>
                        <dd class="col-sm-8">{{ federation.contact_email }}</dd>
                        {% endif %}
                        
                        {% if federation.country %}
                        <dt class="col-sm-4">{% trans "Pays" %}:</dt>
                        <dd class="col-sm-8">{{ federation.get_country_display|default:federation.country }}</dd>
                        {% endif %}
                    </dl>
                </div>
            </div>
        </div>
        
        <div class="col-md-6">
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">{% trans "Actions supplémentaires" %}</h5>
                    <div class="list-group">
                        <a href="{% url 'competitions:dashboard:federation_manage_judges' federation.id %}" class="list-group-item list-group-item-action">
                            <i class="fas fa-gavel"></i> {% trans "Gérer les juges" %}
                        </a>
                        <a href="{% url 'competitions:dashboard:federation_manage_settings' federation.id %}" class="list-group-item list-group-item-action">
                            <i class="fas fa-cog"></i> {% trans "Paramètres de la fédération" %}
                        </a>
                        <a href="{% url 'competitions:dashboard:federations' %}" class="list-group-item list-group-item-action">
                            <i class="fas fa-arrow-left"></i> {% trans "Retour aux fédérations" %}
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Animation des nombres
    const numbers = document.querySelectorAll('.stat-number');
    numbers.forEach(num => {
        const value = parseInt(num.textContent) || 0;
        let current = 0;
        const increment = value / 20;
        const timer = setInterval(() => {
            current += increment;
            if (current >= value) {
                current = value;
                clearInterval(timer);
            }
            num.textContent = Math.floor(current);
        }, 50);
    });
});
</script>
{% endblock %}
TEMPLATE_EOF

echo "✅ Template simple amélioré créé"

echo ""
echo "4️⃣ Redémarrage du service..."
echo "============================"
sudo systemctl restart martialcomp
sleep 2

echo ""
echo "5️⃣ Test final..."
echo "==============="
curl -s -o /dev/null -w "Status: %{http_code}\n" https://martialcomp.com/fr/competitions/dashboard/federation/41/

REMOTE_COMMANDS

echo ""
echo "================================================"
echo "✅ TEMPLATE SIMPLE AMÉLIORÉ ACTIVÉ"
echo "================================================"
echo ""
echo "Le dashboard fédération utilise maintenant un"
echo "template simple mais fonctionnel avec:"
echo "- Statistiques animées"
echo "- Actions rapides"
echo "- Informations de la fédération"
echo "- Design responsive"

