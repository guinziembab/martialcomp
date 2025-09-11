"""URL Configuration for testing"""
from django.contrib import admin
from django.urls import path
from django.http import HttpResponse
import sys
import os

# Ajouter le répertoire parent pour importer test_view
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from test_view import test_view

def simple_view(request):
    """Simple test view"""
    return HttpResponse("<h1>Hello MartialComp!</h1><p>Database test successful!</p>")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', test_view, name='home'),
    path('test/', simple_view, name='simple_test'),
]