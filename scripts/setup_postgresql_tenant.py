#!/usr/bin/env python3
"""
Configuration complète du tenant avec PostgreSQL
À exécuter APRÈS avoir configuré PostgreSQL
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import call_command
from django.contrib.auth.models import User
from competitions.models import Federation
from organizations.models import Organization
from multitenant.models import Tenant, Domain
from django.utils import timezone
from django.db import transaction

def setup_postgresql_tenant():
    print("🚀 CONFIGURATION TENANT POSTGRESQL")
    print("="*60)
    
    # Étape 1: Vérifier la connexion
    print("1️⃣ Vérification de la connexion PostgreSQL...")
    try:
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"   ✅ PostgreSQL connecté: {version[:50]}...")
        cursor.close()
    except Exception as e:
        print(f"   ❌ Erreur connexion: {e}")
        print("   💡 Exécutez d'abord: python3 check_postgresql.py")
        return False
    
    # Étape 2: Appliquer les migrations
    print("2️⃣ Application des migrations...")
    try:
        call_command('migrate', verbosity=1)
        print("   ✅ Migrations appliquées")
    except Exception as e:
        print(f"   ❌ Erreur migrations: {e}")
        return False
    
    # Étape 3: Créer le superuser
    print("3️⃣ Création du superuser...")
    try:
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@martialcomp.com',
                'is_staff': True,
                'is_superuser': True,
                'first_name': 'Admin',
                'last_name': 'MartialComp'
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            print("   ✅ Superuser créé (admin/admin123)")
        else:
            print("   ✅ Superuser existant")
    except Exception as e:
        print(f"   ❌ Erreur superuser: {e}")
        return False
    
    # Étape 4: Créer l'organisation
    print("4️⃣ Création de l'organisation...")
    try:
        with transaction.atomic():
            org, created = Organization.objects.get_or_create(
                name="Federation Test Fix",
                defaults={
                    'organization_type': 'national_federation',
                    'description': 'Fédération de test pour démonstration du template personnalisé',
                    'email': 'contact@federation-test.com',
                    'phone': '+33 1 23 45 67 89',
                    'website': 'https://federation-test.com',
                    'address': '123 Rue du Dojo',
                    'city': 'Paris',
                    'country': 'France',
                    'postal_code': '75001',
                    'is_active': True,
                    'created_by': admin_user
                }
            )
            print(f"   ✅ Organisation: {org.name}")
    except Exception as e:
        print(f"   ❌ Erreur organisation: {e}")
        return False
    
    # Étape 5: Créer la fédération
    print("5️⃣ Création de la fédération...")
    try:
        with transaction.atomic():
            federation, created = Federation.objects.get_or_create(
                slug='federation-test-fix',
                defaults={
                    'name': 'Federation Test Fix',
                    'description': 'Fédération de test pour démonstration du template personnalisé',
                    'contact_email': 'contact@federation-test.com',
                    'contact_phone': '+33 1 23 45 67 89',
                    'website': 'https://federation-test.com',
                    'address': '123 Rue du Dojo',
                    'city': 'Paris',
                    'country': 'France',
                    'postal_code': '75001',
                    'is_active': True,
                    'owner': admin_user,
                    'organization': org
                }
            )
            print(f"   ✅ Fédération: {federation.name}")
    except Exception as e:
        print(f"   ❌ Erreur fédération: {e}")
        return False
    
    # Étape 6: Créer le tenant
    print("6️⃣ Création du tenant...")
    try:
        with transaction.atomic():
            tenant, created = Tenant.objects.get_or_create(
                slug='fed-federation-test-fix',
                defaults={
                    'name': federation.name,
                    'schema_name': 'fed_federation_test_fix',
                    'domain': 'fed-federation-test-fix.localhost:8000',
                    'continent': 'europe_west',
                    'country': 'FR',
                    'timezone': 'Europe/Paris',
                    'currency': 'EUR',
                    'language': 'fr',
                    'subscription_plan': 'masters',
                    'is_active': True,
                    'activated_at': timezone.now(),
                    'owner': admin_user
                }
            )
            print(f"   ✅ Tenant: {tenant.name}")
    except Exception as e:
        print(f"   ❌ Erreur tenant: {e}")
        return False
    
    # Étape 7: Créer le domaine
    print("7️⃣ Création du domaine...")
    try:
        with transaction.atomic():
            domain, created = Domain.objects.get_or_create(
                domain='fed-federation-test-fix.localhost',
                defaults={
                    'tenant': tenant,
                    'is_primary': True
                }
            )
            print(f"   ✅ Domaine: {domain.domain}")
    except Exception as e:
        print(f"   ❌ Erreur domaine: {e}")
        return False
    
    print("\n" + "="*60)
    print("✅ CONFIGURATION POSTGRESQL TERMINÉE!")
    print("="*60)
    print("📋 Informations de connexion:")
    print(f"   👤 Admin: admin / admin123")
    print(f"   🌐 URL principale: http://localhost:8000")
    print(f"   🎯 URL tenant: http://fed-federation-test-fix.localhost:8000")
    print(f"   📊 Base: PostgreSQL (martialcomp_dev)")
    print()
    print("⚠️  CONFIGURATION HOSTS REQUISE:")
    print("   Fichier: C:\\Windows\\System32\\drivers\\etc\\hosts")
    print("   Ligne à ajouter: 127.0.0.1    fed-federation-test-fix.localhost")
    print()
    print("🚀 COMMANDES DE TEST:")
    print("   python manage.py runserver 0.0.0.0:8000")
    print("   python3 final_test.py")
    print("="*60)
    
    return True

if __name__ == "__main__":
    success = setup_postgresql_tenant()
    if not success:
        print("\n❌ Configuration échouée")
        print("💡 Vérifiez PostgreSQL avec: python3 check_postgresql.py")
        sys.exit(1)