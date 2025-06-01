# Stratégie de Migration Multi-Tenant MartialComp

## Vue d'Ensemble

Cette stratégie détaille le processus de migration des clubs existants vers la nouvelle architecture multi-tenant. La migration sera effectuée de manière progressive pour minimiser les interruptions de service.

## Phases de Migration

### Phase 1 : Analyse et Préparation (1 semaine)

1. **Inventaire des données existantes**
   - Identifier tous les clubs existants
   - Mapper les relations entre clubs, fédérations et compétitions
   - Identifier les dépendances critiques
   - Estimer la taille des données par club

2. **Création du plan de migration**
   - Ordre de migration des clubs (pilotes d'abord)
   - Fenêtres de maintenance
   - Plan de rollback en cas d'échec

3. **Préparation de l'infrastructure**
   - Configuration des schémas PostgreSQL
   - Préparation des domaines et certificats SSL
   - Tests de charge

### Phase 2 : Migration Pilote (1 semaine)

1. **Sélection des clubs pilotes**
   - 3-5 clubs de petite/moyenne taille
   - Clubs avec utilisateurs techniques disponibles
   - Données représentatives

2. **Processus de migration**
   - Création du tenant
   - Migration des données
   - Validation
   - Formation des utilisateurs

3. **Collecte de feedback**
   - Performance
   - Problèmes rencontrés
   - Ajustements nécessaires

### Phase 3 : Migration Progressive (2-3 semaines)

1. **Groupes de migration**
   - Groupe 1 : Clubs petits (< 50 pratiquants)
   - Groupe 2 : Clubs moyens (50-200 pratiquants)
   - Groupe 3 : Clubs grands (> 200 pratiquants)
   - Groupe 4 : Fédérations

2. **Calendrier**
   - Semaine 1 : Groupes 1 et 2
   - Semaine 2 : Groupe 3
   - Semaine 3 : Groupe 4 et finalisation

### Phase 4 : Finalisation (1 semaine)

1. **Validation complète**
   - Tests d'intégrité des données
   - Tests de performance
   - Validation utilisateur

2. **Nettoyage**
   - Archivage des anciennes données
   - Optimisation des schémas
   - Documentation finale

## Processus Technique de Migration

### 1. Script de Migration Principal

```python
# multitenant/migrations/migrate_existing_clubs.py

import logging
from django.db import transaction, connection
from multitenant.models import Tenant, Domain
from competitions.models import Club, Federation

logger = logging.getLogger(__name__)

class ClubMigrator:
    def __init__(self):
        self.migrated_clubs = []
        self.failed_clubs = []
    
    def migrate_all_clubs(self):
        """Migre tous les clubs vers l'architecture multi-tenant."""
        clubs = Club.objects.all().select_related('federations')
        
        for club in clubs:
            try:
                self.migrate_club(club)
            except Exception as e:
                logger.error(f"Échec migration club {club.id}: {e}")
                self.failed_clubs.append((club, str(e)))
        
        return self.generate_report()
    
    def migrate_club(self, club):
        """Migre un club spécifique."""
        with transaction.atomic():
            # 1. Créer le tenant
            tenant = self.create_tenant_for_club(club)
            
            # 2. Créer le schéma
            self.create_schema(tenant)
            
            # 3. Migrer les données
            self.migrate_club_data(club, tenant)
            
            # 4. Créer les utilisateurs administrateurs
            self.setup_admin_users(club, tenant)
            
            # 5. Configurer les features
            self.setup_features(tenant)
            
            # 6. Valider la migration
            self.validate_migration(club, tenant)
            
            self.migrated_clubs.append((club, tenant))
    
    def create_tenant_for_club(self, club):
        """Crée un tenant pour un club existant."""
        # Générer un nom de schéma unique
        schema_name = self.generate_schema_name(club)
        
        # Déterminer le continent basé sur le pays
        continent = self.determine_continent(club.country)
        
        # Créer le tenant
        tenant = Tenant.objects.create(
            name=club.name,
            schema_name=schema_name,
            domain=f"{schema_name}.martialcomp.com",
            subdomain=schema_name,
            continent=continent,
            subscription_plan='masters',  # Plan par défaut
            is_active=True,
            original_club_id=club.id
        )
        
        # Créer le domaine principal
        Domain.objects.create(
            tenant=tenant,
            domain=tenant.domain,
            is_primary=True
        )
        
        return tenant
    
    def create_schema(self, tenant):
        """Crée le schéma PostgreSQL pour le tenant."""
        with connection.cursor() as cursor:
            # Créer le schéma
            cursor.execute(f'CREATE SCHEMA IF NOT EXISTS {tenant.schema_name}')
            
            # Copier la structure depuis le schéma public
            cursor.execute(f"""
                SELECT clone_schema('public', '{tenant.schema_name}', FALSE);
            """)
    
    def migrate_club_data(self, club, tenant):
        """Migre les données du club vers le nouveau schéma."""
        with connection.cursor() as cursor:
            # Définir le schéma actuel
            cursor.execute(f'SET search_path TO {tenant.schema_name}')
            
            # Migrer les pratiquants
            self.migrate_practitioners(club, tenant, cursor)
            
            # Migrer les compétitions
            self.migrate_competitions(club, tenant, cursor)
            
            # Migrer les inscriptions
            self.migrate_registrations(club, tenant, cursor)
            
            # Migrer les grades
            self.migrate_grades(club, tenant, cursor)
    
    def generate_schema_name(self, club):
        """Génère un nom de schéma unique pour le club."""
        import re
        
        # Nettoyer le nom du club
        clean_name = re.sub(r'[^a-z0-9]', '_', club.name.lower())
        clean_name = clean_name[:30]  # Limiter la longueur
        
        # Assurer l'unicité
        base_name = clean_name
        counter = 1
        
        while Tenant.objects.filter(schema_name=clean_name).exists():
            clean_name = f"{base_name}_{counter}"
            counter += 1
        
        return clean_name
    
    def determine_continent(self, country):
        """Détermine le continent basé sur le pays."""
        continent_mapping = {
            'FR': 'EUROPE',
            'GB': 'EUROPE',
            'US': 'NORTH_AMERICA',
            'CA': 'NORTH_AMERICA',
            'BR': 'SOUTH_AMERICA',
            'AR': 'SOUTH_AMERICA',
            'CN': 'ASIA',
            'JP': 'ASIA',
            'AU': 'OCEANIA',
            'NZ': 'OCEANIA',
            'ZA': 'AFRICA',
            'NG': 'AFRICA',
            # Ajouter plus de mappings
        }
        
        return continent_mapping.get(country, 'EUROPE')  # Europe par défaut
```

### 2. Commande de Management

```python
# multitenant/management/commands/migrate_clubs_to_tenants.py

from django.core.management.base import BaseCommand
from multitenant.migrations.migrate_existing_clubs import ClubMigrator
from django.utils import timezone
import json

class Command(BaseCommand):
    help = 'Migre les clubs existants vers l'architecture multi-tenant'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--club-ids',
            nargs='+',
            type=int,
            help='IDs spécifiques des clubs à migrer'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simuler la migration sans modifier les données'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Nombre de clubs à migrer par batch'
        )
    
    def handle(self, *args, **options):
        migrator = ClubMigrator()
        
        self.stdout.write('Début de la migration des clubs...')
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('Mode DRY RUN activé'))
        
        start_time = timezone.now()
        
        if options['club_ids']:
            # Migrer des clubs spécifiques
            clubs = Club.objects.filter(id__in=options['club_ids'])
        else:
            # Migrer tous les clubs
            clubs = Club.objects.all()
        
        total_clubs = clubs.count()
        self.stdout.write(f'Nombre de clubs à migrer : {total_clubs}')
        
        # Migration par batch
        batch_size = options['batch_size']
        for i in range(0, total_clubs, batch_size):
            batch_clubs = clubs[i:i+batch_size]
            
            for club in batch_clubs:
                try:
                    if not options['dry_run']:
                        migrator.migrate_club(club)
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Club {club.name} migré')
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Échec pour {club.name}: {e}')
                    )
        
        # Générer le rapport
        end_time = timezone.now()
        duration = end_time - start_time
        
        report = {
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration': str(duration),
            'total_clubs': total_clubs,
            'migrated': len(migrator.migrated_clubs),
            'failed': len(migrator.failed_clubs),
            'failures': [
                {'club': club.name, 'error': error}
                for club, error in migrator.failed_clubs
            ]
        }
        
        # Sauvegarder le rapport
        report_file = f'migration_report_{start_time.strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.stdout.write(
            self.style.SUCCESS(f'\nRapport sauvegardé: {report_file}')
        )
```

### 3. Script de Validation

```python
# multitenant/migrations/validate_migration.py

class MigrationValidator:
    def __init__(self, tenant):
        self.tenant = tenant
        self.errors = []
        self.warnings = []
    
    def validate_all(self):
        """Valide tous les aspects de la migration."""
        self.validate_schema()
        self.validate_data_integrity()
        self.validate_permissions()
        self.validate_performance()
        
        return self.generate_validation_report()
    
    def validate_schema(self):
        """Valide que le schéma a été créé correctement."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name = %s
            """, [self.tenant.schema_name])
            
            if not cursor.fetchone():
                self.errors.append("Schéma non trouvé")
            
            # Vérifier les tables
            cursor.execute(f"""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s
            """, [self.tenant.schema_name])
            
            tables = cursor.fetchall()
            if len(tables) < 10:  # Nombre minimum de tables attendu
                self.warnings.append(f"Seulement {len(tables)} tables trouvées")
    
    def validate_data_integrity(self):
        """Valide l'intégrité des données migrées."""
        original_club = Club.objects.get(id=self.tenant.original_club_id)
        
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO {self.tenant.schema_name}')
            
            # Vérifier le nombre de pratiquants
            cursor.execute("SELECT COUNT(*) FROM competitions_practitioner")
            migrated_count = cursor.fetchone()[0]
            
            original_count = original_club.practitioners.count()
            if migrated_count != original_count:
                self.errors.append(
                    f"Nombre de pratiquants incorrect: "
                    f"{migrated_count} vs {original_count}"
                )
    
    def validate_permissions(self):
        """Valide les permissions et accès."""
        # Vérifier que les admins ont accès
        admin_users = User.objects.filter(
            is_staff=True,
            email__endswith=f"@{self.tenant.domain}"
        )
        
        if not admin_users.exists():
            self.warnings.append("Aucun administrateur trouvé pour ce tenant")
    
    def validate_performance(self):
        """Teste les performances du nouveau schéma."""
        import time
        
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO {self.tenant.schema_name}')
            
            # Test de performance simple
            start_time = time.time()
            cursor.execute("""
                SELECT COUNT(*) 
                FROM competitions_practitioner p
                JOIN competitions_registration r ON p.id = r.practitioner_id
            """)
            duration = time.time() - start_time
            
            if duration > 1.0:
                self.warnings.append(
                    f"Requête lente détectée: {duration:.2f}s"
                )
```

### 4. Script de Rollback

```python
# multitenant/migrations/rollback_migration.py

class MigrationRollback:
    def __init__(self, tenant):
        self.tenant = tenant
    
    def rollback(self):
        """Effectue un rollback complet de la migration."""
        try:
            # 1. Désactiver le tenant
            self.tenant.is_active = False
            self.tenant.save()
            
            # 2. Supprimer le schéma
            with connection.cursor() as cursor:
                cursor.execute(f'DROP SCHEMA IF EXISTS {self.tenant.schema_name} CASCADE')
            
            # 3. Supprimer les domaines
            self.tenant.domains.all().delete()
            
            # 4. Supprimer le tenant
            self.tenant.delete()
            
            # 5. Réactiver le club original si nécessaire
            if hasattr(self.tenant, 'original_club_id'):
                club = Club.objects.get(id=self.tenant.original_club_id)
                club.is_migrated = False
                club.save()
            
            return True, "Rollback effectué avec succès"
            
        except Exception as e:
            return False, f"Erreur lors du rollback: {e}"
```

## Checklist de Migration

### Avant la Migration

- [ ] Backup complet de la base de données
- [ ] Tests de charge sur l'infrastructure
- [ ] Communication aux utilisateurs
- [ ] Fenêtre de maintenance planifiée
- [ ] Équipe de support disponible

### Pendant la Migration

- [ ] Monitoring actif des performances
- [ ] Logs détaillés de chaque étape
- [ ] Validation après chaque batch
- [ ] Communication des progrès
- [ ] Tests utilisateurs pilotes

### Après la Migration

- [ ] Validation complète des données
- [ ] Tests de performance
- [ ] Formation des administrateurs
- [ ] Documentation mise à jour
- [ ] Support renforcé (1 semaine)

## Métriques de Succès

- **Taux de réussite** : > 99%
- **Temps d'arrêt par club** : < 10 minutes
- **Intégrité des données** : 100%
- **Performance** : Maintenue ou améliorée
- **Satisfaction utilisateur** : > 90%

## Plan de Communication

### Avant Migration
- Email 2 semaines avant
- FAQ et documentation
- Sessions de formation

### Pendant Migration
- Status en temps réel
- Support dédié
- Communication d'urgence si nécessaire

### Après Migration
- Confirmation de succès
- Guide des nouvelles fonctionnalités
- Collecte de feedback