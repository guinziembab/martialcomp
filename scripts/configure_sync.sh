#!/bin/bash

# Script de configuration pour la synchronisation
# Adapte automatiquement les chemins selon l'environnement

echo "=== CONFIGURATION DE LA SYNCHRONISATION ==="
echo ""

# Détection automatique de l'environnement
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # Windows avec Git Bash ou MSYS
    BACKUP_LOCAL="C:/martial_hub_django/martialcomp_backup_local"
    PG_DUMP_PATHS=(
        "/c/Program Files/PostgreSQL/*/bin/pg_dump.exe"
        "C:/Program Files/PostgreSQL/*/bin/pg_dump.exe"
    )
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    BACKUP_LOCAL="$HOME/martial_hub_django/martialcomp_backup_local"
    PG_DUMP_PATHS=(
        "/usr/local/bin/pg_dump"
        "/opt/homebrew/bin/pg_dump"
    )
else
    # Linux
    BACKUP_LOCAL="$HOME/martial_hub_django/martialcomp_backup_local"
    PG_DUMP_PATHS=(
        "/usr/bin/pg_dump"
        "/usr/local/bin/pg_dump"
    )
fi

echo "🔍 Détection de l'environnement..."
echo "OS: $OSTYPE"
echo "Backup local: $BACKUP_LOCAL"

# Vérifier l'existence du dossier backup
if [ ! -d "$BACKUP_LOCAL" ]; then
    echo "⚠ Dossier backup non trouvé: $BACKUP_LOCAL"
    echo "Veuillez spécifier le chemin correct:"
    read -p "Chemin du dossier backup: " BACKUP_LOCAL
fi

# Détecter pg_dump
PG_DUMP_CMD=""
for path in "${PG_DUMP_PATHS[@]}"; do
    if ls $path 2>/dev/null | head -1; then
        PG_DUMP_CMD=$(ls $path 2>/dev/null | head -1)
        break
    fi
done

if [ -z "$PG_DUMP_CMD" ]; then
    echo "⚠ pg_dump non trouvé automatiquement"
    echo "Veuillez spécifier le chemin manuellement:"
    read -p "Chemin vers pg_dump: " PG_DUMP_CMD
fi

# Configuration des paramètres de base de données
echo ""
echo "📊 Configuration des bases de données..."
echo "Base de développement:"
read -p "Hôte (défaut: localhost): " DEV_HOST
DEV_HOST=${DEV_HOST:-localhost}
read -p "Port (défaut: 5432): " DEV_PORT
DEV_PORT=${DEV_PORT:-5432}
read -p "Utilisateur (défaut: martialcomp_user): " DEV_USER
DEV_USER=${DEV_USER:-martialcomp_user}
read -p "Base de données (défaut: martialcomp_db): " DEV_DB
DEV_DB=${DEV_DB:-martialcomp_db}

echo ""
echo "Base de production:"
read -p "Hôte (défaut: localhost): " PROD_HOST
PROD_HOST=${PROD_HOST:-localhost}
read -p "Port (défaut: 5432): " PROD_PORT
PROD_PORT=${PROD_PORT:-5432}
read -p "Utilisateur (défaut: martialcomp_user): " PROD_USER
PROD_USER=${PROD_USER:-martialcomp_user}
read -p "Base de données (défaut: martialcomp_db): " PROD_DB
PROD_DB=${PROD_DB:-martialcomp_db}
read -s -p "Mot de passe: " PROD_PASSWORD
echo ""

# Configuration du serveur
echo ""
echo "🌐 Configuration du serveur..."
read -p "Hôte du serveur (défaut: martialcomp.com): " SERVER_HOST
SERVER_HOST=${SERVER_HOST:-martialcomp.com}
read -p "Utilisateur SSH (défaut: root): " SERVER_USER
SERVER_USER=${SERVER_USER:-root}
read -p "Chemin du projet (défaut: /var/www/vhosts/martialcomp.com/httpdocs): " SERVER_PATH
SERVER_PATH=${SERVER_PATH:-/var/www/vhosts/martialcomp.com/httpdocs}

# Générer le script de synchronisation configuré
echo ""
echo "⚙️ Génération du script de synchronisation..."

cat > sync_dev_to_prod_configured.sh << EOF
#!/bin/bash

# Script de synchronisation configuré automatiquement
# Généré le $(date)

# Variables de configuration
DEV_HOST="$DEV_HOST"
DEV_USER="$DEV_USER"
DEV_DB="$DEV_DB"
DEV_PORT="$DEV_PORT"

PROD_HOST="$PROD_HOST"
PROD_USER="$PROD_USER"
PROD_DB="$PROD_DB"
PROD_PASSWORD="$PROD_PASSWORD"
PROD_PORT="$PROD_PORT"

SERVER_HOST="$SERVER_HOST"
SERVER_USER="$SERVER_USER"
SERVER_PATH="$SERVER_PATH"

BACKUP_LOCAL="$BACKUP_LOCAL"
PG_DUMP_CMD="$PG_DUMP_CMD"

# Le reste du script de synchronisation...
$(cat sync_dev_to_prod_complete.sh | sed -n '/^# A. Export de la base de développement/,$p')
EOF

chmod +x sync_dev_to_prod_configured.sh

echo ""
echo "✅ Configuration terminée !"
echo ""
echo "📋 Résumé de la configuration:"
echo "🔧 Environnement: $OSTYPE"
echo "📁 Backup local: $BACKUP_LOCAL"
echo "🗄️ pg_dump: $PG_DUMP_CMD"
echo ""
echo "🖥️ Base de développement:"
echo "  - Hôte: $DEV_HOST:$DEV_PORT"
echo "  - Utilisateur: $DEV_USER"
echo "  - Base: $DEV_DB"
echo ""
echo "🌐 Base de production:"
echo "  - Hôte: $PROD_HOST:$PROD_PORT"
echo "  - Utilisateur: $PROD_USER"
echo "  - Base: $PROD_DB"
echo ""
echo "🚀 Serveur:"
echo "  - Hôte: $SERVER_HOST"
echo "  - Utilisateur: $SERVER_USER"
echo "  - Chemin: $SERVER_PATH"
echo ""
echo "🎯 Pour lancer la synchronisation:"
echo "   ./sync_dev_to_prod_configured.sh" 