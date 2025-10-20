#!/bin/bash

# Script pour diagnostiquer l'erreur 500

echo "=== DIAGNOSTIC DE L'ERREUR 500 ==="
echo "URL: https://martialcomp.com/fr/competitions/dashboard/club/"
echo "Date: $(date)"
echo ""

cd /var/www/vhosts/martialcomp.com/httpdocs

# 1. Vérifier les logs Django
echo "1. DERNIÈRES ERREURS DANS LES LOGS DJANGO"
echo "========================================="

echo "Recherche des erreurs 500 récentes..."
tail -n 100 logs/django.log | grep -A 5 -B 5 "500\|ERROR\|Traceback" | tail -50

echo ""
echo "Recherche spécifique pour le dashboard..."
tail -n 100 logs/django.log | grep -A 5 -B 5 "dashboard/club" | tail -30

echo ""

# 2. Vérifier les logs Gunicorn
echo "2. LOGS GUNICORN RÉCENTS"
echo "========================"

journalctl -u martialcomp.service -n 50 | grep -A 3 -B 3 "ERROR\|500\|Traceback" | tail -30

echo ""

# 3. Tester l'accès au dashboard
echo "3. TEST D'ACCÈS AU DASHBOARD"
echo "============================="

# Test avec curl
echo "Test de l'URL du dashboard..."
response_code=$(curl -s -o /tmp/dashboard_response.html -w "%{http_code}" https://martialcomp.com/fr/competitions/dashboard/club/)

echo "Code de réponse: $response_code"

if [ "$response_code" = "500" ]; then
    echo "❌ Erreur 500 confirmée"
    
    # Chercher des indices dans la réponse
    if [ -f /tmp/dashboard_response.html ]; then
        echo ""
        echo "Contenu de l'erreur (si DEBUG=True):"
        grep -A 5 -B 5 "Exception\|Error\|Traceback" /tmp/dashboard_response.html 2>/dev/null | head -20
    fi
else
    echo "✓ Code de réponse: $response_code"
fi

echo ""

# 4. Vérifier les erreurs communes
echo "4. VÉRIFICATION DES ERREURS COMMUNES"
echo "===================================="

/var/www/vhosts/martialcomp.com/venv/bin/python manage.py shell --settings=config.settings.production << 'EOF'
import sys
print("Vérifications Python:")

# Vérifier les imports du dashboard
try:
    from apps.competitions.views.dashboard import club
    print("✓ Import views.dashboard.club réussi")
except Exception as e:
    print(f"❌ Erreur import dashboard.club: {e}")

try:
    from apps.competitions.views.club import dashboard
    print("✓ Import views.club.dashboard réussi") 
except Exception as e:
    print(f"❌ Erreur import club.dashboard: {e}")

# Vérifier les modèles
try:
    from apps.competitions.models import Club, Practitioner, Competition
    print("✓ Modèles Competition importés")
except Exception as e:
    print(f"❌ Erreur import modèles: {e}")

# Vérifier la base de données
try:
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    print("✓ Connexion base de données OK")
except Exception as e:
    print(f"❌ Erreur base de données: {e}")
EOF

echo ""

# 5. Vérifier les permissions et l'authentification
echo "5. VÉRIFICATION DES PERMISSIONS"
echo "================================"

/var/www/vhosts/martialcomp.com/venv/bin/python manage.py shell --settings=config.settings.production << 'EOF'
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import Client

User = get_user_model()

# Simuler une requête
try:
    # Vérifier l'URL
    url = reverse('competitions:dashboard:club_dashboard')
    print(f"✓ URL trouvée: {url}")
except Exception as e:
    print(f"❌ Erreur URL: {e}")
    # Essayer une autre variante
    try:
        url = reverse('competitions:club_dashboard')
        print(f"✓ URL alternative trouvée: {url}")
    except:
        print("❌ Aucune URL dashboard trouvée")
EOF

echo ""

# 6. Vérifier les fichiers statiques et templates
echo "6. VÉRIFICATION DES TEMPLATES"
echo "============================="

# Chercher le template du dashboard
echo "Recherche du template dashboard..."
find . -name "*dashboard*" -path "*/templates/*" -type f | grep -E "club|competitions" | head -10

echo ""

# 7. Activer temporairement DEBUG pour plus d'infos
echo "7. SUGGESTION POUR DÉBOGUER"
echo "==========================="

echo "Pour obtenir plus d'informations sur l'erreur 500:"
echo ""
echo "1. Activez temporairement DEBUG dans .env.production:"
echo "   echo 'DEBUG=True' >> .env.production"
echo ""
echo "2. Redémarrez le service:"
echo "   systemctl restart martialcomp.service"
echo ""
echo "3. Rechargez la page pour voir la trace complète"
echo ""
echo "4. N'OUBLIEZ PAS de désactiver DEBUG après:"
echo "   sed -i 's/DEBUG=True/DEBUG=False/' .env.production"
echo "   systemctl restart martialcomp.service"
echo ""

# 8. Problèmes courants
echo "8. PROBLÈMES COURANTS IDENTIFIÉS"
echo "================================="

echo "D'après les logs d'initialisation, il y a des erreurs avec:"
echo "- Grade model: Unknown field(s) (accessible_to_clubs, description)"
echo "- unified_scoring.py: syntax error line 325"
echo ""
echo "Ces erreurs pourraient causer le problème 500 si le dashboard utilise ces modules."

echo ""
echo "============================================"
echo "RÉSUMÉ DU DIAGNOSTIC"
echo "============================================"
echo ""
echo "Actions recommandées:"
echo "1. Vérifier les logs ci-dessus pour l'erreur exacte"
echo "2. Si nécessaire, activer DEBUG temporairement"
echo "3. Corriger les erreurs dans Grade model et unified_scoring.py"
echo "4. Vérifier que l'utilisateur a les permissions pour accéder au dashboard"
echo ""
echo "============================================"

# Nettoyer
rm -f /tmp/dashboard_response.html