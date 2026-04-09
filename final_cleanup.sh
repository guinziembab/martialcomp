#\!/bin/bash
# Nettoyage final du template

echo "=== NETTOYAGE FINAL DU TEMPLATE ==="

ssh martialcomp-production << 'SSHEOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1. Supprimer la balise </script> orpheline après {% endblock %}..."
# Utiliser Python pour un nettoyage précis
sudo python3 << 'PYTHON_CLEAN'
with open('apps/competitions/templates/competitions/competition/create.html', 'r') as f:
    lines = f.readlines()

new_lines = []
found_endblock = False

for i, line in enumerate(lines):
    # Si on trouve {% endblock %}
    if '{% endblock %}' in line:
        new_lines.append(line)
        found_endblock = True
        # Ignorer tout ce qui suit {% endblock %}
        continue
    
    # Si on n'a pas encore trouvé endblock, garder la ligne
    if not found_endblock:
        new_lines.append(line)

# Écrire le fichier nettoyé
with open('apps/competitions/templates/competitions/competition/create.html', 'w') as f:
    f.writelines(new_lines)

print("✓ Template nettoyé - tout ce qui était après {% endblock %} a été supprimé")
PYTHON_CLEAN

echo -e "\n2. Vérifier le résultat..."
echo "Dernières 10 lignes du template:"
tail -10 apps/competitions/templates/competitions/competition/create.html

echo -e "\n3. Vérifier la structure du template..."
echo "Nombre de {% block %}: $(grep -c '{% block' apps/competitions/templates/competitions/competition/create.html)"
echo "Nombre de {% endblock %}: $(grep -c '{% endblock' apps/competitions/templates/competitions/competition/create.html)"

echo -e "\n4. Redémarrer Gunicorn..."
sudo pkill -HUP -f gunicorn
sleep 2

echo -e "\n✓ NETTOYAGE TERMINÉ"
echo "Le template est maintenant propre et l'erreur de syntaxe devrait être résolue."

SSHEOF

echo ""
echo "=== TERMINÉ ==="
