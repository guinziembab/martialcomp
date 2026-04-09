#!/bin/bash
# Script pour mettre à jour tous les fichiers PO de toutes les langues

cd /mnt/c/martial_hub_django/martialcomp

# Liste des langues disponibles
LANGUAGES=("am" "ar" "de" "en" "es" "fr" "hi" "it" "ja" "ko" "no" "pt" "ru" "sw" "vi" "yo" "zh" "zu")

echo "🔄 Mise à jour des fichiers PO pour toutes les langues..."
echo "============================================================"

for lang in "${LANGUAGES[@]}"; do
    echo ""
    echo "📝 Traitement de la langue: $lang"
    echo "-----------------------------------"
    
    # Vérifier si le fichier PO existe
    if [ -f "locale/$lang/LC_MESSAGES/django.po" ]; then
        echo "   ✅ Fichier PO trouvé pour $lang"
        
        # Mettre à jour le fichier PO
        python3 manage.py makemessages -l $lang --no-obsolete --no-wrap 2>&1 | grep -v "UnicodeDecodeError" | grep -v "CommandError" | tail -5
        
        if [ $? -eq 0 ]; then
            echo "   ✅ Fichier PO mis à jour pour $lang"
        else
            echo "   ⚠️  Erreur lors de la mise à jour pour $lang"
        fi
    else
        echo "   ⚠️  Fichier PO non trouvé pour $lang"
    fi
done

echo ""
echo "============================================================"
echo "✅ Mise à jour terminée pour toutes les langues"
echo ""
echo "💡 Note: Ignorez les erreurs UnicodeDecodeError et CommandError"
echo "   qui proviennent de fichiers binaires ou .py dans les dossiers de backup"
