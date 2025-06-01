from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.middleware.csrf import get_token
import logging

logger = logging.getLogger(__name__)

def debug_login_view(request):
    """Vue de login avec débogage CSRF"""
    if request.method == 'GET':
        # Forcer la génération d'un token CSRF
        token = get_token(request)
        logger.info(f"Token CSRF généré: {token[:10]}...")
        
        context = {
            'csrf_token': token,
            'debug_info': {
                'csrf_cookie': request.COOKIES.get('csrftoken', 'Non défini'),
                'session_id': request.session.session_key,
                'host': request.get_host(),
                'is_secure': request.is_secure(),
            }
        }
        return render(request, 'registration/debug_login.html', context)
    
    elif request.method == 'POST':
        # Déboguer la soumission
        debug_data = {
            'csrf_token_form': request.POST.get('csrfmiddlewaretoken'),
            'csrf_cookie': request.COOKIES.get('csrftoken'),
            'csrf_header': request.META.get('HTTP_X_CSRFTOKEN'),
            'username': request.POST.get('username'),
            'referer': request.META.get('HTTP_REFERER'),
            'host': request.get_host(),
        }
        
        logger.info(f"Tentative de login - Debug: {debug_data}")
        
        # Tenter l'authentification normale
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard:index')
        else:
            return JsonResponse({
                'error': 'Authentification échouée',
                'debug': debug_data
            })

# Vue temporaire sans CSRF pour test
@csrf_exempt
def test_login_no_csrf(request):
    """Vue de test sans protection CSRF"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return JsonResponse({'success': True, 'redirect': '/dashboard/'})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid credentials'})
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)
