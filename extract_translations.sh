#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# Script d'Extraction et Mise à Jour des Traductions
# ═══════════════════════════════════════════════════════════════

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  EXTRACTION ET MISE À JOUR DES TRADUCTIONS                    ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Langues à mettre à jour
LANGUAGES=(fr en es it de pt ru vi no ja zh hi ar sw am zu yo ko)

# Créer un backup avant modification
BACKUP_DIR="locale_backup_$(date +%Y%m%d_%H%M%S)"
echo "📦 Création du backup: $BACKUP_DIR"
mkdir -p backups
tar -czf "backups/$BACKUP_DIR.tar.gz" locale/ 2>/dev/null
echo "✅ Backup créé"
echo ""

# Fonction pour extraire les messages pour une langue
extract_for_language() {
    local lang=$1
    echo "📝 Extraction pour: $lang"
    
    # Utiliser xgettext directement pour éviter les problèmes Django
    find apps/competitions/templates -name "*.html" -type f > /tmp/template_files.txt
    
    # Créer le fichier .pot
    xgettext \
        --language=Python \
        --keyword=trans \
        --keyword=trans_lazy \
        --keyword=blocktrans \
        --from-code=UTF-8 \
        --output=locale/$lang/LC_MESSAGES/django_new.pot \
        --files-from=/tmp/template_files.txt \
        2>/dev/null || echo "⚠️  xgettext non disponible"
    
    # Utiliser msggrep pour extraire les chaînes Django
    if [ -f "locale/$lang/LC_MESSAGES/django.po" ]; then
        echo "   ✅ Fichier .po existant trouvé"
        # Compter les entrées
        total=$(grep -c "^msgid " "locale/$lang/LC_MESSAGES/django.po" 2>/dev/null || echo 0)
        trans=$(grep "^msgstr " "locale/$lang/LC_MESSAGES/django.po" | grep -v '^msgstr ""$' | wc -l)
        echo "   📊 $trans/$total traduits"
    else
        echo "   ❌ Fichier .po manquant"
    fi
}

# Extraire pour toutes les langues
echo "═══════════════════════════════════════════════════════════════"
echo "EXTRACTION DES CHAÎNES"
echo "═══════════════════════════════════════════════════════════════"
echo ""

for lang in "${LANGUAGES[@]}"; do
    extract_for_language "$lang"
done

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "COMPILATION DES FICHIERS .mo"
echo "═══════════════════════════════════════════════════════════════"
echo ""

compiled=0
errors=0

for lang in "${LANGUAGES[@]}"; do
    if [ -f "locale/$lang/LC_MESSAGES/django.po" ]; then
        echo "🔨 Compilation: $lang"
        if msgfmt -o "locale/$lang/LC_MESSAGES/django.mo" "locale/$lang/LC_MESSAGES/django.po" 2>/dev/null; then
            echo "   ✅ Compilé"
            ((compiled++))
        else
            echo "   ❌ Erreur compilation"
            ((errors++))
        fi
    fi
done

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "RÉSUMÉ"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "✅ Langues compilées: $compiled"
echo "❌ Erreurs: $errors"
echo "📦 Backup: backups/$BACKUP_DIR.tar.gz"
echo ""
echo "Pour voir les statistiques détaillées:"
echo "  bash translation_stats.sh"
echo ""
