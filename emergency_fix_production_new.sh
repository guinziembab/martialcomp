#!/bin/bash
# Script de correction d'urgence pour restaurer le serveur

echo "=== CORRECTION D'URGENCE - RESTAURATION DU SERVEUR ==="

ssh martialcomp-production << 'EOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1. Restauration depuis la sauvegarde..."
# Restaurer depuis la sauvegarde
sudo cp apps/competitions/views/competitions.py.backup_syntax_error apps/competitions/views/competitions.py

echo "2. Application du patch minimal..."
# Corriger uniquement la ligne problématique
sudo python3 << 'PYTHON_SCRIPT'
import re

# Lire le fichier
with open('apps/competitions/views/competitions.py', 'r') as f:
    content = f.read()

# Corriger la ligne 554 - l'import de JudgeAssignment doit être seul sur la ligne
content = re.sub(
    r'from apps\.competitions\.models import CompetitionRegistration\ntry:',
    r'from apps.competitions.models import CompetitionRegistration\n    try:',
    content
)

# S'assurer que la ligne 611 est bien indentée (4 espaces)
lines = content.split('\n')
for i, line in enumerate(lines):
    if i == 610 and line.strip().startswith('return render(request,'):
        # S'assurer qu'elle a exactement 4 espaces d'indentation
        lines[i] = '    ' + line.strip()

content = '\n'.join(lines)

# Écrire le fichier corrigé
with open('apps/competitions/views/competitions.py', 'w') as f:
    f.write(content)

print("Patch appliqué")
PYTHON_SCRIPT

echo "3. Correction des permissions..."
sudo chown www-data:www-data apps/competitions/views/competitions.py

echo "4. Nettoyage des fichiers compilés..."
sudo find apps/competitions -name "*.pyc" -delete
sudo rm -rf apps/competitions/__pycache__
sudo rm -rf apps/competitions/views/__pycache__

echo "5. Redémarrage complet de gunicorn..."
# Tuer tous les processus gunicorn
sudo pkill -f gunicorn

# Attendre un peu
sleep 2

# Redémarrer gunicorn
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

echo "6. Redémarrage d'Apache..."
sudo systemctl restart apache2

echo "✓ Serveur redémarré"
EOF

echo ""
echo "=== CORRECTION TERMINÉE ==="
echo "Le serveur devrait maintenant fonctionner."