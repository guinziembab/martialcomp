#!/bin/bash
# Script de déploiement pour corriger la redirection du dashboard juge

echo "====================================="
echo "Déploiement de la correction du dashboard juge"
echo "====================================="

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "manage.py" ]; then
    echo "Erreur : Ce script doit être exécuté depuis le répertoire racine du projet Django"
    exit 1
fi

echo "1. Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

echo "2. Compilation des messages..."
python manage.py compilemessages

echo "3. Vérification de la syntaxe Python..."
python -m py_compile apps/competitions/views/dashboard/base.py
python -m py_compile apps/competitions/views/dashboard/referee.py

if [ $? -ne 0 ]; then
    echo "Erreur : La syntaxe Python contient des erreurs"
    exit 1
fi

echo "4. Redémarrage du service Django..."
# Pour un serveur de production avec systemd
if command -v systemctl &> /dev/null; then
    sudo systemctl restart django
    echo "Service Django redémarré via systemctl"
# Pour un serveur de développement
else
    echo "Veuillez redémarrer manuellement votre serveur Django"
fi

echo "5. Vider le cache Django..."
python manage.py shell << EOF
from django.core.cache import cache
cache.clear()
print("Cache Django vidé")
EOF

echo "====================================="
echo "Déploiement terminé avec succès !"
echo "====================================="

echo ""
echo "Corrections appliquées :"
echo "- La vue dashboard détecte automatiquement si un utilisateur avec role='participant' a un profil Judge"
echo "- Si oui, il est redirigé vers le dashboard juge par défaut"
echo "- Support des profils Judge liés directement à User ou via Practitioner"
echo "- La vue referee_dashboard accepte maintenant les pratiquants avec profil juge"
echo ""
echo "Test : Connectez-vous avec l'utilisateur JUGE111 pour vérifier la redirection"