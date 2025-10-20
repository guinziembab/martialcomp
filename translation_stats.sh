#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# Statistiques des Traductions
# ═══════════════════════════════════════════════════════════════

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  STATISTIQUES DES TRADUCTIONS                                 ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Langues
LANGUAGES=(fr en es it de pt ru vi no ja zh hi ar sw am zu yo ko)
LANG_NAMES=(
    "Français"
    "English"
    "Español"
    "Italiano"
    "Deutsch"
    "Português"
    "Русский"
    "Tiếng Việt"
    "Norsk"
    "日本語"
    "中文"
    "हिन्दी"
    "العربية"
    "Kiswahili"
    "አማርኛ"
    "isiZulu"
    "Yorùbá"
    "한국어"
)

echo "┌─────────────────────┬──────────┬──────────┬──────────┬──────┬──────────┐"
echo "│ Langue              │ Total    │ Traduits │ Manquant │   %  │ Statut   │"
echo "├─────────────────────┼──────────┼──────────┼──────────┼──────┼──────────┤"

for i in "${!LANGUAGES[@]}"; do
    lang="${LANGUAGES[$i]}"
    name="${LANG_NAMES[$i]}"
    po_file="locale/$lang/LC_MESSAGES/django.po"
    
    if [ -f "$po_file" ]; then
        total=$(grep -c "^msgid " "$po_file" 2>/dev/null || echo 0)
        trans=$(grep "^msgstr " "$po_file" | grep -v '^msgstr ""$' | wc -l)
        
        if [ $total -gt 0 ]; then
            missing=$((total - trans))
            pct=$((trans * 100 / total))
            
            # Déterminer le statut
            if [ $pct -ge 95 ]; then
                status="✅ OK"
            elif [ $pct -ge 80 ]; then
                status="⚠️  Bon"
            else
                status="❌ À faire"
            fi
            
            printf "│ %-19s │ %8d │ %8d │ %8d │ %3d%% │ %-8s │\n" \
                "$name" "$total" "$trans" "$missing" "$pct" "$status"
        else
            printf "│ %-19s │ %8s │ %8s │ %8s │ %4s │ %-8s │\n" \
                "$name" "?" "?" "?" "?" "❌ Vide"
        fi
    else
        printf "│ %-19s │ %8s │ %8s │ %8s │ %4s │ %-8s │\n" \
            "$name" "-" "-" "-" "-" "❌ Absent"
    fi
done

echo "└─────────────────────┴──────────┴──────────┴──────────┴──────┴──────────┘"
echo ""

# Calculer les totaux
total_strings=0
total_translated=0
total_missing=0

for lang in "${LANGUAGES[@]}"; do
    po_file="locale/$lang/LC_MESSAGES/django.po"
    if [ -f "$po_file" ]; then
        total=$(grep -c "^msgid " "$po_file" 2>/dev/null || echo 0)
        trans=$(grep "^msgstr " "$po_file" | grep -v '^msgstr ""$' | wc -l)
        total_strings=$((total_strings + total))
        total_translated=$((total_translated + trans))
    fi
done

total_missing=$((total_strings - total_translated))

if [ $total_strings -gt 0 ]; then
    global_pct=$((total_translated * 100 / total_strings))
    echo "STATISTIQUES GLOBALES:"
    echo "  Total de chaînes: $total_strings"
    echo "  Traduites: $total_translated ($global_pct%)"
    echo "  Manquantes: $total_missing"
fi

echo ""
