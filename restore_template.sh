#\!/bin/bash
# Restaurer le template depuis la sauvegarde

echo "=== RESTAURATION DU TEMPLATE ==="

ssh martialcomp-production << 'SSHEOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1. Lister les sauvegardes disponibles..."
ls -la apps/competitions/templates/competitions/competition/create.html.backup*  < /dev/null |  tail -5

echo -e "\n2. Restaurer depuis la sauvegarde la plus récente..."
# Trouver la sauvegarde la plus récente
latest_backup=$(ls -t apps/competitions/templates/competitions/competition/create.html.backup* | head -1)

if [ -f "$latest_backup" ]; then
    echo "Restauration depuis: $latest_backup"
    cp "$latest_backup" apps/competitions/templates/competitions/competition/create.html
    echo "✓ Template restauré"
else
    echo "✗ Aucune sauvegarde trouvée"
fi

echo -e "\n3. Appliquer une correction propre..."
# Maintenant corriger proprement le problème du script après endblock
sudo python3 << 'PYTHON_FIX'
with open('apps/competitions/templates/competitions/competition/create.html', 'r') as f:
    content = f.read()

# Chercher le dernier {% endblock %} qui correspond à {% block extra_js %}
# et s'assurer que rien ne vient après
parts = content.split('{% endblock %}')

if len(parts) > 2:
    # Garder seulement jusqu'au deuxième endblock (celui d'extra_js)
    # Le premier endblock ferme block title, le second ferme block extra_js
    cleaned = parts[0] + '{% endblock %}' + parts[1] + '{% endblock %}'
    
    # S'assurer qu'il n'y a pas de contenu après le dernier endblock
    cleaned = cleaned.rstrip() + '\n'
    
    with open('apps/competitions/templates/competitions/competition/create.html', 'w') as f:
        f.write(cleaned)
    
    print("✓ Template nettoyé correctement")
else:
    print("✓ Template déjà propre")

# Vérifier la structure finale
with open('apps/competitions/templates/competitions/competition/create.html', 'r') as f:
    content = f.read()
    blocks = content.count('{% block')
    endblocks = content.count('{% endblock')
    print(f"Blocks: {blocks}, Endblocks: {endblocks}")
    if blocks == endblocks:
        print("✓ Structure équilibrée")
PYTHON_FIX

echo -e "\n4. Vérifier les dernières lignes..."
tail -5 apps/competitions/templates/competitions/competition/create.html

echo -e "\n5. Redémarrer Gunicorn..."
sudo pkill -HUP -f gunicorn
sleep 2

echo -e "\n✓ RESTAURATION ET CORRECTION TERMINÉES"

SSHEOF

echo ""
echo "=== TERMINÉ ==="
