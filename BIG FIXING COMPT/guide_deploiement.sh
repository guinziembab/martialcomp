#!/bin/bash
# ============================================================================
# GUIDE DE CORRECTION ET DÉPLOIEMENT - competition_management_pro
# ============================================================================
# Ce script guide le déploiement de la correction pour le problème 
# d'affichage des catégories, types et inscriptions
# ============================================================================

echo "============================================================================"
echo "DIAGNOSTIC ET CORRECTION - competition_management_pro"
echo "============================================================================"
echo ""

# ============================================================================
# RÉSUMÉ DU PROBLÈME
# ============================================================================
cat << 'PROBLEM'
PROBLÈME IDENTIFIÉ:
------------------
Les données (catégories, types de compétition, inscriptions) existent en 
base de données mais ne s'affichent pas dans le template.

CAUSE RACINE:
------------
Les proxies Python créés pour exposer les données au template Django ne 
s'intègrent pas correctement avec le système de templates Django.

Même avec __iter__, __len__, __getitem__, Django templates ne peut pas 
itérer correctement sur ces objets personnalisés.

SOLUTION:
---------
1. Charger les données directement via des querysets Django natifs
2. Passer les querysets/listes directement au contexte (sans proxies)
3. Modifier le template pour utiliser les variables du contexte directement

PROBLEM

echo ""
echo "============================================================================"
echo "FICHIERS CORRIGÉS GÉNÉRÉS"
echo "============================================================================"
echo ""
echo "1. competition_management_pro_fixed.py"
echo "   - Vue Django corrigée"
echo "   - Chargement direct des données sans proxies"
echo "   - 11 remplacements effectués"
echo ""
echo "2. competition_management_pro_fixed.html"
echo "   - Template corrigé"
echo "   - Utilise les variables du contexte directement"
echo "   - Élimine les appels à competition.categories.all"
echo ""

# ============================================================================
# ÉTAPE 1: VÉRIFICATION DES DONNÉES EN BASE
# ============================================================================
cat << 'VERIFY'

============================================================================
ÉTAPE 1: VÉRIFIER LES DONNÉES EN BASE
============================================================================

Avant de déployer, vérifions que les données existent:

ssh martialcomp-production << 'PYEOF'
cd /var/www/vhosts/martialcomp.com/httpdocs
python3 << 'INNERPY'
import os
import sys
sys.path.insert(0, '/var/www/vhosts/martialcomp.com/httpdocs')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'martialcomp.settings')

import django
django.setup()

from apps.competitions.models import CompetitionCategory, CompetitionType, CompetitionRegistration

competition_id = 4

# Vérifier les catégories
categories = CompetitionCategory.objects.filter(competition_id=competition_id)
print(f"✓ Catégories trouvées: {categories.count()}")
for cat in categories[:5]:
    print(f"  - {cat.name} (type_id: {cat.competition_type_id})")

# Vérifier les types
type_ids = list(categories.values_list('competition_type_id', flat=True).distinct())
if type_ids:
    types = CompetitionType.objects.filter(id__in=type_ids)
    print(f"\n✓ Types trouvés: {types.count()}")
    for t in types:
        print(f"  - {t.name}")

# Vérifier les inscriptions
registrations = CompetitionRegistration.objects.filter(competition_id=competition_id)
print(f"\n✓ Inscriptions trouvées: {registrations.count()}")

print("\n" + "="*60)
print("Si vous voyez des données ci-dessus, le problème vient")
print("uniquement de l'affichage dans le template.")
print("="*60)
INNERPY
PYEOF

VERIFY

# ============================================================================
# ÉTAPE 2: SAUVEGARDE
# ============================================================================
cat << 'BACKUP'

============================================================================
ÉTAPE 2: SAUVEGARDER LES FICHIERS ACTUELS
============================================================================

IMPORTANT: Toujours sauvegarder avant de modifier !

# Sur votre machine locale
cd /mnt/c/martial_hub_django/martialcomp

# Sauvegarder la vue actuelle
cp apps/competitions/views/competition_management_pro.py \
   apps/competitions/views/competition_management_pro.py.backup.$(date +%Y%m%d_%H%M%S)

# Sauvegarder le template actuel
cp apps/competitions/templates/competitions/club/competition_management_pro.html \
   apps/competitions/templates/competitions/club/competition_management_pro.html.backup.$(date +%Y%m%d_%H%M%S)

echo "✓ Sauvegardes créées"

BACKUP

# ============================================================================
# ÉTAPE 3: DÉPLOIEMENT
# ============================================================================
cat << 'DEPLOY'

============================================================================
ÉTAPE 3: DÉPLOYER LES FICHIERS CORRIGÉS
============================================================================

# Copier la vue corrigée depuis Claude vers votre machine locale
# Puis la copier vers le serveur

cd /mnt/c/martial_hub_django/martialcomp

# Remplacer le fichier de vue
scp competition_management_pro_fixed.py \
    martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/competition_management_pro.py

echo "✓ Vue copiée"

# Remplacer le template
scp competition_management_pro_fixed.html \
    martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/club/competition_management_pro.html

echo "✓ Template copié"

# Vider le cache Python
ssh martialcomp-production "cd /var/www/vhosts/martialcomp.com/httpdocs && \
    rm -rf apps/competitions/views/__pycache__ 2>/dev/null; \
    find . -name '*competition_management_pro*.pyc' -delete 2>/dev/null; \
    echo 'Cache Python vidé'"

echo "✓ Cache vidé"

# Redémarrer Apache (si nécessaire)
ssh martialcomp-production "sudo service apache2 reload"

echo "✓ Apache rechargé"

DEPLOY

# ============================================================================
# ÉTAPE 4: TEST ET VÉRIFICATION
# ============================================================================
cat << 'TEST'

============================================================================
ÉTAPE 4: TESTER LA CORRECTION
============================================================================

1. Vider le cache du navigateur (Ctrl+F5 ou Cmd+Shift+R)

2. Accéder à la page:
   https://martialcomp.com/fr/competitions/club/competitions/4/manage/pro/

3. Vérifier les onglets:
   ✓ Types de compétition - Les types doivent s'afficher
   ✓ Catégories - Les catégories doivent s'afficher
   ✓ Inscriptions - Les inscriptions doivent s'afficher
   ✓ Arbitres - L'onglet doit être visible

4. Vérifier les logs Django:
   ssh martialcomp-production "tail -f /var/www/vhosts/martialcomp.com/httpdocs/logs/django.log | grep 'Compétition 4:'"

   Vous devriez voir:
   - "Compétition 4: X catégories chargées"
   - "Compétition 4: X types chargés"
   - "Compétition 4: X inscriptions chargées"

TEST

# ============================================================================
# RÉSUMÉ DES MODIFICATIONS
# ============================================================================
cat << 'SUMMARY'

============================================================================
RÉSUMÉ DES MODIFICATIONS EFFECTUÉES
============================================================================

DANS LA VUE (competition_management_pro.py):
--------------------------------------------
✓ Suppression de tous les proxies (CategoriesProxy, CompetitionTypesProxy, etc.)
✓ Chargement direct via querysets Django natifs
✓ Passage des querysets au contexte sans wrapping
✓ Ajout de logs pour le diagnostic
✓ Gestion d'erreur améliorée

DANS LE TEMPLATE (competition_management_pro.html):
---------------------------------------------------
✓ Remplacement de {{ competition.categories.all }} par {{ categories }}
✓ Remplacement de {{ competition.competition_types.all }} par {{ competition_types }}
✓ 11 remplacements au total

AVANTAGES DE CETTE APPROCHE:
-----------------------------
✓ Simplicité: pas de proxies complexes
✓ Compatibilité: utilise les querysets Django natifs
✓ Performance: préfetching et select_related optimisés
✓ Maintenabilité: code plus simple et lisible
✓ Débogage: logs détaillés pour identifier les problèmes

SUMMARY

# ============================================================================
# SCRIPT DE DIAGNOSTIC POST-DÉPLOIEMENT
# ============================================================================
cat << 'DIAGNOSTIC'

============================================================================
SCRIPT DE DIAGNOSTIC POST-DÉPLOIEMENT
============================================================================

Si les données ne s'affichent toujours pas après déploiement, 
exécuter ce script de diagnostic:

ssh martialcomp-production << 'DIAGEOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "===== DIAGNOSTIC ====="
echo ""

# 1. Vérifier que les fichiers ont bien été copiés
echo "1. Vérification des fichiers:"
stat apps/competitions/views/competition_management_pro.py
stat apps/competitions/templates/competitions/club/competition_management_pro.html

echo ""
echo "2. Vérification du contenu de la vue:"
grep -c "PAS DE PROXIES COMPLEXES" apps/competitions/views/competition_management_pro.py || echo "ERREUR: Fichier pas mis à jour"

echo ""
echo "3. Vérification du contenu du template:"
grep -c "{% for category in categories %}" apps/competitions/templates/competitions/club/competition_management_pro.html || echo "ATTENTION: Template peut-être pas mis à jour"

echo ""
echo "4. Test de chargement Django:"
python3 << 'PYEOF'
import os
import sys
sys.path.insert(0, '/var/www/vhosts/martialcomp.com/httpdocs')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'martialcomp.settings')

import django
django.setup()

from apps.competitions.models import CompetitionCategory, CompetitionType, CompetitionRegistration

competition_id = 4

categories = CompetitionCategory.objects.filter(competition_id=competition_id)
print(f"Catégories: {categories.count()}")

type_ids = list(categories.values_list('competition_type_id', flat=True).distinct())
if type_ids:
    types = CompetitionType.objects.filter(id__in=type_ids)
    print(f"Types: {types.count()}")

registrations = CompetitionRegistration.objects.filter(competition_id=competition_id)
print(f"Inscriptions: {registrations.count()}")
PYEOF

echo ""
echo "===== FIN DIAGNOSTIC ====="
DIAGEOF

DIAGNOSTIC

echo ""
echo "============================================================================"
echo "DOCUMENTATION CRÉÉE"
echo "============================================================================"
echo ""
echo "Ce guide contient toutes les étapes nécessaires pour:"
echo "  1. Vérifier les données en base"
echo "  2. Sauvegarder les fichiers actuels"
echo "  3. Déployer les corrections"
echo "  4. Tester et diagnostiquer"
echo ""
echo "Suivez les étapes dans l'ordre pour une correction réussie."
echo ""
echo "============================================================================"
