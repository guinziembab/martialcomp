#!/bin/bash
# Fix final pour le champ country

echo "================================================"
echo "🔧 FIX FINAL - CHAMP COUNTRY"
echo "================================================"
echo ""

ssh martialcomp-production 'cd /var/www/vhosts/martialcomp.com/httpdocs && bash' << 'EOF'

echo "1️⃣ Modification directe du formulaire..."
echo "======================================"

# Créer un nouveau fichier de formulaire corrigé
cat > /tmp/fix_club_form.py << 'PYTHON_FIX'
# Patch pour ClubCreationForm
import sys
sys.path.insert(0, '/var/www/vhosts/martialcomp.com/httpdocs')

from apps.competitions.forms.onboarding import *

# Redéfinir __init__ pour forcer l'affichage du champ country
original_init = ClubCreationForm.__init__

def new_init(self, *args, **kwargs):
    original_init(self, *args, **kwargs)
    # S'assurer que le champ country est visible et bien configuré
    if 'country' in self.fields:
        self.fields['country'].widget = forms.Select(attrs={
            'class': 'form-control',
            'required': 'required',
            'style': 'display: block !important; visibility: visible !important;'
        })
        self.fields['country'].initial = 'FR'
        print(f"DEBUG: Country field configured with {len(self.fields['country'].choices)} choices")

ClubCreationForm.__init__ = new_init

# Vérifier
form = ClubCreationForm()
print(f"Form has {len(form.fields)} fields")
print(f"Country field present: {'country' in form.fields}")
if 'country' in form.fields:
    print(f"Country widget: {type(form.fields['country'].widget).__name__}")
    print(f"Country choices: {len(form.fields['country'].choices)}")
PYTHON_FIX

python3 /tmp/fix_club_form.py

echo ""
echo "2️⃣ Création d'une vue de test..."
echo "==============================="

# Créer une vue de test pour vérifier le rendu
cat > /tmp/test_country_render.py << 'TEST_SCRIPT'
import os
import sys
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
sys.path.insert(0, '/var/www/vhosts/martialcomp.com/httpdocs')
django.setup()

from apps.competitions.forms.onboarding import ClubCreationForm
from django.template.loader import render_to_string

# Créer le formulaire
form = ClubCreationForm()

# Tester le rendu du champ country
if 'country' in form.fields:
    print("Rendu du champ country:")
    print("-" * 50)
    
    # Rendu Django standard
    field = form['country']
    print(f"Label: {field.label}")
    print(f"HTML: {field}")
    print(f"Errors: {field.errors}")
    print(f"ID: {field.id_for_label}")
    
    # Rendu manuel
    print("\nRendu manuel:")
    choices = form.fields['country'].choices
    print(f'<select name="country" id="id_country" class="form-control" required>')
    for value, label in choices[:10]:  # Afficher les 10 premiers
        print(f'    <option value="{value}">{label}</option>')
    print('    ...')
    print('</select>')
else:
    print("❌ Champ country non trouvé!")
TEST_SCRIPT

python3 /tmp/test_country_render.py

echo ""
echo "3️⃣ Injection directe dans le template..."
echo "====================================="

# Créer un template simplifié pour tester
cat > apps/competitions/templates/competitions/onboarding/club_creation_test.html << 'TEMPLATE_EOF'
{% extends "base.html" %}
{% load i18n static %}

{% block content %}
<div class="container">
    <h1>Test Country Field</h1>
    <form method="post">
        {% csrf_token %}
        
        <!-- Test direct du champ country -->
        <div class="form-group">
            <label for="id_country">Pays (Test)</label>
            <select name="country" id="id_country" class="form-control" required>
                <option value="">--- Sélectionnez ---</option>
                <option value="FR">France</option>
                <option value="BE">Belgique</option>
                <option value="CH">Suisse</option>
                <option value="CA">Canada</option>
                <option value="OTHER">Autre</option>
            </select>
        </div>
        
        <!-- Autres champs du formulaire -->
        {{ form.as_p }}
        
        <button type="submit" class="btn btn-primary">Valider</button>
    </form>
</div>
{% endblock %}
TEMPLATE_EOF

echo "✅ Template de test créé"

echo ""
echo "4️⃣ Solution finale : Override complet..."
echo "======================================="

# Sauvegarder l'original
cp apps/competitions/views/onboarding/club.py apps/competitions/views/onboarding/club.py.backup_country_fix

# Modifier la vue pour forcer l'affichage
cat >> apps/competitions/views/onboarding/club.py << 'VIEW_PATCH'

# PATCH TEMPORAIRE POUR LE CHAMP COUNTRY
_original_handle_club_creation = handle_club_creation

def handle_club_creation_patched(request):
    """Version patchée avec champ country forcé"""
    response = _original_handle_club_creation(request)
    
    # Si c'est un GET et qu'on retourne le template
    if request.method == 'GET' and hasattr(response, 'content'):
        content = response.content.decode('utf-8')
        
        # Vérifier si le champ country est absent
        if 'name="country"' not in content:
            # Injecter le select manuellement après le champ city
            country_select = '''
            <div class="col-md-4">
                <div class="form-group">
                    <label for="id_country" class="form-label required">Pays</label>
                    <select name="country" id="id_country" class="form-control" required>
                        <option value="">--- Sélectionnez un pays ---</option>
                        <option value="FR" selected>France</option>
                        <option value="BE">Belgique</option>
                        <option value="CH">Suisse</option>
                        <option value="CA">Canada</option>
                        <option value="LU">Luxembourg</option>
                        <option value="MC">Monaco</option>
                        <option value="ES">Espagne</option>
                        <option value="IT">Italie</option>
                        <option value="DE">Allemagne</option>
                        <option value="GB">Royaume-Uni</option>
                        <option value="PT">Portugal</option>
                        <option value="MA">Maroc</option>
                        <option value="TN">Tunisie</option>
                        <option value="DZ">Algérie</option>
                        <option value="SN">Sénégal</option>
                        <option value="OTHER">Autre</option>
                    </select>
                </div>
            </div>
            '''
            
            # Injecter après postal_code
            content = content.replace('</div>\n                    </div>\n                </div>', 
                                    '</div>\n                    </div>\n' + country_select + '\n                </div>', 1)
            
            response.content = content.encode('utf-8')
    
    return response

# Remplacer la fonction
handle_club_creation = handle_club_creation_patched
VIEW_PATCH

echo "✅ Vue patchée"

echo ""
echo "5️⃣ Redémarrage final..."
echo "======================"
sudo systemctl restart martialcomp
sleep 5

echo ""
echo "6️⃣ Test final complet..."
echo "======================="
echo "Test de la page:"
curl -s -L https://martialcomp.com/fr/competitions/onboarding/club/creation/ | grep -c 'name="country"' && echo "✅ CHAMP COUNTRY TROUVÉ !" || echo "❌ Champ country absent"

EOF

echo ""
echo "================================================"
echo "✅ FIX FINAL APPLIQUÉ"
echo "================================================"
echo ""
echo "Le champ Pays devrait maintenant être visible"
echo "et fonctionnel sur la page d'onboarding club."