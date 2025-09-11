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
DB_PORT="5432"

echo -e "${CYAN}=== Diagnostic Base de Données Production ===${RESET}"

# 1. Vérification du service PostgreSQL
echo -e "${YELLOW}[1] Vérification du service PostgreSQL...${RESET}"
if systemctl is-active --quiet postgresql; then
    echo -e "${GREEN}[OK] PostgreSQL est actif${RESET}"
else
    echo -e "${RED}[ERREUR] PostgreSQL n'est pas actif${RESET}"
    exit 1
fi

# 2. Test de connexion à la base
echo -e "${YELLOW}[2] Test de connexion à la base de données...${RESET}"
if psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${GREEN}[OK] Connexion à la base réussie${RESET}"
else
    echo -e "${RED}[ERREUR] Impossible de se connecter à la base${RESET}"
    echo -e "${YELLOW}Vérifiez les paramètres de connexion :${RESET}"
    echo -e "  Host: $DB_HOST"
    echo -e "  Port: $DB_PORT"
    echo -e "  Database: $DB_NAME"
    echo -e "  User: $DB_USER"
    exit 1
fi

# 3. Liste des tables
echo -e "${YELLOW}[3] Liste des tables dans la base...${RESET}"
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "\dt" 2>/dev/null || echo -e "${RED}[ERREUR] Impossible de lister les tables${RESET}"

# 4. Recherche de tables de tenants
echo -e "${YELLOW}[4] Recherche de tables de tenants...${RESET}"
TENANT_TABLES=$(psql -h $DB_HOST -U $DB_USER -d $DB_NAME -t -c "SELECT tablename FROM pg_tables WHERE tablename LIKE '%tenant%' OR tablename LIKE '%organization%' OR tablename LIKE '%club%';" 2>/dev/null)

if [ -n "$TENANT_TABLES" ]; then
    echo -e "${GREEN}[OK] Tables de tenants trouvées :${RESET}"
    echo "$TENANT_TABLES"
else
    echo -e "${YELLOW}[INFO] Aucune table de tenant trouvée${RESET}"
fi

# 5. Vérification des tenants pour martialcomp.com
echo -e "${YELLOW}[5] Vérification des tenants pour martialcomp.com...${RESET}"
for table in $TENANT_TABLES; do
    echo -e "${CYAN}Recherche dans la table: $table${RESET}"
    psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT * FROM $table WHERE domain LIKE '%martialcomp.com%' LIMIT 3;" 2>/dev/null || echo -e "${RED}[ERREUR] Impossible de requêter $table${RESET}"
done

# 6. Statistiques de la base
echo -e "${YELLOW}[6] Statistiques de la base de données...${RESET}"
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT schemaname, tablename, n_tup_ins as inserts, n_tup_upd as updates, n_tup_del as deletes FROM pg_stat_user_tables ORDER BY n_tup_ins DESC LIMIT 10;" 2>/dev/null || echo -e "${RED}[ERREUR] Impossible d'obtenir les statistiques${RESET}"

echo -e "${CYAN}=== Fin du diagnostic ===${RESET}"
echo -e "${YELLOW}Si aucun tenant n'est trouvé pour martialcomp.com, il faut en créer un.${RESET}" 

# Couleurs pour le statut visuel
GREEN="\033[1;32m"
RED="\033[1;31m"
YELLOW="\033[1;33m"
CYAN="\033[1;36m"
RESET="\033[0m"

DB_NAME="martialcomp_db"
DB_USER="martialcomp_user"
DB_HOST="localhost"
DB_PORT="5432"

echo -e "${CYAN}=== Diagnostic Base de Données Production ===${RESET}"

# 1. Vérification du service PostgreSQL
echo -e "${YELLOW}[1] Vérification du service PostgreSQL...${RESET}"
if systemctl is-active --quiet postgresql; then
    echo -e "${GREEN}[OK] PostgreSQL est actif${RESET}"
else
    echo -e "${RED}[ERREUR] PostgreSQL n'est pas actif${RESET}"
    exit 1
fi

# 2. Test de connexion à la base
echo -e "${YELLOW}[2] Test de connexion à la base de données...${RESET}"
if psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${GREEN}[OK] Connexion à la base réussie${RESET}"
else
    echo -e "${RED}[ERREUR] Impossible de se connecter à la base${RESET}"
    echo -e "${YELLOW}Vérifiez les paramètres de connexion :${RESET}"
    echo -e "  Host: $DB_HOST"
    echo -e "  Port: $DB_PORT"
    echo -e "  Database: $DB_NAME"
    echo -e "  User: $DB_USER"
    exit 1
fi

# 3. Liste des tables
echo -e "${YELLOW}[3] Liste des tables dans la base...${RESET}"
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "\dt" 2>/dev/null || echo -e "${RED}[ERREUR] Impossible de lister les tables${RESET}"

# 4. Recherche de tables de tenants
echo -e "${YELLOW}[4] Recherche de tables de tenants...${RESET}"
TENANT_TABLES=$(psql -h $DB_HOST -U $DB_USER -d $DB_NAME -t -c "SELECT tablename FROM pg_tables WHERE tablename LIKE '%tenant%' OR tablename LIKE '%organization%' OR tablename LIKE '%club%';" 2>/dev/null)

if [ -n "$TENANT_TABLES" ]; then
    echo -e "${GREEN}[OK] Tables de tenants trouvées :${RESET}"
    echo "$TENANT_TABLES"
else
    echo -e "${YELLOW}[INFO] Aucune table de tenant trouvée${RESET}"
fi

# 5. Vérification des tenants pour martialcomp.com
echo -e "${YELLOW}[5] Vérification des tenants pour martialcomp.com...${RESET}"
for table in $TENANT_TABLES; do
    echo -e "${CYAN}Recherche dans la table: $table${RESET}"
    psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT * FROM $table WHERE domain LIKE '%martialcomp.com%' LIMIT 3;" 2>/dev/null || echo -e "${RED}[ERREUR] Impossible de requêter $table${RESET}"
done

# 6. Statistiques de la base
echo -e "${YELLOW}[6] Statistiques de la base de données...${RESET}"
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT schemaname, tablename, n_tup_ins as inserts, n_tup_upd as updates, n_tup_del as deletes FROM pg_stat_user_tables ORDER BY n_tup_ins DESC LIMIT 10;" 2>/dev/null || echo -e "${RED}[ERREUR] Impossible d'obtenir les statistiques${RESET}"

echo -e "${CYAN}=== Fin du diagnostic ===${RESET}"
echo -e "${YELLOW}Si aucun tenant n'est trouvé pour martialcomp.com, il faut en créer un.${RESET}" 