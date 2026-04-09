#!/bin/bash
# Vérifier les logs d'import
ssh martialcomp-production << 'EOF'
cd /var/www/vhosts/martialcomp.com/httpdocs
source /var/www/vhosts/martialcomp.com/venv/bin/activate

# Chercher les logs récents concernant l'import
echo "=== Logs Django récents ==="
tail -100 logs/django.log 2>/dev/null | grep -i "import\|en-tête\|header\|birth\|naissance\|error" | tail -30

echo ""
echo "=== Logs Gunicorn error ==="
tail -50 logs/gunicorn_error.log | tail -20

echo ""
echo "=== Test rapide du fichier import_export.py ==="
python -c "
from apps.competitions.views.club.import_export import import_practitioners_from_excel
print('Import module OK')
"
EOF
