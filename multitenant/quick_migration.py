"""
Script direct pour migrer les 2 clubs existants.
À exécuter dans le shell Django: python manage.py shell < multitenant/quick_migration.py
"""
from django.db import transaction, connection
from multitenant.models import Tenant, Domain, TenantFeature
from competitions.models import Club
import re

def migrate_clubs():
    """Migration simple et directe des clubs."""
    clubs = Club.objects.all()
    print(f"Migration de {clubs.count()} clubs...")
    
    for club in clubs:
        try:
            with transaction.atomic():
                # Générer le nom du schéma
                schema_name = re.sub(r'[^a-z0-9]', '_', club.name.lower())[:30]
                
                # Vérifier si le tenant existe déjà
                if Tenant.objects.filter(schema_name=schema_name).exists():
                    print(f"⚠️  {club.name} déjà migré")
                    continue
                
                # Créer le tenant
                tenant = Tenant.objects.create(
                    name=club.name,
                    schema_name=schema_name,
                    domain=f"{schema_name}.martialcomp.com",
                    subdomain=schema_name,
                    continent='EUROPE',
                    subscription_plan='masters',
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
                    print(f"✓ Schéma créé: {schema_name}")
                
                # Ajouter les features
                features = [
                    'basic_competitions',
                    'advanced_competitions',
                    'practitioner_management',
                    'grade_management',
                    'financial_reports',
                    'custom_categories'
                ]
                
                for feature_code in features:
                    TenantFeature.objects.create(
                        tenant=tenant,
                        feature_code=feature_code,
                        is_enabled=True
                    )
                
                print(f"✓ {club.name} migré avec succès")
                print(f"  URL: https://{tenant.domain}")
                print(f"  Schéma: {schema_name}")
                print(f"  Features: {len(features)}")
                
        except Exception as e:
            print(f"✗ Erreur pour {club.name}: {e}")
    
    print("\nMigration terminée!")
    
    # Afficher le résumé
    tenants = Tenant.objects.all()
    print(f"\nTotal tenants: {tenants.count()}")
    for tenant in tenants:
        print(f"- {tenant.name}: {tenant.domain}")

# Exécuter la migration
if __name__ == '__main__':
    migrate_clubs()