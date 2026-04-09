#!/bin/bash

# Script pour créer les Judges en production
# Date: 16 novembre 2025

echo "========================================================================"
echo "CRÉATION DES JUDGES POUR LES UTILISATEURS STAFF"
echo "========================================================================"
echo ""

# Copier le script Python sur le serveur
echo "📤 Copie du script sur le serveur..."
scp create_judges_for_staff.py martialcomp-production:/tmp/

# Exécuter le script en production
echo ""
echo "🚀 Exécution du script en production..."
echo ""

ssh martialcomp-production << 'ENDSSH'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "=== AVANT EXÉCUTION ==="
python3 manage.py shell << 'ENDPYTHON'
from apps.competitions.models import Judge, Practitioner
print(f"Practitioners existants: {Practitioner.objects.count()}")
print(f"Judges existants: {Judge.objects.count()}")
ENDPYTHON

echo ""
echo "=== EXÉCUTION DU SCRIPT ==="
python3 manage.py shell < /tmp/create_judges_for_staff.py

echo ""
echo "=== APRÈS EXÉCUTION ==="
python3 manage.py shell << 'ENDPYTHON'
from apps.competitions.models import Judge, Practitioner
print(f"Practitioners: {Practitioner.objects.count()}")
print(f"Judges: {Judge.objects.count()}")
print(f"Judges actifs: {Judge.objects.filter(active=True).count()}")
ENDPYTHON

ENDSSH

echo ""
echo "========================================================================"
echo "✅ SCRIPT TERMINÉ"
echo "========================================================================"
echo ""
echo "Prochaines étapes:"
echo "1. Vérifier que les Judges ont été créés (voir résumé ci-dessus)"
echo "2. Tester la création de combat sur:"
echo "   https://martialcomp.com/fr/competitions/combat/combats/creer/competition/4/"
echo ""
