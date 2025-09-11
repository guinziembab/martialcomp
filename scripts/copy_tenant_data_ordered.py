#!/usr/bin/env python3
"""
Copier les données vers le schéma tenant dans le bon ordre
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

def copy_tenant_data_ordered():
    print("📋 COPIE ORDONNÉE DES DONNÉES TENANT")
    print("="*60)
    
    tenant = Tenant.objects.get(slug='fed-federation-test-fix')
    print(f"Tenant: {tenant.name}")
    print(f"Schéma: {tenant.schema_name}")
    
    # Ordre de copie respectant les dépendances
    copy_order = [
        # 1. Utilisateurs d'abord (pas de dépendances)
        ('auth_user', 'Utilisateurs'),
        
        # 2. Organisations (dépendent des utilisateurs)
        ('organizations_organization', 'Organisations'),
        
        # 3. Fédérations (dépendent des organisations)
        ('competitions_federation', 'Fédérations'),
        
        # 4. Disciplines (optionnel mais utile)
        ('competitions_discipline', 'Disciplines'),
    ]
    
    with connection.cursor() as cursor:
        for table, description in copy_order:
            print(f"\n📋 Copie de {description} ({table})...")
            
            try:
                # Vérifier existence des tables
                cursor.execute(f"""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema='public' AND table_name=%s
                """, [table])
                
                if cursor.fetchone()[0] == 0:
                    print(f"   ⚠️  Table {table} n'existe pas dans public")
                    continue
                
                cursor.execute(f"""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema=%s AND table_name=%s
                """, [tenant.schema_name, table])
                
                if cursor.fetchone()[0] == 0:
                    print(f"   ⚠️  Table {table} n'existe pas dans {tenant.schema_name}")
                    continue
                
                # Compter les données
                cursor.execute(f"SELECT COUNT(*) FROM public.{table}")
                source_count = cursor.fetchone()[0]
                
                cursor.execute(f"SELECT COUNT(*) FROM {tenant.schema_name}.{table}")
                tenant_count = cursor.fetchone()[0]
                
                print(f"   📊 Source: {source_count} | Tenant: {tenant_count}")
                
                if source_count > 0:
                    if tenant_count == 0:
                        # Copier avec gestion des contraintes
                        if table == 'auth_user':
                            # Pour les utilisateurs, copier seulement l'admin
                            cursor.execute(f"""
                                INSERT INTO {tenant.schema_name}.{table} 
                                SELECT * FROM public.{table} WHERE username = 'admin'
                                ON CONFLICT (username) DO NOTHING
                            """)
                        else:
                            # Pour les autres, copier tout
                            cursor.execute(f"""
                                INSERT INTO {tenant.schema_name}.{table} 
                                SELECT * FROM public.{table}
                                ON CONFLICT DO NOTHING
                            """)
                        
                        # Vérifier la copie
                        cursor.execute(f"SELECT COUNT(*) FROM {tenant.schema_name}.{table}")
                        new_count = cursor.fetchone()[0]
                        print(f"   ✅ Copié: {new_count} enregistrements")
                        
                    else:
                        print(f"   ✅ Données déjà présentes ({tenant_count})")
                else:
                    print(f"   ⚠️  Aucune donnée source à copier")
                    
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
                # Continuer avec la table suivante
    
    # Alternative: créer les données directement dans le schéma tenant
    print(f"\n🔧 CRÉATION DIRECTE DES DONNÉES...")
    
    # Basculer vers le schéma tenant
    set_schema(tenant.schema_name)
    
    try:
        from django.contrib.auth.models import User
        from organizations.models import Organization
        from competitions.models import Federation
        
        # 1. Créer ou récupérer l'utilisateur admin
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@martialcomp.com',
                'first_name': 'Admin',
                'last_name': 'MartialComp',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True
            }
        )
        print(f"   👤 Admin user: {'créé' if created else 'existant'}")
        
        # 2. Créer l'organisation
        org, created = Organization.objects.get_or_create(
            name='Federation Test Fix',
            defaults={
                'organization_type': 'national_federation',
                'description': 'Fédération de test pour MartialComp',
                'country': 'FR',
                'email': 'contact@federation-test-fix.com',
                'is_active': True,
                'created_by': admin_user
            }
        )
        print(f"   🏢 Organisation: {'créée' if created else 'existante'}")
        
        # 3. Créer la fédération
        fed, created = Federation.objects.get_or_create(
            slug='federation-test-fix',
            defaults={
                'name': 'Federation Test Fix',
                'description': 'Fédération de test avec template personnalisé',
                'contact_email': 'contact@federation-test-fix.com',
                'country': 'France',
                'is_active': True,
                'owner': admin_user,
                'organization': org
            }
        )
        print(f"   🏛️  Fédération: {'créée' if created else 'existante'}")
        
        print(f"\n✅ DONNÉES CRÉÉES AVEC SUCCÈS!")
        print(f"   - Organisation: {org.name} (ID: {org.id})")
        print(f"   - Fédération: {fed.name} (ID: {fed.id})")
        print(f"   - Lien: {fed.organization}")
        
    except Exception as e:
        print(f"   ❌ Erreur création directe: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Toujours revenir au schéma public
        set_schema('public')
    
    print("\n" + "="*60)
    print("✅ CRÉATION TERMINÉE")
    print("="*60)
    print("🧪 Testez maintenant: python3 test_corrected_tenant.py")

if __name__ == "__main__":
    copy_tenant_data_ordered()