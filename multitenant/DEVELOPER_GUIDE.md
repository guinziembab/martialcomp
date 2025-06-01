# Multi-Tenant Developer Guide

This guide provides comprehensive documentation for developers working with the MartialComp multi-tenant architecture.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Components](#core-components)
3. [Development Workflow](#development-workflow)
4. [API Reference](#api-reference)
5. [Testing](#testing)
6. [Deployment](#deployment)
7. [Troubleshooting](#troubleshooting)

## Architecture Overview

MartialComp uses a **schema-based multi-tenancy** approach with PostgreSQL. Each tenant (organization) has:

- Isolated data in a separate PostgreSQL schema
- Custom subdomain (e.g., `club-name.martialcomp.com`)
- Independent subscription and billing
- Configurable features and limits

### Key Design Decisions

1. **Schema Isolation**: Each tenant gets a dedicated PostgreSQL schema
2. **Subdomain Routing**: Tenants are identified by subdomain
3. **Shared Infrastructure**: Single codebase serves all tenants
4. **Regional Pricing**: Pricing varies by continent

## Core Components

### 1. Tenant Model

```python
from multitenant.models import Tenant

# Key fields
tenant = Tenant(
    name="Martial Arts Club",
    slug="mac",
    schema_name="tenant_mac",
    domain="mac.martialcomp.com",
    continent="europe_west",
    subscription_plan="essentials",
    owner=user_instance,
)
```

### 2. Middleware

The `TenantMiddleware` handles tenant identification and schema switching:

```python
# In settings.py
MIDDLEWARE = [
    # ...
    'multitenant.middleware.TenantMiddleware',
    # ...
]
```

### 3. Schema Context

Use `SchemaContext` for explicit schema switching:

```python
from multitenant.utils import SchemaContext

# Execute code in specific tenant schema
with SchemaContext('tenant_abc'):
    users = User.objects.all()  # Returns users from tenant_abc schema
```

### 4. Database Router

The router ensures queries go to the correct schema:

```python
DATABASE_ROUTERS = ['multitenant.routers.TenantDatabaseRouter']
```

## Development Workflow

### Creating a New Feature

When developing tenant-aware features:

1. **Always consider tenant context**:
```python
def my_view(request):
    tenant = request.tenant  # Set by middleware
    if not tenant:
        return HttpResponse("No tenant", status=404)
    
    # Your tenant-specific logic here
```

2. **Use tenant-aware models**:
```python
from django.db import models

class MyModel(models.Model):
    # Model will automatically use tenant schema
    name = models.CharField(max_length=100)
    
    class Meta:
        # Ensure model is tenant-aware
        db_table = 'myapp_mymodel'
```

3. **Handle public vs tenant data**:
```python
# Public data (available to all tenants)
from multitenant.models import Tenant  # Always in public schema

# Tenant-specific data
from myapp.models import MyModel  # Uses tenant schema
```

### Local Development Setup

1. **Environment setup**:
```bash
# Clone repository
git clone <repository>
cd martialcomp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

2. **Database setup**:
```bash
# Create database
createdb martialcomp

# Run migrations
python manage.py migrate

# Create test tenant
python manage.py create_tenant "Test Club" test-club test@example.com
```

3. **Local hosts configuration**:
```bash
# Add to /etc/hosts (Linux/Mac) or C:\Windows\System32\drivers\etc\hosts
127.0.0.1  test-club.martialcomp.local
127.0.0.1  demo.martialcomp.local
```

4. **Run development server**:
```bash
python manage.py runserver
# Visit http://test-club.martialcomp.local:8000
```

## API Reference

### Tenant Management API

#### Get Tenant Info
```python
GET /tenant/api/tenant-info/
Response: {
    "tenant": {
        "id": "uuid",
        "name": "Club Name",
        "domain": "club.martialcomp.com",
        "plan": "essentials",
        "is_active": true
    }
}
```

#### Health Check
```python
GET /tenant/health/
Response: {
    "status": "healthy",
    "checks": {
        "database": {"status": "ok"},
        "schema": {"status": "ok"},
        "subscription": {"status": "ok"}
    }
}
```

### Payment Integration

```python
from multitenant.payments.service import TenantPaymentService

service = TenantPaymentService()

# Create subscription
subscription = service.create_tenant_subscription(tenant, "essentials")

# Cancel subscription
service.cancel_tenant_subscription(tenant)

# Handle webhook
service.handle_webhook("stripe", payload, signature)
```

## Testing

### Unit Tests

```python
from django.test import TestCase
from multitenant.models import Tenant

class TenantTestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name="Test Club",
            slug="test",
            schema_name="test_tenant",
            domain="test.martialcomp.com"
        )
    
    def test_tenant_creation(self):
        self.assertEqual(self.tenant.name, "Test Club")
```

### Integration Tests

```python
from django.test import TransactionTestCase
from multitenant.utils import SchemaContext

class TenantIntegrationTest(TransactionTestCase):
    def test_schema_isolation(self):
        tenant1 = create_test_tenant("tenant1")
        tenant2 = create_test_tenant("tenant2")
        
        # Create data in tenant1
        with SchemaContext(tenant1.schema_name):
            MyModel.objects.create(name="Tenant 1 Data")
        
        # Verify isolation
        with SchemaContext(tenant2.schema_name):
            self.assertEqual(MyModel.objects.count(), 0)
```

### Running Tests

```bash
# All tests
python manage.py test

# Specific app
python manage.py test multitenant

# With coverage
coverage run --source='.' manage.py test
coverage report
```

## Deployment

### Production Checklist

1. **Environment Variables**:
```bash
export DJANGO_SETTINGS_MODULE=config.settings.production
export DATABASE_URL=postgres://user:pass@host/db
export STRIPE_SECRET_KEY=sk_live_xxx
export ALLOWED_HOSTS=.martialcomp.com
```

2. **Database Migration**:
```bash
# Migrate public schema
python manage.py migrate

# Create tenants
python manage.py create_tenant "Production Club" prod-club owner@club.com
```

3. **Static Files**:
```bash
python manage.py collectstatic --noinput
```

4. **Web Server Configuration** (see SUBDOMAIN_SETUP.md)

### Monitoring

```bash
# Check all tenants
python manage.py monitor_tenants --check

# Watch mode
python manage.py monitor_tenants --watch

# Specific tenant
python manage.py monitor_tenants --check --tenant club-slug
```

## Troubleshooting

### Common Issues

#### 1. "No tenant found" Error
```python
# Check middleware is installed
MIDDLEWARE = [
    # ...
    'multitenant.middleware.TenantMiddleware',
]

# Verify domain configuration
python manage.py shell
>>> from multitenant.models import Tenant
>>> Tenant.objects.filter(domain='your-domain.com')
```

#### 2. Schema Not Found
```sql
-- Check schema exists
SELECT schema_name FROM information_schema.schemata 
WHERE schema_name = 'tenant_xxx';

-- Create manually if needed
CREATE SCHEMA tenant_xxx;
GRANT ALL ON SCHEMA tenant_xxx TO your_db_user;
```

#### 3. Migration Issues
```bash
# Reset migrations for tenant
python manage.py migrate_schemas --schema=tenant_xxx --fake

# Run specific migration
python manage.py migrate_schemas --schema=tenant_xxx app_name 0001
```

### Debug Mode

Enable detailed logging:

```python
# settings.py
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'multitenant': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

### Performance Optimization

1. **Use schema caching**:
```python
from django.core.cache import cache

def get_tenant_cached(domain):
    cache_key = f'tenant_{domain}'
    tenant = cache.get(cache_key)
    
    if not tenant:
        tenant = Tenant.objects.get(domain=domain)
        cache.set(cache_key, tenant, 3600)
    
    return tenant
```

2. **Optimize queries**:
```python
# Use select_related for foreign keys
tenants = Tenant.objects.select_related('owner').filter(is_active=True)

# Use prefetch_related for reverse foreign keys
tenant = Tenant.objects.prefetch_related('domains').get(id=tenant_id)
```

3. **Connection pooling**:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c default_transaction_isolation=read_committed',
        },
        'CONN_MAX_AGE': 60,  # Connection pooling
    }
}
```

## Best Practices

1. **Always test with multiple tenants**
2. **Use transactions for tenant operations**
3. **Implement proper access controls**
4. **Monitor resource usage per tenant**
5. **Regular backups of tenant schemas**
6. **Document tenant-specific customizations**

## Support

For issues or questions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review test cases in `multitenant/tests/`
3. Enable debug logging
4. Contact the development team

---

*Last updated: [Current Date]*