#!/bin/bash
# Script pour vérifier et compléter le transfert

echo "======================================"
echo "VÉRIFICATION DU TRANSFERT COMPLET"
echo "======================================"

# 1. Vérifier la présence du module task_management
echo "1. Vérification du module task_management..."
if [ -d "apps/task_management" ]; then
    echo "✓ Module task_management présent"
    ls -la apps/task_management/
else
    echo "✗ Module task_management MANQUANT!"
fi

# 2. Vérifier si task_management est dans INSTALLED_APPS
echo -e "\n2. Vérification de INSTALLED_APPS..."
grep -A 30 "INSTALLED_APPS" config/settings.py | grep -E "(task_management|competitions|finances|organizations)"

# 3. Vérifier les imports dans api/views.py
echo -e "\n3. Vérification du nouveau fichier api/views.py..."
if [ -f "api/views.py" ]; then
    echo "✓ api/views.py présent"
    head -20 api/views.py
else
    echo "✗ api/views.py MANQUANT! Ce fichier est nécessaire pour les nouveaux endpoints"
fi

# 4. Vérifier la structure complète de apps/
echo -e "\n4. Structure du dossier apps/..."
ls -la apps/

# 5. Vérifier les nouveaux endpoints dans api/urls.py
echo -e "\n5. Vérification des nouveaux endpoints..."
grep -E "(health|info|mobile|dashboard)" api/urls.py || echo "✗ Nouveaux endpoints manquants"

# 6. Créer api/views.py s'il manque
if [ ! -f "api/views.py" ]; then
    echo -e "\n6. Création du fichier api/views.py manquant..."
    cat > api/views.py << 'EOF'
from django.http import JsonResponse
from django.views.generic import View
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def health(request):
    """Health check endpoint"""
    return Response({'status': 'healthy', 'service': 'MartialComp API'})

@api_view(['GET'])
def info(request):
    """API info endpoint"""
    return Response({
        'name': 'MartialComp API',
        'version': '1.0.0',
        'endpoints': {
            'health': '/api/health/',
            'auth': '/api/v1/auth/',
            'mobile': '/api/v1/mobile/',
        }
    })

class MobileDashboardView(View):
    def get(self, request):
        return JsonResponse({'message': 'Mobile dashboard endpoint'})

class PaymentMethodsView(View):
    def get(self, request):
        return JsonResponse({'methods': ['credit_card', 'paypal', 'bank_transfer']})

@api_view(['GET'])
def generate_certificate_number(request):
    return Response({'certificate_number': 'CERT-2025-001'})

@api_view(['GET'])
def generate_license_number(request):
    return Response({'license_number': 'LIC-2025-001'})
EOF
fi

echo -e "\n======================================"
echo "RÉSUMÉ DES VÉRIFICATIONS"
echo "======================================"