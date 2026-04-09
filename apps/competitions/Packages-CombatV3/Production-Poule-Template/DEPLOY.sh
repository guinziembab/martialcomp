#!/bin/bash

# Script de déploiement pour le template poule professionnel
# MartialComp - Production

set -e  # Arrêter en cas d'erreur

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="/mnt/c/martial_hub_django/martialcomp"
BACKUP_DIR="${PROJECT_ROOT}/backups/$(date +%Y%m%d_%H%M%S)"
PACKAGE_DIR="${PROJECT_ROOT}/apps/competitions/Packages-CombatV3/Production-Poule-Template"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Déploiement Template Poule Professionnel${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "${PROJECT_ROOT}/manage.py" ]; then
    echo -e "${RED}Erreur: manage.py non trouvé. Vérifiez PROJECT_ROOT.${NC}"
    exit 1
fi

# Créer le répertoire de backup
echo -e "${YELLOW}📦 Création du répertoire de backup...${NC}"
mkdir -p "${BACKUP_DIR}"
echo -e "${GREEN}✓ Backup directory: ${BACKUP_DIR}${NC}"

# Sauvegarder les fichiers existants
echo ""
echo -e "${YELLOW}💾 Sauvegarde des fichiers existants...${NC}"

# Template detail_poule
if [ -f "${PROJECT_ROOT}/apps/competitions/templates/competitions/combat/detail_poule.html" ]; then
    cp "${PROJECT_ROOT}/apps/competitions/templates/competitions/combat/detail_poule.html" \
       "${BACKUP_DIR}/detail_poule.html.backup"
    echo -e "${GREEN}✓ detail_poule.html sauvegardé${NC}"
else
    echo -e "${YELLOW}⚠ detail_poule.html n'existe pas encore${NC}"
fi

# Template base
if [ -f "${PROJECT_ROOT}/apps/competitions/templates/competitions/combat/base.html" ]; then
    cp "${PROJECT_ROOT}/apps/competitions/templates/competitions/combat/base.html" \
       "${BACKUP_DIR}/base.html.backup"
    echo -e "${GREEN}✓ base.html sauvegardé${NC}"
else
    echo -e "${YELLOW}⚠ base.html n'existe pas encore${NC}"
fi

# Vue combat.py (sauvegarder seulement la fonction)
if [ -f "${PROJECT_ROOT}/apps/competitions/views/combat.py" ]; then
    cp "${PROJECT_ROOT}/apps/competitions/views/combat.py" \
       "${BACKUP_DIR}/combat.py.backup"
    echo -e "${GREEN}✓ combat.py sauvegardé${NC}"
else
    echo -e "${RED}✗ combat.py non trouvé${NC}"
    exit 1
fi

# Copier les nouveaux fichiers
echo ""
echo -e "${YELLOW}📋 Copie des nouveaux fichiers...${NC}"

# Template detail_poule
if [ -f "${PACKAGE_DIR}/templates/competitions/combat/detail_poule.html" ]; then
    cp "${PACKAGE_DIR}/templates/competitions/combat/detail_poule.html" \
       "${PROJECT_ROOT}/apps/competitions/templates/competitions/combat/detail_poule.html"
    chmod 644 "${PROJECT_ROOT}/apps/competitions/templates/competitions/combat/detail_poule.html"
    echo -e "${GREEN}✓ detail_poule.html déployé${NC}"
else
    echo -e "${RED}✗ detail_poule.html non trouvé dans le package${NC}"
    exit 1
fi

# Template base
if [ -f "${PACKAGE_DIR}/templates/competitions/combat/base.html" ]; then
    cp "${PACKAGE_DIR}/templates/competitions/combat/base.html" \
       "${PROJECT_ROOT}/apps/competitions/templates/competitions/combat/base.html"
    chmod 644 "${PROJECT_ROOT}/apps/competitions/templates/competitions/combat/base.html"
    echo -e "${GREEN}✓ base.html déployé${NC}"
else
    echo -e "${RED}✗ base.html non trouvé dans le package${NC}"
    exit 1
fi

# Mettre à jour la fonction detail_poule dans combat.py
echo ""
echo -e "${YELLOW}🔧 Mise à jour de la fonction detail_poule...${NC}"

if [ -f "${PACKAGE_DIR}/views/detail_poule_function.py" ]; then
    # Extraire la fonction du fichier
    python3 << EOF
import re
import sys

# Lire le fichier source
with open('${PROJECT_ROOT}/apps/competitions/views/combat.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Lire la nouvelle fonction
with open('${PACKAGE_DIR}/views/detail_poule_function.py', 'r', encoding='utf-8') as f:
    new_function = f.read()
    # Extraire seulement la fonction (sans les commentaires de début)
    new_function = re.sub(r'^#.*\n', '', new_function, flags=re.MULTILINE)
    new_function = new_function.strip()

# Trouver et remplacer l'ancienne fonction
pattern = r'@login_required\s+def detail_poule\(request, poule_id\):.*?return render\(request.*?\)\s+'
match = re.search(pattern, content, re.DOTALL)

if match:
    # Remplacer l'ancienne fonction
    content = content[:match.start()] + new_function + '\n\n' + content[match.end():]
    print("✓ Fonction detail_poule trouvée et remplacée")
else:
    # Si la fonction n'existe pas, l'ajouter avant modifier_poule
    modifier_pattern = r'(@login_required\s+def modifier_poule)'
    match = re.search(modifier_pattern, content)
    if match:
        content = content[:match.start()] + new_function + '\n\n' + content[match.start():]
        print("✓ Fonction detail_poule ajoutée")
    else:
        print("⚠ Impossible de trouver où insérer la fonction")
        sys.exit(1)

# Écrire le fichier modifié
with open('${PROJECT_ROOT}/apps/competitions/views/combat.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ combat.py mis à jour avec succès")
EOF

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Fonction detail_poule mise à jour${NC}"
    else
        echo -e "${RED}✗ Erreur lors de la mise à jour de la fonction${NC}"
        echo -e "${YELLOW}⚠ Vous devrez mettre à jour manuellement la fonction detail_poule${NC}"
    fi
else
    echo -e "${YELLOW}⚠ detail_poule_function.py non trouvé, mise à jour manuelle requise${NC}"
fi

# Vérifier les permissions
echo ""
echo -e "${YELLOW}🔐 Vérification des permissions...${NC}"
chmod 644 "${PROJECT_ROOT}/apps/competitions/templates/competitions/combat/detail_poule.html"
chmod 644 "${PROJECT_ROOT}/apps/competitions/templates/competitions/combat/base.html"
chmod 644 "${PROJECT_ROOT}/apps/competitions/views/combat.py"
echo -e "${GREEN}✓ Permissions configurées${NC}"

# Test de syntaxe Python
echo ""
echo -e "${YELLOW}🔍 Vérification de la syntaxe Python...${NC}"
python3 -m py_compile "${PROJECT_ROOT}/apps/competitions/views/combat.py" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Syntaxe Python valide${NC}"
else
    echo -e "${RED}✗ Erreur de syntaxe Python détectée${NC}"
    exit 1
fi

# Résumé
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Déploiement terminé avec succès !${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "📦 Backup créé dans : ${BACKUP_DIR}"
echo ""
echo -e "${YELLOW}⚠️  N'oubliez pas de :${NC}"
echo -e "   1. Redémarrer le serveur web/WSGI"
echo -e "   2. Tester l'accès à une page de poule"
echo -e "   3. Vérifier les statistiques et l'affichage"
echo ""
echo -e "${YELLOW}Pour restaurer les backups :${NC}"
echo -e "   cp ${BACKUP_DIR}/*.backup <destination>"
echo ""
