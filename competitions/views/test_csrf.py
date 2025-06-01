from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import render

@ensure_csrf_cookie
def test_csrf_login(request):
    """
    Vue de test pour vérifier les problèmes CSRF lors de la connexion.
    """
    return render(request, "test_csrf_login.html")

