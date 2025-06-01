# Guide de Migration Multi-Tenant MartialComp

## Introduction

Ce guide détaille le processus de migration des clubs existants vers la nouvelle architecture multi-tenant. La migration est conçue pour être progressive, sûre et réversible.

## Prérequis

### Infrastructure
- PostgreSQL 12+ avec support des schémas
- Redis pour le cache
- Espace disque suffisant (2x la taille actuelle de la DB)
- Accès SSH aux serveurs de production

### Logiciels
```bash
# Installer les dépendances
pip install -r requirements.txt
pip install -r requirements-performance.txt

# Vérifier PostgreSQL
psql --version

# Vérifier Redis
redis-cli ping
```

### Permissions
- Accès superuser PostgreSQL
- Accès administrateur Django
- Permissions de backup/restore

## Workflow de Migration

### 1. Préparation (1-2 jours)

#### A. Audit Initial
```bash
# Analyser l'état actuel
python manage.py audit_clubs --report

# Identifier les clubs problématiques
python manage.py check_migration_readiness
```

#### B. Test en Environnement de Staging
```bash
# Créer un environnement de test
./scripts/create_staging_env.sh

# Migrer un club test
python manage.py migrate_clubs_to_tenants --club-ids 1 --dry-run
```

#### C. Communication
- Informer les clubs de la migration
- Planifier les fenêtres de maintenance
- Préparer l'équipe de support

### 2. Migration Pilote (3-5 jours)

#### A. Sélectionner les Clubs Pilotes
```python
# Dans le shell Django
from competitions.models import Club

# Clubs petits et moyens, actifs
pilot_clubs = Club.objects.filter(
    practitioners__count__lt=100,
    is_active=True
).order_by('?')[:5]

pilot_ids = list(pilot_clubs.values_list('id', flat=True))
print(f"Clubs pilotes: {pilot_ids}")
```

#### B. Migrer les Clubs Pilotes
```bash
# Migration avec monitoring détaillé
python manage.py migrate_clubs_to_tenants \
    --club-ids 1 2 3 4 5 \
    --interactive \
    --report-dir ./pilot_reports

# Valider chaque migration
python manage.py validate_tenant_migration club1_schema --full
```

#### C. Collecter le Feedback
```bash
# Générer un rapport de validation
python manage.py generate_migration_report \
    --tenants club1 club2 club3 \
    --output pilot_validation.json
```

### 3. Migration Production (1-2 semaines)

#### A. Backup Complet
```bash
# Backup de la base de données
pg_dump -h localhost -U postgres martialcomp > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup des fichiers media
tar -czf media_backup_$(date +%Y%m%d_%H%M%S).tar.gz media/
```

#### B. Migration Progressive
```bash
# Migrer par groupes de taille
# Groupe 1: Petits clubs (< 50 pratiquants)
python manage.py migrate_clubs_to_tenants \
    --filter-size small \
    --batch-size 20 \
    --report-dir ./migration_reports/small

# Groupe 2: Clubs moyens (50-200 pratiquants)
python manage.py migrate_clubs_to_tenants \
    --filter-size medium \
    --batch-size 10 \
    --report-dir ./migration_reports/medium

# Groupe 3: Grands clubs (> 200 pratiquants)
python manage.py migrate_clubs_to_tenants \
    --filter-size large \
    --batch-size 5 \
    --report-dir ./migration_reports/large \
    --interactive
```

#### C. Migration avec Monitoring Live
```python
# Script de migration avec monitoring
from multitenant.migrations.progressive_migration import MigrationOrchestrator

orchestrator = MigrationOrchestrator()
orchestrator.run_migration(
    dry_run=False,
    club_ids=None  # Tous les clubs non migrés
)
```

### 4. Validation Post-Migration

#### A. Tests d'Intégrité
```bash
# Valider tous les tenants
for schema in $(python manage.py list_tenants --format=schema); do
    echo "Validation de $schema"
    python manage.py validate_tenant_migration $schema --full
done
```

#### B. Tests de Performance
```bash
# Optimiser et tester
python manage.py optimize_tenant_db --all
python manage.py test_tenant_performance --report
```

#### C. Tests Fonctionnels
```python
# Tests automatisés
python manage.py test multitenant.tests.test_migration
python manage.py test competitions.tests.test_tenant_isolation
```

### 5. Finalisation

#### A. Configuration DNS
```bash
# Configurer les sous-domaines
# Pour chaque tenant, créer un enregistrement DNS
# *.martialcomp.com -> serveur application
```

#### B. Certificats SSL
```bash
# Générer les certificats wildcard
certbot certonly \
    --dns-cloudflare \
    --dns-cloudflare-credentials ~/.cloudflare.ini \
    -d *.martialcomp.com
```

#### C. Mise à Jour de la Configuration
```python
# settings.py
ALLOWED_HOSTS = [
    '.martialcomp.com',
    'martialcomp.com',
]

# Configuration nginx
server {
    server_name *.martialcomp.com;
    # ...
}
```

## Commandes Utiles

### Migration
```bash
# Migration simple
python manage.py migrate_clubs_to_tenants

# Migration avec options
python manage.py migrate_clubs_to_tenants \
    --club-ids 1 2 3 \
    --dry-run \
    --batch-size 5 \
    --report-dir ./reports

# Migration interactive
python manage.py migrate_clubs_to_tenants --interactive
```

### Validation
```bash
# Validation basique
python manage.py validate_tenant_migration schema_name

# Validation complète
python manage.py validate_tenant_migration schema_name --full

# Validation avec corrections
python manage.py validate_tenant_migration schema_name --full --fix
```

### Monitoring
```bash
# État des tenants
python manage.py tenant_status

# Statistiques de migration
python manage.py migration_stats --format=json

# Health check
python manage.py check_tenant_health --all
```

### Rollback
```bash
# Rollback d'un club spécifique
python manage.py migrate_clubs_to_tenants --rollback 123

# Rollback complet (dernier recours)
psql -U postgres martialcomp < backup_pre_migration.sql
```

## Troubleshooting

### Problème 1: Échec de création de schéma
```bash
# Vérifier les permissions PostgreSQL
psql -U postgres -c "SELECT has_schema_privilege('user', 'CREATE');"

# Créer manuellement si nécessaire
psql -U postgres -c "CREATE SCHEMA schema_name;"
```

### Problème 2: Timeout pendant la migration
```python
# Augmenter le timeout dans settings.py
DATABASES['default']['OPTIONS']['connect_timeout'] = 30
DATABASES['default']['OPTIONS']['options'] = '-c statement_timeout=60000'
```

### Problème 3: Contraintes d'intégrité
```sql
-- Désactiver temporairement les contraintes
SET session_replication_role = 'replica';

-- Réactiver après migration
SET session_replication_role = 'origin';
```

### Problème 4: Mémoire insuffisante
```bash
# Augmenter la mémoire PostgreSQL
postgresql.conf:
shared_buffers = 2GB
work_mem = 256MB
maintenance_work_mem = 1GB
```

## Checklist de Production

### Avant la Migration
- [ ] Backup complet effectué
- [ ] Tests en staging réussis
- [ ] Équipe de support briefée
- [ ] Communication envoyée aux clubs
- [ ] Monitoring actif configuré

### Pendant la Migration
- [ ] Logs en temps réel surveillés
- [ ] Métriques de performance OK
- [ ] Pas d'erreurs critiques
- [ ] Rollback prêt si nécessaire

### Après la Migration
- [ ] Tous les clubs validés
- [ ] Performance acceptable
- [ ] Utilisateurs peuvent se connecter
- [ ] Données intègres
- [ ] Documentation mise à jour

## Support et Contacts

### Équipe Technique
- Chef de projet: [email]
- DBA: [email]
- DevOps: [email]

### Escalade
1. Niveau 1: Équipe de migration
2. Niveau 2: Architecte système
3. Niveau 3: CTO

### Resources
- Documentation: `/docs/multitenant/`
- Logs: `/var/log/martialcomp/migration/`
- Rapports: `/reports/migration/`

---

**Note**: Ce guide doit être adapté selon votre infrastructure spécifique et vos procédures opérationnelles.