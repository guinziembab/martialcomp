#!/bin/bash

# Fix d'urgence pour l'erreur Discipline.get()

echo "=== FIX D'URGENCE - Correction erreur Discipline.get() ==="

cd /var/www/vhosts/martialcomp.com/httpdocs

# Créer le fichier wsgi_startup_fix.py s'il n'existe pas
echo "Création/mise à jour de wsgi_startup_fix.py..."
cat > wsgi_startup_fix.py << 'EOF'
"""
Fix de démarrage WSGI pour corriger les erreurs de Discipline
"""
import logging

logger = logging.getLogger(__name__)

try:
    # Importer le modèle Discipline
    from apps.competitions.models import Discipline
    
    # S'assurer que Discipline n'a pas de méthode get() directe
    if hasattr(Discipline, 'get'):
        logger.warning("Suppression de la méthode get() non standard sur Discipline")
        delattr(Discipline, 'get')
    
    # Ajouter une propriété pour rediriger les appels incorrects
    original_getattr = Discipline.__getattribute__
    
    def patched_getattr(self, name):
        if name == 'get' and not hasattr(self, 'get'):
            logger.error("Tentative d'accès à Discipline.get() - utilisez Discipline.objects.get() à la place!")
            raise AttributeError(
                "Discipline n'a pas de méthode get(). "
                "Utilisez Discipline.objects.get() pour récupérer un objet."
            )
        return original_getattr(self, name)
    
    Discipline.__getattribute__ = patched_getattr
    
    logger.info("✓ Patch Discipline appliqué avec succès")
    
except Exception as e:
    logger.error(f"Erreur lors de l'application du patch Discipline: {e}")
    # Ne pas faire crasher le serveur si le patch échoue
    pass
EOF

# Définir les permissions
chown www-data:www-data wsgi_startup_fix.py
chmod 644 wsgi_startup_fix.py

echo "wsgi_startup_fix.py créé/mis à jour."

# Rechercher et corriger les fichiers qui utilisent Discipline.get()
echo ""
echo "Recherche des fichiers utilisant Discipline.get()..."
grep -r "Discipline\.get(" apps/ 2>/dev/null | head -10

# Créer un script de correction pour l'admin si nécessaire
if [ -f "apps/competitions/admin.py" ]; then
    echo ""
    echo "Vérification de admin.py..."
    if grep -q "Discipline\.get(" apps/competitions/admin.py; then
        echo "⚠️  Erreur trouvée dans admin.py - création d'une sauvegarde"
        cp apps/competitions/admin.py apps/competitions/admin.py.backup_$(date +%Y%m%d_%H%M%S)
        
        # Corriger l'erreur
        sed -i 's/Discipline\.get(/Discipline.objects.get(/g' apps/competitions/admin.py
        echo "✓ admin.py corrigé"
    fi
fi

# Vérifier aussi dans les vues
for file in $(find apps/competitions/views -name "*.py" -type f 2>/dev/null); do
    if grep -q "Discipline\.get(" "$file"; then
        echo "⚠️  Erreur trouvée dans $file"
        cp "$file" "${file}.backup_$(date +%Y%m%d_%H%M%S)"
        sed -i 's/Discipline\.get(/Discipline.objects.get(/g' "$file"
        echo "✓ $file corrigé"
    fi
done

# Redémarrer Apache
echo ""
echo "Redémarrage d'Apache..."
systemctl restart apache2

# Vérifier le statut
systemctl status apache2 --no-pager | head -10

echo ""
echo "=== Fix appliqué ==="
echo ""
echo "Testez maintenant avec : curl -I https://martialcomp.com"