# DOCUMENTATION : standalone_scoring/judge/performance_list.html

**Liste des performances disponibles pour notation (système standalone)**

---

## 📋 INFORMATIONS GÉNÉRALES

- **Nom du template :** `judge/performance_list.html`
- **Localisation :** `apps/competitions/templates/competitions/standalone_scoring/judge/performance_list.html`
- **Type :** Liste des performances pour juges
- **Priorité :** 🟠 Moyenne
- **Usage :** Affiche la liste des performances assignées au juge avec statut de notation

---

## 🔗 URL ASSOCIÉE

**Pattern URL :** `/standalone-scoring/judge/performances/`

**Vue Django :** `apps/competitions/views/standalone_scoring.py::JudgePerformanceListView`

**Nom de l'URL :** `competitions:standalone_scoring:judge_performances`

---

## 📦 CONTEXTE REQUIS

### Variables obligatoires

| Variable | Type | Description |
|----------|------|-------------|
| `performances` | `QuerySet[StandalonePerformance]` | Liste des performances assignées |

### Structure de chaque `performance`

Chaque performance doit avoir :
- `id` : ID de la performance
- `competition_name` : Nom de la compétition
- `category_name` : Nom de la catégorie
- `practitioner_name` : Nom du pratiquant
- `round_type` : Type de round (preliminary, semifinal, final, exhibition)
- `round_number` : Numéro du round
- `judging_status` : Statut de notation ('not_started', 'in_progress', 'submitted')

---

## 🎨 STRUCTURE DU TEMPLATE

### Table des performances

```html
<table class="table">
    <thead>
        <tr>
            <th>Competition</th>
            <th>Category</th>
            <th>Participant</th>
            <th>Round</th>
            <th>Status</th>
            <th>Actions</th>
        </tr>
    </thead>
    <tbody>
        {% for performance in performances %}
        <tr>
            <td>{{ performance.competition_name }}</td>
            <td>{{ performance.category_name }}</td>
            <td>{{ performance.practitioner_name }}</td>
            <td>
                {% if performance.round_type == 'preliminary' %}
                    Preliminary
                {% elif performance.round_type == 'semifinal' %}
                    Semifinal
                {% elif performance.round_type == 'final' %}
                    Final
                {% endif %}
                {{ performance.round_number }}
            </td>
            <td>
                {% if performance.judging_status == 'not_started' %}
                    <span class="status-not-started">Not Started</span>
                {% elif performance.judging_status == 'in_progress' %}
                    <span class="status-in-progress">In Progress</span>
                {% elif performance.judging_status == 'submitted' %}
                    <span class="status-submitted">Submitted</span>
                {% endif %}
            </td>
            <td>
                {% if performance.judging_status == 'submitted' %}
                    <button disabled>Submitted</button>
                {% else %}
                    <a href="{% url 'competitions:standalone_scoring:judge_score_entry' performance.id %}">
                        {% if performance.judging_status == 'not_started' %}
                            Start Scoring
                        {% else %}
                            Continue Scoring
                        {% endif %}
                    </a>
                {% endif %}
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>
```

---

## 🎯 FONCTIONNALITÉS

### ✅ Fonctionnalités implémentées

1. **Liste complète** : Toutes les performances assignées au juge
2. **Statut visuel** : Badges de statut (Not Started, In Progress, Submitted)
3. **Actions contextuelles** : "Start Scoring" ou "Continue Scoring"
4. **Support rounds** : Affichage du type et numéro de round
5. **Informations complètes** : Compétition, catégorie, participant

---

## 📝 EXEMPLE D'UTILISATION

### Dans la vue Django

```python
class JudgePerformanceListView(LoginRequiredMixin, ListView):
    template_name = 'competitions/standalone_scoring/judge/performance_list.html'
    context_object_name = 'performances'
    
    def get_queryset(self):
        # Récupérer le juge
        judge = Judge.objects.get(user=self.request.user)
        
        # Récupérer les performances assignées
        performances = StandalonePerformance.objects.filter(
            competition_id__in=judge.competitions.values_list('id', flat=True),
            status__in=['pending', 'in_progress']
        )
        
        # Annoter avec statut de notation
        for performance in performances:
            # Vérifier si soumis
            # Vérifier si en cours
            # Assigner judging_status
        
        return performances
```

---

**Dernière mise à jour :** 3 novembre 2025  
**Statut :** ✅ Documenté
