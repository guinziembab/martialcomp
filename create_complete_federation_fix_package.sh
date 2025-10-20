#!/bin/bash
# Script pour créer le package complet de correction fédération

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PACKAGE_NAME="federation_fixes_complete_${TIMESTAMP}"
PACKAGE_DIR="/tmp/${PACKAGE_NAME}"

echo "📦 Création du package complet de correction fédération..."
echo "Package : ${PACKAGE_NAME}"

# Créer la structure
mkdir -p ${PACKAGE_DIR}/apps/competitions/views/{dashboard,onboarding}
mkdir -p ${PACKAGE_DIR}/docs

# Copier tous les fichiers corrigés
echo "📄 Copie des fichiers corrigés..."

# Dashboard federations
cp apps/competitions/views/dashboard/federations.py ${PACKAGE_DIR}/apps/competitions/views/dashboard/
echo "✓ Dashboard federations.py"

# Onboarding federations
cp apps/competitions/views/onboarding/federations.py ${PACKAGE_DIR}/apps/competitions/views/onboarding/
echo "✓ Onboarding federations.py"

# Onboarding __init__
cp apps/competitions/views/onboarding/__init__.py ${PACKAGE_DIR}/apps/competitions/views/onboarding/
echo "✓ Onboarding __init__.py"

# Documentation
cp RAPPORT_CORRECTION_FEDERATION_DASHBOARD.md ${PACKAGE_DIR}/docs/
cp AUDIT_ONBOARDING_FEDERATION.md ${PACKAGE_DIR}/docs/

# Créer le script de déploiement complet
cat > ${PACKAGE_DIR}/apply_all_fixes.sh << 'EOF'
#!/bin/bash
# Script de déploiement complet des corrections fédération

echo "🔧 Application complète des corrections fédération..."
echo "📅 Date : $(date)"

# Configuration
WEBAPP_DIR="/home/martialcomp/public_html"
BACKUP_DIR="/home/martialcomp/backups/federation_$(date +%Y%m%d_%H%M%S)"

# Vérifier que le répertoire webapp existe
if [ ! -d "$WEBAPP_DIR" ]; then
    echo "❌ Erreur : Le répertoire $WEBAPP_DIR n'existe pas!"
    exit 1
fi

# Créer le répertoire de sauvegarde
echo "💾 Création des sauvegardes..."
mkdir -p $BACKUP_DIR/{dashboard,onboarding}

# Sauvegarder tous les fichiers
files_to_backup=(
    "apps/competitions/views/dashboard/federations.py"
    "apps/competitions/views/onboarding/federations.py"
    "apps/competitions/views/onboarding/__init__.py"
)

for file in "${files_to_backup[@]}"; do
    if [ -f "$WEBAPP_DIR/$file" ]; then
        cp "$WEBAPP_DIR/$file" "$BACKUP_DIR/$file"
        echo "✓ Sauvegardé : $file"
    fi
done

# Copier les nouveaux fichiers
echo ""
echo "📤 Installation des corrections..."
cp -rf apps/* $WEBAPP_DIR/apps/
echo "✓ Fichiers copiés avec succès"

# Activer l'environnement virtuel
echo ""
echo "🐍 Vérification de l'environnement Python..."
cd $WEBAPP_DIR
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv_regen/bin/activate" ]; then
    source venv_regen/bin/activate
else
    echo "⚠️  Environnement virtuel non trouvé"
fi

# Vérifier la syntaxe Python
echo ""
echo "🔍 Vérification de la syntaxe..."
error_found=false

for file in "${files_to_backup[@]}"; do
    if [ -f "$WEBAPP_DIR/$file" ]; then
        python -m py_compile "$WEBAPP_DIR/$file" 2>/dev/null || {
            echo "❌ Erreur de syntaxe dans $file"
            error_found=true
        }
    fi
done

if [ "$error_found" = true ]; then
    echo ""
    echo "❌ Erreurs détectées! Restauration depuis backup..."
    for file in "${files_to_backup[@]}"; do
        if [ -f "$BACKUP_DIR/$file" ]; then
            cp "$BACKUP_DIR/$file" "$WEBAPP_DIR/$file"
        fi
    done
    exit 1
fi

echo "✓ Syntaxe Python valide"

# Collecter les fichiers statiques si nécessaire
echo ""
echo "🎨 Mise à jour des assets..."
python manage.py collectstatic --noinput --clear 2>/dev/null || {
    echo "⚠️  Collectstatic non exécuté (non critique)"
}

# Redémarrer l'application
echo ""
echo "🔄 Redémarrage de l'application..."
touch $WEBAPP_DIR/passenger_wsgi.py
echo "✓ Application redémarrée"

echo ""
echo "✅ Toutes les corrections ont été appliquées avec succès!"
echo ""
echo "📋 Résumé des corrections :"
echo "1. ✓ Onboarding fédération : fonction create_federation_user ajoutée"
echo "2. ✓ Dashboard fédération : paramètre federation_id rendu optionnel"
echo "3. ✓ Redirections corrigées vers les bonnes URLs"
echo "4. ✓ Permissions et contexte améliorés"
echo ""
echo "🧪 Tests à effectuer :"
echo "1. Créer un nouveau compte admin fédération"
echo "2. Passer par l'onboarding complet"
echo "3. Vérifier l'accès au dashboard sans erreur"
echo "4. Tester avec et sans federation_id dans l'URL"
echo ""
echo "🔙 Sauvegarde complète disponible dans : $BACKUP_DIR"
echo ""
echo "📝 Pour restaurer en cas de problème :"
echo "   cp -r $BACKUP_DIR/apps/* $WEBAPP_DIR/apps/"
echo "   touch $WEBAPP_DIR/passenger_wsgi.py"
EOF

chmod +x ${PACKAGE_DIR}/apply_all_fixes.sh

# Créer un script de test
cat > ${PACKAGE_DIR}/test_fixes.sh << 'EOF'
#!/bin/bash
# Script de test des corrections

echo "🧪 Test des corrections fédération..."
echo ""

# Test 1 : Syntaxe Python
echo "1️⃣ Test de syntaxe Python..."
cd /home/martialcomp/public_html
python -c "from apps.competitions.views.onboarding.federations import create_federation_user, handle_federation_creation" && {
    echo "✅ Import onboarding OK"
} || {
    echo "❌ Erreur d'import onboarding"
}

python -c "from apps.competitions.views.dashboard.federations import federation_dashboard" && {
    echo "✅ Import dashboard OK"
} || {
    echo "❌ Erreur d'import dashboard"
}

# Test 2 : URLs
echo ""
echo "2️⃣ Test des URLs..."
python manage.py show_urls 2>/dev/null | grep -E "(onboarding.*federation|dashboard.*federation)" | head -10

echo ""
echo "✅ Tests terminés"
EOF

chmod +x ${PACKAGE_DIR}/test_fixes.sh

# Créer un README détaillé
cat > ${PACKAGE_DIR}/README.md << 'EOF'
# Corrections Complètes - Système Fédération

## 🎯 Objectif
Corriger les erreurs d'import et de paramètres dans le système de gestion des fédérations.

## 🐛 Problèmes corrigés

### 1. ImportError: create_federation_user
- **Erreur** : `cannot import name 'create_federation_user'`
- **Solution** : Ajout de la fonction comme alias vers `handle_federation_creation`

### 2. TypeError: federation_dashboard
- **Erreur** : `missing 1 required positional argument: 'federation_id'`
- **Solution** : Paramètre rendu optionnel avec gestion intelligente

### 3. URLs incorrectes
- **Erreur** : Redirections vers des URLs inexistantes
- **Solution** : Correction vers `dashboard:federations`

## 📦 Contenu du package

```
federation_fixes_complete/
├── apps/competitions/views/
│   ├── dashboard/
│   │   └── federations.py          # Dashboard avec federation_id optionnel
│   └── onboarding/
│       ├── federations.py          # Ajout create_federation_user
│       └── __init__.py             # Export corrigé
├── docs/
│   ├── AUDIT_ONBOARDING_FEDERATION.md
│   └── RAPPORT_CORRECTION_FEDERATION_DASHBOARD.md
├── apply_all_fixes.sh              # Script d'installation
├── test_fixes.sh                   # Script de test
└── README.md                       # Ce fichier
```

## 🚀 Installation

1. **Application automatique**
   ```bash
   ./apply_all_fixes.sh
   ```

2. **Test des corrections**
   ```bash
   ./test_fixes.sh
   ```

## 🧪 Validation

### Onboarding
1. Créer un compte avec email/mot de passe
2. Sélectionner "Administrateur de fédération"
3. Remplir le formulaire de création
4. Vérifier la redirection vers le dashboard

### Dashboard
1. Accéder à `/competitions/dashboard/federations/`
2. Vérifier l'absence d'erreur TypeError
3. Confirmer l'affichage des statistiques
4. Tester avec un ID spécifique : `/competitions/dashboard/federations/1/`

## ⚠️ Points d'attention

1. **Permissions** : Seuls les admins fédération peuvent accéder au dashboard
2. **Multi-fédération** : Un utilisateur ne peut gérer qu'une fédération actuellement
3. **Cache** : Penser à vider le cache Django après déploiement

## 🔄 Rollback

En cas de problème :
```bash
cp -r /home/martialcomp/backups/federation_*/apps/* /home/martialcomp/public_html/apps/
touch /home/martialcomp/public_html/passenger_wsgi.py
```

## 📞 Support

Conserver le numéro du backup pour référence future.
EOF

# Créer l'archive finale
cd /tmp
tar -czf ${PACKAGE_NAME}.tar.gz ${PACKAGE_NAME}

echo ""
echo "✅ Package complet créé avec succès!"
echo "📦 Fichier : /tmp/${PACKAGE_NAME}.tar.gz"
echo "📏 Taille : $(du -h /tmp/${PACKAGE_NAME}.tar.gz | cut -f1)"
echo ""
echo "📋 Contenu :"
tar -tzf ${PACKAGE_NAME}.tar.gz | grep -E "\.(py|sh|md)$" | sort
echo ""
echo "🚀 Pour déployer en production :"
echo "1. scp /tmp/${PACKAGE_NAME}.tar.gz user@production:/home/martialcomp/"
echo "2. ssh user@production"
echo "3. cd /home/martialcomp && tar -xzf ${PACKAGE_NAME}.tar.gz"
echo "4. cd ${PACKAGE_NAME} && ./apply_all_fixes.sh"
echo ""
echo "✅ Toutes les corrections fédération sont prêtes!"