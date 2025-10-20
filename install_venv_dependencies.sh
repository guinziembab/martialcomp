#!/bin/bash

# Script pour installer les dépendances dans l'environnement virtuel

echo "=== INSTALLATION DES DÉPENDANCES DANS L'ENVIRONNEMENT VIRTUEL ==="
echo ""

cd /var/www/vhosts/martialcomp.com/httpdocs

# Activer l'environnement virtuel
echo "Activation de l'environnement virtuel..."
source /var/www/vhosts/martialcomp.com/venv/bin/activate

# Vérifier Python et pip
echo "Python version dans venv:"
which python
python --version
which pip

# Mettre à jour pip
echo ""
echo "Mise à jour de pip..."
pip install --upgrade pip

# Installer les dépendances essentielles si requirements.txt existe
if [ -f "requirements.txt" ]; then
    echo ""
    echo "Installation des dépendances depuis requirements.txt..."
    pip install -r requirements.txt
else
    echo ""
    echo "Installation manuelle des dépendances essentielles..."
    # Installer les packages essentiels
    pip install django==4.2.11
    pip install psycopg2-binary
    pip install python-decouple
    pip install pillow
    pip install django-cors-headers
    pip install djangorestframework
    pip install gunicorn
fi

# Vérifier que Django est bien installé dans le venv
echo ""
echo "Vérification de l'installation Django dans venv:"
python -c "import django; print(f'Django {django.get_version()} installé avec succès')"

# Tester la connexion à la base de données
echo ""
echo "Test de connexion à la base de données..."
python manage.py dbshell --settings=config.settings.production << EOF
SELECT version();
\q
EOF

# Appliquer les migrations
echo ""
echo "Application des migrations..."
python manage.py migrate --settings=config.settings.production

# Collecter les fichiers statiques
echo ""
echo "Collecte des fichiers statiques..."
python manage.py collectstatic --settings=config.settings.production --noinput

# Créer un superutilisateur si nécessaire
echo ""
echo "Pour créer un superutilisateur, exécutez :"
echo "python manage.py createsuperuser --settings=config.settings.production"

# Redémarrer Apache
echo ""
echo "Redémarrage d'Apache..."
systemctl restart apache2

# Vérifier les erreurs
echo ""
echo "Vérification des logs après redémarrage..."
sleep 2
tail -20 /var/log/apache2/error.log | grep -E "(Error|ERROR|Exception|Traceback)" -A 3

echo ""
echo "=== INSTALLATION TERMINÉE ==="
echo ""
echo "Testez le site : curl -I https://martialcomp.com"