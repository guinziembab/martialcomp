#!/bin/bash
# Script pour ajouter le champ logo et corriger les dates dans le template

echo "=== AJOUT DU CHAMP LOGO ET CORRECTION DES DATES ==="

ssh martialcomp-production << 'EOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1. Sauvegarde du template..."
sudo cp apps/competitions/templates/competitions/competition/create.html apps/competitions/templates/competitions/competition/create.html.backup_logo_dates

echo "2. Vérification et ajout du champ logo..."
# Vérifier si le champ logo existe déjà
if ! grep -q "form\.logo" apps/competitions/templates/competitions/competition/create.html; then
    echo "Ajout du champ logo au template..."
    
    # Ajouter le champ logo après le champ description
    sudo python3 << 'PYTHON_SCRIPT'
import re

with open('apps/competitions/templates/competitions/competition/create.html', 'r') as f:
    content = f.read()

# Chercher où ajouter le champ logo (après la description)
if '{{ form.logo }}' not in content:
    # Pattern pour trouver la fin du champ description
    pattern = r'({{ form\.description }}[\s\S]*?</div>\s*</div>)'
    
    # HTML du champ logo
    logo_field = """
                    
                    <!-- Logo/Bannière -->
                    <div class="mb-3">
                        <label for="{{ form.logo.id_for_label }}" class="form-label">
                            <i class="fas fa-image me-1"></i> {% trans "Logo/Bannière de la compétition" %}
                        </label>
                        {{ form.logo }}
                        {% if form.logo.help_text %}
                            <small class="form-text text-muted">{{ form.logo.help_text }}</small>
                        {% endif %}
                        {% if form.logo.errors %}
                            <div class="invalid-feedback d-block">
                                {% for error in form.logo.errors %}{{ error }}{% endfor %}
                            </div>
                        {% endif %}
                        {% if competition.logo %}
                            <div class="mt-2">
                                <img src="{{ competition.logo.url }}" alt="Logo actuel" class="img-thumbnail" style="max-height: 100px;">
                                <small class="d-block text-muted">{% trans "Logo actuel" %}</small>
                            </div>
                        {% endif %}
                    </div>"""
    
    # Remplacer
    replacement = r'\1' + logo_field
    content = re.sub(pattern, replacement, content, count=1)
    
    with open('apps/competitions/templates/competitions/competition/create.html', 'w') as f:
        f.write(content)
    
    print("✓ Champ logo ajouté au template")
else:
    print("✓ Champ logo déjà présent dans le template")
PYTHON_SCRIPT
fi

echo "3. Ajout du script JavaScript pour les dates..."
# Ajouter le script JS avant la fermeture du block content
if ! grep -q "date_format_fix.js" apps/competitions/templates/competitions/competition/create.html; then
    sudo sed -i '/<\/script>/,$s|{% endblock %}|<script src="{% static '\''competitions/js/date_format_fix.js'\'' %}"></script>\n{% endblock %}|' apps/competitions/templates/competitions/competition/create.html
    echo "✓ Script de formatage des dates ajouté"
else
    echo "✓ Script de formatage des dates déjà présent"
fi

echo "4. Ajout d'un script inline pour gérer flatpickr..."
# Ajouter un script pour gérer flatpickr spécifiquement
sudo tee -a apps/competitions/templates/competitions/competition/create.html << 'INLINE_SCRIPT'

<script>
document.addEventListener('DOMContentLoaded', function() {
    // Désactiver flatpickr sur les champs de date si il pose problème
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        if (input._flatpickr) {
            input._flatpickr.destroy();
        }
    });
    
    // S'assurer que les dates sont au bon format
    ['id_start_date', 'id_end_date', 'id_registration_deadline'].forEach(id => {
        const field = document.getElementById(id);
        if (field && field.value) {
            // Convertir DD/MM/YYYY en YYYY-MM-DD si nécessaire
            const value = field.value;
            if (value.match(/^\d{2}\/\d{2}\/\d{4}$/)) {
                const parts = value.split('/');
                field.value = `${parts[2]}-${parts[1]}-${parts[0]}`;
            }
        }
    });
});
</script>
INLINE_SCRIPT

echo "5. Correction des permissions..."
sudo chown www-data:www-data apps/competitions/templates/competitions/competition/create.html

echo "6. Redémarrage de Gunicorn..."
sudo pkill -HUP -f gunicorn

echo "✓ Toutes les corrections appliquées"
EOF

echo ""
echo "=== TERMINÉ ==="
echo "Le champ logo et les corrections de dates ont été appliqués."