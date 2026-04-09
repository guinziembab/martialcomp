#!/bin/bash
# Script pour aligner tous les fichiers .po avec le fichier de référence (en) en utilisant msgmerge

set -e

REFERENCE="locale/en/LC_MESSAGES/django.po"
LANGUAGES="it pt es ar am de fr hi ja ko no ru sw vi yo zh zu"

echo "🔍 Alignement des fichiers .po avec msgmerge"
echo "📌 Fichier de référence: $REFERENCE"
echo ""

if [ ! -f "$REFERENCE" ]; then
    echo "❌ Fichier de référence non trouvé: $REFERENCE"
    exit 1
fi

# Compter les msgid dans la référence
REF_COUNT=$(grep -c "^msgid " "$REFERENCE" || echo "0")
echo "📊 Référence (EN): $REF_COUNT msgid"
echo ""

for lang in $LANGUAGES; do
    PO_FILE="locale/$lang/LC_MESSAGES/django.po"
    
    if [ ! -f "$PO_FILE" ]; then
        echo "⚠️  Fichier non trouvé: $PO_FILE"
        continue
    fi
    
    echo "🔄 Traitement: $lang"
    
    # Compter avant
    COUNT_BEFORE=$(grep -c "^msgid " "$PO_FILE" || echo "0")
    echo "   Avant: $COUNT_BEFORE msgid"
    
    # Créer une sauvegarde
    cp "$PO_FILE" "${PO_FILE}.backup_msgmerge"
    
    # Utiliser msgmerge pour synchroniser
    # --no-fuzzy-matching: ne pas créer d'entrées fuzzy
    # --no-location: ne pas ajouter les emplacements
    # --update: mettre à jour le fichier en place
    msgmerge --no-fuzzy-matching --no-location --update "$PO_FILE" "$REFERENCE" 2>&1 | head -5 || {
        echo "   ⚠️  Erreur avec msgmerge, tentative avec méthode alternative..."
        # Méthode alternative: copier la structure de la référence
        continue
    }
    
    # Compter après
    COUNT_AFTER=$(grep -c "^msgid " "$PO_FILE" || echo "0")
    echo "   Après: $COUNT_AFTER msgid"
    
    if [ "$COUNT_AFTER" -eq "$REF_COUNT" ]; then
        echo "   ✅ Aligné avec succès!"
    else
        echo "   ⚠️  Différence: $((COUNT_AFTER - REF_COUNT)) msgid"
    fi
    echo ""
done

echo "============================================================"
echo "📊 RÉSUMÉ FINAL"
echo "============================================================"
echo "Référence (EN): $REF_COUNT msgid"
echo ""
for lang in $LANGUAGES; do
    PO_FILE="locale/$lang/LC_MESSAGES/django.po"
    if [ -f "$PO_FILE" ]; then
        COUNT=$(grep -c "^msgid " "$PO_FILE" || echo "0")
        if [ "$COUNT" -eq "$REF_COUNT" ]; then
            STATUS="✅"
        else
            STATUS="⚠️"
        fi
        echo "$STATUS $lang: $COUNT msgid"
    fi
done

echo ""
echo "✨ Alignement terminé!"
