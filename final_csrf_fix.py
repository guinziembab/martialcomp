#!/usr/bin/env python3
"""
Solution finale pour corriger le problème CSRF avec multi-tenant
"""

import os
import re

def fix_login_template_final():
    """Corrige définitivement le template de login"""
    template_path = "competitions/templates/registration/login.html"
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # S'assurer que l'action utilise l'URL correcte
    # Utiliser l'URL absolue pour éviter les problèmes de routage
    content = re.sub(
        r'action="[^"]*"',
        'action="/accounts/login/"',
        content
    )
    
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✓ Template de login corrigé avec URL absolue")

def add_csrf_logging():
    """Ajoute le logging CSRF pour le débogage"""
    settings_path = "config/settings.py"
    
    with open(settings_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    csrf_logging = '''
# Logging CSRF pour débogage
if DEBUG:
    LOGGING['loggers']['django.security.csrf'] = {
        'handlers': ['console'],
        'level': 'DEBUG',
        'propagate': False,
    }
'''
    
    if 'django.security.csrf' not in content:
        # Ajouter après la section LOGGING
        content = content.replace(
            "# Créer le répertoire de logs s'il n'existe pas",
            csrf_logging + "\n# Créer le répertoire de logs s'il n'existe pas"
        )
        
        with open(settings_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✓ Logging CSRF ajouté pour le débogage")
    else:
        print("✓ Logging CSRF déjà configuré")

def create_simple_test_form():
    """Crée un formulaire de test simple"""
    test_form = '''<!DOCTYPE html>
<html>
<head>
    <title>Test CSRF Login</title>
</head>
<body>
    <h1>Test CSRF Login Simple</h1>
    
    <form method="post" action="/accounts/login/">
        {% csrf_token %}
        <p>
            <label>Username: <input type="text" name="username" required></label>
        </p>
        <p>
            <label>Password: <input type="password" name="password" required></label>
        </p>
        <p>
            <button type="submit">Login</button>
        </p>
    </form>
    
    <hr>
    
    <h2>Test sans CSRF (pour vérification)</h2>
    <form method="post" action="/auth/test-login-no-csrf/">
        <p>
            <label>Username: <input type="text" name="username" required></label>
        </p>
        <p>
            <label>Password: <input type="password" name="password" required></label>
        </p>
        <p>
            <button type="submit">Login sans CSRF</button>
        </p>
    </form>
</body>
</html>'''
    
    # Sauvegarder le formulaire de test
    test_path = "competitions/templates/registration/test_csrf_login.html"
    with open(test_path, 'w', encoding='utf-8') as f:
        f.write(test_form)
    
    print(f"✓ Formulaire de test créé: {test_path}")

def create_csrf_test_view():
    """Crée une vue de test simple"""
    view_content = '''from django.shortcuts import render

def test_csrf_view(request):
    """Vue de test pour CSRF"""
    return render(request, 'registration/test_csrf_login.html')
'''
    
    # Sauvegarder la vue
    view_path = "competitions/views/test_csrf.py"
    with open(view_path, 'w', encoding='utf-8') as f:
        f.write(view_content)
    
    print(f"✓ Vue de test créée: {view_path}")
    
    # Instructions pour l'URL
    print("\nAjoutez dans competitions/urls/auth.py:")
    print("from ..views.test_csrf import test_csrf_view")
    print("path('test-csrf/', test_csrf_view, name='test_csrf'),")

def create_final_documentation():
    """Crée la documentation finale"""
    doc_content = """# Solution CSRF pour Multi-tenant

## Le problème
L'erreur "CSRF token from POST incorrect" se produit lors du login en environnement multi-tenant.

## La solution appliquée

1. **Middleware tenant corrigé** pour préserver le token CSRF
2. **Template de login** utilisant l'URL absolue `/accounts/login/`
3. **Paramètres CSRF** configurés pour multi-tenant
4. **Logging CSRF** activé pour le débogage

## Test de la solution

1. Videz le cache du navigateur (Ctrl+Shift+Delete)
2. Redémarrez le serveur Django
3. Accédez à http://127.0.0.1:8000/auth/test-csrf/ pour tester
4. Si ça fonctionne, le login normal devrait aussi fonctionner

## Débogage avancé

Si l'erreur persiste:

1. Vérifiez la console Django pour les logs CSRF
2. Utilisez http://127.0.0.1:8000/auth/debug-login/ pour voir les détails
3. Testez avec http://127.0.0.1:8000/auth/test-login-no-csrf/ (sans CSRF)

## Configuration vérifiée

- ✓ CsrfViewMiddleware avant TenantMiddleware
- ✓ CSRF_COOKIE_DOMAIN = None (pour localhost)
- ✓ CSRF_TRUSTED_ORIGINS inclut localhost
- ✓ Template contient {% csrf_token %}
- ✓ Formulaire utilise l'URL absolue

## Si tout échoue

Désactivez temporairement la protection CSRF pour le login:

```python
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def login_view(request):
    # ... code existant ...
```

**ATTENTION**: Ne jamais faire cela en production!
"""
    
    with open("CSRF_SOLUTION_FINALE.md", 'w', encoding='utf-8') as f:
        f.write(doc_content)
    
    print("✓ Documentation finale créée: CSRF_SOLUTION_FINALE.md")

def main():
    print("=== Solution finale CSRF ===\n")
    
    try:
        fix_login_template_final()
        add_csrf_logging()
        create_simple_test_form()
        create_csrf_test_view()
        create_final_documentation()
        
        print("\n=== Solution appliquée avec succès ===")
        print("\n1. Videz le cache du navigateur")
        print("2. Redémarrez le serveur Django")
        print("3. Testez à nouveau le login")
        print("\nConsultez CSRF_SOLUTION_FINALE.md pour plus de détails")
        
    except Exception as e:
        print(f"\nErreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()