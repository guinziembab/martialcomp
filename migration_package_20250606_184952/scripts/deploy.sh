#!/bin/bash
# Script de déploiement multilingue

echo "🚀 DÉPLOIEMENT MULTILINGUE MARTIALCOMP"
echo "======================================"

set -e  # Arrêter en cas d'erreur

# 1. Vérifications
echo "1. Vérifications préalables..."
python --version
echo "Django version:"
python -c "import django; print(django.get_version())"

# 2. Installation des packages
echo "2. Installation des packages multilingues..."
pip install -r config/requirements_multilingual.txt

# 3. Copie des fichiers
echo "3. Copie des fichiers de traduction..."
if [ -d "locale" ]; then
    cp -r locale/ ../../../locale/
    echo "✅ Fichiers locale copiés"
fi

# 4. Copie du template
echo "4. Copie du template welcome.html..."
if [ -f "templates/welcome.html" ]; then
    cp templates/welcome.html ../../../competitions/templates/competitions/
    echo "✅ Template welcome.html copié"
fi

# 5. Migrations
echo "5. Migrations de la base de données..."
cd ../../..
python manage.py makemigrations
python manage.py migrate

# 6. Compilation des traductions
echo "6. Compilation des traductions..."
python manage.py compilemessages || echo "⚠️ Erreur compilation, essai script manuel..."
if [ -f "compile_translations.py" ]; then
    python compile_translations.py
fi

# 7. Collecte des fichiers statiques
echo "7. Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# 8. Tests de base
echo "8. Vérifications finales..."
python manage.py check

echo "✅ DÉPLOIEMENT TERMINÉ!"
echo "🌍 Testez:"
echo "  • Page d'accueil: https://your-domain.com/"
echo "  • Admin: https://your-domain.com/admin/"
echo "  • Rosetta: https://your-domain.com/rosetta/"
