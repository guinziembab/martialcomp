# Fichiers à transférer en production - 14 Octobre 2025

## 🔴 CRITIQUES - Fichiers Python/Template modifiés

### 1. **apps/competitions/views/categories.py**
- **Modifié**: 14 Oct 18:17
- **Changements**: 
  - Ajout de l'import `from apps.grades.models import Grade`
  - Ajout de la fonction `get_discipline_grades()` pour l'API des grades
  - Variables `min_grade` et `max_grade` définies dans `add_category()`
- **Impact**: Corrige l'erreur de création de catégorie et ajoute l'API des grades

### 2. **apps/competitions/urls/competitions.py**
- **Modifié**: 14 Oct 18:17
- **Changements**:
  - Import de `get_discipline_grades`
  - Nouvelle route: `path('<int:competition_id>/api/grades/', get_discipline_grades, name='get_discipline_grades')`
- **Impact**: Active l'endpoint API pour récupérer les grades

### 3. **apps/competitions/templates/competitions/club/competition_management_detail.html**
- **Modifié**: 14 Oct 18:18
- **Changements**:
  - Remplacement des inputs text par des selects pour les grades
  - Ajout du JavaScript pour la soumission AJAX du formulaire
  - Ajout de la fonction `loadDisciplineGrades()`
  - Gestion des événements du modal
- **Impact**: Corrige l'affichage JSON brut et active la sélection dynamique des grades

## 📦 Package de transfert recommandé

```bash
# Créer un package avec les fichiers modifiés
tar -czf categories_fix_20251014.tar.gz \
  apps/competitions/views/categories.py \
  apps/competitions/urls/competitions.py \
  apps/competitions/templates/competitions/club/competition_management_detail.html
```

## 🚀 Commandes de déploiement

### Option 1: Utiliser le script automatisé
```bash
# Transférer et exécuter le script automatisé
scp deploy_categories_production_automated.sh martialcomp-production:/tmp/
ssh martialcomp-production
cd /var/www/vhosts/martialcomp.com/httpdocs
bash /tmp/deploy_categories_production_automated.sh
```

### Option 2: Déploiement manuel
```bash
# 1. Se connecter
ssh martialcomp-production
cd /var/www/vhosts/martialcomp.com/httpdocs

# 2. Backup
mkdir -p backups/$(date +%Y%m%d)
cp apps/competitions/views/categories.py backups/$(date +%Y%m%d)/
cp apps/competitions/urls/competitions.py backups/$(date +%Y%m%d)/
cp apps/competitions/templates/competitions/club/competition_management_detail.html backups/$(date +%Y%m%d)/

# 3. Transférer les fichiers
# (depuis votre machine locale)
scp apps/competitions/views/categories.py martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/
scp apps/competitions/urls/competitions.py martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/urls/
scp apps/competitions/templates/competitions/club/competition_management_detail.html martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/club/

# 4. Sur le serveur
source /var/www/vhosts/martialcomp.com/venv/bin/activate
python manage.py collectstatic --noinput --settings=config.settings.production
sudo systemctl restart martialcomp.service
```

## 📄 Fichiers de documentation créés (pour référence)

1. **RAPPORT_CORRECTION_CATEGORIES_COMPLETE.md** - Rapport détaillé des corrections
2. **DEPLOIEMENT_PRODUCTION_CATEGORIES_COMPLET.md** - Guide complet de déploiement
3. **template_patch_categories.txt** - Patch pour les modifications du template
4. **deploy_categories_production_automated.sh** - Script de déploiement automatisé
5. **deploy_category_fixes.sh** - Script de déploiement simple

## ⚠️ Points d'attention

1. **Template HTML**: Contient beaucoup de JavaScript, vérifier que tout est bien copié
2. **Permissions**: S'assurer que les fichiers ont les bonnes permissions après transfert
3. **Cache**: Peut nécessiter un vidage du cache navigateur pour voir les changements JS
4. **Grades**: Vérifier que les grades existent dans la base pour la discipline testée

## 🧪 Tests post-déploiement

1. Créer une catégorie et vérifier:
   - ✅ Pas d'affichage JSON brut
   - ✅ Message de succès dans l'interface
   - ✅ Page se recharge avec la nouvelle catégorie

2. Sélection des grades:
   - ✅ Les dropdowns se remplissent à l'ouverture du modal
   - ✅ Les grades correspondent à la discipline

3. Gestion d'erreurs:
   - ✅ Essayer sans nom → message d'erreur approprié