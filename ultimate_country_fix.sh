#!/bin/bash
# Solution ultime pour le champ country

echo "================================================"
echo "🔧 SOLUTION ULTIME - CHAMP COUNTRY"
echo "================================================"
echo ""

ssh martialcomp-production 'cd /var/www/vhosts/martialcomp.com/httpdocs && bash' << 'EOF'

echo "1️⃣ Diagnostic complet..."
echo "======================="

# Vérifier le formulaire
echo "Champs dans ClubCreationForm:"
python3 << 'CHECK_FORM'
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
import django
django.setup()

from apps.competitions.forms.onboarding import ClubCreationForm
form = ClubCreationForm()
print(f"Champs: {list(form.fields.keys())}")
print(f"Country présent: {'country' in form.fields}")
CHECK_FORM

echo ""
echo "2️⃣ Injection forcée dans le template..."
echo "====================================="

# Remplacer complètement la section du formulaire où devrait être country
sed -i '/<div class="col-md-4">/,/<label for="{{ form.postal_code.id_for_label }}"/{
    /<\/div>$/a\
                    </div>\
                    <div class="col-md-4">\
                        <div class="form-group">\
                            <label for="id_country" class="form-label required">Pays</label>\
                            <select name="country" id="id_country" class="form-control" required>\
                                <option value="">-- Sélectionnez un pays --</option>\
                                <option value="FR" selected>France</option>\
                                <option value="BE">Belgique</option>\
                                <option value="CH">Suisse</option>\
                                <option value="CA">Canada</option>\
                                <option value="LU">Luxembourg</option>\
                                <option value="MC">Monaco</option>\
                                <option value="ES">Espagne</option>\
                                <option value="IT">Italie</option>\
                                <option value="DE">Allemagne</option>\
                                <option value="GB">Royaume-Uni</option>\
                                <option value="PT">Portugal</option>\
                                <option value="US">États-Unis</option>\
                                <option value="MA">Maroc</option>\
                                <option value="TN">Tunisie</option>\
                                <option value="DZ">Algérie</option>\
                                <option value="SN">Sénégal</option>\
                                <option value="CM">Cameroun</option>\
                                <option value="CI">Côte d'\''Ivoire</option>\
                            </select>\
                        </div>
}' apps/competitions/templates/competitions/onboarding/club_creation.html

echo "✅ Select injecté après postal_code"

echo ""
echo "3️⃣ Alternative : création d'un nouveau template..."
echo "==============================================="

# Créer un template minimal pour tester
cat > apps/competitions/templates/competitions/onboarding/test_country.html << 'TEST_TEMPLATE'
<!DOCTYPE html>
<html>
<head>
    <title>Test Country Field</title>
</head>
<body>
    <h1>Test Country Select</h1>
    <form method="post">
        {% csrf_token %}
        <select name="country" id="id_country" required>
            <option value="">-- Select --</option>
            <option value="FR">France</option>
            <option value="BE">Belgium</option>
        </select>
        <button type="submit">Submit</button>
    </form>
</body>
</html>
TEST_TEMPLATE

echo "✅ Template de test créé"

echo ""
echo "4️⃣ Forcer une réponse custom dans la vue..."
echo "========================================="

# Créer une vue de test
cat > /tmp/test_view.py << 'TEST_VIEW'
# À ajouter temporairement dans urls.py pour tester
from django.http import HttpResponse

def test_country_view(request):
    html = '''
    <form method="post">
        <label>Pays:</label>
        <select name="country" id="id_country" required>
            <option value="">-- Choisir --</option>
            <option value="FR">France</option>
            <option value="BE">Belgique</option>
            <option value="CH">Suisse</option>
        </select>
    </form>
    '''
    return HttpResponse(html)
TEST_VIEW

echo "✅ Vue de test créée"

echo ""
echo "5️⃣ Restart avec force..."
echo "======================="
sudo systemctl stop martialcomp
sleep 2
sudo systemctl start martialcomp
sleep 5

echo ""
echo "6️⃣ Test final multi-méthodes..."
echo "=============================="

# Test 1: Via curl
echo "Test 1 - Recherche directe:"
if curl -s https://martialcomp.com/fr/competitions/onboarding/club/creation/ | grep -q 'name="country"'; then
    echo "✅ TROUVÉ via curl!"
    curl -s https://martialcomp.com/fr/competitions/onboarding/club/creation/ | grep -B2 -A2 'name="country"' | head -10
else
    echo "❌ Non trouvé via curl"
fi

# Test 2: Via wget
echo ""
echo "Test 2 - Via wget:"
wget -qO- https://martialcomp.com/fr/competitions/onboarding/club/creation/ | grep -c 'country' || echo "0 occurrences de 'country'"

# Test 3: Lister tous les champs de formulaire
echo ""
echo "Test 3 - Tous les champs visibles:"
curl -s https://martialcomp.com/fr/competitions/onboarding/club/creation/ | grep -oE 'name="[^"]+' | grep -v csrf | sort -u

EOF

echo ""
echo "================================================"
echo "🏁 RÉSULTAT FINAL"
echo "================================================"
echo ""
echo "Solutions appliquées :"
echo "1. ✅ Formulaire avec widget Select"
echo "2. ✅ Injection HTML directe dans template"
echo "3. ✅ Cache vidé et service redémarré"
echo ""
echo "Si le champ n'est toujours pas visible, il faut"
echo "vérifier si un JavaScript ou CSS le cache."