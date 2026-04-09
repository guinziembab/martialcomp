# PHASE 2: Isolation des donnees par discipline

## Resume des modifications

Cette phase complete la securisation du systeme MartialComp en implementant
l'isolation des donnees par discipline. Chaque utilisateur ne peut acceder
qu'aux donnees liees aux disciplines de son organisation.

## Fichiers modifies

### 1. Apps/Grades

#### Views Core (`apps/grades/views/core.py`)
- Applique `DisciplineAccessMixin` a toutes les CBV:
  - GradeDetailView, GradeCreateView, GradeUpdateView, GradeDeleteView
  - GradeCategoryListView, GradeCategoryCreateView, GradeCategoryUpdateView, GradeCategoryDeleteView
  - GradeExamListView, GradeExamDetailView, GradeExamCreateView, GradeExamUpdateView, GradeExamDeleteView
  - GradeRequirementListView, GradeRequirementCreateView, GradeRequirementUpdateView, GradeRequirementDeleteView
- Securise `get_eligible_practitioners` avec verification d'acces discipline

#### Views API (`apps/grades/views/api.py`)
- Securise `categories_by_discipline` avec verification d'acces
- Securise `grades_by_disciplines` avec filtrage par disciplines accessibles

#### Views Bulk (`apps/grades/views/bulk.py`)
- Ajoute filtrage discipline a `bulk_grade_assignment_form`
- Ajoute verification d'acces a `batch_update_grades`

#### Views Dashboard (`apps/grades/views/dashboard.py`)
- Ajoute verification d'acces discipline dans le filtrage
- Utilise `get_user_disciplines` pour la liste des disciplines

#### Forms (`apps/grades/forms.py`)
- Securise `GradeCategoryForm` avec parametre `user`
- Securise `GradeForm` avec parametre `user`
- Securise `GradeExamForm` avec parametre `user`
- Securise `GradeRequirementForm` avec parametre `user`

### 2. Apps/Competitions

#### Forms Competitions (`apps/competitions/forms/competitions.py`)
- Ajoute imports de securite
- Securise `CompetitionForm` avec parametre `user`

#### Forms Categories (`apps/competitions/forms/categories.py`)
- Ajoute imports de securite
- Securise `CategoryTemplateForm` avec parametre `user`

#### Forms Judges (`apps/competitions/forms/judges.py`)
- Ajoute imports de securite
- Securise `JudgeProfileForm` (champs main_discipline et disciplines)
- Securise `JudgeSearchForm` avec parametre `user`

### 3. Tests

#### Nouveau fichier (`apps/grades/tests/test_discipline_isolation.py`)
- Tests `DisciplineIsolationTestCase`: helpers de securite
- Tests `GradeAPIIsolationTestCase`: APIs de grades
- Tests `FormDisciplineIsolationTestCase`: formulaires
- Tests `MixinDisciplineIsolationTestCase`: mixin et vues

## Regles de securite appliquees

1. **Principe du moindre privilege**: Sans utilisateur, les querysets sont vides
2. **Filtrage par organisation**: Les utilisateurs voient les disciplines de leur organisation
3. **Superusers exempts**: Les superusers ont acces a toutes les disciplines
4. **Logging**: Tous les acces refuses sont logues dans 'discipline_isolation'

## Commandes de deploiement

```bash
# Copier les fichiers vers production
rsync -avz apps/grades/ user@server:/path/to/app/apps/grades/
rsync -avz apps/competitions/forms/ user@server:/path/to/app/apps/competitions/forms/

# Redemarrer le serveur
sudo systemctl restart gunicorn

# Executer les tests
python manage.py test apps.grades.tests.test_discipline_isolation
```

## Verification post-deploiement

1. Se connecter avec un utilisateur club (non superuser)
2. Verifier que seules les disciplines du club sont visibles
3. Tester l'acces a une URL de grade d'une autre discipline (doit etre refuse)
4. Verifier les logs pour les tentatives d'acces refuses

## Date de modification

2026-01-09
