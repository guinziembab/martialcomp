#!/bin/bash
# Script pour redémarrer le serveur Django avec une gestion améliorée des traductions

echo "Redémarrage du serveur Django..."

# Définir le répertoire du projet
PROJECT_DIR="$(dirname "$(readlink -f "$0")")"
cd "$PROJECT_DIR"

# Traiter les options
INSTALL_POLIB=0
FORCE_RECOMPILE=0

for arg in "$@"; do
    case $arg in
        --install-polib)
            INSTALL_POLIB=1
            shift
            ;;
        --force-recompile)
            FORCE_RECOMPILE=1
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --install-polib     Installer polib pour une meilleure compilation des traductions"
            echo "  --force-recompile   Forcer la recompilation de toutes les traductions"
            echo "  --help              Afficher ce message d'aide"
            exit 0
            ;;
    esac
done

# Tentative d'arrêt du serveur existant (si en cours d'exécution)
echo "Tentative d'arrêt du serveur existant..."
pkill -f "python.*manage.py runserver" || true

# Attendre que le serveur s'arrête
sleep 2

# Vider les fichiers .pyc compilés pour assurer un redémarrage propre
echo "Nettoyage des fichiers .pyc compilés..."
find . -name "*.pyc" -delete

# Installer polib si demandé
if [ $INSTALL_POLIB -eq 1 ]; then
    echo "Installation de polib..."
    python3 install_polib.py
fi

# Compiler les fichiers de traduction
echo "Compilation des fichiers de traduction..."
if [ $FORCE_RECOMPILE -eq 1 ]; then
    # Supprimer tous les fichiers .mo existants pour forcer une recompilation
    echo "Suppression des fichiers .mo existants..."
    find ./locale -name "*.mo" -delete
fi

python3 recompile_translations.py

# Vérifier que les traductions fonctionnent
echo "Vérification des traductions..."
python3 debug_translations.py

# Démarrer le serveur Django
echo "Démarrage du serveur Django..."
python3 manage.py runserver 0.0.0.0:8000

echo "Serveur Django redémarré."