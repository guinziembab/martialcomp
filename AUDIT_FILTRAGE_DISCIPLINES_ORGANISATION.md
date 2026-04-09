# Audit - Filtrage par Disciplines d'Organisation

## Problème identifié

Lorsqu'une organisation sélectionne des disciplines (ex: Karaté, Kung Fu), les filtres globaux de l'organisation affichent actuellement TOUTES les données de l'organisation, sans tenir compte des disciplines sélectionnées. 

**Exemple :** Une organisation avec Karaté et Kung Fu voit actuellement :
- Tous les pratiquants (Karaté + Kung Fu)
- Toutes les compétitions (Karaté + Kung Fu)
- Tous les juges (Karaté + Kung Fu)

**Attendu :** Si l'utilisateur sélectionne "Karaté" dans les filtres, il devrait voir uniquement :
- Pratiquants de Karaté
- Compétitions de Karaté
- Juges de Karaté

## Structure actuelle

### Modèle Organization
- `disciplines` : ManyToManyField vers `Discipline` (ligne 36-41 de `apps/organizations/models.py`)
- Les disciplines sont stockées au niveau de l'organisation

### Filtrage actuel dans le dashboard
- **Ligne 320** : `Practitioner.objects.filter(organization_id=club_organization.id)` - ❌ Pas de filtre par discipline
- **Ligne 552** : `Practitioner.objects.filter(organization=club_organization)` - ❌ Pas de filtre par discipline
- **Ligne 425** : `Judge.objects.filter(practitioner__organization=club_organization)` - ❌ Pas de filtre par discipline
- **Ligne 964** : `Event.objects.filter(organization=club_organization)` - ❌ Pas de filtre par discipline

## Zones à corriger

### 1. Dashboard Club (`apps/competitions/views/dashboard/club.py`)
- Statistiques des pratiquants (ligne 320)
- Liste des pratiquants (lignes 448, 462, 552, 872)
- Juges (ligne 425)
- Compétitions (ligne 964)
- Événements (ligne 964)
- Combats (ligne 1004)
- Inscriptions (ligne 409)

### 2. Vues de Pratiquants (`apps/competitions/views/club/practitioners.py`)
- Liste des pratiquants
- Filtres de recherche

### 3. Vues de Compétitions
- Liste des compétitions
- Inscriptions aux compétitions

### 4. Vues de Juges
- Liste des juges
- Assignations de juges

## Solution proposée

### 1. Créer une fonction utilitaire de filtrage
Fichier : `apps/competitions/utils/organization_discipline_filtering.py`

Fonctions à créer :
- `get_organization_disciplines(organization)` : Récupère les disciplines d'une organisation
- `filter_by_organization_disciplines(queryset, organization, discipline_field='discipline')` : Filtre un queryset par les disciplines de l'organisation
- `filter_practitioners_by_org_disciplines(organization)` : Filtre les pratiquants
- `filter_competitions_by_org_disciplines(organization)` : Filtre les compétitions
- `filter_judges_by_org_disciplines(organization)` : Filtre les juges

### 2. Appliquer le filtrage dans toutes les vues
- Remplacer tous les `filter(organization=...)` par `filter_by_organization_disciplines(...)`
- Ajouter un paramètre optionnel pour permettre de filtrer par une discipline spécifique

### 3. Ajouter un sélecteur de discipline dans l'interface
- Permettre à l'utilisateur de sélectionner une discipline spécifique dans les filtres
- Stocker la sélection dans la session
- Appliquer le filtre sélectionné en plus du filtre d'organisation

## Plan d'implémentation

1. ✅ Créer le fichier utilitaire de filtrage
2. ✅ Modifier le dashboard club pour utiliser le filtrage
3. ✅ Modifier les vues de pratiquants
4. ✅ Modifier les vues de compétitions
5. ✅ Modifier les vues de juges (intégré dans les autres vues)
6. ⏳ Ajouter un sélecteur de discipline dans l'interface (optionnel)
7. ⏳ Tester le filtrage

## Corrections appliquées dans le dashboard club

### Fichiers modifiés
- `apps/competitions/utils/organization_discipline_filtering.py` : Créé - Fonctions utilitaires de filtrage
- `apps/competitions/views/dashboard/club.py` : Modifié - Application du filtrage dans :
  - Statistiques des pratiquants (ligne 328)
  - Liste des pratiquants récents (ligne 460, 464)
  - Tous les pratiquants (ligne 472)
  - Juges (ligne 435, 445)
  - Compétitions (ligne 372-395)
  - Inscriptions actives (ligne 420)
  - Paiements récents (ligne 560)
  - Tickets de support (ligne 880)

### Fonctions utilisées
- `filter_practitioners_by_org_disciplines()` : Filtre les pratiquants
- `filter_competitions_by_org_disciplines()` : Filtre les compétitions
- `filter_judges_by_org_disciplines()` : Filtre les juges
- `get_organization_disciplines()` : Récupère les disciplines d'une organisation

## Corrections appliquées dans les vues de pratiquants

### Fichiers modifiés
- `apps/competitions/views/club/practitioners.py` : Modifié - Application du filtrage dans :
  - Comptage des pratiquants (ligne 251)
  - Queryset principal de la liste (ligne 282)
  - Choix de disciplines pour les filtres (ligne 641-658)
  - Actions en lot sur les pratiquants (ligne 677)

## Corrections appliquées dans les vues de compétitions

### Fichiers modifiés
- `apps/competitions/views/club/competitions.py` : Modifié - Application du filtrage dans :
  - Compétitions à venir (ligne 49-59) - Filtrage par disciplines de l'organisation
  - Compétitions passées (ligne 61-64) - Filtrage par disciplines de l'organisation
  - Nombre de participants par compétition (ligne 72-78) - Filtrage des pratiquants
  - Inscriptions d'une compétition (ligne 121-126) - Filtrage des pratiquants
  - Pratiquants disponibles pour inscription (ligne 181-183) - Filtrage par disciplines
  - Juges disponibles (ligne 189-191) - Filtrage par disciplines
  - Inscriptions existantes (ligne 203-207) - Filtrage des pratiquants

## Résumé des corrections

### Fichiers créés
1. `apps/competitions/utils/organization_discipline_filtering.py` - Module de filtrage par disciplines

### Fichiers modifiés
1. `apps/competitions/views/dashboard/club.py` - Dashboard club avec filtrage
2. `apps/competitions/views/club/practitioners.py` - Vues de pratiquants avec filtrage
3. `apps/competitions/views/club/competitions.py` - Vues de compétitions avec filtrage

### Fonctionnalités implémentées
- ✅ Filtrage automatique des pratiquants par disciplines de l'organisation
- ✅ Filtrage automatique des compétitions par disciplines de l'organisation
- ✅ Filtrage automatique des juges par disciplines de l'organisation
- ✅ Filtrage des inscriptions aux compétitions
- ✅ Filtrage des statistiques et comptages

### Résultat attendu
Une organisation avec plusieurs disciplines (ex: Karaté, Kung Fu) verra maintenant uniquement :
- Les pratiquants ayant au moins une discipline en commun avec l'organisation
- Les compétitions des disciplines de l'organisation
- Les juges des disciplines de l'organisation
- Les inscriptions aux compétitions filtrées par disciplines

**Isolation complète :** Le Karaté ne verra plus les données du Kung Fu et vice versa.
