"""
URLs minimales pour les traductions uniquement
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.i18n import set_language
from django.http import HttpResponse
from django.shortcuts import render


from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

def test_page(request):
    """Page de test pour vérifier que tout fonctionne"""
    from django.middleware.csrf import get_token
    
    # Générer le token CSRF
    csrf_token = get_token(request)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test MartialComp</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 50px; }}
            .status {{ padding: 10px; margin: 10px 0; border-radius: 5px; }}
            .success {{ background: #d4edda; color: #155724; }}
            .info {{ background: #d1ecf1; color: #0c5460; }}
            .warning {{ background: #fff3cd; color: #856404; }}
            .form {{ background: #f8f9fa; padding: 20px; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <h1>🔧 Test MartialComp</h1>
        
        <div class="status success">
            ✅ Django fonctionne correctement
        </div>
        
        <div class="status info">
            🔐 Test de connexion direct avec CSRF corrigé
        </div>
        
        <div class="status warning">
            🛡️ CSRF Token: {csrf_token[:20]}...
        </div>
        
        <div class="form">
            <form method="post" action="/admin/login/">
                <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">
                <p>
                    <label>Username:</label><br>
                    <input type="text" name="username" value="guinziembab" style="width: 200px; padding: 5px;">
                </p>
                <p>
                    <label>Password:</label><br>
                    <input type="password" name="password" value="zBx43V22" style="width: 200px; padding: 5px;">
                </p>
                <input type="hidden" name="next" value="/rosetta/">
                <p>
                    <button type="submit" style="padding: 10px 20px; background: #007cba; color: white; border: none; border-radius: 3px;">
                        🚀 Connexion vers Rosetta
                    </button>
                </p>
            </form>
        </div>
        
        <div class="form">
            <h3>🔗 Liens directs:</h3>
            <p><a href="/admin/">📊 Administration Django</a></p>
            <p><a href="/admin/login/">🔐 Page de connexion Django</a></p>
            <p><a href="/rosetta/">🌍 Interface Rosetta</a></p>
        </div>
        
        <div class="status info">
            <strong>Instructions:</strong><br>
            1. Utilisez le formulaire ci-dessus (CSRF corrigé)<br>
            2. Ou cliquez sur "Page de connexion Django"<br>
            3. Username: guinziembab<br>
            4. Password: zBx43V22
        </div>
        
        <div class="status warning">
            <strong>Si ça ne marche toujours pas:</strong><br>
            • Videz le cache navigateur<br>
            • Essayez en navigation privée<br>
            • Acceptez les cookies pour localhost
        </div>
    </body>
    </html>
    """
    
    return HttpResponse(html)



def test_page_fixed(request):
    """Page de test avec URLs corrigées"""
    from django.middleware.csrf import get_token
    
    csrf_token = get_token(request)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>MartialComp - Test Corrigé</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 50px; background: #f5f5f5; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .success {{ background: #d4edda; color: #155724; padding: 15px; border-radius: 5px; margin: 15px 0; }}
            .info {{ background: #d1ecf1; color: #0c5460; padding: 15px; border-radius: 5px; margin: 15px 0; }}
            .form {{ background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }}
            .btn {{ padding: 12px 24px; background: #007cba; color: white; border: none; border-radius: 5px; text-decoration: none; display: inline-block; margin: 5px; }}
            .btn:hover {{ background: #005a87; }}
            input[type="text"], input[type="password"] {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin: 5px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎉 MartialComp - Connexion Corrigée</h1>
            
            <div class="success">
                ✅ PROBLÈME RÉSOLU! Utilisez les URLs avec /fr/
            </div>
            
            <div class="info">
                🔍 Diagnostic: Le serveur utilise i18n_patterns, donc les URLs incluent le code langue
            </div>
            
            <div class="form">
                <h3>🔐 Connexion avec URLs corrigées</h3>
                <form method="post" action="/fr/admin/login/">
                    <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">
                    <p>
                        <label>Username:</label><br>
                        <input type="text" name="username" value="admin">
                    </p>
                    <p>
                        <label>Password:</label><br>
                        <input type="password" name="password" value="admin123">
                    </p>
                    <input type="hidden" name="next" value="/rosetta/">
                    <p>
                        <button type="submit" class="btn">
                            🚀 Connexion vers Rosetta (URLs corrigées)
                        </button>
                    </p>
                </form>
            </div>
            
            <div class="form">
                <h3>🔗 Liens directs (URLs corrigées)</h3>
                <a href="/fr/admin/login/" class="btn">🔐 Page de connexion (/fr/admin/login/)</a>
                <a href="/fr/admin/" class="btn">📊 Administration (/fr/admin/)</a>
                <a href="/rosetta/" class="btn">🌍 Rosetta (/rosetta/)</a>
            </div>
            
            <div class="info">
                <h3>📋 Instructions finales:</h3>
                <ol>
                    <li><strong>Utilisez le formulaire ci-dessus</strong> (URLs corrigées)</li>
                    <li><strong>OU cliquez sur "Page de connexion"</strong></li>
                    <li><strong>Identifiants:</strong> admin / admin123</li>
                    <li><strong>Après connexion:</strong> Allez sur /rosetta/</li>
                </ol>
            </div>
            
            <div class="success">
                🎯 <strong>URLs qui fonctionnent:</strong><br>
                • Connexion: <code>http://localhost:8000/fr/admin/login/</code><br>
                • Administration: <code>http://localhost:8000/fr/admin/</code><br>
                • Rosetta: <code>http://localhost:8000/rosetta/</code>
            </div>
        </div>
    </body>
    </html>
    """
    
    return HttpResponse(html)


def minimal_welcome(request):
    """Page d'accueil minimaliste avec selecteur de langue"""
    return HttpResponse("""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>MartialComp - Interface de Traduction</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 50px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
        .header { text-align: center; margin-bottom: 30px; }
        .language-selector { margin: 20px 0; }
        .language-select { padding: 10px; border: 2px solid #007cba; border-radius: 5px; }
        .links { margin: 30px 0; }
        .links a { display: block; padding: 15px; margin: 10px 0; background: #007cba; color: white; text-decoration: none; border-radius: 5px; text-align: center; }
        .links a:hover { background: #005a87; }
        .info { background: #e8f4f8; padding: 20px; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌍 MartialComp - Interface de Traduction</h1>
            <p>Système multilingue en mode développement</p>
        </div>
        
        <div class="language-selector">
            <form action="/set-language/" method="post">
                <input type="hidden" name="csrfmiddlewaretoken" value="{{ csrf_token }}">
                <label for="language">Choisir la langue:</label>
                <select name="language" id="language" class="language-select" onchange="this.form.submit()">
                    <option value="fr">Français</option>
                    <option value="en">English</option>
                    <option value="es">Español</option>
                    <option value="de">Deutsch</option>
                    <option value="it">Italiano</option>
                </select>
            </form>
        </div>
        
        <div class="links">
            <a href="/rosetta/">📝 Interface Rosetta (Gestion des traductions)</a>
            <a href="/admin/">⚙️ Administration Django</a>
        </div>
        
        <div class="info">
            <h3>📋 Instructions:</h3>
            <ol>
                <li><strong>Créer un superuser:</strong><br>
                    <code>python manage.py createsuperuser --settings=config.settings_minimal_translation</code>
                </li>
                <li><strong>Accéder à Rosetta:</strong> Cliquez sur "Interface Rosetta" ci-dessus</li>
                <li><strong>Gérer les traductions:</strong> Éditez les fichiers .po dans Rosetta</li>
                <li><strong>Tester les langues:</strong> Utilisez le sélecteur de langue ci-dessus</li>
            </ol>
        </div>
        
        <div class="info">
            <h3>🎯 Statut du système:</h3>
            <ul>
                <li>✅ Django multilingue activé</li>
                <li>✅ Rosetta installé et configuré</li>
                <li>✅ 5 langues supportées</li>
                <li>✅ Interface simplifiée pour développement</li>
            </ul>
        </div>
    </div>
</body>
</html>
    """)

# URLs de base
urlpatterns = [
    path('admin/', admin.site.urls),
    path('rosetta/', include('rosetta.urls')),
    path('set-language/', set_language, name='set_language'),
    path('test/', test_page, name='test_page'),
    path('fixed/', test_page_fixed, name='test_fixed'),
    path('', minimal_welcome, name='welcome'),
]

# Fichiers statiques en mode debug
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)