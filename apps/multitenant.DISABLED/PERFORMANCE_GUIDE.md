# Guide d'Optimisation des Performances Multi-Tenant

Ce guide détaille les optimisations de performance implémentées pour l'architecture multi-tenant de MartialComp.

## Vue d'Ensemble

Les optimisations de performance incluent :

1. **Mise en Cache Agressive** - Redis avec isolation par tenant
2. **Optimisation des Requêtes** - select_related et prefetch_related
3. **Indexes de Base de Données** - Indexes spécifiques par schéma
4. **Pools de Connexions** - Réutilisation des connexions DB
5. **ETags et Cache HTTP** - Réponses conditionnelles
6. **Monitoring et Métriques** - Suivi des performances

## 1. Configuration du Cache

### Installation

```bash
pip install -r requirements-performance.txt
```

### Configuration Redis

```python
# config/settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'CONNECTION_POOL_CLASS': 'redis.ConnectionPool',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
        },
        'KEY_PREFIX': 'martialcomp',
        'TIMEOUT': 300,
    },
    'session': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/2',
        'KEY_PREFIX': 'session',
        'TIMEOUT': 86400,
    },
}
```

## 2. Utilisation du Cache Tenant-Aware

### Cache Simple

```python
from multitenant.cache import tenant_cache

# Dans une vue
def my_view(request):
    # Le tenant est automatiquement défini via le middleware
    
    # Obtenir une valeur
    value = tenant_cache.get('my_key')
    
    # Définir une valeur
    tenant_cache.set('my_key', 'my_value', timeout=300)
    
    # Obtenir ou définir
    value = tenant_cache.get_or_set(
        'expensive_calculation',
        expensive_calculation_function,
        timeout=3600
    )
```

### Cache avec Mixins

```python
from multitenant.performance_mixins import TenantCacheMixin

class MyView(TenantCacheMixin, View):
    cache_timeout = 600  # 10 minutes
    
    def get(self, request):
        # Générer une clé de cache unique
        cache_key = self.get_cache_key('my_data')
        
        # Obtenir ou calculer les données
        data = self.get_cached_data(
            cache_key,
            self._calculate_expensive_data
        )
        
        return render(request, 'template.html', {'data': data})
    
    def _calculate_expensive_data(self):
        # Calcul coûteux
        return expensive_operation()
```

## 3. Optimisation des Requêtes

### QuerySet Optimisé

```python
from multitenant.performance_mixins import TenantQueryMixin

class OptimizedListView(TenantQueryMixin, ListView):
    model = Competition
    
    # Optimisations de requête
    select_related_fields = ['category', 'owner', 'location']
    prefetch_related_fields = ['disciplines', 'registrations']
```

### Décorateur pour Méthodes

```python
from multitenant.db_optimization import cached_tenant_method

class MyModel(models.Model):
    @cached_tenant_method('stats:{tenant_id}:model:{id}', timeout=1800)
    def get_statistics(self):
        # Calcul coûteux de statistiques
        return {
            'count': self.related_objects.count(),
            'total': self.related_objects.aggregate(Sum('value'))
        }
```

## 4. Optimisation de la Base de Données

### Créer des Indexes Optimisés

```bash
python manage.py optimize_tenant_db --create-indexes
```

### Analyser les Tables

```bash
python manage.py optimize_tenant_db --analyze-tables --tenant=schema_name
```

### Voir les Statistiques de Performance

```bash
python manage.py optimize_tenant_db --show-stats
```

## 5. Préchauffage du Cache

### Commande de Préchauffage

```bash
# Préchauffer tous les tenants actifs
python manage.py warm_tenant_cache

# Préchauffer un tenant spécifique
python manage.py warm_tenant_cache --tenant=example.martialcomp.com

# Avec timeout personnalisé
python manage.py warm_tenant_cache --timeout=7200
```

### Préchauffage Automatique

```python
# Dans signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from multitenant.models import Tenant
from multitenant.cache import CacheManager

@receiver(post_save, sender=Tenant)
def warm_cache_on_tenant_creation(sender, instance, created, **kwargs):
    if created and instance.is_active:
        CacheManager.warm_cache(instance)
```

## 6. Vues Optimisées

### Dashboard avec Cache Lourd

```python
from multitenant.performance_mixins import TenantDashboardMixin

class DashboardView(TenantDashboardMixin, TemplateView):
    template_name = 'dashboard.html'
    cache_timeout = 1800  # 30 minutes
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Les stats sont automatiquement mises en cache
        return context
```

### ListView avec Pagination Cachée

```python
from multitenant.performance_mixins import TenantListViewMixin

class CompetitionListView(TenantListViewMixin, ListView):
    model = Competition
    paginate_by = 25
    cache_timeout = 600
    
    # Configuration de recherche
    search_fields = ['name', 'description']
    ordering_fields = ['date', 'name']
```

### API avec Support ETag

```python
from multitenant.performance_mixins import TenantAPIViewMixin

class CompetitionAPIView(TenantAPIViewMixin, View):
    cache_timeout = 300
    use_etag = True
    
    def get_serialized_data(self):
        # Retourner les données sérialisées
        return {'competitions': [...]}
```

## 7. Invalidation du Cache

### Invalidation Manuelle

```python
from multitenant.cache import tenant_cache, CacheManager

# Invalider une clé spécifique
tenant_cache.delete('my_key')

# Invalider tout le cache d'un tenant
CacheManager.invalidate_tenant_cache(tenant)
```

### Invalidation Automatique dans les Formulaires

```python
from multitenant.performance_mixins import TenantFormViewMixin

class CompetitionCreateView(TenantFormViewMixin, CreateView):
    model = Competition
    
    # Clés à invalider après succès
    cache_keys_to_invalidate = [
        'dashboard_stats',
        'competition_list',
    ]
```

## 8. Monitoring des Performances

### Logs de Requêtes Lentes

```python
# Dans settings.py
LOGGING = {
    'loggers': {
        'multitenant': {
            'handlers': ['file'],
            'level': 'WARNING',
        },
    },
}
```

### Métriques Prometheus

```python
# Dans views.py
from multitenant.monitoring import TenantMetrics

class MyView(View):
    def get(self, request):
        with TenantMetrics.timer('view_duration'):
            # Votre code ici
            pass
```

## 9. Best Practices

### 1. Toujours Utiliser les Mixins

```python
# Bon
class MyView(TenantPerformanceMixin, View):
    pass

# Mauvais
class MyView(View):
    def get(self, request):
        # Cache manuel...
```

### 2. Définir des Timeouts Appropriés

```python
class MyView(TenantCacheMixin, View):
    # Court pour les données volatiles
    cache_timeout = 300  # 5 minutes
    
    # Long pour les données statiques
    static_cache_timeout = 86400  # 24 heures
```

### 3. Optimiser les QuerySets

```python
# Bon
Competition.objects.select_related('category').prefetch_related('registrations')

# Mauvais
Competition.objects.all()  # N+1 queries
```

### 4. Utiliser le Cache en Cascade

```python
def get_data(self):
    # Cache L1 - Mémoire
    if hasattr(self, '_cached_data'):
        return self._cached_data
    
    # Cache L2 - Redis
    data = tenant_cache.get('data')
    if data:
        self._cached_data = data
        return data
    
    # Calcul
    data = expensive_calculation()
    tenant_cache.set('data', data)
    self._cached_data = data
    return data
```

## 10. Dépannage

### Vérifier le Cache

```python
# Dans le shell Django
from multitenant.cache import tenant_cache
from multitenant.models import Tenant

tenant = Tenant.objects.get(domain='example.com')
tenant_cache.set_tenant(tenant)

# Tester le cache
tenant_cache.set('test', 'value')
print(tenant_cache.get('test'))
```

### Monitorer Redis

```bash
redis-cli monitor
```

### Analyser les Performances

```python
from multitenant.db_optimization import PerformanceMonitor

# Afficher les requêtes lentes
PerformanceMonitor.log_slow_queries(threshold_ms=50)

# Obtenir les statistiques
stats = PerformanceMonitor.get_query_stats('tenant_schema')
```

## Conclusion

L'utilisation correcte de ces outils d'optimisation peut améliorer les performances de 10x à 100x pour les opérations courantes. Assurez-vous de :

1. Toujours utiliser les mixins appropriés
2. Définir des stratégies de cache appropriées
3. Monitorer les performances régulièrement
4. Préchauffer le cache après les déploiements
5. Invalider le cache de manière intelligente

Pour plus d'informations, consultez la documentation Django et Redis.