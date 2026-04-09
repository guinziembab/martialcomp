# DOCUMENTATION : scoring_history.html

**Historique des notations effectuées par le juge**

---

## 📋 INFORMATIONS GÉNÉRALES

- **Nom du template :** `scoring_history.html`
- **Localisation :** `apps/competitions/templates/competitions/technical_scoring/scoring_history.html`
- **Type :** Historique des notations
- **Priorité :** 🟡 Faible
- **Usage :** Consulter l'historique des notations précédentes effectuées par le juge

---

## 🔗 URL ASSOCIÉE

**Pattern URL :** `/technical-scoring/history/` ou `/technical-scoring/history/<competition_id>/`

**Vue Django :** `apps/competitions/views/technical_scoring.py::scoring_history`

**Nom de l'URL :** `competitions:technical_scoring:scoring_history`

---

## 📦 CONTEXTE REQUIS

### Variables obligatoires

| Variable | Type | Description |
|----------|------|-------------|
| `user` | `User` | Utilisateur juge |
| `scoring_history` | `List[Dict]` | Historique des notations |

### Variables optionnelles

| Variable | Type | Description |
|----------|------|-------------|
| `competition_id` | `int` | ID de la compétition (si filtré) |

### Structure de chaque entrée `scoring_history`

- `id` : ID de l'entrée d'historique
- `created_at` : Date et heure de notation
- `competition.name` : Nom de la compétition
- `participant.name` : Nom du participant
- `category.name` : Nom de la catégorie
- `total_score` : Score total (sur 10)

---

## 🎨 STRUCTURE DU TEMPLATE

### Table de l'historique

```html
<table class="table">
    <thead>
        <tr>
            <th>Date</th>
            <th>Compétition</th>
            <th>Participant</th>
            <th>Catégorie</th>
            <th>Score</th>
            <th>Actions</th>
        </tr>
    </thead>
    <tbody>
        {% for history in scoring_history %}
        <tr>
            <td>{{ history.created_at|date:"d/m/Y H:i" }}</td>
            <td>{{ history.competition.name }}</td>
            <td>{{ history.participant.name }}</td>
            <td>{{ history.category.name }}</td>
            <td>
                <span class="badge bg-primary">{{ history.total_score }}/10</span>
            </td>
            <td>
                <button onclick="viewDetails({{ history.id }})">
                    <i class="fas fa-eye"></i> Détails
                </button>
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>
```

### État vide

```html
{% if not scoring_history %}
<div class="text-center py-5">
    <i class="fas fa-history fa-3x text-muted mb-3"></i>
    <h5 class="text-muted">Aucun historique</h5>
    <p class="text-muted">Vous n'avez pas encore effectué de notations.</p>
</div>
{% endif %}
```

---

## 🎯 FONCTIONNALITÉS

### ✅ Fonctionnalités implémentées

1. **Historique complet** : Toutes les notations du juge
2. **Filtrage** : Possibilité de filtrer par compétition
3. **Affichage détaillé** : Date, compétition, participant, catégorie, score
4. **Vue détails** : Bouton pour voir les détails (TODO)

### ⚠️ Limitations identifiées

1. **TODO** : Vue détails non implémentée
2. Pas de recherche/filtres avancés
3. Pas de tri personnalisable
4. Pas de pagination

---

## 📝 EXEMPLE D'UTILISATION

### Dans la vue Django

```python
@login_required
def scoring_history(request, competition_id=None):
    user = request.user
    
    # TODO: Récupérer l'historique réel
    scoring_history = []  # À remplacer
    
    context = {
        'user': user,
        'competition_id': competition_id,
        'scoring_history': scoring_history,
    }
    
    return render(request, 'competitions/technical_scoring/scoring_history.html', context)
```

---

**Dernière mise à jour :** 3 novembre 2025  
**Statut :** ✅ Documenté
