#!/bin/bash
# Script de déploiement des corrections API Training
# À exécuter sur le serveur de production

echo "=== Déploiement des corrections API Training ==="

# 1. Créer une sauvegarde
echo "1. Sauvegarde des fichiers existants..."
cp /var/www/martialcomp/api/mobile_api.py /var/www/martialcomp/api/mobile_api.py.backup_$(date +%Y%m%d_%H%M%S)
cp /var/www/martialcomp/api/mobile_urls.py /var/www/martialcomp/api/mobile_urls.py.backup_$(date +%Y%m%d_%H%M%S)

# 2. Copier les fichiers depuis le dépôt local (si disponible) ou coller le contenu
echo "2. Mise à jour des fichiers API..."

# Si vous avez accès au dépôt Git sur le serveur:
# cd /var/www/martialcomp && git pull origin fix/federation-dashboard

# 3. Redémarrer Gunicorn
echo "3. Redémarrage de Gunicorn..."
GUNICORN_PID=$(pgrep -f "gunicorn.*martialcomp")
if [ -n "$GUNICORN_PID" ]; then
    echo "   Envoi du signal HUP au processus Gunicorn ($GUNICORN_PID)..."
    kill -HUP $GUNICORN_PID
    echo "   Gunicorn rechargé avec succès"
else
    echo "   ATTENTION: Processus Gunicorn non trouvé!"
    echo "   Tentative de redémarrage via systemctl..."
    systemctl restart gunicorn || service gunicorn restart
fi

# 4. Vérifier que le serveur répond
echo "4. Vérification de l'API..."
sleep 2
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/health/ | grep -q "200" && echo "   API OK" || echo "   ERREUR: API non accessible"

# 5. Tester les endpoints training
echo "5. Test des endpoints training..."
echo "   - /api/training/sessions/: $(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/training/sessions/)"
echo "   - /api/training/categories/: $(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/training/categories/)"

echo ""
echo "=== Déploiement terminé ==="
echo "Si les tests échouent, restaurez les sauvegardes :"
echo "cp /var/www/martialcomp/api/mobile_api.py.backup_* /var/www/martialcomp/api/mobile_api.py"
echo "cp /var/www/martialcomp/api/mobile_urls.py.backup_* /var/www/martialcomp/api/mobile_urls.py"
