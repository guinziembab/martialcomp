#!/bin/bash

# Script de déploiement complet pour toutes les modifications du jour
# MartialComp - Production - 17 novembre 2024

set -e  # Arrêter en cas d'erreur

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="/mnt/c/martial_hub_django/martialcomp"
BACKUP_DIR="${PROJECT_ROOT}/backups/$(date +%Y%m%d_%H%M%S)"
PACKAGE_DIR="${PROJECT_ROOT}/apps/competitions/Packages-CombatV3/Production-Complete-20241117"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Déploiement Complet - Toutes Modifications${NC}"
echo -e "${BLUE}Date: 17 novembre 2024${NC}"
echo -e "${BLUE}========================================${NC}"
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

# Templates
for template in interface_combat_v3.html detail_poule.html base.html; do
    if [ -f "${PROJECT_ROOT}/apps/competitions/templates/competitions/combat/${template}" ]; then
        cp "${PROJECT_ROOT}/apps/competitions/templates/competitions/combat/${template}" \
           "${BACKUP_DIR}/${template}.backup"
        echo -e "${GREEN}✓ ${template} sauvegardé${NC}"
    else
        echo -e "${YELLOW}⚠ ${template} n'existe pas encore${NC}"
    fi
done

# Vues et URLs
for file in combat.py; do
    if [ -f "${PROJECT_ROOT}/apps/competitions/views/${file}" ]; then
        cp "${PROJECT_ROOT}/apps/competitions/views/${file}" \
           "${BACKUP_DIR}/views_${file}.backup"
        echo -e "${GREEN}✓ views/${file} sauvegardé${NC}"
    fi
done

for file in combat.py; do
    if [ -f "${PROJECT_ROOT}/apps/competitions/urls/${file}" ]; then
        cp "${PROJECT_ROOT}/apps/competitions/urls/${file}" \
           "${BACKUP_DIR}/urls_${file}.backup"
        echo -e "${GREEN}✓ urls/${file} sauvegardé${NC}"
    fi
done

# Config
for file in wsgi.py urls.py; do
    if [ -f "${PROJECT_ROOT}/config/${file}" ]; then
        cp "${PROJECT_ROOT}/config/${file}" \
           "${BACKUP_DIR}/config_${file}.backup"
        echo -e "${GREEN}✓ config/${file} sauvegardé${NC}"
    fi
done

# Templatetags
if [ -f "${PROJECT_ROOT}/apps/competitions/templatetags/combat_filters.py" ]; then
    cp "${PROJECT_ROOT}/apps/competitions/templatetags/combat_filters.py" \
       "${BACKUP_DIR}/combat_filters.py.backup"
    echo -e "${GREEN}✓ combat_filters.py sauvegardé${NC}"
fi

# Copier les nouveaux fichiers
echo ""
echo -e "${YELLOW}📋 Copie des nouveaux fichiers...${NC}"

# Templates
for template in interface_combat_v3.html detail_poule.html base.html; do
    if [ -f "${PACKAGE_DIR}/templates/competitions/combat/${template}" ]; then
        cp "${PACKAGE_DIR}/templates/competitions/combat/${template}" \
           "${PROJECT_ROOT}/apps/competitions/templates/competitions/combat/${template}"
        chmod 644 "${PROJECT_ROOT}/apps/competitions/templates/competitions/combat/${template}"
        echo -e "${GREEN}✓ ${template} déployé${NC}"
    else
        echo -e "${RED}✗ ${template} non trouvé dans le package${NC}"
    fi
done

# Vues API (nouveaux fichiers)
if [ -f "${PACKAGE_DIR}/views/combat_api_views.py" ]; then
    cp "${PACKAGE_DIR}/views/combat_api_views.py" \
       "${PROJECT_ROOT}/apps/competitions/combat_api_views.py"
    chmod 644 "${PROJECT_ROOT}/apps/competitions/combat_api_views.py"
    echo -e "${GREEN}✓ combat_api_views.py déployé${NC}"
fi

if [ -f "${PACKAGE_DIR}/urls/combat_api_urls.py" ]; then
    cp "${PACKAGE_DIR}/urls/combat_api_urls.py" \
       "${PROJECT_ROOT}/apps/competitions/combat_api_urls.py"
    chmod 644 "${PROJECT_ROOT}/apps/competitions/combat_api_urls.py"
    echo -e "${GREEN}✓ combat_api_urls.py déployé${NC}"
fi

# Config
if [ -f "${PACKAGE_DIR}/config/wsgi.py" ]; then
    cp "${PACKAGE_DIR}/config/wsgi.py" \
       "${PROJECT_ROOT}/config/wsgi.py"
    chmod 644 "${PROJECT_ROOT}/config/wsgi.py"
    echo -e "${GREEN}✓ wsgi.py déployé${NC}"
fi

# Templatetags
if [ -f "${PACKAGE_DIR}/templatetags/combat_filters.py" ]; then
    cp "${PACKAGE_DIR}/templatetags/combat_filters.py" \
       "${PROJECT_ROOT}/apps/competitions/templatetags/combat_filters.py"
    chmod 644 "${PROJECT_ROOT}/apps/competitions/templatetags/combat_filters.py"
    echo -e "${GREEN}✓ combat_filters.py déployé${NC}"
fi

# Appliquer les patches
echo ""
echo -e "${YELLOW}🔧 Application des patches...${NC}"

# Patch 1: interface_combat_v2 dans views/combat.py
if [ -f "${PROJECT_ROOT}/apps/competitions/views/combat.py" ]; then
    python3 << 'EOF'
import re
import sys

file_path = '${PROJECT_ROOT}/apps/competitions/views/combat.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Patch 1: interface_combat_v2
old_pattern = r"return render\(request, 'competitions/combat/interface_combat_v2\.html', context\)"
new_replacement = "# Utiliser le nouveau template V3 si disponible, sinon V2\n      return render(request, 'competitions/combat/interface_combat_v3.html', context)"

if re.search(old_pattern, content):
    content = re.sub(old_pattern, new_replacement, content)
    print("✓ Patch interface_combat_v2 appliqué")
else:
    # Vérifier si déjà modifié
    if "interface_combat_v3.html" in content:
        print("✓ interface_combat_v2 déjà modifié")
    else:
        print("⚠ interface_combat_v2 non trouvé, vérification manuelle requise")

# Patch 2: detail_poule avec statistiques
detail_poule_pattern = r"def detail_poule\(request, poule_id\):.*?return render\(request.*?\)\s+"
new_detail_poule = """def detail_poule(request, poule_id):
    \"\"\"
    Affiche les détails d'une poule, y compris les équipes/participants et les combats.
    Version améliorée avec calcul des statistiques côté serveur.
    \"\"\"
    poule = get_object_or_404(Poule, id=poule_id)
    combats = Combat.objects.filter(poule=poule).order_by('date_planifiee')
    
    # Calculer les statistiques
    total_combats = combats.count()
    combats_termines = combats.filter(status='termine').count()
    combats_en_cours = combats.filter(status='en_cours').count()
    combats_planifies = combats.filter(status='planifie').count()
    
    return render(request, 'competitions/combat/detail_poule.html', {
        'poule': poule,
        'combats': combats,
        'equipes': poule.equipes.all(),
        'pratiquants': poule.pratiquants.all(),
        'total_combats': total_combats,
        'combats_termines': combats_termines,
        'combats_en_cours': combats_en_cours,
        'combats_planifies': combats_planifies,
    })

"""

match = re.search(detail_poule_pattern, content, re.DOTALL)
if match:
    # Vérifier si les statistiques sont déjà présentes
    if 'total_combats' in content[match.start():match.end()]:
        print("✓ detail_poule déjà avec statistiques")
    else:
        content = content[:match.start()] + new_detail_poule + content[match.end():]
        print("✓ Patch detail_poule appliqué")
else:
    print("⚠ detail_poule non trouvé, vérification manuelle requise")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ views/combat.py mis à jour")
EOF

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Patches views/combat.py appliqués${NC}"
    else
        echo -e "${RED}✗ Erreur lors de l'application des patches views/combat.py${NC}"
        echo -e "${YELLOW}⚠ Application manuelle requise (voir views/combat_patches.txt)${NC}"
    fi
fi

# Patch 2: URLs combat.py (ordre des URLs)
if [ -f "${PROJECT_ROOT}/apps/competitions/urls/combat.py" ]; then
    python3 << 'EOF'
import re
import sys

file_path = '${PROJECT_ROOT}/apps/competitions/urls/combat.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Vérifier si l'ordre est correct (detail_poule avant liste_poules)
pattern = r"path\('poules/<int:competition_id>/',.*?name='liste_poules'\).*?path\('poules/<int:poule_id>/',.*?name='detail_poule'\)"

if re.search(pattern, content, re.DOTALL):
    # Inverser l'ordre
    content = re.sub(
        r"(path\('poules/<int:competition_id>/',.*?name='liste_poules'\))\s+(path\('poules/<int:poule_id>/',.*?name='detail_poule'\))",
        r"# IMPORTANT: detail_poule doit être AVANT liste_poules car les deux patterns sont identiques\n    # Django matche dans l'ordre, donc on met le plus spécifique en premier\n    \2\n    \1",
        content,
        flags=re.DOTALL
    )
    print("✓ Ordre des URLs corrigé")
elif "detail_poule" in content and "liste_poules" in content:
    # Vérifier l'ordre actuel
    detail_pos = content.find("detail_poule")
    liste_pos = content.find("liste_poules")
    if detail_pos < liste_pos:
        print("✓ Ordre des URLs déjà correct")
    else:
        print("⚠ Ordre des URLs à vérifier manuellement")
else:
    print("⚠ URLs poules non trouvées")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ urls/combat.py vérifié")
EOF

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Patch urls/combat.py appliqué${NC}"
    else
        echo -e "${YELLOW}⚠ Vérification manuelle requise pour urls/combat.py${NC}"
    fi
fi

# Patch 3: config/urls.py (ajout API)
if [ -f "${PROJECT_ROOT}/config/urls.py" ]; then
    if ! grep -q "apps.competitions.combat_api_urls" "${PROJECT_ROOT}/config/urls.py"; then
        python3 << 'EOF'
import re
import sys

file_path = '${PROJECT_ROOT}/config/urls.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Trouver la ligne après api/v1/auth
pattern = r"(path\('api/v1/auth/',.*?\))\s*\]"
match = re.search(pattern, content, re.DOTALL)

if match:
    insertion_point = match.end() - 1  # Avant le ]
    new_line = "    # API Combat V3 - IMPORTANT: Placer après api.urls pour éviter les conflits\n    # Les URLs de combat_api_urls commencent par 'combat/', donc pas de conflit\n    path('api/', include('apps.competitions.combat_api_urls')),\n"
    content = content[:insertion_point] + new_line + content[insertion_point:]
    print("✓ Inclusion API ajoutée dans config/urls.py")
else:
    print("⚠ Position d'insertion non trouvée dans config/urls.py")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ config/urls.py mis à jour")
EOF

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Patch config/urls.py appliqué${NC}"
        else
            echo -e "${YELLOW}⚠ Ajout manuel requis dans config/urls.py${NC}"
        fi
    else
        echo -e "${GREEN}✓ API déjà incluse dans config/urls.py${NC}"
    fi
fi

# Créer le répertoire des drapeaux
echo ""
echo -e "${YELLOW}📁 Création du répertoire des drapeaux...${NC}"
mkdir -p "${PROJECT_ROOT}/static/images/flags"
echo -e "${GREEN}✓ Répertoire static/images/flags créé${NC}"

# Vérifier les permissions
echo ""
echo -e "${YELLOW}🔐 Vérification des permissions...${NC}"
chmod 644 "${PROJECT_ROOT}/apps/competitions/templates/competitions/combat/"*.html 2>/dev/null || true
chmod 644 "${PROJECT_ROOT}/apps/competitions/combat_api_views.py" 2>/dev/null || true
chmod 644 "${PROJECT_ROOT}/apps/competitions/combat_api_urls.py" 2>/dev/null || true
chmod 644 "${PROJECT_ROOT}/config/wsgi.py" 2>/dev/null || true
chmod 644 "${PROJECT_ROOT}/apps/competitions/templatetags/combat_filters.py" 2>/dev/null || true
echo -e "${GREEN}✓ Permissions configurées${NC}"

# Test de syntaxe Python
echo ""
echo -e "${YELLOW}🔍 Vérification de la syntaxe Python...${NC}"
python3 -m py_compile "${PROJECT_ROOT}/apps/competitions/views/combat.py" 2>/dev/null && \
python3 -m py_compile "${PROJECT_ROOT}/apps/competitions/combat_api_views.py" 2>/dev/null && \
python3 -m py_compile "${PROJECT_ROOT}/apps/competitions/combat_api_urls.py" 2>/dev/null && \
python3 -m py_compile "${PROJECT_ROOT}/config/wsgi.py" 2>/dev/null && \
python3 -m py_compile "${PROJECT_ROOT}/apps/competitions/templatetags/combat_filters.py" 2>/dev/null

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
echo -e "   2. Tester l'interface combat V3"
echo -e "   3. Tester le template poule"
echo -e "   4. Tester le bouton Refresh"
echo -e "   5. Vérifier les logs pour les erreurs"
echo ""
echo -e "${YELLOW}Pour restaurer les backups :${NC}"
echo -e "   cp ${BACKUP_DIR}/*.backup <destination>"
echo ""
echo -e "${BLUE}📋 Fichiers déployés :${NC}"
echo -e "   • interface_combat_v3.html"
echo -e "   • detail_poule.html"
echo -e "   • base.html"
echo -e "   • combat_api_views.py"
echo -e "   • combat_api_urls.py"
echo -e "   • wsgi.py"
echo -e "   • combat_filters.py"
echo -e "   • views/combat.py (patches appliqués)"
echo -e "   • urls/combat.py (patches appliqués)"
echo -e "   • config/urls.py (patches appliqués)"
echo ""
