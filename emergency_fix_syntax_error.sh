#!/bin/bash
# Script d'urgence pour corriger l'erreur de syntaxe

echo "=== CORRECTION D'URGENCE - ERREUR DE SYNTAXE ==="

ssh martialcomp-production << 'EOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1. Correction de l'erreur de syntaxe dans competitions.py..."
# Corriger l'erreur de syntaxe à la ligne 172
sudo python3 << 'PYTHON_FIX'
with open('apps/competitions/models/competitions.py', 'r') as f:
    lines = f.readlines()

# Chercher et corriger la ligne problématique autour de la ligne 172
for i in range(165, min(180, len(lines))):
    if i < len(lines):
        line = lines[i]
        # Compter les parenthèses
        if "field_name.endswith('_ar'))" in line:
            # Vérifier le contexte
            open_count = line.count('(')
            close_count = line.count(')')
            
            if close_count > open_count:
                # Retirer une parenthèse fermante en trop
                lines[i] = line.replace(')):', '):', 1)
                print(f"✓ Ligne {i+1} corrigée: parenthèse en trop retirée")
                break

# Écrire le fichier corrigé
with open('apps/competitions/models/competitions.py', 'w') as f:
    f.writelines(lines)

print("✓ Fichier corrigé")
PYTHON_FIX

echo "2. Vérification de la syntaxe Python..."
python3 -m py_compile apps/competitions/models/competitions.py && echo "✓ Syntaxe Python valide" || echo "✗ Erreur de syntaxe persistante"

echo "3. Redémarrage complet de Gunicorn..."
# Tuer tous les processus Gunicorn
sudo pkill -f gunicorn
sleep 2

# Redémarrer Gunicorn
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

echo "4. Vérification du statut..."
sleep 3
ps aux | grep gunicorn | grep -v grep
if [ $? -eq 0 ]; then
    echo "✓ Gunicorn redémarré avec succès"
else
    echo "✗ Gunicorn n'a pas pu redémarrer"
    echo "Vérification des logs..."
    tail -n 20 /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_error.log
fi

echo "5. Test de connectivité..."
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://127.0.0.1:8888/

EOF

echo ""
echo "=== TERMINÉ ==="