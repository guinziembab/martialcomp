# DOCUMENTATION : judge_competition_list.html

**Liste des compétitions assignées au juge**

---

## 📋 INFORMATIONS GÉNÉRALES

- **Nom du template :** `judge_competition_list.html`
- **Localisation :** `apps/competitions/templates/competitions/technical_scoring/judge_competition_list.html`
- **Type :** Liste des compétitions pour juges
- **Priorité :** 🟠 Moyenne
- **Usage :** Affiche toutes les compétitions techniques assignées au juge avec accès rapide

---

## 🔗 URL ASSOCIÉE

**Pattern URL :** `/technical-scoring/judge/competitions/`

**Vue Django :** `apps/competitions/views/technical_scoring.py::judge_competition_list`

**Nom de l'URL :** `competitions:technical_scoring:judge_competition_list`

---

## 📦 CONTEXTE REQUIS

### Variables obligatoires

| Variable | Type | Description |
|----------|------|-------------|
| `competitions` | `List[Competition]` | Liste des compétitions assignées |

### Structure de chaque `competition`

- `id` : ID de la compétition
- `name` : Nom de la compétition
- `start_date` / `end_date` : Dates
- `location` : Lieu
- `discipline.name` : Nom de la discipline
- `categories.count` : Nombre de catégories

---

## 🎨 STRUCTURE DU TEMPLATE

### En-tête

```html
<div class="competitions-header">
    <h1>
        <i class="fas fa-clipboard-list"></i>
        Mes compétitions techniques
    </h1>
    <p>Gérez vos assignations de notation technique et suivez vos performances</p>
</div>
```

### Statistiques

```html
<div class="stats-row">
    <div class="stat-card">
        <div class="stat-number">{{ competitions|length }}</div>
        <div class="stat-label">Compétitions totales</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">0</div>
        <div class="stat-label">En cours</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">0</div>
        <div class="stat-label">À venir</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">0</div>
        <div class="stat-label">Terminées</div>
    </div>
</div>
```

### Cartes de compétitions

```html
{% for competition in competitions %}
<div class="competition-card">
    <div class="competition-header">
        <div>
            <h3>{{ competition.name }}</h3>
            <span class="competition-status status-upcoming">À venir</span>
        </div>
    </div>
    
    <div class="competition-info">
        <div class="info-item">
            <i class="fas fa-calendar"></i>
            <span>{{ competition.start_date|date:"d/m/Y" }} - {{ competition.end_date|date:"d/m/Y" }}</span>
        </div>
        <div class="info-item">
            <i class="fas fa-map-marker-alt"></i>
            <span>{{ competition.location }}</span>
        </div>
        <div class="info-item">
            <i class="fas fa-users"></i>
            <span>{{ competition.categories.count }} catégorie(s)</span>
        </div>
        <div class="info-item">
            <i class="fas fa-karate"></i>
            <span>{{ competition.discipline.name }}</span>
        </div>
    </div>
    
    <div class="competition-actions">
        <a href="{% url 'competitions:technical_scoring:judge_dashboard' %}" class="btn-competition btn-primary-comp">
            <i class="fas fa-tachometer-alt"></i> Tableau de bord
        </a>
        <a href="{% url 'competitions:technical_scoring:scoring_interface' competition.id %}" class="btn-competition btn-outline-comp">
            <i class="fas fa-edit"></i> Interface de notation
        </a>
        <a href="{% url 'competitions:technical_scoring:scoring_history' competition.id %}" class="btn-competition btn-info-comp">
            <i class="fas fa-history"></i> Historique
        </a>
    </div>
</div>
{% endfor %}
```

---

## 🎯 FONCTIONNALITÉS

### ✅ Fonctionnalités implémentées

1. **Liste visuelle** : Cartes pour chaque compétition
2. **Statistiques** : Compteurs animés
3. **Informations complètes** : Dates, lieu, catégories, discipline
4. **Actions rapides** : Liens vers dashboard, notation, historique
5. **Design responsive** : Adapté mobile et desktop
6. **Animations** : Fade in up pour les cartes
7. **État vide** : Message si aucune compétition

---

## 💻 CODE JAVASCRIPT

### Animations des cartes

```javascript
const competitionCards = document.querySelectorAll('.competition-card');
competitionCards.forEach((card, index) => {
    card.style.animationDelay = `${index * 0.1}s`;
    card.style.animation = 'fadeInUp 0.5s ease forwards';
});
```

### Animation des statistiques

```javascript
const animateNumber = (element, target) => {
    let current = 0;
    const increment = target / 30;
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }
        element.textContent = Math.floor(current);
    }, 16);
};
```

---

**Dernière mise à jour :** 3 novembre 2025  
**Statut :** ✅ Documenté
