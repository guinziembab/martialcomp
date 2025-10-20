#!/bin/bash

# Script pour tester les fonctionnalités après correction

echo "=== TEST DES FONCTIONNALITÉS ==="
echo ""

cd /var/www/vhosts/martialcomp.com/httpdocs

# 1. Test de l'URL grades
echo "1. TEST URL GRADES"
echo "=================="

response=$(curl -s -o /tmp/grades_response.html -w "%{http_code}" -L https://martialcomp.com/fr/competitions/grades/management/)
echo "URL Grades: HTTP $response"

if [ "$response" = "200" ]; then
    echo "✅ Page grades accessible !"
    echo ""
    echo "Aperçu du contenu:"
    grep -o "<title>.*</title>" /tmp/grades_response.html || echo "Pas de titre trouvé"
    grep -o "<h1>.*</h1>" /tmp/grades_response.html | head -1 || echo "Pas de H1 trouvé"
else
    echo "❌ Erreur d'accès à la page grades"
fi

echo ""

# 2. Test de l'URL combat
echo "2. TEST URL COMBAT"
echo "=================="

response=$(curl -s -o /tmp/combat_response.html -w "%{http_code}" -L https://martialcomp.com/fr/competitions/combat/combats/creer/)
echo "URL Combat: HTTP $response"

if [ "$response" = "200" ]; then
    echo "✅ Page combat accessible !"
elif [ "$response" = "302" ]; then
    echo "⚠️ Redirection (authentification requise probablement)"
    location=$(curl -s -I -L https://martialcomp.com/fr/competitions/combat/combats/creer/ | grep -i "location:" | tail -1)
    echo "Redirige vers: $location"
elif [ "$response" = "500" ]; then
    echo "❌ Erreur 500 persiste"
    echo ""
    echo "Recherche d'erreurs récentes dans les logs:"
    tail -n 50 logs/django.log | grep -A 5 -B 2 "combat.*creer\|ERROR.*combat" | tail -20
fi

echo ""

# 3. Vérifier les URLs disponibles
echo "3. VÉRIFICATION DES URLS DISPONIBLES"
echo "===================================="

/var/www/vhosts/martialcomp.com/venv/bin/python << 'EOF'
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
import django
django.setup()

from django.urls import get_resolver
from django.urls import reverse

print("URLs importantes disponibles:")

# Tester les URLs clés
urls_to_check = [
    ('competitions:grades_management', 'Grades et Examens'),
    ('competitions:dashboard:club_dashboard', 'Dashboard Club'),
    ('admin:index', 'Admin Django'),
]

for url_name, description in urls_to_check:
    try:
        url = reverse(url_name)
        print(f"✓ {description}: {url}")
    except:
        pass

# Lister quelques URLs combat
print("\nURLs combat disponibles:")
resolver = get_resolver()
for pattern in resolver.url_patterns:
    if hasattr(pattern, 'pattern'):
        pattern_str = str(pattern.pattern)
        if 'combat' in pattern_str.lower():
            print(f"  - {pattern_str}")
EOF

echo ""

# 4. État général du système
echo "4. ÉTAT GÉNÉRAL DU SYSTÈME"
echo "=========================="

echo "Service Gunicorn:"
systemctl is-active martialcomp.service && echo "✅ Actif" || echo "❌ Inactif"

echo ""
echo "Dernières erreurs dans les logs (s'il y en a):"
tail -n 100 logs/django.log | grep -i "error\|exception" | tail -5 || echo "✅ Pas d'erreurs récentes"

echo ""

# 5. Résumé
echo "============================================"
echo "RÉSUMÉ DES TESTS"
echo "============================================"
echo ""

# Nettoyer
rm -f /tmp/grades_response.html /tmp/combat_response.html

echo "Points à vérifier dans le navigateur:"
echo ""
echo "1. Connectez-vous avec TESTBGA_USER1"
echo "2. Allez au dashboard: https://martialcomp.com/fr/competitions/dashboard/club/"
echo "3. Cliquez sur 'Grades et Examens' - devrait afficher la page"
echo "4. Essayez 'Créer un combat' - devrait fonctionner maintenant"
echo ""
echo "Si tout fonctionne, le déploiement est réussi ! 🎉"
echo ""
echo "============================================"