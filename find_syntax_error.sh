#\!/bin/bash
# Trouver l'erreur de syntaxe exacte

echo "=== RECHERCHE ERREUR DE SYNTAXE ==="

ssh martialcomp-production << 'SSHEOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1. Extraire tout le JavaScript après 'Types filtrés avec succès'..."
# Chercher le contexte après cette ligne
awk '/Types filtrés avec succès/,/<\/script>/' apps/competitions/templates/competitions/competition/create.html  < /dev/null |  head -50

echo "2. Vérifier s'il y a des template tags Django mal fermés..."
grep -n "{{.*[^}]$\|{%.*[^%]$" apps/competitions/templates/competitions/competition/create.html | head -10

echo "3. Chercher des erreurs de syntaxe spécifiques..."
# Créer un script Python pour une analyse plus précise
python3 << 'PYTHON_CHECK'
import re

with open('apps/competitions/templates/competitions/competition/create.html', 'r') as f:
    lines = f.readlines()

# Chercher la ligne avec "Types filtrés"
for i, line in enumerate(lines):
    if 'Types filtrés avec succès' in line:
        # Examiner les 100 lignes suivantes
        print(f"Trouvé à la ligne {i+1}")
        print("Contexte des 30 lignes suivantes:")
        for j in range(i, min(i+30, len(lines))):
            line_content = lines[j].rstrip()
            # Détecter les problèmes potentiels
            if '{{' in line_content or '{%' in line_content:
                print(f"L{j+1} [TEMPLATE]: {line_content}")
            elif re.search(r'[^\\]".*[^\\]".*[^\\]"', line_content):
                print(f"L{j+1} [QUOTES?]: {line_content}")
            elif line_content.strip() and (
                line_content.strip()[-1] in ',;' and 
                j+1 < len(lines) and 
                lines[j+1].strip().startswith('}')
            ):
                print(f"L{j+1} [TRAILING]: {line_content}")
            else:
                print(f"L{j+1}: {line_content}")
        break

print("\n4. Recherche de caractères non-ASCII ou invisibles...")
with open('apps/competitions/templates/competitions/competition/create.html', 'rb') as f:
    content = f.read()
    
# Chercher les caractères non-printables
for i, byte in enumerate(content):
    if byte > 127 or (byte < 32 and byte not in [9, 10, 13]):  # Non-ASCII ou contrôle
        context_start = max(0, i-20)
        context_end = min(len(content), i+20)
        print(f"Caractère suspect à la position {i}: {byte} (0x{byte:02x})")
        print(f"Contexte: ...{content[context_start:context_end]}...")
        if i > 50000:  # Limiter la recherche
            break
PYTHON_CHECK

echo "5. Solution temporaire - Commenter le code problématique..."
# Identifier et commenter la partie problématique
sudo python3 << 'PYTHON_FIX'
with open('apps/competitions/templates/competitions/competition/create.html', 'r') as f:
    content = f.read()

# Sauvegarder l'original
with open('apps/competitions/templates/competitions/competition/create.html.backup_syntax', 'w') as f:
    f.write(content)

# Chercher et corriger les erreurs courantes
# 1. Supprimer les virgules finales avant }
content = re.sub(r',(\s*\})', r'\1', content)

# 2. Vérifier les template tags non fermés
# Cela nécessite une analyse plus complexe...

with open('apps/competitions/templates/competitions/competition/create.html', 'w') as f:
    f.write(content)

print("✓ Corrections basiques appliquées")
PYTHON_FIX

echo "6. Redémarrer pour appliquer les changements..."
sudo pkill -HUP -f gunicorn

SSHEOF

echo ""
echo "=== ANALYSE TERMINÉE ==="
