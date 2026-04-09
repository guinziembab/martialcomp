# DOCUMENTATION : judge_dashboard.html

**Dashboard principal des juges pour la notation technique**

---

## 📋 INFORMATIONS GÉNÉRALES

- **Nom du template :** `judge_dashboard.html`
- **Localisation :** `apps/competitions/templates/competitions/technical_scoring/judge_dashboard.html`
- **Type :** Dashboard pour juges
- **Priorité :** 🔴 Haute
- **Usage :** Point d'entrée principal pour les juges - Vue d'ensemble de leurs compétitions assignées

---

## 🔗 URL ASSOCIÉE

**Pattern URL :** `/technical-scoring/judge/dashboard/`

**Vue Django :** `apps/competitions/views/technical_scoring.py::judge_dashboard`

**Nom de l'URL :** `competitions:technical_scoring:judge_dashboard`

---

## 📦 CONTEXTE REQUIS

### Variables obligatoires

| Variable | Type | Description |
|----------|------|-------------|
| `user` | `User` | Utilisateur juge connecté |
| `assigned_competitions` | `List[Competition]` | Liste des compétitions assignées au juge |
| `pending_scores` | `List[Dict]` | Liste des scores en attente de notation |
| `completed_scores` | `List[Dict]` | Liste des scores récemment notés |
| `stats` | `Dict` | Statistiques du juge |

### Structure de `stats`

```python
stats = {
    'total_competitions': int,          # Nombre de compétitions assignées
    'pending_matches': int,             # Nombre de matchs en attente
    'completed_matches': int,            # Nombre de matchs notés
    'average_score_time': str,          # Temps moyen (ex: "5 min")
}
```

### Structure de `assigned_competitions`

Chaque compétition doit avoir :
- `id` : ID de la compétition
- `name` : Nom de la compétition
- `discipline.name` : Nom de la discipline
- `date` : Date de la compétition
- `status` : Statut de la compétition
- `status_color` : Couleur pour le badge de statut
- `get_status_display()` : Texte du statut

---

## 🎨 STRUCTURE DU TEMPLATE

### 1. Navigation latérale (Sidebar)

```html
{% block sidebar_nav %}
    <!-- Tableau de bord -->
    <a href="{% url 'competitions:technical_scoring:judge_dashboard' %}">
        Tableau de bord
    </a>
    
    <!-- Historique -->
    <a href="{% url 'competitions:technical_scoring:scoring_history' %}">
        Historique
    </a>
    
    <!-- Catégories -->
    <a href="{% url 'competitions:technical_scoring:categories' %}">
        Catégories
    </a>
    
    <!-- Mon profil -->
    <a href="/profile/">
        Mon profil
    </a>
{% endblock %}
```

### 2. Statistiques du juge

```html
{% block dashboard_stats %}
    <!-- Compétitions assignées -->
    <div class="stat-card">
        <i class="fas fa-trophy"></i>
        <div class="stat-number">{{ stats.total_competitions }}</div>
        <div class="stat-label">Compétitions assignées</div>
    </div>
    
    <!-- Matchs en attente -->
    <div class="stat-card">
        <i class="fas fa-clock"></i>
        <div class="stat-number">{{ stats.pending_matches }}</div>
        <div class="stat-label">Matchs en attente</div>
    </div>
    
    <!-- Matchs notés -->
    <div class="stat-card">
        <i class="fas fa-check-circle"></i>
        <div class="stat-number">{{ stats.completed_matches }}</div>
        <div class="stat-label">Matchs notés</div>
    </div>
    
    <!-- Temps moyen -->
    <div class="stat-card">
        <i class="fas fa-stopwatch"></i>
        <div class="stat-number">{{ stats.average_score_time }}</div>
        <div class="stat-label">Temps moyen</div>
    </div>
{% endblock %}
```

### 3. Liste des compétitions assignées

```html
<div class="table-responsive">
    <table class="table">
        <thead>
            <tr>
                <th>Compétition</th>
                <th>Date</th>
                <th>Statut</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for competition in assigned_competitions %}
            <tr>
                <td>
                    <strong>{{ competition.name }}</strong>
                    <br>
                    <small>{{ competition.discipline.name }}</small>
                </td>
                <td>{{ competition.date|date:"d/m/Y H:i" }}</td>
                <td>
                    <span class="badge bg-{{ competition.status_color }}">
                        {{ competition.get_status_display }}
                    </span>
                </td>
                <td>
                    <a href="{% url 'competitions:technical_scoring:scoring_interface' competition.id %}">
                        Noter
                    </a>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
```

### 4. Actions rapides

```html
<div class="d-grid gap-2">
    <!-- Voir l'historique -->
    <a href="{% url 'competitions:technical_scoring:scoring_history' %}">
        <i class="fas fa-history"></i>
        Voir l'historique
    </a>
    
    <!-- Gérer les catégories -->
    <a href="{% url 'competitions:technical_scoring:categories' %}">
        <i class="fas fa-tags"></i>
        Gérer les catégories
    </a>
</div>
```

### 5. Aide contextuelle

```html
<div class="mt-4 p-3 bg-light rounded">
    <h6>
        <i class="fas fa-info-circle"></i>
        Aide
    </h6>
    <ul class="list-unstyled mb-0 small">
        <li>
            <i class="fas fa-check text-success"></i>
            Cliquez sur 'Noter' pour accéder à l'interface de notation
        </li>
        <li>
            <i class="fas fa-check text-success"></i>
            Consultez l'historique pour revoir vos évaluations
        </li>
        <li>
            <i class="fas fa-check text-success"></i>
            Utilisez les catégories pour organiser vos notations
        </li>
    </ul>
</div>
```

### 6. Activité récente

```html
<!-- Scores en attente -->
{% if pending_scores %}
<div class="col-md-6">
    <h6 class="text-warning">
        <i class="fas fa-clock"></i>
        En attente de notation
    </h6>
    <div class="list-group">
        {% for score in pending_scores %}
        <div class="list-group-item">
            <strong>{{ score.participant.name }}</strong>
            <br>
            <small>{{ score.competition.name }}</small>
            <a href="{% url 'competitions:technical_scoring:scoring_interface' score.competition.id %}">
                Noter
            </a>
        </div>
        {% endfor %}
    </div>
</div>
{% endif %}

<!-- Scores récemment notés -->
{% if completed_scores %}
<div class="col-md-6">
    <h6 class="text-success">
        <i class="fas fa-check-circle"></i>
        Récemment notés
    </h6>
    <div class="list-group">
        {% for score in completed_scores %}
        <div class="list-group-item">
            <strong>{{ score.participant.name }}</strong>
            <br>
            <small>{{ score.competition.name }}</small>
            <span class="badge bg-success">{{ score.total_score }}/10</span>
        </div>
        {% endfor %}
    </div>
</div>
{% endif %}
```

---

## 🎯 FONCTIONNALITÉS

### ✅ Fonctionnalités implémentées

1. **Vue d'ensemble** : Tableau de bord avec statistiques
2. **Liste compétitions** : Affichage de toutes les compétitions assignées
3. **Navigation rapide** : Liens directs vers les interfaces de notation
4. **Actions rapides** : Accès rapide à l'historique et aux catégories
5. **Activité récente** : Affichage des scores en attente et complétés
6. **Aide contextuelle** : Guide d'utilisation intégré
7. **Responsive** : Design adapté mobile et desktop

### ⚠️ Limitations identifiées

1. Données mockées dans la vue actuelle (TODO)
2. Pas de filtres sur les compétitions
3. Pas de recherche de compétitions
4. Pas de tri personnalisable
5. Pas de notifications visuelles pour nouvelles assignations

---

## 📝 EXEMPLE D'UTILISATION

### Dans la vue Django

```python
from apps.competitions.views.technical_scoring import judge_dashboard
from django.shortcuts import render

@login_required
def judge_dashboard(request):
    user = request.user
    
    # TODO: Implémenter la récupération réelle des compétitions assignées
    assigned_competitions = []  # À remplacer par la vraie requête
    
    # TODO: Implémenter la récupération des scores
    pending_scores = []  # Scores en attente
    completed_scores = []  # Scores terminés
    
    # Statistiques
    stats = {
        'total_competitions': len(assigned_competitions),
        'pending_matches': len(pending_scores),
        'completed_matches': len(completed_scores),
        'average_score_time': '0 min',  # À calculer
    }
    
    context = {
        'user': user,
        'assigned_competitions': assigned_competitions,
        'pending_scores': pending_scores,
        'completed_scores': completed_scores,
        'stats': stats,
    }
    
    return render(request, 'competitions/technical_scoring/judge_dashboard.html', context)
```

---

## 🔗 DÉPENDANCES

### Templates étendus

- `competitions/dashboard/unified_base.html` : Template de base unifié

### Tags Django requis

- `{% load i18n %}` : Internationalisation
- `{% load static %}` : Fichiers statiques

### CSS

- Bootstrap 5 (classes utilisées : `table`, `btn`, `badge`, `card`, etc.)
- Font Awesome (icônes : `fas fa-trophy`, `fas fa-clock`, `fas fa-check-circle`, etc.)

### JavaScript

- Aucun JavaScript spécifique requis

---

## ✅ TESTS RECOMMANDÉS

### Tests unitaires

1. **Rendu du template** : Vérifier l'affichage correct
2. **Statistiques** : Vérifier l'affichage des stats
3. **Liste compétitions** : Vérifier l'affichage de la liste
4. **Actions rapides** : Vérifier les liens
5. **Activité récente** : Vérifier l'affichage des scores

### Tests d'intégration

1. **Navigation** : Tester les liens vers autres pages
2. **Connexion juge** : Vérifier l'accès avec compte juge
3. **Données manquantes** : Tester avec données vides

---

## 📌 NOTES IMPORTANTES

1. **Données mockées** : La vue actuelle utilise des données mockées - À implémenter
2. **Isolation** : Vérifier l'isolation organisationnelle des compétitions
3. **Permissions** : Vérifier que seul un juge peut accéder
4. **Performance** : Optimiser les requêtes pour les compétitions assignées

---

## 🔄 AMÉLIORATIONS POSSIBLES

1. **Notifications** : Ajouter des notifications visuelles pour nouvelles assignations
2. **Filtres** : Ajouter filtres par statut, date, discipline
3. **Recherche** : Ajouter recherche de compétitions
4. **Tri** : Permettre tri personnalisable
5. **Graphiques** : Ajouter graphiques de progression
6. **Export** : Permettre export de l'historique
7. **Calendrier** : Afficher calendrier des compétitions

---

**Dernière mise à jour :** 3 novembre 2025  
**Statut :** ✅ Documenté
