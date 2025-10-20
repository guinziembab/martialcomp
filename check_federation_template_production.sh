#!/bin/bash

echo "=== Analyse du template federation utilisé en production ==="
echo ""

# 1. Vérifier la structure des URLs
echo "1. Vérification de la structure des URLs dans dashboard.py:"
grep -n "federation" /mnt/c/martial_hub_django/martialcomp/apps/competitions/urls/dashboard.py | grep "path"

echo ""
echo "2. Templates federation existants:"
find /mnt/c/martial_hub_django/martialcomp/apps/competitions/templates -name "*federation*.html" -type f | grep -v backup | sort

echo ""
echo "3. Vérification du template appelé dans la vue:"
grep -n "render.*federation" /mnt/c/martial_hub_django/martialcomp/apps/competitions/views/dashboard/federations.py

echo ""
echo "4. Recherche d'overrides possibles dans les settings:"
grep -r "TEMPLATES" /mnt/c/martial_hub_django/martialcomp/config/settings/production.py 2>/dev/null | head -20

echo ""
echo "5. Vérification si un template loader particulier est utilisé:"
grep -r "template.*loader" /mnt/c/martial_hub_django/martialcomp/config/settings/ 2>/dev/null

echo ""
echo "6. Structure actuelle du template federation.html (navigation):"
echo "- Recherche de la structure de navigation:"
grep -A10 "nav.*tab" /mnt/c/martial_hub_django/martialcomp/apps/competitions/templates/competitions/dashboard/federation.html | head -20

echo ""
echo "7. Comparaison avec la structure attendue en production:"
echo "Le code HTML de production montre des liens directs comme:"
echo "- /fr/competitions/dashboard/federations/42/clubs/"
echo "- /fr/competitions/dashboard/federations/42/competitions/"
echo ""
echo "Ces liens correspondent aux URLs définies dans dashboard.py"

echo ""
echo "=== CONCLUSION ==="
echo "Le template en développement utilise une navigation par onglets Bootstrap,"
echo "mais la production semble utiliser soit:"
echo "1. Un template différent (modifié directement sur le serveur)"
echo "2. Un système de template override"
echo "3. Un template généré différemment selon l'environnement"