#!/bin/bash
# ============================================================================
# SCRIPT DE VÉRIFICATION RAPIDE - competition_management_pro
# ============================================================================
# Ce script vérifie rapidement si la correction est correctement déployée
# et fonctionnelle
# ============================================================================

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
SERVER="martialcomp-production"
HTTPDOCS="/var/www/vhosts/martialcomp.com/httpdocs"
COMPETITION_ID="4"

echo "============================================================================"
echo -e "${BLUE}VÉRIFICATION RAPIDE - competition_management_pro${NC}"
echo "============================================================================"
echo ""

# ============================================================================
# Fonction de vérification
# ============================================================================
check() {
    local description="$1"
    local command="$2"
    local expected="$3"
    
    echo -n "Vérification: $description... "
    
    result=$(eval "$command" 2>&1)
    
    if echo "$result" | grep -q "$expected"; then
        echo -e "${GREEN}✓ OK${NC}"
        return 0
    else
        echo -e "${RED}✗ ÉCHEC${NC}"
        echo "  Résultat: $result"
        return 1
    fi
}

# ============================================================================
# VÉRIFICATION 1: Fichiers déployés
# ============================================================================
echo -e "${BLUE}[1/5] Vérification des fichiers déployés${NC}"
echo "----------------------------------------"

check "Vue mise à jour" \
    "ssh $SERVER 'grep -q \"PAS DE PROXIES COMPLEXES\" $HTTPDOCS/apps/competitions/views/competition_management_pro.py && echo \"OK\" || echo \"KO\"'" \
    "OK"

check "Template mis à jour" \
    "ssh $SERVER 'grep -q \"{% for category in categories %}\" $HTTPDOCS/apps/competitions/templates/competitions/club/competition_management_pro.html && echo \"OK\" || echo \"KO\"'" \
    "OK"

echo ""

# ============================================================================
# VÉRIFICATION 2: Cache Python vidé
# ============================================================================
echo -e "${BLUE}[2/5] Vérification du cache Python${NC}"
echo "----------------------------------------"

check "Cache __pycache__ absent" \
    "ssh $SERVER 'test ! -d $HTTPDOCS/apps/competitions/views/__pycache__ && echo \"OK\" || echo \"KO\"'" \
    "OK"

check "Fichiers .pyc absents" \
    "ssh $SERVER 'find $HTTPDOCS/apps/competitions/views -name \"*competition_management_pro*.pyc\" 2>/dev/null | wc -l'" \
    "0"

echo ""

# ============================================================================
# VÉRIFICATION 3: Données en base de données
# ============================================================================
echo -e "${BLUE}[3/5] Vérification des données en base${NC}"
echo "----------------------------------------"

ssh $SERVER << 'VERIFYEOF'
cd /var/www/vhosts/martialcomp.com/httpdocs
python3 << 'PYEOF'
import os, sys
sys.path.insert(0, '/var/www/vhosts/martialcomp.com/httpdocs')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'martialcomp.settings')

import django
django.setup()

from apps.competitions.models import CompetitionCategory, CompetitionType, CompetitionRegistration

competition_id = 4

try:
    categories = CompetitionCategory.objects.filter(competition_id=competition_id)
    cat_count = categories.count()
    
    type_ids = list(categories.values_list('competition_type_id', flat=True).distinct())
    if type_ids:
        types = CompetitionType.objects.filter(id__in=type_ids)
        type_count = types.count()
    else:
        type_count = 0
    
    registrations = CompetitionRegistration.objects.filter(competition_id=competition_id)
    reg_count = registrations.count()
    
    print(f"CATEGORIES:{cat_count}")
    print(f"TYPES:{type_count}")
    print(f"REGISTRATIONS:{reg_count}")
    
    if cat_count > 0 and type_count > 0 and reg_count > 0:
        print("STATUS:OK")
    else:
        print("STATUS:KO")
except Exception as e:
    print(f"ERROR:{str(e)}")
    print("STATUS:ERROR")
PYEOF
VERIFYEOF

echo ""

# ============================================================================
# VÉRIFICATION 4: Logs Django
# ============================================================================
echo -e "${BLUE}[4/5] Vérification des logs Django${NC}"
echo "----------------------------------------"

echo "Dernières entrées des logs (5 dernières lignes):"
ssh $SERVER "tail -5 $HTTPDOCS/logs/django.log | grep -v '^$'" || echo "Aucune erreur récente"

echo ""

# ============================================================================
# VÉRIFICATION 5: Accès à la page
# ============================================================================
echo -e "${BLUE}[5/5] Test d'accès à la page${NC}"
echo "----------------------------------------"

URL="https://martialcomp.com/fr/competitions/club/competitions/$COMPETITION_ID/manage/pro/"

echo "Test de l'URL: $URL"
http_code=$(curl -s -o /dev/null -w "%{http_code}" -L "$URL" 2>/dev/null)

if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✓ Page accessible (HTTP $http_code)${NC}"
elif [ "$http_code" = "302" ] || [ "$http_code" = "301" ]; then
    echo -e "${YELLOW}⚠ Redirection (HTTP $http_code) - Vérifier l'authentification${NC}"
elif [ "$http_code" = "500" ]; then
    echo -e "${RED}✗ Erreur serveur (HTTP $http_code) - Vérifier les logs${NC}"
else
    echo -e "${RED}✗ Code HTTP inattendu: $http_code${NC}"
fi

echo ""

# ============================================================================
# RÉSUMÉ
# ============================================================================
echo "============================================================================"
echo -e "${BLUE}RÉSUMÉ DE LA VÉRIFICATION${NC}"
echo "============================================================================"
echo ""

# Recompter les tests réussis
total_checks=5
passed_checks=0

# Test 1: Fichiers
if ssh $SERVER 'grep -q "PAS DE PROXIES COMPLEXES" '$HTTPDOCS'/apps/competitions/views/competition_management_pro.py' 2>/dev/null; then
    ((passed_checks++))
fi

# Test 2: Cache
if ssh $SERVER 'test ! -d '$HTTPDOCS'/apps/competitions/views/__pycache__' 2>/dev/null; then
    ((passed_checks++))
fi

# Test 3: Données
data_check=$(ssh $SERVER << 'DATAEOF'
cd /var/www/vhosts/martialcomp.com/httpdocs
python3 << 'PYEOF'
import os, sys
sys.path.insert(0, '/var/www/vhosts/martialcomp.com/httpdocs')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'martialcomp.settings')

import django
django.setup()

from apps.competitions.models import CompetitionCategory

competition_id = 4
try:
    categories = CompetitionCategory.objects.filter(competition_id=competition_id)
    if categories.count() > 0:
        print("OK")
    else:
        print("KO")
except:
    print("ERROR")
PYEOF
DATAEOF
)

if echo "$data_check" | grep -q "OK"; then
    ((passed_checks++))
fi

# Test 4: HTTP
if [ "$http_code" = "200" ] || [ "$http_code" = "302" ]; then
    ((passed_checks++))
fi

# Test 5: Global
if [ $passed_checks -eq $total_checks ]; then
    ((passed_checks++))
fi

echo -e "Tests réussis: ${GREEN}$passed_checks/$total_checks${NC}"
echo ""

if [ $passed_checks -eq $total_checks ]; then
    echo -e "${GREEN}✓✓✓ TOUTES LES VÉRIFICATIONS SONT PASSÉES ✓✓✓${NC}"
    echo ""
    echo "La correction est correctement déployée et fonctionnelle."
    echo ""
    echo "Prochaines étapes:"
    echo "  1. Vider le cache de votre navigateur (Ctrl+F5)"
    echo "  2. Accéder à: $URL"
    echo "  3. Vérifier que les onglets affichent bien les données"
    exit 0
elif [ $passed_checks -ge 3 ]; then
    echo -e "${YELLOW}⚠ CERTAINES VÉRIFICATIONS ONT ÉCHOUÉ${NC}"
    echo ""
    echo "La correction est partiellement déployée."
    echo ""
    echo "Actions recommandées:"
    echo "  1. Vérifier les logs Django pour identifier les problèmes"
    echo "  2. Redéployer les fichiers si nécessaire"
    echo "  3. Vider le cache Python et redémarrer Apache"
    exit 1
else
    echo -e "${RED}✗✗✗ PLUSIEURS VÉRIFICATIONS ONT ÉCHOUÉ ✗✗✗${NC}"
    echo ""
    echo "La correction n'est pas correctement déployée."
    echo ""
    echo "Actions requises:"
    echo "  1. Consulter ANALYSE_ET_CORRECTION.md"
    echo "  2. Suivre le guide de déploiement manuel"
    echo "  3. Vérifier les logs Django pour les erreurs"
    echo "  4. Contacter le support si le problème persiste"
    exit 2
fi

echo ""
echo "============================================================================"
