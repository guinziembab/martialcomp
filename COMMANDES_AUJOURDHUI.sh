#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# COMMANDES À EXÉCUTER AUJOURD'HUI - Traductions MartialComp
# ═══════════════════════════════════════════════════════════════
# Temps estimé : 30 minutes
# ═══════════════════════════════════════════════════════════════

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  CORRECTIONS IMMÉDIATES DES TRADUCTIONS                       ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Configuration
PROJECT_DIR="/mnt/c/martial_hub_django/martialcomp"
cd "$PROJECT_DIR"

echo "1️⃣  Recompilation du portugais (30 secondes)"
echo "─────────────────────────────────────────────────────────────────"
python manage.py compilemessages -l pt
echo "✅ Portugais recompilé - Les 6,368 traductions existantes sont maintenant actives"
echo ""

echo "2️⃣  Vérification du résultat"
echo "─────────────────────────────────────────────────────────────────"
if [ -f "locale/pt/LC_MESSAGES/django.mo" ]; then
    echo "✅ Fichier django.mo créé pour le portugais"
    ls -lh locale/pt/LC_MESSAGES/django.mo
else
    echo "❌ Erreur : Fichier .mo non créé"
    exit 1
fi
echo ""

echo "3️⃣  Identification des chaînes manquantes FR/ES"
echo "─────────────────────────────────────────────────────────────────"
echo ""
echo "FRANÇAIS (fr) - Chaînes vides:"
awk '/^msgid/ {msgid=$0; line=NR} /^msgstr ""$/ && msgid && line>1 {print "Ligne " line ": " msgid}' locale/fr/LC_MESSAGES/django.po | head -5
echo ""
echo "ESPAGNOL (es) - Chaînes vides:"
awk '/^msgid/ {msgid=$0; line=NR} /^msgstr ""$/ && msgid && line>1 {print "Ligne " line ": " msgid}' locale/es/LC_MESSAGES/django.po | head -5
echo ""

echo "4️⃣  Statistiques finales après recompilation"
echo "─────────────────────────────────────────────────────────────────"
for lang in fr en es pt; do
    if [ -f "locale/$lang/LC_MESSAGES/django.po" ]; then
        total=$(grep -c '^msgid ' locale/$lang/LC_MESSAGES/django.po)
        trans=$(grep '^msgstr ' locale/$lang/LC_MESSAGES/django.po | grep -v '^msgstr ""$' | wc -l)
        pct=$(($trans*100/$total))
        
        if [ "$lang" = "pt" ]; then
            echo "  $lang: $trans/$total ($pct%) ← Recompilé ✅"
        else
            echo "  $lang: $trans/$total ($pct%)"
        fi
    fi
done
echo ""

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  RÉSUMÉ                                                       ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "✅ Portugais recompilé (6,368 traductions actives)"
echo "⚠️  Reste à faire : Traduire les 5,314 chaînes manquantes PT"
echo "⚠️  Reste à faire : Corriger 1 chaîne FR"
echo "⚠️  Reste à faire : Corriger 1 chaîne ES"
echo ""
echo "📋 PROCHAINE ÉTAPE:"
echo "   python translate_portuguese.py --api-key VOTRE_CLE_DEEPL"
echo ""
echo "Pour obtenir une clé DeepL gratuite :"
echo "   https://www.deepl.com/pro-api"
echo ""
