#!/bin/bash
# Script final pour résoudre définitivement l'erreur Practitioner

echo "🚨 CORRECTION FINALE - PRACTITIONER ADMIN"
echo "========================================"

cd /var/www/vhosts/martialcomp.com/httpdocs

# 1. Créer un admin ultra-simple
echo "📝 Création d'un admin minimal..."
cat > apps/competitions/admin.py << 'EOF'
from django.contrib import admin
from .models import *

# Admin minimal pour Practitioner
@admin.register(Practitioner)
class MinimalPractitionerAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'organization']
    search_fields = ['first_name', 'last_name']
    list_filter = ['gender', 'status']
    
    # Exclure TOUS les champs liés aux disciplines
    exclude = ['disciplines', 'primary_discipline', 'secondary_disciplines']
    
    def get_queryset(self, request):
        # Pas de prefetch_related sur les disciplines
        return super().get_queryset(request).select_related('organization')

# Enregistrer les autres modèles normalement
for model in [Competition, Category, Judge, Registration, Club, Federation, Discipline]:
    try:
        if model not in admin.site._registry:
            admin.site.register(model)
    except:
        pass

print("✅ Admin Practitioner minimal chargé")
EOF

# 2. Supprimer le dossier admin/ s'il existe
if [ -d "apps/competitions/admin" ]; then
    echo "🗑️  Suppression du dossier admin/..."
    rm -rf apps/competitions/admin
fi

# 3. Nettoyer complètement
echo "🧹 Nettoyage complet..."
find . -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# 4. Vérifier la syntaxe Python
echo "🔍 Vérification de la syntaxe..."
python -m py_compile apps/competitions/admin.py

# 5. Redémarrer Apache
echo "🔄 Redémarrage d'Apache..."
systemctl restart apache2

echo "✅ Correction appliquée !"
echo ""
echo "Testez maintenant : https://martialcomp.com/fr/admin/competitions/practitioner/"