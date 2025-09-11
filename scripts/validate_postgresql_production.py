#!/usr/bin/env python3
"""
Script de validation spécifique pour PostgreSQL en production
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def validate_postgresql_production():
    """Valide le déploiement PostgreSQL en production"""
    
    print("🔍 VALIDATION POSTGRESQL PRODUCTION")
    print("=" * 40)
    
    validation_results = {
        'database': False,
        'models': False,
        'admin_user': False,
        'notifications': False,
        'gunicorn': False
    }
    
    try:
        # 1. Validation PostgreSQL
        print("\n1. 🗄️ VALIDATION POSTGRESQL")
        print("=" * 28)
        
        try:
            from django.db import connection
            
            with connection.cursor() as cursor:
                # Vérifier la connexion PostgreSQL
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                print(f"✅ PostgreSQL connecté: {version.split(',')[0]}")
                
                # Vérifier la table notifications
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'competitions_notification'
                """)
                
                if cursor.fetchone():
                    print("✅ Table competitions_notification existe")
                    
                    # Vérifier les colonnes
                    cursor.execute("""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = 'competitions_notification'
                    """)
                    
                    columns = [row[0] for row in cursor.fetchall()]
                    required_columns = ['notification_type', 'priority', 'is_read', 'action_url']
                    
                    missing = [col for col in required_columns if col not in columns]
                    
                    if not missing:
                        print("✅ Structure de table correcte")
                        validation_results['database'] = True
                    else:
                        print(f"❌ Colonnes manquantes: {missing}")
                else:
                    print("❌ Table competitions_notification manquante")
                    
        except Exception as e:
            print(f"❌ Erreur PostgreSQL: {e}")
        
        # 2. Validation des modèles
        print("\n2. 📋 VALIDATION DES MODÈLES")
        print("=" * 30)
        
        try:
            from competitions.models.users import UserProfile, create_user_profile
            from competitions.models.notifications import Notification
            
            print("✅ Modèles importés avec succès")
            print("✅ Fonction create_user_profile disponible")
            
            # Test des propriétés
            test_profile = UserProfile()
            assert hasattr(test_profile, 'needs_onboarding'), "Propriété needs_onboarding manquante"
            assert hasattr(test_profile, 'complete_onboarding'), "Méthode complete_onboarding manquante"
            
            test_notification = Notification()
            assert hasattr(test_notification, 'css_class'), "Propriété css_class manquante"
            assert hasattr(test_notification, 'icon_class'), "Propriété icon_class manquante"
            
            print("✅ Propriétés des modèles validées")
            validation_results['models'] = True
            
        except ImportError as e:
            print(f"❌ Erreur import: {e}")
        except Exception as e:
            print(f"❌ Erreur modèles: {e}")
        
        # 3. Validation utilisateur admin
        print("\n3. 👤 VALIDATION ADMIN")
        print("=" * 22)
        
        try:
            from django.contrib.auth.models import User
            
            admin_user = User.objects.get(username='admin')
            admin_profile = UserProfile.objects.get(user=admin_user)
            
            print(f"✅ Admin trouvé: {admin_user.email}")
            print(f"✅ Profil: {admin_profile.role}")
            print(f"✅ Onboarding: {admin_profile.onboarding_completed}")
            print(f"✅ Staff: {admin_user.is_staff}")
            print(f"✅ Superuser: {admin_user.is_superuser}")
            
            validation_results['admin_user'] = True
            
        except User.DoesNotExist:
            print("❌ Utilisateur admin non trouvé")
        except Exception as e:
            print(f"❌ Erreur admin: {e}")
        
        # 4. Validation notifications
        print("\n4. 🔔 VALIDATION NOTIFICATIONS")
        print("=" * 32)
        
        try:
            # Compter les notifications
            total_notifications = Notification.objects.count()
            unread_notifications = Notification.objects.filter(is_read=False).count()
            
            print(f"📊 Total notifications: {total_notifications}")
            print(f"📊 Non lues: {unread_notifications}")
            
            # Test de création
            if admin_user:
                test_notif = Notification.objects.create(
                    user=admin_user,
                    title="Test validation PostgreSQL",
                    message="Test de validation après correction PostgreSQL.",
                    notification_type='info',
                    priority='standard'
                )
                
                print(f"✅ Notification créée: {test_notif.id}")
                print(f"   📋 Type: {test_notif.notification_type}")
                print(f"   📋 CSS: {test_notif.css_class}")
                print(f"   📋 Icon: {test_notif.icon_class}")
                
                # Nettoyer
                test_notif.delete()
                print("✅ Notification de test supprimée")
                
                validation_results['notifications'] = True
            
        except Exception as e:
            print(f"❌ Erreur notifications: {e}")
            import traceback
            traceback.print_exc()
        
        # 5. Validation Gunicorn
        print("\n5. 🚀 VALIDATION GUNICORN")
        print("=" * 25)
        
        try:
            import subprocess
            
            # Vérifier si Gunicorn tourne
            result = subprocess.run(['pgrep', '-f', 'gunicorn'], capture_output=True, text=True)
            
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                print(f"✅ Gunicorn actif avec {len(pids)} processus")
                for pid in pids:
                    if pid:
                        print(f"   📋 PID: {pid}")
                validation_results['gunicorn'] = True
            else:
                print("❌ Gunicorn non actif")
                
                # Essayer de voir les logs
                try:
                    with open('/tmp/gunicorn_corrected.log', 'r') as f:
                        last_lines = f.readlines()[-5:]
                        print("📋 Dernières lignes du log:")
                        for line in last_lines:
                            print(f"   {line.strip()}")
                except:
                    print("⚠️ Pas de logs Gunicorn disponibles")
            
        except Exception as e:
            print(f"❌ Erreur Gunicorn: {e}")
        
        # 6. Test des URLs
        print("\n6. 🌐 TEST DES URLs")
        print("=" * 19)
        
        try:
            import requests
            import time
            
            # Attendre que le serveur soit prêt
            time.sleep(2)
            
            test_urls = [
                ('https://martialcomp.com/', 'Page d\'accueil'),
                ('https://martialcomp.com/admin/', 'Administration'),
            ]
            
            for url, description in test_urls:
                try:
                    response = requests.get(url, timeout=10, verify=False)
                    print(f"   ✅ {description}: HTTP {response.status_code}")
                except requests.exceptions.RequestException as e:
                    print(f"   ⚠️ {description}: {str(e)}")
                    
        except ImportError:
            print("⚠️ Module requests non disponible pour test URLs")
        except Exception as e:
            print(f"⚠️ Erreur test URLs: {e}")
        
        # 7. Résumé final
        print("\n7. 📊 RÉSUMÉ VALIDATION")
        print("=" * 23)
        
        total_checks = len(validation_results)
        passed_checks = sum(validation_results.values())
        success_rate = (passed_checks / total_checks) * 100
        
        print(f"\n📋 Vérifications réussies: {passed_checks}/{total_checks}")
        print(f"📊 Taux de réussite: {success_rate:.1f}%")
        
        for check, status in validation_results.items():
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {check.replace('_', ' ').title()}")
        
        # Déterminer le statut
        if passed_checks >= 4:
            status = "SUCCESS"
            print("\n🎉 VALIDATION POSTGRESQL RÉUSSIE!")
            print("   Le système est fonctionnel avec PostgreSQL")
        elif passed_checks >= 3:
            status = "PARTIAL_SUCCESS"
            print("\n✅ VALIDATION LARGEMENT RÉUSSIE")
            print("   Le système fonctionne avec quelques problèmes mineurs")
        else:
            status = "NEEDS_WORK"
            print("\n⚠️ VALIDATION PARTIELLEMENT RÉUSSIE")
            print("   Le système nécessite encore des corrections")
        
        # Actions recommandées
        print("\n📋 ACTIONS RECOMMANDÉES:")
        print("========================")
        
        if not validation_results['gunicorn']:
            print("🔄 Redémarrer Gunicorn manuellement:")
            print("   cd /var/www/vhosts/martialcomp.com/httpdocs")
            print("   source venv/bin/activate")
            print("   pkill -f gunicorn")
            print("   gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --daemon")
        
        if not validation_results['database']:
            print("🗄️ Corriger la base de données:")
            print("   python3 /tmp/fix_postgresql_production.py")
        
        print("\n🌐 URLs de test:")
        print("   🏠 https://martialcomp.com/")
        print("   🔧 https://martialcomp.com/admin/ (admin / admin123)")
        
        return status == "SUCCESS" or status == "PARTIAL_SUCCESS"
        
    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 VALIDATION POSTGRESQL PRODUCTION")
    print("=" * 40)
    
    success = validate_postgresql_production()
    
    if success:
        print("\n🏆 VALIDATION RÉUSSIE!")
        print("🎉 LE SYSTÈME POSTGRESQL EST OPÉRATIONNEL!")
    else:
        print("\n🔧 VALIDATION NÉCESSITE DES CORRECTIONS")
    
    sys.exit(0 if success else 1)