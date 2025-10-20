#!/bin/bash
# ================================================
# AUDIT COMPLET DES TRADUCTIONS - MartialComp DEV
# ================================================

# Configuration
PROJECT_ROOT="/mnt/c/martial_hub_django/martialcomp"
LOCALE_DIR="$PROJECT_ROOT/locale"
REPORT_DIR="$PROJECT_ROOT/translation_reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Langues supportées
LANGUAGES=(
    "fr:Français"
    "en:English"
    "es:Español"
    "it:Italiano"
    "de:Deutsch"
    "pt:Português"
    "ru:Русский"
    "vi:Tiếng Việt"
    "no:Norsk"
    "ja:日本語"
    "zh:中文"
    "hi:हिन्दी"
    "ar:العربية"
    "sw:Kiswahili"
    "am:አማርኛ"
    "zu:isiZulu"
    "yo:Yorùbá"
    "ko:한국어"
)

# Créer le répertoire de rapports
mkdir -p "$REPORT_DIR"

echo "╔════════════════════════════════════════════════╗"
echo "║  AUDIT COMPLET DES TRADUCTIONS - MartialComp  ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# Fonction pour analyser une langue
check_language_stats() {
    local lang_code=$1
    local lang_name=$2
    local po_file="$LOCALE_DIR/$lang_code/LC_MESSAGES/django.po"
    
    if [ ! -f "$po_file" ]; then
        echo "✗ MANQUANT: $lang_code ($lang_name)"
        echo "MISSING|$lang_code|$lang_name|0|0|0|0%" >> "$REPORT_DIR/stats_$TIMESTAMP.csv"
        return
    fi
    
    # Extraire les statistiques
    total=$(grep -c "^msgid " "$po_file" 2>/dev/null || echo 0)
    translated=$(grep -c "^msgstr \"[^\"]" "$po_file" 2>/dev/null || echo 0)
    fuzzy=$(grep -c "^#, fuzzy" "$po_file" 2>/dev/null || echo 0)
    untranslated=$((total - translated - fuzzy))
    
    # Calculer le pourcentage
    if [ $total -gt 0 ]; then
        percentage=$((translated * 100 / total))
    else
        percentage=0
    fi
    
    # Afficher avec statut
    if [ $percentage -ge 90 ]; then
        status="✓ Excellent"
    elif [ $percentage -ge 70 ]; then
        status="⚠ Bon"
    else
        status="✗ À compléter"
    fi
    
    echo "$status $lang_code ($lang_name): $translated/$total traduits (${percentage}%)"
    echo "OK|$lang_code|$lang_name|$total|$translated|$untranslated|$percentage%" >> "$REPORT_DIR/stats_$TIMESTAMP.csv"
}

# En-tête CSV
echo "Status|Code|Langue|Total|Traduits|Non traduits|Pourcentage" > "$REPORT_DIR/stats_$TIMESTAMP.csv"

# Analyser chaque langue
echo "═══ Analyse des fichiers de traduction ═══"
echo ""
for lang_pair in "${LANGUAGES[@]}"; do
    IFS=':' read -r code name <<< "$lang_pair"
    check_language_stats "$code" "$name"
done

# Vérifier les fichiers .mo compilés
echo ""
echo "═══ Vérification des fichiers compilés (.mo) ═══"
echo ""

for lang_pair in "${LANGUAGES[@]}"; do
    IFS=':' read -r code name <<< "$lang_pair"
    mo_file="$LOCALE_DIR/$code/LC_MESSAGES/django.mo"
    po_file="$LOCALE_DIR/$code/LC_MESSAGES/django.po"
    
    if [ ! -f "$mo_file" ]; then
        echo "✗ MANQUANT: $code ($name) - Fichier .mo non compilé"
    elif [ "$po_file" -nt "$mo_file" ]; then
        echo "⚠ OBSOLÈTE: $code ($name) - .mo plus ancien que .po"
    else
        echo "✓ OK: $code ($name)"
    fi
done

echo ""
echo "═══════════════════════════════════════════════"
echo "✓ AUDIT TERMINÉ"
echo "═══════════════════════════════════════════════"
echo ""
echo "Rapports générés dans: $REPORT_DIR/"
echo ""
echo "Pour voir les statistiques:"
echo "  cat $REPORT_DIR/stats_$TIMESTAMP.csv"
