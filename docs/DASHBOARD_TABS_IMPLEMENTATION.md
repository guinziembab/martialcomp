# Plan d'implémentation - Dashboard avec onglets

## Phase 1 : Structure avec onglets Bootstrap

### 1. Modification du template principal

Remplacer la structure actuelle par des onglets :

```html
<!-- Navigation des onglets -->
<ul class="nav nav-tabs dashboard-tabs" id="dashboardTabs" role="tablist">
  <li class="nav-item" role="presentation">
    <button class="nav-link active" id="overview-tab" data-bs-toggle="tab" data-bs-target="#overview" type="button">
      <i class="fas fa-chart-line"></i> Vue d'ensemble
    </button>
  </li>
  <li class="nav-item" role="presentation">
    <button class="nav-link" id="members-tab" data-bs-toggle="tab" data-bs-target="#members" type="button">
      <i class="fas fa-users"></i> Membres
    </button>
  </li>
  <li class="nav-item" role="presentation">
    <button class="nav-link" id="competitions-tab" data-bs-toggle="tab" data-bs-target="#competitions" type="button">
      <i class="fas fa-trophy"></i> Compétitions
    </button>
  </li>
  <li class="nav-item" role="presentation">
    <button class="nav-link" id="finances-tab" data-bs-toggle="tab" data-bs-target="#finances" type="button">
      <i class="fas fa-euro-sign"></i> Finances
    </button>
  </li>
  <li class="nav-item" role="presentation">
    <button class="nav-link" id="events-tab" data-bs-toggle="tab" data-bs-target="#events" type="button">
      <i class="fas fa-calendar"></i> Événements
    </button>
  </li>
</ul>

<!-- Contenu des onglets -->
<div class="tab-content" id="dashboardTabContent">
  <div class="tab-pane fade show active" id="overview" role="tabpanel">
    <!-- Contenu vue d'ensemble -->
  </div>
  <div class="tab-pane fade" id="members" role="tabpanel">
    <!-- Contenu membres -->
  </div>
  <!-- etc... -->
</div>
```

### 2. CSS pour les onglets

```css
.dashboard-tabs {
  background-color: white;
  padding: 0.5rem 1rem 0;
  border-radius: var(--card-border-radius) var(--card-border-radius) 0 0;
  margin-bottom: 0;
  border-bottom: 1px solid #dee2e6;
}

.dashboard-tabs .nav-link {
  color: #6c757d;
  border: none;
  padding: 0.75rem 1.5rem;
  margin-right: 0.5rem;
  border-radius: 0.5rem 0.5rem 0 0;
  transition: all 0.3s;
}

.dashboard-tabs .nav-link:hover {
  background-color: #f8f9fa;
  color: var(--primary);
}

.dashboard-tabs .nav-link.active {
  background-color: var(--primary);
  color: white;
  font-weight: 500;
}

.dashboard-tabs .nav-link i {
  margin-right: 0.5rem;
}

.tab-content {
  background-color: white;
  padding: 2rem;
  border-radius: 0 0 var(--card-border-radius) var(--card-border-radius);
  min-height: 500px;
}
```

### 3. JavaScript pour sauvegarder les préférences

```javascript
// Sauvegarder l'onglet actif
document.addEventListener('DOMContentLoaded', function() {
  // Récupérer l'onglet sauvegardé
  const savedTab = localStorage.getItem('dashboardActiveTab');
  if (savedTab) {
    const tabEl = document.querySelector(`#${savedTab}-tab`);
    if (tabEl) {
      const tab = new bootstrap.Tab(tabEl);
      tab.show();
    }
  }

  // Sauvegarder l'onglet lors du changement
  const tabEls = document.querySelectorAll('#dashboardTabs button[data-bs-toggle="tab"]');
  tabEls.forEach(tabEl => {
    tabEl.addEventListener('shown.bs.tab', function (event) {
      const tabId = event.target.id.replace('-tab', '');
      localStorage.setItem('dashboardActiveTab', tabId);
    });
  });
});
```

## Phase 2 : Pagination des tables

### 1. Vue Django avec pagination

```python
from django.core.paginator import Paginator

@login_required
def club_dashboard(request):
    # ... code existant ...
    
    # Pagination des pratiquants
    practitioners_list = Practitioner.objects.filter(organization=club_organization)
    practitioners_paginator = Paginator(practitioners_list, 10)  # 10 par page
    practitioners_page = request.GET.get('practitioners_page', 1)
    practitioners = practitioners_paginator.get_page(practitioners_page)
    
    # Pagination des paiements
    payments_list = PaymentAttempt.objects.filter(...)
    payments_paginator = Paginator(payments_list, 10)
    payments_page = request.GET.get('payments_page', 1)
    recent_payments = payments_paginator.get_page(payments_page)
    
    context = {
        'practitioners': practitioners,
        'recent_payments': recent_payments,
        # ... autres données ...
    }
```

### 2. Template avec pagination

```html
<!-- Table des pratiquants -->
<div class="table-responsive">
  <table class="table">
    <!-- ... contenu table ... -->
  </table>
</div>

<!-- Pagination -->
<nav aria-label="Navigation pratiquants">
  <ul class="pagination justify-content-center">
    {% if practitioners.has_previous %}
      <li class="page-item">
        <a class="page-link" href="?practitioners_page={{ practitioners.previous_page_number }}#members">
          Précédent
        </a>
      </li>
    {% endif %}
    
    <li class="page-item active">
      <span class="page-link">
        Page {{ practitioners.number }} sur {{ practitioners.paginator.num_pages }}
      </span>
    </li>
    
    {% if practitioners.has_next %}
      <li class="page-item">
        <a class="page-link" href="?practitioners_page={{ practitioners.next_page_number }}#members">
          Suivant
        </a>
      </li>
    {% endif %}
  </ul>
</nav>
```

## Phase 3 : Cards collapsibles

### 1. Structure HTML

```html
<div class="card dashboard-card collapsible-card">
  <div class="card-header d-flex justify-content-between align-items-center" 
       data-bs-toggle="collapse" 
       data-bs-target="#financeContent" 
       style="cursor: pointer;">
    <h5 class="mb-0">
      <i class="fas fa-wallet"></i> Résumé financier
    </h5>
    <i class="fas fa-chevron-down collapse-icon"></i>
  </div>
  <div id="financeContent" class="collapse show">
    <div class="card-body">
      <!-- Contenu -->
    </div>
  </div>
</div>
```

### 2. CSS pour les cards collapsibles

```css
.collapsible-card .card-header {
  background-color: #f8f9fa;
  transition: background-color 0.3s;
}

.collapsible-card .card-header:hover {
  background-color: #e9ecef;
}

.collapse-icon {
  transition: transform 0.3s;
}

.collapsible-card .card-header[aria-expanded="false"] .collapse-icon {
  transform: rotate(-90deg);
}
```

### 3. Sauvegarder l'état des cards

```javascript
// Sauvegarder l'état des cards collapsibles
document.querySelectorAll('.collapsible-card .collapse').forEach(collapse => {
  const collapseId = collapse.id;
  
  // Restaurer l'état sauvegardé
  const savedState = localStorage.getItem(`collapse-${collapseId}`);
  if (savedState === 'hidden') {
    collapse.classList.remove('show');
  }
  
  // Sauvegarder lors du changement
  collapse.addEventListener('shown.bs.collapse', () => {
    localStorage.setItem(`collapse-${collapseId}`, 'shown');
  });
  
  collapse.addEventListener('hidden.bs.collapse', () => {
    localStorage.setItem(`collapse-${collapseId}`, 'hidden');
  });
});
```

## Phase 4 : Optimisations supplémentaires

### 1. Lazy loading des onglets

```javascript
// Charger le contenu seulement quand l'onglet est activé
document.querySelectorAll('#dashboardTabs button[data-bs-toggle="tab"]').forEach(tabEl => {
  tabEl.addEventListener('show.bs.tab', function (event) {
    const targetId = event.target.getAttribute('data-bs-target');
    const targetPane = document.querySelector(targetId);
    
    if (!targetPane.dataset.loaded) {
      // Charger le contenu via AJAX
      fetch(`/api/dashboard/${targetId.replace('#', '')}`)
        .then(response => response.text())
        .then(html => {
          targetPane.innerHTML = html;
          targetPane.dataset.loaded = 'true';
        });
    }
  });
});
```

### 2. Filtres rapides

```html
<div class="filter-bar mb-3">
  <div class="row">
    <div class="col-md-4">
      <input type="text" class="form-control" placeholder="Rechercher..." id="searchFilter">
    </div>
    <div class="col-md-3">
      <select class="form-select" id="statusFilter">
        <option value="">Tous les statuts</option>
        <option value="active">Actif</option>
        <option value="inactive">Inactif</option>
      </select>
    </div>
    <div class="col-md-3">
      <select class="form-select" id="dateFilter">
        <option value="">Toutes les dates</option>
        <option value="today">Aujourd'hui</option>
        <option value="week">Cette semaine</option>
        <option value="month">Ce mois</option>
      </select>
    </div>
  </div>
</div>
```

## Ordre de priorité d'implémentation

1. **Jour 1-2** : Implémenter la structure avec onglets
2. **Jour 3-4** : Ajouter la pagination aux tables
3. **Jour 5** : Implémenter les cards collapsibles
4. **Jour 6** : Tests et ajustements responsive
5. **Jour 7** : Documentation et déploiement

## Points d'attention

- Maintenir la compatibilité avec les URLs existantes
- Conserver tous les liens et fonctionnalités actuels
- Tester sur mobile, tablette et desktop
- Prévoir une migration progressive pour les utilisateurs
- Documenter les changements pour les utilisateurs