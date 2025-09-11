#!/bin/bash

echo "=== MIGRATION MULTI-TENANT MARTIALCOMP ==="
echo "Date: $(date)"
echo

# 1. Vérifier l'état actuel
echo "1. État actuel de la base de données..."
python manage.py shell << EOF
from competitions.models import Club, Practitioner, Competition
from multitenant.models import Tenant

# Statistiques actuelles
total_clubs = Club.objects.count()
migrated_clubs = Club.objects.filter(is_migrated=True).count()
pending_clubs = total_clubs - migrated_clubs

print(f"Total de clubs: {total_clubs}")
print(f"Clubs migrés: {migrated_clubs}")
print(f"Clubs à migrer: {pending_clubs}")
print()

# Clubs à migrer
if pending_clubs > 0:
    print("Clubs en attente de migration:")
    for club in Club.objects.filter(is_migrated=False)[:10]:
        print(f"  - ID: {club.id}, Nom: {club.name}, Pratiquants: {club.practitioners.count()}")
    
    if pending_clubs > 10:
        print(f"  ... et {pending_clubs - 10} autres")
print()

# Tenants existants
tenant_count = Tenant.objects.count()
print(f"Tenants existants: {tenant_count}")
if tenant_count > 0:
    for tenant in Tenant.objects.all()[:5]:
        print(f"  - {tenant.name} ({tenant.schema_name})")
EOF

echo
echo "2. Test de la migration en dry-run..."
echo "Simulation de migration pour 3 premiers clubs..."
python manage.py migrate_clubs_to_tenants --dry-run --batch-size 3

echo
read -p "Continuer avec la migration réelle? (oui/non): " response

if [[ "$response" == "oui" || "$response" == "o" ]]; then
    echo
    echo "3. Début de la migration réelle..."
    
    # Créer le répertoire de rapports
    mkdir -p migration_reports
    
    # Migration interactive par batch
    python manage.py migrate_clubs_to_tenants \
        --batch-size 5 \
        --interactive \
        --report-dir migration_reports
    
    echo
    echo "4. Vérification post-migration..."
    python manage.py shell << EOF
from competitions.models import Club
from multitenant.models import Tenant

# Statistiques finales
total_clubs = Club.objects.count()
migrated_clubs = Club.objects.filter(is_migrated=True).count()
success_rate = (migrated_clubs / total_clubs * 100) if total_clubs > 0 else 0

print(f"Migration terminée:")
print(f"  - Total de clubs: {total_clubs}")
print(f"  - Clubs migrés: {migrated_clubs}")
print(f"  - Taux de succès: {success_rate:.1f}%")
print()

# Tenants créés
tenant_count = Tenant.objects.count()
print(f"Tenants créés: {tenant_count}")
for tenant in Tenant.objects.all()[:10]:
    print(f"  - {tenant.name} ({tenant.domain})")
EOF

    echo
    echo "5. Sauvegarde du rapport..."
    timestamp=$(date +%Y%m%d_%H%M%S)
    report_file="migration_reports/final_report_${timestamp}.json"
    
    python manage.py shell << EOF
import json
from datetime import datetime
from competitions.models import Club
from multitenant.models import Tenant

report = {
    'migration_date': datetime.now().isoformat(),
    'statistics': {
        'total_clubs': Club.objects.count(),
        'migrated_clubs': Club.objects.filter(is_migrated=True).count(),
        'total_tenants': Tenant.objects.count(),
    },
    'tenants': [
        {
            'name': t.name,
            'schema': t.schema_name,
            'domain': t.domain,
            'plan': t.subscription_plan,
            'created': t.created_at.isoformat() if hasattr(t, 'created_at') else None
        }
        for t in Tenant.objects.all()
    ]
}

with open('$report_file', 'w') as f:
    json.dump(report, f, indent=2)

print(f"Rapport sauvegardé: $report_file")
EOF

    echo
    echo "=== MIGRATION TERMINÉE ==="
    echo "Consultez les rapports dans le dossier 'migration_reports/'"
else
    echo "Migration annulée."
fi