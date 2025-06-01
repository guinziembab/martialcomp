# Guide du système de limites de ressources

## Vue d'ensemble

Le système de limites de ressources est conçu pour gérer et contrôler l'utilisation des ressources par tenant dans l'architecture multi-tenant. Il permet d'appliquer des limites basées sur les plans d'abonnement et de surveiller l'utilisation en temps réel.

## Plans d'abonnement

### 1. Plan Essentials
- **Storage**: 1 GB
- **Utilisateurs**: 5
- **Pratiquants**: 100
- **Compétitions**: 3
- **Catégories**: 15
- **Clubs**: 3
- **Emails mensuels**: 1000
- **Fonctionnalités**: Basiques

### 2. Plan Masters
- **Storage**: 5 GB
- **Utilisateurs**: 15
- **Pratiquants**: 500
- **Compétitions**: 10
- **Catégories**: 50
- **Clubs**: 10
- **Emails mensuels**: 5000
- **Fonctionnalités**: Avancées + Grades + Rapports financiers

### 3. Plan Champion
- **Storage**: 20 GB
- **Utilisateurs**: 50
- **Pratiquants**: 2000
- **Compétitions**: 30
- **Catégories**: 100
- **Clubs**: 30
- **Emails mensuels**: 20000
- **Fonctionnalités**: Toutes + API + White label + Analytics

### 4. Plan Enterprise
- **Storage**: 100 GB
- **Limites**: Illimitées pour la plupart des ressources
- **Fonctionnalités**: Toutes + Support prioritaire + SLA

## Utilisation

### 1. Tracker de ressources

```python
from multitenant.resource_limits import ResourceUsageTracker

# Obtenir l'utilisation actuelle
tracker = ResourceUsageTracker(tenant)
usage = tracker.get_resource_usage()

# Vérifier une limite spécifique
can_add = tracker.can_add_resource('practitioners')
```

### 2. Gestionnaire de quotas

```python
from multitenant.resource_limits import ResourceQuotaManager

# Créer un gestionnaire
quota_manager = ResourceQuotaManager(tenant)

# Vérifier si on peut consommer
if quota_manager.can_consume('monthly_emails', 10):
    # Consommer le quota
    quota_manager.consume_quota('monthly_emails', 10)

# Obtenir le quota restant
remaining = quota_manager.get_remaining_quota('monthly_emails')
```

### 3. Décorateurs pour les vues

```python
from multitenant.resource_limits import check_resource_limit, check_feature_access

@check_resource_limit('practitioners')
def create_practitioner_view(request):
    # Cette vue ne sera accessible que si la limite n'est pas atteinte
    pass

@check_feature_access('api_access')
def api_endpoint_view(request):
    # Cette vue ne sera accessible que si la fonctionnalité est disponible
    pass
```

### 4. Monitoring et alertes

```python
from multitenant.resource_limits import ResourceMonitor

# Créer un moniteur
monitor = ResourceMonitor(tenant)

# Vérifier les alertes
alerts = monitor.check_alerts()

# Envoyer des notifications
monitor.send_alert_notifications(alerts)
```

## Interface utilisateur

### 1. Tableau de bord
Accessible via `/multitenant/resources/`
- Vue d'ensemble de l'utilisation
- Graphiques de progression
- Alertes actives
- Quotas restants

### 2. Administration
Accessible via `/multitenant/resources/admin/` (super-admin uniquement)
- Vue de tous les tenants
- Alertes globales
- Statistiques d'utilisation

### 3. API
- `/multitenant/resources/api/usage/` : Obtenir l'utilisation actuelle
- `/multitenant/resources/api/quota/` : Vérifier et consommer des quotas

## Configuration

### 1. Middleware
Le `ResourceTrackerMiddleware` doit être ajouté dans `settings.py`:

```python
MIDDLEWARE = [
    # ...
    'multitenant.middleware.TenantMiddleware',
    'multitenant.resource_limits.ResourceTrackerMiddleware',
    # ...
]
```

### 2. Limites personnalisées
Pour un plan custom, définir les limites dans les métadonnées du tenant:

```python
tenant.metadata = {
    'custom_limits': {
        'max_users': 100,
        'max_practitioners': 5000,
        # ...
    }
}
```

## Commandes de gestion

### 1. Afficher l'utilisation
```bash
python manage.py show_resource_usage
python manage.py show_resource_usage --tenant=slug-tenant
python manage.py show_resource_usage --format=json
```

### 2. Surveiller les alertes
```bash
python manage.py show_resource_usage --alerts-only
```

## Bonnes pratiques

1. **Vérification préventive**: Toujours vérifier les limites avant de créer des ressources
2. **Gestion des quotas**: Utiliser le gestionnaire de quotas pour les ressources consommables
3. **Monitoring**: Surveiller régulièrement les alertes et l'utilisation
4. **Communication**: Informer les tenants quand ils approchent de leurs limites
5. **Mise à niveau**: Proposer proactivement la mise à niveau du plan

## Dépannage

### Problèmes courants

1. **"Limite atteinte" lors de la création**
   - Vérifier l'utilisation actuelle
   - Proposer la mise à niveau du plan
   - Nettoyer les ressources inutilisées

2. **Performances lentes**
   - Vérifier le cache
   - Optimiser les requêtes de comptage
   - Utiliser le cache Redis pour les gros volumes

3. **Alertes non envoyées**
   - Vérifier la configuration email
   - Vérifier les logs d'erreur
   - Tester manuellement l'envoi

## Intégration

### 1. Avec le système de paiement
```python
# Lors du changement de plan
tenant.subscription_plan = new_plan
tenant.save()

# Mettre à jour les limites immédiatement
tracker = ResourceUsageTracker(tenant)
new_limits = tracker.limits
```

### 2. Avec l'API
```python
from rest_framework.decorators import api_view
from multitenant.resource_limits import check_rate_limit

@api_view(['GET'])
@check_rate_limit('api')
def api_endpoint(request):
    # Limite de taux appliquée automatiquement
    pass
```

### 3. Avec les notifications
```python
# Intégrer avec votre système de notifications
def send_limit_warning(tenant, resource_type, percentage):
    notification = Notification.objects.create(
        tenant=tenant,
        type='resource_limit_warning',
        message=f'{resource_type} at {percentage}% capacity'
    )
    # Envoyer par email, SMS, etc.
```

## Exemples de code

### 1. Vue de création avec vérification
```python
class CreatePractitionerView(View):
    @check_resource_limit('practitioners')
    def post(self, request):
        # Créer le pratiquant
        practitioner = Practitioner.objects.create(
            # ...
        )
        return JsonResponse({'id': practitioner.id})
```

### 2. Import en masse avec quota
```python
def bulk_import_practitioners(request, file):
    quota_manager = ResourceQuotaManager(request.tenant)
    
    # Vérifier le quota d'imports
    if not quota_manager.can_consume('imports', 1):
        raise QuotaExceededError("Import quota exceeded for today")
    
    # Vérifier la limite de pratiquants
    tracker = ResourceUsageTracker(request.tenant)
    new_count = len(parse_csv(file))
    
    if not tracker.can_add_resource('practitioners', new_count):
        raise LimitExceededError("Practitioner limit would be exceeded")
    
    # Procéder à l'import
    quota_manager.consume_quota('imports', 1)
    # ... code d'import
```

### 3. Dashboard avec alertes
```python
def dashboard_view(request):
    tenant = request.tenant
    summary = get_resource_summary_for_tenant(tenant)
    
    # Afficher les alertes prioritaires
    critical_alerts = [a for a in summary['alerts'] if a['level'] == 'critical']
    
    if critical_alerts:
        messages.error(request, "Critical resource limits reached!")
    
    return render(request, 'dashboard.html', {
        'summary': summary,
        'alerts': critical_alerts
    })
```

## Maintenance

### 1. Nettoyage régulier
```python
# Script de maintenance
def cleanup_old_data():
    # Supprimer les anciens logs
    # Archiver les données historiques
    # Optimiser les compteurs
    pass
```

### 2. Optimisation des performances
```python
# Utiliser le cache pour les calculs coûteux
def get_storage_usage_cached(tenant):
    cache_key = f'storage_usage_{tenant.id}'
    usage = cache.get(cache_key)
    
    if usage is None:
        usage = calculate_storage_usage(tenant)
        cache.set(cache_key, usage, 3600)  # 1 heure
    
    return usage
```

### 3. Monitoring avancé
```python
# Intégration avec Prometheus/Grafana
from prometheus_client import Counter, Gauge

resource_usage_gauge = Gauge(
    'tenant_resource_usage',
    'Resource usage by tenant',
    ['tenant_id', 'resource_type']
)

def update_metrics():
    for tenant in Tenant.objects.filter(is_active=True):
        usage = get_resource_summary_for_tenant(tenant)
        
        for resource, value in usage['usage'].items():
            if resource.endswith('_count'):
                resource_usage_gauge.labels(
                    tenant_id=tenant.id,
                    resource_type=resource
                ).set(value)
```