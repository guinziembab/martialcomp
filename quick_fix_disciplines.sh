#!/bin/bash
# Script rapide pour corriger les disciplines en production

echo "🚀 CORRECTION RAPIDE - DISCIPLINES PRODUCTION"
echo "==========================================="

# Aller dans le bon répertoire
cd /var/www/vhosts/martialcomp.com/httpdocs

# Activer l'environnement virtuel
source venv/bin/activate

echo ""
echo "1️⃣ Vérification initiale..."
python manage.py shell --settings=config.settings.production -c "from apps.competitions.models import Discipline; print(f'Disciplines actuelles: {Discipline.objects.count()}')"

echo ""
echo "2️⃣ Application des migrations..."
python manage.py migrate --settings=config.settings.production --noinput

echo ""
echo "3️⃣ Chargement des disciplines..."
# Essayer la commande load_disciplines
python manage.py load_disciplines --settings=config.settings.production 2>/dev/null || {
    echo "   ⚠️  Commande load_disciplines non trouvée, création manuelle..."
    
    # Création manuelle si la commande n'existe pas
    python manage.py shell --settings=config.settings.production << EOF
from apps.competitions.models import Discipline

disciplines = [
    ('Karaté', 'Art martial japonais'),
    ('Judo', 'Art martial japonais de projection'),
    ('Taekwondo', 'Art martial coréen'),
    ('Aikido', 'Art martial japonais défensif'),
    ('Kung Fu', 'Arts martiaux chinois'),
    ('Boxe', 'Sport de combat avec les poings'),
    ('MMA', 'Arts martiaux mixtes'),
    ('Krav Maga', 'Self-défense israélienne'),
    ('Capoeira', 'Art martial brésilien'),
    ('Long Phai', 'Art martial vietnamien')
]

created = 0
for name, desc in disciplines:
    _, is_new = Discipline.objects.get_or_create(
        name=name,
        defaults={'description': desc, 'is_active': True}
    )
    if is_new:
        created += 1

print(f"✅ {created} nouvelles disciplines créées")
print(f"📊 Total: {Discipline.objects.count()} disciplines en base")
EOF
}

echo ""
echo "4️⃣ Test de création practitioner..."
python manage.py shell --settings=config.settings.production << EOF
try:
    from apps.competitions.models import Practitioner
    from apps.organizations.models import Organization
    
    org = Organization.objects.first()
    if org:
        p = Practitioner.objects.create(
            first_name="Test",
            last_name="QuickFix",
            organization=org
        )
        print(f"✅ Test OK - Practitioner créé (ID: {p.id})")
        p.delete()
        print("✅ Test nettoyé")
    else:
        print("⚠️  Pas d'organisation pour le test")
except Exception as e:
    print(f"❌ Erreur: {e}")
EOF

echo ""
echo "5️⃣ Résumé final..."
python manage.py shell --settings=config.settings.production -c "from apps.competitions.models import Discipline; print(f'✅ Disciplines en base: {Discipline.objects.count()}')"

echo ""
echo "==========================================="
echo "✅ Correction terminée!"
echo ""
echo "Prochaines étapes:"
echo "1. Tester l'accès à /fr/admin/competitions/practitioner/"
echo "2. Si OK, retirer le middleware de blocage dans production.py"
echo "==========================================="