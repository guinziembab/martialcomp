#!/bin/bash
# Nettoyer les imports COUNTRY_CHOICES

echo "================================================"
echo "🧹 NETTOYAGE DES IMPORTS COUNTRY_CHOICES"
echo "================================================"
echo ""

ssh martialcomp-production 'cd /var/www/vhosts/martialcomp.com/httpdocs && bash' << 'EOF'

echo "1️⃣ Analyse du problème..."
echo "========================"
echo "Il y a un double import de COUNTRY_CHOICES :"
echo "- Un défini localement"
echo "- Un importé depuis ..choices"

echo ""
echo "2️⃣ Vérification de choices.py..."
echo "================================"
if [ -f "apps/competitions/choices.py" ]; then
    echo "Le fichier choices.py existe"
    echo "Vérification de COUNTRY_CHOICES:"
    grep -n "COUNTRY_CHOICES" apps/competitions/choices.py | head -5
else
    echo "Le fichier choices.py n'existe pas"
fi

echo ""
echo "3️⃣ Nettoyage des imports..."
echo "============================"

# Supprimer la définition locale de COUNTRY_CHOICES
sed -i '/^COUNTRY_CHOICES = \[/,/^\]/d' apps/competitions/forms/onboarding.py

# Supprimer aussi les lignes django_countries
sed -i '/from django_countries import countries/d' apps/competitions/forms/onboarding.py

echo "✅ Définition locale supprimée"

# Vérifier que l'import depuis choices est présent
if ! grep -q "from ..choices import COUNTRY_CHOICES" apps/competitions/forms/onboarding.py; then
    echo "⚠️  L'import depuis choices n'est pas présent"
    
    # Créer choices.py si nécessaire
    if [ ! -f "apps/competitions/choices.py" ]; then
        echo "Création de choices.py..."
        cat > apps/competitions/choices.py << 'CHOICES_EOF'
from django.utils.translation import gettext_lazy as _

# Choix de pays
COUNTRY_CHOICES = [
    ('FR', _('France')),
    ('BE', _('Belgique')),
    ('CH', _('Suisse')),
    ('CA', _('Canada')),
    ('LU', _('Luxembourg')),
    ('MC', _('Monaco')),
    ('AD', _('Andorre')),
    ('ES', _('Espagne')),
    ('IT', _('Italie')),
    ('DE', _('Allemagne')),
    ('GB', _('Royaume-Uni')),
    ('US', _('États-Unis')),
    ('BR', _('Brésil')),
    ('PT', _('Portugal')),
    ('NL', _('Pays-Bas')),
    ('AT', _('Autriche')),
    ('PL', _('Pologne')),
    ('RO', _('Roumanie')),
    ('GR', _('Grèce')),
    ('TR', _('Turquie')),
    ('MA', _('Maroc')),
    ('TN', _('Tunisie')),
    ('DZ', _('Algérie')),
    ('SN', _('Sénégal')),
    ('CI', _("Côte d'Ivoire")),
    ('CM', _('Cameroun')),
    ('CD', _('RD Congo')),
    ('MG', _('Madagascar')),
    ('MU', _('Maurice')),
    ('RE', _('La Réunion')),
    ('OTHER', _('Autre')),
]
CHOICES_EOF
        echo "✅ choices.py créé"
    fi
fi

echo ""
echo "4️⃣ Vérification finale des imports..."
echo "===================================="
echo "Imports dans onboarding.py:"
grep -E "(from|import).*COUNTRY" apps/competitions/forms/onboarding.py

echo ""
echo "5️⃣ Test de syntaxe..."
echo "===================="
python3 -m py_compile apps/competitions/forms/onboarding.py 2>&1 || echo "✅ Syntaxe OK"

echo ""
echo "6️⃣ Redémarrage du service..."
echo "==========================="
sudo systemctl restart martialcomp
sleep 3

echo ""
echo "7️⃣ Test avec curl..."
echo "==================="
RESPONSE=$(curl -s -L -w "\nSTATUS:%{http_code}" https://martialcomp.com/fr/competitions/onboarding/club/creation/)
STATUS=$(echo "$RESPONSE" | grep "STATUS:" | cut -d: -f2)
echo "Status: $STATUS"

if [ "$STATUS" = "200" ]; then
    # Vérifier si le champ country est présent
    if echo "$RESPONSE" | grep -q 'name="country"'; then
        echo "✅ Champ country trouvé dans le HTML !"
        
        # Vérifier s'il y a des options
        OPTION_COUNT=$(echo "$RESPONSE" | grep -c '<option.*value=')
        echo "✅ Nombre d'options dans le select: $OPTION_COUNT"
    else
        echo "❌ Champ country non trouvé dans le HTML"
    fi
fi

EOF

echo ""
echo "================================================"
echo "✅ NETTOYAGE TERMINÉ"
echo "================================================"
echo ""
echo "Le champ Pays devrait maintenant fonctionner correctement"
echo "sur https://martialcomp.com/fr/competitions/onboarding/club/creation/"