#!/bin/bash
# Script pour mettre à jour tous les fichiers PO de toutes les langues
# Après nettoyage des fichiers problématiques

cd /mnt/c/martial_hub_django/martialcomp

# Liste des langues disponibles
LANGUAGES=("am" "ar" "de" "en" "es" "fr" "hi" "it" "ja" "ko" "no" "pt" "ru" "sw" "vi" "yo" "zh" "zh-hans" "zu")

echo "🔄 Mise à jour des fichiers PO pour toutes les langues..."
echo "============================================================"
echo ""

SUCCESS_COUNT=0
ERROR_COUNT=0
ERROR_LANGS=()

for lang in "${LANGUAGES[@]}"; do
    echo "📝 Traitement de la langue: $lang"
    echo "-----------------------------------"
    
    # Vérifier si le fichier PO existe
    if [ -f "locale/$lang/LC_MESSAGES/django.po" ]; then
        echo "   ✅ Fichier PO trouvé pour $lang"
        
        # Mettre à jour le fichier PO
        python3 manage.py makemessages -l "$lang" --no-obsolete --no-wrap > /tmp/makemessages_${lang}.log 2>&1
        RESULT=$?
        
        if [ $RESULT -eq 0 ]; then
            echo "   ✅ Fichier PO mis à jour pour $lang"
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        else
            echo "   ⚠️  Erreur lors de la mise à jour pour $lang"
            echo "   📋 Dernières lignes du log:"
            tail -10 /tmp/makemessages_${lang}.log | sed 's/^/      /'
            ERROR_COUNT=$((ERROR_COUNT + 1))
            ERROR_LANGS+=("$lang")
        fi
    else
        echo "   ⚠️  Fichier PO non trouvé pour $lang (création...)"
        python3 manage.py makemessages -l "$lang" --no-obsolete --no-wrap > /tmp/makemessages_${lang}.log 2>&1
        RESULT=$?
        
        if [ $RESULT -eq 0 ]; then
            echo "   ✅ Fichier PO créé pour $lang"
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        else
            echo "   ❌ Erreur lors de la création pour $lang"
            tail -10 /tmp/makemessages_${lang}.log | sed 's/^/      /'
            ERROR_COUNT=$((ERROR_COUNT + 1))
            ERROR_LANGS+=("$lang")
        fi
    fi
    echo ""
done

echo "============================================================"
echo "📊 RÉSUMÉ"
echo "============================================================"
echo "✅ Succès: $SUCCESS_COUNT langue(s)"
echo "❌ Erreurs: $ERROR_COUNT langue(s)"

if [ $ERROR_COUNT -gt 0 ]; then
    echo ""
    echo "⚠️  Langues en erreur: ${ERROR_LANGS[*]}"
    echo ""
    echo "💡 Vérifiez les logs dans /tmp/makemessages_*.log pour plus de détails"
fi

echo ""
echo "✅ Mise à jour terminée"
echo ""
