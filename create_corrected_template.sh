#\!/bin/bash
# Créer un template corrigé avec les bonnes URLs

echo "================================================"
echo "🔧 CRÉATION TEMPLATE CORRIGÉ"
echo "================================================"
echo ""

# Créer localement une version corrigée
cat > federation_corrected.html << 'TEMPLATE_HEAD'
{% extends "base.html" %}
{% load i18n static %}
{% load custom_filters %}

{% block title %}{% trans "Tableau de bord Fédération" %}  < /dev/null |  {{ federation.name }}{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="{% static 'css/dashboard.css' %}">
<style>
    .dashboard-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem 0;
        margin-bottom: 2rem;
        border-radius: 0 0 1rem 1rem;
    }
    
    .stat-card {
        border: none;
        border-radius: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
        height: 100%;
    }
    
    .stat-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0;
    }
    
    .action-card {
        border: none;
        border-radius: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
        height: 100%;
    }
    
    .action-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    }
    
    .section-title {
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #667eea;
    }
    
    .quick-action-btn {
        border-radius: 0.5rem;
        padding: 1rem;
        transition: all 0.3s ease;
    }
    
    .recent-item {
        padding: 1rem;
        border-left: 4px solid #667eea;
        margin-bottom: 1rem;
        background: #f8f9fa;
        border-radius: 0.5rem;
    }
</style>
{% endblock %}

{% block content %}
<div class="dashboard-header">
    <div class="container-fluid">
        <div class="row align-items-center">
            <div class="col-md-8">
                <h1 class="h2 mb-0">
                    <i class="fas fa-building mr-2"></i>{{ federation.name }}
                </h1>
                <p class="mb-0 mt-2">{% trans "Tableau de bord de gestion de votre fédération" %}</p>
            </div>
            <div class="col-md-4 text-md-right">
                <a href="{% url 'competitions:dashboard:federation_manage_settings' federation.id %}" class="btn btn-light btn-sm">
                    <i class="fas fa-cog"></i> {% trans "Paramètres" %}
                </a>
            </div>
        </div>
    </div>
</div>

<div class="container-fluid">
    <\!-- Statistiques -->
    <div class="row mb-4">
        <div class="col-md-3 col-sm-6 mb-3">
            <div class="card stat-card text-center">
                <div class="card-body">
                    <i class="fas fa-users fa-3x text-primary mb-3"></i>
                    <h5 class="card-title">{% trans "Clubs" %}</h5>
                    <p class="stat-number text-primary">{{ clubs_count|default:"0" }}</p>
                </div>
            </div>
        </div>
        <div class="col-md-3 col-sm-6 mb-3">
            <div class="card stat-card text-center">
                <div class="card-body">
                    <i class="fas fa-trophy fa-3x text-success mb-3"></i>
                    <h5 class="card-title">{% trans "Compétitions" %}</h5>
                    <p class="stat-number text-success">{{ competitions_count|default:"0" }}</p>
                </div>
            </div>
        </div>
        <div class="col-md-3 col-sm-6 mb-3">
            <div class="card stat-card text-center">
                <div class="card-body">
                    <i class="fas fa-user-friends fa-3x text-info mb-3"></i>
                    <h5 class="card-title">{% trans "Pratiquants" %}</h5>
                    <p class="stat-number text-info">{{ practitioners_count|default:"0" }}</p>
                </div>
            </div>
        </div>
        <div class="col-md-3 col-sm-6 mb-3">
            <div class="card stat-card text-center">
                <div class="card-body">
                    <i class="fas fa-gavel fa-3x text-warning mb-3"></i>
                    <h5 class="card-title">{% trans "Juges" %}</h5>
                    <p class="stat-number text-warning">{{ judges_count|default:"0" }}</p>
                </div>
            </div>
        </div>
    </div>

    <\!-- Actions principales -->
    <div class="row mb-4">
        <div class="col-12">
            <h2 class="section-title">{% trans "Gestion de la fédération" %}</h2>
        </div>
    </div>
    
    <div class="row mb-5">
        <div class="col-lg-4 col-md-6 mb-3">
            <div class="card action-card h-100">
                <div class="card-body">
                    <div class="d-flex align-items-center mb-3">
                        <i class="fas fa-users fa-2x text-primary mr-3"></i>
                        <h5 class="card-title mb-0">{% trans "Gestion des clubs" %}</h5>
                    </div>
                    <p class="card-text">{% trans "Gérez les clubs affiliés à votre fédération, leurs informations et leurs membres." %}</p>
                    <a href="{% url 'competitions:dashboard:federation_manage_clubs' federation.id %}" class="btn btn-primary btn-block quick-action-btn">
                        <i class="fas fa-arrow-right mr-2"></i>{% trans "Gérer les clubs" %}
                    </a>
                </div>
            </div>
        </div>
        
        <div class="col-lg-4 col-md-6 mb-3">
            <div class="card action-card h-100">
                <div class="card-body">
                    <div class="d-flex align-items-center mb-3">
                        <i class="fas fa-calendar-alt fa-2x text-success mr-3"></i>
                        <h5 class="card-title mb-0">{% trans "Gestion des compétitions" %}</h5>
                    </div>
                    <p class="card-text">{% trans "Créez et gérez les compétitions organisées sous l'égide de votre fédération." %}</p>
                    <a href="{% url 'competitions:dashboard:federation_manage_competitions' federation.id %}" class="btn btn-success btn-block quick-action-btn">
                        <i class="fas fa-arrow-right mr-2"></i>{% trans "Gérer les compétitions" %}
                    </a>
                </div>
            </div>
        </div>
        
        <div class="col-lg-4 col-md-6 mb-3">
            <div class="card action-card h-100">
                <div class="card-body">
                    <div class="d-flex align-items-center mb-3">
                        <i class="fas fa-id-card fa-2x text-info mr-3"></i>
                        <h5 class="card-title mb-0">{% trans "Gestion des licences" %}</h5>
                    </div>
                    <p class="card-text">{% trans "Gérez les licences des pratiquants et leur validation annuelle." %}</p>
                    <a href="{% url 'competitions:dashboard:federation_manage_licenses' federation.id %}" class="btn btn-info btn-block quick-action-btn">
                        <i class="fas fa-arrow-right mr-2"></i>{% trans "Gérer les licences" %}
                    </a>
                </div>
            </div>
        </div>
        
        <div class="col-lg-4 col-md-6 mb-3">
            <div class="card action-card h-100">
                <div class="card-body">
                    <div class="d-flex align-items-center mb-3">
                        <i class="fas fa-gavel fa-2x text-warning mr-3"></i>
                        <h5 class="card-title mb-0">{% trans "Gestion des juges" %}</h5>
                    </div>
                    <p class="card-text">{% trans "Gérez la liste des juges accrédités et leurs qualifications." %}</p>
                    <a href="{% url 'competitions:dashboard:federation_manage_judges' federation.id %}" class="btn btn-warning btn-block quick-action-btn">
                        <i class="fas fa-arrow-right mr-2"></i>{% trans "Gérer les juges" %}
                    </a>
                </div>
            </div>
        </div>
        
        <div class="col-lg-4 col-md-6 mb-3">
            <div class="card action-card h-100">
                <div class="card-body">
                    <div class="d-flex align-items-center mb-3">
                        <i class="fas fa-certificate fa-2x text-danger mr-3"></i>
                        <h5 class="card-title mb-0">{% trans "Gestion des grades" %}</h5>
                    </div>
                    <p class="card-text">{% trans "Gérez les grades et certifications délivrés par votre fédération." %}</p>
                    <a href="{% url 'competitions:dashboard:federation_manage_certifications' federation.id %}" class="btn btn-danger btn-block quick-action-btn">
                        <i class="fas fa-arrow-right mr-2"></i>{% trans "Gérer les grades" %}
                    </a>
                </div>
            </div>
        </div>
        
        <div class="col-lg-4 col-md-6 mb-3">
            <div class="card action-card h-100">
                <div class="card-body">
                    <div class="d-flex align-items-center mb-3">
                        <i class="fas fa-chart-bar fa-2x text-secondary mr-3"></i>
                        <h5 class="card-title mb-0">{% trans "Rapports et statistiques" %}</h5>
                    </div>
                    <p class="card-text">{% trans "Consultez les rapports détaillés et statistiques de votre fédération." %}</p>
                    <a href="{% url 'competitions:dashboard:federation_manage_reports' federation.id %}" class="btn btn-secondary btn-block quick-action-btn">
                        <i class="fas fa-arrow-right mr-2"></i>{% trans "Voir les rapports" %}
                    </a>
                </div>
            </div>
        </div>
    </div>

    <\!-- Activité récente -->
    <div class="row">
        <div class="col-lg-6 mb-4">
            <h3 class="section-title">{% trans "Compétitions récentes" %}</h3>
            <div class="card">
                <div class="card-body">
                    {% if recent_competitions %}
                        {% for competition in recent_competitions %}
                        <div class="recent-item">
                            <h6 class="mb-1">{{ competition.title }}</h6>
                            <p class="mb-0 text-muted">
                                <i class="fas fa-calendar mr-1"></i>{{ competition.start_date|date:"d/m/Y" }}
                                <span class="ml-3"><i class="fas fa-map-marker-alt mr-1"></i>{{ competition.venue_name|default:"-" }}</span>
                            </p>
                        </div>
                        {% endfor %}
                    {% else %}
                        <p class="text-center text-muted">{% trans "Aucune compétition récente" %}</p>
                    {% endif %}
                </div>
            </div>
        </div>
        
        <div class="col-lg-6 mb-4">
            <h3 class="section-title">{% trans "Clubs récents" %}</h3>
            <div class="card">
                <div class="card-body">
                    {% if recent_clubs %}
                        {% for club in recent_clubs %}
                        <div class="recent-item">
                            <h6 class="mb-1">{{ club.name }}</h6>
                            <p class="mb-0 text-muted">
                                <i class="fas fa-map-marker-alt mr-1"></i>{{ club.city|default:"-" }}
                                <span class="ml-3"><i class="fas fa-users mr-1"></i>{{ club.members.count }} {% trans "membres" %}</span>
                            </p>
                        </div>
                        {% endfor %}
                    {% else %}
                        <p class="text-center text-muted">{% trans "Aucun club récent" %}</p>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
$(document).ready(function() {
    // Animation des nombres
    $('.stat-number').each(function() {
        var $this = $(this);
        var countTo = parseInt($this.text());
        
        $({countNum: 0}).animate({
            countNum: countTo
        },
        {
            duration: 2000,
            easing: 'swing',
            step: function() {
                $this.text(Math.floor(this.countNum));
            },
            complete: function() {
                $this.text(this.countNum);
            }
        });
    });
});
</script>
{% endblock %}
TEMPLATE_HEAD

echo "✅ Template corrigé créé localement"

# Transférer vers la production
echo ""
echo "Transfert vers la production..."
scp federation_corrected.html martialcomp-production:/tmp/

ssh martialcomp-production << 'REMOTE_COMMANDS'
cd /var/www/vhosts/martialcomp.com/httpdocs

# Sauvegarder l'ancien
mv apps/competitions/templates/competitions/dashboard/federation.html \
   apps/competitions/templates/competitions/dashboard/federation.html.old_$(date +%Y%m%d_%H%M%S)

# Installer le nouveau
cp /tmp/federation_corrected.html apps/competitions/templates/competitions/dashboard/federation.html

echo "✅ Template corrigé installé"

# Nettoyer
rm -f /tmp/federation_corrected.html

# Redémarrer
sudo systemctl restart martialcomp

echo ""
echo "Test du nouveau template..."
curl -s -o /dev/null -w "Status: %{http_code}\n" https://martialcomp.com/fr/competitions/dashboard/federation/41/

REMOTE_COMMANDS

# Nettoyer localement
rm -f federation_corrected.html

echo ""
echo "================================================"
echo "✅ TEMPLATE COMPLET CORRIGÉ INSTALLÉ"
echo "================================================"
echo ""
echo "Le template complet est maintenant actif avec:"
echo "- Toutes les fonctionnalités"
echo "- Les bonnes URLs (competitions:dashboard:*)"
echo "- Un design moderne et professionnel"
echo "- Des animations et effets visuels"

