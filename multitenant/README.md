# Module Multi-Tenant MartialComp

## Vue d'ensemble

Ce module implémente l'architecture multi-tenant pour MartialComp, permettant à plusieurs organisations (clubs, fédérations) de partager la même instance d'application tout en maintenant leurs données isolées.

## Architecture

- **Isolation des données** : Schémas PostgreSQL séparés par tenant
- **Identification des tenants** : Par sous-domaine (ex: `club1.martialcomp.com`)
- **Tarification régionale** : Prix adaptés par continent
- **Plans d'abonnement** : 3 niveaux (Essentials, Masters, Champion)

## Installation

1. **Ajouter l'application aux `INSTALLED_APPS`** :
```python
INSTALLED_APPS = [
    # ...
    'multitenant',
    # ...
]
```

2. **Ajouter le middleware** :
```python
MIDDLEWARE = [
    # ...
    'multitenant.middleware.TenantMiddleware',
    # ...
]
```

3. **Configurer le routeur de base de données** :
```python
DATABASE_ROUTERS = ['multitenant.routers.TenantDatabaseRouter']
```

4. **Exécuter les migrations** :
```bash
python manage.py migrate multitenant
```

## Utilisation

### Créer un tenant

```bash
python manage.py create_tenant "Nom du Club" slug-du-club --continent europe_west --plan essentials
```

### Tester l'isolation

```bash
python manage.py test_tenant_isolation --tenant1 club1 --tenant2 club2
```

### API Endpoints

- `/tenant/api/tenant-info/` : Informations sur le tenant actuel
- `/tenant/dashboard/` : Tableau de bord du tenant

## Modèles

### Tenant
- Représente une organisation (club, fédération)
- Contient les informations de facturation et d'abonnement
- Gère l'isolation des données par schéma PostgreSQL

### Domain
- Domaines supplémentaires pour un tenant
- Permet plusieurs URLs pour la même organisation

### TenantFeature
- Gestion fine des fonctionnalités par tenant
- Permet d'activer/désactiver des fonctionnalités spécifiques

## Plans et Tarification

### Plans disponibles
1. **Dojo Essentials** : Jusqu'à 100 membres, 2 disciplines
2. **Master's Circle** : Jusqu'à 300 membres, 5 disciplines, compétitions
3. **Grand Champion Suite** : Illimité, toutes fonctionnalités

### Tarification par continent
Les prix sont adaptés au pouvoir d'achat de chaque région :
- Afrique : 2,99€ - 9,99€/an
- Europe de l'Ouest : 9,99€ - 29,99€/an
- Amérique du Nord : 9,99€ - 29,99€/an

## Commandes de gestion

### create_tenant
Crée un nouveau tenant avec son schéma PostgreSQL
```bash
python manage.py create_tenant "Club Name" club-slug [options]
```

### test_tenant_isolation
Teste l'isolation des données entre tenants
```bash
python manage.py test_tenant_isolation --tenant1 slug1 --tenant2 slug2
```

### migrate_to_public_schema
Prépare les données existantes pour la migration multi-tenant
```bash
python manage.py migrate_to_public_schema [--dry-run]
```

## Sécurité

- Isolation stricte des données par schéma PostgreSQL
- Validation des noms de schéma pour éviter les injections SQL
- Middleware vérifiant l'accès aux bonnes données
- Tests d'isolation automatisés

## Tests

Exécuter les tests du module :
```bash
python manage.py test multitenant
```

Test complet de configuration :
```bash
python test_multitenant_setup.py
```

## Prochaines étapes

1. Configurer le serveur web pour gérer les sous-domaines
2. Implémenter l'intégration Stripe Connect
3. Créer l'interface d'administration des tenants
4. Développer les outils de migration des données existantes