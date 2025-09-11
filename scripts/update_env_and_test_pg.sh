#!/bin/bash

# === CONFIGURATION À ADAPTER ===
ENV_FILE=".env"  # ou "production.env" selon votre usage
PG_DB="martialcomp_db"
PG_USER="martialcomp_user"
PG_PASSWORD="MartialComp2025Production!"
PG_HOST="localhost"
PG_PORT="5432"

# === MISE À JOUR DU FICHIER .env ===
echo "Mise à jour du fichier $ENV_FILE ..."

cat > $ENV_FILE << EOF
POSTGRES_DB=$PG_DB
POSTGRES_USER=$PG_USER
POSTGRES_PASSWORD=$PG_PASSWORD
POSTGRES_HOST=$PG_HOST
POSTGRES_PORT=$PG_PORT
EOF

chmod 600 $ENV_FILE

echo "✓ Fichier $ENV_FILE mis à jour."

# === TEST DE CONNEXION POSTGRESQL ===
echo "Test de connexion à PostgreSQL..."

PGPASSWORD="$PG_PASSWORD" psql -h "$PG_HOST" -U "$PG_USER" -d "$PG_DB" -p "$PG_PORT" -c '\dt' > /tmp/pg_test_result.txt 2>&1

if grep -q "Did not find any relations" /tmp/pg_test_result.txt || grep -q "List of relations" /tmp/pg_test_result.txt; then
    echo -e "\033[0;32m✓ Connexion PostgreSQL réussie !\033[0m"
    cat /tmp/pg_test_result.txt | grep -A 10 "List of relations"
else
    echo -e "\033[0;31m✗ Échec de la connexion PostgreSQL !\033[0m"
    cat /tmp/pg_test_result.txt
fi

rm -f /tmp/pg_test_result.txt

echo ""
echo "Résumé :"
echo "- Fichier d'environnement : $ENV_FILE"
echo "- Base testée : $PG_DB"
echo "- Utilisateur : $PG_USER"
echo "- Hôte : $PG_HOST"
echo "- Port : $PG_PORT" 