# Guide des Modules Optionnels MartialComp

## Introduction

MartialComp est conçu avec une architecture modulaire permettant d'activer ou désactiver certaines fonctionnalités selon les besoins. Ce document explique comment gérer correctement les modules optionnels pour assurer la stabilité de l'application, même lorsque certains modules ne sont pas disponibles.

## Modules Principaux et Optionnels

### Modules principaux (toujours requis)

| Module | Description | Statut |
|--------|-------------|--------|
| `competitions` | Module principal de gestion des compétitions | Obligatoire |
| `multitenant` | Gestion de l'architecture multi-tenant | Obligatoire |
| `permissions_manager` | Gestion des rôles et permissions | Obligatoire |

### Modules optionnels

| Module | Description | Dépendances |
|--------|-------------|-------------|
| `grades` | Système de grades d'arts martiaux | `competitions` |
| `finances` | Paiements, factures, transactions | `competitions` |
| `shop` | Boutique en ligne | `competitions`, `finances` |
| `organizations` | Structure organisationnelle | `competitions` |
| `family_management` | Gestion des familles et des relations | `competitions` |

## Gestion des Dépendances de Modules

### 1. Imports Conditionnels

La technique principale pour gérer les modules optionnels est l'utilisation d'imports conditionnels :

```python
# Au niveau du module
try:
    from grades.models import Grade, GradeCategory
    HAS_GRADES_MODULE = True
except ImportError:
    HAS_GRADES_MODULE = False
    # Classes fantômes pour éviter les erreurs
    class Grade:
        """Classe fantôme pour le module grades non disponible."""
        pass
    class GradeCategory:
        """Classe fantôme pour le module grades non disponible."""
        pass

# Dans les fonctions ou méthodes
def get_practitioner_grades(practitioner_id):
    if HAS_GRADES_MODULE:
        from grades.models import PractitionerGrade
        return PractitionerGrade.objects.filter(practitioner_id=practitioner_id)
    else:
        return []  # Retourner une liste vide si le module n'est pas disponible
```

### 2. Modèles avec Dépendances Conditionnelles

Pour les modèles qui ont des relations avec des modèles dans des modules optionnels :

```python
# Dans competitions/models/practitioners.py
from django.db import models
from django.conf import settings

class Practitioner(models.Model):
    """Modèle représentant un pratiquant d'arts martiaux."""
    name = models.CharField(max_length=100)
    # Champs communs...
    
    # Champ conditionnel lié au module grades
    if 'grades' in settings.INSTALLED_APPS:
        current_grade = models.ForeignKey(
            'grades.Grade',
            on_delete=models.SET_NULL,
            null=True,
            blank=True,
            related_name='practitioners'
        )
    else:
        # Champ alternatif quand le module grades n'est pas disponible
        current_grade_name = models.CharField(
            max_length=100,
            blank=True,
            help_text="Nom du grade actuel (module grades non installé)"
        )
    
    def get_current_grade(self):
        """Méthode pour récupérer le grade actuel, indépendamment de la disponibilité du module."""
        if 'grades' in settings.INSTALLED_APPS:
            return self.current_grade
        else:
            return self.current_grade_name
```

### 3. Vues Adaptatives

Les vues doivent être conçues pour s'adapter à la présence ou l'absence de modules optionnels :

```python
# Dans competitions/views/dashboard/participant.py
from django.shortcuts import render
from django.conf import settings

def participant_dashboard(request, participant_id):
    """Tableau de bord du participant."""
    context = {
        'participant': get_object_or_404(Participant, id=participant_id),
        # Données de base...
    }
    
    # Ajouter des données conditionnelles selon les modules disponibles
    if 'grades' in settings.INSTALLED_APPS:
        from grades.models import PractitionerGrade
        context['grades_history'] = PractitionerGrade.objects.filter(
            practitioner=context['participant'].practitioner
        ).order_by('-date_obtained')
        context['has_grades_module'] = True
    else:
        context['has_grades_module'] = False
    
    if 'finances' in settings.INSTALLED_APPS:
        from finances.models import Transaction
        context['recent_transactions'] = Transaction.objects.filter(
            practitioner=context['participant'].practitioner
        ).order_by('-date')[:5]
        context['has_finances_module'] = True
    else:
        context['has_finances_module'] = False
    
    return render(request, 'competitions/dashboard/participant.html', context)
```

### 4. Templates Conditionnels

Les templates doivent également être adaptés pour gérer l'absence de modules :

```django
{# Dans competitions/templates/competitions/dashboard/participant.html #}
<div class="dashboard-container">
    <h1>{{ participant.name }}</h1>
    
    {# Section toujours présente #}
    <div class="profile-section">
        <h2>Profil</h2>
        {# Contenu du profil #}
    </div>
    
    {# Section conditionnelle pour les grades #}
    {% if has_grades_module %}
        <div class="grades-section">
            <h2>Historique des Grades</h2>
            {% if grades_history %}
                <ul class="grades-list">
                    {% for grade in grades_history %}
                        <li>
                            <span class="grade-name">{{ grade.grade.name }}</span>
                            <span class="grade-date">{{ grade.date_obtained|date:"d/m/Y" }}</span>
                        </li>
                    {% endfor %}
                </ul>
            {% else %}
                <p>Aucun grade enregistré.</p>
            {% endif %}
        </div>
    {% endif %}
    
    {# Section conditionnelle pour les finances #}
    {% if has_finances_module %}
        <div class="finances-section">
            <h2>Transactions Récentes</h2>
            {% if recent_transactions %}
                <ul class="transactions-list">
                    {% for transaction in recent_transactions %}
                        <li>
                            <span class="transaction-date">{{ transaction.date|date:"d/m/Y" }}</span>
                            <span class="transaction-amount">{{ transaction.amount }} €</span>
                            <span class="transaction-description">{{ transaction.description }}</span>
                        </li>
                    {% endfor %}
                </ul>
                <a href="{% url 'finances:transactions' participant.id %}" class="btn btn-primary">
                    Voir toutes les transactions
                </a>
            {% else %}
                <p>Aucune transaction récente.</p>
            {% endif %}
        </div>
    {% endif %}
</div>
```

### 5. Gestion des URLs Conditionnelles

Pour éviter les erreurs `NoReverseMatch`, les URLs doivent être gérées conditionnellement :

```python
# Dans config/urls.py
from django.conf import settings
from django.urls import path, include

urlpatterns = [
    # URLs de base
    path('admin/', admin.site.urls),
    path('', include('competitions.urls')),
    
    # URLs conditionnelles
]

# Ajouter les URLs des modules optionnels s'ils sont disponibles
if 'grades' in settings.INSTALLED_APPS:
    urlpatterns.append(path('grades/', include('grades.urls', namespace='grades')))

if 'finances' in settings.INSTALLED_APPS:
    urlpatterns.append(path('finances/', include('finances.urls', namespace='finances')))

if 'shop' in settings.INSTALLED_APPS:
    urlpatterns.append(path('shop/', include('shop.urls', namespace='shop')))
```

### 6. Utilitaires pour la Gestion des Modules

Créez un module d'utilitaires pour centraliser la logique de détection des modules :

```python
# Dans competitions/utils/modules.py
from django.conf import settings

def has_module(module_name):
    """Vérifie si un module optionnel est disponible."""
    return module_name in settings.INSTALLED_APPS

def get_module_url(module_name, view_name, *args, **kwargs):
    """Récupère une URL de module de façon sécurisée."""
    from django.urls import reverse, NoReverseMatch
    
    if not has_module(module_name):
        return None
    
    try:
        return reverse(f"{module_name}:{view_name}", args=args, kwargs=kwargs)
    except NoReverseMatch:
        return None

def get_module_model(module_name, model_name):
    """Récupère un modèle d'un module optionnel de façon sécurisée."""
    if not has_module(module_name):
        return None
    
    try:
        from django.apps import apps
        return apps.get_model(module_name, model_name)
    except (LookupError, ImportError):
        return None
```

## Configuration des Modules dans les Paramètres

### 1. Ajout Conditionnel des Applications

```python
# Dans config/settings/base.py
INSTALLED_APPS = [
    # Applications Django de base
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Applications tierces
    'rest_framework',
    'crispy_forms',
    
    # Applications MartialComp principales
    'competitions',
    'multitenant',
    'permissions_manager',
]

# Applications optionnelles
OPTIONAL_APPS = {
    'grades': {
        'enabled': True,  # Activer/désactiver le module
        'requires': [],   # Dépendances
    },
    'finances': {
        'enabled': True,
        'requires': [],
    },
    'shop': {
        'enabled': True,
        'requires': ['finances'],
    },
    'organizations': {
        'enabled': True,
        'requires': [],
    },
    'family_management': {
        'enabled': False,  # Module désactivé
        'requires': [],
    },
}

# Ajouter les applications optionnelles activées et leurs dépendances
for app, config in OPTIONAL_APPS.items():
    if config['enabled']:
        # Vérifier que toutes les dépendances sont activées
        dependencies_met = all(OPTIONAL_APPS.get(dep, {}).get('enabled', False) 
                              for dep in config['requires'])
        
        if dependencies_met:
            INSTALLED_APPS.append(app)
        else:
            print(f"Warning: Le module '{app}' ne peut pas être activé car ses dépendances ne sont pas satisfaites.")
```

### 2. Configuration Spécifique aux Modules

```python
# Dans config/settings/base.py
# Après avoir configuré INSTALLED_APPS

# Configuration spécifique au module grades (si activé)
if 'grades' in INSTALLED_APPS:
    GRADE_SYSTEM_TYPES = [
        ('belt', 'Système de ceintures'),
        ('dan', 'Système Dan/Kyu'),
        ('level', 'Système par niveau'),
    ]

# Configuration spécifique au module finances (si activé)
if 'finances' in INSTALLED_APPS:
    PAYMENT_PROVIDERS = [
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
    ]
    DEFAULT_PAYMENT_PROVIDER = 'stripe'

# Configuration spécifique au module shop (si activé)
if 'shop' in INSTALLED_APPS:
    SHOP_CURRENCY = 'EUR'
    SHOP_TAX_RATE = 0.20  # 20% TVA
```

## Migrations et Base de Données

### 1. Migrations Conditionnelles

Pour les modèles ayant des champs conditionnels, les migrations doivent être gérées avec soin :

```python
# Dans competitions/migrations/XXXX_conditional_fields.py
from django.db import migrations, models
import django.db.models.deletion

def check_grades_app(apps, schema_editor):
    """Vérifie si l'application grades est installée."""
    return 'grades' in schema_editor.connection.settings_dict.get('INSTALLED_APPS', [])

class Migration(migrations.Migration):
    dependencies = [
        ('competitions', 'XXXX_previous_migration'),
    ]

    operations = []

    # Ajouter des opérations conditionnelles
    grades_operations = [
        migrations.AddField(
            model_name='practitioner',
            name='current_grade',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='practitioners',
                to='grades.grade'
            ),
        ),
    ]

    # Vérifier si le module grades est disponible
    try:
        import grades
        operations.extend(grades_operations)
    except ImportError:
        # Ajouter un champ alternatif si le module grades n'est pas disponible
        operations.append(
            migrations.AddField(
                model_name='practitioner',
                name='current_grade_name',
                field=models.CharField(
                    blank=True,
                    max_length=100,
                    help_text="Nom du grade actuel (module grades non installé)"
                ),
            )
        )
```

### 2. RunPython Sécurisés

Pour les migrations RunPython qui dépendent de modules optionnels :

```python
# Dans competitions/migrations/XXXX_data_migration.py
from django.db import migrations

def update_practitioner_grades(apps, schema_editor):
    """Met à jour les grades des praticiens si le module grades est disponible."""
    try:
        Practitioner = apps.get_model('competitions', 'Practitioner')
        Grade = apps.get_model('grades', 'Grade')
        
        # Logique de migration...
    except LookupError:
        # Le module grades n'est pas disponible, ne rien faire
        pass

def reverse_func(apps, schema_editor):
    """Fonction de réversion qui gère l'absence du module grades."""
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('competitions', 'XXXX_previous_migration'),
    ]

    operations = [
        migrations.RunPython(update_practitioner_grades, reverse_func),
    ]
```

## Interface Utilisateur Adaptative

### 1. Menus Conditionnels

```django
{# Dans templates/base.html #}
<nav class="sidebar">
    <ul class="nav-menu">
        <li><a href="{% url 'dashboard' %}">Tableau de bord</a></li>
        <li><a href="{% url 'competitions:list' %}">Compétitions</a></li>
        <li><a href="{% url 'practitioners:list' %}">Pratiquants</a></li>
        
        {% if 'grades' in INSTALLED_APPS %}
            <li><a href="{% url 'grades:list' %}">Grades</a></li>
        {% endif %}
        
        {% if 'finances' in INSTALLED_APPS %}
            <li><a href="{% url 'finances:dashboard' %}">Finances</a></li>
        {% endif %}
        
        {% if 'shop' in INSTALLED_APPS %}
            <li><a href="{% url 'shop:dashboard' %}">Boutique</a></li>
        {% endif %}
        
        <li><a href="{% url 'settings' %}">Paramètres</a></li>
    </ul>
</nav>
```

### 2. Tags de Template Personnalisés

```python
# Dans competitions/templatetags/module_tags.py
from django import template
from django.conf import settings
from django.urls import reverse, NoReverseMatch

register = template.Library()

@register.simple_tag
def has_module(module_name):
    """Vérifie si un module est disponible."""
    return module_name in settings.INSTALLED_APPS

@register.simple_tag
def module_url(module_name, view_name, *args, **kwargs):
    """Génère une URL si le module est disponible."""
    if module_name not in settings.INSTALLED_APPS:
        return '#'
    
    try:
        return reverse(f"{module_name}:{view_name}", args=args, kwargs=kwargs)
    except NoReverseMatch:
        return '#'

@register.filter
def module_enabled(module_name):
    """Filtre pour vérifier si un module est activé."""
    return module_name in settings.INSTALLED_APPS
```

Utilisation dans les templates :

```django
{% load module_tags %}

{% if 'grades'|module_enabled %}
    <a href="{% module_url 'grades' 'list' %}">Grades</a>
{% endif %}

{% if has_module 'finances' %}
    <div class="finances-widget">
        {# Contenu du widget finances #}
    </div>
{% endif %}
```

## Tests avec Modules Optionnels

### 1. Tests Conditionnels

```python
# Dans competitions/tests/test_practitioners.py
import unittest
from django.test import TestCase
from django.conf import settings

class PractitionerTestCase(TestCase):
    """Tests pour le modèle Practitioner."""
    
    def test_practitioner_creation(self):
        """Test de création d'un praticien."""
        from competitions.models import Practitioner
        
        practitioner = Practitioner.objects.create(
            name="John Doe",
            email="john@example.com",
        )
        
        self.assertEqual(practitioner.name, "John Doe")
    
    @unittest.skipIf('grades' not in settings.INSTALLED_APPS, "Module grades non disponible")
    def test_practitioner_grade_assignment(self):
        """Test d'attribution d'un grade à un praticien."""
        from competitions.models import Practitioner
        from grades.models import Grade, PractitionerGrade
        
        practitioner = Practitioner.objects.create(name="John Doe")
        grade = Grade.objects.create(name="Ceinture Noire", level=10)
        
        PractitionerGrade.objects.create(
            practitioner=practitioner,
            grade=grade,
            date_obtained="2025-01-01"
        )
        
        self.assertEqual(practitioner.current_grade, grade)
```

### 2. Tests avec Mock Modules

```python
# Dans competitions/tests/test_with_mocks.py
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.test.utils import override_settings

class DashboardTestWithMockModules(TestCase):
    """Tests pour le dashboard avec modules mockés."""
    
    @override_settings(INSTALLED_APPS=['django.contrib.auth', 'competitions'])
    @patch('competitions.views.dashboard.participant.settings')
    def test_dashboard_without_optional_modules(self, mock_settings):
        """Test du dashboard sans modules optionnels."""
        # Configurer le mock pour simuler l'absence de modules
        mock_settings.INSTALLED_APPS = ['django.contrib.auth', 'competitions']
        
        # Créer un utilisateur et un participant pour le test
        # ...
        
        # Accéder au dashboard
        response = self.client.get('/dashboard/participant/1/')
        
        # Vérifier que la réponse est OK
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que les sections des modules optionnels ne sont pas présentes
        self.assertNotContains(response, 'Historique des Grades')
        self.assertNotContains(response, 'Transactions Récentes')
    
    @override_settings(INSTALLED_APPS=['django.contrib.auth', 'competitions', 'grades'])
    @patch('competitions.views.dashboard.participant.settings')
    @patch('competitions.views.dashboard.participant.PractitionerGrade')
    def test_dashboard_with_grades_module(self, mock_practitioner_grade, mock_settings):
        """Test du dashboard avec le module grades activé."""
        # Configurer le mock pour simuler la présence du module grades
        mock_settings.INSTALLED_APPS = ['django.contrib.auth', 'competitions', 'grades']
        
        # Configurer le mock pour PractitionerGrade
        mock_grade = MagicMock()
        mock_grade.name = "Ceinture Noire"
        
        mock_practitioner_grade_instance = MagicMock()
        mock_practitioner_grade_instance.grade = mock_grade
        mock_practitioner_grade_instance.date_obtained = "2025-01-01"
        
        mock_practitioner_grade.objects.filter.return_value.order_by.return_value = [
            mock_practitioner_grade_instance
        ]
        
        # Créer un utilisateur et un participant pour le test
        # ...
        
        # Accéder au dashboard
        response = self.client.get('/dashboard/participant/1/')
        
        # Vérifier que la réponse est OK
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que la section des grades est présente
        self.assertContains(response, 'Historique des Grades')
        self.assertContains(response, 'Ceinture Noire')
```

## Conclusion

En suivant les principes décrits dans ce guide, vous pouvez développer et maintenir une application MartialComp robuste qui s'adapte à la présence ou l'absence de modules optionnels. Cette approche modulaire offre une grande flexibilité tout en garantissant la stabilité de l'application.

Points clés à retenir :

1. **Imports conditionnels** : Utilisez try/except pour gérer l'absence de modules
2. **Modèles adaptables** : Concevez des modèles qui peuvent fonctionner avec ou sans relations externes
3. **Vues flexibles** : Ajustez le comportement des vues selon les modules disponibles
4. **Templates intelligents** : Utilisez des conditionnels pour adapter l'interface utilisateur
5. **Configuration centralisée** : Gérez l'activation des modules via les paramètres Django
6. **Tests adaptés** : Créez des tests qui prennent en compte la présence ou l'absence de modules

En suivant ces pratiques, vous minimiserez les erreurs liées aux modules manquants et offrirez une expérience utilisateur cohérente, même avec différentes configurations de modules.
