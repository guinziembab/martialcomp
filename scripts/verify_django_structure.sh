#!/bin/bash

# Script de vérification de la structure Django après nettoyage
# Vérifie que tous les éléments essentiels sont présents

echo "=== VÉRIFICATION DE LA STRUCTURE DJANGO ==="
echo "Date: $(date)"
echo ""

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction pour vérifier un fichier
check_file() {
    local file="$1"
    local description="$2"
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $description: $file"
        return 0
    else
        echo -e "${RED}✗${NC} $description: $file (MANQUANT)"
        return 1
    fi
}

# Fonction pour vérifier un dossier
check_dir() {
    local dir="$1"
    local description="$2"
    if [ -d "$dir" ]; then
        local count=$(find "$dir" -type f | wc -l)
        echo -e "${GREEN}✓${NC} $description: $dir ($count fichiers)"
        return 0
    else
        echo -e "${RED}✗${NC} $description: $dir (MANQUANT)"
        return 1
    fi
}

echo "1. Vérification des fichiers Django essentiels..."
errors=0

check_file "manage.py" "Fichier de gestion Django" || ((errors++))
check_file "requirements.txt" "Fichier des dépendances" || ((errors++))
check_file "martialcomp/settings.py" "Configuration Django" || ((errors++))
check_file "martialcomp/urls.py" "URLs principales" || ((errors++))
check_file "martialcomp/wsgi.py" "Configuration WSGI" || ((errors++))

echo ""
echo "2. Vérification des applications Django..."
check_dir "accounts" "Application Accounts" || ((errors++))
check_dir "competitions" "Application Competitions" || ((errors++))
check_dir "shop" "Application Shop" || ((errors++))
check_dir "finances" "Application Finances" || ((errors++))
check_dir "clubs" "Application Clubs" || ((errors++))
check_dir "organizations" "Application Organizations" || ((errors++))
check_dir "federations" "Application Federations" || ((errors++))
check_dir "grades" "Application Grades" || ((errors++))
check_dir "family_management" "Application Family Management" || ((errors++))
check_dir "payment" "Application Payment" || ((errors++))
check_dir "permissions_manager" "Application Permissions Manager" || ((errors++))
check_dir "mobile" "Application Mobile" || ((errors++))
check_dir "multitenant" "Application Multitenant" || ((errors++))

echo ""
echo "3. Vérification des dossiers de templates et statiques..."
check_dir "templates" "Dossiers de templates" || ((errors++))
check_dir "static" "Fichiers statiques" || ((errors++))
check_dir "staticfiles" "Fichiers statiques collectés" || ((errors++))

echo ""
echo "4. Vérification des médias et uploads..."
check_dir "media" "Fichiers média" || ((errors++))
check_dir "locale" "Fichiers de traduction" || ((errors++))

echo ""
echo "5. Vérification de la base de données..."
if [ -f "db.sqlite3" ]; then
    size=$(du -h db.sqlite3 | cut -f1)
    echo -e "${GREEN}✓${NC} Base de données: db.sqlite3 ($size)"
else
    echo -e "${YELLOW}⚠${NC} Base de données: db.sqlite3 (MANQUANTE - à créer)"
    ((errors++))
fi

echo ""
echo "6. Vérification des fichiers de configuration..."
check_file "production.env" "Configuration de production" || ((errors++))
check_file "production.py" "Settings de production" || ((errors++))

echo ""
echo "7. Vérification des migrations..."
for app in accounts competitions shop finances clubs organizations federations grades family_management payment permissions_manager mobile multitenant; do
    if [ -d "$app/migrations" ]; then
        migration_count=$(find "$app/migrations" -name "*.py" | wc -l)
        echo -e "${GREEN}✓${NC} Migrations $app: $migration_count fichiers"
    else
        echo -e "${YELLOW}⚠${NC} Migrations $app: dossier manquant"
    fi
done

echo ""
echo "8. Vérification des fichiers de logs..."
if [ -d "logs" ]; then
    log_count=$(find logs -type f -name "*.log" | wc -l)
    echo -e "${GREEN}✓${NC} Dossier logs: $log_count fichiers de log"
else
    echo -e "${YELLOW}⚠${NC} Dossier logs: manquant (à créer)"
fi

echo ""
echo "9. Vérification de l'espace disque..."
echo "Espace disque disponible:"
df -h .

echo ""
echo "10. Test de la configuration Django..."
echo "Test de la configuration Django:"
if python manage.py check --deploy 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Configuration Django valide"
else
    echo -e "${RED}✗${NC} Problèmes de configuration Django"
    ((errors++))
fi

echo ""
echo "=== RÉSUMÉ DE LA VÉRIFICATION ==="
if [ $errors -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Structure Django complète et valide"
    echo ""
    echo "Prochaines étapes recommandées:"
    echo "1. Créer les migrations: python manage.py makemigrations"
    echo "2. Appliquer les migrations: python manage.py migrate"
    echo "3. Collecter les fichiers statiques: python manage.py collectstatic"
    echo "4. Créer un superutilisateur: python manage.py createsuperuser"
    echo "5. Tester le serveur: python manage.py runserver 0.0.0.0:8000"
else
    echo -e "${RED}✗${NC} $errors problème(s) détecté(s)"
    echo ""
    echo "Actions recommandées:"
    echo "1. Vérifier les fichiers manquants"
    echo "2. Restaurer depuis le backup si nécessaire"
    echo "3. Relancer la synchronisation"
fi

echo ""
echo "=== VÉRIFICATION TERMINÉE ==="
echo "Date: $(date)" 