#!/usr/bin/env python3
"""
Script de validation du déploiement onboarding et notifications
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append('/var/www/vhosts/martialcomp.com/httpdocs')
django.setup()

def validate_deployment():
    """Valide le déploiement des corrections d'onboarding et notifications"""
    
    print("🔍 VALIDATION DU DÉPLOIEMENT ONBOARDING & NOTIFICATIONS")
    print("=" * 60)
    
    validation_results = {
        'models': False,
        'views': False,
        'urls': False,
        'templates': False,
        'database': False,
        'users': False,
        'notifications': False
    }
    
    try:
        # 1. Validation des modèles
        print("\n1. 🔧 VALIDATION DES MODÈLES")
        print("=" * 30)
        
        try:
            from competitions.models.users import UserProfile
            from competitions.models.notifications import Notification, NotificationPreference
            
            print("   ✅ UserProfile importé avec succès")
            print("   ✅ Notification importé avec succès")
            print("   ✅ NotificationPreference importé avec succès")
            
            # Vérifier les propriétés du UserProfile
            test_profile = UserProfile()
            assert hasattr(test_profile, 'needs_onboarding'), "Propriété needs_onboarding manquante"
            assert hasattr(test_profile, 'complete_onboarding'), "Méthode complete_onboarding manquante"
            
            print("   ✅ Propriétés UserProfile validées")
            
            # Vérifier les propriétés de Notification
            test_notification = Notification()
            assert hasattr(test_notification, 'css_class'), "Propriété css_class manquante"
            assert hasattr(test_notification, 'icon_class'), "Propriété icon_class manquante"
            assert hasattr(test_notification, 'mark_as_read'), "Méthode mark_as_read manquante"
            
            print("   ✅ Propriétés Notification validées")
            validation_results['models'] = True
            
        except Exception as e:
            print(f"   ❌ Erreur modèles: {str(e)}")
        
        # 2. Validation des vues
        print("\n2. 🔧 VALIDATION DES VUES")
        print("=" * 25)
        
        try:
            from competitions.views.welcome import welcome, get_welcome_context
            from competitions.views.notifications import (
                notifications_list, notifications_api_list, 
                mark_notification_read, mark_all_read, create_notification
            )
            
            print("   ✅ Vue welcome importée")
            print("   ✅ Vues notifications importées")
            
            # Vérifier que create_notification est callable
            assert callable(create_notification), "create_notification n'est pas callable"
            print("   ✅ Fonction create_notification validée")
            
            validation_results['views'] = True
            
        except Exception as e:
            print(f"   ❌ Erreur vues: {str(e)}")
        
        # 3. Validation des URLs
        print("\n3. 🔧 VALIDATION DES URLs")
        print("=" * 25)
        
        try:
            from django.urls import reverse
            
            # Test des URLs principales
            test_urls = [
                ('welcome', 'Page d\'accueil'),
                ('admin:index', 'Administration'),
                ('competitions:notifications:list', 'Liste notifications'),
                ('competitions:notifications:api_list', 'API notifications'),
            ]
            
            working_urls = 0
            for url_name, description in test_urls:
                try:
                    url = reverse(url_name)
                    print(f"   ✅ {description}: {url}")
                    working_urls += 1
                except Exception as e:
                    print(f"   ❌ {description}: {str(e)}")
            
            if working_urls >= 3:
                validation_results['urls'] = True
                print(f"   📊 URLs validées: {working_urls}/{len(test_urls)}")
            
        except Exception as e:
            print(f"   ❌ Erreur URLs: {str(e)}")
        
        # 4. Validation de la base de données
        print("\n4. 🔧 VALIDATION DE LA BASE DE DONNÉES")
        print("=" * 35)
        
        try:
            from django.db import connection
            
            # Vérifier les tables
            with connection.cursor() as cursor:
                # Vérifier table notifications
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='competitions_notification'")
                if cursor.fetchone():
                    print("   ✅ Table competitions_notification existe")
                else:
                    print("   ❌ Table competitions_notification manquante")
                    raise Exception("Table notifications manquante")
                
                # Vérifier table préférences
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='competitions_notificationpreference'")
                if cursor.fetchone():
                    print("   ✅ Table competitions_notificationpreference existe")
                else:
                    print("   ❌ Table competitions_notificationpreference manquante")
                
                # Vérifier les colonnes de la table notifications
                cursor.execute("PRAGMA table_info(competitions_notification)")
                columns = [row[1] for row in cursor.fetchall()]
                required_columns = ['notification_type', 'priority', 'is_read', 'action_url']
                
                for col in required_columns:
                    if col in columns:
                        print(f"   ✅ Colonne {col} présente")
                    else:
                        print(f"   ❌ Colonne {col} manquante")
                        raise Exception(f"Colonne {col} manquante")
            
            validation_results['database'] = True
            
        except Exception as e:
            print(f"   ❌ Erreur base de données: {str(e)}")
        
        # 5. Validation des utilisateurs et profils
        print("\n5. 🔧 VALIDATION DES UTILISATEURS")
        print("=" * 30)
        
        try:
            from django.contrib.auth.models import User
            
            # Compter les utilisateurs
            total_users = User.objects.count()
            total_profiles = UserProfile.objects.count()
            
            print(f"   📊 Total utilisateurs: {total_users}")
            print(f"   📊 Total profils: {total_profiles}")
            
            # Vérifier l'admin
            try:
                admin_user = User.objects.get(username='admin')
                admin_profile = UserProfile.objects.get(user=admin_user)
                print("   ✅ Utilisateur admin trouvé avec profil")
                
                if admin_profile.onboarding_completed:
                    print("   ✅ Admin a terminé l'onboarding")
                else:
                    print("   ⚠️ Admin n'a pas terminé l'onboarding")
                
            except User.DoesNotExist:
                print("   ⚠️ Utilisateur admin non trouvé")
            except UserProfile.DoesNotExist:
                print("   ⚠️ Profil admin non trouvé")
            
            # Compter les utilisateurs nécessitant onboarding
            users_need_onboarding = UserProfile.objects.filter(onboarding_completed=False).count()
            print(f"   📊 Utilisateurs nécessitant onboarding: {users_need_onboarding}")
            
            validation_results['users'] = True
            
        except Exception as e:
            print(f"   ❌ Erreur utilisateurs: {str(e)}")
        
        # 6. Validation des notifications
        print("\n6. 🔧 VALIDATION DES NOTIFICATIONS")
        print("=" * 32)
        
        try:
            # Compter les notifications
            total_notifications = Notification.objects.count()
            unread_notifications = Notification.objects.filter(is_read=False).count()
            
            print(f"   📊 Total notifications: {total_notifications}")
            print(f"   📊 Notifications non lues: {unread_notifications}")
            
            # Tester la création d'une notification de test
            from competitions.views.notifications import create_notification
            
            if User.objects.filter(username='admin').exists():
                admin_user = User.objects.get(username='admin')
                test_notification = create_notification(
                    user=admin_user,
                    title="Test de validation",
                    message="Cette notification teste le système après déploiement.",
                    notification_type='success',
                    priority='standard'
                )
                print("   ✅ Création de notification de test réussie")
                
                # Tester les propriétés
                print(f"   📋 CSS class: {test_notification.css_class}")
                print(f"   📋 Icon class: {test_notification.icon_class}")
                
                # Tester mark as read
                test_notification.mark_as_read()
                if test_notification.is_read:
                    print("   ✅ Marquer comme lu fonctionne")
                else:
                    print("   ❌ Marquer comme lu ne fonctionne pas")
            
            validation_results['notifications'] = True
            
        except Exception as e:
            print(f"   ❌ Erreur notifications: {str(e)}")
        
        # 7. Validation des templates
        print("\n7. 🔧 VALIDATION DES TEMPLATES")
        print("=" * 28)
        
        try:
            import os
            
            # Vérifier les fichiers de template
            template_files = [
                'competitions/templates/base.html',
                'competitions/templates/competitions/notifications/list.html'
            ]
            
            for template_file in template_files:
                if os.path.exists(template_file):
                    print(f"   ✅ Template {template_file} existe")
                else:
                    print(f"   ❌ Template {template_file} manquant")
                    raise Exception(f"Template {template_file} manquant")
            
            # Vérifier que base.html contient le système de notifications
            with open('competitions/templates/base.html', 'r', encoding='utf-8') as f:
                base_content = f.read()
                
            if 'notifications-icon' in base_content:
                print("   ✅ Système de notifications présent dans base.html")
            else:
                print("   ❌ Système de notifications manquant dans base.html")
                raise Exception("Système de notifications manquant")
            
            if 'notification-badge' in base_content:
                print("   ✅ Badge de notifications présent")
            else:
                print("   ❌ Badge de notifications manquant")
            
            validation_results['templates'] = True
            
        except Exception as e:
            print(f"   ❌ Erreur templates: {str(e)}")
        
        # 8. Résumé de validation
        print("\n8. 📊 RÉSUMÉ DE VALIDATION")
        print("=" * 25)
        
        total_checks = len(validation_results)
        passed_checks = sum(validation_results.values())
        
        print(f"\n   📋 Vérifications réussies: {passed_checks}/{total_checks}")
        
        for check, status in validation_results.items():
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {check.capitalize()}")
        
        # Déterminer le statut global
        if passed_checks == total_checks:
            print("\n🎉 VALIDATION COMPLÈTE RÉUSSIE!")
            print("   Le déploiement des corrections est entièrement fonctionnel.")
            deployment_status = "SUCCESS"
        elif passed_checks >= total_checks - 2:
            print("\n✅ VALIDATION PARTIELLEMENT RÉUSSIE")
            print("   Le déploiement est fonctionnel avec quelques problèmes mineurs.")
            deployment_status = "PARTIAL_SUCCESS"
        else:
            print("\n❌ VALIDATION ÉCHOUÉE")
            print("   Le déploiement nécessite des corrections supplémentaires.")
            deployment_status = "FAILED"
        
        # 9. Recommandations
        print("\n9. 💡 RECOMMANDATIONS")
        print("=" * 18)
        
        if deployment_status == "SUCCESS":
            print("   🎯 Le système est prêt pour la production")
            print("   📋 Testez avec les comptes de test créés")
            print("   🔔 Créez des notifications pour les utilisateurs")
            print("   👥 Monitarez le processus d'onboarding")
        
        elif deployment_status == "PARTIAL_SUCCESS":
            print("   🔧 Corrigez les problèmes identifiés")
            print("   🧪 Relancez la validation après corrections")
            print("   📋 Testez manuellement les fonctionnalités")
        
        else:
            print("   🚨 Vérifiez les logs d'erreur")
            print("   🔄 Relancez le déploiement si nécessaire")
            print("   💾 Restaurez depuis la sauvegarde si critique")
        
        print("\n📋 URLS DE TEST RECOMMANDÉES:")
        print("   🏠 http://localhost:8000/fr/ (test onboarding)")
        print("   🔔 http://localhost:8000/fr/competitions/notifications/ (notifications)")
        print("   🔧 http://localhost:8000/admin/ (administration)")
        
        print(f"\nStatut final: {deployment_status}")
        return deployment_status == "SUCCESS"
        
    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE DE VALIDATION: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = validate_deployment()
    sys.exit(0 if success else 1)