#!/bin/bash

# clean_and_fix_requirements.sh
# Nettoie requirements.txt (BOM, caractères non imprimables), corrige django-deepl, puis relance l'installation

set -e

PROJECT_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
REQ="$PROJECT_DIR/requirements.txt"
REQ_CLEAN="$PROJECT_DIR/requirements_clean.txt"

step() {
    echo -e "\n\033[1;34m[ETAPE]\033[0m $1"
}

error() {
    echo -e "\033[1;31m[ERREUR]\033[0m $1"
}

success() {
    echo -e "\033[1;32m[SUCCES]\033[0m $1"
}

step "Suppression du BOM et des caractères non imprimables dans requirements.txt..."
# Supprime le BOM UTF-8 et les caractères non imprimables
awk '{gsub(/\r/,""); gsub(/\xef\xbb\xbf/,""); print}' "$REQ" | tr -cd '\11\12\15\40-\176' > "$REQ_CLEAN"
mv "$REQ_CLEAN" "$REQ"

step "Correction de la ligne django-deepl dans requirements.txt..."
sed -i 's/^django-deepl==.*$/django-deepl==0.0.2/' "$REQ"
grep django-deepl "$REQ"

step "Relance du script d'installation complet..."
sudo bash $PROJECT_DIR/fix_deepl_and_install.sh 

# clean_and_fix_requirements.sh
# Nettoie requirements.txt (BOM, caractères non imprimables), corrige django-deepl, puis relance l'installation

set -e

PROJECT_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
REQ="$PROJECT_DIR/requirements.txt"
REQ_CLEAN="$PROJECT_DIR/requirements_clean.txt"

step() {
    echo -e "\n\033[1;34m[ETAPE]\033[0m $1"
}

error() {
    echo -e "\033[1;31m[ERREUR]\033[0m $1"
}

success() {
    echo -e "\033[1;32m[SUCCES]\033[0m $1"
}

step "Suppression du BOM et des caractères non imprimables dans requirements.txt..."
# Supprime le BOM UTF-8 et les caractères non imprimables
awk '{gsub(/\r/,""); gsub(/\xef\xbb\xbf/,""); print}' "$REQ" | tr -cd '\11\12\15\40-\176' > "$REQ_CLEAN"
mv "$REQ_CLEAN" "$REQ"

step "Correction de la ligne django-deepl dans requirements.txt..."
sed -i 's/^django-deepl==.*$/django-deepl==0.0.2/' "$REQ"
grep django-deepl "$REQ"

step "Relance du script d'installation complet..."
sudo bash $PROJECT_DIR/fix_deepl_and_install.sh 