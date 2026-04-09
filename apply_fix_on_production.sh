#!/bin/bash
# Script à exécuter DIRECTEMENT sur le serveur de production
# Usage: ssh pierrep99@martialcomp.com 'bash -s' < apply_fix_on_production.sh

echo "=== Application des corrections sur le serveur de production ==="
echo ""

cd /var/www/vhosts/martialcomp.com/httpdocs
FILE="apps/competitions/views/dashboard/club.py"

# Sauvegarder le fichier original
echo "Sauvegarde du fichier original..."
cp "$FILE" "${FILE}.backup_$(date +%Y%m%d_%H%M%S)"

# Vérifier l'état actuel
echo "Vérification de l'état actuel..."
NOW_LINE=$(grep -n "^    now = timezone.now().date()" "$FILE" | head -1 | cut -d: -f1)
CLUB_ORG_LINE=$(grep -n "^    club_organization = None" "$FILE" | head -1 | cut -d: -f1)

if [ -n "$NOW_LINE" ]; then
    echo "✓ now trouvé à la ligne $NOW_LINE"
else
    echo "✗ now non trouvé"
fi

if [ -n "$CLUB_ORG_LINE" ]; then
    echo "✓ club_organization trouvé à la ligne $CLUB_ORG_LINE"
else
    echo "✗ club_organization non trouvé"
fi

# Appliquer les corrections avec Python
echo ""
echo "Application des corrections..."
python3 << 'ENDPYTHON'
import re
import sys

file_path = "apps/competitions/views/dashboard/club.py"

try:
    # Lire le fichier
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Trouver la ligne avec le log du club
    log_line = None
    for i, line in enumerate(lines):
        if 'logger.info(f"Club:' in line or "logger.info(f'Club:" in line:
            log_line = i
            break
    
    if log_line is None:
        print("ERREUR: Ligne de log du club non trouvée")
        sys.exit(1)
    
    # Vérifier si now est déjà après le log (ligne 158 environ)
    target_now_line = log_line + 3  # Après log, ligne vide, commentaire
    
    # Chercher toutes les définitions de now
    now_positions = []
    for i, line in enumerate(lines):
        if re.match(r'^\s+now\s*=\s*timezone\.now\(\)\.date\(\)', line):
            now_positions.append(i)
    
    # Si now n'est pas à la position cible, le déplacer
    needs_fix = True
    if now_positions and now_positions[0] == target_now_line - 1:
        needs_fix = False
    
    if needs_fix:
        # Supprimer toutes les définitions existantes de now
        for pos in reversed(now_positions):
            if pos != target_now_line - 1:  # Garder celle à la position cible si elle existe
                del lines[pos]
        
        # Insérer now à la position cible si elle n'existe pas
        if target_now_line - 1 >= len(lines) or not re.match(r'^\s+now\s*=\s*timezone\.now\(\)\.date\(\)', lines[target_now_line - 1]):
            # Insérer après le log
            insert_pos = log_line + 2  # Après log et ligne vide
            lines.insert(insert_pos, "    # Date actuelle pour les calculs - DÉPLACÉ ICI POUR ÉVITER L'ERREUR\n")
            lines.insert(insert_pos + 1, "    now = timezone.now().date()\n")
            lines.insert(insert_pos + 2, "\n")
    
    # Vérifier si club_organization est initialisé après now
    now_line = None
    for i, line in enumerate(lines):
        if re.match(r'^\s+now\s*=\s*timezone\.now\(\)\.date\(\)', line):
            now_line = i
            break
    
    if now_line is not None:
        target_org_line = now_line + 2  # Après now et ligne vide
        
        # Vérifier si club_organization = None existe déjà
        org_exists = False
        for i in range(max(0, now_line), min(len(lines), now_line + 5)):
            if re.match(r'^\s+club_organization\s*=\s*None', lines[i]):
                org_exists = True
                break
        
        if not org_exists:
            # Insérer club_organization = None
            lines.insert(now_line + 2, "    # Initialiser club_organization\n")
            lines.insert(now_line + 3, "    club_organization = None\n")
            lines.insert(now_line + 4, "\n")
    
    # Écrire le fichier corrigé
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("✓ Corrections appliquées avec succès")
    
except Exception as e:
    print(f"ERREUR lors de l'application des corrections: {e}")
    sys.exit(1)
ENDPYTHON

if [ $? -eq 0 ]; then
    echo ""
    echo "Vérification des corrections appliquées..."
    NOW_LINE=$(grep -n "^    now = timezone.now().date()" "$FILE" | head -1 | cut -d: -f1)
    CLUB_ORG_LINE=$(grep -n "^    club_organization = None" "$FILE" | head -1 | cut -d: -f1)
    
    if [ -n "$NOW_LINE" ]; then
        echo "✓ now défini à la ligne $NOW_LINE"
    fi
    
    if [ -n "$CLUB_ORG_LINE" ]; then
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
    
    echo ""
    echo "=== Corrections appliquées avec succès ==="
    echo "Vérifiez que la page https://martialcomp.com/fr/competitions/dashboard/club/ fonctionne maintenant"
else
    echo ""
    echo "✗ Erreur lors de l'application des corrections"
    exit 1
fi
