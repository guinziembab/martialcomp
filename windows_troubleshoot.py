#!/usr/bin/env python3
"""
Script de résolution pour l'environnement Windows avec BACH_HAC
INSTRUCTIONS: Exécutez ce script sur votre machine Windows
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from apps.competitions.models.users import UserProfile
from apps.competitions.models import Practitioner

print("=== RÉSOLUTION PROBLÈME BACH_HAC SUR WINDOWS ===")

try:
    # 1. Vérifier l'utilisateur
    user = User.objects.get(username='ClaudiuG')
    print(f"✅ User trouvé: {user.username}")
    
    # 2. Vérifier et corriger le UserProfile
    profile = UserProfile.objects.get(user=user)
    print(f"Current UserProfile organisation: {profile.organization}")
    
    # 3. Trouver la bonne organisation via le practitioner
    practitioner = Practitioner.objects.filter(user=user).first()
    if practitioner and practitioner.organization:
        if profile.organization != practitioner.organization:
            print(f"🔧 CORRECTION: Mise à jour du UserProfile")
            print(f"   Ancienne organisation: {profile.organization}")
            print(f"   Nouvelle organisation: {practitioner.organization}")
            
            profile.organization = practitioner.organization
            profile.save()
            print("✅ UserProfile corrigé!")
        else:
            print("✅ UserProfile déjà correct")
    
    # 4. Nettoyer toutes les sessions actives pour forcer la reconnexion
    print("\n🧹 Nettoyage des sessions...")
    Session.objects.all().delete()
    print("✅ Toutes les sessions supprimées")
    
    # 5. Vérifications finales
    print(f"\n=== VÉRIFICATIONS FINALES ===")
    final_profile = UserProfile.objects.get(user=user)
    print(f"UserProfile final: {final_profile.organization}")
    
    practitioner_count = Practitioner.objects.filter(organization=final_profile.organization).count()
    print(f"Practitioners dans cette organisation: {practitioner_count}")
    
    print(f"\n=== ACTIONS REQUISES ===")
    print("1. 🔄 Redémarrez complètement votre serveur Django (Ctrl+C puis relancez)")
    print("2. 🌐 Videz le cache de votre navigateur (Ctrl+Shift+Del)")
    print("3. 🔐 Reconnectez-vous avec ClaudiuG / AQW123ok;")
    print("4. 🎯 Testez: http://127.0.0.1:8080/fr/competitions/club/practitioners/")
    print("\nSi le problème persiste, utilisez un navigateur privé/incognito.")
    
    print(f"\n✅ SCRIPT TERMINÉ AVEC SUCCÈS")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
    
    print(f"\n=== SOLUTION ALTERNATIVE ===")
    print("Si cette erreur persiste:")
    print("1. Vérifiez que vous êtes dans le bon dossier de projet")
    print("2. Vérifiez que la base de données est accessible")
    print("3. Contactez le support avec cette erreur")