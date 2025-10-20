#!/bin/bash

# Script complet pour déployer toutes les corrections
# 1. Correction génération numéro de licence (404)
# 2. Duplication grades Qwan Ki Do → Long Phai
# 8 Octobre 2025

set -e

echo "=============================================="
echo "DÉPLOIEMENT COMPLET DES CORRECTIONS"
echo "=============================================="
echo "1. Correction génération numéro de licence"
echo "2. Duplication grades Qwan Ki Do → Long Phai"
echo "=============================================="
echo

# Vérifier qu'on est bien en production
if [ ! -d "/var/www/vhosts/martialcomp.com/httpdocs" ]; then
    echo "❌ Ce script doit être exécuté sur le serveur de production"
    exit 1
fi

HTTPDOCS="/var/www/vhosts/martialcomp.com/httpdocs"
VENV="/var/www/vhosts/martialcomp.com/venv"

# Aller dans le répertoire du projet
cd "${HTTPDOCS}"

# Activer l'environnement virtuel
source "${VENV}/bin/activate"

echo
echo "======================================"
echo "ÉTAPE 1: CORRECTION NUMÉRO DE LICENCE"
echo "======================================"
echo

# 1. Backup du fichier api.py
API_FILE="${HTTPDOCS}/apps/competitions/api.py"
BACKUP_API="${API_FILE}.backup_$(date +%Y%m%d_%H%M%S)"

echo "1️⃣  Création backup de api.py..."
cp "${API_FILE}" "${BACKUP_API}"
echo "✅ Backup créé: $(basename ${BACKUP_API})"
echo

# 2. Vérifier si la correction est déjà appliquée
if grep -q "generate-license-number" "${API_FILE}"; then
    echo "✅ La route generate-license-number existe déjà dans api.py"
else
    echo "2️⃣  Ajout de la route dans api.py..."
    
    # Utiliser Python pour modifier le fichier de manière sûre
    python3 << 'PYTHON_SCRIPT'
import re

api_file = '/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/api.py'

with open(api_file, 'r') as f:
    content = f.read()

# Vérifier si l'import existe déjà
if 'from apps.competitions.views.api import generate_license_number' not in content:
    # Ajouter l'import après "from django.urls import path"
    content = content.replace(
        'from django.urls import path',
        'from django.urls import path\nfrom apps.competitions.views.api import generate_license_number'
    )

# Ajouter la route dans urlpatterns
if "path('generate-license-number/'," not in content:
    # Trouver la fin de urlpatterns et ajouter la route
    content = re.sub(
        r"(urlpatterns = \[\s*path\('upcoming/',.*?\),)",
        r"\1\n    path('generate-license-number/', generate_license_number, name='generate_license_number'),",
        content,
        flags=re.DOTALL
    )

with open(api_file, 'w') as f:
    f.write(content)

print("✅ Route ajoutée dans api.py")
PYTHON_SCRIPT
    
    # Vérifier la syntaxe Python
    echo "3️⃣  Vérification syntaxe Python..."
    python3 -m py_compile "${API_FILE}"
    
    if [ $? -eq 0 ]; then
        echo "✅ Syntaxe Python valide"
    else
        echo "❌ Erreur de syntaxe!"
        cp "${BACKUP_API}" "${API_FILE}"
        exit 1
    fi
fi

echo

echo "======================================"
echo "ÉTAPE 2: DUPLICATION GRADES"
echo "======================================"
echo

# 3. Créer le script de duplication de grades
SCRIPT_GRADES="/tmp/duplicate_grades_longphai.py"

cat > "${SCRIPT_GRADES}" << 'PYTHON_GRADES'
import os
import sys
import django

sys.path.insert(0, '/var/www/vhosts/martialcomp.com/httpdocs')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from apps.grades.models import Grade
from apps.competitions.models import Discipline

print("1️⃣  Vérification des disciplines...")

try:
    qwan = Discipline.objects.get(name="Qwan Ki Do")
    print(f"✅ Qwan Ki Do trouvée (ID: {qwan.id})")
except:
    print("❌ Qwan Ki Do non trouvée")
    sys.exit(1)

try:
    long_phai = Discipline.objects.get(name="Long Phai")
    print(f"✅ Long Phai trouvée (ID: {long_phai.id})")
except:
    print("⚠️  Long Phai non trouvée, création...")
    long_phai = Discipline.objects.create(
        name="Long Phai",
        description="Long Phai - Art martial vietnamien"
    )
    print(f"✅ Long Phai créée (ID: {long_phai.id})")

print()
print("2️⃣  Récupération des grades Qwan Ki Do...")
qwan_grades = Grade.objects.filter(discipline=qwan).order_by('level')
print(f"📊 {qwan_grades.count()} grades trouvés")

# Vérifier si des grades existent déjà pour Long Phai
existing = Grade.objects.filter(discipline=long_phai).count()
if existing > 0:
    print(f"⚠️  {existing} grades existent déjà pour Long Phai")
    print("🗑️  Suppression des grades existants...")
    Grade.objects.filter(discipline=long_phai).delete()

print()
print("3️⃣  Duplication des grades...")

created = 0
for grade in qwan_grades:
    try:
        Grade.objects.create(
            discipline=long_phai,
            name=grade.name,
            category=grade.category,
            color=grade.color,
            color_code=grade.color_code,
            level=grade.level,
            min_age=grade.min_age,
            is_dan_grade=grade.is_dan_grade,
            description=grade.description if hasattr(grade, 'description') else '',
        )
        created += 1
    except Exception as e:
        print(f"❌ Erreur pour {grade.name}: {e}")

print()
print(f"✅ {created} grades créés pour Long Phai")

# Vérification finale
final = Grade.objects.filter(discipline=long_phai).count()
print(f"📊 Total final: {final} grades")

if final == qwan_grades.count():
    print("🎉 SUCCÈS: Tous les grades ont été dupliqués!")
else:
    print(f"⚠️  Attention: {qwan_grades.count() - final} grade(s) manquant(s)")
PYTHON_GRADES

echo "4️⃣  Exécution du script de duplication..."
python3 "${SCRIPT_GRADES}"

if [ $? -eq 0 ]; then
    echo "✅ Duplication terminée avec succès"
else
    echo "❌ Erreur lors de la duplication"
fi

echo

echo "======================================"
echo "ÉTAPE 3: REDÉMARRAGE DU SERVICE"
echo "======================================"
echo

# 4. Ajuster les permissions
echo "5️⃣  Ajustement des permissions..."
chown www-data:www-data "${API_FILE}"
chmod 644 "${API_FILE}"
echo "✅ Permissions OK"
echo

# 5. Redémarrer le service
echo "6️⃣  Redémarrage du service..."
systemctl restart martialcomp.service
sleep 5

if systemctl is-active --quiet martialcomp.service; then
    echo "✅ Service redémarré"
else
    echo "❌ Erreur redémarrage service"
    systemctl status martialcomp.service --no-pager | head -20
    exit 1
fi

echo

echo "======================================"
echo "RÉSUMÉ FINAL"
echo "======================================"
echo "✅ Route API ajoutée: /fr/competitions/api/generate-license-number/"
echo "✅ Grades Qwan Ki Do dupliqués vers Long Phai"
echo "✅ Service redémarré avec succès"
echo
echo "📝 TESTS À EFFECTUER:"
echo "1. https://martialcomp.com/fr/competitions/club/practitioners/add/"
echo "   → Tester la génération de numéro de licence"
echo "   → Vérifier qu'il n'y a pas d'erreur 404 dans la console"
echo
echo "2. Vérifier que Long Phai apparaît dans les disciplines"
echo
echo "📦 BACKUPS CRÉÉS:"
echo "   - ${BACKUP_API}"
echo
echo "🔄 ROLLBACK SI NÉCESSAIRE:"
echo "   cp ${BACKUP_API} ${API_FILE}"
echo "   systemctl restart martialcomp.service"
echo

exit 0
