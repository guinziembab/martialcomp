# Segmentation par Discipline dans MartialComp

## Résumé du Problème

Le système doit segmenter les données par discipline : le Karaté ne doit pas voir les informations du Judo et vice-versa. Actuellement, cette segmentation n'est pas appliquée correctement, particulièrement pour la sélection des grades.

## Problèmes Identifiés

### 1. **API des Grades Non Sécurisée** ❌
- La fonction `get_grades_by_disciplines()` retourne TOUS les grades d'une discipline
- Pas de vérification des permissions ou de l'organisation de l'utilisateur
- N'importe quel utilisateur peut voir tous les grades de n'importe quelle discipline

### 2. **Disciplines Sans Organisation** ⚠️
L'analyse montre que :
- Sur 35 disciplines, seulement 2 ont des organisations associées
- Karaté : 1 organisation (CLUB BGATEST1)
- Long Phai : 1 organisation (FEDETEST2)
- **33 disciplines n'ont AUCUNE organisation**

C'est la cause principale du problème de segmentation !

### 3. **Absence de Middleware de Discipline** 
- Pas de système centralisé pour gérer la discipline courante
- Chaque vue gère manuellement le filtrage
- Pas de contexte global pour les templates

## Solutions Implémentées

### 1. **Correction de l'API des Grades** ✅
```python
# Ajout du filtrage par organisation dans get_grades_by_disciplines()
- Vérification que l'utilisateur a accès à la discipline
- Filtrage des grades par organisation de l'utilisateur
- Utilisation de get_filtered_disciplines_for_user()
```

### 2. **Correction des Formulaires** ✅
```python
# PractitionerGradeForm modifié pour :
- Accepter l'utilisateur en paramètre
- Filtrer les grades par disciplines accessibles
- N'afficher que les grades pertinents
```

### 3. **Nouveau Middleware DisciplineMiddleware** ✅
```python
# Gère automatiquement :
- La discipline courante en session
- Les disciplines accessibles par utilisateur
- L'injection dans le contexte des templates
```

### 4. **Vue de Changement de Discipline** ✅
```python
# Permet de :
- Changer la discipline courante
- Vérifier les permissions
- Support AJAX pour changement dynamique
```

## Actions Requises

### 1. **Associer les Disciplines aux Organisations**
C'est le plus urgent ! Les disciplines doivent être associées aux organisations appropriées :

```python
# Script pour associer les disciplines
from apps.competitions.models import Discipline
from apps.organizations.models import Organization

# Exemple : Associer Karaté à toutes les fédérations de karaté
karate = Discipline.objects.get(name="Karaté")
karate_orgs = Organization.objects.filter(
    Q(name__icontains="karate") | 
    Q(disciplines__name="Karaté")
)
karate.organization_list.add(*karate_orgs)
```

### 2. **Activer le Middleware**
Dans `settings/base.py`, ajouter :
```python
MIDDLEWARE = [
    # ... autres middlewares ...
    'apps.core.middleware.discipline_middleware.DisciplineMiddleware',
]
```

### 3. **Ajouter la Route**
Dans `urls.py` :
```python
path('discipline/change/', change_discipline, name='change_discipline'),
```

### 4. **Ajouter le Sélecteur dans les Templates**
```html
<!-- Sélecteur de discipline -->
{% if user_disciplines|length > 1 %}
<form method="post" action="{% url 'change_discipline' %}" class="discipline-selector">
    {% csrf_token %}
    <select name="discipline_id" onchange="this.form.submit()">
        {% for disc in user_disciplines %}
        <option value="{{ disc.id }}" {% if disc == current_discipline %}selected{% endif %}>
            {{ disc.name }}
        </option>
        {% endfor %}
    </select>
</form>
{% endif %}
```

## Logique de Segmentation

### Comment ça fonctionne :

1. **Organisation → Disciplines** : Chaque organisation a des disciplines associées
2. **Utilisateur → Organisation** : Via OrganizationMember
3. **Utilisateur → Disciplines** : Via son/ses organisation(s)
4. **Grades filtrés** : Seulement les grades des disciplines accessibles

### Exemple :
- Fédération de Karaté → Discipline Karaté → Grades de Karaté
- Club de Judo → Discipline Judo → Grades de Judo
- Un utilisateur du club de Judo ne voit QUE les grades de Judo

## Recommandations

### Court terme :
1. **Associer TOUTES les disciplines** aux organisations appropriées
2. **Activer le middleware** de discipline
3. **Tester** avec différents utilisateurs

### Moyen terme :
1. **Audit complet** de toutes les vues manipulant des grades
2. **Créer des tests** pour vérifier l'isolation
3. **Documentation** pour les développeurs

### Long terme :
1. **Refactoring** : Utiliser systématiquement le filtrage par discipline
2. **Manager personnalisé** pour les modèles liés aux disciplines
3. **Dashboard** pour gérer les associations discipline-organisation

## Impact

Une fois correctement implémenté :
- ✅ Isolation complète des données par discipline
- ✅ Pas de fuite d'information entre disciplines
- ✅ Interface utilisateur adaptée à la discipline courante
- ✅ Sécurité renforcée sur l'API des grades