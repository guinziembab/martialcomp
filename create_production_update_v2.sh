#!/bin/bash
# Script de création du package de mise à jour pour la production - Version 2
# Inclut l'onglet Résultats et les corrections d'URLs

# Variables
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PACKAGE_NAME="update_resultats_v2_${TIMESTAMP}"
PACKAGE_DIR="/tmp/${PACKAGE_NAME}"

echo "🚀 Création du package de mise à jour (v2)..."
echo "📦 Package : ${PACKAGE_NAME}"

# Créer la structure complète
mkdir -p ${PACKAGE_DIR}/apps/competitions/views/{club,}
mkdir -p ${PACKAGE_DIR}/apps/competitions/templates/competitions/club
mkdir -p ${PACKAGE_DIR}/docs

# 1. Copier les fichiers modifiés
echo "📄 Copie des fichiers modifiés..."

# Template principal avec l'onglet Résultats
if [ -f "apps/competitions/templates/competitions/club/competition_management_detail.html" ]; then
    cp apps/competitions/templates/competitions/club/competition_management_detail.html \
       ${PACKAGE_DIR}/apps/competitions/templates/competitions/club/
    echo "✓ Template competition_management_detail.html copié"
fi

# Vue event_organizer
if [ -f "apps/competitions/views/club/event_organizer.py" ]; then
    cp apps/competitions/views/club/event_organizer.py \
       ${PACKAGE_DIR}/apps/competitions/views/club/
    echo "✓ Vue event_organizer.py copiée"
fi

# Vue competition_management_pro (si elle existe)
if [ -f "apps/competitions/views/competition_management_pro.py" ]; then
    cp apps/competitions/views/competition_management_pro.py \
       ${PACKAGE_DIR}/apps/competitions/views/
    echo "✓ Vue competition_management_pro.py copiée"
fi

# Documentation
for doc in RAPPORT_INTEGRATION_RESULTATS.md RAPPORT_CORRECTION_URLS_RESULTATS.md GUIDE_MISE_A_JOUR_PRODUCTION.md; do
    if [ -f "$doc" ]; then
        cp "$doc" ${PACKAGE_DIR}/docs/
        echo "✓ Documentation $doc copiée"
    fi
done

# 2. Créer le script de déploiement amélioré
cat > ${PACKAGE_DIR}/deploy_on_server.sh << 'DEPLOY_SCRIPT'
#!/bin/bash
# Script de déploiement sur le serveur de production

set -e  # Arrêter en cas d'erreur

echo "🚀 Déploiement de l'onglet Résultats - Version 2..."
echo "📅 Date : $(date)"

# Configuration
WEBAPP_DIR="/home/martialcomp/public_html"
BACKUP_DIR="/home/martialcomp/backups/$(date +%Y%m%d_%H%M%S)"

# Vérifier que le répertoire webapp existe
if [ ! -d "$WEBAPP_DIR" ]; then
    echo "❌ Erreur : Le répertoire $WEBAPP_DIR n'existe pas!"
    exit 1
fi

# Créer le répertoire de sauvegarde
echo "💾 Création de la sauvegarde..."
mkdir -p $BACKUP_DIR/{templates,views}

# Sauvegarder les fichiers existants
if [ -f "$WEBAPP_DIR/apps/competitions/templates/competitions/club/competition_management_detail.html" ]; then
    cp "$WEBAPP_DIR/apps/competitions/templates/competitions/club/competition_management_detail.html" \
       "$BACKUP_DIR/templates/competition_management_detail.html.bak"
    echo "✓ Template sauvegardé"
fi

if [ -f "$WEBAPP_DIR/apps/competitions/views/club/event_organizer.py" ]; then
    cp "$WEBAPP_DIR/apps/competitions/views/club/event_organizer.py" \
       "$BACKUP_DIR/views/event_organizer.py.bak"
    echo "✓ Vue event_organizer sauvegardée"
fi

if [ -f "$WEBAPP_DIR/apps/competitions/views/competition_management_pro.py" ]; then
    cp "$WEBAPP_DIR/apps/competitions/views/competition_management_pro.py" \
       "$BACKUP_DIR/views/competition_management_pro.py.bak"
    echo "✓ Vue competition_management_pro sauvegardée"
fi

# Copier les nouveaux fichiers
echo "📤 Installation des nouveaux fichiers..."
cp -r apps/* $WEBAPP_DIR/apps/
echo "✓ Fichiers copiés avec succès"

# Activer l'environnement virtuel
echo "🐍 Activation de l'environnement virtuel..."
cd $WEBAPP_DIR
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "../venv/bin/activate" ]; then
    source ../venv/bin/activate
elif [ -f "venv_regen/bin/activate" ]; then
    source venv_regen/bin/activate
else
    echo "⚠️  Environnement virtuel non trouvé, continuons..."
fi

# Vérifier la syntaxe Python des fichiers
echo "🔍 Vérification de la syntaxe Python..."
python -m py_compile apps/competitions/views/club/event_organizer.py || {
    echo "❌ Erreur de syntaxe dans event_organizer.py"
    exit 1
}
echo "✓ Syntaxe Python valide"

# Collecter les fichiers statiques
echo "🎨 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput --clear || {
    echo "⚠️  Erreur lors de collectstatic (non critique)"
}

# Compiler les messages si nécessaire
if [ -d "locale" ]; then
    echo "🌐 Compilation des messages..."
    python manage.py compilemessages || {
        echo "⚠️  Erreur lors de la compilation des messages (non critique)"
    }
fi

# Redémarrer l'application
echo "🔄 Redémarrage de l'application..."
if [ -f "$WEBAPP_DIR/passenger_wsgi.py" ]; then
    touch $WEBAPP_DIR/passenger_wsgi.py
    echo "✓ Application redémarrée via Passenger"
elif command -v systemctl &> /dev/null; then
    sudo systemctl reload apache2 || sudo systemctl reload nginx || true
    echo "✓ Serveur web redémarré"
else
    echo "⚠️  Redémarrage manuel peut être nécessaire"
fi

echo ""
echo "✅ Déploiement terminé avec succès!"
echo ""
echo "📝 Vérifications à faire :"
echo "1. Accéder à : https://[votre-domaine]/fr/competitions/club/competitions/[id]/manage/"
echo "2. Vérifier que l'onglet 'Résultats' (🏆) apparaît après 'Publier & Partager'"
echo "3. Cliquer sur l'onglet et vérifier :"
echo "   - Section 'Interfaces de notation' avec 2 cartes"
echo "   - Section 'Résultats par catégorie'"
echo "   - Graphique de l'état de notation (si Chart.js chargé)"
echo "   - Tableau de suivi temps réel"
echo ""
echo "🔙 En cas de problème :"
echo "   Restaurer depuis : $BACKUP_DIR"
echo "   cp -r $BACKUP_DIR/* $WEBAPP_DIR/apps/competitions/"
echo "   touch $WEBAPP_DIR/passenger_wsgi.py"
DEPLOY_SCRIPT

chmod +x ${PACKAGE_DIR}/deploy_on_server.sh

# 3. Créer un script de test
cat > ${PACKAGE_DIR}/test_deployment.sh << 'TEST_SCRIPT'
#!/bin/bash
# Script de test post-déploiement

echo "🧪 Tests post-déploiement..."

# Test 1: Vérifier que les fichiers existent
echo "📁 Vérification des fichiers..."
files_to_check=(
    "apps/competitions/templates/competitions/club/competition_management_detail.html"
    "apps/competitions/views/club/event_organizer.py"
)

for file in "${files_to_check[@]}"; do
    if [ -f "/home/martialcomp/public_html/$file" ]; then
        echo "✓ $file existe"
    else
        echo "❌ $file manquant!"
    fi
done

# Test 2: Vérifier la syntaxe Python
echo "🐍 Vérification syntaxe Python..."
cd /home/martialcomp/public_html
python -m py_compile apps/competitions/views/club/event_organizer.py && echo "✓ Syntaxe OK"

# Test 3: Tester une URL
echo "🌐 Test d'accès HTTP..."
curl -s -o /dev/null -w "%{http_code}" https://localhost/fr/competitions/club/competitions/1/manage/ || echo "⚠️  Test HTTP échoué"

echo "✅ Tests terminés"
TEST_SCRIPT

chmod +x ${PACKAGE_DIR}/test_deployment.sh

# 4. Créer un README détaillé
cat > ${PACKAGE_DIR}/README.md << 'README'
# Mise à jour Production : Onglet Résultats

## 🎯 Objectif
Ajouter un nouvel onglet "Résultats" dans l'interface de gestion des compétitions avec intégration du système de notation technique.

## 📦 Contenu du package

### Fichiers modifiés
1. **competition_management_detail.html** - Template principal avec :
   - Nouvel onglet "Résultats" (icône trophée)
   - Sections : Interfaces de notation, Résultats par catégorie, État de notation, Actions
   - Intégration Chart.js pour graphiques
   - Tableau temps réel avec auto-refresh

2. **event_organizer.py** - Vue backend mise à jour :
   - Fourniture des données clubs pour filtres
   - Support du nouveau template

3. **competition_management_pro.py** - APIs pour drag & drop (optionnel)

## 🚀 Installation

### Méthode automatique (recommandée)
```bash
# Sur le serveur de production
cd /home/martialcomp
tar -xzf update_resultats_v2_*.tar.gz
cd update_resultats_v2_*
./deploy_on_server.sh
```

### Méthode manuelle
```bash
# 1. Sauvegarder
cp -r /home/martialcomp/public_html/apps/competitions /backup/

# 2. Copier les fichiers
cp -r apps/* /home/martialcomp/public_html/apps/

# 3. Redémarrer
touch /home/martialcomp/public_html/passenger_wsgi.py
```

## ✅ Vérifications

### Interface utilisateur
1. Connexion en tant qu'organisateur
2. Aller dans "Gérer une compétition" 
3. Vérifier présence onglet "Résultats" (🏆)
4. Cliquer et vérifier les 4 sections principales

### Fonctionnalités
- **Dashboard Juges** : Lien vers `technical_scoring:judge_dashboard`
- **Gestion Notation** : Configuration des critères
- **Par catégorie** : 3 actions (notation, résultats, temps réel)
- **Graphique** : État de notation (Chart.js requis)

### URLs corrigées
- ~~`competitions:public:competition_results`~~ → `competitions:club:results`
- APIs temporaires remplacées par JavaScript

## ⚠️ Notes importantes

1. **Chart.js** : Chargé via CDN (pas d'installation locale)
2. **APIs manquantes** : Certains boutons affichent "en développement"
3. **Auto-refresh** : Actif uniquement sur l'onglet Résultats (5 secondes)

## 🔧 Dépannage

### Erreur 500
```bash
# Vérifier les logs
tail -f /var/log/apache2/error.log
tail -f /home/martialcomp/public_html/logs/django.log
```

### Template non trouvé
```bash
# Vérifier le chemin
ls -la /home/martialcomp/public_html/apps/competitions/templates/competitions/club/
```

### Rollback complet
```bash
# Restaurer depuis backup
cp -r /home/martialcomp/backups/[timestamp]/* /home/martialcomp/public_html/
touch /home/martialcomp/public_html/passenger_wsgi.py
```

## 📞 Support
En cas de problème, conserver le numéro de backup : `backups/[timestamp]`
README

# 5. Ajouter la liste des modifications
cat > ${PACKAGE_DIR}/CHANGELOG.md << 'CHANGELOG'
# Changelog - Onglet Résultats

## Version 2.0 - 14/10/2025

### Ajouté
- Nouvel onglet "Résultats" dans la gestion des compétitions
- Interface d'accès au dashboard des juges
- Liste des catégories avec actions rapides (notation, résultats, temps réel)
- Graphique de l'état de notation (donut chart)
- Tableau de suivi temps réel avec rafraîchissement automatique
- Intégration Chart.js 3.9.1 via CDN

### Corrigé
- NoReverseMatch pour 'competitions:public:competition_results'
- URLs d'API manquantes remplacées par placeholders JavaScript
- Gestion des erreurs pour APIs non implémentées

### Modifié
- competition_management_detail.html : +250 lignes pour l'onglet Résultats
- event_organizer.py : Ajout des données clubs pour filtres
- Ajout d'animations CSS pour indicateur LIVE

### À faire
- Implémenter API `/api/competitions/{id}/publish-results/`
- Implémenter API `/api/competitions/{id}/scoring-stats/`
- Créer vue d'export PDF des résultats
- Créer générateur de certificats
CHANGELOG

# 6. Créer l'archive finale
echo "📦 Création de l'archive..."
cd /tmp
tar -czf ${PACKAGE_NAME}.tar.gz ${PACKAGE_NAME}

# Vérifier la taille et le contenu
echo ""
echo "✅ Package créé avec succès!"
echo "📦 Fichier : /tmp/${PACKAGE_NAME}.tar.gz"
echo "📏 Taille : $(du -h /tmp/${PACKAGE_NAME}.tar.gz | cut -f1)"
echo ""
echo "📋 Contenu du package :"
tar -tzf ${PACKAGE_NAME}.tar.gz | grep -v "/$" | sort
echo ""
echo "🚀 Commandes pour le déploiement :"
echo "1. Transférer : scp /tmp/${PACKAGE_NAME}.tar.gz user@production:/home/martialcomp/"
echo "2. Extraire  : tar -xzf ${PACKAGE_NAME}.tar.gz"
echo "3. Déployer  : cd ${PACKAGE_NAME} && ./deploy_on_server.sh"