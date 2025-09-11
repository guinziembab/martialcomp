#!/usr/bin/env python3
"""
Copier les données essentielles vers le schéma tenant
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection, transaction
from multitenant.models import Tenant
from multitenant.schema_utils import set_schema

def copy_tenant_data():
    print("📋 COPIE DES DONNÉES TENANT")
    print("="*60)
    
    tenant = Tenant.objects.get(slug='fed-federation-test-fix')
    print(f"Tenant: {tenant.name}")
    print(f"Schéma: {tenant.schema_name}")
    
    # Tables essentielles à copier avec leurs données
    essential_tables = [
        'competitions_federation',
        'organizations_organization', 
        'competitions_discipline',
        'organizations_organization_disciplines',
        'competitions_federation_disciplines'
    ]
    
    with connection.cursor() as cursor:
        for table in essential_tables:
            print(f"\n📋 Copie de {table}...")
            
            try:
                # Vérifier si la table existe dans le schéma source
                cursor.execute(f"""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema='public' AND table_name=%s
                """, [table])
                
                if cursor.fetchone()[0] == 0:
                    print(f"   ⚠️  Table {table} n'existe pas dans public")
                    continue
                
                # Vérifier si la table existe dans le schéma tenant
                cursor.execute(f"""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema=%s AND table_name=%s
                """, [tenant.schema_name, table])
                
                if cursor.fetchone()[0] == 0:
                    print(f"   ⚠️  Table {table} n'existe pas dans {tenant.schema_name}")
                    continue
                
                # Compter les données source
                cursor.execute(f"SELECT COUNT(*) FROM public.{table}")
                source_count = cursor.fetchone()[0]
                
                # Compter les données tenant
                cursor.execute(f"SELECT COUNT(*) FROM {tenant.schema_name}.{table}")
                tenant_count = cursor.fetchone()[0]
                
                print(f"   📊 Source: {source_count} | Tenant: {tenant_count}")
                
                if source_count > 0 and tenant_count == 0:
                    # Copier les données
                    cursor.execute(f"""
                        INSERT INTO {tenant.schema_name}.{table} 
                        SELECT * FROM public.{table}
                        ON CONFLICT DO NOTHING
                    """)
                    
                    # Vérifier la copie
                    cursor.execute(f"SELECT COUNT(*) FROM {tenant.schema_name}.{table}")
                    new_count = cursor.fetchone()[0]
                    print(f"   ✅ Copié: {new_count} enregistrements")
                    
                elif tenant_count > 0:
                    print(f"   ✅ Données déjà présentes")
                else:
                    print(f"   ⚠️  Aucune donnée source à copier")
                    
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
    
    # Test final: vérifier les données dans le schéma tenant
    print("\n🧪 VÉRIFICATION FINALE...")
    
    # Basculer vers le schéma tenant
    set_schema(tenant.schema_name)
    
    try:
        from competitions.models import Federation
        from organizations.models import Organization
        
        feds = Federation.objects.all()
        orgs = Organization.objects.all()
        
        print(f"   ✅ Fédérations: {feds.count()}")
        print(f"   ✅ Organisations: {orgs.count()}")
        
        if feds.exists():
            fed = feds.first()
            print(f"   🏛️  Première fédération: {fed.name}")
            print(f"   🔗 Organisation liée: {fed.organization}")
            
        if orgs.exists():
            org = orgs.first()
            print(f"   🏢 Première organisation: {org.name}")
            print(f"   📊 Type: {org.organization_type}")
            
    except Exception as e:
        print(f"   ❌ Erreur d'accès: {e}")
    finally:
        # Toujours revenir au schéma public
        set_schema('public')
    
    print("\n" + "="*60)
    print("✅ COPIE TERMINÉE")
    print("="*60)
    print("🧪 Testez maintenant: python3 test_corrected_tenant.py")

if __name__ == "__main__":
    copy_tenant_data()