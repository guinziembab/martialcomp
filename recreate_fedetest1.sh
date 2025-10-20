#!/bin/bash
# Script pour recréer l'utilisateur FEDETEST1 s'il a disparu

echo "=== RECRÉATION DE L'UTILISATEUR FEDETEST1 ==="
echo ""

cd ~/martialcomp
source venv/bin/activate

python manage.py shell << 'PYEOF'
from django.contrib.auth import get_user_model
from apps.core.models import UserProfile
from apps.competitions.models import Federation

User = get_user_model()

print("1. Vérification de l'existence de FEDETEST1...")
try:
    user = User.objects.get(username='FEDETEST1')
    print(f"   ✓ Utilisateur trouvé: {user.username} ({user.email})")
    print(f"   Actif: {user.is_active}")
    print(f"   Email vérifié: {user.email_verified if hasattr(user, 'email_verified') else 'N/A'}")
    
    # Vérifier le profil
    if not hasattr(user, 'profile') or not user.profile:
        print("\n2. Création du profil manquant...")
        profile = UserProfile.objects.create(
            user=user,
            role='federation_admin'
        )
        print(f"   ✓ Profil créé avec rôle: federation_admin")
    else:
        print(f"\n2. Profil existant: {user.profile.role}")
        if user.profile.role != 'federation_admin':
            user.profile.role = 'federation_admin'
            user.profile.save()
            print(f"   ✓ Rôle mis à jour: federation_admin")
    
    # Vérifier si actif
    if not user.is_active:
        print("\n3. Réactivation de l'utilisateur...")
        user.is_active = True
        user.save()
        print("   ✓ Utilisateur réactivé")
    
    # Vérifier les fédérations
    print("\n4. Vérification des fédérations...")
    feds = Federation.objects.filter(owner=user)
    if feds.exists():
        print(f"   ✓ {feds.count()} fédération(s) trouvée(s):")
        for fed in feds:
            print(f"     - {fed.name} (ID: {fed.id})")
    else:
        print("   ⚠ Aucune fédération associée")
        print("   Recherche de la fédération ID 6...")
        try:
            fed6 = Federation.objects.get(id=6)
            print(f"   Fédération trouvée: {fed6.name}")
            print(f"   Propriétaire actuel: {fed6.owner.username if fed6.owner else 'Aucun'}")
            print("\n   Voulez-vous associer FEDETEST1 à cette fédération?")
            print("   Exécutez manuellement:")
            print(f"   >>> fed = Federation.objects.get(id=6)")
            print(f"   >>> user = User.objects.get(username='FEDETEST1')")
            print(f"   >>> fed.owner = user")
            print(f"   >>> fed.save()")
        except Federation.DoesNotExist:
            print("   ✗ Fédération ID 6 non trouvée")

except User.DoesNotExist:
    print("   ✗ Utilisateur FEDETEST1 non trouvé")
    print("\n2. Création de l'utilisateur FEDETEST1...")
    
    # Créer l'utilisateur
    user = User.objects.create_user(
        username='FEDETEST1',
        email='fedetest1@martialcomp.com',
        password='TestFede2025!',
        is_active=True
    )
    print(f"   ✓ Utilisateur créé: {user.username}")
    print(f"   Email: {user.email}")
    print(f"   Mot de passe: TestFede2025!")
    
    # Créer le profil
    print("\n3. Création du profil...")
    profile = UserProfile.objects.create(
        user=user,
        role='federation_admin'
    )
    print(f"   ✓ Profil créé avec rôle: federation_admin")
    
    # Associer à la fédération 6 si elle existe
    print("\n4. Association à la fédération ID 6...")
    try:
        fed = Federation.objects.get(id=6)
        fed.owner = user
        fed.save()
        print(f"   ✓ Associé à la fédération: {fed.name}")
        print(f"   URL dashboard: https://martialcomp.com/fr/competitions/federations/{fed.id}/dashboard/")
    except Federation.DoesNotExist:
        print("   ⚠ Fédération ID 6 non trouvée")
        print("   Liste des fédérations disponibles:")
        for f in Federation.objects.all()[:10]:
            print(f"     - ID {f.id}: {f.name} (Propriétaire: {f.owner.username if f.owner else 'Aucun'})")

print("\n=== RÉSUMÉ ===")
user = User.objects.get(username='FEDETEST1')
print(f"Username: {user.username}")
print(f"Email: {user.email}")
print(f"Actif: {user.is_active}")
print(f"Rôle profil: {user.profile.role if hasattr(user, 'profile') and user.profile else 'N/A'}")
feds = Federation.objects.filter(owner=user)
print(f"Fédérations: {feds.count()}")
for fed in feds:
    print(f"  - {fed.name} (ID: {fed.id})")
    print(f"    Dashboard: https://martialcomp.com/fr/competitions/federations/{fed.id}/dashboard/")

PYEOF

echo ""
echo "=== REDÉMARRAGE DE L'APPLICATION ==="
touch ~/martialcomp/passenger_wsgi.py
echo "✓ Application redémarrée"

echo ""
echo "=== INSTRUCTIONS DE CONNEXION ==="
echo "URL: https://martialcomp.com/fr/account/login/"
echo "Username: FEDETEST1"
echo "Email: fedetest1@martialcomp.com"
echo "Mot de passe: TestFede2025!"
echo ""
echo "Après connexion, accéder au dashboard:"
echo "https://martialcomp.com/fr/competitions/federations/6/dashboard/"
