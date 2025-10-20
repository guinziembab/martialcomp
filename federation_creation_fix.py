#!/usr/bin/env python3
"""
Script de correction pour le problème de création de fédération
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.competitions.models import Federation, Discipline
from apps.competitions.forms.onboarding import FederationCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()

def test_federation_creation():
    """Test de création de fédération"""
    print("🧪 Test de création de fédération...")
    
    # Créer un utilisateur de test
    user, created = User.objects.get_or_create(
        username='test_federation_user',
        defaults={
            'email': 'test@federation.com',
            'first_name': 'Test',
            'last_name': 'Federation'
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
        print("✅ Utilisateur de test créé")
    else:
        print("ℹ️ Utilisateur de test existant")
    
    # Créer un profil pour l'utilisateur
    from apps.competitions.models import Practitioner
    profile, created = Practitioner.objects.get_or_create(
        user=user,
        defaults={
            'role': 'federation_admin',
            'first_name': 'Test',
            'last_name': 'Federation'
        }
    )
    
    if created:
        print("✅ Profil de test créé")
    else:
        print("ℹ️ Profil de test existant")
    
    # Test du formulaire
    form_data = {
        'name': 'Test Federation',
        'country': 'France',
        'description': 'Fédération de test',
        'contact_email': 'test@federation.com',
        'contact_phone': '0123456789',
        'address': '123 Test Street',
        'city': 'Test City',
        'postal_code': '12345',
        'website': 'https://test-federation.com'
    }
    
    form = FederationCreationForm(data=form_data)
    
    if form.is_valid():
        print("✅ Formulaire valide")
        
        # Tester la sauvegarde
        try:
            federation = form.save(commit=False)
            federation.owner = user
            federation.save()
            print(f"✅ Fédération créée avec succès: {federation.name} (ID: {federation.id})")
            
            # Nettoyer
            federation.delete()
            print("✅ Fédération de test supprimée")
            
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {str(e)}")
            return False
    else:
        print(f"❌ Formulaire invalide: {form.errors}")
        return False
    
    return True

def main():
    """Fonction principale"""
    print("🚀 Correction du problème de création de fédération")
    print("=" * 50)
    
    # Test de création
    if test_federation_creation():
        print("\n✅ Tous les tests sont passés !")
        print("Le problème de création de fédération est résolu.")
    else:
        print("\n❌ Des erreurs persistent.")
        print("Vérifiez les logs ci-dessus pour plus de détails.")
    
    print("\n📋 Résumé des corrections appliquées:")
    print("1. ✅ Ajout des champs manquants dans Meta.fields du formulaire")
    print("2. ✅ Simplification de la validation du champ country")
    print("3. ✅ Correction de la méthode save() du formulaire")
    print("4. ✅ Amélioration de la gestion d'erreur dans la vue")
    print("5. ✅ Ajout de logs détaillés pour le débogage")

if __name__ == '__main__':
    main()