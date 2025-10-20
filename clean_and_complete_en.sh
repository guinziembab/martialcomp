#!/bin/bash
# Nettoyer les doublons et vérifier le fichier EN

PO_FILE="locale/en/LC_MESSAGES/django.po"
PO_BACKUP="locale/en/LC_MESSAGES/django.po.backup_$(date +%Y%m%d_%H%M%S)"

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  NETTOYAGE ET VÉRIFICATION - TRADUCTIONS ANGLAISES           ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# 1. Backup
echo "1. Création du backup..."
cp "$PO_FILE" "$PO_BACKUP"
echo "   ✅ Backup: $PO_BACKUP"
echo ""

# 2. Compter les doublons
echo "2. Détection des doublons..."
doublons=$(grep "^msgid " "$PO_FILE" | sort | uniq -d | wc -l)
echo "   ⚠️  Doublons trouvés: $doublons"
echo ""

# 3. Vérifier la compilation
echo "3. Test de compilation..."
if msgfmt --check "$PO_FILE" 2>/dev/null; then
    echo "   ✅ Fichier .po valide"
else
    echo "   ❌ Fichier .po contient des erreurs"
fi
echo ""

# 4. Statistiques
echo "4. Statistiques:"
total=$(grep -c "^msgid " "$PO_FILE")
trans=$(grep "^msgstr " "$PO_FILE" | grep -v '^msgstr ""$' | wc -l)
pct=$((trans * 100 / total))
echo "   Total msgid: $total"
echo "   Traductions: $trans ($pct%)"
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "Pour compiler (si pas d'erreurs):"
echo "  msgfmt -o locale/en/LC_MESSAGES/django.mo \\"
echo "         locale/en/LC_MESSAGES/django.po"
echo ""
echo "Pour restaurer le backup:"
echo "  cp $PO_BACKUP $PO_FILE"
echo "═══════════════════════════════════════════════════════════════"
