#!/usr/bin/env python3
"""
Script de validation du déploiement en production
"""
import os
import sys
import django

# Configuration Django pour la production
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append('/var/www/vhosts/martialcomp.com/httpdocs')
django.setup()

def validate_production_deployment():
    """Valide le déploiement en production"""
    
    print("🔍 VALIDATION DU DÉPLOIEMENT PRODUCTION")
    print("=" * 50)
    
    validation_results = {
        'models': False,
        'database': False,
        'views': False,
        'urls': False,
        'admin_user': False,
        'notifications': False,
        'onboarding': False
    }
    
    try:
        # 1. Validation des modèles
        print("\n1. 📋 VALIDATION DES MODÈLES")
        print("=" * 30)
        
        try:
            from competitions.models.users import UserProfile
            from competitions.models.notifications import Notification, NotificationPreference
            
            print("✅ Modèles importés avec succès")
            
            # Test des propriétés
            test_profile = UserProfile()
            assert hasattr(test_profile, 'needs_onboarding'), "Propriété needs_onboarding manquante"
            assert hasattr(test_profile, 'complete_onboarding'), "Méthode complete_onboarding manquante"
            
            test_notification = Notification()
            assert hasattr(test_notification, 'css_class'), "Propriété css_class manquante"
            assert hasattr(test_notification, 'icon_class'), "Propriété icon_class manquante"
            
            print("✅ Propriétés des modèles validées")
            validation_results['models'] = True
            
        except Exception as e:
            print(f"❌ Erreur modèles: {e}")
        
        # 2. Validation de la base de données
        print("\n2. 🗄️ VALIDATION DE LA BASE DE DONNÉES")
        print("=" * 35)
        
        try:
            from django.db import connection
            
            with connection.cursor() as cursor:
                # Vérifier la table notifications
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='competitions_notification'")
                if cursor.fetchone():
                    print("✅ Table competitions_notification existe")
                    
                    # Vérifier la structure
                    cursor.execute("PRAGMA table_info(competitions_notification)")
                    columns = cursor.fetchall()
                    column_names = [col[1] for col in columns]
                    
                    required_columns = ['notification_type', 'priority', 'is_read', 'action_url']
                    missing = [col for col in required_columns if col not in column_names]
                    
                    if not missing:
                        print("✅ Structure de table correcte")
                        validation_results['database'] = True
                    else:
                        print(f"❌ Colonnes manquantes: {missing}")
                else:
                    print("❌ Table competitions_notification manquante")
                
        except Exception as e:
            print(f"❌ Erreur base de données: {e}")
        
        # 3. Validation des vues
        print("\n3. 🔧 VALIDATION DES VUES")
        print("=" * 25)
        
        try:
            from competitions.views.welcome import welcome, get_welcome_context
            from competitions.views.notifications import (
                notifications_list, create_notification
            )
            
            print("✅ Vues importées avec succès")
            validation_results['views'] = True
            
        except Exception as e:
            print(f"❌ Erreur vues: {e}")
        
        # 4. Validation des URLs
        print("\n4. 🔗 VALIDATION DES URLs")
        print("=" * 25)
        
        try:
            from django.urls import reverse
            
            test_urls = [
                ('welcome', 'Page d\'accueil'),
                ('admin:index', 'Administration'),
            ]
            
            working = 0
            for url_name, description in test_urls:
                try:
                    url = reverse(url_name)
                    print(f"   ✅ {description}: {url}")
                    working += 1
                except Exception as e:
                    print(f"   ❌ {description}: {e}")
            
            if working >= len(test_urls):
                validation_results['urls'] = True
                
        except Exception as e:
            print(f"❌ Erreur URLs: {e}")
        
        # 5. Validation de l'utilisateur admin
        print("\n5. 👤 VALIDATION UTILISATEUR ADMIN")
        print("=" * 32)
        
        try:
            from django.contrib.auth.models import User
            
            admin_user = User.objects.get(username='admin')
            admin_profile = UserProfile.objects.get(user=admin_user)
            
            print(f"✅ Utilisateur admin trouvé: {admin_user.email}")
            print(f"✅ Profil admin: {admin_profile.role}")
            print(f"✅ Onboarding terminé: {admin_profile.onboarding_completed}")
            
            validation_results['admin_user'] = True
            
        except User.DoesNotExist:
            print("❌ Utilisateur admin non trouvé")
        except UserProfile.DoesNotExist:
            print("❌ Profil admin non trouvé")
        except Exception as e:
            print(f"❌ Erreur admin: {e}")
        
        # 6. Validation des notifications
        print("\n6. 🔔 VALIDATION DES NOTIFICATIONS")
        print("=" * 32)
        
        try:
            # Compter les notifications
            total_notifications = Notification.objects.count()
            print(f"📊 Total notifications: {total_notifications}")
            
            # Test de création
            admin_user = User.objects.get(username='admin')
            test_notif = create_notification(
                user=admin_user,
                title="Test validation production",
                message="Test de validation après déploiement en production.",
                notification_type='success',
                priority='standard'
            )
            
            print(f"✅ Notification créée: {test_notif.id}")
            print(f"   📋 Type: {test_notif.notification_type}")
            print(f"   📋 CSS: {test_notif.css_class}")
            
            validation_results['notifications'] = True
            
        except Exception as e:
            print(f"❌ Erreur notifications: {e}")
        
        # 7. Validation de l'onboarding
        print("\n7. 🎯 VALIDATION ONBOARDING")
        print("=" * 27)
        
        try:
            # Compter les utilisateurs nécessitant onboarding
            users_need_onboarding = UserProfile.objects.filter(onboarding_completed=False).count()
            print(f"📊 Utilisateurs nécessitant onboarding: {users_need_onboarding}")
            
            # Test logique d'onboarding
            test_user, created = User.objects.get_or_create(
                username='test_validation',
                defaults={'email': 'test@validation.com'}
            )
            
            test_profile, created = UserProfile.objects.get_or_create(
                user=test_user,
                defaults={'role': 'club_manager', 'onboarding_completed': False}
            )
            
            if test_profile.needs_onboarding:
                print("✅ Logique needs_onboarding fonctionne")
                validation_results['onboarding'] = True
            
        except Exception as e:
            print(f"❌ Erreur onboarding: {e}")
        
        # 8. Résumé final
        print("\n8. 📊 RÉSUMÉ DE VALIDATION")
        print("=" * 25)
        
        total_checks = len(validation_results)
        passed_checks = sum(validation_results.values())
        success_rate = (passed_checks / total_checks) * 100
        
        print(f"\n📋 Vérifications réussies: {passed_checks}/{total_checks}")
        print(f"📊 Taux de réussite: {success_rate:.1f}%")
        
        for check, status in validation_results.items():
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {check.replace('_', ' ').title()}")
        
        # Déterminer le statut
        if passed_checks == total_checks:
            status = "SUCCESS"
            print("\n🎉 VALIDATION PRODUCTION RÉUSSIE!")
            print("   Le déploiement est entièrement fonctionnel")
        elif passed_checks >= total_checks - 1:
            status = "PARTIAL_SUCCESS"
            print("\n✅ VALIDATION LARGEMENT RÉUSSIE")
            print("   Le déploiement est fonctionnel avec des problèmes mineurs")
        else:
            status = "NEEDS_WORK"
            print("\n⚠️ VALIDATION PARTIELLEMENT RÉUSSIE")
            print("   Le déploiement nécessite des corrections")
        
        # Informations finales
        print("\n📋 INFORMATIONS PRODUCTION:")
        print("   🔐 Admin: admin / admin123")
        print("   🌐 Site: https://martialcomp.com/fr/")
        print("   🔧 Admin: https://martialcomp.com/admin/")
        
        if status == "SUCCESS":
            print("\n🎊 LE SYSTÈME EST PRÊT POUR LA PRODUCTION!")
            print("📝 Actions recommandées:")
            print("   - Créer des notifications pour les utilisateurs")
            print("   - Tester les processus d'onboarding")
            print("   - Monitorer les métriques d'utilisation")
        
        return status == "SUCCESS"
        
    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 DÉMARRAGE VALIDATION PRODUCTION")
    
    success = validate_production_deployment()
    
    if success:
        print("\n🏆 VALIDATION PRODUCTION RÉUSSIE!")
    else:
        print("\n🔧 VALIDATION PRODUCTION NÉCESSITE DES CORRECTIONS")
    
    sys.exit(0 if success else 1)