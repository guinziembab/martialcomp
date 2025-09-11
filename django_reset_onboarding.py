
# Script Django pour reset des statuts onboarding
# À exécuter avec : python manage.py shell < reset_onboarding_status.py

import logging
from django.contrib.auth.models import User
from apps.competitions.models import UserProfile

logger = logging.getLogger(__name__)

def reset_all_onboarding_status():
    """Reset tous les statuts onboarding pour permettre une reconfiguration propre"""
    
    print("=" * 60)
    print("RESET DES STATUTS ONBOARDING")
    print("=" * 60)
    
    try:
        # 1. Récupérer tous les profils utilisateur
        profiles = UserProfile.objects.all()
        total_profiles = profiles.count()
        
        print(f"Nombre de profils trouvés : {total_profiles}")
        
        if total_profiles == 0:
            print("Aucun profil utilisateur trouvé.")
            return
        
        # 2. Reset des profils selon la logique métier
        practitioners_converted = 0
        regular_users = 0
        
        for profile in profiles:
            user = profile.user
            
            # Vérifier si l'utilisateur a un pratiquant associé
            has_practitioner = False
            try:
                if hasattr(user, 'practitioners') and user.practitioners.exists():
                    has_practitioner = True
                elif hasattr(user, 'practitioner') and user.practitioner:
                    has_practitioner = True
            except Exception:
                pass
            
            if has_practitioner:
                # Utilisateur pratiquant converti -> Onboarding terminé
                profile.role = 'participant'
                profile.onboarding_completed = True
                profile.onboarding_step = 'completed'
                profile.save()
                practitioners_converted += 1
                print(f"✅ Pratiquant converti : {user.username} -> role=participant, onboarding=completed")
            
            else:
                # Utilisateur normal -> Reset onboarding
                profile.onboarding_completed = False
                profile.onboarding_step = 'role'
                if not profile.role or profile.role == '':
                    profile.role = 'spectator'  # Rôle par défaut
                profile.save()
                regular_users += 1
                print(f"🔄 Utilisateur normal : {user.username} -> onboarding=reset")
        
        print("=" * 60)
        print("RÉSUMÉ DU RESET :")
        print(f"✅ Pratiquants convertis (onboarding terminé) : {practitioners_converted}")
        print(f"🔄 Utilisateurs normaux (onboarding reset) : {regular_users}")
        print(f"📊 Total traité : {practitioners_converted + regular_users}")
        print("=" * 60)
        
        # 3. Afficher les utilisateurs avec problèmes
        problematic_users = User.objects.filter(
            userprofile__isnull=True
        ) if hasattr(User, 'userprofile') else []
        
        if problematic_users.exists():
            print("⚠️  Utilisateurs sans profil détectés :")
            for user in problematic_users:
                print(f"   - {user.username} ({user.email})")
                # Créer un profil par défaut
                UserProfile.objects.create(
                    user=user,
                    role='spectator',
                    onboarding_completed=False,
                    onboarding_step='role'
                )
                print(f"   ✅ Profil créé pour {user.username}")
        
        print("\n🎉 Reset des statuts onboarding terminé avec succès !")
        
    except Exception as e:
        print(f"❌ Erreur lors du reset : {str(e)}")
        logger.error(f"Erreur reset onboarding: {e}", exc_info=True)

# Exécuter le reset
reset_all_onboarding_status()
