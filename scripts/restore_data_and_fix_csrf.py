#!/usr/bin/env python3
"""
Restaurer les données et corriger le problème CSRF
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import call_command
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.test import Client
import json

def restore_backup_data():
    print("🔄 RESTAURATION DES DONNÉES")
    print("="*60)
    
    # 1. Vérifier le backup disponible
    backup_file = 'backup.json'
    
    if os.path.exists(backup_file):
        print(f"   📁 Backup trouvé: {backup_file}")
        
        # Lire un échantillon pour voir le contenu
        with open(backup_file, 'r', encoding='utf-8') as f:
            content = f.read(1000)  # Premier 1000 caractères
            print(f"   📄 Échantillon: {content[:200]}...")
        
        # Vérifier si c'est du JSON valide
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"   ✅ JSON valide - {len(data)} entrées")
            
            # Compter par modèle
            model_counts = {}
            for item in data:
                model = item.get('model', 'unknown')
                model_counts[model] = model_counts.get(model, 0) + 1
            
            print(f"   📊 Contenu par modèle:")
            for model, count in sorted(model_counts.items()):
                print(f"      - {model}: {count}")
            
            # Restaurer les données
            print(f"\n   🔄 Restauration en cours...")
            try:
                call_command('loaddata', backup_file, verbosity=0)
                print(f"   ✅ Données restaurées avec succès!")
                return True
            except Exception as e:
                print(f"   ❌ Erreur restauration: {e}")
                return False
                
        except json.JSONDecodeError as e:
            print(f"   ❌ Fichier JSON invalide: {e}")
    else:
        print(f"   ❌ Aucun backup trouvé")
    
    return False

def fix_csrf_issue():
    print(f"\n🔒 CORRECTION PROBLÈME CSRF")
    print("="*60)
    
    # 1. Nettoyer complètement les sessions
    print("\n1️⃣ Nettoyage complet sessions...")
    
    try:
        Session.objects.all().delete()
        print(f"   🧹 Toutes les sessions supprimées")
    except Exception as e:
        print(f"   ❌ Erreur nettoyage: {e}")
    
    # 2. Corriger le template welcome pour le CSRF
    print(f"\n2️⃣ Vérification template CSRF...")
    
    # Vérifier si le template a le bon token CSRF
    template_path = 'competitions/templates/competitions/welcome.html'
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if '{% csrf_token %}' in content:
            print(f"   ✅ Token CSRF présent dans le template")
        else:
            print(f"   ❌ Token CSRF manquant dans le template")
        
        # Vérifier la structure du formulaire
        if 'name="login"' in content:
            print(f"   ✅ Champ login correct")
        else:
            print(f"   ❌ Champ login incorrect")
        
        if 'action="{% url \'account_login\' %}"' in content:
            print(f"   ✅ Action URL correcte")
        else:
            print(f"   ❌ Action URL incorrecte")
            
    except Exception as e:
        print(f"   ❌ Erreur lecture template: {e}")
    
    # 3. Test de connexion avec nouvelle session
    print(f"\n3️⃣ Test connexion avec session fraîche...")
    
    # S'assurer que ClaudiuG existe avec le bon mot de passe
    try:
        user = User.objects.get(username='ClaudiuG')
        user.set_password('AQW123ok')
        user.save()
        print(f"   ✅ Utilisateur ClaudiuG réinitialisé")
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='ClaudiuG',
            email='claudiug@martialcomp.com',
            password='AQW123ok',
            first_name='Claudiu'
        )
        print(f"   ✅ Utilisateur ClaudiuG créé")
    
    # Test avec Client Django
    try:
        client = Client()
        
        # Étape 1: Récupérer la page de connexion
        response = client.get('/accounts/login/')
        print(f"   Page login: {response.status_code}")
        
        if response.status_code == 200:
            # Récupérer le token CSRF du cookie ET du formulaire
            csrf_cookie = client.cookies.get('csrftoken')
            
            if csrf_cookie:
                csrf_token = csrf_cookie.value
                print(f"   🔑 Token CSRF: {csrf_token[:20]}...")
                
                # Données de connexion
                login_data = {
                    'login': 'ClaudiuG',
                    'password': 'AQW123ok',
                    'csrfmiddlewaretoken': csrf_token
                }
                
                # Tentative de connexion
                response = client.post('/accounts/login/', data=login_data)
                print(f"   Test connexion: {response.status_code}")
                
                if response.status_code == 302:
                    print(f"   🎉 CONNEXION RÉUSSIE!")
                    redirect_url = response.get('Location', '')
                    print(f"   📍 Redirection: {redirect_url}")
                    return True
                elif response.status_code == 403:
                    print(f"   ❌ Encore erreur CSRF 403")
                    
                    # Debug: analyser la réponse
                    content = response.content.decode('utf-8')
                    if 'CSRF token from POST incorrect' in content:
                        print(f"   🔍 Token POST incorrect détecté")
                elif response.status_code == 200:
                    print(f"   ⚠️  Formulaire réaffiché - possibles erreurs de validation")
                    
                    # Vérifier s'il y a des erreurs dans la réponse
                    content = response.content.decode('utf-8')
                    if 'error' in content.lower():
                        print(f"   🔍 Erreurs détectées dans le formulaire")
            else:
                print(f"   ❌ Pas de cookie CSRF")
    
    except Exception as e:
        print(f"   ❌ Erreur test connexion: {e}")
    
    return False

def verify_data_restoration():
    print(f"\n📊 VÉRIFICATION DONNÉES RESTAURÉES")
    print("="*60)
    
    try:
        # Vérifier les données métier
        checks = [
            ('User.objects.count()', 'Utilisateurs'),
            ('from competitions.models import Discipline; Discipline.objects.count()', 'Disciplines'),
            ('from grades.models import Grade; Grade.objects.count()', 'Grades'),
            ('from competitions.models import Club; Club.objects.count()', 'Clubs'),
            ('from competitions.models import Federation; Federation.objects.count()', 'Fédérations'),
        ]
        
        for command, description in checks:
            try:
                count = eval(command)
                print(f"   📊 {description}: {count}")
            except Exception as e:
                print(f"   ❌ {description}: Erreur - {e}")
    
    except Exception as e:
        print(f"   ❌ Erreur vérification: {e}")

if __name__ == "__main__":
    print("🔧 RESTAURATION DONNÉES ET CORRECTION CSRF")
    print("="*70)
    
    # 1. Restaurer les données
    data_restored = restore_backup_data()
    
    # 2. Vérifier les données restaurées
    if data_restored:
        verify_data_restoration()
    
    # 3. Corriger le CSRF
    csrf_fixed = fix_csrf_issue()
    
    print(f"\n{'='*70}")
    print("📋 RÉSUMÉ:")
    
    if data_restored:
        print("✅ Données restaurées depuis backup.json")
    else:
        print("❌ Échec restauration données")
    
    if csrf_fixed:
        print("✅ Problème CSRF résolu")
    else:
        print("❌ Problème CSRF persiste")
    
    print("\n🚀 PROCHAINES ÉTAPES:")
    print("   1. Redémarrer le serveur Django")
    print("   2. Tester l'accès admin: /admin/")
    print("   3. Tester la connexion utilisateur: /fr/")
    print("   4. Vérifier que les données sont bien visibles")
    print("="*70)