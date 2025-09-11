# Correction des Références aux Administrateurs d'Organisation

## Problème Identifié
**Erreur** : `FieldError at /competitions/events/ - Cannot resolve keyword 'admins' into field`

Le code tentait d'utiliser un champ `admins` sur le modèle `Organization` qui n'existe pas.

## Analyse de la Structure

### Modèle Organization Actuel
Le modèle `Organization` utilise un système de membres avec des rôles via le modèle `OrganizationMember` :

```python
class OrganizationMember(models.Model):
    organization = models.ForeignKey(Organization, related_name='members', ...)
    user = models.ForeignKey(User, ...)
    role = models.CharField(choices=[
        ('owner', 'Propriétaire'), 
        ('admin', 'Administrateur'), 
        ('manager', 'Gestionnaire'), 
        ('member', 'Membre'), 
        ('coach', 'Entraîneur'), 
        ('judge', 'Juge')
    ], ...)
    is_active = models.BooleanField(default=True)
```

### Champs Disponibles sur Organization
- `members` (relation vers OrganizationMember)
- `club_administrators` 
- `federation_administrators`
- Pas de champ `admins` direct

## Corrections Appliquées

### Fichiers Modifiés

**competitions/forms/event_forms.py** :
```python
# Avant (❌)
Organization.objects.filter(
    Q(admins=self.user) | Q(members=self.user)
)

# Après (✅)
Organization.objects.filter(
    members__user=self.user,
    members__is_active=True
)
```

**competitions/forms/event_import_export.py** :
- 3 occurrences corrigées avec la même logique
- Utilisation de `members__user=self.user` avec `members__is_active=True`

### Logique de Filtrage
La nouvelle approche :
1. Utilise la relation `members` du modèle Organization
2. Filtre par `members__user=self.user` pour trouver les organisations où l'utilisateur est membre
3. Ajoute `members__is_active=True` pour ne considérer que les membres actifs
4. Inclut tous les rôles (admin, manager, member, etc.) - le filtrage par rôle peut être ajouté plus tard si nécessaire

## Avantages de la Correction

✅ **Compatibilité avec la structure de données** : Utilise les vraies relations du modèle  
✅ **Flexibilité** : Inclut tous les types de membres (peut être raffiné par rôle)  
✅ **Performance** : Utilise des jointures Django efficaces  
✅ **Maintenance** : Plus facile à comprendre et maintenir  

## Résultat
🎉 **La page des événements se charge maintenant sans erreur** et les filtres d'organisation fonctionnent correctement pour les utilisateurs non-administrateurs.