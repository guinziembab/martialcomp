#!/usr/bin/env python3
"""
Diagnostic complet pour identifier pourquoi les coaches vont vers spectator
À exécuter avec: python manage.py shell
"""

def diagnostic_complet():
    """Diagnostic approfondi du système de routage"""
    
    print("🔍 DIAGNOSTIC COMPLET SYSTÈME ROUTAGE COACH")
    print("=" * 50)
    
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import User
    
    User = get_user_model()
    
    # 1. VÉRIFIER LES UTILISATEURS COACH1 ET COACH2
    print("👥 VÉRIFICATION UTILISATEURS")
    print("=" * 30)
    
    coaches = []
    for username in ['COACH1', 'COACH2']:
        try:
            coach = User.objects.get(username=username)
            coaches.append(coach)
            
            print(f"\n✅ {username} trouvé:")
            print(f"   • Email: {coach.email}")
            print(f"   • Active: {coach.is_active}")
            print(f"   • Type: {type(coach).__name__}")
            print(f"   • Module: {type(coach).__module__}")
            
            # Vérifier tous les attributs liés aux rôles
            role_attrs = []
            for attr in dir(coach):
                if 'role' in attr.lower() and not attr.startswith('_'):
                    try:
                        value = getattr(coach, attr)
                        if not callable(value):
                            role_attrs.append((attr, value))
                    except:
                        pass
            
            if role_attrs:
                print(f"   • Attributs rôle trouvés:")
                for attr, value in role_attrs:
                    print(f"     - {attr}: {value}")
            else:
                print(f"   ❌ Aucun attribut 'role' trouvé sur User")
            
            # Vérifier le profil
            profile = getattr(coach, 'profile', None)
            if profile:
                print(f"   • Profile: {profile} (type: {type(profile).__name__})")
                
                profile_role_attrs = []
                for attr in dir(profile):
                    if 'role' in attr.lower() and not attr.startswith('_'):
                        try:
                            value = getattr(profile, attr)
                            if not callable(value):
                                profile_role_attrs.append((attr, value))
                        except:
                            pass
                
                if profile_role_attrs:
                    print(f"   • Attributs rôle profil:")
                    for attr, value in profile_role_attrs:
                        print(f"     - {attr}: {value}")
                else:
                    print(f"   ❌ Aucun attribut 'role' trouvé sur Profile")
            else:
                print(f"   ❌ Pas de profil utilisateur")
                
        except User.DoesNotExist:
            print(f"❌ {username} non trouvé")
    
    # 2. TESTER LE DASHBOARD ROUTER EN DIRECT
    print(f"\n🔄 TEST DASHBOARD ROUTER")
    print("=" * 25)
    
    try:
        from competitions.views.dashboard_router import dashboard_router
        from django.test import RequestFactory
        
        factory = RequestFactory()
        
        for coach in coaches:
            print(f"\n🧪 Test routage pour {coach.username}:")
            
            # Créer une requête simulée
            request = factory.get('/competitions/dashboard/')
            request.user = coach
            
            # Appeler directement le router avec debug
            try:
                response = dashboard_router(request)
                
                if hasattr(response, 'url'):
                    print(f"   ✅ Redirection: {response.url}")
                    if '/coach/' in response.url:
                        print(f"   🎉 CORRECT: Dirigé vers coach dashboard")
                    else:
                        print(f"   ❌ INCORRECT: Dirigé vers {response.url}")
                else:
                    print(f"   ❌ Pas de redirection: {type(response)}")
                    
            except Exception as e:
                print(f"   ❌ Erreur router: {e}")
                import traceback
                traceback.print_exc()
                
    except ImportError as e:
        print(f"❌ Impossible d'importer dashboard_router: {e}")
    
    # 3. VÉRIFIER LA STRUCTURE DES MODÈLES
    print(f"\n📊 ANALYSE MODÈLES")
    print("=" * 20)
    
    print(f"Modèle User utilisé: {User}")
    print(f"Champs User:")
    
    # Obtenir les champs du modèle User
    for field in User._meta.get_fields():
        field_name = field.name
        field_type = type(field).__name__
        print(f"   • {field_name}: {field_type}")
    
    # 4. CHERCHER TOUS LES MODÈLES AVEC 'ROLE'
    print(f"\n🔍 RECHERCHE MODÈLES AVEC 'ROLE'")
    print("=" * 35)
    
    from django.apps import apps
    
    role_models = []
    for model in apps.get_models():
        model_name = f"{model._meta.app_label}.{model._meta.model_name}"
        
        # Vérifier si le modèle a des champs avec 'role'
        role_fields = []
        for field in model._meta.get_fields():
            if 'role' in field.name.lower():
                role_fields.append(field.name)
        
        if role_fields:
            role_models.append((model_name, role_fields))
            print(f"✅ {model_name}: {role_fields}")
    
    if not role_models:
        print("❌ Aucun modèle avec champ 'role' trouvé")
    
    # 5. VÉRIFIER LES SETTINGS DE ROUTAGE
    print(f"\n⚙️ VÉRIFICATION SETTINGS")
    print("=" * 25)
    
    from django.conf import settings
    
    auth_settings = [
        'LOGIN_REDIRECT_URL',
        'ACCOUNT_LOGIN_REDIRECT_URL', 
        'LOGOUT_REDIRECT_URL',
        'AUTH_USER_MODEL'
    ]
    
    for setting in auth_settings:
        value = getattr(settings, setting, 'NON DÉFINI')
        print(f"   • {setting}: {value}")
    
    # 6. TESTER LA CRÉATION D'UN PROFIL COACH
    print(f"\n🛠️ TEST CRÉATION PROFIL COACH")
    print("=" * 30)
    
    if coaches:
        coach = coaches[0]  # Utiliser COACH1 ou COACH2
        
        print(f"Test avec {coach.username}:")
        
        # Essayer de forcer le rôle de différentes manières
        methods_tested = []
        
        # Méthode 1: user.role direct
        try:
            coach.role = 'coach'
            coach.save()
            methods_tested.append("✅ user.role = 'coach' - SUCCESS")
        except Exception as e:
            methods_tested.append(f"❌ user.role = 'coach' - FAILED: {e}")
        
        # Méthode 2: Créer/modifier profil
        try:
            profile = getattr(coach, 'profile', None)
            if profile:
                profile.role = 'coach'
                profile.save()
                methods_tested.append("✅ profile.role = 'coach' - SUCCESS")
            else:
                # Essayer de créer un profil
                from django.apps import apps
                
                # Chercher un modèle Profile
                profile_created = False
                for model in apps.get_models():
                    if 'profile' in model._meta.model_name.lower():
                        try:
                            profile = model.objects.create(user=coach, role='coach')
                            methods_tested.append(f"✅ Profil créé avec {model._meta.label} - SUCCESS")
                            profile_created = True
                            break
                        except Exception as e:
                            continue
                
                if not profile_created:
                    methods_tested.append("❌ Impossible de créer un profil")
                    
        except Exception as e:
            methods_tested.append(f"❌ profile.role = 'coach' - FAILED: {e}")
        
        for method in methods_tested:
            print(f"   {method}")
    
    # 7. TEST FINAL APRÈS CORRECTIONS
    print(f"\n🎯 TEST FINAL ROUTAGE")
    print("=" * 20)
    
    if coaches:
        for coach in coaches:
            try:
                from competitions.views.dashboard_router import dashboard_router
                from django.test import RequestFactory
                
                factory = RequestFactory()
                request = factory.get('/competitions/dashboard/')
                request.user = coach
                
                print(f"\n🔬 Test final {coach.username}:")
                response = dashboard_router(request)
                
                if hasattr(response, 'url'):
                    print(f"   → {response.url}")
                    if '/coach/' in response.url:
                        print(f"   🎉 SUCCESS!")
                    else:
                        print(f"   ⚠️ Toujours dirigé vers: {response.url}")
                        
            except Exception as e:
                print(f"   ❌ Erreur: {e}")

if __name__ == "__main__":
    diagnostic_complet()
    
    print(f"\n" + "=" * 50)
    print("📋 DIAGNOSTIC TERMINÉ")
    print("Ce script a analysé tous les aspects du routage.")
    print("Regardez les résultats ci-dessus pour identifier le problème exact.")
    print("=" * 50)

# Exécuter automatiquement
diagnostic_complet()