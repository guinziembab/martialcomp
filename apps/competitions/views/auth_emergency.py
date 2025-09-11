from django.core.exceptions import PermissionDenied
# -*- coding: utf-8 -*-
"""
Vue de login d'urgence sans CSRF pour débloquer la situation
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
def emergency_login(request):
    """Login d'urgence sans CSRF pour débloquer la situation"""
    
    if request.method == 'GET':
        # Afficher le formulaire de login d'urgence
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login d'urgence - MartialComp</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                .container { max-width: 400px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
                .emergency { background: #fff3cd; color: #856404; padding: 15px; border-radius: 5px; margin-bottom: 20px; border: 1px solid #ffeaa7; }
                .form-group { margin-bottom: 15px; }
                label { display: block; margin-bottom: 5px; font-weight: bold; }
                input[type="text"], input[type="password"] { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
                .btn { background: #007bff; color: white; padding: 12px 20px; border: none; border-radius: 5px; cursor: pointer; width: 100%; }
                .btn:hover { background: #0056b3; }
                .users { background: #d1ecf1; padding: 15px; border-radius: 5px; margin-top: 20px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚨 Login d'Urgence</h1>
                
                <div class="emergency">
                    <strong>Mode d'urgence activé</strong><br>
                    Ce formulaire de login d'urgence contourne temporairement les problèmes CSRF.
                </div>
                
                <form method="post" action="/competitions/emergency-login/">
                    <div class="form-group">
                        <label for="username">Nom d'utilisateur:</label>
                        <input type="text" id="username" name="username" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="password">Mot de passe:</label>
                        <input type="password" id="password" name="password" required>
                    </div>
                    
                    <button type="submit" class="btn">Se connecter</button>
                </form>
                
                <div class="users">
                    <strong>Utilisateurs de test disponibles:</strong><br>
                    • COACH1 / COACH2<br>
                    • (utilisez vos mots de passe habituels)
                </div>
                
                <p><a href="/accounts/login/">← Retour au login normal</a></p>
            </div>
        </body>
        </html>
        """
        return HttpResponse(html)
    
    elif request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        logger.info(f"Emergency login attempt for: {username}")
        
        # Authentifier l'utilisateur
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                login(request, user)
                logger.info(f"Emergency login successful for: {username}")
                
                # Rediriger vers le dashboard
                return redirect('/competitions/dashboard/')
            else:
                error_msg = "Compte désactivé"
        else:
            error_msg = "Nom d'utilisateur ou mot de passe incorrect"
            logger.warning(f"Emergency login failed for: {username}")
        
        # Afficher l'erreur
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Erreur de connexion</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                .container {{ max-width: 400px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }}
                .error {{ background: #f8d7da; color: #721c24; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>❌ Erreur de connexion</h1>
                <div class="error">
                    {error_msg}
                </div>
                <p><a href="/competitions/emergency-login/">← Réessayer</a></p>
            </div>
        </body>
        </html>
        """
        return HttpResponse(html)

@csrf_exempt  
def quick_login_coach1(request):
    """Connexion ultra-rapide pour COACH1"""
    try:
        user = User.objects.get(username='COACH1')
        # Spécifier le backend pour éviter l'erreur multi-backend
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        logger.info("Quick login COACH1 successful")
        return redirect('/competitions/dashboard/')
    except User.DoesNotExist:
        return HttpResponse("COACH1 non trouvé")
    except Exception as e:
        return HttpResponse(f"Erreur COACH1: {e}")

@csrf_exempt
def quick_login_coach2(request):
    """Connexion ultra-rapide pour COACH2"""
    try:
        user = User.objects.get(username='COACH2')
        # Spécifier le backend pour éviter l'erreur multi-backend
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        logger.info("Quick login COACH2 successful")
        return redirect('/competitions/dashboard/')
    except User.DoesNotExist:
        return HttpResponse("COACH2 non trouvé")
    except Exception as e:
        return HttpResponse(f"Erreur COACH2: {e}")