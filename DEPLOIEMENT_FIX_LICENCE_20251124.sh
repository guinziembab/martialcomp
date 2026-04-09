#!/bin/bash
# Script de déploiement du fix pour le bouton "Générer licence"
# Date: 2024-11-24

echo "=========================================="
echo "DÉPLOIEMENT FIX BOUTON GÉNÉRER LICENCE"
echo "=========================================="

# Étape 1: Transférer les fichiers modifiés via SCP
echo "Étape 1: Transfert des fichiers vers le serveur de production..."

# Transférer registration_api.py (contient la fonction generate_license_number_api)
scp apps/competitions/views/club/registration_api.py martialcomp-production:/home/martialcomp/martialcomp_project/apps/competitions/views/club/

# Transférer urls/__init__.py (contient l'import et l'URL de l'API)
scp apps/competitions/urls/__init__.py martialcomp-production:/home/martialcomp/martialcomp_project/apps/competitions/urls/

# Transférer urls/club.py (contient l'import de la fonction)
scp apps/competitions/urls/club.py martialcomp-production:/home/martialcomp/martialcomp_project/apps/competitions/urls/

# Transférer practitioner_form.html (contient le JavaScript corrigé)
scp apps/competitions/templates/competitions/club/practitioner_form.html martialcomp-production:/home/martialcomp/martialcomp_project/apps/competitions/templates/competitions/club/

# Transférer admin/__init__.py (import practitioner admin)
scp apps/competitions/admin/__init__.py martialcomp-production:/home/martialcomp/martialcomp_project/apps/competitions/admin/

# Transférer admin/practitioner.py (admin pour pratiquants)
scp apps/competitions/admin/practitioner.py martialcomp-production:/home/martialcomp/martialcomp_project/apps/competitions/admin/

echo "✓ Fichiers transférés avec succès"

# Étape 2: Se connecter au serveur et redémarrer les services
echo ""
echo "Étape 2: Redémarrage des services sur le serveur..."
ssh martialcomp-production << 'ENDSSH'
cd /home/martialcomp/martialcomp_project

# Activer l'environnement virtuel
source venv/bin/activate

# Vérifier la syntaxe Python
echo "Vérification de la syntaxe Python..."
python -m py_compile apps/competitions/views/club/registration_api.py
python -m py_compile apps/competitions/urls/__init__.py
python -m py_compile apps/competitions/urls/club.py
python -m py_compile apps/competitions/admin/__init__.py
python -m py_compile apps/competitions/admin/practitioner.py

if [ $? -eq 0 ]; then
    echo "✓ Syntaxe Python valide"
else
    echo "✗ Erreur de syntaxe Python détectée"
    exit 1
fi

# Collecter les fichiers statiques si nécessaire
# python manage.py collectstatic --noinput

# Redémarrer Gunicorn
echo "Redémarrage de Gunicorn..."
sudo systemctl restart gunicorn

# Vérifier le statut
sleep 3
sudo systemctl status gunicorn | head -10

echo "✓ Déploiement terminé"
ENDSSH

echo ""
echo "=========================================="
echo "DÉPLOIEMENT TERMINÉ"
echo "=========================================="
echo ""
echo "Testez le bouton 'Générer' sur:"
echo "https://martialcomp.com/en/competitions/club/practitioners/88/edit/"
echo ""
