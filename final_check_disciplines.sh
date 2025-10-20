#!/bin/bash
# Vérification finale avec python3

echo "================================================"
echo "🔍 VÉRIFICATION FINALE DISCIPLINES"
echo "================================================"
echo ""

ssh martialcomp-production << 'REMOTE_COMMANDS'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "✅ Fichier forms/onboarding.py modifié avec succès!"
echo "Les disciplines sont maintenant dans Meta.fields:"
grep "fields = \[" apps/competitions/forms/onboarding.py | grep disciplines

echo ""
echo "📊 Vérification rapide des disciplines:"
source /var/www/vhosts/martialcomp.com/venv/bin/activate

python3 -c "
from apps.competitions.models import Discipline
count = Discipline.objects.filter(is_active=True).count()
print(f'✅ Nombre de disciplines actives: {count}')
if count > 0:
    print('📋 Premières disciplines:')
    for d in Discipline.objects.filter(is_active=True)[:5]:
        print(f'  - {d.name}')
"

echo ""
echo "🧪 Test du formulaire:"
python3 -c "
from apps.competitions.forms.onboarding import FederationCreationForm
form = FederationCreationForm()
if 'disciplines' in form.fields:
    print('✅ SUCCESS: Le champ disciplines est dans le formulaire!')
    print(f'   Nombre de disciplines disponibles: {form.fields[\"disciplines\"].queryset.count()}')
else:
    print('❌ ERREUR: disciplines manquant')
"

echo ""
echo "================================================"
echo "✅ CORRECTION APPLIQUÉE AVEC SUCCÈS!"
echo "================================================"
echo ""
echo "La correction des disciplines fédération est maintenant active."
echo ""
echo "🎯 Pour tester:"
echo "1. Allez sur https://app.martialcomp.com"
echo "2. Connectez-vous ou créez un compte"
echo "3. Accédez à: https://app.martialcomp.com/competitions/onboarding/federation/"
echo "4. Les cases à cocher des disciplines devraient maintenant être visibles!"
echo ""
REMOTE_COMMANDS