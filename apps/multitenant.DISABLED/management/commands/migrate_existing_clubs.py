"""
Script de migration des clubs existants vers l'architecture multi-tenant.
"""
import logging
import re
from typing import Dict, List, Tuple, Optional
from django.db import transaction, connection
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q, Count

from apps.multitenant.models import Tenant, Domain, TenantFeature
from apps.competitions.models import (
    Club, Federation, Practitioner, Competition, 
    CompetitionRegistration, CompetitionCategory, Discipline
)
from apps.finances.models import Invoice, PaymentAttempt

logger = logging.getLogger('multitenant.migration')


class ClubMigrator:
    """Gestionnaire de migration des clubs vers multi-tenant."""
    
    CONTINENT_MAPPING = {
        'FR': 'EUROPE', 'GB': 'EUROPE', 'DE': 'EUROPE', 'IT': 'EUROPE',
        'ES': 'EUROPE', 'PT': 'EUROPE', 'BE': 'EUROPE', 'NL': 'EUROPE',
        'US': 'NORTH_AMERICA', 'CA': 'NORTH_AMERICA', 'MX': 'NORTH_AMERICA',
        'BR': 'SOUTH_AMERICA', 'AR': 'SOUTH_AMERICA', 'CL': 'SOUTH_AMERICA',
        'CN': 'ASIA', 'JP': 'ASIA', 'KR': 'ASIA', 'IN': 'ASIA',
        'AU': 'OCEANIA', 'NZ': 'OCEANIA',
        'ZA': 'AFRICA', 'NG': 'AFRICA', 'EG': 'AFRICA', 'KE': 'AFRICA',
    }
    
    DEFAULT_PLAN_MAPPING = {
        'small': 'essentials',    # < 50 pratiquants
        'medium': 'masters',      # 50-200 pratiquants
        'large': 'champion',      # > 200 pratiquants
    }
    
from apps.grades.models import Grade, PractitionerGrade, GradeRequirement
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.migrated_clubs: List[Tuple[Club, Tenant]] = []
        self.failed_clubs: List[Tuple[Club, str]] = []
        self.migration_stats: Dict[str, int] = {
            'total_clubs': 0,
            'migrated': 0,
            'failed': 0,
            'practitioners_migrated': 0,
            'competitions_migrated': 0,
            'registrations_migrated': 0,
        }
    
    def migrate_all_clubs(self, club_ids: Optional[List[int]] = None):
        """Migre tous les clubs ou une liste spécifique."""
        if club_ids:
            clubs = Club.objects.filter(id__in=club_ids)
        else:
            clubs = Club.objects.all()
        
        clubs = clubs.select_related('owner').prefetch_related(
            'federations', 'practitioners', 'competitions'
        )
        
        self.migration_stats['total_clubs'] = clubs.count()
        logger.info(f"Début de la migration de {clubs.count()} clubs")
        
        for club in clubs:
            try:
                logger.info(f"Migration du club: {club.name} (ID: {club.id})")
                self.migrate_club(club)
                self.migration_stats['migrated'] += 1
            except Exception as e:
                logger.error(f"Ã‰chec migration club {club.id}: {e}", exc_info=True)
                self.failed_clubs.append((club, str(e)))
                self.migration_stats['failed'] += 1
        
        return self.generate_report()
    
    @transaction.atomic
    def migrate_club(self, club: Club):
        """Migre un club spécifique vers un tenant."""
        if self.dry_run:
            logger.info(f"[DRY RUN] Migration du club {club.name}")
            return
        
        # 1. Créer le tenant
        tenant = self.create_tenant_for_club(club)
        logger.info(f"Tenant créé: {tenant.name} (schema: {tenant.schema_name})")
        
        # 2. Créer le schéma PostgreSQL
        self.create_schema(tenant)
        logger.info(f"Schéma créé: {tenant.schema_name}")
        
        # 3. Migrer les données
        self.migrate_club_data(club, tenant)
        
        # 4. Créer les utilisateurs administrateurs
        self.setup_admin_users(club, tenant)
        
        # 5. Configurer les features selon le plan
        self.setup_features(tenant)
        
        # 6. Valider la migration
        validator = MigrationValidator(tenant, club)
        validation_result = validator.validate_all()
        
        if validation_result['has_errors']:
            raise Exception(f"Validation échouée: {validation_result['errors']}")
        
        # 7. Marquer le club comme migré
        club.is_migrated = True
        club.tenant = tenant
        club.save()
        
        self.migrated_clubs.append((club, tenant))
        logger.info(f"Migration réussie pour {club.name}")
    
    def create_tenant_for_club(self, club: Club) -> Tenant:
        """Crée un tenant pour un club existant."""
        schema_name = self.generate_schema_name(club)
        continent = self.determine_continent(club)
        plan = self.determine_subscription_plan(club)
        
        tenant = Tenant.objects.create(
            name=club.name,
            schema_name=schema_name,
            domain=f"{schema_name}.martialcomp.com",
            subdomain=schema_name,
            continent=continent,
            subscription_plan=plan,
            payment_frequency='monthly',
            timezone=club.timezone or 'Europe/Paris',
            currency=club.currency or 'EUR',
            is_active=True,
            original_club_id=club.id,
            migration_date=timezone.now(),
        )
        
        # Créer le domaine principal
        Domain.objects.create(
            tenant=tenant,
            domain=tenant.domain,
            is_primary=True
        )
        
        # Si le club a un domaine personnalisé
        if hasattr(club, 'custom_domain') and club.custom_domain:
            Domain.objects.create(
                tenant=tenant,
                domain=club.custom_domain,
                is_primary=False
            )
        
        return tenant
    
    def create_schema(self, tenant: Tenant):
        """Crée et initialise le schéma PostgreSQL."""
        with connection.cursor() as cursor:
            # Créer le schéma
            cursor.execute(f'CREATE SCHEMA IF NOT EXISTS {tenant.schema_name}')
            
            # Définir le search_path
            cursor.execute(f'SET search_path TO {tenant.schema_name}')
            
            # Copier la structure depuis public
            cursor.execute(f"""
                SELECT duplicate_schema('public', '{tenant.schema_name}');
            """)
            
            # Créer les indexes nécessaires
            from apps.multitenant.db_optimization import IndexManager
            IndexManager.create_tenant_indexes(tenant.schema_name)
    
    def migrate_club_data(self, club: Club, tenant: Tenant):
        """Migre toutes les données du club vers le schéma tenant."""
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO {tenant.schema_name}')
            
            # 1. Migrer les données de base du club
            self.migrate_club_info(club, tenant, cursor)
            
            # 2. Migrer les pratiquants
            practitioners_migrated = self.migrate_practitioners(club, tenant, cursor)
            self.migration_stats['practitioners_migrated'] += practitioners_migrated
            
            # 3. Migrer les compétitions
            competitions_migrated = self.migrate_competitions(club, tenant, cursor)
            self.migration_stats['competitions_migrated'] += competitions_migrated
            
            # 4. Migrer les inscriptions
            registrations_migrated = self.migrate_registrations(club, tenant, cursor)
            self.migration_stats['registrations_migrated'] += registrations_migrated
            
            # 5. Migrer les grades
            self.migrate_grades(club, tenant, cursor)
            
            # 6. Migrer les données financières
            self.migrate_financial_data(club, tenant, cursor)
    
    def migrate_practitioners(self, club: Club, tenant: Tenant, cursor) -> int:
        """Migre les pratiquants du club."""
        practitioners = Practitioner.objects.filter(club=club)
        count = 0
        
        for practitioner in practitioners.iterator():
            cursor.execute("""
                INSERT INTO competitions_practitioner (
                    id, user_id, club_id, federation_id, 
                    license_number, date_of_birth, gender,
                    created_at, updated_at, is_active
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET updated_at = EXCLUDED.updated_at
            """, [
                practitioner.id,
                practitioner.user_id,
                practitioner.club_id,
                practitioner.federation_id,
                practitioner.license_number,
                practitioner.date_of_birth,
                practitioner.gender,
                practitioner.created_at,
                practitioner.updated_at,
                practitioner.is_active
            ])
            count += 1
        
        logger.info(f"Migré {count} pratiquants")
        return count
    
    def migrate_competitions(self, club: Club, tenant: Tenant, cursor) -> int:
        """Migre les compétitions du club."""
        competitions = Competition.objects.filter(
            Q(owner=club) | Q(participating_clubs=club)
        ).distinct()
        
        count = 0
        for competition in competitions.iterator():
            cursor.execute("""
                INSERT INTO competitions_competition (
                    id, name, date, end_date, location_id, 
                    category_id, owner_id, status, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET updated_at = EXCLUDED.updated_at
            """, [
                competition.id,
                competition.name,
                competition.date,
                competition.end_date,
                competition.location_id,
                competition.category_id,
                competition.owner_id,
                competition.status,
                competition.created_at,
                competition.updated_at
            ])
            count += 1
        
        logger.info(f"Migré {count} compétitions")
        return count
    
    def generate_schema_name(self, club: Club) -> str:
        """Génère un nom de schéma unique et valide."""
        # Nettoyer le nom du club
        clean_name = re.sub(r'[^a-z0-9]', '_', club.name.lower())
        clean_name = re.sub(r'_+', '_', clean_name)  # Remplacer multiples _
        clean_name = clean_name.strip('_')[:30]  # Limiter longueur
        
        # Assurer l'unicité
        base_name = clean_name
        counter = 1
        
        while Tenant.objects.filter(schema_name=clean_name).exists():
            clean_name = f"{base_name}_{counter}"
            counter += 1
        
        return clean_name
    
    def determine_continent(self, club: Club) -> str:
        """Détermine le continent basé sur le pays du club."""
        country = getattr(club, 'country', 'FR')  # France par défaut
        return self.CONTINENT_MAPPING.get(country, 'EUROPE')
    
    def determine_subscription_plan(self, club: Club) -> str:
        """Détermine le plan d'abonnement basé sur la taille du club."""
        practitioner_count = club.practitioners.count()
        
        if practitioner_count < 50:
            return 'essentials'
        elif practitioner_count < 200:
            return 'masters'
        else:
            return 'champion'
    
    def setup_admin_users(self, club: Club, tenant: Tenant):
        """Configure les utilisateurs administrateurs pour le tenant."""
        # L'owner du club devient super-admin du tenant
        if club.owner:
            club.owner.groups.add('tenant_superadmin')
            
            # Créer un compte email avec le domaine du tenant
            tenant_email = f"admin@{tenant.domain}"
            if not User.objects.filter(email=tenant_email).exists():
                admin_user = User.objects.create_user(
                    username=f"admin_{tenant.schema_name}",
                    email=tenant_email,
                    first_name=club.owner.first_name,
                    last_name=club.owner.last_name,
                    is_staff=True
                )
                admin_user.set_password('temp_password_to_change')
                admin_user.save()
    
    def setup_features(self, tenant: Tenant):
        """Configure les features selon le plan du tenant."""
        plan_features = {
            'essentials': [
                'basic_competitions',
                'practitioner_management',
                'basic_reports',
            ],
            'masters': [
                'basic_competitions',
                'advanced_competitions', 
                'practitioner_management',
                'grade_management',
                'financial_reports',
                'custom_categories',
            ],
            'champion': [
                'basic_competitions',
                'advanced_competitions',
                'practitioner_management', 
                'grade_management',
                'financial_reports',
                'custom_categories',
                'api_access',
                'white_label',
                'advanced_analytics',
            ],
        }
        
        features = plan_features.get(tenant.subscription_plan, [])
        
        for feature_code in features:
            TenantFeature.objects.create(
                tenant=tenant,
                feature_code=feature_code,
                is_enabled=True
            )
    
    def generate_report(self) -> Dict:
        """Génère un rapport détaillé de la migration."""
        return {
            'summary': self.migration_stats,
            'migrated_clubs': [
                {
                    'club_name': club.name,
                    'tenant_schema': tenant.schema_name,
                    'domain': tenant.domain,
                    'plan': tenant.subscription_plan,
                }
                for club, tenant in self.migrated_clubs
            ],
            'failed_clubs': [
                {
                    'club_name': club.name,
                    'error': error
                }
                for club, error in self.failed_clubs
            ],
            'timestamp': timezone.now().isoformat(),
        }


class MigrationValidator:
    """Valide la migration d'un club vers un tenant."""
    
    def __init__(self, tenant: Tenant, original_club: Club):
        self.tenant = tenant
        self.original_club = original_club
        self.errors = []
        self.warnings = []
    
    def validate_all(self) -> Dict:
        """Effectue toutes les validations."""
        self.validate_schema()
        self.validate_data_integrity()
        self.validate_permissions()
        self.validate_relationships()
        
        return {
            'tenant': self.tenant.name,
            'has_errors': len(self.errors) > 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'validated_at': timezone.now().isoformat(),
        }
    
    def validate_schema(self):
        """Valide l'existence et la structure du schéma."""
        with connection.cursor() as cursor:
            # Vérifier l'existence du schéma
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name = %s
            """, [self.tenant.schema_name])
            
            if not cursor.fetchone():
                self.errors.append(f"Schéma {self.tenant.schema_name} non trouvé")
                return
            
            # Vérifier les tables essentielles
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = %s
                AND table_name IN (
                    'competitions_practitioner',
                    'competitions_competition',
                    'competitions_registration'
                )
            """, [self.tenant.schema_name])
            
            table_count = cursor.fetchone()[0]
            if table_count < 3:
                self.errors.append("Tables essentielles manquantes")
    
    def validate_data_integrity(self):
        """Valide l'intégrité des données migrées."""
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO {self.tenant.schema_name}')
            
            # Vérifier le nombre de pratiquants
            cursor.execute("SELECT COUNT(*) FROM competitions_practitioner")
            migrated_count = cursor.fetchone()[0]
            
            original_count = self.original_club.practitioners.count()
            if migrated_count != original_count:
                self.errors.append(
                    f"Incohérence pratiquants: {migrated_count} migrés vs {original_count} originaux"
                )
            
            # Vérifier les compétitions
            cursor.execute("SELECT COUNT(*) FROM competitions_competition")
            comp_count = cursor.fetchone()[0]
            
            if comp_count == 0 and self.original_club.competitions.exists():
                self.warnings.append("Aucune compétition migrée")
    
    def validate_permissions(self):
        """Valide les permissions et accès administrateurs."""
        # Vérifier qu'au moins un admin existe
        admin_emails = [
            f"admin@{self.tenant.domain}",
            self.original_club.owner.email if self.original_club.owner else None
        ]
        
        admin_exists = User.objects.filter(
            email__in=admin_emails,
            is_staff=True
        ).exists()
        
        if not admin_exists:
            self.errors.append("Aucun administrateur configuré pour le tenant")
    
    def validate_relationships(self):
        """Valide les relations entre les entités."""
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO {self.tenant.schema_name}')
            
            # Vérifier l'intégrité référentielle
            cursor.execute("""
                SELECT COUNT(*) 
                FROM competitions_registration r
                LEFT JOIN competitions_practitioner p ON r.practitioner_id = p.id
                WHERE p.id IS NULL
            """)
            
            orphan_registrations = cursor.fetchone()[0]
            if orphan_registrations > 0:
                self.errors.append(f"{orphan_registrations} inscriptions orphelines détectées")

