#!/bin/bash
# Script pour créer le package de déploiement du patch onboarding

PATCH_DIR="onboarding_patch_production_20251017_000929"

echo "================================================"
echo "📦 CRÉATION DU PACKAGE PATCH ONBOARDING"
echo "================================================"

# Créer la structure des répertoires
echo "📁 Création de la structure..."
mkdir -p $PATCH_DIR/apps/competitions/management/commands
mkdir -p $PATCH_DIR/apps/competitions/views/onboarding
mkdir -p $PATCH_DIR/apps/competitions/templates/competitions/onboarding
mkdir -p $PATCH_DIR/apps/competitions/urls
mkdir -p $PATCH_DIR/scripts

# Copier les fichiers modifiés
echo ""
echo "📋 Copie des fichiers du patch..."

# 1. Commande d'initialisation des disciplines
cp apps/competitions/management/commands/init_disciplines.py $PATCH_DIR/apps/competitions/management/commands/
echo "✅ init_disciplines.py"

# 2. Vues d'urgence sécurisées
cp apps/competitions/views/onboarding/emergency_views.py $PATCH_DIR/apps/competitions/views/onboarding/
echo "✅ emergency_views.py"

# 3. Template de page d'erreur
cp apps/competitions/templates/competitions/onboarding/error.html $PATCH_DIR/apps/competitions/templates/competitions/onboarding/
echo "✅ error.html"

# 4. Configuration des URLs (modifiée)
cp apps/competitions/urls/onboarding.py $PATCH_DIR/apps/competitions/urls/
echo "✅ onboarding.py (URLs)"

# 5. Script d'initialisation des disciplines
cp init_disciplines_direct.py $PATCH_DIR/scripts/
echo "✅ init_disciplines_direct.py"

# 6. Créer le script de déploiement
cat > $PATCH_DIR/deploy_patch.sh << 'EOF'
#!/bin/bash
# Script de déploiement du patch onboarding en production

echo "================================================"
echo "🚀 DÉPLOIEMENT PATCH ONBOARDING - PRODUCTION"
echo "================================================"
echo ""

# Variables
BACKUP_DIR="/home/martialc/backups/onboarding_$(date +%Y%m%d_%H%M%S)"
PROJECT_DIR="/home/martialc/martialcomp"

# Créer le répertoire de backup
echo "📁 Création du backup..."
mkdir -p $BACKUP_DIR

# Backup des fichiers existants
if [ -f "$PROJECT_DIR/apps/competitions/views/onboarding/emergency_views.py" ]; then
    cp $PROJECT_DIR/apps/competitions/views/onboarding/emergency_views.py $BACKUP_DIR/
fi
if [ -f "$PROJECT_DIR/apps/competitions/urls/onboarding.py" ]; then
    cp $PROJECT_DIR/apps/competitions/urls/onboarding.py $BACKUP_DIR/
fi

# Copier les nouveaux fichiers
echo ""
echo "📋 Installation des fichiers..."
cp -r apps/* $PROJECT_DIR/apps/
echo "✅ Fichiers copiés"

# Initialiser les disciplines
echo ""
echo "🔧 Initialisation des disciplines..."
cd $PROJECT_DIR
python manage.py init_disciplines

# Collecter les fichiers statiques
echo ""
echo "📦 Collection des fichiers statiques..."
python manage.py collectstatic --noinput

# Redémarrer les services
echo ""
echo "🔄 Redémarrage des services..."
# Option 1: Passenger
touch tmp/restart.txt
echo "✅ Passenger redémarré"

# Option 2: systemctl (décommenter si nécessaire)
# sudo systemctl restart gunicorn
# sudo systemctl restart nginx

echo ""
echo "================================================"
echo "✅ PATCH DÉPLOYÉ AVEC SUCCÈS!"
echo "================================================"
echo ""
echo "📝 Vérifications recommandées:"
echo "1. Tester l'onboarding: https://app.martialcomp.com/competitions/onboarding/"
echo "2. Vérifier les logs: tail -f /var/log/martialcomp/django.log"
echo "3. En cas de problème, restaurer depuis: $BACKUP_DIR"
EOF

chmod +x $PATCH_DIR/deploy_patch.sh

# 7. Créer le README
cat > $PATCH_DIR/README.md << 'EOF'
# 🚀 Patch Onboarding MartialComp - Production

## 📋 Description

Ce patch corrige l'erreur 500 lors de l'onboarding en ajoutant :
- ✅ Gestion d'erreurs robuste sur toutes les vues
- ✅ Création automatique du profil utilisateur si manquant
- ✅ Fallback sur disciplines par défaut
- ✅ Page d'erreur gracieuse
- ✅ Correction de la redirection vers le dashboard fédération

## 📁 Contenu du patch

```
apps/competitions/
├── management/commands/
│   └── init_disciplines.py          # Commande pour initialiser les disciplines
├── views/onboarding/
│   └── emergency_views.py           # Vues sécurisées avec gestion d'erreurs
├── templates/competitions/onboarding/
│   └── error.html                   # Page d'erreur user-friendly
└── urls/
    └── onboarding.py                # URLs modifiées avec routes sécurisées

scripts/
└── init_disciplines_direct.py       # Script direct d'initialisation (backup)
```

## 🔧 Installation

1. **Transférer le package sur le serveur**
```bash
scp -r onboarding_patch_production_* user@martialcomp-production:/home/martialc/
```

2. **Se connecter au serveur**
```bash
ssh user@martialcomp-production
```

3. **Extraire et exécuter**
```bash
cd /home/martialc
tar -xzf onboarding_patch_production_*.tar.gz
cd onboarding_patch_production_*
sudo ./deploy_patch.sh
```

## ✅ Corrections appliquées

### 1. Vue safe_club_creation()
- Try/except sur toute la logique
- Création automatique du UserProfile si manquant
- Gestion des disciplines manquantes

### 2. Vue safe_federation_creation()
- Correction de la redirection: `'dashboard:federation'` → `'competitions:dashboard:federations'`
- Gestion robuste des erreurs
- Logs détaillés pour debugging

### 3. URLs activées
- `/competitions/onboarding/club/creation/` → Vue sécurisée
- `/competitions/onboarding/federation/` → Vue sécurisée
- `/competitions/onboarding/error/` → Page d'erreur
- `/competitions/onboarding/complete/` → Finalisation

## 🔍 Vérification post-déploiement

1. **Tester la création de club**
   - https://app.martialcomp.com/competitions/onboarding/club/creation/
   
2. **Tester la création de fédération**
   - https://app.martialcomp.com/competitions/onboarding/federation/
   
3. **Vérifier les disciplines**
   ```bash
   python manage.py shell
   from apps.competitions.models import Discipline
   print(f"Disciplines actives: {Discipline.objects.filter(is_active=True).count()}")
   ```

## 🔄 Rollback si nécessaire

Les backups sont créés automatiquement dans `/home/martialc/backups/onboarding_*`

Pour restaurer :
```bash
cp /home/martialc/backups/onboarding_*/emergency_views.py /home/martialc/martialcomp/apps/competitions/views/onboarding/
cp /home/martialc/backups/onboarding_*/onboarding.py /home/martialc/martialcomp/apps/competitions/urls/
touch /home/martialc/martialcomp/tmp/restart.txt
```

## 📞 Support

En cas de problème :
- Logs Django : `/var/log/martialcomp/django.log`
- Logs Passenger : `/var/log/passenger/passenger.log`
- Contact : support@martialcomp.com
EOF

# 8. Créer le script SQL pour vérifier/créer les disciplines (optionnel)
cat > $PATCH_DIR/scripts/check_disciplines.sql << 'EOF'
-- Script SQL pour vérifier les disciplines
SELECT COUNT(*) as total_disciplines FROM competitions_discipline;
SELECT COUNT(*) as active_disciplines FROM competitions_discipline WHERE is_active = true;
SELECT id, name, is_active FROM competitions_discipline ORDER BY name LIMIT 20;
EOF

# Créer l'archive
echo ""
echo "📦 Création de l'archive..."
tar -czf ${PATCH_DIR}.tar.gz $PATCH_DIR/

echo ""
echo "================================================"
echo "✅ PACKAGE CRÉÉ AVEC SUCCÈS!"
echo "================================================"
echo ""
echo "📦 Fichier: ${PATCH_DIR}.tar.gz"
echo ""
echo "🚀 Pour déployer:"
echo "1. scp ${PATCH_DIR}.tar.gz user@martialcomp-production:/home/martialc/"
echo "2. ssh user@martialcomp-production"
echo "3. tar -xzf ${PATCH_DIR}.tar.gz"
echo "4. cd ${PATCH_DIR}"
echo "5. sudo ./deploy_patch.sh"
echo ""