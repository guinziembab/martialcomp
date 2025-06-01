"""
Guide complet de débogage pour l'application grades dans MartialComp
"""

# Guide de débogage pour l'application grades

Ce guide propose une approche systématique pour identifier et résoudre les problèmes courants lors de l'implémentation de l'application grades dans MartialComp.

## 1. Vérification de la configuration de base

### 1.1. Vérifier l'installation de l'application

```bash
# Exécuter le script de diagnostic
python manage.py shell < debug_grades_app.py
```

### 1.2. Vérifier les migrations

```bash
# Lister les migrations
python manage.py showmigrations

# Générer les migrations si nécessaire
python manage.py makemigrations grades

# Appliquer les migrations
python manage.py migrate grades
```

### 1.3. Vérifier la configuration dans settings.py

Assurez-vous que l'application est correctement listée dans `INSTALLED_APPS` :

```python
INSTALLED_APPS = [
    # ...
    'competitions',
    'grades',
    # ...
]
```

## 2. Problèmes d'imports circulaires

### 2.1. Vérifier les imports circulaires

```bash
# Exécuter le script de vérification des imports
python manage.py shell < check_grades_imports.py
```

### 2.2. Solutions pour les imports circulaires

#### Solution 1 : Imports à l'intérieur des fonctions

```python
# Au lieu de:
from competitions.models import Discipline

# Utilisez:
def my_function():
    from competitions.models import Discipline
    # Code utilisant Discipline
```

#### Solution 2 : Références par chaîne dans les modèles

```python
# Au lieu de:
discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE)

# Utilisez:
discipline = models.ForeignKey('competitions.Discipline', on_delete=models.CASCADE)
```

#### Solution 3 : Utiliser get_model

```python
from django.apps import apps

def my_function():
    Discipline = apps.get_model('competitions', 'Discipline')
    # Code utilisant Discipline
```

## 3. Problèmes de modèles et relations

### 3.1. Vérifier les relations entre modèles

```bash
# Dans le shell Django
python manage.py shell
```

```python
from grades.models import Grade, PractitionerGrade
from competitions.models import Discipline, Practitioner

# Vérifier qu'une discipline peut être liée à un grade
discipline = Discipline.objects.first()
grade = Grade.objects.create(name="Test Grade", discipline=discipline)
print(grade.discipline)  # Devrait afficher la discipline

# Vérifier qu'un pratiquant peut avoir des grades
practitioner = Practitioner.objects.first()
practitioner_grade = PractitionerGrade.objects.create(
    practitioner=practitioner,
    grade=grade,
    discipline=discipline,
    date_obtained=timezone.now().date(),
    is_current=True
)
print(practitioner_grade.practitioner)  # Devrait afficher le pratiquant
```

### 3.2. Vérifier les contraintes d'unicité

```python
# Vérifiez les contraintes d'unicité dans le modèle PractitionerGrade
# S'il y a des erreurs d'unicité, essayez:
with transaction.atomic():
    # Code pour créer ou mettre à jour les objets
```

## 4. Problèmes de URLs et de vues

### 4.1. Vérifier les URLs de l'application

```bash
# Lister toutes les URLs définies
python manage.py show_urls | grep grades
```

### 4.2. Tester les vues principales avec des URLs spécifiques

```python
# Dans le shell Django
from django.test import Client
from django.urls import reverse

client = Client()
# Pour se connecter si nécessaire
client.login(username='admin', password='adminpassword')

# Tester la vue de liste des grades
response = client.get(reverse('grades:grade_list'))
print(response.status_code)  # Devrait être 200

# Tester la vue de détail d'un grade existant
grade_id = Grade.objects.first().id
response = client.get(reverse('grades:grade_detail', kwargs={'pk': grade_id}))
print(response.status_code)  # Devrait être 200
```

### 4.3. Vérifier les erreurs de template

Si vous obtenez une erreur `TemplateDoesNotExist`, vérifiez :

1. Que le template existe dans `grades/templates/grades/`
2. Que le nom du template dans la vue correspond exactement au fichier
3. Que `grades/templates/` est dans les répertoires de recherche de templates

## 5. Problèmes de CSRF et de formulaires

### 5.1. Tester les formulaires

```python
from django.test import Client
from django.urls import reverse

client = Client()
client.login(username='admin', password='adminpassword')

# Tester la création d'un grade
form_data = {
    'name': 'Test Grade',
    'discipline': 1,  # ID d'une discipline existante
    'level': 1,
    'min_age': 6,
    'is_active': True
}
response = client.post(reverse('grades:grade_create'), form_data, follow=True)
print(response.status_code)  # Devrait être 200
```

### 5.2. Vérifier les erreurs CSRF

Si vous avez des erreurs CSRF, assurez-vous que :

1. Le tag `{% csrf_token %}` est présent dans tous les formulaires
2. Le middleware CSRF est activé dans settings.py
3. Les cookies sont correctement gérés pour les requêtes AJAX

## 6. Problèmes de décorateurs et mixins

### 6.1. Vérifier les décorateurs personnalisés

```python
# Tester si le décorateur club_required fonctionne
from competitions.utils.decorators import club_required
from django.http import HttpRequest
from django.contrib.auth.models import User

# Créer une requête factice
request = HttpRequest()
request.user = User.objects.get(username='manager')  # Un utilisateur responsable de club

# Essayer d'appliquer le décorateur à une fonction simple
@club_required
def test_function(request):
    return "OK"

try:
    result = test_function(request)
    print("Décorateur OK:", result)
except Exception as e:
    print("Erreur avec le décorateur:", str(e))
```

## 7. Problèmes de permissions et d'authentification

### 7.1. Vérifier les permissions

```python
# Dans le shell Django
from django.contrib.auth.models import User
from competitions.models import Club

# Vérifier qu'un utilisateur est bien associé à un club
user = User.objects.get(username='manager')
club = Club.objects.filter(owner=user).first()
print(f"Club associé à {user.username}: {club}")

# Vérifier si l'utilisateur a un profil
if hasattr(user, 'profile'):
    print(f"Rôle de l'utilisateur: {user.profile.role}")
else:
    print("L'utilisateur n'a pas de profil")
```

## 8. Tests automatisés

### 8.1. Exécuter les tests de l'application

```bash
# Exécuter tous les tests
python manage.py test grades

# Exécuter une classe de test spécifique
python manage.py test grades.tests.GradeModelTestCase

# Exécuter un test spécifique
python manage.py test grades.tests.GradeModelTestCase.test_grade_creation
```

### 8.2. Utiliser le mode verbeux pour plus d'informations

```bash
python manage.py test grades -v 2
```

## 9. Problèmes courants et solutions

### 9.1. Erreur "No such table"

→ Les migrations n'ont pas été appliquées correctement.

```bash
python manage.py migrate --run-syncdb
```

### 9.2. Erreur "Cannot resolve keyword 'xxx' into field"

→ Le modèle a été modifié mais les migrations n'ont pas été mises à jour.

```bash
python manage.py makemigrations grades
python manage.py migrate grades
```

### 9.3. Erreur "Reverse for 'xxx' not found"

→ Le nom d'URL est incorrect ou n'existe pas.

```python
# Vérifiez les URLs dans grades/urls.py
# Assurez-vous que l'app_name est défini:
app_name = 'grades'
```

### 9.4. Erreur "AttributeError: 'xxx' object has no attribute 'yyy'"

→ L'objet n'a pas l'attribut attendu, souvent lié à une relation manquante.

```python
# Dans le shell Django, vérifiez l'objet
obj = Model.objects.get(id=1)
print(dir(obj))  # Liste tous les attributs et méthodes
```

### 9.5. Erreur "IntegrityError: foreign key constraint fails"

→ Une contrainte de clé étrangère est violée.

```python
# Vérifiez que l'objet référencé existe
from grades.models import Grade
grade = Grade.objects.filter(id=grade_id).exists()
if not grade:
    print(f"Le grade avec l'ID {grade_id} n'existe pas!")
```

## 10. Problèmes spécifiques au club_required

### 10.1. Le décorateur ne fonctionne pas correctement

Si le décorateur `club_required` pose problème, vérifiez son implémentation dans `competitions/utils/decorators.py` :

```python
# Voici une implémentation fonctionnelle du décorateur club_required
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils.functional import wraps

def club_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Vérification principale : l'utilisateur est-il propriétaire d'un club?
        club = None
        if hasattr(request.user, 'owned_clubs') and request.user.owned_clubs.exists():
            club = request.user.owned_clubs.first()
        elif hasattr(request.user, 'club') and request.user.club:
            club = request.user.club
        else:
            from competitions.models import Club
            club = Club.objects.filter(owner=request.user).first()

        if not club:
            messages.error(request, _("Vous devez être responsable de club pour accéder à cette page."))
            return redirect('competitions:dashboard:index')

        # Ajouter le club à la requête pour faciliter l'accès dans les vues
        request.club = club

        return view_func(request, *args, **kwargs)
    return _wrapped_view
```

### 10.2. Ajouter un club temporairement pour les tests

```python
# Dans le shell Django, pour les tests
from competitions.models import Club
from django.contrib.auth.models import User

# Créer un club et l'assigner à un utilisateur pour tester
user = User.objects.get(username='testuser')
club = Club.objects.create(name="Test Club", city="Test City", owner=user)

# Vérifier l'association
print(Club.objects.filter(owner=user).exists())  # Devrait être True
```

## 11. Administration de l'application

### 11.1. Vérifier l'enregistrement dans admin.py

Assurez-vous que les modèles sont correctement enregistrés dans `grades/admin.py` :

```python
from django.contrib import admin
from .models import (
    Grade,
    GradeCategory,
    PractitionerGrade,
    GradeRequirement,
    GradeExam,
    GradeExamRegistration
)

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('name', 'discipline', 'level', 'is_active')
    list_filter = ('discipline', 'is_active', 'is_dan_grade')
    search_fields = ('name', 'discipline__name')

@admin.register(GradeCategory)
class GradeCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'discipline', 'order', 'is_active')
    list_filter = ('discipline', 'is_active')
    search_fields = ('name', 'discipline__name')

@admin.register(PractitionerGrade)
class PractitionerGradeAdmin(admin.ModelAdmin):
    list_display = ('practitioner', 'grade', 'discipline', 'date_obtained', 'is_current')
    list_filter = ('discipline', 'is_current', 'date_obtained')
    search_fields = ('practitioner__first_name', 'practitioner__last_name', 'grade__name')
    date_hierarchy = 'date_obtained'

@admin.register(GradeRequirement)
class GradeRequirementAdmin(admin.ModelAdmin):
    list_display = ('name', 'grade', 'is_mandatory', 'order')
    list_filter = ('grade__discipline', 'is_mandatory')
    search_fields = ('name', 'grade__name')

@admin.register(GradeExam)
class GradeExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'discipline', 'date', 'status')
    list_filter = ('discipline', 'status', 'date')
    search_fields = ('title', 'description', 'location')
    date_hierarchy = 'date'
    filter_horizontal = ('available_grades',)

@admin.register(GradeExamRegistration)
class GradeExamRegistrationAdmin(admin.ModelAdmin):
    list_display = ('practitioner', 'exam', 'target_grade', 'status', 'payment_confirmed')
    list_filter = ('status', 'payment_confirmed', 'exam')
    search_fields = ('practitioner__first_name', 'practitioner__last_name', 'exam__title')
```

### 11.2. Accéder à l'interface d'administration

```bash
# Créer un superutilisateur si nécessaire
python manage.py createsuperuser

# Lancer le serveur
python manage.py runserver
```

Puis accédez à http://localhost:8000/admin/ et vérifiez que tous les modèles de l'application grades sont accessibles.

## 12. Optimisation des performances

### 12.1. Optimiser les requêtes

Utilisez `select_related` et `prefetch_related` pour réduire le nombre de requêtes SQL :

```python
# Au lieu de:
grades = PractitionerGrade.objects.filter(practitioner=practitioner)

# Utilisez:
grades = PractitionerGrade.objects.filter(practitioner=practitioner).select_related(
    'grade', 'discipline'
)
```

### 12.2. Utiliser le cache pour les opérations coûteuses

```python
from django.core.cache import cache

# Mettre en cache les grades d'une discipline
def get_grades_for_discipline(discipline_id):
    cache_key = f'discipline_grades_{discipline_id}'
    grades = cache.get(cache_key)

    if grades is None:
        grades = list(Grade.objects.filter(discipline_id=discipline_id))
        cache.set(cache_key, grades, 60*60)  # Cache pendant 1 heure

    return grades
```

## 13. Intégration avec l'app competitions

### 13.1. Ajouter des points d'entrée dans les templates de competitions

Dans `competitions/templates/competitions/club/practitioner_detail.html` ou un autre template approprié :

```html
{% if 'grades' in settings.INSTALLED_APPS %}
<div class="card mt-3">
  <div class="card-header">
    <h5 class="mb-0"><i class="fas fa-award me-2"></i>{% trans "Grades" %}</h5>
  </div>
  <div class="card-body">
    <a
      href="{% url 'grades:practitioner_grades' practitioner.id %}"
      class="btn btn-primary"
    >
      <i class="fas fa-eye me-1"></i>{% trans "Voir les grades" %}
    </a>
    <a
      href="{% url 'grades:add_practitioner_grade' practitioner.id %}"
      class="btn btn-success"
    >
      <i class="fas fa-plus-circle me-1"></i>{% trans "Ajouter un grade" %}
    </a>
  </div>
</div>
{% endif %}
```

### 13.2. Ajouter un lien dans le menu de navigation

Dans le template où se trouve votre menu de navigation :

```html
{% if 'grades' in settings.INSTALLED_APPS %}
<li class="nav-item">
  <a href="{% url 'grades:grade_list' %}" class="nav-link">
    <i class="fas fa-award"></i> {% trans "Grades" %}
  </a>
</li>
{% endif %}
```

## 14. Vérification finale

### 14.1. Liste de vérification pour la mise en production

- [ ] Toutes les migrations sont appliquées
- [ ] Les tests passent sans erreur
- [ ] Les URLs sont correctement configurées
- [ ] Les modèles ont les bonnes relations
- [ ] Les formulaires fonctionnent correctement
- [ ] Les permissions et décorateurs sont bien configurés
- [ ] Les templates sont tous présents et fonctionnels
- [ ] L'interface d'administration est configurée
- [ ] Les traductions sont complètes (si nécessaire)
- [ ] Les performances sont optimisées

### 14.2. Sauvegarder la base de données avant les modifications

```bash
# Créer une sauvegarde des données
python manage.py dumpdata grades > grades_backup.json

# Pour restaurer si nécessaire
python manage.py loaddata grades_backup.json
```

## Conclusion

En suivant ce guide de débogage systématique, vous devriez pouvoir identifier et résoudre la plupart des problèmes courants lors de l'implémentation de l'application grades. Si des problèmes persistent, n'hésitez pas à consulter la documentation Django ou à demander de l'aide sur des forums spécialisés comme Stack Overflow.

Bonne résolution de problèmes!
