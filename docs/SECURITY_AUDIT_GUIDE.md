# Guide d'Audit de Sécurité Multi-Tenant

Ce guide décrit comment utiliser le système d'audit de sécurité pour l'architecture multi-tenant de MartialComp.

## Vue d'ensemble

Le système d'audit de sécurité vérifie l'intégrité et l'isolation de l'architecture multi-tenant. Il effectue plusieurs tests pour s'assurer que les données de chaque tenant sont correctement isolées et sécurisées.

## Tests disponibles

### 1. Isolation des schémas (Schema Isolation)
- Vérifie que chaque tenant ne peut accéder qu'à son propre schéma PostgreSQL
- Teste l'impossibilité d'accès croisé entre schémas
- Détecte les fuites de données potentielles

### 2. Isolation du middleware
- Vérifie que le middleware multi-tenant filtre correctement les requêtes
- S'assure que chaque requête est correctement associée au bon tenant
- Teste les redirections et les domaines

### 3. Isolation du cache
- Vérifie que les caches sont isolés entre tenants
- Teste les clés de cache pour s'assurer qu'elles incluent l'identifiant du tenant
- Détecte les fuites de cache potentielles

### 4. Accès aux fichiers
- Contrôle l'accès aux fichiers uploadés
- Vérifie que les médias sont correctement séparés par tenant
- Teste les permissions de fichiers

### 5. En-têtes de sécurité
- Vérifie la présence des en-têtes de sécurité HTTP importants
- Contrôle HSTS, X-Frame-Options, Content-Security-Policy, etc.
- S'assure de la protection contre les attaques courantes

### 6. Permissions des tenants
- Vérifie que les permissions sont correctement appliquées
- Teste les rôles et autorisations par tenant
- Contrôle l'accès aux ressources

## Utilisation

### 1. Via l'interface web

1. Connectez-vous en tant que super-administrateur
2. Accédez à `/multitenant/admin/security/`
3. Cliquez sur "Lancer un audit de sécurité"
4. Sélectionnez le tenant à auditer (ou laissez vide pour un audit global)
5. Choisissez les tests à exécuter
6. Lancez l'audit

### 2. Via la ligne de commande

#### Audit complet
```bash
python manage.py run_security_audit
```

#### Audit d'un tenant spécifique
```bash
python manage.py run_security_audit --tenant tenant-slug
```

#### Audit avec tests spécifiques
```bash
python manage.py run_security_audit --tests cross_schema_access,middleware_isolation
```

#### Contrôle rapide
```bash
python manage.py security_check
```

### 3. Via Celery (asynchrone)

```python
from multitenant.tasks.security_tasks import run_scheduled_security_audit

# Audit global
run_scheduled_security_audit.delay()

# Audit d'un tenant spécifique
run_scheduled_security_audit.delay(tenant_id='uuid-du-tenant')
```

## Planification des audits

### Configuration des audits réguliers

```bash
# Audit hebdomadaire à 2h du matin
python manage.py schedule_security_audits --frequency weekly --hour 2

# Audit quotidien d'un tenant spécifique
python manage.py schedule_security_audits --frequency daily --tenant tenant-id

# Désactiver les audits planifiés
python manage.py schedule_security_audits --disable
```

## Interprétation des résultats

### Statuts des tests

- **passed** : Aucune violation détectée
- **failed** : Des violations ont été trouvées
- **error** : Une erreur est survenue pendant le test

### Niveaux de sévérité

1. **Critical** : Problème de sécurité grave nécessitant une action immédiate
2. **High** : Problème important à corriger rapidement
3. **Medium** : Problème de sécurité modéré
4. **Low** : Problème mineur ou recommandation

### Score de sécurité

Le score de sécurité est calculé sur 100 points :
- 90-100 : Excellente sécurité
- 75-89 : Bonne sécurité
- 50-74 : Sécurité moyenne
- 0-49 : Sécurité insuffisante

## Résolution des problèmes

### 1. Violations d'isolation des schémas

**Problème** : Des accès croisés entre schémas sont détectés.

**Solutions** :
- Vérifier la configuration du middleware multi-tenant
- S'assurer que tous les modèles héritent de `TenantAwareModel`
- Vérifier les requêtes SQL personnalisées

### 2. Problèmes de middleware

**Problème** : Le middleware ne filtre pas correctement les requêtes.

**Solutions** :
- Vérifier l'ordre des middlewares dans `settings.py`
- S'assurer que `TenantMiddleware` est bien configuré
- Vérifier la configuration des domaines

### 3. Violations de cache

**Problème** : Les données de cache ne sont pas isolées.

**Solutions** :
- Utiliser le préfixe de tenant dans les clés de cache
- Configurer le cache backend pour supporter les préfixes
- Nettoyer le cache après correction

### 4. Problèmes d'accès aux fichiers

**Problème** : Les fichiers ne sont pas correctement isolés.

**Solutions** :
- Vérifier la configuration de `MEDIA_ROOT`
- S'assurer que les chemins incluent l'identifiant du tenant
- Vérifier les permissions des répertoires

### 5. En-têtes de sécurité manquants

**Problème** : Des en-têtes de sécurité HTTP sont absents.

**Solutions** :
- Configurer le middleware de sécurité Django
- Ajouter les en-têtes dans la configuration nginx/Apache
- Utiliser `django-security` pour une configuration complète

## Notifications et alertes

### Configuration des alertes email

1. Configurer les paramètres email dans `settings.py`
2. Ajouter les administrateurs dans `ADMINS`
3. Les alertes sont envoyées automatiquement pour :
   - Les violations critiques
   - Les scores de sécurité < 50%
   - Les échecs d'audit

### Intégration avec des systèmes de monitoring

Le système peut être intégré avec :
- Sentry pour le tracking des erreurs
- Prometheus pour les métriques
- Slack pour les notifications temps réel

## Bonnes pratiques

1. **Audits réguliers** : Effectuer des audits au minimum hebdomadaires
2. **Surveillance continue** : Monitorer les métriques de sécurité
3. **Réaction rapide** : Traiter les violations critiques immédiatement
4. **Documentation** : Documenter toutes les corrections apportées
5. **Tests** : Tester les corrections avant mise en production

## API REST

### Endpoints disponibles

```
GET /api/security/audit/
POST /api/security/audit/run/
GET /api/security/audit/reports/
GET /api/security/audit/reports/{id}/
GET /api/security/violations/
GET /api/security/compliance/{tenant_id}/
```

### Exemple d'utilisation

```python
import requests

# Lancer un audit
response = requests.post(
    'https://app.martialcomp.com/api/security/audit/run/',
    headers={'Authorization': 'Token your-token'},
    json={'tenant_id': 'tenant-uuid'}
)

# Récupérer les résultats
audit_id = response.json()['audit_id']
results = requests.get(
    f'https://app.martialcomp.com/api/security/audit/reports/{audit_id}/',
    headers={'Authorization': 'Token your-token'}
)
```

## Personnalisation

### Ajouter un nouveau test

1. Créer une méthode dans `SecurityAuditor`
2. Suivre le pattern des tests existants
3. Retourner un dictionnaire avec `status` et `violations`
4. Ajouter le test aux choix disponibles

### Modifier les seuils

Les seuils peuvent être configurés dans `settings.py` :

```python
SECURITY_AUDIT_CONFIG = {
    'critical_score_threshold': 50,
    'warning_score_threshold': 75,
    'report_retention_days': 30,
    'email_alerts_enabled': True,
}
```

## Support

Pour toute question ou problème :
1. Consultez la documentation complète
2. Vérifiez les logs d'audit
3. Contactez l'équipe de sécurité
4. Ouvrez un ticket sur le système de support