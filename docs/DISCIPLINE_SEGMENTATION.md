# Architecture de Segmentation par Discipline

## Vue d'ensemble

MartialComp implémente un système de segmentation des données par discipline pour garantir que chaque utilisateur n'accède qu'aux données des disciplines auxquelles il est autorisé.

## Table des matières

1. [Principe de fonctionnement](#principe-de-fonctionnement)
2. [Architecture des modèles](#architecture-des-modèles)
3. [Helpers de sécurité](#helpers-de-sécurité)
4. [Mixins et décorateurs](#mixins-et-décorateurs)
5. [Formulaires sécurisés](#formulaires-sécurisés)
6. [Audit et logging](#audit-et-logging)
7. [Guide pour les développeurs](#guide-pour-les-développeurs)

---

## Principe de fonctionnement

### Règles d'isolation

1. **Superusers et Staff** : Accès à toutes les disciplines
2. **Utilisateurs normaux** : Accès uniquement aux disciplines de leur organisation
3. **Fallback sécurisé** : En cas d'erreur, retourner `queryset.none()` plutôt que de risquer une fuite de données

### Chaîne de détermination des disciplines

```
Utilisateur
    │
    ├── UserProfile.organization
    │       │
    │       └── organization.disciplines (ManyToMany)
    │
    ├── Club.owner
    │       │
    │       └── club.disciplines (ManyToMany)
    │
    └── Practitioner.club
            │
            └── club.disciplines (ManyToMany)
```

---

## Architecture des modèles

### Modèles clés

```python
# apps/competitions/models/discipline.py
class Discipline(models.Model):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

# apps/organizations/models.py
class Organization(models.Model):
    disciplines = models.ManyToManyField(Discipline, related_name='organizations')

# apps/competitions/models/club.py
class Club(models.Model):
    disciplines = models.ManyToManyField(Discipline, related_name='clubs')
    owner = models.ForeignKey(User, on_delete=models.SET_NULL)
```

### Modèle d'audit (Phase 3)

```python
# apps/core/models.py
class DisciplineAccessLog(models.Model):
    """Journal des accès aux données par discipline."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True)
    action = models.CharField(choices=[
        ('view', 'Consultation'),
        ('edit', 'Modification'),
        ('create', 'Creation'),
        ('delete', 'Suppression'),
        ('export', 'Export'),
        ('api_access', 'Acces API'),
    ])
    allowed = models.BooleanField()
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True)
    resource_type = models.CharField(max_length=100, blank=True)
    resource_id = models.PositiveIntegerField(null=True)
    details = models.JSONField(default=dict)
```

---

## Helpers de sécurité

Fichier : `apps/competitions/utils/permission_helpers.py`

### get_user_organization(user)

Récupère l'organisation de l'utilisateur.

```python
from apps.competitions.utils.permission_helpers import get_user_organization

organization = get_user_organization(request.user)
```

### get_user_disciplines(user, organization=None)

Retourne les disciplines accessibles à un utilisateur.

```python
from apps.competitions.utils.permission_helpers import get_user_disciplines

# Retourne un QuerySet de Discipline
disciplines = get_user_disciplines(request.user)
```

### check_discipline_access(user, discipline, ...)

Vérifie si un utilisateur peut accéder à une discipline.

```python
from apps.competitions.utils.permission_helpers import check_discipline_access

# Vérification simple
if check_discipline_access(user, discipline):
    # Accès autorisé
    pass

# Avec logging d'audit (Phase 3)
if check_discipline_access(
    user,
    discipline,
    log_access=True,
    request=request,
    action='view',
    resource_type='Grade',
    resource_id=grade.pk
):
    # Accès autorisé
    pass
```

### filter_queryset_by_user_disciplines(queryset, user, discipline_field)

Filtre un queryset par les disciplines accessibles.

```python
from apps.competitions.utils.permission_helpers import filter_queryset_by_user_disciplines

# Filtrer les grades par disciplines accessibles
grades = Grade.objects.all()
filtered_grades = filter_queryset_by_user_disciplines(grades, request.user, 'discipline')
```

---

## Mixins et décorateurs

### DisciplineAccessMixin

Mixin pour les Class-Based Views.

```python
from apps.competitions.utils.permission_helpers import DisciplineAccessMixin

class GradeDetailView(DisciplineAccessMixin, DetailView):
    model = Grade
    discipline_field = 'discipline'  # Optionnel, défaut: 'discipline'
```

### DisciplineFormMixin

Mixin pour les formulaires.

```python
from apps.competitions.utils.permission_helpers import DisciplineFormMixin

class MyForm(DisciplineFormMixin, forms.ModelForm):
    discipline_fields = ['discipline', 'secondary_discipline']

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.filter_discipline_fields()
```

### @secure_discipline_api_view

Décorateur pour les vues API.

```python
from apps.competitions.utils.permission_helpers import secure_discipline_api_view

@secure_discipline_api_view
def my_api_view(request):
    # request.accessible_disciplines contient les disciplines accessibles
    # request.discipline_ids contient les IDs
    disciplines = request.accessible_disciplines
    return JsonResponse({'disciplines': list(disciplines.values())})
```

---

## Formulaires sécurisés

### Pattern standard

Tous les formulaires avec un champ discipline doivent :

1. Accepter un paramètre `user=None`
2. Filtrer le queryset des disciplines selon l'utilisateur
3. Retourner `Discipline.objects.none()` si aucun utilisateur

```python
import logging
from apps.competitions.utils.permission_helpers import get_user_disciplines

logger = logging.getLogger('discipline_isolation')

class MyForm(forms.ModelForm):
    class Meta:
        model = MyModel
        fields = ['name', 'discipline']

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user:
            if user.is_superuser:
                self.fields['discipline'].queryset = Discipline.objects.filter(is_active=True)
            else:
                self.fields['discipline'].queryset = get_user_disciplines(user)
        else:
            # SÉCURITÉ: Sans utilisateur, aucune discipline
            self.fields['discipline'].queryset = Discipline.objects.none()
            logger.warning("MyForm: No user provided - disciplines empty")
```

### Formulaires sécurisés dans le projet

| Fichier | Formulaire | Statut |
|---------|------------|--------|
| `apps/grades/forms.py` | `GradeForm` | ✅ Sécurisé |
| `apps/grades/forms.py` | `GradeCategoryForm` | ✅ Sécurisé |
| `apps/grades/forms.py` | `GradeRequirementForm` | ✅ Sécurisé |
| `apps/competitions/forms/competitions.py` | `CompetitionForm` | ✅ Sécurisé |
| `apps/competitions/forms/categories.py` | `CategoryTemplateForm` | ✅ Sécurisé |
| `apps/competitions/forms/judges.py` | `JudgeProfileForm` | ✅ Sécurisé |
| `apps/competitions/forms/judges.py` | `JudgeSearchForm` | ✅ Sécurisé |

---

## Audit et logging

### Logger dédié

Toutes les opérations de sécurité utilisent le logger `discipline_isolation`.

```python
import logging
logger = logging.getLogger('discipline_isolation')
```

Configuration dans `settings/base.py` :

```python
LOGGING = {
    'loggers': {
        'discipline_isolation': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': True,
        },
    },
}
```

### Modèle DisciplineAccessLog

Utilisé pour auditer les accès refusés.

```python
from apps.core.models import DisciplineAccessLog

# Logger un accès refusé
DisciplineAccessLog.log_denied_access(
    user=request.user,
    discipline=discipline,
    action='view',
    request=request,
    resource_type='Grade',
    resource_id=grade.pk,
    reason='User not authorized for this discipline'
)

# Récupérer les statistiques
from datetime import timedelta
from django.utils import timezone

stats = DisciplineAccessLog.get_access_stats(
    since=timezone.now() - timedelta(days=7)
)
# Retourne: {'total': N, 'allowed': N, 'denied': N, 'denial_rate': X.X, ...}

# Récupérer les accès refusés
denied = DisciplineAccessLog.get_denied_accesses(
    since=timezone.now() - timedelta(days=1),
    user=some_user
)
```

### Interface d'administration

Les logs sont accessibles dans l'admin Django à `/admin/core/disciplineaccesslog/`.

Fonctionnalités :
- Filtrage par statut (autorisé/refusé)
- Filtrage par action
- Filtrage par discipline/organisation
- Recherche par utilisateur, IP, type de ressource
- Statistiques rapides (24h, 7 jours)

---

## Guide pour les développeurs

### Checklist pour une nouvelle vue

1. [ ] Importer les helpers de sécurité
2. [ ] Utiliser `DisciplineAccessMixin` pour les CBV
3. [ ] Filtrer les querysets avec `filter_queryset_by_user_disciplines()`
4. [ ] Vérifier l'accès avec `check_discipline_access()` si nécessaire
5. [ ] Logger les refus d'accès

### Checklist pour un nouveau formulaire

1. [ ] Ajouter le paramètre `user=None` à `__init__()`
2. [ ] Filtrer les champs discipline avec `get_user_disciplines()`
3. [ ] Utiliser `Discipline.objects.none()` comme fallback
4. [ ] Logger un warning si pas d'utilisateur fourni

### Exemple complet de vue sécurisée

```python
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.competitions.utils.permission_helpers import (
    DisciplineAccessMixin,
    filter_queryset_by_user_disciplines,
    get_user_disciplines
)
from apps.grades.models import Grade

class GradeListView(DisciplineAccessMixin, ListView):
    model = Grade
    template_name = 'grades/grade_list.html'
    discipline_field = 'discipline'

    def get_queryset(self):
        # Le mixin filtre automatiquement, mais on peut ajouter d'autres filtres
        qs = super().get_queryset()

        # Filtrer par discipline sélectionnée
        discipline_id = self.request.GET.get('discipline')
        if discipline_id:
            qs = qs.filter(discipline_id=discipline_id)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fournir les disciplines accessibles pour le filtre
        context['disciplines'] = get_user_disciplines(self.request.user)
        return context
```

### Bonnes pratiques

1. **Ne jamais** exposer toutes les disciplines par défaut
2. **Toujours** utiliser `queryset.none()` comme fallback sécurisé
3. **Logger** tous les accès refusés
4. **Tester** l'isolation avec des tests automatisés
5. **Vérifier** les superusers ont accès à tout
6. **Documenter** les champs discipline dans les modèles

---

## Tests d'isolation

Fichier : `apps/grades/tests/test_discipline_isolation.py`

```bash
# Exécuter les tests d'isolation
python manage.py test apps.grades.tests.test_discipline_isolation
```

Classes de test :
- `DisciplineIsolationTestCase` - Tests des helpers
- `GradeAPIIsolationTestCase` - Tests des APIs
- `FormDisciplineIsolationTestCase` - Tests des formulaires
- `MixinDisciplineIsolationTestCase` - Tests du mixin

---

## Historique des modifications

| Date | Phase | Description |
|------|-------|-------------|
| 2025-01-XX | Phase 1 | Corrections critiques de sécurité |
| 2025-01-XX | Phase 2 | Sécurisation formulaires, vues, APIs |
| 2025-01-XX | Phase 3 | Audit logging et documentation |

---

## Contacts

Pour toute question sur l'architecture de sécurité :
- Consulter les logs : `discipline_isolation` logger
- Admin audit : `/admin/core/disciplineaccesslog/`
