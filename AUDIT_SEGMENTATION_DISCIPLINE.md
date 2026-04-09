# AUDIT SEGMENTATION PAR DISCIPLINE - MartialComp
## Date: 2026-01-09

---

## RESUME EXECUTIF

L'audit a identifie **8 problemes majeurs** avec **21 points d'exposition critiques**.
La segmentation par discipline existe conceptuellement mais souffre d'une **application inconsistante** et de **lacunes de securite significatives**.

### Regles de Segmentation Attendues
1. La **DISCIPLINE** est l'element premier de segmentation
2. Une Organisation ne doit voir que ses informations ET ceux lies a sa discipline
3. Les clubs affilies a la meme federation peuvent voir les elements partages
4. Des federations differentes partageant la meme discipline NE doivent PAS partager d'informations (sauf autorisation)
5. Les grades ne doivent afficher que les grades de la discipline concernee

---

## 1. ETAT ACTUEL DE LA SEGMENTATION

### 1.1 Architecture des Modeles

#### POSITIF :
- **Discipline** : Bien structuree comme entite primaire
  - Relation ForeignKey vers Organization (federation principale)
  - Relations ManyToMany depuis Organization et Practitioner
  - Liens vers grades via `Grade.discipline` (unique_together: name + discipline)

- **Grade** : Correctement segmente par discipline
  - ForeignKey obligatoire vers Discipline (unique_together: name + discipline)
  - PractitionerGrade inclut discipline_id separe
  - GradeCategory liee a Discipline

- **Organization** : ManyToMany vers Discipline
  - Permet aux federations et clubs de gerer plusieurs disciplines

- **Practitioner** : Relation multi-disciplines
  - `primary_discipline` : ForeignKey
  - `secondary_disciplines` : ManyToMany

### 1.2 Utilitaires de Filtrage Existants

**Fichier : `apps/competitions/utils/discipline_filtering.py`**
- `get_user_access_context()` : Recupere disciplines accessibles
- `filter_queryset_by_discipline_federation()` : Filtre base sur discipline + federation
- `has_access_to_object()` : Verifie acces utilisateur

**Fichier : `apps/competitions/utils/organization_discipline_filtering.py`**
- `get_organization_disciplines()` : Recupere disciplines d'une org
- `filter_by_organization_disciplines()` : Filtre queryset par disciplines org
- `filter_practitioners_by_org_disciplines()` : Filtre pratiquants
- `filter_competitions_by_org_disciplines()` : Filtre competitions

---

## 2. PROBLEMES IDENTIFIES

### PROBLEME CRITIQUE #1 : Formulaires sans filtrage discipline

**Localisation :** `apps/competitions/forms/*.py` (18+ fichiers)

**Exemple de code problematique :**
```python
# MAUVAIS - apps/competitions/forms/club.py
self.fields['disciplines'].queryset = Discipline.objects.filter(is_active=True).order_by('name')
# Retourne TOUTES les disciplines, pas seulement celles de l'organisation
```

**Impact :** Un utilisateur d'une federation Karate peut voir et selectionner des disciplines Kung Fu

**Fichiers affectes :**
- `apps/competitions/forms/club.py`
- `apps/competitions/forms/competitions.py`
- `apps/competitions/forms/federations.py`
- `apps/competitions/forms/profile_forms.py`
- `apps/competitions/forms/practitioners.py`
- `apps/competitions/forms/competition_types.py`

---

### PROBLEME CRITIQUE #2 : APIs ouvertes sans controle d'acces

**Localisation :** `apps/grades/views/core.py`

```python
# MAUVAIS - ligne 1196-1232
@require_GET
def search_grade_system(request):
    queryset = Grade.objects.filter(is_active=True)  # Pas de filtrage par org
    # Retourne TOUTES les disciplines et tous les grades

# MAUVAIS - ligne 1235-1286
@require_GET
def get_discipline_grade_structure(request, discipline_id):
    # Aucun controle d'acces par organization
    # N'importe qui avec le discipline_id peut voir tous les grades

# MAUVAIS - ligne 1404-1420
@require_GET
def categories_by_discipline(request):
    # Pas de verification si l'utilisateur a acces a cette discipline
```

**Impact :** Fuite potentielle de donnees via APIs

---

### PROBLEME CRITIQUE #3 : Vues Grade sans permission check

**Localisation :** `apps/grades/views/core.py`

```python
class GradeCreateView(LoginRequiredMixin, CreateView):
    # Seul LoginRequiredMixin!
    # Aucune verification que l'utilisateur est admin de l'org
    # Aucune verification de la discipline
```

**Impact :** Un utilisateur connecte peut creer des grades pour n'importe quelle discipline

---

### PROBLEME MAJEUR #4 : Exception sans fallback securise

**Localisation :** Multiples fichiers

```python
# MAUVAIS - apps/grades/views/core.py ligne 65-71
try:
    org = _get_request_organization(self.request)
    if org is not None and hasattr(org, 'disciplines'):
        allowed = list(org.disciplines.values_list('id', flat=True))
        if allowed:
            queryset = queryset.filter(discipline_id__in=allowed)
except Exception:
    pass  # DANGER : en cas d'erreur, aucun filtrage = acces a TOUT!
```

**Impact :** En cas d'erreur, l'utilisateur voit toutes les donnees

---

### PROBLEME MAJEUR #5 : Relations cross-organization non securisees

**Probleme :** Une Discipline peut etre associee a PLUSIEURS Organizations via M2M, mais il n'y a PAS de mecanisme pour empecher le partage involontaire de donnees.

**Risque :** Deux federations Karate independantes pourraient partager accidentellement :
- Les grades
- Les categories de grades
- Les candidats aux examens
- Les resultats de competition

---

### PROBLEME MODERE #6 : Dashboard isolation incomplete

**Localisation :** `apps/competitions/views/dashboard/*.py`

- Melange deux approches (Organization isolation mixin + Discipline filtering utils)
- Application inconsistante
- Certaines vues ne filtrent pas du tout

---

### PROBLEME MODERE #7 : Inconsistances entre modeles

```
Grade : Discipline est ForeignKey (obligatoire)
GradeCategory : Discipline est ForeignKey
Organization : disciplines (M2M)
Discipline : organization (FK nullable)

Asymetrie : Organization -> Discipline (M2M)
            Discipline -> Organization (FK)
Confusion : qui "possede" une discipline?
```

---

## 3. SCENARIOS DE COMPROMISSION

### Scenario #1 : Cross-org Grade Exposure (CRITIQUE)
1. Federation A (Karate) cree Grade "Shodan"
2. Federation B (Karate) cree la meme Discipline "Karate"
3. Utilisateur B accede a /grades/api/search?discipline=karate
4. Recoit les grades de Federation A aussi

### Scenario #2 : Unauthorized Grade Management (CRITIQUE)
1. Admin Club A (affilie a Federation Karate) cree un compte
2. Accede directement a /grades/add/
3. Pas de verification d'organisation
4. Cree des grades pour Karate (vus par tous)

### Scenario #3 : Form Discipline Bypass (HAUTE)
1. User B manipule le formulaire de creation de pratiquant
2. Change la discipline d'une autre organisation
3. Systeme ne valide pas les disciplines accessibles
4. Cree un pratiquant multi-discipline non autorise

### Scenario #4 : Exception Bypass (HAUTE)
1. Organisation isolation echoue
2. except Exception: pass -> aucun filtrage applique
3. Utilisateur voit TOUTES les donnees

---

## 4. TODOLIST DES CORRECTIONS

### PHASE 1 - CRITIQUE (2-3 jours)

#### 1.1 Securiser TOUS les formulaires
```python
# Template a appliquer a tous les formulaires
def __init__(self, *args, user=None, organization=None, **kwargs):
    super().__init__(*args, **kwargs)

    if not organization and user:
        organization = get_user_organization(user)

    if organization and hasattr(organization, 'disciplines'):
        self.fields['disciplines'].queryset = organization.disciplines.all()
        self.fields['discipline'].queryset = organization.disciplines.all()
    else:
        self.fields['disciplines'].queryset = Discipline.objects.none()
```

**Fichiers a modifier :**
- [ ] `apps/competitions/forms/club.py`
- [ ] `apps/competitions/forms/competitions.py`
- [ ] `apps/competitions/forms/federations.py`
- [ ] `apps/competitions/forms/profile_forms.py`
- [ ] `apps/competitions/forms/practitioners.py`
- [ ] `apps/competitions/forms/grades.py`
- [ ] `apps/competitions/forms/registrations.py`
- [ ] `apps/competitions/forms/onboarding.py`
- [ ] `apps/grades/forms.py`

#### 1.2 Securiser les APIs Grade
```python
# apps/grades/views/core.py
@require_GET
@login_required  # Ajouter
def search_grade_system(request):
    user_org = get_user_organization(request.user)
    if user_org:
        allowed_disciplines = user_org.disciplines.values_list('id', flat=True)
        queryset = queryset.filter(discipline_id__in=allowed_disciplines)
    else:
        queryset = queryset.none()  # Jamais de fallback a "toutes les donnees"
```

**APIs a securiser :**
- [ ] `search_grade_system`
- [ ] `get_discipline_grade_structure`
- [ ] `categories_by_discipline`
- [ ] `get_grade_requirements`
- [ ] `get_grades_for_discipline`

#### 1.3 Ajouter DisciplineAccessMixin
```python
# apps/competitions/mixins.py
class DisciplineAccessMixin(LoginRequiredMixin):
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)

        user_org = get_user_organization(self.request.user)
        if user_org:
            accessible_disciplines = user_org.disciplines.all()
            if hasattr(obj, 'discipline') and obj.discipline not in accessible_disciplines:
                raise PermissionDenied("Acces a cette discipline non autorise")

        return obj
```

**Vues a modifier :**
- [ ] `GradeListView`
- [ ] `GradeCreateView`
- [ ] `GradeUpdateView`
- [ ] `GradeDeleteView`
- [ ] `GradeCategoryListView`
- [ ] `GradeExamListView`

#### 1.4 Remplacer except pass par fallback securise
```python
# AVANT
try:
    org = _get_request_organization(self.request)
    if org:
        queryset = queryset.filter(...)
except Exception:
    pass

# APRES
try:
    org = _get_request_organization(self.request)
    if org:
        queryset = queryset.filter(...)
    else:
        queryset = queryset.none()
except Exception as e:
    logger.critical(f"Discipline isolation failed: {e}")
    queryset = queryset.none()
```

---

### PHASE 2 - HAUTE PRIORITE (4-5 jours)

#### 2.1 Creer permission_helpers.py centralise
```python
# apps/competitions/utils/permission_helpers.py

def check_discipline_access(user, discipline, organization=None):
    """Verifie si un utilisateur peut acceder a une discipline."""
    if user.is_superuser:
        return True

    if not organization:
        organization = get_user_organization(user)

    if not organization:
        return False

    return organization.disciplines.filter(id=discipline.id).exists()

def get_accessible_disciplines(user, organization=None):
    """Retourne les disciplines accessibles pour un utilisateur."""
    if user.is_superuser:
        return Discipline.objects.all()

    if not organization:
        organization = get_user_organization(user)

    if organization:
        return organization.disciplines.all()

    return Discipline.objects.none()

def filter_queryset_by_user_disciplines(queryset, user, discipline_field='discipline'):
    """Filtre un queryset par les disciplines accessibles de l'utilisateur."""
    accessible = get_accessible_disciplines(user)
    filter_kwargs = {f'{discipline_field}__in': accessible}
    return queryset.filter(**filter_kwargs)
```

#### 2.2 Clarifier relation Discipline-Organization

**Option recommandee :** Ajouter un champ `owner_organization` explicite

```python
class Discipline(models.Model):
    name = models.CharField(max_length=100)
    owner_organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='owned_disciplines',
        help_text="Organisation proprietaire de cette discipline"
    )
    # M2M pour les organisations autorisees a utiliser cette discipline
    authorized_organizations = models.ManyToManyField(
        'organizations.Organization',
        related_name='authorized_disciplines',
        blank=True
    )
```

#### 2.3 Ecrire tests d'isolation
```python
# tests/test_discipline_isolation.py
class DisciplineIsolationTests(TestCase):
    def test_cannot_see_other_discipline_grades(self):
        """Un admin Karate ne doit pas voir les grades Judo"""

    def test_cannot_create_grade_for_other_discipline(self):
        """Un admin ne peut pas creer de grade pour une discipline non autorisee"""

    def test_form_only_shows_accessible_disciplines(self):
        """Les formulaires ne montrent que les disciplines accessibles"""

    def test_api_filters_by_discipline(self):
        """Les APIs filtrent par discipline de l'organisation"""
```

---

### PHASE 3 - MAINTENANCE (1-2 jours)

#### 3.1 Ajouter audit logging
```python
class DisciplineAccessLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    action = models.CharField(choices=[('view', 'View'), ('edit', 'Edit')])
    allowed = models.BooleanField()
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
```

#### 3.2 Documenter l'architecture
Creer `docs/DISCIPLINE_SEGMENTATION.md` avec :
- Architecture des modeles
- Regles d'isolation
- Procedures de verification d'acces
- Guide pour les developpeurs

---

## 5. RESUME DES PROBLEMES

| # | Probleme | Severite | Fichiers | Correction |
|---|----------|----------|----------|-----------|
| 1 | Formulaires sans filtrage discipline | CRITIQUE | 18+ forms/*.py | Ajouter filtrage org |
| 2 | APIs ouvertes | CRITIQUE | grades/views/core.py | @login_required + filtrage |
| 3 | Vues sans permission check | CRITIQUE | 20+ vues | DisciplineAccessMixin |
| 4 | Exception sans fallback | HAUTE | 10+ fichiers | queryset.none() |
| 5 | Cross-org discipline sharing | HAUTE | models.py | Clarifier M2M/FK |
| 6 | Dashboard isolation incomplete | MOYENNE | dashboard/*.py | Application systematique |
| 7 | Pas de tests d'isolation | MOYENNE | tests/ | Ecrire tests complets |
| 8 | Pas de documentation | BASSE | docs/ | Documenter |

---

## 6. ESTIMATION DU TRAVAIL

| Phase | Duree estimee | Priorite |
|-------|---------------|----------|
| Phase 1 - Securisation immediate | 2-3 jours | CRITIQUE |
| Phase 2 - Architecture | 4-5 jours | HAUTE |
| Phase 3 - Maintenance | 1-2 jours | MOYENNE |
| **Total** | **7-10 jours** | |

---

## 7. FICHIERS CLES A MODIFIER

### CRITIQUE :
- `apps/competitions/forms/*.py` (18+ fichiers)
- `apps/grades/views/core.py` (APIs)
- `apps/grades/forms.py`

### HAUTE :
- `apps/competitions/utils/permission_helpers.py` (nouveau)
- `apps/grades/views/*.py` (tous les endpoints)
- `apps/organizations/models.py`

### MOYENNE :
- `apps/competitions/views/dashboard/*.py`
- `apps/competitions/utils/discipline_filtering.py`
- `tests/test_discipline_isolation.py` (nouveau)

---

*Audit realise le 2026-01-09*
