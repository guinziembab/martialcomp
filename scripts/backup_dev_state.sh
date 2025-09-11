#!/bin/bash
"""
Script de sauvegarde complète de l'état de développement
"""

BACKUP_DIR="backup_dev_20250630_211015"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "🔄 SAUVEGARDE ÉTAT DÉVELOPPEMENT - $TIMESTAMP"
echo "=============================================="

# Créer le répertoire de sauvegarde
mkdir -p "$BACKUP_DIR"

echo "📁 Création répertoire: $BACKUP_DIR"

# 1. Sauvegarde base de données PostgreSQL
echo "🗄️  Sauvegarde base de données..."
pg_dump -h localhost -U postgres -d martialcomp_db > "$BACKUP_DIR/database_dev_$TIMESTAMP.sql"
if [ $? -eq 0 ]; then
    echo "   ✅ Base de données sauvegardée"
else
    echo "   ❌ Erreur sauvegarde base de données"
fi

# 2. Sauvegarde fichiers de configuration
echo "⚙️  Sauvegarde configuration..."
cp config/settings.py "$BACKUP_DIR/settings_dev_$TIMESTAMP.py"
cp config/urls.py "$BACKUP_DIR/urls_dev_$TIMESTAMP.py"
echo "   ✅ Fichiers config sauvegardés"

# 3. Sauvegarde modèles Django
echo "📋 Sauvegarde modèles..."
mkdir -p "$BACKUP_DIR/models"
cp -r competitions/models/ "$BACKUP_DIR/models/"
echo "   ✅ Modèles sauvegardés"

# 4. Sauvegarde vues importantes
echo "👁️  Sauvegarde vues..."
mkdir -p "$BACKUP_DIR/views"
cp -r competitions/views/ "$BACKUP_DIR/views/"
echo "   ✅ Vues sauvegardées"

# 5. Sauvegarde formulaires
echo "📝 Sauvegarde formulaires..."
mkdir -p "$BACKUP_DIR/forms"
cp -r competitions/forms/ "$BACKUP_DIR/forms/"
echo "   ✅ Formulaires sauvegardés"

# 6. Sauvegarde templates modifiés
echo "🎨 Sauvegarde templates..."
mkdir -p "$BACKUP_DIR/templates"
cp competitions/templates/competitions/welcome.html "$BACKUP_DIR/templates/welcome_dev_$TIMESTAMP.html"
echo "   ✅ Templates sauvegardés"

# 7. Sauvegarde signaux
echo "📡 Sauvegarde signaux..."
cp competitions/signals.py "$BACKUP_DIR/signals_dev_$TIMESTAMP.py"
echo "   ✅ Signaux sauvegardés"

# 8. Sauvegarde requirements
echo "📦 Sauvegarde requirements..."
cp requirements.txt "$BACKUP_DIR/requirements_dev_$TIMESTAMP.txt"
echo "   ✅ Requirements sauvegardés"

# 9. Sauvegarde migrations
echo "🔄 Sauvegarde migrations..."
mkdir -p "$BACKUP_DIR/migrations"
cp -r competitions/migrations/ "$BACKUP_DIR/migrations/competitions/"
cp -r grades/migrations/ "$BACKUP_DIR/migrations/grades/" 2>/dev/null || true
cp -r finances/migrations/ "$BACKUP_DIR/migrations/finances/" 2>/dev/null || true
echo "   ✅ Migrations sauvegardées"

# 10. Créer un résumé de l'état
echo "📊 Création résumé état..."
cat > "$BACKUP_DIR/README_BACKUP_$TIMESTAMP.md" << EOF
# Sauvegarde État Développement - $TIMESTAMP

## Contenu de cette sauvegarde

### Base de données
- \`database_dev_$TIMESTAMP.sql\` - Dump complet PostgreSQL

### Configuration
- \`settings_dev_$TIMESTAMP.py\` - Configuration Django
- \`urls_dev_$TIMESTAMP.py\` - URLs principales
- \`requirements_dev_$TIMESTAMP.txt\` - Dépendances Python

### Code applicatif
- \`models/\` - Tous les modèles Django
- \`views/\` - Toutes les vues
- \`forms/\` - Tous les formulaires
- \`signals_dev_$TIMESTAMP.py\` - Signaux Django

### Templates et UI
- \`templates/welcome_dev_$TIMESTAMP.html\` - Template principal

### Migrations
- \`migrations/\` - Toutes les migrations Django

## État au moment de la sauvegarde

### Fonctionnalités implémentées
- ✅ Système d'onboarding club/fédération
- ✅ Création automatique sous-domaines
- ✅ Sélection automatique pays (France)
- ✅ Redirection selon rôles utilisateur
- ✅ Signaux auto création profils

### Problèmes identifiés
- ❌ Système authentification/enregistrement instable
- ❌ Conflits URLs allauth
- ❌ Configuration CSRF problématique

### Corrections récentes
- Fixé URLs d'inscription
- Amélioré protection CSRF
- Corrigé redirection admin → manager

## Pour restaurer cet état
1. Restaurer base de données: \`psql -U postgres -d martialcomp_db < database_dev_$TIMESTAMP.sql\`
2. Copier fichiers config
3. Appliquer migrations si nécessaire
4. Redémarrer serveur Django

Date: $(date)
Commit: $(git rev-parse HEAD 2>/dev/null || echo "Non disponible")
Branch: $(git branch --show-current 2>/dev/null || echo "Non disponible")
EOF

echo "   ✅ Résumé créé"

# 11. Informations git
echo "🔀 Sauvegarde info Git..."
git status > "$BACKUP_DIR/git_status_$TIMESTAMP.txt" 2>/dev/null || echo "Git non disponible" > "$BACKUP_DIR/git_status_$TIMESTAMP.txt"
git log --oneline -10 > "$BACKUP_DIR/git_recent_commits_$TIMESTAMP.txt" 2>/dev/null || echo "Git non disponible" > "$BACKUP_DIR/git_recent_commits_$TIMESTAMP.txt"
echo "   ✅ Info Git sauvegardées"

# 12. Archive compressée
echo "📦 Création archive..."
tar -czf "backup_dev_complete_$TIMESTAMP.tar.gz" "$BACKUP_DIR/"
echo "   ✅ Archive créée: backup_dev_complete_$TIMESTAMP.tar.gz"

echo ""
echo "🎉 SAUVEGARDE TERMINÉE"
echo "=============================================="
echo "📁 Répertoire: $BACKUP_DIR"
echo "📦 Archive: backup_dev_complete_$TIMESTAMP.tar.gz"
echo "📏 Taille archive: $(du -h backup_dev_complete_$TIMESTAMP.tar.gz | cut -f1)"
echo "📊 Nombre fichiers: $(find $BACKUP_DIR -type f | wc -l)"
echo ""
echo "✅ État de développement sauvegardé avec succès!"