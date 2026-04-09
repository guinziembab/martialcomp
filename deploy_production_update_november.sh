#!/bin/bash
# Script de déploiement pour aligner la production avec les mises à jour depuis le 1er novembre 2024
# Ce script crée un package de mise à jour avec tous les fichiers essentiels modifiés

set -e

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="/mnt/c/martial_hub_django/martialcomp"
PACKAGE_DIR="production_update_november_$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="backup_production_$(date +%Y%m%d_%H%M%S)"
FILES_LIST="/tmp/files_essential.txt"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Package de mise à jour Production${NC}"
echo -e "${GREEN}Mises à jour depuis le 1er novembre 2024${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Vérifier que nous sommes dans le bon répertoire
if [ ! -d "$PROJECT_ROOT" ]; then
    echo -e "${RED}Erreur: Le répertoire du projet n'existe pas: $PROJECT_ROOT${NC}"
    exit 1
fi

cd "$PROJECT_ROOT"

# Créer le répertoire du package
echo -e "${YELLOW}Création du répertoire du package...${NC}"
mkdir -p "$PACKAGE_DIR"
mkdir -p "$PACKAGE_DIR/apps/competitions"

# Créer la liste des fichiers essentiels si elle n'existe pas
if [ ! -f "$FILES_LIST" ]; then
    echo -e "${YELLOW}Génération de la liste des fichiers essentiels...${NC}"
    git log --since="2024-11-01" --name-only --pretty=format: --diff-filter=AM | \
        grep -E "^apps/competitions/(forms|models|views|urls|templates|utils|templatetags)" | \
        grep -v "backup" | grep -v "\.py\.py$" | grep -v "\.backup" | \
        grep -v "_fix\.py$" | grep -v "_fixed\.py$" | grep -v "Backup" | \
        grep -v "copy\.py$" | grep -v "emergency\.py$" | grep -v "corrupted\.py$" | \
        grep -v "urls_bak" | grep -v "coach_forms_fix" | sort -u > "$FILES_LIST"
fi

# Compter les fichiers
FILE_COUNT=$(wc -l < "$FILES_LIST")
echo -e "${GREEN}Nombre de fichiers à inclure: $FILE_COUNT${NC}\n"

# Copier les fichiers dans le package
echo -e "${YELLOW}Copie des fichiers dans le package...${NC}"
COPIED=0
SKIPPED=0

while IFS= read -r file; do
    if [ -f "$file" ]; then
        # Créer le répertoire de destination si nécessaire
        dir=$(dirname "$PACKAGE_DIR/$file")
        mkdir -p "$dir"
        
        # Copier le fichier
        cp "$file" "$PACKAGE_DIR/$file"
        ((COPIED++))
        echo -e "  ${GREEN}✓${NC} $file"
    else
        echo -e "  ${YELLOW}⚠${NC} Fichier non trouvé: $file"
        ((SKIPPED++))
    fi
done < "$FILES_LIST"

echo -e "\n${GREEN}Fichiers copiés: $COPIED${NC}"
echo -e "${YELLOW}Fichiers ignorés: $SKIPPED${NC}\n"

# Créer un fichier de manifest
echo -e "${YELLOW}Création du manifest...${NC}"
cat > "$PACKAGE_DIR/MANIFEST.txt" << EOF
Package de mise à jour Production
Date de création: $(date)
Mises à jour depuis: 1er novembre 2024
Nombre de fichiers: $COPIED

Fichiers inclus:
EOF
cat "$FILES_LIST" >> "$PACKAGE_DIR/MANIFEST.txt"

# Créer un script de déploiement pour la production
echo -e "${YELLOW}Création du script de déploiement...${NC}"
cat > "$PACKAGE_DIR/deploy_to_production.sh" << 'DEPLOY_SCRIPT'
#!/bin/bash
# Script de déploiement sur le serveur de production
# À exécuter sur le serveur de production

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration - À ADAPTER selon votre environnement de production
PROJECT_ROOT="/path/to/production/martialcomp"  # MODIFIER ICI
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Déploiement sur la production${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Vérifier que nous sommes dans le bon répertoire
if [ ! -d "$PROJECT_ROOT" ]; then
    echo -e "${RED}Erreur: Le répertoire du projet n'existe pas: $PROJECT_ROOT${NC}"
    exit 1
fi

cd "$PROJECT_ROOT"

# Créer un backup
echo -e "${YELLOW}Création d'un backup...${NC}"
mkdir -p "../$BACKUP_DIR"

# Backup des fichiers qui seront remplacés
while IFS= read -r file; do
    if [ -f "$file" ]; then
        dir=$(dirname "../$BACKUP_DIR/$file")
        mkdir -p "$dir"
        cp "$file" "../$BACKUP_DIR/$file"
    fi
done < MANIFEST.txt

echo -e "${GREEN}Backup créé dans: ../$BACKUP_DIR${NC}\n"

# Copier les fichiers du package
echo -e "${YELLOW}Copie des fichiers de mise à jour...${NC}"
COPIED=0

while IFS= read -r file; do
    if [ -f "$file" ]; then
        dir=$(dirname "$file")
        mkdir -p "$dir"
        cp "$file" "$PROJECT_ROOT/$file"
        ((COPIED++))
        echo -e "  ${GREEN}✓${NC} $file"
    fi
done < MANIFEST.txt

echo -e "\n${GREEN}Fichiers déployés: $COPIED${NC}\n"

# Instructions post-déploiement
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Étapes post-déploiement:${NC}"
echo -e "${YELLOW}========================================${NC}"
echo -e "1. Vérifier les permissions des fichiers"
echo -e "2. Exécuter les migrations si nécessaire: python manage.py migrate"
echo -e "3. Collecter les fichiers statiques: python manage.py collectstatic --noinput"
echo -e "4. Redémarrer l'application (gunicorn/uwsgi/etc.)"
echo -e "5. Vérifier les logs pour détecter d'éventuelles erreurs"
echo -e "\n${GREEN}Déploiement terminé!${NC}"
DEPLOY_SCRIPT

chmod +x "$PACKAGE_DIR/deploy_to_production.sh"

# Créer un fichier README
echo -e "${YELLOW}Création du README...${NC}"
cat > "$PACKAGE_DIR/README.md" << 'README'
# Package de mise à jour Production - Novembre 2024

Ce package contient tous les fichiers essentiels de l'application "Compétitions" modifiés depuis le 1er novembre 2024.

## Contenu

- **Forms**: Formulaires modifiés (combat_forms.py, practitioners.py, standalone_scoring.py, etc.)
- **Models**: Modèles modifiés (combat.py, etc.)
- **Views**: Vues modifiées (club/, dashboard/, combat.py, etc.)
- **URLs**: Routes modifiées (__init__.py, club.py, combat.py, dashboard.py, etc.)
- **Templates**: Templates HTML modifiés
- **Utils**: Utilitaires modifiés (decorators.py, permission_helpers.py, custom_filters.py, etc.)

## Fichiers exclus

Les fichiers suivants ont été exclus du package:
- Fichiers de backup (*.backup, *_backup, Backup/)
- Fichiers de correction (*_fix.py, *_fixed.py)
- Fichiers d'urgence (*_emergency.py)
- Fichiers corrompus (*_corrupted.py)
- Fichiers de copie (* copy.py)
- Fichiers .py.py (doublons)

## Installation

1. Transférer le package sur le serveur de production
2. Extraire le package dans un répertoire temporaire
3. Modifier le script `deploy_to_production.sh` pour pointer vers le bon répertoire de production
4. Exécuter le script de déploiement:
   ```bash
   cd production_update_november_YYYYMMDD_HHMMSS
   ./deploy_to_production.sh
   ```

## Post-déploiement

1. Vérifier les permissions des fichiers
2. Exécuter les migrations si nécessaire:
   ```bash
   python manage.py migrate
   ```
3. Collecter les fichiers statiques:
   ```bash
   python manage.py collectstatic --noinput
   ```
4. Redémarrer l'application (gunicorn/uwsgi/etc.)
5. Vérifier les logs pour détecter d'éventuelles erreurs

## Rollback

En cas de problème, le backup est disponible dans le répertoire `backup_YYYYMMDD_HHMMSS` créé lors du déploiement.

Pour restaurer:
```bash
cp -r backup_YYYYMMDD_HHMMSS/* /path/to/production/martialcomp/
```

## Notes importantes

- Ce package ne contient que les fichiers de l'application "Compétitions"
- Les migrations de base de données doivent être exécutées séparément si nécessaire
- Les fichiers statiques (CSS, JS, images) ne sont pas inclus dans ce package
- Les fichiers de configuration (settings.py, etc.) ne sont pas inclus
README

# Créer une archive tar.gz
echo -e "${YELLOW}Création de l'archive...${NC}"
tar -czf "${PACKAGE_DIR}.tar.gz" "$PACKAGE_DIR"
echo -e "${GREEN}Archive créée: ${PACKAGE_DIR}.tar.gz${NC}\n"

# Afficher le résumé
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Résumé${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Package créé: ${GREEN}$PACKAGE_DIR${NC}"
echo -e "Archive créée: ${GREEN}${PACKAGE_DIR}.tar.gz${NC}"
echo -e "Fichiers inclus: ${GREEN}$COPIED${NC}"
echo -e "Fichiers ignorés: ${YELLOW}$SKIPPED${NC}"
echo -e "\n${GREEN}Package prêt pour le déploiement!${NC}\n"

# Afficher les instructions
echo -e "${YELLOW}Instructions:${NC}"
echo -e "1. Transférer ${PACKAGE_DIR}.tar.gz sur le serveur de production"
echo -e "2. Extraire: tar -xzf ${PACKAGE_DIR}.tar.gz"
echo -e "3. Modifier deploy_to_production.sh pour pointer vers le répertoire de production"
echo -e "4. Exécuter: cd $PACKAGE_DIR && ./deploy_to_production.sh"
echo -e "\n"
