# Directive de filtrage par disciplines et fédérations

## Compréhension du besoin

Notre application MartialComp doit respecter un principe fondamental : **l'étanchéité des données entre disciplines et organisations**. Chaque utilisateur ne doit voir que les informations pertinentes à son contexte disciplinaire et organisationnel.

### Principe général

Un utilisateur associé à un club pratiquant une ou plusieurs disciplines ne doit voir que :
- Les informations relatives à ces disciplines spécifiques
- Les éléments des fédérations auxquelles son club est affilié, pour ces disciplines uniquement
- Les filtres et options limités à ce périmètre d'accès

### Exemples concrets

1. **Club mono-discipline** :
   - Un club de Karaté affilié à la Fédération Française de Karaté ne voit QUE les éléments de Karaté de cette fédération
   - Il ne voit pas les compétitions/grades de Taekwondo, Judo, etc.

2. **Club multi-disciplines** :
   - Un club pratiquant Karaté et Judo voit uniquement les éléments de ces deux disciplines
   - Pour chaque discipline, il ne voit que les informations des fédérations auxquelles il est affilié pour cette discipline

3. **Administrateur de fédération** :
   - Voit uniquement les données relatives aux disciplines gérées par sa fédération
   - Ne voit pas les données des autres fédérations

## Directive technique pour les développeurs

### 1. Récupération du contexte d'accès

Pour chaque utilisateur authentifié, déterminer :
- Les disciplines auxquelles il a accès
- Pour chaque discipline, les fédérations auxquelles il est associé

```python
def get_user_access_context(user):
    """
    Récupère le contexte d'accès d'un utilisateur.
    Retourne un tuple (disciplines, discipline_federation_mapping)
    """
    if user.is_superuser:
        # Un superuser voit tout
        disciplines = Discipline.objects.all()
        mapping = {d.id: Federation.objects.all() for d in disciplines}
        return disciplines, mapping
    
    # Récupérer le(s) club(s) de l'utilisateur
    clubs = Club.objects.filter(administrators__user=user)
    
    # Initialiser les structures
    user_disciplines = set()
    discipline_federation_mapping = {}
    
    # Pour chaque club
    for club in clubs:
        # Récupérer les disciplines du club
        club_disciplines = club.disciplines.all()
        
        for discipline in club_disciplines:
            # Ajouter la discipline à l'ensemble des disciplines autorisées
            user_disciplines.add(discipline)
            
            # Récupérer la fédération associée pour ce club et cette discipline
            federation = club.federation
            
            # Ajouter au mapping
            if discipline.id not in discipline_federation_mapping:
                discipline_federation_mapping[discipline.id] = set()
            
            if federation:
                discipline_federation_mapping[discipline.id].add(federation)
    
    return list(user_disciplines), discipline_federation_mapping
```

### 2. Middleware de contexte d'accès

Créer un middleware pour rendre ce contexte disponible dans toutes les requêtes :

```python
class AccessContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            request.user_disciplines, request.discipline_federation_mapping = get_user_access_context(request.user)
        else:
            request.user_disciplines = []
            request.discipline_federation_mapping = {}
        
        response = self.get_response(request)
        return response
```

### 3. Filtrage des requêtes en base de données

Adapter toutes les vues pour appliquer le filtrage :

```python
class BaseFilteredListView(ListView):
    """Classe de base pour toutes les vues listant des éléments à filtrer par discipline/fédération"""
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Si l'utilisateur n'est pas authentifié ou est superuser, pas de filtrage
        if not self.request.user.is_authenticated or self.request.user.is_superuser:
            return queryset
        
        # Récupérer le contexte d'accès
        user_disciplines = self.request.user_disciplines
        discipline_federation_mapping = self.request.discipline_federation_mapping
        
        # Construction d'une requête complexe avec Q objects
        from django.db.models import Q
        
        # Initialiser une condition vide
        filter_condition = Q(pk=None)  # Condition toujours fausse pour initialiser
        
        # Pour chaque discipline autorisée
        for discipline in user_disciplines:
            # Récupérer les fédérations autorisées pour cette discipline
            federations = discipline_federation_mapping.get(discipline.id, [])
            
            # Ajouter la condition: (discipline=X AND federation in [Y, Z, ...])
            discipline_condition = Q(discipline=discipline) & Q(federation__in=federations)
            
            # Combiner avec OR
            filter_condition |= discipline_condition
        
        # Appliquer le filtre
        return queryset.filter(filter_condition)
```

### 4. Adaptation des formulaires

Tous les formulaires doivent être adaptés pour restreindre les choix :

```python
class BaseFilteredForm(forms.ModelForm):
    """Classe de base pour tous les formulaires avec filtrage par discipline/fédération"""
    
    def __init__(self, *args, **kwargs):
        # Récupérer l'utilisateur et le retirer des kwargs
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if not user or user.is_superuser:
            return
        
        # Récupérer le contexte d'accès
        user_disciplines, discipline_federation_mapping = get_user_access_context(user)
        
        # Restreindre les choix de disciplines
        if 'discipline' in self.fields:
            self.fields['discipline'].queryset = Discipline.objects.filter(id__in=[d.id for d in user_disciplines])
        
        # Restreindre les choix de fédérations en fonction de la discipline sélectionnée
        if 'federation' in self.fields:
            # Si on édite un objet existant, limiter aux fédérations de sa discipline
            if self.instance and self.instance.pk and hasattr(self.instance, 'discipline'):
                discipline = self.instance.discipline
                federations = discipline_federation_mapping.get(discipline.id, [])
                self.fields['federation'].queryset = Federation.objects.filter(id__in=[f.id for f in federations])
            else:
                # Sinon, vider temporairement les choix (seront remplis par JavaScript)
                self.fields['federation'].queryset = Federation.objects.none()
```

### 5. Vérification de sécurité pour les vues de détail

Ajouter une vérification de sécurité dans toutes les vues de détail :

```python
@login_required
def detail_view(request, pk):
    obj = get_object_or_404(Model, pk=pk)
    
    # Vérifier que l'utilisateur a accès à cet objet
    if not has_access_to_object(request.user, obj):
        raise PermissionDenied("Vous n'avez pas accès à cette ressource.")
    
    # Suite de la vue...

def has_access_to_object(user, obj):
    """Vérifie si un utilisateur a accès à un objet selon son contexte discipline/fédération"""
    if user.is_superuser:
        return True
    
    user_disciplines, discipline_federation_mapping = get_user_access_context(user)
    
    # Récupérer la discipline et la fédération de l'objet
    discipline = getattr(obj, 'discipline', None)
    federation = getattr(obj, 'federation', None)
    
    # Si l'objet n'a pas de discipline ou de fédération, accès autorisé
    if not discipline or not federation:
        return True
    
    # Vérifier si la discipline est dans les disciplines autorisées
    if discipline not in user_disciplines:
        return False
    
    # Vérifier si la fédération est dans les fédérations autorisées pour cette discipline
    federations = discipline_federation_mapping.get(discipline.id, [])
    return federation in federations
```

### 6. Adaptation des templates

Tous les templates doivent être adaptés pour n'afficher que les éléments pertinents :

```html
<!-- Filtres de formulaire -->
<select name="discipline" id="discipline-filter">
    <option value="">Toutes les disciplines</option>
    {% for discipline in user_disciplines %}
        <option value="{{ discipline.id }}">{{ discipline.name }}</option>
    {% endfor %}
</select>

<!-- JavaScript pour le filtrage dynamique des fédérations -->
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Mapping des disciplines aux fédérations (fourni par le backend)
    const disciplineFederationMapping = {{ discipline_federation_mapping|safe }};
    
    const disciplineFilter = document.getElementById('discipline-filter');
    const federationFilter = document.getElementById('federation-filter');
    
    // Mettre à jour les fédérations disponibles quand la discipline change
    disciplineFilter.addEventListener('change', function() {
        const selectedDisciplineId = this.value;
        
        // Vider les options actuelles
        federationFilter.innerHTML = '<option value="">Toutes les fédérations</option>';
        
        // Si une discipline est sélectionnée
        if (selectedDisciplineId) {
            // Ajouter les fédérations associées
            const federations = disciplineFederationMapping[selectedDisciplineId] || [];
            
            federations.forEach(function(federation) {
                const option = document.createElement('option');
                option.value = federation.id;
                option.textContent = federation.name;
                federationFilter.appendChild(option);
            });
        }
    });
});
</script>
```

### 7. Tests automatisés

Créer des tests automatisés pour vérifier que le filtrage fonctionne correctement :

```python
def test_discipline_federation_filtering():
    """Teste que le filtrage par discipline/fédération fonctionne correctement"""
    
    # Créer des disciplines
    karate = Discipline.objects.create(name="Karaté")
    judo = Discipline.objects.create(name="Judo")
    taekwondo = Discipline.objects.create(name="Taekwondo")
    
    # Créer des fédérations
    ffk = Federation.objects.create(name="Fédération Française de Karaté")
    ffjda = Federation.objects.create(name="Fédération Française de Judo")
    
    # Créer un club multi-disciplines
    club = Club.objects.create(name="Dojo Central", federation=None)
    club.disciplines.add(karate, judo)
    
    # Créer des affiliations
    ClubFederationAffiliation.objects.create(club=club, federation=ffk, discipline=karate)
    ClubFederationAffiliation.objects.create(club=club, federation=ffjda, discipline=judo)
    
    # Créer un utilisateur
    user = User.objects.create_user(username="club_admin", password="password")
    ClubAdministrator.objects.create(user=user, club=club, role="admin")
    
    # Créer des compétitions
    comp_karate_ffk = Competition.objects.create(name="Compétition Karaté FFK", discipline=karate, federation=ffk)
    comp_judo_ffjda = Competition.objects.create(name="Compétition Judo FFJDA", discipline=judo, federation=ffjda)
    comp_taekwondo = Competition.objects.create(name="Compétition Taekwondo", discipline=taekwondo, federation=None)
    
    # Tester l'accès
    client = Client()
    client.login(username="club_admin", password="password")
    
    # L'utilisateur devrait voir la compétition de Karaté
    response = client.get(f"/competitions/{comp_karate_ffk.id}/")
    assert response.status_code == 200
    
    # L'utilisateur devrait voir la compétition de Judo
    response = client.get(f"/competitions/{comp_judo_ffjda.id}/")
    assert response.status_code == 200
    
    # L'utilisateur ne devrait PAS voir la compétition de Taekwondo
    response = client.get(f"/competitions/{comp_taekwondo.id}/")
    assert response.status_code == 403
```

## Implémentation dans les modules existants

### Compétitions

- Filtrer la liste des compétitions par discipline/fédération
- Restreindre les catégories disponibles
- Limiter les inscriptions aux compétitions accessibles

### Grades

- Filtrer les systèmes de grades par discipline/fédération
- Restreindre l'attribution des grades aux disciplines du club

### Pratiquants

- Afficher uniquement les pratiquants des disciplines du club
- Restreindre l'inscription aux compétitions selon les disciplines

### Fédérations

- Un club ne doit voir que les fédérations auxquelles il est affilié
- Pour chaque fédération, ne montrer que le contenu relatif aux disciplines du club

## Timeline d'implémentation

1. **Semaine 1** : Mise en place du middleware et des fonctions utilitaires
2. **Semaine 2** : Adaptation des vues principales (compétitions, grades)
3. **Semaine 3** : Adaptation des formulaires et vérifications de sécurité
4. **Semaine 4** : Tests et correction des bugs

## Contrôle qualité

Vérifier systématiquement pour chaque fonctionnalité :

1. Un club mono-discipline ne voit que ses disciplines
2. Un club multi-disciplines ne voit que ses disciplines
3. Un club voit uniquement le contenu des fédérations auxquelles il est affilié
4. Les filtres et options dans l'interface sont correctement limités
5. Les tentatives d'accès direct à des ressources non autorisées sont bloquées

## Conclusion

Cette directive établit le principe fondamental d'étanchéité des données entre disciplines et organisations dans notre application MartialComp. Son implémentation rigoureuse garantira que chaque utilisateur ne verra que les informations pertinentes à son contexte disciplinaire et organisationnel, tout en maintenant un code propre et maintenable.
