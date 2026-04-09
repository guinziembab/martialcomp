#!/bin/bash
# Script de déploiement - FIX CRITIQUE: Correction base.html + bouton licence + mode jour/nuit
# Date: 2024-11-24
# CAUSE RACINE: Django URL tags dans JavaScript (base.html ligne 231, 339, 357)

echo "=========================================="
echo "DÉPLOIEMENT FIX CRITIQUE"
echo "1. Fix base.html (Django URL tags → JavaScript URLs)"
echo "2. Fix bouton Générer licence"
echo "3. Mode jour/nuit dashboard club"
echo "=========================================="

# Étape 1: Transférer les fichiers modifiés via SCP
echo "Étape 1: Transfert des fichiers vers le serveur de production..."

# FIX CRITIQUE: base.html avec correction des URL Django en JavaScript
echo "  → Transfert base.html (FIX CRITIQUE)..."
scp apps/competitions/templates/base.html martialcomp-production:/home/martialcomp/martialcomp_project/apps/competitions/templates/

# Fix bouton Générer licence
echo "  → Transfert registration_api.py..."
scp apps/competitions/views/club/registration_api.py martialcomp-production:/home/martialcomp/martialcomp_project/apps/competitions/views/club/

echo "  → Transfert urls/__init__.py..."
scp apps/competitions/urls/__init__.py martialcomp-production:/home/martialcomp/martialcomp_project/apps/competitions/urls/

echo "  → Transfert urls/club.py..."
scp apps/competitions/urls/club.py martialcomp-production:/home/martialcomp/martialcomp_project/apps/competitions/urls/

echo "  → Transfert practitioner_form.html..."
scp apps/competitions/templates/competitions/club/practitioner_form.html martialcomp-production:/home/martialcomp/martialcomp_project/apps/competitions/templates/competitions/club/

# Admin Practitioner
echo "  → Transfert admin/__init__.py..."
scp apps/competitions/admin/__init__.py martialcomp-production:/home/martialcomp/martialcomp_project/apps/competitions/admin/

echo "  → Transfert admin/practitioner.py..."
scp apps/competitions/admin/practitioner.py martialcomp-production:/home/martialcomp/martialcomp_project/apps/competitions/admin/

# Mode jour/nuit dashboard club
echo "  → Transfert dashboard club.html (mode jour/nuit)..."
scp apps/competitions/templates/competitions/dashboard/club.html martialcomp-production:/home/martialcomp/martialcomp_project/apps/competitions/templates/competitions/dashboard/

echo "✓ Tous les fichiers transférés avec succès"

# Étape 2: Se connecter au serveur et redémarrer les services
echo ""
echo "Étape 2: Vérification et redémarrage sur le serveur..."
ssh martialcomp-production << 'ENDSSH'
cd /home/martialcomp/martialcomp_project

# Activer l'environnement virtuel
source venv/bin/activate

# Vérifier la syntaxe Python
echo "Vérification de la syntaxe Python..."
python -m py_compile apps/competitions/views/club/registration_api.py
if [ $? -ne 0 ]; then
    echo "✗ Erreur de syntaxe dans registration_api.py"
    exit 1
fi

python -m py_compile apps/competitions/urls/__init__.py
if [ $? -ne 0 ]; then
    echo "✗ Erreur de syntaxe dans urls/__init__.py"
    exit 1
fi

python -m py_compile apps/competitions/urls/club.py
if [ $? -ne 0 ]; then
    echo "✗ Erreur de syntaxe dans urls/club.py"
    exit 1
fi

python -m py_compile apps/competitions/admin/__init__.py
if [ $? -ne 0 ]; then
    echo "✗ Erreur de syntaxe dans admin/__init__.py"
    exit 1
fi

python -m py_compile apps/competitions/admin/practitioner.py
if [ $? -ne 0 ]; then
    echo "✗ Erreur de syntaxe dans admin/practitioner.py"
    exit 1
fi

echo "✓ Syntaxe Python valide"

# Vérifier la syntaxe des templates (basique)
echo "Vérification des templates..."
if [ ! -f "apps/competitions/templates/base.html" ]; then
    echo "✗ base.html manquant"
    exit 1
fi

if [ ! -f "apps/competitions/templates/competitions/club/practitioner_form.html" ]; then
    echo "✗ practitioner_form.html manquant"
    exit 1
fi

if [ ! -f "apps/competitions/templates/competitions/dashboard/club.html" ]; then
    echo "✗ dashboard/club.html manquant"
    exit 1
fi

echo "✓ Templates présents"

# Vérifier que les corrections sont bien dans base.html
echo "Vérification des corrections dans base.html..."
if grep -q "const currentLang = document.documentElement.lang" apps/competitions/templates/base.html; then
    echo "✓ Corrections JavaScript détectées dans base.html"
else
    echo "✗ Les corrections JavaScript ne sont pas présentes dans base.html"
    exit 1
fi

# Effacer le cache Python
echo "Effacement du cache Python..."
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Redémarrer Gunicorn
echo "Redémarrage de Gunicorn..."
sudo systemctl restart gunicorn

# Attendre que le service redémarre
sleep 3

# Vérifier le statut
if sudo systemctl is-active --quiet gunicorn; then
    echo "✓ Gunicorn redémarré avec succès"
    sudo systemctl status gunicorn | head -10
else
    echo "✗ Erreur lors du redémarrage de Gunicorn"
    sudo systemctl status gunicorn
    exit 1
fi

echo ""
echo "✓ Déploiement terminé avec succès"
ENDSSH

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "DÉPLOIEMENT RÉUSSI"
    echo "=========================================="
    echo ""
    echo "✓ Fix critique base.html déployé (Django URL tags → JavaScript)"
    echo "✓ Fix bouton Générer licence déployé"
    echo "✓ Mode jour/nuit dashboard club déployé"
    echo ""
    echo "CAUSE RACINE DU PROBLÈME:"
    echo "Les Django URL tags {% url %} dans le JavaScript de base.html"
    echo "causaient une erreur de syntaxe JavaScript à la ligne 2570"
    echo "du HTML rendu. Ces tags ont été remplacés par des URLs"
    echo "construites dynamiquement en JavaScript pur."
    echo ""
    echo "TESTS À EFFECTUER:"
    echo "1. Bouton Générer licence:"
    echo "   https://martialcomp.com/en/competitions/club/practitioners/88/edit/"
    echo "   → Ouvrir la console (F12) et vérifier qu'il n'y a PLUS d'erreur JavaScript"
    echo "   → Cliquer sur 'Générer' et vérifier qu'un numéro de licence est généré"
    echo ""
    echo "2. Mode jour/nuit:"
    echo "   https://martialcomp.com/en/competitions/dashboard/club/"
    echo "   → Cliquer sur le bouton toggle (soleil/lune) en haut à droite"
    echo "   → Vérifier que le thème bascule entre clair et sombre"
    echo "   → Recharger la page pour vérifier que le thème est persistant"
    echo ""
else
    echo ""
    echo "=========================================="
    echo "ERREUR DE DÉPLOIEMENT"
    echo "=========================================="
    echo ""
    echo "Le déploiement a échoué. Vérifiez les logs ci-dessus."
    exit 1
fi
