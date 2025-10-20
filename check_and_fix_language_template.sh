#!/bin/bash

# Script pour vérifier et corriger le template de changement de langue

echo "=== VÉRIFICATION ET CORRECTION DU TEMPLATE DE LANGUE ==="
echo ""

cd /var/www/vhosts/martialcomp.com/httpdocs

# 1. Trouver et examiner le template actuel
echo "1. RECHERCHE DU TEMPLATE DE SÉLECTION DE LANGUE"
echo "=============================================="

# Le script a trouvé ce fichier
TEMPLATE_FILE="./apps/competitions/templates/competitions/includes/language_selector.html"

if [ -f "$TEMPLATE_FILE" ]; then
    echo "Template trouvé: $TEMPLATE_FILE"
    echo ""
    echo "Contenu actuel:"
    echo "---------------"
    cat "$TEMPLATE_FILE"
    echo ""
    echo "---------------"
    
    # Vérifier si csrf_token est présent
    if grep -q "csrf_token" "$TEMPLATE_FILE"; then
        echo "✓ Le template contient déjà csrf_token"
    else
        echo "❌ PROBLÈME: csrf_token MANQUANT dans le template!"
        
        # Sauvegarder
        cp "$TEMPLATE_FILE" "${TEMPLATE_FILE}.bak.$(date +%Y%m%d_%H%M%S)"
        
        # Créer une version corrigée
        echo ""
        echo "2. CRÉATION D'UN TEMPLATE CORRIGÉ"
        echo "================================="
        
        cat > "$TEMPLATE_FILE" << 'TEMPLATE_EOF'
{% load i18n %}

<form action="{% url 'set_language' %}" method="post" class="language-selector-form">
    {% csrf_token %}
    <input name="next" type="hidden" value="{{ request.get_full_path }}">
    
    <select name="language" class="form-control" onchange="this.form.submit()">
        {% get_current_language as LANGUAGE_CODE %}
        {% get_available_languages as LANGUAGES %}
        {% get_language_info_list for LANGUAGES as languages %}
        
        {% for language in languages %}
            <option value="{{ language.code }}"{% if language.code == LANGUAGE_CODE %} selected{% endif %}>
                {% if language.code == 'fr' %}Français
                {% elif language.code == 'en' %}English
                {% elif language.code == 'es' %}Español
                {% elif language.code == 'it' %}Italiano
                {% elif language.code == 'de' %}Deutsch
                {% elif language.code == 'pt' %}Português
                {% elif language.code == 'ru' %}Русский
                {% elif language.code == 'ja' %}日本語
                {% elif language.code == 'zh-hans' %}中文
                {% elif language.code == 'ko' %}한국어
                {% elif language.code == 'ar' %}العربية
                {% elif language.code == 'hi' %}हिंदी
                {% else %}{{ language.name_local }}{% endif %}
            </option>
        {% endfor %}
    </select>
    
    <noscript>
        <button type="submit" class="btn btn-sm btn-primary">{% trans "Change" %}</button>
    </noscript>
</form>

<style>
.language-selector-form {
    display: inline-block;
}
.language-selector-form select {
    min-width: 120px;
}
</style>
TEMPLATE_EOF
        
        echo "✓ Template corrigé avec csrf_token"
    fi
else
    echo "❌ Template non trouvé à l'emplacement attendu"
    echo "Création d'un nouveau template..."
    
    # Créer le répertoire si nécessaire
    mkdir -p apps/competitions/templates/competitions/includes/
    
    # Créer le template
    cat > "$TEMPLATE_FILE" << 'TEMPLATE_EOF'
{% load i18n %}

<form action="{% url 'set_language' %}" method="post" class="language-selector-form">
    {% csrf_token %}
    <input name="next" type="hidden" value="{{ request.get_full_path }}">
    
    <select name="language" class="form-control" onchange="this.form.submit()">
        {% get_current_language as LANGUAGE_CODE %}
        {% get_available_languages as LANGUAGES %}
        {% get_language_info_list for LANGUAGES as languages %}
        
        {% for language in languages %}
            <option value="{{ language.code }}"{% if language.code == LANGUAGE_CODE %} selected{% endif %}>
                {% if language.code == 'fr' %}Français
                {% elif language.code == 'en' %}English
                {% elif language.code == 'es' %}Español
                {% elif language.code == 'it' %}Italiano
                {% elif language.code == 'de' %}Deutsch
                {% elif language.code == 'pt' %}Português
                {% elif language.code == 'ru' %}Русский
                {% elif language.code == 'ja' %}日本語
                {% elif language.code == 'zh-hans' %}中文
                {% elif language.code == 'ko' %}한국어
                {% elif language.code == 'ar' %}العربية
                {% elif language.code == 'hi' %}हिंदी
                {% else %}{{ language.name_local }}{% endif %}
            </option>
        {% endfor %}
    </select>
    
    <noscript>
        <button type="submit" class="btn btn-sm btn-primary">{% trans "Change" %}</button>
    </noscript>
</form>

<style>
.language-selector-form {
    display: inline-block;
}
.language-selector-form select {
    min-width: 120px;
}
</style>
TEMPLATE_EOF
    
    echo "✓ Nouveau template créé avec csrf_token"
fi

echo ""
echo "3. VÉRIFICATION DES AUTRES TEMPLATES"
echo "===================================="

# Chercher tous les fichiers qui utilisent set_language
echo "Recherche de tous les fichiers utilisant set_language..."
grep -r "set_language" templates/ apps/*/templates/ 2>/dev/null | grep -v ".bak" | while read -r line; do
    file=$(echo "$line" | cut -d: -f1)
    echo "Fichier: $file"
    
    if ! grep -q "csrf_token" "$file" 2>/dev/null; then
        echo "  ⚠️ csrf_token manquant - correction nécessaire"
    else
        echo "  ✓ csrf_token présent"
    fi
done

echo ""
echo "4. VÉRIFICATION DE LA BASE TEMPLATE"
echo "==================================="

# Vérifier si la base template inclut le language selector
base_templates=("templates/base.html" "apps/competitions/templates/base.html" "templates/competitions/base.html")

for template in "${base_templates[@]}"; do
    if [ -f "$template" ]; then
        echo "Vérification de $template..."
        
        if grep -q "language_selector.html" "$template"; then
            echo "✓ Include du language_selector trouvé"
        else
            echo "⚠️ Le template de base n'inclut peut-être pas le language_selector"
            echo "  Ajoutez dans votre template de base:"
            echo "  {% include 'competitions/includes/language_selector.html' %}"
        fi
        break
    fi
done

echo ""
echo "5. AJOUT DE CSRF_TRUSTED_ORIGINS"
echo "================================="

# Ajouter les origines de confiance pour CSRF
/var/www/vhosts/martialcomp.com/venv/bin/python << 'EOF'
import os
import re

settings_file = 'config/settings/production.py'

with open(settings_file, 'r') as f:
    content = f.read()

# Vérifier si CSRF_TRUSTED_ORIGINS existe et est correctement configuré
if 'CSRF_TRUSTED_ORIGINS' not in content:
    # Ajouter CSRF_TRUSTED_ORIGINS
    csrf_config = '''
# CSRF Trusted Origins pour Cloudflare et production
CSRF_TRUSTED_ORIGINS = [
    'https://martialcomp.com',
    'https://www.martialcomp.com',
    'https://*.martialcomp.com',
]
'''
    
    # Insérer après CSRF_COOKIE_HTTPONLY
    if 'CSRF_COOKIE_HTTPONLY' in content:
        pos = content.find('CSRF_COOKIE_HTTPONLY')
        newline_pos = content.find('\n', pos)
        if newline_pos != -1:
            content = content[:newline_pos+1] + csrf_config + content[newline_pos+1:]
    else:
        content += csrf_config
    
    with open(settings_file, 'w') as f:
        f.write(content)
    
    print("✓ CSRF_TRUSTED_ORIGINS ajouté")
else:
    print("CSRF_TRUSTED_ORIGINS déjà configuré")
    # Vérifier qu'il contient les bonnes valeurs
    match = re.search(r'CSRF_TRUSTED_ORIGINS\s*=\s*\[(.*?)\]', content, re.DOTALL)
    if match:
        print("Valeurs actuelles:", match.group(1))
EOF

echo ""
echo "6. REDÉMARRAGE DU SERVICE"
echo "========================="

systemctl restart martialcomp.service
sleep 3

echo ""
echo "============================================"
echo "CORRECTIONS APPLIQUÉES"
echo "============================================"
echo ""
echo "✅ Actions effectuées:"
echo "   1. Template language_selector.html corrigé avec {% csrf_token %}"
echo "   2. CSRF_TRUSTED_ORIGINS configuré pour martialcomp.com"
echo "   3. Service redémarré"
echo ""
echo "📋 Pour utiliser le sélecteur de langue:"
echo "   Dans vos templates, incluez:"
echo "   {% include 'competitions/includes/language_selector.html' %}"
echo ""
echo "🔍 Pour tester:"
echo "   1. Videz le cache du navigateur"
echo "   2. Allez sur https://martialcomp.com/"
echo "   3. Utilisez le sélecteur de langue"
echo ""
echo "Si le problème persiste, vérifiez:"
echo "   - Les cookies dans le navigateur (martialcomp_csrftoken)"
echo "   - Les logs: tail -f logs/django.log"
echo ""
echo "============================================"