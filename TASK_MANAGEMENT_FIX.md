# 🔧 Guide de Correction Task Management

Ce guide vous aidera à diagnostiquer et corriger les problèmes de l'application `task_management`.

## 📋 Problème Principal Détecté

L'erreur principale était :
```
RuntimeError: Model class apps.task_management.models.boards.Board doesn't declare an explicit app_label and isn't in an application in INSTALLED_APPS.
```

## ✅ Corrections Automatiques Appliquées

1. **INSTALLED_APPS** - Ajout de `'apps.task_management'` dans `config/settings/base.py`
2. **URLs** - Ajout de `path('task-management/', include('apps.task_management.urls'))` dans `config/urls.py`
3. **Imports conditionnels** - Correction de l'ordre des imports dans les fichiers dashboard
4. **Scripts de diagnostic** - Création de scripts automatiques pour tester et corriger

## 🚀 Instructions de Correction

### Option 1: Script Automatique (Recommandé)

```bash
# Dans le répertoire C:\martial_hub_django\martialcomp\
python run_task_management_fix.py
```

Ce script va :
- Vérifier la configuration Django
- Créer et appliquer les migrations
- Tester tous les composants
- Créer des données de test si nécessaire

### Option 2: Correction Manuelle

Si le script automatique échoue, suivez ces étapes :

#### Étape 1: Vérifier INSTALLED_APPS
```python
# Dans config/settings/base.py
INSTALLED_APPS = [
    # ... autres apps
    'apps.task_management',  # ✅ Doit être présent
    # ...
]
```

#### Étape 2: Créer les migrations
```bash
python manage.py makemigrations task_management
python manage.py migrate task_management
```

#### Étape 3: Vérifier les URLs
```python
# Dans config/urls.py, dans i18n_patterns()
urlpatterns += i18n_patterns(
    # ... autres URLs
    path('task-management/', include('apps.task_management.urls')),
    # ...
)
```

#### Étape 4: Test du serveur
```bash
python manage.py runserver 8000
```

## 🔍 Scripts de Diagnostic Disponibles

### 1. Test Complet
```bash
python test_task_management.py
```
- Teste tous les composants
- Vérifie les imports, modèles, migrations, templates
- Affiche un rapport détaillé

### 2. Correction Automatique
```bash
python fix_task_management.py
```
- Corrige automatiquement les problèmes détectés
- Crée les migrations manquantes
- Génère des données de test

### 3. Diagnostic Global
```bash
python run_task_management_fix.py
```
- Lance tous les tests et corrections
- Fournit un rapport complet
- Recommandations pour les prochaines étapes

## 📊 Structure des Fichiers Task Management

```
apps/task_management/
├── __init__.py
├── apps.py                     ✅ Configuration de l'app
├── models/
│   ├── __init__.py            ✅ Import des modèles
│   ├── boards.py              ✅ Modèle Board, Column
│   ├── tasks.py               ✅ Modèle Task
│   └── assignments.py         ✅ Modèle TaskAssignment
├── views/
│   ├── __init__.py
│   ├── boards.py              ✅ Vues des tableaux
│   ├── kanban.py              ✅ Vue Kanban
│   └── tasks.py               ✅ Vues des tâches
├── templates/task_management/
│   ├── base/                  ✅ Templates de base
│   ├── boards/                ✅ Templates tableaux
│   ├── kanban/                ✅ Templates Kanban
│   ├── widgets/               ✅ Widgets dashboard
│   └── modals/                ✅ Modales
├── static/task_management/
│   ├── css/                   ✅ Styles CSS
│   └── js/                    ✅ JavaScript
├── templatetags/
│   ├── task_permissions.py    ✅ Template tags
│   └── task_i18n.py          ✅ Traductions
├── management/commands/
│   ├── generate_task_translations.py  ✅ Génération traductions
│   └── validate_translations.py       ✅ Validation traductions
├── urls.py                    ✅ Configuration URLs
├── permissions.py             ✅ Système de permissions
├── dashboard_utils.py         ✅ Utilitaires dashboard
└── admin.py                   ✅ Interface admin
```

## 🎯 Vérifications Post-Correction

Après correction, vérifiez :

1. **Serveur démarre sans erreur**
   ```bash
   python manage.py runserver 8000
   ```

2. **Page task-management accessible**
   - URL: `http://localhost:8000/fr/task-management/`

3. **Dashboard avec widgets**
   - Les dashboards affichent les widgets task management
   - Aucune erreur 500 sur les pages dashboard

4. **Base de données**
   - Tables task_management créées
   - Migrations appliquées

## ❌ Erreurs Courantes et Solutions

### Erreur: "No module named 'apps.task_management'"
**Solution**: Vérifiez `INSTALLED_APPS` dans `settings/base.py`

### Erreur: "Reverse for 'task_management:board_list' not found"
**Solution**: Vérifiez que les URLs sont incluses dans `urls.py`

### Erreur: "relation does not exist"
**Solution**: Appliquez les migrations :
```bash
python manage.py migrate task_management
```

### Erreur: "Template does not exist"
**Solution**: Vérifiez la structure des templates dans `templates/task_management/`

## 📞 Support

Si les problèmes persistent :

1. Lancez `python test_task_management.py` pour un diagnostic détaillé
2. Vérifiez les logs Django pour les erreurs spécifiques
3. Consultez la documentation des erreurs dans le terminal

## 🎉 Après Correction Réussie

Une fois tous les tests passés :

1. **Accédez aux tableaux Kanban** : `/fr/task-management/`
2. **Créez un premier tableau** pour tester
3. **Vérifiez les widgets** dans les dashboards club/federation/coach
4. **Testez la traduction** en changeant de langue

L'application task_management devrait maintenant être entièrement fonctionnelle avec toutes les fonctionnalités Kanban, les widgets dashboard et le support multilingue.