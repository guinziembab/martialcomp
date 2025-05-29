"""
Migration simple et directe des clubs existants.
"""
from django.core.management.base import BaseCommand
from django.db import transaction, connection
from multitenant.models import Tenant, Domain, TenantFeature
from competitions.models import Club
import re


class Command(BaseCommand):
    help = 'Migration simple des clubs existants vers multi-tenant'
    
    def handle(self, *args, **options):
        clubs = Club.objects.all()
        self.stdout.write(f'Migration de {clubs.count()} clubs...')
        
        for club in clubs:
            try:
                with transaction.atomic():
                    # Créer le tenant
                    schema_name = self._generate_schema_name(club.name)
                    tenant = Tenant.objects.create(
                        name=club.name,
                        schema_name=schema_name,
                        domain=f"{schema_name}.martialcomp.com",
                        subdomain=schema_name,
                        continent='EUROPE',  # Par défaut
                        subscription_plan='masters',  # Plan moyen par défaut
                        is_active=True
                    )
                    
                    # Créer le domaine
                    Domain.objects.create(
                        tenant=tenant,
                        domain=tenant.domain,
                        is_primary=True
                    )
                    
                    # Créer le schéma PostgreSQL
                    with connection.cursor() as cursor:
                        cursor.execute(f'CREATE SCHEMA IF NOT EXISTS {schema_name}')
                    
                    # Ajouter les features de base
                    features = ['basic_competitions', 'practitioner_management', 'grade_management']
                    for feature in features:
                        TenantFeature.objects.create(
                            tenant=tenant,
                            feature_code=feature,
                            is_enabled=True
                        )
                    
                    # Marquer le club comme migré
                    club.tenant = tenant
                    club.save()
                    
                    self.stdout.write(self.style.SUCCESS(f'✓ {club.name} migré'))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Erreur pour {club.name}: {e}'))
    
    def _generate_schema_name(self, club_name):
        """Génère un nom de schéma valide."""
        clean_name = re.sub(r'[^a-z0-9]', '_', club_name.lower())
        clean_name = clean_name[:30]
        return clean_name