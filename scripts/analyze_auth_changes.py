#!/usr/bin/env python3
"""
Analyser les changements qui ont pu affecter l'authentification
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.conf import settings
from django.db import connection

def analyze_auth_changes():
    print("🔍 ANALYSE DES CHANGEMENTS D'AUTHENTIFICATION")
    print("="*70)
    
    # 1. Vérifier la configuration des bases de données
    print("\n1️⃣ Configuration de base de données...")
    print(f"   Engine: {settings.DATABASES['default']['ENGINE']}")
    print(f"   Name: {settings.DATABASES['default']['NAME']}")
    print(f"   Host: {settings.DATABASES['default']['HOST']}")
    print(f"   Port: {settings.DATABASES['default']['PORT']}")
    
    # 2. Vérifier les tables d'authentification
    print(f"\n2️⃣ Tables d'authentification...")
    
    with connection.cursor() as cursor:
        # Vérifier si les tables existent
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('auth_user', 'django_session', 'auth_user_groups')
        """)
        tables = cursor.fetchall()
        
        print(f"   Tables trouvées: {[table[0] for table in tables]}")
        
        # Compter les utilisateurs
        try:
            cursor.execute("SELECT COUNT(*) FROM auth_user")
            user_count = cursor.fetchone()[0]
            print(f"   👥 Nombre d'utilisateurs: {user_count}")
            
            cursor.execute("SELECT COUNT(*) FROM auth_user WHERE is_superuser = true")
            admin_count = cursor.fetchone()[0]
            print(f"   👑 Nombre d'admins: {admin_count}")
            
            cursor.execute("SELECT COUNT(*) FROM django_session")
            session_count = cursor.fetchone()[0]
            print(f"   🔐 Sessions actives: {session_count}")
            
        except Exception as e:
            print(f"   ❌ Erreur accès tables: {e}")
    
    # 3. Lister tous les utilisateurs
    print(f"\n3️⃣ Liste des utilisateurs...")
    users = User.objects.all().order_by('date_joined')
    
    if users.exists():
        for user in users:
            status = []
            if user.is_superuser:
                status.append("ADMIN")
            if user.is_staff:
                status.append("STAFF")
            if not user.is_active:
                status.append("INACTIF")
            
            status_str = f"[{', '.join(status)}]" if status else ""
            print(f"   👤 {user.username} - {user.email} {status_str}")
            print(f"      📅 Créé: {user.date_joined}")
            if user.last_login:
                print(f"      🕐 Dernière connexion: {user.last_login}")
            else:
                print(f"      🕐 Jamais connecté")
    else:
        print(f"   ❌ Aucun utilisateur trouvé!")
    
    # 4. Vérifier la configuration d'authentification
    print(f"\n4️⃣ Configuration authentification...")
    print(f"   AUTH_USER_MODEL: {getattr(settings, 'AUTH_USER_MODEL', 'auth.User')}")
    print(f"   LOGIN_URL: {getattr(settings, 'LOGIN_URL', '/accounts/login/')}")
    print(f"   LOGIN_REDIRECT_URL: {getattr(settings, 'LOGIN_REDIRECT_URL', '/accounts/profile/')}")
    print(f"   LOGOUT_REDIRECT_URL: {getattr(settings, 'LOGOUT_REDIRECT_URL', None)}")
    
    print(f"\n   AUTHENTICATION_BACKENDS:")
    backends = getattr(settings, 'AUTHENTICATION_BACKENDS', [])
    for backend in backends:
        print(f"      - {backend}")
    
    # 5. Vérifier les middleware
    print(f"\n5️⃣ Middleware d'authentification...")
    middlewares = getattr(settings, 'MIDDLEWARE', [])
    auth_middlewares = [m for m in middlewares if 'auth' in m.lower() or 'session' in m.lower()]
    
    for middleware in auth_middlewares:
        print(f"   ✅ {middleware}")
    
    # 6. Test de création d'utilisateur simple
    print(f"\n6️⃣ Test création utilisateur...")
    
    test_username = f"test_user_{os.getpid()}"
    
    try:
        # Supprimer s'il existe
        User.objects.filter(username=test_username).delete()
        
        # Créer
        test_user = User.objects.create_user(
            username=test_username,
            email='test@martialcomp.com',
            password='test123'
        )
        print(f"   ✅ Utilisateur créé: {test_user.username}")
        
        # Tester l'authentification
        from django.contrib.auth import authenticate
        auth_test = authenticate(username=test_username, password='test123')
        
        if auth_test:
            print(f"   ✅ Authentification fonctionne")
        else:
            print(f"   ❌ Authentification échoue")
        
        # Nettoyer
        test_user.delete()
        print(f"   🧹 Utilisateur test supprimé")
        
    except Exception as e:
        print(f"   ❌ Erreur création utilisateur: {e}")
    
    return True

if __name__ == "__main__":
    analyze_auth_changes()
    
    print(f"\n{'='*70}")
    print("📋 RÉSUMÉ:")
    print("✅ L'utilisateur admin bguinziemba a été recréé")
    print("✅ Le template welcome.html a été restauré à la version récente")
    print("🔧 Les changements récents ont probablement:")
    print("   1. Supprimé la base de données ou les utilisateurs")
    print("   2. Modifié la configuration d'authentification")
    print("   3. Cassé les sessions existantes")
    print("\n🚀 ACTIONS RECOMMANDÉES:")
    print("   1. Redémarrer le serveur Django")
    print("   2. Tester l'accès admin: /admin/ avec bguinziemba / zBx43V22")
    print("   3. Tester l'authentification utilisateur sur /fr/")
    print("="*70)