#!/usr/bin/env python3
"""
Script de validation post-déploiement pour les sites d'organisations.
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from organizations.models import Organization
from multitenant.models import Tenant

def main():
    print("🧪 VALIDATION POST-DÉPLOIEMENT")
    print("=" * 35)
    print("🎯 Vérification que les sites d'organisations fonctionnent")
    print()
    
    try:
        # Test 1: Créer une organisation de test
        print("📋 Test 1: Création d'organisation avec signal automatique")
        
        user = User.objects.first()
        if not user:
            print("❌ Aucun utilisateur trouvé")
            return False
        
        # Compter les tenants avant
        tenant_count_before = Tenant.objects.count()
        
        # Créer une organisation
        org = Organization.objects.create(
            name="Test Validation Production",
            organization_type="CLUB",
            country="FR",
            created_by=user
        )
        
        # Vérifier qu'un tenant a été créé
        tenant_count_after = Tenant.objects.count()
        
        if tenant_count_after > tenant_count_before:
            print("✅ Signal automatique fonctionne: Tenant créé")
            
            # Trouver le tenant
            tenant = Tenant.objects.filter(name=org.name).first()
            if tenant:
                print(f"✅ Sous-domaine généré: {tenant.domain}")
            
            # Nettoyer
            org.delete()
            if tenant:
                tenant.delete()
            
            return True
        else:
            print("❌ ÉCHEC: Aucun tenant créé automatiquement")
            org.delete()
            return False
            
    except Exception as e:
        print(f"❌ ERREUR lors de la validation: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 VALIDATION RÉUSSIE!")
        print("✅ Les sites d'organisations automatiques sont fonctionnels")
    else:
        print("\n❌ VALIDATION ÉCHOUÉE")
        print("⚠️  Vérifiez les logs pour plus de détails")
    
    sys.exit(0 if success else 1)
