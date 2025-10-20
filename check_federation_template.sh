#!/bin/bash
# Vérifier pourquoi le template federation ne fonctionne pas

echo "================================================"
echo "🔍 DIAGNOSTIC DU TEMPLATE FEDERATION"
echo "================================================"
echo ""

ssh martialcomp-production << 'REMOTE_COMMANDS'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1️⃣ Vérification de la structure du template..."
echo "============================================="
echo "Taille du fichier:"
ls -lh apps/competitions/templates/competitions/dashboard/federation.html

echo ""
echo "Premières lignes du template:"
head -20 apps/competitions/templates/competitions/dashboard/federation.html

echo ""
echo "2️⃣ Recherche d'erreurs potentielles..."
echo "====================================="
echo "URLs problématiques dans le template:"
grep -n "{% url" apps/competitions/templates/competitions/dashboard/federation.html | grep -v "competitions:dashboard:" | head -5

echo ""
echo "3️⃣ Vérification des imports dans la vue..."
echo "========================================"
head -30 apps/competitions/views/dashboard/federations.py | grep -E "(from|import)"

echo ""
echo "4️⃣ Test d'une version simplifiée..."
echo "==================================="
# Créer une copie de sauvegarde
cp apps/competitions/templates/competitions/dashboard/federation.html \
   apps/competitions/templates/competitions/dashboard/federation_backup_$(date +%Y%m%d_%H%M%S).html

# Créer un template minimal qui fonctionne à coup sûr
cat > apps/competitions/templates/competitions/dashboard/federation_minimal.html << 'EOF'
{% extends "base.html" %}
{% load i18n static %}

{% block title %}{% trans "Tableau de bord Fédération" %} - {{ federation.name }}{% endblock %}

{% block content %}
<div class="container-fluid mt-4">
    <div class="row">
        <div class="col-12">
            <h1>{{ federation.name }}</h1>
            <p>{% trans "Tableau de bord Fédération" %}</p>
            
            <div class="row mt-4">
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body text-center">
                            <h3>{{ clubs_count|default:"0" }}</h3>
                            <p>{% trans "Clubs" %}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body text-center">
                            <h3>{{ competitions_count|default:"0" }}</h3>
                            <p>{% trans "Compétitions" %}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body text-center">
                            <h3>{{ practitioners_count|default:"0" }}</h3>
                            <p>{% trans "Pratiquants" %}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body text-center">
                            <h3>{{ judges_count|default:"0" }}</h3>
                            <p>{% trans "Juges" %}</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="mt-4">
                <h2>{% trans "Actions" %}</h2>
                <div class="list-group">
                    <a href="{% url 'competitions:dashboard:federation_manage_clubs' federation.id %}" class="list-group-item list-group-item-action">
                        {% trans "Gérer les clubs" %}
                    </a>
                    <a href="{% url 'competitions:dashboard:federation_manage_competitions' federation.id %}" class="list-group-item list-group-item-action">
                        {% trans "Gérer les compétitions" %}
                    </a>
                    <a href="{% url 'competitions:dashboard:federation_manage_judges' federation.id %}" class="list-group-item list-group-item-action">
                        {% trans "Gérer les juges" %}
                    </a>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
EOF

echo "✅ Template minimal créé"

# Modifier temporairement la vue pour utiliser le template minimal
sed -i "s/'competitions\/dashboard\/federation\.html'/'competitions\/dashboard\/federation_minimal.html'/g" \
    apps/competitions/views/dashboard/federations.py

echo ""
echo "5️⃣ Redémarrage du service..."
echo "==========================="
sudo systemctl restart martialcomp
sleep 3

echo ""
echo "6️⃣ Test final..."
echo "==============="
curl -s -o /dev/null -w "Status HTTP: %{http_code}\n" https://martialcomp.com/fr/competitions/dashboard/federation/41/

REMOTE_COMMANDS

echo ""
echo "================================================"
echo "✅ DIAGNOSTIC TERMINÉ"
echo "================================================"