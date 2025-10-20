#!/bin/bash
# Vérifier les traductions manquantes

STRINGS=(
    "Navigation complète"
    "Vue améliorée"
    "Grades et Examens"
    "Suivi projets"
    "Gestion QR"
    "Rôles & Permissions"
    "Rôles disponibles"
)

LANG="en"
PO_FILE="locale/$LANG/LC_MESSAGES/django.po"

echo "Vérification des traductions manquantes en $LANG:"
echo "================================================"
echo ""

missing=0
for str in "${STRINGS[@]}"; do
    if grep -q "^msgid \"$str\"" "$PO_FILE"; then
        echo "✅ \"$str\" existe"
    else
        echo "❌ \"$str\" MANQUANT"
        ((missing++))
    fi
done

echo ""
echo "Total manquant: $missing/${#STRINGS[@]}"
