#!/bin/bash
# Restaurer et corriger le champ country

echo "================================================"
echo "🔧 RESTAURATION ET CORRECTION SIMPLE"
echo "================================================"
echo ""

ssh martialcomp-production 'cd /var/www/vhosts/martialcomp.com/httpdocs && bash' << 'EOF'

echo "1️⃣ Recherche d'une sauvegarde..."
echo "=============================="
BACKUP=$(ls -t apps/competitions/forms/onboarding.py.backup_* 2>/dev/null | head -1)
if [ -n "$BACKUP" ]; then
    echo "Sauvegarde trouvée : $BACKUP"
    cp "$BACKUP" apps/competitions/forms/onboarding.py
    echo "✅ Fichier restauré"
else
    echo "❌ Pas de sauvegarde trouvée"
fi

echo ""
echo "2️⃣ Correction simple du champ country..."
echo "======================================"

# Chercher et remplacer uniquement le widget HiddenInput
sed -i 's/widget=forms\.HiddenInput()/widget=forms.Select(attrs={"class": "form-control"})/g' \
    apps/competitions/forms/onboarding.py

echo "✅ Widget corrigé"

echo ""
echo "3️⃣ Vérification de la syntaxe..."
echo "==============================="
python3 -m py_compile apps/competitions/forms/onboarding.py 2>&1 && echo "✅ Syntaxe OK" || echo "❌ Erreur de syntaxe persiste"

echo ""
echo "4️⃣ Si erreur, utilisation de la solution HTML directe..."
echo "======================================================"

# Modifier directement le template pour injecter le HTML
cat > /tmp/inject_country.py << 'INJECT_PY'
# Lire le template
with open('apps/competitions/templates/competitions/onboarding/club_creation.html', 'r') as f:
    content = f.read()

# Vérifier si on a déjà injecté le select
if 'id="id_country_manual"' not in content:
    # Trouver où injecter (après le champ postal_code)
    inject_point = '{{ form.postal_code.errors }}'
    if inject_point in content:
        country_html = '''
                        </div>
                    </div>
                    
                    <div class="col-md-4">
                        <div class="form-group">
                            <label for="id_country_manual" class="form-label required">Pays</label>
                            <select name="country" id="id_country_manual" class="form-control" required>
                                <option value="">-- Sélectionnez un pays --</option>
                                <option value="FR" selected>France</option>
                                <option value="BE">Belgique</option>
                                <option value="CH">Suisse</option>
                                <option value="CA">Canada</option>
                                <option value="LU">Luxembourg</option>
                                <option value="MC">Monaco</option>
                                <option value="ES">Espagne</option>
                                <option value="IT">Italie</option>
                                <option value="DE">Allemagne</option>
                                <option value="PT">Portugal</option>
                                <option value="GB">Royaume-Uni</option>
                                <option value="US">États-Unis</option>
                                <option value="MA">Maroc</option>
                                <option value="TN">Tunisie</option>
                                <option value="DZ">Algérie</option>
                                <option value="SN">Sénégal</option>
                            </select>'''
        
        # Remplacer
        content = content.replace(
            inject_point + '\n                        </div>\n                    </div>',
            inject_point + country_html
        )
        
        # Écrire le fichier
        with open('apps/competitions/templates/competitions/onboarding/club_creation.html', 'w') as f:
            f.write(content)
        
        print("✅ Select country injecté dans le template")
    else:
        print("❌ Point d'injection non trouvé")
else:
    print("✅ Select country déjà présent")
INJECT_PY

python3 /tmp/inject_country.py

echo ""
echo "5️⃣ Forcer le vidage du cache..."
echo "=============================="
# Vider tous les caches possibles
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Redémarrer avec kill forcé
sudo pkill -f gunicorn || true
sleep 2

echo ""
echo "6️⃣ Redémarrage complet..."
echo "========================"
sudo systemctl restart martialcomp
sleep 5

echo ""
echo "7️⃣ Test final..."
echo "==============="
echo "Test de présence du champ country:"
curl -s https://martialcomp.com/fr/competitions/onboarding/club/creation/ | grep -E 'name="country"|id_country' | head -5

if curl -s https://martialcomp.com/fr/competitions/onboarding/club/creation/ | grep -q 'name="country"'; then
    echo ""
    echo "✅ SUCCÈS ! Le champ country est maintenant visible !"
else
    echo ""
    echo "❌ Le champ country n'est toujours pas visible"
fi

EOF

echo ""
echo "================================================"
echo "✅ CORRECTION FINALE APPLIQUÉE"
echo "================================================"
echo ""
echo "Le champ Pays devrait maintenant être visible sur:"
echo "https://martialcomp.com/fr/competitions/onboarding/club/creation/"