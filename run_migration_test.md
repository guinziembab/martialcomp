# Test de la migration multi-tenant

## 1. Préparation

Assurez-vous d'être dans le répertoire du projet :
```bash
cd /mnt/c/martial_hub_django/martialcomp
```

## 2. Test simple

### Test avec des données de test
```bash
# Créer et migrer un club de test
python manage.py test_migration --mode=simple

# Voir les détails
python manage.py test_migration --mode=all

# Nettoyer après le test
python manage.py test_migration --cleanup
```

### Test dry-run (sans modifications)
```bash
python manage.py test_migration --mode=dry-run
```

## 3. Migration réelle

### Lister les clubs à migrer
```bash
python manage.py shell << EOF
from competitions.models import Club
clubs = Club.objects.filter(is_migrated=False)
for club in clubs:
    print(f"ID: {club.id}, Nom: {club.name}, Pratiquants: {club.practitioners.count()}")
EOF
```

### Migrer un club spécifique
```bash
# Remplacer 123 par l'ID du club
python manage.py migrate_clubs_to_tenants --club-ids 123 --dry-run

# Si tout semble bon, faire la migration réelle
python manage.py migrate_clubs_to_tenants --club-ids 123
```

### Migrer tous les clubs
```bash
# D'abord en dry-run
python manage.py migrate_clubs_to_tenants --dry-run --batch-size 5

# Puis la migration réelle
python manage.py migrate_clubs_to_tenants --batch-size 5 --interactive
```

## 4. Vérification

### Vérifier les tenants créés
```bash
python manage.py shell << EOF
from multitenant.models import Tenant
for tenant in Tenant.objects.all():
    print(f"Tenant: {tenant.name}")
    print(f"  Schema: {tenant.schema_name}")
    print(f"  Domaine: {tenant.domain}")
    print(f"  Plan: {tenant.subscription_plan}")
    print(f"  Actif: {tenant.is_active}")
    print()
EOF
```

### Valider une migration
```bash
python manage.py validate_tenant_migration
```

## 5. Rapport de migration

Les rapports sont sauvegardés dans le dossier `migration_reports/`.

### Voir le dernier rapport
```bash
ls -la migration_reports/
cat migration_reports/migration_report_*.json | python -m json.tool
```

## 6. En cas de problème

### Rollback d'un club
```bash
# Remplacer 123 par l'ID du club
python manage.py migrate_clubs_to_tenants --rollback 123
```

### Logs de debug
```bash
# Activer les logs détaillés
export DJANGO_LOG_LEVEL=DEBUG
python manage.py migrate_clubs_to_tenants --club-ids 123
```

## 7. Commandes utiles

### État de la migration
```bash
python manage.py shell << EOF
from competitions.models import Club
total = Club.objects.count()
migrated = Club.objects.filter(is_migrated=True).count()
print(f"Migration: {migrated}/{total} clubs ({migrated/total*100:.1f}%)")
EOF
```

### Tester l'accès à un tenant
```bash
# Remplacer 'club_name' par le nom du schéma
python manage.py shell << EOF
from django.db import connection
schema_name = 'club_name'
with connection.cursor() as cursor:
    cursor.execute(f'SET search_path TO {schema_name}')
    cursor.execute('SELECT COUNT(*) FROM competitions_practitioner')
    count = cursor.fetchone()[0]
    print(f"Pratiquants dans {schema_name}: {count}")
EOF
```

## Notes importantes

1. **Toujours faire un backup avant la migration**
2. **Tester d'abord en dry-run**
3. **Migrer par petits batches pour les grandes bases**
4. **Vérifier les rapports après chaque batch**
5. **Avoir un plan de rollback**