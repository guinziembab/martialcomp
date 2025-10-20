#!/bin/bash

# Script final pour corriger définitivement le système de langues

echo "=== CORRECTION FINALE DU SYSTÈME DE LANGUES ==="
echo ""

cd /var/www/vhosts/martialcomp.com/httpdocs

# 1. Nettoyer et réorganiser les templates
echo "1. NETTOYAGE DES TEMPLATES"
echo "=========================="

# S'assurer que tous les templates de sélecteur sont au bon endroit
mkdir -p apps/core/templates/includes/
mkdir -p apps/competitions/templates/competitions/includes/

# Copier le template dans tous les endroits nécessaires
if [ -f "apps/core/templates/includes/language_selector_improved.html" ]; then
    cp apps/core/templates/includes/language_selector_improved.html apps/competitions/templates/competitions/includes/
    echo "✅ Template copié dans competitions"
fi

# Remplacer toutes les références au sélecteur amélioré par le standard
find apps -name "*.html" -type f -exec sed -i 's/language_selector_improved\.html/language_selector.html/g' {} \;
echo "✅ Références mises à jour vers le sélecteur standard"

# 2. Créer un sélecteur de langue simple et fonctionnel
echo ""
echo "2. CRÉATION D'UN SÉLECTEUR SIMPLE"
echo "================================="

cat > apps/core/templates/includes/language_selector.html << 'SELECTOR'
{% load i18n %}

<form action="{% url 'set_language' %}" method="post" style="display: inline-block;">
    {% csrf_token %}
    <input name="next" type="hidden" value="{{ redirect_to|default:request.get_full_path }}">
    <select name="language" onchange="this.form.submit();" style="padding: 5px; border-radius: 4px; border: 1px solid #ddd;">
        {% get_current_language as LANGUAGE_CODE %}
        {% get_available_languages as LANGUAGES %}
        {% get_language_info_list for LANGUAGES as languages %}
        {% for language in languages %}
            {% if language.code in 'fr,en,it,es,pt,ar' %}
                <option value="{{ language.code }}"{% if language.code == LANGUAGE_CODE %} selected{% endif %}>
                    {% if language.code == 'fr' %}🇫🇷 Français
                    {% elif language.code == 'en' %}🇬🇧 English
                    {% elif language.code == 'es' %}🇪🇸 Español
                    {% elif language.code == 'it' %}🇮🇹 Italiano
                    {% elif language.code == 'pt' %}🇵🇹 Português
                    {% elif language.code == 'ar' %}🇸🇦 العربية
                    {% endif %}
                </option>
            {% endif %}
        {% endfor %}
    </select>
</form>
SELECTOR

# Copier dans tous les endroits
cp apps/core/templates/includes/language_selector.html apps/competitions/templates/competitions/includes/

echo "✅ Sélecteur simple créé"

# 3. Revenir à la vue Django standard pour set_language
echo ""
echo "3. RESTAURATION DE LA VUE STANDARD"
echo "=================================="

# Modifier config/urls.py pour utiliser la vue Django standard
sed -i 's/from apps\.core\.views\.language import set_language_custom as set_language/from django.views.i18n import set_language/g' config/urls.py
sed -i 's/from apps\.core\.views\.i18n import set_language/from django.views.i18n import set_language/g' config/urls.py

echo "✅ Vue standard restaurée"

# 4. S'assurer que les traductions de base existent
echo ""
echo "4. VÉRIFICATION DES TRADUCTIONS"
echo "==============================="

/var/www/vhosts/martialcomp.com/venv/bin/python << 'CHECK_TRANS'
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
import django
django.setup()

from django.utils import translation
from django.utils.translation import gettext as _

print("Test rapide des traductions:")
for lang in ['fr', 'en', 'it', 'es', 'pt', 'ar']:
    translation.activate(lang)
    welcome = _('Welcome')
    print(f"  {lang}: 'Welcome' → '{welcome}'")
CHECK_TRANS

# 5. Corriger les permissions
echo ""
echo "5. PERMISSIONS"
echo "=============="

chown -R www-data:www-data apps/
chown -R www-data:www-data locale/
chmod -R 755 apps/
chmod -R 755 locale/

echo "✅ Permissions corrigées"

# 6. Redémarrer le service
echo ""
echo "6. REDÉMARRAGE"
echo "============="

systemctl restart martialcomp.service
sleep 3

if systemctl is-active --quiet martialcomp.service; then
    echo "✅ Service actif"
else
    echo "❌ Service inactif"
    systemctl status martialcomp.service | tail -10
fi

# 7. Test final
echo ""
echo "7. TEST FINAL"
echo "============="

echo "Test d'accès aux différentes langues:"
for lang in fr en it es pt ar; do
    code=$(curl -s -o /dev/null -w "%{http_code}" "https://martialcomp.com/$lang/")
    echo "  /$lang/ → Code HTTP: $code"
done

echo ""
echo "============================================"
echo "CORRECTION FINALE TERMINÉE"
echo "============================================"
echo ""
echo "Le système de langues devrait maintenant fonctionner."
echo ""
echo "Pour tester:"
echo "1. Allez sur https://martialcomp.com"
echo "2. Utilisez le sélecteur de langue"
echo "3. Vérifiez que l'URL change (ex: /fr/, /en/, /it/)"
echo "4. Vérifiez que les textes de base sont traduits"
echo ""
echo "Langues disponibles: FR, EN, IT, ES, PT, AR"
echo ""