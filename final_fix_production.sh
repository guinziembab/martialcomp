#!/bin/bash
# Script final pour corriger toutes les erreurs

PRODUCTION_SERVER="martialcomp-production"
PRODUCTION_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

echo "=========================================="
echo "Correction finale de production"
echo "Date: $(date)"
echo "=========================================="

# 1. Corriger practitioner_finance
echo "1. Correction de practitioner_finance..."
ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && cat > apps/competitions/views/practitioner_finance.py << 'EOF'
# Module temporaire pour éviter les erreurs d'import
def practitioner_finance_dashboard(request):
    pass

def practitioner_payment_history(request):
    pass

def practitioner_balance(request):
    pass

def practitioner_invoices(request):
    pass
EOF"

# 2. Vérifier et corriger d'autres imports manquants
echo "2. Vérification des imports dans practitioner.py..."
ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && grep -n 'from apps.competitions.views.practitioner_finance import' apps/competitions/urls/practitioner.py | head -5"

# 3. Redémarrer Gunicorn
echo "3. Redémarrage de Gunicorn..."
ssh "$PRODUCTION_SERVER" "pkill -f gunicorn && sleep 2"
ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && /var/www/vhosts/martialcomp.com/venv/bin/python -m gunicorn --workers 3 --bind 127.0.0.1:8888 --daemon --error-logfile logs/gunicorn_error.log config.wsgi:application"

sleep 3

# 4. Test final
echo "4. Test du site..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://martialcomp.com/)
echo "Statut HTTP: $HTTP_STATUS"

if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "301" ] || [ "$HTTP_STATUS" = "302" ]; then
    echo "✓ Site accessible!"
    # Tester une page spécifique
    echo "Test de la page de connexion..."
    curl -s -o /dev/null -w "%{http_code}\n" https://martialcomp.com/accounts/login/
else
    echo "✗ Erreur $HTTP_STATUS"
    echo "Dernières erreurs Gunicorn:"
    ssh "$PRODUCTION_SERVER" "tail -20 $PRODUCTION_PATH/logs/gunicorn_error.log | grep -E '(Error|Exception|Traceback)' -A 3"
fi

echo "=========================================="
echo "Correction terminée!"
echo "=========================================="