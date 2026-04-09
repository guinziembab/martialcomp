#!/bin/bash
# Commandes de déploiement manuel - À exécuter depuis votre machine Windows (WSL/Git Bash)
# Date: 24 novembre 2024

echo "=========================================="
echo "DÉPLOIEMENT MANUEL - FIX CRITIQUE"
echo "=========================================="
echo ""
echo "Étape 1/3: Transfert des fichiers via SCP"
echo ""

# Étape 1: Transférer tous les fichiers modifiés
echo "→ Transfert de base.html (FIX CRITIQUE)..."
scp apps/competitions/templates/base.html martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/

echo "→ Transfert de registration_api.py..."
scp apps/competitions/views/club/registration_api.py martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/club/

echo "→ Transfert de urls/__init__.py..."
scp apps/competitions/urls/__init__.py martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/urls/

echo "→ Transfert de urls/club.py..."
scp apps/competitions/urls/club.py martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/urls/

echo "→ Transfert de practitioner_form.html..."
scp apps/competitions/templates/competitions/club/practitioner_form.html martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/club/

echo "→ Transfert de dashboard/club.html (mode jour/nuit)..."
scp apps/competitions/templates/competitions/dashboard/club.html martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/dashboard/

echo "→ Transfert de admin/__init__.py..."
scp apps/competitions/admin/__init__.py martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/admin/

echo "→ Transfert de admin/practitioner.py..."
scp apps/competitions/admin/practitioner.py martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/admin/

echo ""
echo "✓ Tous les fichiers transférés"
echo ""
echo "Étape 2/3: Connexion SSH et vérifications..."
echo ""
echo "Vous allez être connecté au serveur pour exécuter les commandes de vérification et rechargement."
echo "Appuyez sur Entrée pour continuer..."
read

# Étape 2: Se connecter et exécuter les commandes
ssh martialcomp-production << 'ENDSSH'
echo "=========================================="
echo "SUR LE SERVEUR DE PRODUCTION"
echo "=========================================="
echo ""

# Se positionner dans le répertoire du projet
cd /var/www/vhosts/martialcomp.com/httpdocs

# Activer l'environnement virtuel
echo "→ Activation de l'environnement virtuel..."
source /var/www/vhosts/martialcomp.com/venv/bin/activate

# Vérifier la syntaxe Python
echo ""
echo "→ Vérification de la syntaxe Python..."
python -m py_compile apps/competitions/views/club/registration_api.py && echo "  ✓ registration_api.py OK"
python -m py_compile apps/competitions/urls/__init__.py && echo "  ✓ urls/__init__.py OK"
python -m py_compile apps/competitions/urls/club.py && echo "  ✓ urls/club.py OK"
python -m py_compile apps/competitions/admin/__init__.py && echo "  ✓ admin/__init__.py OK"
python -m py_compile apps/competitions/admin/practitioner.py && echo "  ✓ admin/practitioner.py OK"

# Vérifier que les templates existent
echo ""
echo "→ Vérification de la présence des templates..."
[ -f "apps/competitions/templates/base.html" ] && echo "  ✓ base.html présent" || echo "  ✗ base.html MANQUANT"
[ -f "apps/competitions/templates/competitions/club/practitioner_form.html" ] && echo "  ✓ practitioner_form.html présent" || echo "  ✗ practitioner_form.html MANQUANT"
[ -f "apps/competitions/templates/competitions/dashboard/club.html" ] && echo "  ✓ dashboard/club.html présent" || echo "  ✗ dashboard/club.html MANQUANT"

# Vérifier les corrections JavaScript dans base.html
echo ""
echo "→ Vérification des corrections JavaScript dans base.html..."
CORRECTIONS_COUNT=$(grep -c "const currentLang = document.documentElement.lang" apps/competitions/templates/base.html)
if [ "$CORRECTIONS_COUNT" -eq 3 ]; then
    echo "  ✓ Les 3 corrections JavaScript sont présentes dans base.html"
    grep -n "const currentLang = document.documentElement.lang" apps/competitions/templates/base.html | sed 's/^/    Ligne /'
else
    echo "  ✗ ERREUR: Seulement $CORRECTIONS_COUNT correction(s) trouvée(s) au lieu de 3"
fi

# Effacer le cache Python
echo ""
echo "→ Effacement du cache Python..."
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
echo "  ✓ Cache Python effacé"

# Recharger l'application (Passenger WSGI)
echo ""
echo "→ Rechargement de l'application..."
mkdir -p tmp
touch tmp/restart.txt
echo "  ✓ Application rechargée (Passenger)"

echo ""
echo "=========================================="
echo "DÉPLOIEMENT TERMINÉ"
echo "=========================================="
ENDSSH

echo ""
echo "Étape 3/3: Tests à effectuer"
echo ""
echo "=========================================="
echo "TESTS À EFFECTUER MAINTENANT"
echo "=========================================="
echo ""
echo "Test 0: Vérifier l'absence d'erreur JavaScript (PRIORITAIRE)"
echo "  1. Ouvrir: https://martialcomp.com/en/competitions/club/practitioners/88/edit/"
echo "  2. Appuyer sur F12 pour ouvrir la console"
echo "  3. VÉRIFIER: Il ne doit PLUS y avoir l'erreur à la ligne 2570"
echo "  ✓ Attendu: Console propre sans erreur JavaScript"
echo ""
echo "Test 1: Bouton Générer licence"
echo "  1. Sur la même page, remplir: date de naissance, nom, discipline"
echo "  2. Cliquer sur le bouton 'Générer'"
echo "  ✓ Attendu: Numéro de licence généré (format: DISC-YYYY-CLUB-XXXX)"
echo ""
echo "Test 2: Mode jour/nuit"
echo "  1. Ouvrir: https://martialcomp.com/en/competitions/dashboard/club/"
echo "  2. Cliquer sur le bouton ☀️/🌙 en haut à droite"
echo "  ✓ Attendu: Le thème change et reste persistant après F5"
echo ""
echo "=========================================="
