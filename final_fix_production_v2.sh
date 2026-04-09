#!/bin/bash
# Script de correction finale

echo "=== CORRECTION FINALE DU SERVEUR ==="

ssh martialcomp-production << 'EOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1. Création d'un fichier Python correct..."
sudo python3 << 'PYTHON_FIX'
# Lire le fichier
with open('apps/competitions/views/competitions.py', 'r') as f:
    lines = f.readlines()

# Trouver et corriger la section problématique
for i in range(len(lines)):
    # Ligne 553 (index 552): from apps.competitions.models import CompetitionRegistration
    if i == 553 and lines[i].strip().startswith('try:'):
        # Le try doit avoir la même indentation que la ligne précédente
        lines[i] = 'try:\n'
    elif i == 554 and 'JudgeAssignment' in lines[i]:
        lines[i] = '    from apps.competitions.models import JudgeAssignment\n'
    elif i == 555 and lines[i].strip().startswith('except'):
        lines[i] = 'except ImportError:\n'
    elif i == 556 and 'JudgeAssignment = None' in lines[i]:
        lines[i] = '    JudgeAssignment = None\n'

# Écrire le fichier corrigé
with open('apps/competitions/views/competitions.py', 'w') as f:
    f.writelines(lines)

print("Fichier corrigé")
PYTHON_FIX

echo "2. Vérification de la correction..."
sed -n '550,560p' apps/competitions/views/competitions.py

echo "3. Permissions..."
sudo chown www-data:www-data apps/competitions/views/competitions.py

echo "4. Nettoyage complet..."
sudo find apps -name "*.pyc" -delete
sudo find apps -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

echo "5. Arrêt complet de gunicorn..."
sudo pkill -f gunicorn
sleep 3

echo "6. Redémarrage de gunicorn..."
cd /var/www/vhosts/martialcomp.com
sudo -u www-data /var/www/vhosts/martialcomp.com/venv/bin/gunicorn \
    --workers 3 \
    --bind 127.0.0.1:8888 \
    --access-logfile /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_access.log \
    --error-logfile /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_error.log \
    --log-level info \
    --chdir /var/www/vhosts/martialcomp.com/httpdocs \
    --daemon \
    config.wsgi:application

echo "7. Redémarrage d'Apache..."
sudo systemctl restart apache2

echo "✓ Serveur redémarré avec succès"
EOF

echo ""
echo "=== TERMINÉ ==="