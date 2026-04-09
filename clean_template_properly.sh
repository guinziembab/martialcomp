#\!/bin/bash
# Nettoyer proprement le template

echo "=== NETTOYAGE PROPRE DU TEMPLATE ==="

ssh martialcomp-production << 'SSHEOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1. Vérifier où se trouve {% endblock %} dans le template..."
grep -n "{% endblock %}" apps/competitions/templates/competitions/competition/create.html  < /dev/null |  tail -5

echo -e "\n2. Vérifier s'il y a du contenu après le dernier {% endblock %}..."
# Trouver la dernière ligne avec {% endblock %}
last_endblock_line=$(grep -n "{% endblock %}" apps/competitions/templates/competitions/competition/create.html | tail -1 | cut -d: -f1)
total_lines=$(wc -l < apps/competitions/templates/competitions/competition/create.html)

echo "Dernier {% endblock %} à la ligne: $last_endblock_line"
echo "Nombre total de lignes: $total_lines"

if [ "$last_endblock_line" -lt "$total_lines" ]; then
    echo "⚠️ Il y a du contenu après {% endblock %} \!"
    echo "Contenu après endblock:"
    sed -n "${last_endblock_line},$((last_endblock_line + 20))p" apps/competitions/templates/competitions/competition/create.html
    
    echo -e "\n3. Supprimer le contenu après {% endblock %}..."
    # Garder seulement jusqu'au dernier endblock
    head -n "$last_endblock_line" apps/competitions/templates/competitions/competition/create.html > /tmp/create_cleaned.html
    mv /tmp/create_cleaned.html apps/competitions/templates/competitions/competition/create.html
    echo "✓ Contenu après {% endblock %} supprimé"
else
    echo "✓ Pas de contenu après {% endblock %}"
fi

echo -e "\n4. Vérifier aussi base.html pour les erreurs de syntaxe..."
# Chercher les scripts mal formés dans base.html
grep -n "<script>" apps/competitions/templates/base.html | tail -10

echo -e "\n5. Corriger les scripts dans base.html si nécessaire..."
sudo python3 << 'PYTHON_BASE'
with open('apps/competitions/templates/base.html', 'r') as f:
    content = f.read()

# Compter les balises script
open_scripts = content.count('<script')
close_scripts = content.count('</script>')

print(f"Balises <script>: {open_scripts}")
print(f"Balises </script>: {close_scripts}")

if open_scripts \!= close_scripts:
    print("⚠️ Déséquilibre dans les balises script\!")
    
    # Chercher les scripts mal fermés
    lines = content.split('\n')
    script_depth = 0
    for i, line in enumerate(lines):
        if '<script' in line:
            script_depth += 1
        if '</script>' in line:
            script_depth -= 1
        if script_depth < 0:
            print(f"Balise </script> orpheline ligne {i+1}")
else:
    print("✓ Balises script équilibrées")
PYTHON_BASE

echo -e "\n6. Redémarrer Gunicorn..."
sudo pkill -HUP -f gunicorn
sleep 2

echo -e "\n✓ NETTOYAGE TERMINÉ"

SSHEOF

echo ""
echo "=== TERMINÉ ==="
