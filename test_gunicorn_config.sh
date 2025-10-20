#!/bin/bash

# =================================================================
# Script de Test de Configuration Gunicorn
# Pour vérifier que tout fonctionne après l'installation
# =================================================================

# Couleurs pour output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
VHOST_DIR="/var/www/vhosts/martialcomp.com"
HTTPDOCS_DIR="${VHOST_DIR}/httpdocs"
VENV_DIR="${VHOST_DIR}/venv"

echo "=============================================================="
echo -e "${BLUE}Test de Configuration Gunicorn MartialComp${NC}"
echo "=============================================================="
echo ""

# Test 1: Vérifier les fichiers critiques
echo -e "${BLUE}[TEST 1] Vérification des fichiers critiques${NC}"
echo ""

FILES_TO_CHECK=(
    "${HTTPDOCS_DIR}/start_gunicorn.sh"
    "${HTTPDOCS_DIR}/.env.production"
    "/etc/systemd/system/martialcomp.service"
    "/var/www/vhosts/system/martialcomp.com/conf/vhost_nginx.conf"
    "${VENV_DIR}/bin/gunicorn"
)

all_files_ok=true
for file in "${FILES_TO_CHECK[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file existe"
    else
        echo -e "${RED}✗${NC} $file manquant"
        all_files_ok=false
    fi
done

echo ""

# Test 2: Vérifier le service systemd
echo -e "${BLUE}[TEST 2] État du service systemd${NC}"
echo ""

if systemctl is-enabled martialcomp.service &>/dev/null; then
    echo -e "${GREEN}✓${NC} Service martialcomp.service activé"
else
    echo -e "${RED}✗${NC} Service martialcomp.service non activé"
fi

if systemctl is-active martialcomp.service &>/dev/null; then
    echo -e "${GREEN}✓${NC} Service martialcomp.service actif"
    
    # Afficher quelques infos du service
    echo ""
    echo "Statut du service:"
    systemctl status martialcomp.service --no-pager | head -15
else
    echo -e "${RED}✗${NC} Service martialcomp.service non actif"
fi

echo ""

# Test 3: Vérifier le port 8000
echo -e "${BLUE}[TEST 3] Vérification du port 8000${NC}"
echo ""

if ss -tlnp 2>/dev/null | grep -q ":8000"; then
    echo -e "${GREEN}✓${NC} Port 8000 en écoute"
    ss -tlnp 2>/dev/null | grep ":8000"
else
    echo -e "${RED}✗${NC} Port 8000 non en écoute"
fi

echo ""

# Test 4: Vérifier les processus Gunicorn
echo -e "${BLUE}[TEST 4] Processus Gunicorn${NC}"
echo ""

GUNICORN_COUNT=$(ps aux | grep "[g]unicorn.*config.wsgi:application" | wc -l)
if [ $GUNICORN_COUNT -gt 0 ]; then
    echo -e "${GREEN}✓${NC} $GUNICORN_COUNT processus Gunicorn trouvés"
    ps aux | grep "[g]unicorn.*config.wsgi:application" | head -5
else
    echo -e "${RED}✗${NC} Aucun processus Gunicorn trouvé"
fi

echo ""

# Test 5: Test HTTP
echo -e "${BLUE}[TEST 5] Test de connexion HTTP${NC}"
echo ""

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/ 2>/dev/null || echo "000")
if [[ "$HTTP_CODE" =~ ^(200|301|302|403)$ ]]; then
    echo -e "${GREEN}✓${NC} Réponse HTTP: $HTTP_CODE (OK)"
else
    echo -e "${RED}✗${NC} Réponse HTTP: $HTTP_CODE (Erreur)"
fi

# Test détaillé avec headers
echo ""
echo "Headers de réponse:"
curl -I -s http://127.0.0.1:8000/ 2>/dev/null | head -10 || echo "Erreur de connexion"

echo ""

# Test 6: Vérifier les logs
echo -e "${BLUE}[TEST 6] Vérification des logs${NC}"
echo ""

LOG_DIR="${HTTPDOCS_DIR}/logs"
if [ -d "$LOG_DIR" ]; then
    echo -e "${GREEN}✓${NC} Répertoire de logs existe"
    
    # Vérifier les fichiers de log
    for logfile in gunicorn.log gunicorn_access.log gunicorn_error.log; do
        if [ -f "$LOG_DIR/$logfile" ]; then
            size=$(ls -lh "$LOG_DIR/$logfile" | awk '{print $5}')
            echo "  - $logfile: $size"
        fi
    done
    
    # Afficher les dernières lignes d'erreur
    if [ -f "$LOG_DIR/gunicorn_error.log" ] && [ -s "$LOG_DIR/gunicorn_error.log" ]; then
        echo ""
        echo "Dernières erreurs Gunicorn:"
        tail -5 "$LOG_DIR/gunicorn_error.log"
    fi
else
    echo -e "${RED}✗${NC} Répertoire de logs manquant"
fi

echo ""

# Test 7: Vérifier .env.production
echo -e "${BLUE}[TEST 7] Configuration .env.production${NC}"
echo ""

if [ -f "${HTTPDOCS_DIR}/.env.production" ]; then
    # Vérifier les variables importantes
    required_vars=("DB_NAME" "DB_USER" "DJANGO_SECRET_KEY" "DJANGO_SETTINGS_MODULE")
    
    for var in "${required_vars[@]}"; do
        if grep -q "^${var}=" "${HTTPDOCS_DIR}/.env.production"; then
            # Vérifier si la valeur contient "CHANGEZ_MOI"
            if grep "^${var}=" "${HTTPDOCS_DIR}/.env.production" | grep -q "CHANGEZ_MOI"; then
                echo -e "${YELLOW}⚠${NC}  $var définie mais contient 'CHANGEZ_MOI'"
            else
                echo -e "${GREEN}✓${NC} $var définie"
            fi
        else
            echo -e "${RED}✗${NC} $var non définie"
        fi
    done
else
    echo -e "${RED}✗${NC} Fichier .env.production manquant"
fi

echo ""

# Test 8: Vérifier Django
echo -e "${BLUE}[TEST 8] Test Django${NC}"
echo ""

if [ -d "${VENV_DIR}" ] && [ -f "${HTTPDOCS_DIR}/manage.py" ]; then
    # Test rapide de Django
    cd "${HTTPDOCS_DIR}"
    export DJANGO_SETTINGS_MODULE=config.settings.production
    
    # Charger .env.production si existe
    if [ -f ".env.production" ]; then
        export $(grep -v '^#' .env.production | xargs) 2>/dev/null
    fi
    
    # Test check Django
    echo "Test Django check:"
    timeout 10 "${VENV_DIR}/bin/python" manage.py check --deploy 2>&1 | head -20 || echo "Timeout ou erreur Django"
else
    echo -e "${RED}✗${NC} Impossible de tester Django (venv ou manage.py manquant)"
fi

echo ""

# Résumé final
echo "=============================================================="
echo -e "${BLUE}RÉSUMÉ${NC}"
echo "=============================================================="

# Compter les succès et échecs
success_count=$(grep -c "✓" /tmp/test_output_$$ 2>/dev/null || echo "0")
error_count=$(grep -c "✗" /tmp/test_output_$$ 2>/dev/null || echo "0")
warning_count=$(grep -c "⚠" /tmp/test_output_$$ 2>/dev/null || echo "0")

echo ""

# Recommandations
if systemctl is-active martialcomp.service &>/dev/null && ss -tlnp 2>/dev/null | grep -q ":8000"; then
    echo -e "${GREEN}✓ Gunicorn semble fonctionner correctement${NC}"
else
    echo -e "${RED}✗ Problèmes détectés avec Gunicorn${NC}"
    echo ""
    echo "Actions recommandées:"
    echo "1. Vérifier les logs: journalctl -u martialcomp.service -f"
    echo "2. Vérifier .env.production"
    echo "3. Relancer le service: systemctl restart martialcomp.service"
fi

echo ""
echo "Pour plus de détails:"
echo "- Logs systemd: journalctl -u martialcomp.service -f"
echo "- Logs Gunicorn: tail -f ${HTTPDOCS_DIR}/logs/gunicorn*.log"
echo "- Diagnostic complet: ${HTTPDOCS_DIR}/diagnose_gunicorn.sh"
echo ""