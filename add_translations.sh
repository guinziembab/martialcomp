#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# Script d'Ajout de Traductions Manquantes
# ═══════════════════════════════════════════════════════════════
# Usage: ./add_translations.sh <langue>
# Ex: ./add_translations.sh en
# ═══════════════════════════════════════════════════════════════

if [ -z "$1" ]; then
    echo "❌ Erreur: Langue non spécifiée"
    echo "Usage: $0 <langue>"
    echo "Ex: $0 en"
    exit 1
fi

LANG=$1
PO_FILE="locale/$LANG/LC_MESSAGES/django.po"
MO_FILE="locale/$LANG/LC_MESSAGES/django.mo"

if [ ! -f "$PO_FILE" ]; then
    echo "❌ Erreur: Fichier $PO_FILE introuvable"
    exit 1
fi

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  Ajout de Traductions - $LANG                                  "
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Fonction pour ajouter une traduction
add_translation() {
    local msgid=$1
    local msgstr=$2
    
    # Vérifier si la traduction existe déjà
    if grep -q "^msgid \"$msgid\"" "$PO_FILE"; then
        echo "⚠️  \"$msgid\" existe déjà"
        return 1
    fi
    
    # Ajouter la traduction
    cat >> "$PO_FILE" << EOF

msgid "$msgid"
msgstr "$msgstr"
EOF
    
    echo "✅ \"$msgid\" → \"$msgstr\""
    return 0
}

# Compteur de traductions ajoutées
COUNT=0

# Exemple d'utilisation:
# add_translation "Texte français" "English text" && ((COUNT++))

# Compiler le fichier
echo ""
echo "Compilation du fichier .mo..."
if msgfmt -o "$MO_FILE" "$PO_FILE" 2>&1; then
    echo "✅ Compilation réussie"
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "  $COUNT traduction(s) ajoutée(s)"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    echo "Redémarrez le serveur Django pour voir les changements:"
    echo "  python manage.py runserver 127.0.0.1:8080"
else
    echo "❌ Erreur lors de la compilation"
    echo "Vérifiez le fichier $PO_FILE pour les doublons ou erreurs"
    exit 1
fi
