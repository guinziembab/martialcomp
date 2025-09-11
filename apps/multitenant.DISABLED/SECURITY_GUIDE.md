# Guide de sécurité multi-tenant pour MartialComp

## Vue d'ensemble

Ce guide décrit le système d'audit de sécurité multi-tenant pour MartialComp. Le système vérifie régulièrement l'isolation des données entre les tenants et garantit la conformité aux normes de sécurité.

## Composants principaux

### 1. Module de sécurité (security.py)

Le module principal contient :

- **SecurityAuditor** : Effectue des audits de sécurité complets
- **TenantSecurityMonitor** : Surveille l'activité suspecte
- **TenantComplianceChecker** : Vérifie la conformité aux standards

### 2. Tests de sécurité

#### A. Test d'isolation des schémas (cross_schema_access)
- Vérifie que chaque tenant ne peut accéder qu'à son propre schéma PostgreSQL
- Test l'isolation entre le schéma public et les schémas des tenants
- Test l'isolation entre les schémas de différents tenants

#### B. Test d'isolation du middleware (middleware_isolation)
- Vérifie que le middleware multi-tenant définit correctement le tenant
- Teste que le contexte tenant est correctement isolé

#### C. Test d'isolation du cache (cache_isolation)
- Vérifie que les clés de cache sont correctement préfixées par tenant
- Teste que les tenants ne peuvent pas accéder aux données de cache des autres

#### D. Test d'accès aux fichiers (file_access)
- Vérifie l'isolation des fichiers entre les tenants
- Teste que les tenants ne peuvent pas accéder aux fichiers des autres

#### E. Test des en-têtes de sécurité (security_headers)
- Vérifie la présence des en-têtes de sécurité HTTP requis
- Teste la configuration de sécurité globale de Django

#### F. Test des permissions (tenant_permissions)
- Vérifie que les permissions sont correctement appliquées aux tenants
- Teste l'isolation des droits d'accès

## Utilisation

### 1. Via l'interface Django Admin

1. Accédez au tableau de bord d'administration multi-tenant
2. Cliquez sur "Sécurité" dans le menu
3. Depuis le tableau de bord de sécurité :
   - Visualisez le score de sécurité global
   - Consultez les rapports d'audit récents
   - Lancez un nouvel audit

### 2. Via la ligne de commande

```bash
# Audit de tous les tenants
python manage.py run_security_audit

# Audit d'un tenant spécifique
python manage.py run_security_audit --tenant=tenant_slug

# Audit avec sortie verbose
python manage.py run_security_audit --verbose

# Audit de tests spécifiques
python manage.py run_security_audit --only=cross_schema_access,cache_isolation

# Ignorer certains tests
python manage.py run_security_audit --skip=security_headers
```

### 3. Via les vues web

Les vues web disponibles incluent :

- **/multitenant/admin/security/** : Tableau de bord de sécurité
- **/multitenant/admin/security/reports/** : Liste des rapports d'audit
- **/multitenant/admin/security/reports/{id}/** : Détail d'un rapport
- **/multitenant/admin/security/audit/run/** : Lancer un nouvel audit
- **/multitenant/admin/security/violations/** : Analyser les violations

## Format des rapports

Les rapports d'audit sont enregistrés au format JSON dans :
```
/mnt/c/martial_hub_django/martialcomp/logs/security_reports/
```

Structure d'un rapport :
```json
{
  "summary": {
    "status": "passed|failed",
    "tests_run": 6,
    "violations_found": 0,
    "report_id": "uuid",
    "timestamp": "2024-01-01T12:00:00",
    "tenant": "tenant_name|all"
  },
  "results": {
    "cross_schema_access": {
      "status": "passed|failed",
      "checks": [...],
      "violations": [...]
    },
    ...
  }
}
```

## Violations et sévérité

Les violations sont classées par sévérité :

- **Critique** : Violation majeure de sécurité, nécessite une action immédiate
- **Haute** : Problème de sécurité important
- **Moyenne** : Problème de sécurité modéré
- **Basse** : Problème mineur de sécurité

## Bonnes pratiques

### 1. Audits réguliers

- Exécutez un audit de sécurité au moins une fois par semaine
- Effectuez un audit après chaque mise à jour importante
- Auditez les nouveaux tenants avant leur activation

### 2. Réponse aux violations

1. **Violations critiques** : Corrigez immédiatement et ré-auditez
2. **Violations hautes** : Corrigez dans les 24 heures
3. **Violations moyennes** : Corrigez dans la semaine
4. **Violations basses** : Corrigez lors de la prochaine maintenance

### 3. Configuration de sécurité

Assurez-vous que les paramètres de sécurité suivants sont configurés dans `settings.py` :

```python
# En production
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
```

### 4. Monitoring continu

- Surveillez les logs de sécurité : `/logs/security_audit.log`
- Configurez des alertes pour les violations critiques
- Examinez les tendances de sécurité au fil du temps

## API Python

Pour intégrer les audits de sécurité dans votre code :

```python
from multitenant.security import SecurityAuditor, run_security_audit

# Auditer un tenant spécifique
auditor = SecurityAuditor(tenant)
result = auditor.run_all_audits()

if result['summary']['status'] == 'failed':
    violations = result['summary']['violations_found']
    print(f"Audit échoué avec {violations} violations")

# Auditer tous les tenants
result = run_security_audit()
```

## Tests spécifiques

### Test d'isolation de schéma personnalisé

```python
from multitenant.security import SecurityAuditor

def test_custom_isolation(tenant):
    auditor = SecurityAuditor(tenant)
    result = auditor.audit_cross_schema_access()
    
    for violation in result['violations']:
        if violation['severity'] == 'critical':
            # Prendre une action immédiate
            notify_security_team(violation)
```

### Monitorer l'activité suspecte

```python
from multitenant.security import TenantSecurityMonitor

def check_suspicious_activity(tenant):
    activities = TenantSecurityMonitor.check_tenant_activity(tenant)
    
    for activity in activities:
        if activity['risk_level'] == 'high':
            # Logger et alerter
            logger.warning(f"Activité suspecte: {activity}")
```

## Conformité RGPD

Le système inclut des vérifications RGPD de base :

```python
from multitenant.security import TenantComplianceChecker

def verify_gdpr_compliance(tenant):
    result = TenantComplianceChecker.check_gdpr_compliance(tenant)
    
    if result['status'] == 'failed':
        for violation in result['violations']:
            print(f"RGPD violation: {violation['description']}")
```

## Dépannage

### Problèmes courants

1. **"Aucun tenant trouvé pour le domaine"**
   - Vérifiez la configuration des domaines
   - Assurez-vous que le tenant est actif

2. **"Le schéma n'existe pas"**
   - Exécutez les migrations : `python manage.py migrate_schemas`
   - Vérifiez la création du schéma

3. **"Accès refusé au schéma"**
   - Vérifiez les permissions PostgreSQL
   - Assurez-vous que l'utilisateur DB a les droits appropriés

### Commandes utiles

```bash
# Vérifier l'état des schémas
psql -d martialcomp -c "\dn+"

# Vérifier les permissions
psql -d martialcomp -c "SELECT * FROM information_schema.role_table_grants;"

# Examiner les logs
tail -f logs/security_audit.log
```

## Support

Pour toute question ou problème :

1. Consultez les logs d'audit dans `/logs/security_reports/`
2. Vérifiez les logs de sécurité dans `/logs/security_audit.log`
3. Contactez l'équipe de développement pour des problèmes complexes

## Évolutions futures

Les améliorations prévues incluent :

1. Audit automatique programmé via Celery
2. Alertes en temps réel pour les violations critiques
3. Dashboard de sécurité plus avancé avec visualisations
4. Intégration avec des services de sécurité externes
5. Tests de pénétration automatisés
6. Conformité étendue (SOC2, ISO 27001, etc.)