# 🔍 Guide de Diagnostic - Système de Sous-domaines MartialComp

## 📋 **Checklist de Diagnostic - Par Ordre de Priorité**

### **ÉTAPE 1 : Vérifications Infrastructure de Base (10 min)**

#### **1.1 Vérification DNS (Local & Production)**

```bash
# Test 1: Résolution DNS de base
nslookup martialcomp.com
nslookup www.martialcomp.com

# Test 2: Vérification wildcard DNS (CRITIQUE)
nslookup test.martialcomp.com
nslookup nonexistent.martialcomp.com

# Test 3: Test avec dig pour plus de détails
dig test.martialcomp.com
dig *.martialcomp.com

# Résultat attendu: Les sous-domaines doivent pointer vers la même IP que le domaine principal
```

**⚠️ POINT CRITIQUE :** Si les tests 2 et 3 échouent, le problème est au niveau DNS. Vérifiez :
- Enregistrement DNS wildcard `*.martialcomp.com IN A [IP_SERVEUR]`
- Configuration du fournisseur DNS (Cloudflare, OVH, etc.)

#### **1.2 Vérification Configuration Serveur Web**

```bash
# Pour Nginx
sudo nginx -t
cat /etc/nginx/sites-enabled/martialcomp* | grep server_name

# Pour Apache
sudo apache2ctl configtest
cat /etc/apache2/sites-enabled/* | grep ServerName

# Rechercher la configuration wildcard
grep -r "*.martialcomp.com" /etc/nginx/sites-*
grep -r "*.martialcomp.com" /etc/apache2/sites-*
```

**Configuration Nginx attendue :**
```nginx
server {
    listen 80;
    listen 443 ssl;
    server_name *.martialcomp.com martialcomp.com;
    
    ssl_certificate /path/to/wildcard.crt;
    ssl_certificate_key /path/to/wildcard.key;
    
    location / {
        proxy_pass http://django-app;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

### **ÉTAPE 2 : Vérifications Django Multi-Tenant (15 min)**

#### **2.1 Vérification des Modèles Tenant**

```python
# Commande 1: Vérifier que les modèles Tenant existent
python manage.py shell -c "
from multitenant.models import Tenant
print('Modèle Tenant trouvé:', Tenant._meta)
print('Nombre de tenants:', Tenant.objects.count())
for t in Tenant.objects.all():
    print(f'- {t.name}: {t.domain}')
"
```

#### **2.2 Vérification du Middleware Tenant**

```python
# Commande 2: Vérifier que le middleware est activé
python manage.py shell -c "
from django.conf import settings
middlewares = settings.MIDDLEWARE
print('Middlewares configurés:')
for i, mw in enumerate(middlewares):
    print(f'{i}: {mw}')
    if 'tenant' in mw.lower():
        print('  --> TENANT MIDDLEWARE TROUVÉ')
"
```

**⚠️ PROBLÈME FRÉQUENT :** Le middleware peut être manquant ou mal positionné. Il doit être après le SecurityMiddleware :

```python
# settings.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'multitenant.middleware.TenantMiddleware',  # <-- Doit être ici
    'django.contrib.sessions.middleware.SessionMiddleware',
    # ... autres middlewares
]
```

#### **2.3 Test du Middleware en Direct**

```python
# Commande 3: Tester la détection de tenant par domaine
python manage.py shell -c "
from multitenant.middleware import TenantMiddleware
from django.http import HttpRequest

# Simuler une requête avec sous-domaine
request = HttpRequest()
request.META['HTTP_HOST'] = 'test-club.martialcomp.com'

middleware = TenantMiddleware(lambda r: None)
try:
    response = middleware(request)
    print('Middleware fonctionne')
    print('Tenant actuel:', getattr(request, 'tenant', 'Aucun'))
except Exception as e:
    print('ERREUR Middleware:', e)
"
```

---

### **ÉTAPE 3 : Vérifications Génération de Sous-domaines (10 min)**

#### **3.1 Test du Générateur de Sous-domaines**

```python
# Commande 4: Tester le générateur
python manage.py shell -c "
from competitions.utils.subdomain_generator import SubdomainGenerator
from organizations.models import Organization

gen = SubdomainGenerator()

# Test avec organisation existante
if Organization.objects.exists():
    org = Organization.objects.first()
    subdomain = gen.generate_subdomain(org)
    print(f'Organisation: {org.name}')
    print(f'Sous-domaine généré: {subdomain}')
else:
    print('Aucune organisation trouvée pour test')
    # Créer une organisation test
    org = Organization.objects.create(
        name='Club Test Diagnostic',
        organization_type='club'
    )
    subdomain = gen.generate_subdomain(org)
    print(f'Organisation test créée: {org.name}')
    print(f'Sous-domaine généré: {subdomain}')
"
```

#### **3.2 Test de Création de Tenant**

```python
# Commande 5: Tester la création automatique de tenant
python manage.py shell -c "
from competitions.utils.subdomain_generator import create_organization_tenant
from organizations.models import Organization

if Organization.objects.exists():
    org = Organization.objects.first()
    print(f'Test avec organisation: {org.name}')
    
    try:
        tenant = create_organization_tenant(org)
        print(f'Tenant créé: {tenant.name} -> {tenant.domain}')
    except Exception as e:
        print(f'ERREUR création tenant: {e}')
        import traceback
        traceback.print_exc()
else:
    print('Aucune organisation pour test de création tenant')
"
```

---

### **ÉTAPE 4 : Vérifications URL et Routage (10 min)**

#### **4.1 Vérification des URLs Intégrées**

```python
# Commande 6: Vérifier l'intégration des URLs
python manage.py shell -c "
from django.urls import get_resolver
from django.conf.urls import include

resolver = get_resolver()
print('URLs principales configurées:')
for pattern in resolver.url_patterns:
    print(f'- {pattern}')
    if hasattr(pattern, 'pattern') and 'organization' in str(pattern.pattern):
        print('  --> URLs ORGANISATIONS TROUVÉES')
"
```

#### **4.2 Test de Résolution d'URL avec Sous-domaine**

```python
# Commande 7: Tester résolution URL
python manage.py shell -c "
from django.test import RequestFactory
from django.urls import resolve

factory = RequestFactory()

# Test 1: URL racine avec sous-domaine
try:
    request = factory.get('/', HTTP_HOST='test-club.martialcomp.com')
    match = resolve('/')
    print(f'URL racine résolue: {match.view_name}')
    print(f'Vue: {match.func}')
except Exception as e:
    print(f'ERREUR résolution URL racine: {e}')

# Test 2: URL spécifique organisation
try:
    request = factory.get('/inscription/', HTTP_HOST='test-club.martialcomp.com')
    match = resolve('/inscription/')
    print(f'URL inscription résolue: {match.view_name}')
except Exception as e:
    print(f'ERREUR résolution URL inscription: {e}')
"
```

---

### **ÉTAPE 5 : Vérifications Templates et Vues (10 min)**

#### **5.1 Vérification des Templates**

```bash
# Commande 8: Vérifier existence des templates
find . -name "*template*" -path "*/organizations/sites/*"
ls -la competitions/templates/organizations/sites/ 2>/dev/null || echo "Dossier templates organisations inexistant"

# Vérifier templates spécifiques
test -f competitions/templates/organizations/sites/club_template.html && echo "✅ Template club trouvé" || echo "❌ Template club manquant"
test -f competitions/templates/organizations/sites/federation_template.html && echo "✅ Template federation trouvé" || echo "❌ Template federation manquant"
```

#### **5.2 Test des Vues d'Organisation**

```python
# Commande 9: Tester les vues
python manage.py shell -c "
from competitions.views.organization_sites import organization_site_view
from django.test import RequestFactory
from multitenant.models import Tenant

factory = RequestFactory()

# Créer une requête test
request = factory.get('/', HTTP_HOST='test-club.martialcomp.com')

# Simuler un tenant
if Tenant.objects.exists():
    request.tenant = Tenant.objects.first()
    
    try:
        response = organization_site_view(request)
        print(f'Vue organisation fonctionne: {response.status_code}')
    except Exception as e:
        print(f'ERREUR vue organisation: {e}')
        import traceback
        traceback.print_exc()
else:
    print('Aucun tenant pour test de vue')
"
```

---

### **ÉTAPE 6 : Test Complet End-to-End (15 min)**

#### **6.1 Test de Création d'Organisation Complète**

```python
# Commande 10: Test complet création organisation -> tenant -> sous-domaine
python manage.py shell -c "
from organizations.models import Organization
from competitions.utils.subdomain_generator import create_organization_tenant
import uuid

# Créer organisation test
org_name = f'Club Test {uuid.uuid4().hex[:8]}'
print(f'Création organisation: {org_name}')

org = Organization.objects.create(
    name=org_name,
    organization_type='club',
    description='Club de test pour diagnostic'
)

print(f'✅ Organisation créée: {org.id}')

# Créer tenant automatiquement
try:
    tenant = create_organization_tenant(org)
    print(f'✅ Tenant créé: {tenant.domain}')
    
    # Vérifier que le tenant fonctionne
    from multitenant.models import Tenant
    tenant_check = Tenant.objects.get(domain=tenant.domain)
    print(f'✅ Tenant vérifié en DB: {tenant_check.name}')
    
except Exception as e:
    print(f'❌ ERREUR création tenant: {e}')
    import traceback
    traceback.print_exc()
"
```

#### **6.2 Test d'Accès HTTP Réel**

```bash
# Commande 11: Test HTTP réel (si serveur de dev lancé)
echo "Test d'accès HTTP au sous-domaine..."

# Test local (avec /etc/hosts si nécessaire)
curl -H "Host: test-club.martialcomp.com" http://localhost:8000/ -v

# Test avec sous-domaine réel si DNS configuré
curl http://test-club.martialcomp.com/ -v
```

---

## 🚨 **Diagnostic des Problèmes Courants**

### **PROBLÈME 1 : "Tenant not found" ou erreur middleware**

**Symptômes :**
- Erreur 500 avec message tenant
- Page blanche sur sous-domaine

**Solutions :**
1. Vérifier que le middleware est activé
2. Créer un tenant par défaut
3. Vérifier la configuration ALLOWED_HOSTS

```python
# Fix rapide: Créer tenant par défaut
python manage.py shell -c "
from multitenant.models import Tenant
default_tenant, created = Tenant.objects.get_or_create(
    domain='martialcomp.com',
    defaults={'name': 'Default Tenant', 'is_active': True}
)
print(f'Tenant par défaut: {default_tenant.domain}')
"
```

### **PROBLÈME 2 : Sous-domaine ne résout pas**

**Symptômes :**
- DNS_PROBE_FINISHED_NXDOMAIN
- "Site ne peut pas être atteint"

**Solutions :**
1. Configurer DNS wildcard
2. Ajouter au fichier hosts local pour test

```bash
# Fix local temporaire
echo "127.0.0.1 test-club.martialcomp.com" | sudo tee -a /etc/hosts
echo "127.0.0.1 club-test.martialcomp.com" | sudo tee -a /etc/hosts
```

### **PROBLÈME 3 : Templates non trouvés**

**Symptômes :**
- TemplateDoesNotExist
- Page d'erreur Django

**Solutions :**
1. Créer les templates manquants
2. Vérifier les chemins dans TEMPLATES

```bash
# Créer structure de templates minimale
mkdir -p competitions/templates/organizations/sites/
cat > competitions/templates/organizations/sites/default_template.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>{{ organization.name }}</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>
    <h1>{{ organization.name }}</h1>
    <p>{{ organization.description }}</p>
    <p>Type: {{ organization.organization_type }}</p>
</body>
</html>
EOF
```

---

## 🎯 **Actions Correctives Prioritaires**

### **SI DNS/INFRASTRUCTURE DÉFAILLANTE :**
1. Configurer enregistrement DNS wildcard
2. Obtenir certificat SSL wildcard
3. Configurer serveur web (Nginx/Apache)

### **SI PROBLÈME DJANGO/TENANT :**
1. Activer middleware tenant
2. Créer tenants pour organisations existantes
3. Intégrer URLs organisation

### **SI PROBLÈME TEMPLATES/VUES :**
1. Créer templates de base
2. Vérifier routage des vues
3. Tester avec organisation simple

---

## 📊 **Rapport de Diagnostic**

Après avoir exécuté toutes les commandes, utilisez ce template pour documenter les résultats :

```
RAPPORT DIAGNOSTIC SOUS-DOMAINES - [DATE]

Infrastructure:
[ ] DNS wildcard configuré
[ ] Serveur web configuré pour sous-domaines
[ ] Certificats SSL en place

Django Multi-Tenant:
[ ] Modèles Tenant présents
[ ] Middleware activé et fonctionnel
[ ] Tenants créés pour organisations

Génération Sous-domaines:
[ ] Générateur fonctionnel
[ ] Création automatique de tenants
[ ] Liaison organisation <-> tenant

URLs et Routage:
[ ] URLs intégrées dans config principale
[ ] Résolution correcte pour sous-domaines
[ ] Vues organisation accessibles

Templates et Interface:
[ ] Templates de base créés
[ ] Vues rendering correctement
[ ] CSS/JS chargés correctement

RÉSULTAT GLOBAL: [FONCTIONNEL / PARTIELLEMENT FONCTIONNEL / NON FONCTIONNEL]

PROCHAINES ACTIONS:
1. [Action prioritaire 1]
2. [Action prioritaire 2]
3. [Action prioritaire 3]
```

---

## ⚡ **Fix Rapide - Mise en Route Minimale**

Si vous voulez un fix rapide pour tester, exécutez ces commandes dans l'ordre :

```bash
# 1. Créer templates minimaux
mkdir -p competitions/templates/organizations/sites/
cat > competitions/templates/organizations/sites/club_template.html << 'EOF'
<!DOCTYPE html>
<html><head><title>{{ organization.name }}</title></head>
<body><h1>{{ organization.name }}</h1><p>{{ organization.description }}</p></body></html>
EOF

# 2. Créer tenant test
python manage.py shell -c "
from multitenant.models import Tenant
from organizations.models import Organization

# Créer organisation test si pas d'organisation
if not Organization.objects.exists():
    org = Organization.objects.create(name='Club Test', organization_type='club')

# Créer tenant pour test
org = Organization.objects.first()
tenant, created = Tenant.objects.get_or_create(
    domain=f'{org.name.lower().replace(\" \", \"-\")}.martialcomp.com',
    defaults={'name': org.name, 'is_active': True}
)
print(f'Tenant: {tenant.domain}')
"

# 3. Test local
echo "127.0.0.1 club-test.martialcomp.com" | sudo tee -a /etc/hosts
curl -H "Host: club-test.martialcomp.com" http://localhost:8000/
```

Ce guide vous permettra d'identifier précisément où se situe le problème et de le résoudre étape par étape.