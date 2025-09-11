from django.http import JsonResponse
from django.conf import settings

def debug_host(request):
    return JsonResponse({
        "ALLOWED_HOSTS": settings.ALLOWED_HOSTS,
        "Host header reçu": request.META.get("HTTP_HOST"),
        "SERVER_NAME": request.META.get("SERVER_NAME"),
        "SERVER_PORT": request.META.get("SERVER_PORT"),
    }) 
from django.conf import settings

def debug_host(request):
    return JsonResponse({
        "ALLOWED_HOSTS": settings.ALLOWED_HOSTS,
        "Host header reçu": request.META.get("HTTP_HOST"),
        "SERVER_NAME": request.META.get("SERVER_NAME"),
        "SERVER_PORT": request.META.get("SERVER_PORT"),
    }) 