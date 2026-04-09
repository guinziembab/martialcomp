#\!/bin/bash
# Débugger l'erreur exacte ligne 1780

echo "=== DEBUG ERREUR EXACTE LIGNE 1780 ==="

ssh martialcomp-production << 'SSHEOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1. Visualiser la page rendue pour voir la ligne 1780..."
# Générer une version du HTML rendu
curl -s "https://martialcomp.com/fr/competitions/competitions/4/update/"  < /dev/null |  sed -n '1770,1790p' | cat -n

echo -e "\n2. Vérifier le template actuel..."
echo "État du template après nos modifications:"
sed -n '1055,1065p' apps/competitions/templates/competitions/competition/create.html

echo -e "\n3. Rechercher tous les endroits où il pourrait y avoir une erreur..."
# Chercher des patterns suspects dans tout le template
grep -n "console\.log\|</script>\|<script" apps/competitions/templates/competitions/competition/create.html | tail -20

echo -e "\n4. Vérifier s'il y a des scripts inline dans le HTML..."
# Parfois l'erreur vient de scripts inline dans des attributs HTML
grep -n "onclick\|onchange\|javascript:" apps/competitions/templates/competitions/competition/create.html | head -10

echo -e "\n5. Créer un fichier de debug pour capturer le HTML rendu..."
cat > /tmp/capture_rendered.py << 'PYTHON'
import requests
from bs4 import BeautifulSoup

# Capturer le HTML rendu
response = requests.get("http://127.0.0.1:8888/fr/competitions/competitions/4/update/")
if response.status_code == 200:
    lines = response.text.split('\n')
    # Afficher les lignes autour de 1780
    for i in range(max(0, 1775), min(len(lines), 1785)):
        print(f"{i+1}: {lines[i]}")
else:
    print(f"Erreur: {response.status_code}")
PYTHON

# Exécuter localement sur le serveur
python3 /tmp/capture_rendered.py 2>/dev/null || echo "Impossible de capturer le HTML rendu"

SSHEOF

echo ""
echo "=== ANALYSE TERMINÉE ==="
