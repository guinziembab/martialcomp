#!/bin/bash

# Script de test simple pour la migration multi-tenant

echo "=== Test de migration multi-tenant MartialComp ==="
echo

# 1. Test du dry-run
echo "1. Test en mode dry-run..."
python manage.py migrate_clubs_to_tenants --dry-run --batch-size 1

echo
echo "2. Création de données de test..."
python manage.py shell << EOF
from competitions.models import Club, Practitioner
from django.contrib.auth.models import User

# Créer un admin
admin, _ = User.objects.get_or_create(
    username='admin_test',
    defaults={'email': 'admin@test.com', 'is_staff': True}
)
admin.set_password('testpass123')
admin.save()

# Créer un club de test
club = Club.objects.create(
    name="Test Migration Club",
    city="Paris",
    country="FR",
    email="test@migration.com",
    owner=admin
)

# Ajouter des pratiquants
for i in range(5):
    Practitioner.objects.create(
        first_name=f"Test{i}",
        last_name="Migrant",
        email=f"test{i}@migration.com",
        club=club
    )

print(f"Club créé: {club.name} (ID: {club.id})")
print(f"Pratiquants: {club.practitioners.count()}")
EOF

echo
echo "3. Migration du club de test..."
python manage.py migrate_clubs_to_tenants --interactive --batch-size 1

echo
echo "4. Vérification de la migration..."
python manage.py shell << EOF
from competitions.models import Club
from multitenant.models import Tenant

# Vérifier le club
club = Club.objects.get(name="Test Migration Club")
if hasattr(club, 'tenant') and club.tenant:
    tenant = club.tenant
    print(f"✓ Migration réussie!")
    print(f"  - Tenant: {tenant.name}")
    print(f"  - Schema: {tenant.schema_name}")
    print(f"  - Domaine: {tenant.domain}")
    print(f"  - Plan: {tenant.subscription_plan}")
else:
    print("✗ Échec de la migration")
EOF

echo
echo "5. Génération du rapport..."
python manage.py shell << EOF
import json
from datetime import datetime

# Créer un rapport
report = {
    'test_date': datetime.now().isoformat(),
    'test_type': 'migration_simple',
    'status': 'completed'
}

with open('migration_test_report.json', 'w') as f:
    json.dump(report, f, indent=2)

print("Rapport sauvegardé: migration_test_report.json")
EOF

echo
echo "=== Test terminé ==="