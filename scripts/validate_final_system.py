#!/usr/bin/env python3
"""
Script de validation finale du système complet
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def validate_final_system():
    """Validation finale complète du système"""
    
    print("🔍 VALIDATION FINALE DU SYSTÈME MARTIALCOMP")
    print("=" * 50)
    
    success_count = 0
    total_tests = 0
    
    try:
        # 1. Test des modèles
        print("\n1. 📋 VALIDATION DES MODÈLES")
        print("=" * 30)
        total_tests += 1
        
        try:
            from competitions.models.users import UserProfile
            from competitions.models.notifications import Notification, NotificationPreference
            from django.contrib.auth.models import User
            
            print("✅ Tous les modèles importés avec succès")
            
            # Test UserProfile
            admin_user = User.objects.get(username='admin')
            profile, created = UserProfile.objects.get_or_create(
                user=admin_user,
                defaults={'role': 'spectator', 'onboarding_completed': True}
            )
            
            print(f"✅ UserProfile testé: {profile}")
            print(f"   📋 Needs onboarding: {profile.needs_onboarding}")
            
            # Test Notification
            test_notifs = Notification.objects.filter(user=admin_user)
            print(f"✅ Notifications: {test_notifs.count()} trouvées")
            
            if test_notifs.exists():
                notif = test_notifs.first()
                print(f"   📋 Exemple: {notif.title}")
                print(f"   📋 Type: {notif.notification_type}")
                print(f"   📋 CSS: {notif.css_class}")
                print(f"   📋 Icon: {notif.icon_class}")
            
            success_count += 1
            
        except Exception as e:
            print(f"❌ Erreur modèles: {e}")
        
        # 2. Test de la base de données
        print("\n2. 🗄️ VALIDATION DE LA BASE DE DONNÉES")
        print("=" * 35)
        total_tests += 1
        
        try:
            from django.db import connection
            
            with connection.cursor() as cursor:
                # Vérifier la table notifications
                cursor.execute("PRAGMA table_info(competitions_notification)")
                columns = cursor.fetchall()
                
                required_columns = ['notification_type', 'priority', 'is_read', 'action_url']
                found_columns = [col[1] for col in columns]
                
                missing = [col for col in required_columns if col not in found_columns]
                
                if not missing:
                    print("✅ Structure de table correcte")
                    success_count += 1
                else:
                    print(f"❌ Colonnes manquantes: {missing}")
                
                # Compter les données
                cursor.execute("SELECT COUNT(*) FROM competitions_notification")
                notif_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM auth_user")
                user_count = cursor.fetchone()[0]
                
                print(f"📊 Utilisateurs: {user_count}")
                print(f"📊 Notifications: {notif_count}")
                
        except Exception as e:
            print(f"❌ Erreur base de données: {e}")
        
        # 3. Test des vues de notifications
        print("\n3. 🔧 VALIDATION DES VUES")
        print("=" * 25)
        total_tests += 1
        
        try:
            from competitions.views.notifications import (
                create_notification, notifications_list, 
                notifications_api_list, mark_notification_read
            )
            
            print("✅ Vues notifications importées")
            
            # Test de création de notification
            test_user = User.objects.get(username='admin')
            test_notif = create_notification(
                user=test_user,
                title="Test validation finale",
                message="Cette notification teste le système après la correction finale.",
                notification_type='info',
                priority='standard'
            )
            
            print(f"✅ Notification créée: {test_notif.id}")
            success_count += 1
            
        except Exception as e:
            print(f"❌ Erreur vues: {e}")
        
        # 4. Test des URLs
        print("\n4. 🔗 VALIDATION DES URLs")
        print("=" * 25)
        total_tests += 1
        
        try:
            from django.urls import reverse
            
            # URLs critiques
            critical_urls = [
                ('welcome', 'Page d\'accueil'),
                ('admin:index', 'Administration'),
            ]
            
            working = 0
            for url_name, description in critical_urls:
                try:
                    url = reverse(url_name)
                    print(f"   ✅ {description}: {url}")
                    working += 1
                except Exception as e:
                    print(f"   ❌ {description}: {e}")
            
            if working >= len(critical_urls):
                print("✅ URLs critiques fonctionnelles")
                success_count += 1
            else:
                print("❌ Certaines URLs ne fonctionnent pas")
                
        except Exception as e:
            print(f"❌ Erreur URLs: {e}")
        
        # 5. Test de l'onboarding
        print("\n5. 🎯 VALIDATION DE L'ONBOARDING")
        print("=" * 32)
        total_tests += 1
        
        try:
            from competitions.views.welcome import welcome, get_welcome_context
            
            print("✅ Vues d'onboarding importées")
            
            # Créer un utilisateur nécessitant onboarding
            test_user, created = User.objects.get_or_create(
                username='test_onboarding',
                defaults={'email': 'test@example.com', 'first_name': 'Test', 'last_name': 'User'}
            )
            
            if created:
                test_user.set_password('test123')
                test_user.save()
            
            # Créer un profil nécessitant onboarding
            test_profile, created = UserProfile.objects.get_or_create(
                user=test_user,
                defaults={'role': 'club_manager', 'onboarding_completed': False}
            )
            
            if test_profile.needs_onboarding:
                print("✅ Logique d'onboarding fonctionne")
                success_count += 1
            else:
                print("❌ Logique d'onboarding ne fonctionne pas")
                
        except Exception as e:
            print(f"❌ Erreur onboarding: {e}")
        
        # 6. Validation finale
        print("\n6. 📊 RÉSUMÉ FINAL")
        print("=" * 18)
        
        success_rate = (success_count / total_tests) * 100
        
        print(f"📋 Tests réussis: {success_count}/{total_tests}")
        print(f"📊 Taux de réussite: {success_rate:.1f}%")
        
        if success_count == total_tests:
            status = "SUCCESS"
            print("\n🎉 VALIDATION COMPLÈTE RÉUSSIE!")
            print("   Le système MartialComp est entièrement opérationnel")
            
            print("\n🎯 FONCTIONNALITÉS VALIDÉES:")
            print("   ✅ Système d'onboarding corrigé")
            print("   ✅ Système de notifications opérationnel")
            print("   ✅ Base de données cohérente")
            print("   ✅ Modèles Django fonctionnels")
            print("   ✅ URLs principales accessibles")
            
        elif success_count >= total_tests - 1:
            status = "PARTIAL_SUCCESS"
            print("\n✅ VALIDATION LARGEMENT RÉUSSIE")
            print("   Le système est fonctionnel avec des problèmes mineurs")
            
        else:
            status = "NEEDS_WORK"
            print("\n⚠️ VALIDATION PARTIELLEMENT RÉUSSIE")
            print("   Le système nécessite encore des corrections")
        
        print("\n🔐 COMPTES DE TEST DISPONIBLES:")
        print("   👤 admin / admin123 (Administrateur)")
        print("   👤 test_onboarding / test123 (Club Manager)")
        
        print("\n🌐 URLS DE TEST:")
        print("   🏠 http://localhost:8000/fr/ (Page d'accueil)")
        print("   🔧 http://localhost:8000/admin/ (Administration)")
        
        print("\n📋 PROCHAINES ÉTAPES:")
        if status == "SUCCESS":
            print("   🎊 Le système est prêt pour la production!")
            print("   📝 Créez des notifications pour les utilisateurs")
            print("   👥 Testez les processus d'onboarding")
            print("   📊 Surveillez les métriques d'utilisation")
        else:
            print("   🔧 Corrigez les problèmes identifiés")
            print("   🧪 Relancez la validation")
            print("   📝 Testez manuellement les fonctionnalités")
        
        return status == "SUCCESS"
        
    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE DE VALIDATION: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 DÉMARRAGE VALIDATION FINALE")
    
    success = validate_final_system()
    
    if success:
        print("\n🏆 VALIDATION FINALE RÉUSSIE AVEC SUCCÈS!")
        print("🎉 MARTIALCOMP EST MAINTENANT ENTIÈREMENT OPÉRATIONNEL!")
    else:
        print("\n🔧 VALIDATION FINALE NÉCESSITE DES CORRECTIONS")
    
    sys.exit(0 if success else 1)