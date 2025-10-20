#!/bin/bash
# Script pour trouver tous les appels à Discipline.objects.get()

echo "🔍 Recherche de tous les appels à Discipline.objects.get()..."
echo "=================================================="

# Recherche dans tous les fichiers Python
echo -e "\n1. Recherche directe de 'Discipline.objects.get':"
grep -r "Discipline\.objects\.get" /var/www/vhosts/martialcomp.com/httpdocs --include="*.py" 2>/dev/null | head -20

echo -e "\n2. Recherche de patterns similaires:"
grep -r "discipline.*\.get(" /var/www/vhosts/martialcomp.com/httpdocs --include="*.py" 2>/dev/null | grep -v "disciplines.all()" | head -20

echo -e "\n3. Recherche dans les templates:"
grep -r "discipline" /var/www/vhosts/martialcomp.com/httpdocs/templates --include="*.html" 2>/dev/null | grep -i "get" | head -10

echo -e "\n4. Recherche dans les fichiers de cache Python:"
find /var/www/vhosts/martialcomp.com/httpdocs -name "*.pyc" -o -name "__pycache__" | xargs rm -rf 2>/dev/null
echo "✅ Cache Python nettoyé"

echo -e "\n5. Vérification des imports circulaires:"
grep -r "from.*practitioner.*import" /var/www/vhosts/martialcomp.com/httpdocs/apps/competitions --include="*.py" | head -10

echo -e "\n=================================================="
echo "✅ Recherche terminée"