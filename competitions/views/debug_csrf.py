from django.http import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import render

@ensure_csrf_cookie
def debug_csrf(request):
    """
    Vue de débogage CSRF qui affiche les informations sur les cookies et les en-têtes CSRF.
    """
    response = HttpResponse()
    response.write("<html><body>")
    response.write("<h1>Débogage CSRF</h1>")
    
    # Informations sur la requête
    response.write("<h2>Informations sur la requête</h2>")
    response.write(f"<p>Method: {request.method}</p>")
    response.write(f"<p>Path: {request.path}</p>")
    response.write(f"<p>User: {request.user}</p>")
    
    # Cookies
    response.write("<h2>Cookies</h2>")
    csrf_cookie = request.COOKIES.get('csrftoken', 'Non trouvé')
    response.write(f"<p>CSRF Cookie: {csrf_cookie}</p>")
    
    for key, value in request.COOKIES.items():
        response.write(f"<p>{key}: {value}</p>")
    
    # En-têtes HTTP
    response.write("<h2>En-têtes HTTP</h2>")
    csrf_header = request.META.get('HTTP_X_CSRFTOKEN', 'Non trouvé')
    response.write(f"<p>CSRF Header: {csrf_header}</p>")
    
    # Formulaire de test
    response.write("<h2>Formulaire de test CSRF</h2>")
    response.write("""
    <form method="post" action="">
        <input type="hidden" name="csrfmiddlewaretoken" value="%s">
        <button type="submit">Tester CSRF</button>
    </form>
    """ % csrf_cookie)
    
    # Formulaire Django standard avec tag CSRF
    response.write("<h2>Formulaire Django avec tag CSRF</h2>")
    
    # Afficher les paramètres CSRF dans settings.py
    response.write("<h2>Paramètres CSRF</h2>")
    from django.conf import settings
    response.write(f"<p>CSRF_COOKIE_HTTPONLY: {settings.CSRF_COOKIE_HTTPONLY}</p>")
    response.write(f"<p>CSRF_COOKIE_SECURE: {settings.CSRF_COOKIE_SECURE}</p>")
    response.write(f"<p>CSRF_COOKIE_NAME: {settings.CSRF_COOKIE_NAME}</p>")
    response.write(f"<p>CSRF_HEADER_NAME: {settings.CSRF_HEADER_NAME}</p>")
    response.write(f"<p>CSRF_USE_SESSIONS: {settings.CSRF_USE_SESSIONS}</p>")
    response.write(f"<p>CSRF_COOKIE_SAMESITE: {settings.CSRF_COOKIE_SAMESITE}</p>")
    
    response.write("</body></html>")
    return response

def debug_csrf_template(request):
    """
    Vue de débogage CSRF qui utilise un template Django.
    """
    return render(request, 'debug_csrf.html', {})