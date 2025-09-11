#!/bin/bash

# Couleurs pour le statut visuel
GREEN="\033[1;32m"
RED="\033[1;31m"
YELLOW="\033[1;33m"
CYAN="\033[1;36m"
RESET="\033[0m"

DB_NAME="martialcomp_db"
DB_USER="martialcomp_user"
DB_HOST="localhost"

echo -e "${CYAN}=== Diagnostic Structure Table multitenant_tenant ===${RESET}"

# 1. Structure de la table
echo -e "${YELLOW}[1] Structure de la table multitenant_tenant :${RESET}"
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "\d multitenant_tenant"

# 2. Contraintes de la table
echo -e "${YELLOW}[2] Contraintes de la table multitenant_tenant :${RESET}"
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT conname, contype, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = 'multitenant_tenant'::regclass;"

# 3. Exemple de tenant existant
echo -e "${YELLOW}[3] Exemple de tenant existant :${RESET}"
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT * FROM multitenant_tenant LIMIT 1;"

# 4. Champs NOT NULL
echo -e "${YELLOW}[4] Champs NOT NULL de la table :${RESET}"
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'multitenant_tenant' AND is_nullable = 'NO';"

echo -e "${CYAN}=== Fin du diagnostic ===${RESET}"
echo -e "${YELLOW}Utilise ces informations pour créer le tenant avec les bons champs.${RESET}" 

# Couleurs pour le statut visuel
GREEN="\033[1;32m"
RED="\033[1;31m"
YELLOW="\033[1;33m"
CYAN="\033[1;36m"
RESET="\033[0m"

DB_NAME="martialcomp_db"
DB_USER="martialcomp_user"
DB_HOST="localhost"

echo -e "${CYAN}=== Diagnostic Structure Table multitenant_tenant ===${RESET}"

# 1. Structure de la table
echo -e "${YELLOW}[1] Structure de la table multitenant_tenant :${RESET}"
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "\d multitenant_tenant"

# 2. Contraintes de la table
echo -e "${YELLOW}[2] Contraintes de la table multitenant_tenant :${RESET}"
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT conname, contype, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = 'multitenant_tenant'::regclass;"

# 3. Exemple de tenant existant
echo -e "${YELLOW}[3] Exemple de tenant existant :${RESET}"
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT * FROM multitenant_tenant LIMIT 1;"

# 4. Champs NOT NULL
echo -e "${YELLOW}[4] Champs NOT NULL de la table :${RESET}"
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'multitenant_tenant' AND is_nullable = 'NO';"

echo -e "${CYAN}=== Fin du diagnostic ===${RESET}"
echo -e "${YELLOW}Utilise ces informations pour créer le tenant avec les bons champs.${RESET}" 