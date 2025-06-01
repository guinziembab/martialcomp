from django.urls import path, include
from rest_framework.documentation import include_docs_urls

urlpatterns = [
    # API d'authentification
    path('v1/auth/', include('api_auth.urls', namespace='api_auth')),
    
    # Documentation API
    path('docs/', include_docs_urls(title='MartialComp API')),
]