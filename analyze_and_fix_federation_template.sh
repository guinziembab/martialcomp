#\!/bin/bash
# Analyser et corriger le template federation.html

echo "================================================"
echo "🔍 ANALYSE DU TEMPLATE FEDERATION.HTML"
echo "================================================"
echo ""

# Copier le template localement pour analyse
cp apps/competitions/templates/competitions/dashboard/federation.html federation_dev.html

echo "1️⃣ Extraction de toutes les URLs du template..."
echo "=============================================="
# Extraire toutes les URLs
grep -o "{% url '[^']*'" federation_dev.html  < /dev/null |  sed "s/{% url '//g" | sed "s/'//g" | sort | uniq > urls_list.txt

echo "📋 URLs trouvées:"
cat urls_list.txt

echo ""
echo "2️⃣ Identification des URLs à corriger..."
echo "======================================"
# Créer le fichier de mapping des corrections
cat > url_mappings.py << 'PYEOF'
# Mapping des URLs à corriger
URL_MAPPINGS = {
    # URLs qui n'existent pas et doivent être remplacées
    'competitions:dashboard:create_competition': 'competitions:dashboard:federation_manage_competitions',
    'competitions:dashboard:clubs': 'competitions:dashboard:federation_manage_clubs',
    'competitions:dashboard:certifications': 'competitions:dashboard:federation_manage_certifications', 
    'competitions:dashboard:import_export': 'competitions:dashboard:federation_manage_settings',
    'competitions:dashboard:judges': 'competitions:dashboard:federation_manage_judges',
    'competitions:federations:create_competition': 'competitions:dashboard:federation_manage_competitions',
    'competitions:federations:clubs': 'competitions:dashboard:federation_manage_clubs',
    'competitions:federations:certifications': 'competitions:dashboard:federation_manage_certifications',
    'competitions:federations:import_export': 'competitions:dashboard:federation_manage_settings',
    'competitions:federations:judges': 'competitions:dashboard:federation_manage_judges',
}

# Analyser et corriger
import re

with open('federation_dev.html', 'r') as f:
    content = f.read()

corrections = 0
for old_url, new_url in URL_MAPPINGS.items():
    # Remplacer dans les tags {% url %}
    pattern = rf"{{% url ['\"]?{re.escape(old_url)}['\"]?"
    if re.search(pattern, content):
        # Avec arguments
        content = re.sub(
            rf"{{% url ['\"]?{re.escape(old_url)}['\"]?\s+",
            f"{{% url '{new_url}' ",
            content
        )
        # Sans arguments
        content = re.sub(
            rf"{{% url ['\"]?{re.escape(old_url)}['\"]?\s*%}}",
            f"{{% url '{new_url}' %}}",
            content
        )
        corrections += 1
        print(f"✅ Corrigé: {old_url} → {new_url}")

print(f"\n✅ Total: {corrections} corrections effectuées")

# Sauvegarder le fichier corrigé
with open('federation_fixed.html', 'w') as f:
    f.write(content)
PYEOF

python3 url_mappings.py

echo ""
echo "3️⃣ Vérification des URLs dans le fichier corrigé..."
echo "================================================="
echo "📋 URLs restantes potentiellement problématiques:"
grep -o "{% url '[^']*'" federation_fixed.html | sed "s/{% url '//g" | sed "s/'//g" | sort | uniq | grep -E "create_competition|clubs['\"]|certifications['\"]|import_export|judges['\"]" || echo "✅ Aucune URL problématique trouvée"

echo ""
echo "4️⃣ Vérification des vues manquantes dans dashboard.py..."
echo "======================================================"
# Vérifier quelles vues doivent être ajoutées
for view in federation_manage_competitions federation_manage_clubs federation_manage_certifications federation_manage_judges federation_manage_settings; do
    if grep -q "name='$view'" apps/competitions/urls/dashboard.py; then
        echo "✅ Vue '$view' existe"
    else
        echo "❌ Vue '$view' manquante - doit être ajoutée"
    fi
done

echo ""
echo "================================================"
echo "✅ ANALYSE TERMINÉE"
echo "================================================"
echo ""
echo "Fichier corrigé: federation_fixed.html"
