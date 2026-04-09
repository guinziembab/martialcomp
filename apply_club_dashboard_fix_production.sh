#!/bin/bash
# Script pour appliquer les corrections directement en production via SSH
# Corrections :
# 1. Déplacer now de la ligne 296 à la ligne 158
# 2. Initialiser club_organization = None à la ligne 161
# 3. Supprimer la définition dupliquée de now

echo "=== Application des corrections en production ==="
echo ""

REMOTE_USER="pierrep99"
REMOTE_HOST="martialcomp.com"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
FILE_PATH="$REMOTE_PATH/apps/competitions/views/dashboard/club.py"

echo "Connexion à la production..."
echo "Fichier à corriger: $FILE_PATH"
echo ""

# Se connecter et appliquer les corrections
ssh "$REMOTE_USER@$REMOTE_HOST" << 'ENDSSH'
cd /var/www/vhosts/martialcomp.com/httpdocs
FILE="apps/competitions/views/dashboard/club.py"

echo "Sauvegarde du fichier original..."
cp "$FILE" "${FILE}.backup_$(date +%Y%m%d_%H%M%S)"

echo "Vérification de l'état actuel du fichier..."
if grep -q "^    now = timezone.now().date()" "$FILE"; then
    echo "✓ La variable now est déjà définie"
    NOW_LINE=$(grep -n "^    now = timezone.now().date()" "$FILE" | head -1 | cut -d: -f1)
    echo "  Trouvée à la ligne $NOW_LINE"
else
    echo "✗ La variable now n'est pas trouvée"
fi

if grep -q "^    club_organization = None" "$FILE"; then
    echo "✓ club_organization est déjà initialisé"
    CLUB_ORG_LINE=$(grep -n "^    club_organization = None" "$FILE" | head -1 | cut -d: -f1)
    echo "  Trouvée à la ligne $CLUB_ORG_LINE"
else
    echo "✗ club_organization n'est pas initialisé"
fi

echo ""
echo "Application des corrections..."

# Créer un script Python temporaire pour appliquer les corrections
python3 << 'ENDPYTHON'
import re

file_path = "apps/competitions/views/dashboard/club.py"

# Lire le fichier
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Vérifier si now est déjà à la ligne 158 (après le log du club)
# Chercher la ligne avec "logger.info(f\"Club:"
log_line = None
for i, line in enumerate(lines):
    if 'logger.info(f"Club:' in line or 'logger.info(f\'Club:' in line:
        log_line = i
        break

# Si now n'est pas déjà après le log, le déplacer
if log_line:
    # Chercher toutes les définitions de now
    now_definitions = []
    for i, line in enumerate(lines):
        if re.match(r'^\s+now\s*=\s*timezone\.now\(\)\.date\(\)', line):
            now_definitions.append(i)
    
    # Si now n'est pas à la ligne log_line + 3 (158), le déplacer
    target_line = log_line + 3  # Après le log, ligne vide, commentaire
    
    if now_definitions:
        # Supprimer toutes les définitions existantes de now
        for line_num in reversed(now_definitions):
            if line_num != target_line - 1:  # -1 car index 0-based
                del lines[line_num]
        
        # Insérer now à la position cible
        if target_line - 1 < len(lines):
            # Vérifier si now n'est pas déjà là
            if not re.match(r'^\s+now\s*=\s*timezone\.now\(\)\.date\(\)', lines[target_line - 1]):
                lines.insert(target_line - 1, "    now = timezone.now().date()\n")
                lines.insert(target_line, "\n")  # Ligne vide après

# Vérifier si club_organization est initialisé après now
# Chercher la ligne avec now
now_line = None
for i, line in enumerate(lines):
    if re.match(r'^\s+now\s*=\s*timezone\.now\(\)\.date\(\)', line):
        now_line = i
        break

if now_line:
    # Vérifier si club_organization = None est à la ligne suivante
    target_org_line = now_line + 2  # Après now et ligne vide
    
    if target_org_line < len(lines):
        if not re.match(r'^\s+club_organization\s*=\s*None', lines[target_org_line]):
            # Insérer club_organization = None
            lines.insert(target_org_line, "    club_organization = None\n")
            lines.insert(target_org_line + 1, "\n")  # Ligne vide après

# Écrire le fichier corrigé
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✓ Corrections appliquées")
ENDPYTHON

echo ""
echo "Vérification des corrections..."
if grep -q "^    now = timezone.now().date()" "$FILE"; then
    NOW_LINE=$(grep -n "^    now = timezone.now().date()" "$FILE" | head -1 | cut -d: -f1)
    echo "✓ now défini à la ligne $NOW_LINE"
fi

if grep -q "^    club_organization = None" "$FILE"; then
    CLUB_ORG_LINE=$(grep -n "^    club_organization = None" "$FILE" | head -1 | cut -d: -f1)
    echo "✓ club_organization initialisé à la ligne $CLUB_ORG_LINE"
fi

echo ""
echo "Redémarrage de Gunicorn..."
sudo systemctl reload gunicorn
if [ $? -eq 0 ]; then
    echo "✓ Gunicorn redémarré avec succès"
else
    echo "✗ Erreur lors du redémarrage de Gunicorn"
fi

ENDSSH

echo ""
echo "=== Corrections appliquées en production ==="
echo ""
echo "Vérifiez que la page https://martialcomp.com/fr/competitions/dashboard/club/ fonctionne maintenant"
