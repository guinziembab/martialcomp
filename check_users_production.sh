#!/bin/bash
# Script pour vérifier l'état des utilisateurs en production

echo "=== VÉRIFICATION DES UTILISATEURS EN PRODUCTION ==="
echo ""

cd ~/martialcomp
source venv/bin/activate

python manage.py shell << 'PYEOF'
from django.contrib.auth import get_user_model
from apps.competitions.models import Federation, Club
from apps.core.models import UserProfile

User = get_user_model()

print("=== STATISTIQUES GLOBALES ===")
total_users = User.objects.count()
active_users = User.objects.filter(is_active=True).count()
staff_users = User.objects.filter(is_staff=True).count()
superusers = User.objects.filter(is_superuser=True).count()

print(f"Total utilisateurs: {total_users}")
print(f"Utilisateurs actifs: {active_users}")
print(f"Utilisateurs staff: {staff_users}")
print(f"Superutilisateurs: {superusers}")

# Compter par rôle
print(f"\n=== RÉPARTITION PAR RÔLE ===")
profiles = UserProfile.objects.all()
role_counts = {}
for profile in profiles:
    role = profile.role if hasattr(profile, 'role') else 'unknown'
    role_counts[role] = role_counts.get(role, 0) + 1

for role, count in sorted(role_counts.items()):
    print(f"{role}: {count}")

# Liste détaillée des utilisateurs
print(f"\n=== LISTE COMPLÈTE DES UTILISATEURS ===")
users = User.objects.all().order_by('username')
for u in users:
    profile_role = "N/A"
    if hasattr(u, 'profile') and u.profile:
        profile_role = u.profile.role if hasattr(u.profile, 'role') else "N/A"
    
    # Vérifier les fédérations et clubs
    fed_count = Federation.objects.filter(owner=u).count()
    club_count = Club.objects.filter(owner=u).count()
    
    status = "✓ ACTIF" if u.is_active else "✗ INACTIF"
    print(f"{status} | {u.username:25} | {u.email:35} | Rôle: {profile_role:20} | Feds: {fed_count} | Clubs: {club_count}")

# Cas spécifique FEDETEST1
print(f"\n=== DÉTAILS FEDETEST1 ===")
try:
    fedetest = User.objects.get(username='FEDETEST1')
    print(f"Username: {fedetest.username}")
    print(f"Email: {fedetest.email}")
    print(f"Actif: {fedetest.is_active}")
    print(f"Staff: {fedetest.is_staff}")
    print(f"Date création: {fedetest.date_joined}")
    print(f"Dernière connexion: {fedetest.last_login}")
    
    if hasattr(fedetest, 'profile') and fedetest.profile:
        print(f"Profil ID: {fedetest.profile.id}")
        print(f"Profil rôle: {fedetest.profile.role if hasattr(fedetest.profile, 'role') else 'N/A'}")
    else:
        print("⚠ ATTENTION: Pas de profil associé!")
    
    # Fédérations
    feds = Federation.objects.filter(owner=fedetest)
    print(f"\nFédérations possédées: {feds.count()}")
    for fed in feds:
        print(f"  - {fed.name} (ID: {fed.id})")
        print(f"    URL: https://martialcomp.com/fr/competitions/federations/{fed.id}/dashboard/")
    
    # Vérifier les administrateurs de fédération
    from apps.competitions.models import FederationAdministrator
    try:
        admin_roles = FederationAdministrator.objects.filter(user=fedetest)
        print(f"\nRôles administrateur fédération: {admin_roles.count()}")
        for role in admin_roles:
            print(f"  - Fédération: {role.federation.name}")
    except:
        print("\nPas de rôles administrateur trouvés (ou modèle non disponible)")
    
except User.DoesNotExist:
    print("❌ ERREUR CRITIQUE: Utilisateur FEDETEST1 non trouvé!")
    print("\nCréation suggérée:")
    print("python manage.py shell")
    print(">>> from django.contrib.auth import get_user_model")
    print(">>> User = get_user_model()")
    print(">>> user = User.objects.create_user('FEDETEST1', 'fedetest1@test.com', 'password')")
    print(">>> user.save()")

PYEOF

echo ""
echo "=== FIN DE LA VÉRIFICATION ==="
