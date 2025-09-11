#!/usr/bin/env python3
"""
Script d'analyse du dysfonctionnement du système d'authentification
"""
import os
import sys

# Répertoire de production
PROD_DIR = '/var/www/vhosts/martialcomp.com/httpdocs'
os.chdir(PROD_DIR)

def analyze_url_patterns():
    """Analyse les patterns URL actuels"""
    
    print("🔍 ANALYSE PATTERNS URL ACTUELS")
    print("===============================")
    
    print("❌ PROBLÈME IDENTIFIÉ:")
    print("   URL demandée: /competitions/dashboard/")
    print("   URLs disponibles selon Django:")
    print("   - /dashboard/ [name='dashboard']")
    print("   - /auth/")
    print("   - /login/ [name='login']")
    print("")
    
    print("🎯 PROBLÈME CRITIQUE:")
    print("   L'URL /dashboard/ existe MAIS quelque chose redirige")
    print("   toujours vers /competitions/dashboard/")
    print("")
    
    return True

def check_django_auth_views():
    """Vérifie les vues d'authentification Django par défaut"""
    
    print("🔍 ANALYSE VUES AUTHENTIFICATION")
    print("================================")
    
    # Lire config/urls.py pour voir la configuration d'auth
    try:
        with open('config/urls.py', 'r', encoding='utf-8') as f:
            config_content = f.read()
        
        print("📄 Configuration auth dans config/urls.py:")
        if 'auth_views.LoginView' in config_content:
            print("✅ LoginView Django trouvée")
            if 'redirect_authenticated_user=True' in config_content:
                print("⚠️ redirect_authenticated_user=True activé")
        
        if 'LOGIN_REDIRECT_URL' in config_content:
            print("✅ LOGIN_REDIRECT_URL configurée")
        else:
            print("❌ LOGIN_REDIRECT_URL non configurée dans urls.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lecture config/urls.py: {e}")
        return False

def check_settings_auth():
    """Vérifie les paramètres d'authentification dans settings.py"""
    
    print("\n🔍 ANALYSE PARAMÈTRES AUTH SETTINGS")
    print("===================================")
    
    try:
        with open('config/settings.py', 'r', encoding='utf-8') as f:
            settings_content = f.read()
        
        # Vérifier paramètres auth importants
        auth_settings = [
            'LOGIN_URL',
            'LOGIN_REDIRECT_URL', 
            'LOGOUT_REDIRECT_URL',
            'AUTHENTICATION_BACKENDS'
        ]
        
        print("📋 Paramètres d'authentification:")
        for setting in auth_settings:
            if setting in settings_content:
                # Extraire la valeur
                lines = settings_content.split('\n')
                for line in lines:
                    if line.strip().startswith(setting):
                        print(f"✅ {line.strip()}")
                        break
            else:
                print(f"❌ {setting} non défini")
        
        # Vérifier si LOGIN_REDIRECT_URL pointe vers /competitions/dashboard/
        if 'LOGIN_REDIRECT_URL' in settings_content:
            if '/competitions/dashboard/' in settings_content:
                print("")
                print("🚨 PROBLÈME TROUVÉ:")
                print("   LOGIN_REDIRECT_URL pointe vers '/competitions/dashboard/'")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lecture settings.py: {e}")
        return False

def check_allauth_configuration():
    """Vérifie la configuration Allauth"""
    
    print("\n🔍 ANALYSE CONFIGURATION ALLAUTH")
    print("================================")
    
    try:
        with open('config/settings.py', 'r', encoding='utf-8') as f:
            settings_content = f.read()
        
        if 'allauth' in settings_content:
            print("✅ Allauth installé")
            
            # Vérifier redirections Allauth
            allauth_settings = [
                'ACCOUNT_LOGIN_REDIRECT_URL',
                'ACCOUNT_LOGOUT_REDIRECT_URL',
                'ACCOUNT_SIGNUP_REDIRECT_URL'
            ]
            
            for setting in allauth_settings:
                if setting in settings_content:
                    lines = settings_content.split('\n')
                    for line in lines:
                        if line.strip().startswith(setting):
                            print(f"⚠️ {line.strip()}")
                            if '/competitions/dashboard/' in line:
                                print(f"🚨 {setting} pointe vers /competitions/dashboard/")
                            break
            
        else:
            print("ℹ️ Allauth non utilisé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur vérification Allauth: {e}")
        return False

def check_middleware_redirects():
    """Vérifie si un middleware cause les redirections"""
    
    print("\n🔍 ANALYSE MIDDLEWARE")
    print("====================")
    
    try:
        with open('config/settings.py', 'r', encoding='utf-8') as f:
            settings_content = f.read()
        
        # Chercher MIDDLEWARE
        if 'MIDDLEWARE' in settings_content:
            print("📋 Middleware configurés:")
            lines = settings_content.split('\n')
            in_middleware = False
            
            for line in lines:
                if 'MIDDLEWARE' in line and '=' in line:
                    in_middleware = True
                    continue
                if in_middleware:
                    if line.strip().startswith(']'):
                        break
                    if line.strip() and not line.strip().startswith('#'):
                        middleware = line.strip().strip("',\"")
                        print(f"   {middleware}")
                        
                        # Vérifier middleware suspects
                        if 'competitions' in middleware.lower():
                            print(f"⚠️ Middleware custom détecté: {middleware}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur analyse middleware: {e}")
        return False

def check_custom_auth_views():
    """Vérifie les vues d'auth personnalisées"""
    
    print("\n🔍 ANALYSE VUES AUTH PERSONNALISÉES")
    print("===================================")
    
    auth_file = 'competitions/views/auth.py'
    
    try:
        with open(auth_file, 'r', encoding='utf-8') as f:
            auth_content = f.read()
        
        print("📄 Vues dans competitions/views/auth.py:")
        
        # Chercher les redirections
        lines = auth_content.split('\n')
        for i, line in enumerate(lines, 1):
            if 'redirect(' in line or 'return redirect' in line:
                print(f"   Ligne {i}: {line.strip()}")
                if '/competitions/dashboard/' in line:
                    print(f"🚨 Redirection problématique trouvée ligne {i}")
        
        # Vérifier si les vues utilisent reverse()
        if 'reverse(' in auth_content:
            print("✅ Utilisation de reverse() détectée")
        else:
            print("⚠️ Pas d'utilisation de reverse() - URLs en dur?")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur analyse auth.py: {e}")
        return False

def identify_redirect_source():
    """Identifie la source des redirections incorrectes"""
    
    print("\n🎯 IDENTIFICATION SOURCE REDIRECTION")
    print("====================================")
    
    # Chercher /competitions/dashboard/ dans tous les fichiers Python
    search_files = [
        'config/settings.py',
        'config/urls.py', 
        'competitions/views/auth.py',
        'competitions/models/practitioners.py',
        'competitions/signals.py'
    ]
    
    found_sources = []
    
    for file_path in search_files:
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if '/competitions/dashboard/' in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        if '/competitions/dashboard/' in line:
                            print(f"🚨 {file_path}:{i}: {line.strip()}")
                            found_sources.append((file_path, i, line.strip()))
        except Exception as e:
            print(f"⚠️ Erreur lecture {file_path}: {e}")
    
    if found_sources:
        print(f"\n📊 {len(found_sources)} occurence(s) de '/competitions/dashboard/' trouvée(s)")
        return found_sources
    else:
        print("✅ Aucune occurrence de '/competitions/dashboard/' trouvée dans les fichiers Python")
        return []

def create_fix_plan():
    """Crée un plan de correction"""
    
    print("\n📋 PLAN DE CORRECTION")
    print("====================")
    
    print("🎯 ACTIONS NÉCESSAIRES:")
    print("1. Corriger LOGIN_REDIRECT_URL dans settings.py")
    print("2. Corriger redirections Allauth si configuré")
    print("3. Corriger redirections dans auth.py")
    print("4. Vérifier et corriger signals.py")
    print("5. Redémarrer Django")
    
    print("\n⚠️ URLS CIBLES CORRECTES:")
    print("   Login redirect: '/dashboard/' (sans /competitions/)")
    print("   Logout redirect: '/' (page d'accueil)")
    print("   Signup redirect: '/dashboard/'")
    
    return True

if __name__ == "__main__":
    print("🔍 ANALYSE DYSFONCTIONNEMENT AUTHENTIFICATION")
    print("=============================================")
    print(f"📂 Répertoire: {os.getcwd()}")
    
    print("\n❌ SYMPTÔMES OBSERVÉS:")
    print("   - Login/Signup ne fonctionne plus")
    print("   - Redirection vers /competitions/dashboard/ (404)")
    print("   - URL /dashboard/ existe mais inaccessible")
    
    # Analyse complète
    success1 = analyze_url_patterns()
    success2 = check_django_auth_views()
    success3 = check_settings_auth()
    success4 = check_allauth_configuration()
    success5 = check_middleware_redirects()
    success6 = check_custom_auth_views()
    sources = identify_redirect_source()
    success7 = create_fix_plan()
    
    print(f"\n📊 ANALYSE TERMINÉE:")
    print(f"   {'✅' if success1 else '❌'} Patterns URL analysés")
    print(f"   {'✅' if success2 else '❌'} Vues Django auth")
    print(f"   {'✅' if success3 else '❌'} Settings auth")
    print(f"   {'✅' if success4 else '❌'} Configuration Allauth")
    print(f"   {'✅' if success5 else '❌'} Middleware analysés")
    print(f"   {'✅' if success6 else '❌'} Vues auth personnalisées")
    print(f"   {'✅' if len(sources) > 0 else '❌'} Sources redirection identifiées")
    
    if sources:
        print("\n🚨 FICHIERS À CORRIGER:")
        for file_path, line_num, line_content in sources:
            print(f"   📝 {file_path}:{line_num}")
            print(f"      {line_content}")
    
    print("\n🎯 PROCHAINE ÉTAPE:")
    print("   Exécuter script de correction basé sur cette analyse")
    
    sys.exit(0)