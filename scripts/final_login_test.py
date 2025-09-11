#!/usr/bin/env python3
"""
Test final pour identifier précisément le problème de connexion
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login

def final_login_test():
    print("🔍 TEST FINAL DE CONNEXION")
    print("="*60)
    
    # Préparer l'utilisateur
    user, created = User.objects.get_or_create(
        username='ClaudiuG',
        defaults={'email': 'claudiug@martialcomp.com', 'first_name': 'Claudiu'}
    )
    user.set_password('AQW123ok')
    user.save()
    print(f"✅ Utilisateur: {user.username}")
    
    # Test 1: Authentification Django directe
    print("\n1️⃣ Test authentification Django...")
    auth_user = authenticate(username='ClaudiuG', password='AQW123ok')
    print(f"   Authentification: {'✅ Succès' if auth_user else '❌ Échec'}")
    
    # Test 2: Login allauth étape par étape
    print("\n2️⃣ Test login allauth détaillé...")
    
    client = Client()
    
    # Étape A: Récupérer le formulaire de login
    response = client.get('/accounts/login/')
    print(f"   Page login status: {response.status_code}")
    
    if response.status_code == 200:
        # Étape B: Extraire le token CSRF
        csrf_token = client.cookies.get('csrftoken', {}).value if 'csrftoken' in client.cookies else ''
        print(f"   CSRF token: {'✅ Présent' if csrf_token else '❌ Manquant'}")
        
        # Étape C: Préparer les données de connexion
        login_data = {
            'login': 'ClaudiuG',  # allauth utilise 'login'
            'password': 'AQW123ok',
            'csrfmiddlewaretoken': csrf_token
        }
        
        # Étape D: Soumettre le formulaire SANS follow
        print("   📤 Soumission du formulaire...")
        response = client.post('/accounts/login/', data=login_data)
        print(f"   Status réponse: {response.status_code}")
        
        if response.status_code == 302:
            redirect_url = response.get('Location', '')
            print(f"   Redirection vers: {redirect_url}")
            
            # Étape E: Suivre la redirection manuellement
            print("   📍 Suivi de la redirection...")
            response = client.get(redirect_url)
            print(f"   Status final: {response.status_code}")
            
            # Étape F: Vérifier l'état de la session
            print("   🔍 Vérification session...")
            
            # Test simple : récupérer une page et vérifier le contenu
            test_response = client.get('/fr/')
            if test_response.status_code == 200:
                content = test_response.content.decode('utf-8')
                
                # Indicateurs simples d'état connecté
                connected_indicators = ['Se déconnecter', 'ClaudiuG', 'Bienvenue']
                disconnected_indicators = ['Se connecter', 'onclick="openModal(\'loginModal\')']
                
                connected_score = sum(1 for indicator in connected_indicators if indicator in content)
                disconnected_score = sum(1 for indicator in disconnected_indicators if indicator in content)
                
                print(f"   Indicateurs connecté: {connected_score}/3")
                print(f"   Indicateurs déconnecté: {disconnected_score}/2")
                
                if connected_score > disconnected_score:
                    print("   🎉 SUCCÈS! Utilisateur semble connecté")
                    return True
                else:
                    print("   ❌ ÉCHEC! Utilisateur semble déconnecté")
                    
                    # Debug : afficher un échantillon
                    print("   🔍 Échantillon de contenu:")
                    # Chercher la section d'auth spécifiquement
                    auth_start = content.find('<div class="auth-section">')
                    if auth_start != -1:
                        auth_end = content.find('</div>', auth_start + 300)
                        auth_section = content[auth_start:auth_end]
                        print(f"   {auth_section[:200]}...")
                    else:
                        print(f"   {content[:200]}...")
        else:
            print(f"   ❌ Pas de redirection, statut: {response.status_code}")
    
    # Test 3: Force login pour comparaison
    print("\n3️⃣ Test force login (comparaison)...")
    
    client2 = Client()
    client2.force_login(user)
    
    response = client2.get('/fr/')
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        
        if 'Se déconnecter' in content and 'ClaudiuG' in content:
            print("   ✅ Force login fonctionne parfaitement")
        else:
            print("   ❌ Même force login a des problèmes")
    
    return False

if __name__ == "__main__":
    success = final_login_test()
    
    print(f"\n{'='*60}")
    if success:
        print("✅ CONNEXION ALLAUTH FONCTIONNE!")
        print("🎯 Le problème était ailleurs")
    else:
        print("❌ CONNEXION ALLAUTH NE FONCTIONNE PAS")
        print("💡 Le problème est dans allauth ou la configuration")
        print("📝 Suggestions:")
        print("   - Vérifier les URLs allauth")
        print("   - Vérifier la configuration SITE_ID")
        print("   - Vérifier les backends d'authentification")
    print("="*60)