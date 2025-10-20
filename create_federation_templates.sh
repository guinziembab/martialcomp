#!/bin/bash
# Créer tous les templates pour les fonctionnalités du dashboard federation

echo "================================================"
echo "📄 CRÉATION DES TEMPLATES FEDERATION"
echo "================================================"
echo ""

ssh martialcomp-production 'cd /var/www/vhosts/martialcomp.com/httpdocs && bash' << 'EOF'

echo "1️⃣ Template pour la gestion des compétitions..."
echo "=============================================="

cat > apps/competitions/templates/competitions/dashboard/federation_competitions.html << 'TEMPLATE_EOF'
{% extends "base.html" %}
{% load i18n static %}

{% block title %}{{ title }} - {{ federation.name }}{% endblock %}

{% block extra_css %}
<style>
    .competition-status {
        font-weight: bold;
    }
    .status-upcoming { color: #17a2b8; }
    .status-ongoing { color: #28a745; }
    .status-past { color: #6c757d; }
</style>
{% endblock %}

{% block content %}
<div class="container-fluid mt-4">
    <div class="row mb-4">
        <div class="col-md-8">
            <h1 class="h2">
                <i class="fas fa-trophy"></i> {{ title }}
                <small class="text-muted">{{ federation.name }}</small>
            </h1>
        </div>
        <div class="col-md-4 text-right">
            <a href="#" class="btn btn-success">
                <i class="fas fa-plus"></i> {% trans "Nouvelle compétition" %}
            </a>
            <a href="{% url 'competitions:dashboard:federation_detail' federation.id %}" class="btn btn-secondary">
                <i class="fas fa-arrow-left"></i> {% trans "Retour" %}
            </a>
        </div>
    </div>

    <!-- Statistiques -->
    <div class="row mb-4">
        <div class="col-md-4">
            <div class="card text-center">
                <div class="card-body">
                    <h3 class="text-primary">{{ total_competitions }}</h3>
                    <p>{% trans "Total compétitions" %}</p>
                </div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card text-center">
                <div class="card-body">
                    <h3 class="text-success">{{ ongoing_competitions.count }}</h3>
                    <p>{% trans "En cours" %}</p>
                </div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card text-center">
                <div class="card-body">
                    <h3 class="text-info">{{ upcoming_competitions.count }}</h3>
                    <p>{% trans "À venir" %}</p>
                </div>
            </div>
        </div>
    </div>

    <!-- Compétitions en cours -->
    {% if ongoing_competitions %}
    <div class="card mb-4">
        <div class="card-header bg-success text-white">
            <h3 class="card-title mb-0">{% trans "Compétitions en cours" %}</h3>
        </div>
        <div class="card-body">
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
                            <td>{{ comp.start_date|date:"d/m/Y" }} - {{ comp.end_date|date:"d/m/Y" }}</td>
                            <td>{{ comp.location|default:"-" }}</td>
                            <td>
                                <a href="#" class="btn btn-sm btn-info">
                                    <i class="fas fa-eye"></i> {% trans "Voir" %}
                                </a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    {% endif %}

    <!-- Compétitions à venir -->
    <div class="card mb-4">
        <div class="card-header">
            <h3 class="card-title mb-0">{% trans "Prochaines compétitions" %}</h3>
        </div>
        <div class="card-body">
            {% if upcoming_competitions %}
            <div class="table-responsive">
                <table class="table">
                    <thead>
                        <tr>
                            <th>{% trans "Nom" %}</th>
                            <th>{% trans "Date début" %}</th>
                            <th>{% trans "Lieu" %}</th>
                            <th>{% trans "Inscriptions" %}</th>
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
                                <span class="badge badge-info">0</span>
                            </td>
                            <td>
                                <div class="btn-group btn-group-sm">
                                    <a href="#" class="btn btn-info" title="{% trans 'Voir' %}">
                                        <i class="fas fa-eye"></i>
                                    </a>
                                    <a href="#" class="btn btn-primary" title="{% trans 'Modifier' %}">
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
            <p class="text-center text-muted py-4">
                {% trans "Aucune compétition à venir." %}
            </p>
            {% endif %}
        </div>
    </div>
</div>
{% endblock %}
TEMPLATE_EOF

echo "✅ Template federation_competitions.html créé"

echo ""
echo "2️⃣ Template pour la gestion des pratiquants..."
echo "============================================"

cat > apps/competitions/templates/competitions/dashboard/federation_practitioners.html << 'TEMPLATE_EOF'
{% extends "base.html" %}
{% load i18n static %}

{% block title %}{{ title }} - {{ federation.name }}{% endblock %}

{% block content %}
<div class="container-fluid mt-4">
    <div class="row mb-4">
        <div class="col-md-8">
            <h1 class="h2">
                <i class="fas fa-user-friends"></i> {{ title }}
                <small class="text-muted">{{ federation.name }}</small>
            </h1>
        </div>
        <div class="col-md-4 text-right">
            <a href="{% url 'competitions:dashboard:federation_detail' federation.id %}" class="btn btn-secondary">
                <i class="fas fa-arrow-left"></i> {% trans "Retour" %}
            </a>
        </div>
    </div>

    <!-- Statistiques -->
    <div class="row mb-4">
        <div class="col-md-6">
            <div class="card">
                <div class="card-body text-center">
                    <h3 class="text-primary">{{ total_practitioners }}</h3>
                    <p>{% trans "Total pratiquants" %}</p>
                </div>
            </div>
        </div>
        <div class="col-md-6">
            <div class="card">
                <div class="card-body">
                    <h5>{% trans "Répartition par grade" %}</h5>
                    {% for grade, count in grade_stats.items %}
                    <div class="mb-2">
                        <span class="badge badge-secondary">{{ grade }}</span>
                        <span class="float-right">{{ count }}</span>
                    </div>
                    {% empty %}
                    <p class="text-muted">{% trans "Pas de données" %}</p>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>

    <!-- Liste des pratiquants -->
    <div class="card">
        <div class="card-header">
            <h3 class="card-title">{% trans "Liste des pratiquants" %} (100 premiers)</h3>
        </div>
        <div class="card-body">
            {% if practitioners %}
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>{% trans "Nom" %}</th>
                            <th>{% trans "Prénom" %}</th>
                            <th>{% trans "Licence" %}</th>
                            <th>{% trans "Grade" %}</th>
                            <th>{% trans "Club" %}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for practitioner in practitioners %}
                        <tr>
                            <td>{{ practitioner.last_name|upper }}</td>
                            <td>{{ practitioner.first_name }}</td>
                            <td>{{ practitioner.license_number|default:"-" }}</td>
                            <td>{{ practitioner.grade|default:"-" }}</td>
                            <td>{{ practitioner.organization.name|default:"-" }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% else %}
            <p class="text-center text-muted py-4">
                {% trans "Aucun pratiquant trouvé." %}
            </p>
            {% endif %}
        </div>
    </div>
</div>
{% endblock %}
TEMPLATE_EOF

echo "✅ Template federation_practitioners.html créé"

echo ""
echo "3️⃣ Template pour la gestion des juges..."
echo "======================================="

cat > apps/competitions/templates/competitions/dashboard/federation_judges.html << 'TEMPLATE_EOF'
{% extends "base.html" %}
{% load i18n static %}

{% block title %}{{ title }} - {{ federation.name }}{% endblock %}

{% block content %}
<div class="container-fluid mt-4">
    <div class="row mb-4">
        <div class="col-md-8">
            <h1 class="h2">
                <i class="fas fa-gavel"></i> {{ title }}
                <small class="text-muted">{{ federation.name }}</small>
            </h1>
        </div>
        <div class="col-md-4 text-right">
            <a href="#" class="btn btn-success">
                <i class="fas fa-plus"></i> {% trans "Ajouter un juge" %}
            </a>
            <a href="{% url 'competitions:dashboard:federation_detail' federation.id %}" class="btn btn-secondary">
                <i class="fas fa-arrow-left"></i> {% trans "Retour" %}
            </a>
        </div>
    </div>

    <!-- Statistiques -->
    <div class="row mb-4">
        <div class="col-md-6">
            <div class="card">
                <div class="card-body text-center">
                    <h3 class="text-warning">{{ total_judges }}</h3>
                    <p>{% trans "Total juges" %}</p>
                </div>
            </div>
        </div>
        <div class="col-md-6">
            <div class="card">
                <div class="card-body">
                    <h5>{% trans "Par niveau" %}</h5>
                    {% for level, count in level_stats.items %}
                    <div class="mb-2">
                        <span class="badge badge-info">{{ level }}</span>
                        <span class="float-right">{{ count }}</span>
                    </div>
                    {% empty %}
                    <p class="text-muted">{% trans "Pas de données" %}</p>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>

    <!-- Liste des juges -->
    <div class="card">
        <div class="card-header">
            <h3 class="card-title">{% trans "Liste des juges" %}</h3>
        </div>
        <div class="card-body">
            {% if judges %}
            <div class="table-responsive">
                <table class="table table-hover">
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
                            <td>
                                {{ judge.user.last_name|upper }} {{ judge.user.first_name }}
                            </td>
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
                                    <a href="#" class="btn btn-info">
                                        <i class="fas fa-eye"></i>
                                    </a>
                                    <a href="#" class="btn btn-primary">
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
            <p class="text-center text-muted py-4">
                {% trans "Aucun juge enregistré." %}
            </p>
            {% endif %}
        </div>
    </div>
</div>
{% endblock %}
TEMPLATE_EOF

echo "✅ Template federation_judges.html créé"

echo ""
echo "4️⃣ Template pour les paramètres..."
echo "================================="

cat > apps/competitions/templates/competitions/dashboard/federation_settings.html << 'TEMPLATE_EOF'
{% extends "base.html" %}
{% load i18n static %}

{% block title %}{{ title }} - {{ federation.name }}{% endblock %}

{% block content %}
<div class="container-fluid mt-4">
    <div class="row mb-4">
        <div class="col-md-8">
            <h1 class="h2">
                <i class="fas fa-cog"></i> {{ title }}
                <small class="text-muted">{{ federation.name }}</small>
            </h1>
        </div>
        <div class="col-md-4 text-right">
            <a href="{% url 'competitions:dashboard:federation_detail' federation.id %}" class="btn btn-secondary">
                <i class="fas fa-arrow-left"></i> {% trans "Retour" %}
            </a>
        </div>
    </div>

    <div class="card">
        <div class="card-body">
            <form method="post" enctype="multipart/form-data">
                {% csrf_token %}
                
                <div class="row">
                    <div class="col-md-6">
                        <div class="form-group">
                            <label>{% trans "Nom de la fédération" %}</label>
                            {{ form.name }}
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="form-group">
                            <label>{% trans "Email de contact" %}</label>
                            {{ form.contact_email }}
                        </div>
                    </div>
                </div>

                <div class="row">
                    <div class="col-md-12">
                        <div class="form-group">
                            <label>{% trans "Description" %}</label>
                            {{ form.description }}
                        </div>
                    </div>
                </div>

                {% for field in form %}
                    {% if field.name not in 'name,contact_email,description' %}
                    <div class="form-group">
                        {{ field.label_tag }}
                        {{ field }}
                        {% if field.help_text %}
                        <small class="form-text text-muted">{{ field.help_text }}</small>
                        {% endif %}
                        {% if field.errors %}
                        <div class="text-danger">
                            {{ field.errors }}
                        </div>
                        {% endif %}
                    </div>
                    {% endif %}
                {% endfor %}

                <div class="form-group">
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-save"></i> {% trans "Enregistrer" %}
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}
TEMPLATE_EOF

echo "✅ Template federation_settings.html créé"

echo ""
echo "5️⃣ Template pour les rapports..."
echo "=============================="

cat > apps/competitions/templates/competitions/dashboard/federation_reports.html << 'TEMPLATE_EOF'
{% extends "base.html" %}
{% load i18n static %}

{% block title %}{{ title }} - {{ federation.name }}{% endblock %}

{% block content %}
<div class="container-fluid mt-4">
    <div class="row mb-4">
        <div class="col-12">
            <h1 class="h2">
                <i class="fas fa-chart-bar"></i> {{ title }}
                <small class="text-muted">{{ federation.name }}</small>
            </h1>
        </div>
    </div>

    <!-- Statistiques générales -->
    <div class="row mb-4">
        <div class="col-md-3">
            <div class="card text-center">
                <div class="card-body">
                    <i class="fas fa-users fa-2x text-primary mb-2"></i>
                    <h3>{{ stats.clubs_count }}</h3>
                    <p>{% trans "Clubs" %}</p>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card text-center">
                <div class="card-body">
                    <i class="fas fa-user-friends fa-2x text-success mb-2"></i>
                    <h3>{{ stats.practitioners_count }}</h3>
                    <p>{% trans "Pratiquants" %}</p>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card text-center">
                <div class="card-body">
                    <i class="fas fa-trophy fa-2x text-warning mb-2"></i>
                    <h3>{{ stats.competitions_count }}</h3>
                    <p>{% trans "Compétitions" %}</p>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card text-center">
                <div class="card-body">
                    <i class="fas fa-gavel fa-2x text-info mb-2"></i>
                    <h3>{{ stats.judges_count }}</h3>
                    <p>{% trans "Juges" %}</p>
                </div>
            </div>
        </div>
    </div>

    <!-- Actions d'export -->
    <div class="card">
        <div class="card-header">
            <h3 class="card-title">{% trans "Export des données" %}</h3>
        </div>
        <div class="card-body">
            <div class="row">
                <div class="col-md-4">
                    <a href="#" class="btn btn-block btn-outline-primary mb-2">
                        <i class="fas fa-download"></i> {% trans "Export clubs (CSV)" %}
                    </a>
                </div>
                <div class="col-md-4">
                    <a href="#" class="btn btn-block btn-outline-success mb-2">
                        <i class="fas fa-download"></i> {% trans "Export pratiquants (Excel)" %}
                    </a>
                </div>
                <div class="col-md-4">
                    <a href="#" class="btn btn-block btn-outline-info mb-2">
                        <i class="fas fa-download"></i> {% trans "Rapport complet (PDF)" %}
                    </a>
                </div>
            </div>
        </div>
    </div>

    <div class="mt-4 text-center">
        <a href="{% url 'competitions:dashboard:federation_detail' federation.id %}" class="btn btn-secondary">
            <i class="fas fa-arrow-left"></i> {% trans "Retour au dashboard" %}
        </a>
    </div>
</div>
{% endblock %}
TEMPLATE_EOF

echo "✅ Template federation_reports.html créé"

echo ""
echo "6️⃣ Template pour les licences..."
echo "==============================="

cat > apps/competitions/templates/competitions/dashboard/federation_licenses.html << 'TEMPLATE_EOF'
{% extends "base.html" %}
{% load i18n static %}

{% block title %}{{ title }} - {{ federation.name }}{% endblock %}

{% block content %}
<div class="container-fluid mt-4">
    <div class="row mb-4">
        <div class="col-md-8">
            <h1 class="h2">
                <i class="fas fa-id-card"></i> {{ title }}
                <small class="text-muted">{{ federation.name }}</small>
            </h1>
        </div>
        <div class="col-md-4 text-right">
            <a href="{% url 'competitions:dashboard:federation_detail' federation.id %}" class="btn btn-secondary">
                <i class="fas fa-arrow-left"></i> {% trans "Retour" %}
            </a>
        </div>
    </div>

    <!-- Statistiques -->
    <div class="row mb-4">
        <div class="col-md-6">
            <div class="card bg-success text-white text-center">
                <div class="card-body">
                    <h3>{{ total_with_license }}</h3>
                    <p>{% trans "Avec licence" %} {{ current_year }}</p>
                </div>
            </div>
        </div>
        <div class="col-md-6">
            <div class="card bg-warning text-white text-center">
                <div class="card-body">
                    <h3>{{ total_without_license }}</h3>
                    <p>{% trans "Sans licence" %}</p>
                </div>
            </div>
        </div>
    </div>

    <!-- Pratiquants avec licence -->
    <div class="card mb-4">
        <div class="card-header bg-success text-white">
            <h3 class="card-title mb-0">{% trans "Pratiquants avec licence" %}</h3>
        </div>
        <div class="card-body">
            {% if practitioners_with_license %}
            <div class="table-responsive">
                <table class="table">
                    <thead>
                        <tr>
                            <th>{% trans "Nom" %}</th>
                            <th>{% trans "Prénom" %}</th>
                            <th>{% trans "N° Licence" %}</th>
                            <th>{% trans "Club" %}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for p in practitioners_with_license %}
                        <tr>
                            <td>{{ p.last_name|upper }}</td>
                            <td>{{ p.first_name }}</td>
                            <td><strong>{{ p.license_number }}</strong></td>
                            <td>{{ p.organization.name|default:"-" }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% else %}
            <p class="text-center text-muted">{% trans "Aucun pratiquant avec licence." %}</p>
            {% endif %}
        </div>
    </div>
</div>
{% endblock %}
TEMPLATE_EOF

echo "✅ Tous les templates créés"

echo ""
echo "7️⃣ Redémarrage final..."
echo "======================"
sudo systemctl restart martialcomp
sleep 3

echo ""
echo "✅ TERMINÉ !"

EOF

echo ""
echo "================================================"
echo "✅ TEMPLATES CRÉÉS AVEC SUCCÈS"
echo "================================================"
echo ""
echo "Templates créés :"
echo "- federation_clubs.html"
echo "- federation_competitions.html" 
echo "- federation_practitioners.html"
echo "- federation_judges.html"
echo "- federation_settings.html"
echo "- federation_reports.html"
echo "- federation_licenses.html"