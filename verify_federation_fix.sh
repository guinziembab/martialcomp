#!/bin/bash
# Script pour vérifier que la correction fonctionne

echo "================================================"
echo "🔍 VÉRIFICATION CORRECTION DISCIPLINES"
echo "================================================"
echo ""

ssh martialcomp-production << 'REMOTE_COMMANDS'
cd /var/www/vhosts/martialcomp.com/httpdocs
source /var/www/vhosts/martialcomp.com/venv/bin/activate

echo "1️⃣ Vérification du fichier modifié:"
echo "===================================="
grep -A 2 "fields = \[" apps/competitions/forms/onboarding.py | grep -B1 -A1 disciplines

echo ""
echo "2️⃣ Vérification des disciplines en base:"
echo "========================================"
python manage.py shell << 'PYEOF'
from apps.competitions.models import Discipline

# Compter les disciplines
total = Discipline.objects.count()
active = Discipline.objects.filter(is_active=True).count()

print(f"📊 Total disciplines: {total}")
print(f"✅ Disciplines actives: {active}")

if active == 0:
    print("\n⚠️  Aucune discipline active! Création des disciplines...")
    disciplines = [
        ('Karaté', 'Art martial japonais'),
        ('Judo', 'Art martial japonais, sport olympique'),
        ('Taekwondo', 'Art martial coréen, sport olympique'),
        ('Kung Fu', 'Arts martiaux chinois'),
        ('Aikido', 'Art martial japonais défensif'),
        ('Boxe', 'Sport de combat avec les poings'),
        ('MMA', 'Arts martiaux mixtes'),
        ('Muay Thai', 'Boxe thaïlandaise'),
        ('Jiu-Jitsu Brésilien', 'Art martial brésilien'),
        ('Krav Maga', 'Système de défense israélien'),
    ]
    
    for name, desc in disciplines:
        d, created = Discipline.objects.get_or_create(
            name=name,
            defaults={'description': desc, 'is_active': True}
        )
        if created:
            print(f"  ✅ Créé: {name}")
    
    print(f"\n✅ {Discipline.objects.filter(is_active=True).count()} disciplines actives maintenant")
else:
    print("\n📋 Disciplines existantes:")
    for d in Discipline.objects.filter(is_active=True)[:10]:
        print(f"  - {d.name}")
PYEOF

echo ""
echo "3️⃣ Test du formulaire:"
echo "======================"
python manage.py shell << 'PYEOF'
from apps.competitions.forms.onboarding import FederationCreationForm

# Créer une instance du formulaire
form = FederationCreationForm()

print("🧪 Test du formulaire FederationCreationForm:")
print(f"  - Nombre de champs: {len(form.fields)}")

if 'disciplines' in form.fields:
    print("  ✅ Le champ 'disciplines' est présent!")
    field = form.fields['disciplines']
    print(f"  - Type de widget: {field.widget.__class__.__name__}")
    print(f"  - Nombre de choix: {field.queryset.count()}")
    print(f"  - Requis: {field.required}")
else:
    print("  ❌ ERREUR: Le champ 'disciplines' n'est pas dans le formulaire!")

# Lister tous les champs
print("\n📋 Tous les champs du formulaire:")
for name in form.fields:
    print(f"  - {name}")
PYEOF

echo ""
echo "4️⃣ Collecte des fichiers statiques:"
echo "===================================="
python manage.py collectstatic --noinput --clear > /dev/null 2>&1
echo "✅ Fichiers statiques collectés"

echo ""
echo "================================================"
echo "✅ VÉRIFICATION TERMINÉE"
echo "================================================"
echo ""
echo "🎯 Prochaines étapes:"
echo "1. Ouvrir https://app.martialcomp.com/competitions/onboarding/federation/"
echo "2. Les cases à cocher des disciplines devraient maintenant s'afficher"
echo "3. Créer une fédération test pour vérifier que tout fonctionne"
echo ""
REMOTE_COMMANDS