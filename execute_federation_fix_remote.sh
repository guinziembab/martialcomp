#!/bin/bash

# Script à exécuter directement sur le serveur de production
# Usage: cat execute_federation_fix_remote.sh | ssh martialcomp-production 'bash -s'

echo "================================================"
echo "🔧 EXÉCUTION DIRECTE DES CORRECTIONS"
echo "================================================"
echo ""

cd /home/martialc/martialcomp

# Créer le script de diagnostic directement
cat > diagnose_federation.sh << 'EOF'
#!/bin/bash
# Script de diagnostic pour l'onboarding fédération en production

echo "=========================================="
echo "🔍 DIAGNOSTIC ONBOARDING FÉDÉRATION"
echo "=========================================="
echo ""

PROJECT_DIR="/home/martialc/martialcomp"
cd "$PROJECT_DIR"

# 1. Vérifier les disciplines
echo "1️⃣ Vérification disciplines..."
python manage.py shell << 'PYEOF'
from apps.competitions.models import Discipline
count = Discipline.objects.filter(is_active=True).count()
print(f"  ✓ Disciplines actives: {count}")
for d in Discipline.objects.filter(is_active=True)[:5]:
    print(f"    - {d.name}")
PYEOF

# 2. Vérifier le formulaire actuel
echo ""
echo "2️⃣ Vérification formulaire..."
if grep -q "CheckboxSelectMultiple" apps/competitions/forms/competitions.py; then
    echo "  ✅ CheckboxSelectMultiple trouvé"
else
    echo "  ❌ CheckboxSelectMultiple MANQUANT"
fi

# 3. Vérifier le template
echo ""
echo "3️⃣ Vérification template..."
if grep -q "{{ form.disciplines }}" apps/competitions/templates/competitions/onboarding/federation_creation.html; then
    echo "  ✅ Template utilise {{ form.disciplines }}"
else
    echo "  ❌ Template ne utilise pas {{ form.disciplines }}"
fi

echo ""
echo "=========================================="
echo "✅ DIAGNOSTIC TERMINÉ"
echo "=========================================="
EOF

chmod +x diagnose_federation.sh
./diagnose_federation.sh

# Demander confirmation avant d'appliquer les corrections
echo ""
read -p "Appliquer les corrections ? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Créer le script de correction
    cat > fix_federation.sh << 'EOF'
#!/bin/bash
# Script de correction pour l'onboarding fédération

echo ""
echo "🔧 APPLICATION DES CORRECTIONS..."
echo ""

PROJECT_DIR="/home/martialc/martialcomp"
BACKUP_DIR="/home/martialc/backups/federation_fix_$(date +%Y%m%d_%H%M%S)"

mkdir -p $BACKUP_DIR
cd $PROJECT_DIR

# 1. Backup des fichiers
echo "📁 Création des backups..."
[ -f "apps/competitions/forms/competitions.py" ] && cp apps/competitions/forms/competitions.py $BACKUP_DIR/
[ -f "apps/competitions/templates/competitions/onboarding/federation_creation.html" ] && cp apps/competitions/templates/competitions/onboarding/federation_creation.html $BACKUP_DIR/
[ -f "config/settings/production.py" ] && cp config/settings/production.py $BACKUP_DIR/

# 2. Corriger le formulaire
echo "1️⃣ Correction du formulaire..."
python << 'PYEOF'
import re

forms_file = "apps/competitions/forms/competitions.py"

# Lire le fichier
with open(forms_file, 'r') as f:
    content = f.read()

# Chercher FederationCreationForm
if 'class FederationCreationForm' in content:
    print("  ✓ FederationCreationForm trouvé")
    
    # Vérifier si disciplines utilise CheckboxSelectMultiple
    if 'CheckboxSelectMultiple' not in content:
        # Ajouter l'import si nécessaire
        if 'from django import forms' in content:
            content = content.replace(
                'from django import forms',
                'from django import forms\nfrom django.forms.widgets import CheckboxSelectMultiple'
            )
        
        # Modifier la classe pour ajouter le champ disciplines avec le bon widget
        pattern = r'(class FederationCreationForm.*?)(class Meta:.*?fields = \[.*?\])'
        
        replacement = r'''\1    disciplines = forms.ModelMultipleChoiceField(
        queryset=Discipline.objects.filter(is_active=True),
        widget=CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label=_("Disciplines")
    )
    
    \2'''
        
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        # S'assurer que disciplines est dans Meta.fields
        if "'disciplines'" not in content and '"disciplines"' not in content:
            content = content.replace(
                "fields = [",
                "fields = ['disciplines', "
            )
        
        # Écrire le fichier
        with open(forms_file, 'w') as f:
            f.write(content)
        
        print("  ✅ Formulaire corrigé avec CheckboxSelectMultiple")
    else:
        print("  ✓ CheckboxSelectMultiple déjà présent")
else:
    print("  ❌ FederationCreationForm introuvable")
PYEOF

# 3. Corriger le template
echo "2️⃣ Correction du template..."
TEMPLATE="apps/competitions/templates/competitions/onboarding/federation_creation.html"

# Créer un template simple qui utilise correctement le formulaire
cat > $TEMPLATE << 'TMPL'
{% extends "competitions/onboarding/base_onboarding.html" %}
{% load i18n %}

{% block title %}{% trans "Créer votre fédération" %}{% endblock %}

{% block content %}
<div class="container mt-5">
    <div class="row justify-content-center">
        <div class="col-md-8">
            <div class="card shadow">
                <div class="card-header bg-primary text-white">
                    <h3 class="mb-0">{% trans "Configuration de votre fédération" %}</h3>
                </div>
                <div class="card-body">
                    <form method="post" enctype="multipart/form-data" id="federation-form">
                        {% csrf_token %}
                        
                        {% if form.errors %}
                            <div class="alert alert-danger">
                                {{ form.errors }}
                            </div>
                        {% endif %}
                        
                        <div class="mb-3">
                            <label class="form-label">{{ form.name.label }}</label>
                            {{ form.name }}
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">{{ form.country.label }}</label>
                            {{ form.country }}
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">{{ form.description.label }}</label>
                            {{ form.description }}
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">{% trans "Disciplines" %}</label>
                            <div class="disciplines-container border rounded p-3" style="max-height: 300px; overflow-y: auto;">
                                {{ form.disciplines }}
                            </div>
                            <small class="text-muted">{% trans "Sélectionnez les disciplines gérées par votre fédération" %}</small>
                        </div>
                        
                        <button type="submit" class="btn btn-primary btn-lg w-100">
                            {% trans "Créer la fédération" %}
                        </button>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>

<style>
.disciplines-container .form-check {
    margin-bottom: 0.5rem;
}
.disciplines-container input[type="checkbox"] {
    margin-right: 0.5rem;
}
</style>
TMPL

echo "  ✅ Template corrigé"

# 4. Désactiver le middleware problématique
echo "3️⃣ Désactivation du middleware..."
python << 'PYEOF'
settings_file = "config/settings/production.py"

try:
    with open(settings_file, 'r') as f:
        content = f.read()
    
    if 'OnboardingRedirectMiddleware' in content and '# OnboardingRedirectMiddleware' not in content:
        content = content.replace(
            "'apps.competitions.middleware.OnboardingRedirectMiddleware'",
            "# 'apps.competitions.middleware.OnboardingRedirectMiddleware'  # TEMPORAIREMENT DÉSACTIVÉ"
        )
        with open(settings_file, 'w') as f:
            f.write(content)
        print("  ✅ OnboardingRedirectMiddleware désactivé")
    else:
        print("  ✓ OnboardingRedirectMiddleware déjà désactivé ou absent")
except:
    print("  ⚠️  Impossible de modifier settings")
PYEOF

# 5. Collecter les fichiers statiques
echo "4️⃣ Collection des fichiers statiques..."
python manage.py collectstatic --noinput

# 6. Redémarrer
echo "5️⃣ Redémarrage..."
touch tmp/restart.txt

echo ""
echo "✅ CORRECTIONS APPLIQUÉES!"
echo ""
echo "Backup créé dans: $BACKUP_DIR"
echo ""
EOF

    chmod +x fix_federation.sh
    sudo ./fix_federation.sh
    
    # Nettoyer
    rm -f diagnose_federation.sh fix_federation.sh
    
    echo ""
    echo "🎯 Tester maintenant sur: https://app.martialcomp.com/competitions/onboarding/federation/"
else
    echo "❌ Corrections annulées"
fi
