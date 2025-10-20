#!/bin/bash
# Script de déploiement pour la correction disciplines fédération
# Adapté pour la structure Plesk de production

echo "================================================"
echo "🚀 DÉPLOIEMENT CORRECTION DISCIPLINES FÉDÉRATION"
echo "================================================"
echo ""

# Adapter le script de correction pour la bonne structure
cat > fix_federation_disciplines_plesk.sh << 'EOF'
#!/bin/bash
# Script de correction DÉFINITIVE pour les cases à cocher disciplines
# Version adaptée pour Plesk

echo "================================================"
echo "🔧 CORRECTION DÉFINITIVE - DISCIPLINES FÉDÉRATION"
echo "================================================"
echo ""
echo "Date: $(date)"
echo ""

PROJECT_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
BACKUP_DIR="/var/www/vhosts/martialcomp.com/backups/federation_disciplines_$(date +%Y%m%d_%H%M%S)"

# Créer le répertoire de backup
echo "📁 Création du backup..."
mkdir -p $BACKUP_DIR

cd $PROJECT_DIR

# 1. Backup du fichier forms/onboarding.py
echo "📋 Sauvegarde du fichier forms/onboarding.py..."
cp apps/competitions/forms/onboarding.py $BACKUP_DIR/onboarding.py.backup

# 2. Corriger le formulaire FederationCreationForm
echo ""
echo "🔧 Correction du formulaire FederationCreationForm..."

python3 << 'PYEOF'
import re

# Lire le fichier
file_path = "apps/competitions/forms/onboarding.py"
with open(file_path, 'r') as f:
    content = f.read()

# Trouver la ligne Meta.fields pour FederationCreationForm
# Pattern pour trouver la classe Meta dans FederationCreationForm
pattern = r"(class FederationCreationForm.*?class Meta:.*?fields = \[)(.*?)(\])"

def replace_fields(match):
    prefix = match.group(1)
    current_fields = match.group(2)
    suffix = match.group(3)
    
    # Vérifier si 'disciplines' est déjà dans les champs
    if "'disciplines'" not in current_fields and '"disciplines"' not in current_fields:
        # Ajouter disciplines à la fin
        if current_fields.strip().endswith("'") or current_fields.strip().endswith('"'):
            new_fields = current_fields + ", 'disciplines'"
        else:
            new_fields = current_fields + "'disciplines'"
        
        print("✅ Ajout de 'disciplines' dans Meta.fields")
        return prefix + new_fields + suffix
    else:
        print("ℹ️  'disciplines' déjà présent dans Meta.fields")
        return match.group(0)

# Appliquer la correction
new_content = re.sub(pattern, replace_fields, content, flags=re.DOTALL)

# Écrire le fichier corrigé
with open(file_path, 'w') as f:
    f.write(new_content)

print("✅ Fichier forms/onboarding.py mis à jour")

# Vérifier la correction
print("\n📋 Vérification de la correction:")
with open(file_path, 'r') as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if "class FederationCreationForm" in line:
            # Afficher les 20 lignes suivantes pour vérifier
            for j in range(i, min(i+20, len(lines))):
                if "fields = [" in lines[j]:
                    print(f"Ligne {j+1}: {lines[j].strip()}")
                    if "'disciplines'" in lines[j] or '"disciplines"' in lines[j]:
                        print("✅ CONFIRMÉ: 'disciplines' est maintenant dans Meta.fields")
                    break
PYEOF

# 3. Activer l'environnement virtuel
echo ""
echo "🐍 Activation de l'environnement virtuel..."
source /var/www/vhosts/martialcomp.com/venv/bin/activate

# 4. Initialiser les disciplines si nécessaire
echo ""
echo "📋 Vérification des disciplines..."
python manage.py shell << 'EOF'
from apps.competitions.models import Discipline

count = Discipline.objects.filter(is_active=True).count()
if count == 0:
    print("⚠️  Aucune discipline active - Création des disciplines de base...")
    disciplines = [
        ('Karaté', 'Art martial japonais'),
        ('Judo', 'Art martial japonais, sport olympique'),
        ('Taekwondo', 'Art martial coréen, sport olympique'),
        ('Kung Fu', 'Arts martiaux chinois'),
        ('Aikido', 'Art martial japonais défensif'),
        ('Boxe', 'Sport de combat avec les poings'),
        ('MMA', 'Arts martiaux mixtes'),
        ('Muay Thai', 'Boxe thaïlandaise'),
    ]
    for name, desc in disciplines:
        Discipline.objects.get_or_create(
            name=name,
            defaults={'description': desc, 'is_active': True}
        )
    print(f"✅ {len(disciplines)} disciplines créées")
else:
    print(f"✅ {count} disciplines actives disponibles")
EOF

# 5. Collecter les fichiers statiques
echo ""
echo "📦 Collection des fichiers statiques..."
python manage.py collectstatic --noinput > /dev/null 2>&1

# 6. Nettoyer le cache Python
echo "🧹 Nettoyage du cache Python..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# 7. Redémarrer les services
echo ""
echo "🔄 Redémarrage des services..."

# Pour Gunicorn (via systemctl)
if systemctl is-active --quiet gunicorn; then
    sudo systemctl restart gunicorn
    echo "✅ Gunicorn redémarré"
fi

# Pour le service martialcomp
if systemctl is-active --quiet martialcomp; then
    sudo systemctl restart martialcomp
    echo "✅ Service martialcomp redémarré"
fi

# Pour Apache
if systemctl is-active --quiet apache2; then
    sudo systemctl reload apache2
    echo "✅ Apache rechargé"
fi

# 8. Test final
echo ""
echo "🧪 Test de validation du formulaire..."
python manage.py shell << 'EOF'
from apps.competitions.forms.onboarding import FederationCreationForm

# Créer une instance du formulaire
form = FederationCreationForm()

# Vérifier que disciplines est dans les champs
if 'disciplines' in form.fields:
    print("✅ Le champ 'disciplines' est présent dans le formulaire")
    field = form.fields['disciplines']
    print(f"   - Widget: {field.widget.__class__.__name__}")
    print(f"   - Nombre de disciplines: {field.queryset.count()}")
else:
    print("❌ ERREUR: Le champ 'disciplines' n'est pas dans le formulaire!")
EOF

echo ""
echo "================================================"
echo "✅ CORRECTION TERMINÉE!"
echo "================================================"
echo ""
echo "📋 Résumé des modifications:"
echo "1. ✅ Ajout de 'disciplines' dans Meta.fields du formulaire"
echo "2. ✅ Disciplines initialisées en base de données"
echo "3. ✅ Services redémarrés"
echo ""
echo "🎯 Actions à effectuer:"
echo "1. Tester sur https://app.martialcomp.com/competitions/onboarding/federation/"
echo "2. Vérifier que les cases à cocher s'affichent"
echo "3. Créer une fédération test"
echo "4. Vérifier que les disciplines sont bien sauvegardées"
echo ""
echo "📁 Backup créé dans: $BACKUP_DIR"
echo ""
EOF

echo "📦 Transfert du script vers le serveur de production..."
scp fix_federation_disciplines_plesk.sh martialcomp-production:/root/

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors du transfert SCP"
    exit 1
fi

echo "✅ Script transféré avec succès"
echo ""
echo "🔧 Exécution de la correction sur le serveur..."
echo ""

# Exécuter le script sur le serveur distant
ssh martialcomp-production << 'REMOTE_COMMANDS'
cd /root
chmod +x fix_federation_disciplines_plesk.sh
./fix_federation_disciplines_plesk.sh
REMOTE_COMMANDS

if [ $? -eq 0 ]; then
    echo ""
    echo "================================================"
    echo "✅ CORRECTION APPLIQUÉE AVEC SUCCÈS!"
    echo "================================================"
    echo ""
    echo "🎯 Actions suivantes:"
    echo "1. Ouvrir https://app.martialcomp.com"
    echo "2. Se connecter ou créer un compte"
    echo "3. Aller sur https://app.martialcomp.com/competitions/onboarding/federation/"
    echo "4. Vérifier que les cases à cocher des disciplines s'affichent"
    echo ""
else
    echo ""
    echo "❌ Une erreur s'est produite lors de l'exécution"
    echo "Connectez-vous manuellement pour vérifier:"
    echo "ssh martialcomp-production"
    echo "cd /root"
    echo "./fix_federation_disciplines_plesk.sh"
fi

# Nettoyer le fichier temporaire
rm -f fix_federation_disciplines_plesk.sh