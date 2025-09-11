# Directive de Développement : Isolation des Données par Organisation

## 📋 Contexte et Problématique

**Situation actuelle** : Les filtres dans les tableaux de bord affichent des informations provenant d'autres organisations, créant des problèmes de confidentialité et de pertinence des données.

**Exigence** : Chaque organisation doit uniquement voir les informations qui lui appartiennent ou qui lui sont explicitement partagées, même si plusieurs organisations pratiquent les mêmes disciplines.

## 🎯 Objectif de la Directive

Mettre en place un système d'isolation strict des données par organisation, garantissant que chaque entité (fédération, club, juge, pratiquant) n'accède qu'aux informations relevant de son périmètre organisationnel.

## 📝 Directive de Développement

### 1. Principe Fondamental

**RÈGLE D'OR** : Toute requête de données DOIT inclure un filtre sur l'organisation de l'utilisateur connecté, sauf cas explicite de partage inter-organisationnel approuvé.

### 2. Implémentation Technique Obligatoire

#### 2.1 Au Niveau des Modèles Django

```python
# OBLIGATOIRE : Tous les modèles principaux doivent hériter de cette classe
class OrganizationScopedModel(models.Model):
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE)
    
    class Meta:
        abstract = True
```

#### 2.2 Au Niveau des Managers Django

```python
# OBLIGATOIRE : Créer des managers personnalisés pour filtrer automatiquement
class OrganizationScopedManager(models.Manager):
    def for_organization(self, organization):
        return self.filter(organization=organization)
```

#### 2.3 Au Niveau des Vues

**INTERDICTION ABSOLUE** : Utiliser `.objects.all()` sur les modèles contenant des données organisationnelles.

**OBLIGATION** : Utiliser systématiquement :
```python
# ✅ CORRECT
objects = Model.objects.filter(organization=request.user.organization)

# ❌ INTERDIT
objects = Model.objects.all()
```

### 3. Checklist de Validation par Feature

#### Pour chaque vue/endpoint développé :

- [ ] **Vérification de l'organisation** : L'utilisateur connecté a-t-il accès à cette ressource ?
- [ ] **Filtrage automatique** : Toutes les requêtes sont-elles filtrées par organisation ?
- [ ] **Formulaires** : Les choix dans les listes déroulantes sont-ils limités à l'organisation ?
- [ ] **Recherche** : Les résultats de recherche sont-ils restreints au périmètre organisationnel ?
- [ ] **API** : Les endpoints API respectent-ils l'isolation organisationnelle ?

#### Pour chaque modèle de données :

- [ ] **Relation organisation** : Le modèle a-t-il une relation avec l'organisation (directe ou indirecte) ?
- [ ] **Manager personnalisé** : Un manager filtrant par organisation est-il implémenté ?
- [ ] **Méthodes d'accès** : Les méthodes personnalisées respectent-elles l'isolation ?

### 4. Cas Spéciaux et Exceptions

#### 4.1 Données de Référence Partagées
```python
# Exemples : Disciplines de base, grades standards
# Ces données peuvent être visibles par toutes les organisations
# MAIS doivent être clairement identifiées comme "référence"

class ReferenceDiscipline(models.Model):
    name = models.CharField(max_length=100)
    is_shared_reference = models.BooleanField(default=True)
    # Pas de relation organization pour les données de référence
```

#### 4.2 Partage Inter-Organisationnel Explicite
```python
# Pour les cas où un partage est nécessaire (compétitions inter-clubs)
class SharedResource(models.Model):
    owner_organization = models.ForeignKey('Organization', related_name='owned_resources')
    shared_with = models.ManyToManyField('Organization', related_name='shared_resources')
    
    def visible_to_organization(self, organization):
        return (self.owner_organization == organization or 
                organization in self.shared_with.all())
```

### 5. Architecture de Contrôle d'Accès

#### 5.1 Middleware de Sécurité
```python
# OBLIGATOIRE : Implémenter un middleware qui vérifie l'isolation
class OrganizationIsolationMiddleware:
    def process_view(self, request, view_func, view_args, view_kwargs):
        # Vérifier que toutes les données accédées appartiennent à l'organisation
        pass
```

#### 5.2 Décorateurs de Sécurité
```python
# OBLIGATOIRE : Utiliser des décorateurs pour protéger les vues
@require_organization_access
def my_view(request):
    # Vue automatiquement protégée
    pass
```

### 6. Tests de Non-Régression

#### 6.1 Tests Automatisés Obligatoires
```python
# OBLIGATOIRE : Chaque feature doit avoir ces tests
class OrganizationIsolationTests(TestCase):
    def test_user_cannot_see_other_organization_data(self):
        # Test que l'utilisateur A ne voit pas les données de l'organisation B
        pass
        
    def test_filters_respect_organization_boundary(self):
        # Test que les filtres ne montrent que les données de l'organisation
        pass
```

#### 6.2 Tests d'Intrusion
```python
# OBLIGATOIRE : Tests de sécurité
def test_direct_url_access_blocked(self):
    # Tenter d'accéder directement à des ressources d'autres organisations
    pass
```

### 7. Gestion des Erreurs et Logs

#### 7.1 Logging de Sécurité
```python
# OBLIGATOIRE : Logger toute tentative d'accès inter-organisationnel
import logging
security_logger = logging.getLogger('security.organization_access')

def check_organization_access(user, resource):
    if resource.organization != user.organization:
        security_logger.warning(
            f"User {user.id} attempted to access resource {resource.id} "
            f"from different organization"
        )
        raise PermissionDenied()
```

### 8. Documentation et Formation

#### 8.1 Documentation Technique
- **OBLIGATOIRE** : Documenter tous les cas d'exception au principe d'isolation
- **OBLIGATOIRE** : Maintenir une liste des modèles concernés par l'isolation
- **OBLIGATOIRE** : Documenter les API de partage inter-organisationnel

#### 8.2 Formation Équipe
- **OBLIGATOIRE** : Sensibiliser l'équipe aux enjeux de confidentialité
- **OBLIGATOIRE** : Former aux bonnes pratiques de développement sécurisé

### 9. Validation et Contrôle Qualité

#### 9.1 Code Review
**OBLIGATION** : Chaque Pull Request doit inclure une vérification de l'isolation organisationnelle par un reviewer senior.

#### 9.2 Audit Périodique
**OBLIGATION** : Audit mensuel du code pour détecter les violations du principe d'isolation.

### 10. Outils de Support

#### 10.1 Scripts de Vérification
```bash
# Script pour vérifier les violations d'isolation
grep -r "\.objects\.all()" --include="*.py" .
grep -r "\.objects\.filter(" --include="*.py" . | grep -v "organization"
```

#### 10.2 Métriques de Conformité
- Pourcentage de modèles avec isolation correcte
- Nombre de violations détectées par audit
- Temps de résolution des problèmes d'isolation

## 🚨 Sanctions et Escalade

### Niveaux de Gravité
1. **Critique** : Fuite de données entre organisations → Correction immédiate obligatoire
2. **Majeur** : Filtres incorrects dans les interfaces → Correction sous 48h
3. **Mineur** : Documentation manquante → Correction sous 1 semaine

### Processus d'Escalade
1. Détection automatique ou manuelle du problème
2. Notification immédiate au développeur responsable
3. Si pas de correction dans les délais : escalade au lead technique
4. Si problème récurrent : formation obligatoire du développeur

## 📊 Indicateurs de Succès

- **0 incident** de fuite de données inter-organisationnel
- **100%** des nouvelles features respectent l'isolation
- **< 24h** de délai de correction pour les problèmes critiques
- **100%** de couverture des tests d'isolation

## 🔧 Implémentation Pratique

### Phase 1 : Audit de l'Existant (Semaine 1-2)

1. **Inventaire des modèles** : Lister tous les modèles qui contiennent des données organisationnelles
2. **Audit des vues** : Identifier toutes les vues qui utilisent `.objects.all()` ou des filtres inadéquats
3. **Analyse des API** : Vérifier tous les endpoints pour l'isolation
4. **Cartographie des risques** : Prioriser les corrections par niveau de risque

### Phase 2 : Corrections Critiques (Semaine 3-4)

1. **Modèles critiques** : Ajouter les relations d'organisation manquantes
2. **Vues sensibles** : Corriger les filtres dans les tableaux de bord
3. **API de base** : Sécuriser les endpoints les plus utilisés
4. **Tests urgents** : Implémenter les tests de non-régression critiques

### Phase 3 : Systématisation (Semaine 5-8)

1. **Middleware** : Implémenter le middleware de sécurité
2. **Managers personnalisés** : Créer les managers pour tous les modèles
3. **Décorateurs** : Développer et déployer les décorateurs de sécurité
4. **Tests complets** : Couvrir tous les scénarios d'isolation

### Phase 4 : Monitoring et Amélioration Continue (Ongoing)

1. **Scripts de vérification** : Automatiser la détection des violations
2. **Métriques** : Mettre en place le tableau de bord de conformité
3. **Formation** : Organiser les sessions de formation équipe
4. **Documentation** : Maintenir à jour la documentation technique

## 🛠️ Outils et Ressources

### Templates de Code

#### Modèle avec Isolation
```python
from django.db import models
from django.contrib.auth.models import User

class OrganizationScopedModel(models.Model):
    """Classe abstraite pour tous les modèles avec isolation organisationnelle"""
    organization = models.ForeignKey(
        'Organization', 
        on_delete=models.CASCADE,
        verbose_name="Organisation"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class OrganizationScopedManager(models.Manager):
    """Manager pour filtrer automatiquement par organisation"""
    
    def for_organization(self, organization):
        return self.filter(organization=organization)
    
    def for_user(self, user):
        return self.filter(organization=user.organization)
```

#### Vue avec Isolation
```python
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

@login_required
def secure_list_view(request):
    """Vue exemple avec isolation organisationnelle"""
    
    # ✅ CORRECT : Filtrer par organisation de l'utilisateur
    objects = MyModel.objects.filter(organization=request.user.organization)
    
    # Ou utiliser le manager personnalisé
    objects = MyModel.objects.for_user(request.user)
    
    return render(request, 'template.html', {'objects': objects})

def check_organization_access(user, obj):
    """Fonction utilitaire pour vérifier l'accès"""
    if hasattr(obj, 'organization') and obj.organization != user.organization:
        raise PermissionDenied("Accès non autorisé à cette ressource")
```

#### API avec Isolation
```python
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated

class SecureViewSet(ModelViewSet):
    """ViewSet avec isolation organisationnelle"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # ✅ CORRECT : Filtrer par organisation
        return self.queryset.filter(organization=self.request.user.organization)
    
    def perform_create(self, serializer):
        # ✅ CORRECT : Assigner l'organisation lors de la création
        serializer.save(organization=self.request.user.organization)
```

### Scripts d'Audit

#### Script de Détection des Violations
```bash
#!/bin/bash
# audit_isolation.sh

echo "=== Audit de l'Isolation Organisationnelle ==="

echo "1. Recherche des .objects.all() dangereux :"
grep -r "\.objects\.all()" --include="*.py" . | grep -v "migrations" | grep -v "__pycache__"

echo "2. Recherche des filtres sans organisation :"
grep -r "\.objects\.filter(" --include="*.py" . | grep -v "organization" | grep -v "migrations" | head -10

echo "3. Vérification des modèles sans relation organisation :"
find . -name "*.py" -exec grep -l "class.*Model" {} \; | xargs grep -L "organization.*ForeignKey"

echo "4. Recherche des API sans filtrage :"
grep -r "class.*ViewSet" --include="*.py" . | xargs grep -L "get_queryset"
```

---

**Note importante** : Cette directive est non-négociable pour des raisons de sécurité, de confidentialité et de conformité réglementaire. Tout développement qui ne respecte pas ces principes sera rejeté en code review.

**Date d'entrée en vigueur** : Immédiatement pour tous les nouveaux développements

**Responsable** : Équipe de développement, sous supervision du Lead Technique

**Révision** : Cette directive sera révisée trimestriellement pour s'adapter aux évolutions du projet