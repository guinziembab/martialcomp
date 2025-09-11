# LaraClassified - Bwatoo Project

## Overview

LaraClassified est un système de gestion de petites annonces (CMS) basé sur Laravel. Ce projet contient la configuration et les modifications nécessaires pour déployer LaraClassified dans l'environnement de développement et de production de Bwatoo.

## Project Structure

```
bwatoo-laraclassified/
├── app/                           # Application Laravel
│   ├── Http/Controllers/         # Contrôleurs de l'application
│   ├── Models/                   # Modèles Eloquent
│   ├── Rules/                    # Règles de validation personnalisées
│   ├── Services/                 # Services métier
│   └── ...
├── config/                       # Configuration Laravel
│   ├── larapen/                  # Configuration spécifique LaraClassified
│   └── ...
├── database/                     # Base de données
│   ├── migrations/               # Migrations de base de données
│   ├── seeders/                  # Seeders pour les données initiales
│   └── ...
├── docs/                         # Documentation du projet
│   ├── README.md                 # Documentation principale
│   ├── META.md                   # Métadonnées du projet
│   ├── TODO.md                   # Liste des tâches
│   ├── DOCKER-GUIDE.md           # Guide Docker
│   └── BYPASS_PURCHASE_CODE.md   # Guide pour bypasser le code d'achat
├── public/                       # Fichiers publics
├── resources/                    # Ressources (vues, assets)
├── routes/                       # Routes de l'application
└── ...
```

## Installation

### Prérequis

- PHP 8.1 ou supérieur
- Composer
- Node.js et NPM
- MySQL 8.0 ou supérieur
- Apache ou Nginx

### Installation locale

1. **Cloner le projet**
   ```bash
   git clone [repository-url]
   cd bwatoo-laraclassified
   ```

2. **Installer les dépendances**
   ```bash
   composer install
   npm install
   ```

3. **Configuration de l'environnement**
   ```bash
   cp .env.example .env
   php artisan key:generate
   ```

4. **Configuration de la base de données**
   - Créer une base de données MySQL
   - Configurer les paramètres dans `.env`
   - Exécuter les migrations : `php artisan migrate`

5. **Démarrer le serveur de développement**
   ```bash
   php artisan serve
   ```

### Installation avec Docker

#### Prérequis Docker
- Docker Desktop installé
- Docker Compose installé
- Au moins 4GB de RAM disponible

#### Configuration Docker

**Structure des fichiers Docker :**
```
bwatoo-laraclassified/
├── Dockerfile                 # Configuration du container PHP/Apache
├── docker-compose.yml         # Orchestration des services
└── docker/
    ├── apache/
    │   └── laraclassified.conf # Configuration Apache
    ├── mysql/
    │   └── init.sql           # Script d'initialisation DB
    └── php/
        └── php.ini            # Configuration PHP
```

**Services Docker :**
- **Application** : PHP 8.2 + Apache (Port 8000)
- **Base de données** : MySQL 8.0 (Port 3306)
- **phpMyAdmin** : Interface web MySQL (Port 8080)
- **Redis** : Cache et sessions (Port 6379)
- **MailHog** : Test des emails (Port 8025)

#### Installation Docker étape par étape

1. **Préparer l'environnement**
   ```bash
   # Créer le fichier .env
   cp .env.example .env
   
   # Configurer les variables pour Docker
   DB_CONNECTION=mysql
   DB_HOST=db
   DB_PORT=3306
   DB_DATABASE=laraclassified
   DB_USERNAME=laraclassified
   DB_PASSWORD=password
   
   CACHE_DRIVER=redis
   SESSION_DRIVER=redis
   REDIS_HOST=redis
   REDIS_PORT=6379
   
   MAIL_MAILER=smtp
   MAIL_HOST=mailhog
   MAIL_PORT=1025
   ```

2. **Construire et démarrer les containers**
   ```bash
   # Construire les images
   docker-compose build
   
   # Démarrer les services
   docker-compose up -d
   
   # Vérifier le statut
   docker-compose ps
   ```

3. **Configuration de l'application**
   ```bash
   # Générer la clé d'application
   docker-compose exec app php artisan key:generate
   
   # Exécuter les migrations
   docker-compose exec app php artisan migrate
   
   # Créer le lien symbolique pour le storage
   docker-compose exec app php artisan storage:link
   ```

#### Accès aux services Docker

- **Application** : http://localhost:8000
- **phpMyAdmin** : http://localhost:8080 (root/rootpassword)
- **MailHog** : http://localhost:8025
- **Redis** : localhost:6379

#### Commandes Docker utiles

```bash
# Démarrer/arrêter les services
docker-compose up -d
docker-compose down

# Voir les logs
docker-compose logs -f app

# Accéder au container
docker-compose exec app bash

# Commandes Laravel
docker-compose exec app php artisan migrate
docker-compose exec app php artisan tinker

# Sauvegarder la base de données
docker-compose exec db mysqldump -u root -p laraclassified > backup.sql
```

### Déploiement sur serveur

1. **Serveur de développement** : `dev.bwatoo.com`
2. **Serveur de production** : `bwatoo.com`

## Configuration

### Variables d'environnement importantes

#### Développement local
```env
APP_NAME=LaraClassified
APP_ENV=local
APP_KEY=base64:...
APP_DEBUG=true
APP_URL=http://localhost

DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=laraclassified
DB_USERNAME=root
DB_PASSWORD=

#### Serveur de développement (dev.bwatoo.com)
```env
DB_CONNECTION=mysql
DB_HOST=localhost
DB_PORT=3306
DB_DATABASE=admin_btlara
DB_USERNAME=admin_lara
DB_PASSWORD=AQWZSX123ok,
DB_CHARSET=utf8mb3
DB_COLLATION=utf8mb3_general_ci

MAIL_MAILER=smtp
MAIL_HOST=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_ENCRYPTION=tls
```

### Configuration LaraClassified

LaraClassified utilise des fichiers de configuration spécifiques dans `config/larapen/` :

- `core.php` : Configuration principale
- `admin.php` : Configuration du panel d'administration
- `options.php` : Options et paramètres
- `routes.php` : Configuration des routes

## Fonctionnalités

### Fonctionnalités principales

- **Gestion des annonces** : Création, modification, suppression d'annonces
- **Système de catégories** : Organisation hiérarchique des annonces
- **Géolocalisation** : Recherche par localisation
- **Système de paiement** : Intégration PayPal et autres moyens de paiement
- **Panel d'administration** : Interface d'administration complète
- **Multilingue** : Support de plusieurs langues
- **Responsive Design** : Interface adaptée mobile

### Plugins disponibles

#### **Plugins natifs**
- **PayPal** : Intégration des paiements PayPal
- **Reviews** : Système d'avis et de notation
- **Domainmapping** : Gestion des domaines personnalisés

#### **Plugins personnalisés développés**
- **CreditSystem** : ✅ INSTALLÉ ET OPÉRATIONNEL
  - **Status** : Plugin détecté, installé et activé avec succès
  - **Architecture** : Respect total des normes LaraClassified
  - **Base de données** : 4 tables créées automatiquement
    - `user_credits` - Portefeuille utilisateur
    - `credit_transactions` - Historique transactions
    - `credit_packages` - Packs de crédits (3 packs par défaut)
    - `revenue_sources` - Sources revenus (AdMob, Gaming)
  - **Fonctionnalités prêtes** :
    - Système de détection automatique
    - Installation via interface LaraClassified
    - Données par défaut (Starter 1000, Standard 5000, Premium 12000 crédits)
    - Configuration flexible via config.php
  - **À développer** :
    - Interface utilisateur pour portefeuille
    - Intégration PayPal/Stripe pour achats
    - Mini-jeux et challenges
    - Revenus AdMob

- **AdvancedPromotions** : En attente de développement
  - Bump-up : Remonter les annonces
  - Featured : Annonces vedettes
  - Top : Priorité en haut de catégorie
  - Urgent : Badge urgent rouge
  - Intégration seamless avec système existant

## Développement

### Modifications apportées

1. **Bypass du code d'achat pour le développement**
   - Modification de `app/Rules/PurchaseCodeRule.php`
   - Permet l'installation sans code d'achat valide

2. **Configuration Docker**
   - Dockerfile personnalisé pour l'environnement
   - Docker-compose pour les services

3. **Plugin CreditSystem développé avec succès**
   - **Structure** : `/extras/plugins/creditsystem/`
   - **Fichiers créés** :
     - `init.json` - Métadonnées du plugin
     - `Creditsystem.php` - Classe principale
     - `CreditsystemServiceProvider.php` - Service provider
     - `config.php` - Configuration flexible
     - `routes/web.php` - Routes utilisateur et admin
     - `database/migrations/` - 4 migrations pour les tables
   - **Respect architecture LaraClassified** : Aucune modification du code core
   - **Installation réussie** : Tables créées automatiquement, données par défaut insérées

## Bypass du code d'achat (Développement uniquement)

### ⚠️ Important
Cette modification est **UNIQUEMENT** pour l'environnement de développement. Le code d'achat valide **DOIT** être restauré en production.

### Méthode 1 : Modifier PurchaseCodeRule (Recommandée)

**Fichier** : `app/Rules/PurchaseCodeRule.php`
**Méthode** : `passes()`
**Ligne** : 52-74

```php
// Code original
public function passes(string $attribute, mixed $value): bool
{
    $value = getAsString($value);
    
    // Check the purchase code
    $purchaseCodeData = $this->purchaseCodeChecker($value);
    $isValid = data_get($purchaseCodeData, 'valid');
    $doesPurchaseCodeIsValid = (is_bool($isValid) && $isValid == true);
    
    // Retrieve the error message
    if (!$doesPurchaseCodeIsValid) {
        $errorMessage = data_get($purchaseCodeData, 'message');
        $errorMessage = !empty($errorMessage) ? ' ERROR: <span class="fw-bold">' . $errorMessage . '</span>' : '';
        $this->errorMessage .= $errorMessage;
    }
    
    return $doesPurchaseCodeIsValid;
}

// Code modifié pour le développement
public function passes(string $attribute, mixed $value): bool
{
    // Bypass purchase code validation for development
    return true;
    
    /*
    $value = getAsString($value);
    
    // Check the purchase code
    $purchaseCodeData = $this->purchaseCodeChecker($value);
    $isValid = data_get($purchaseCodeData, 'valid');
    $doesPurchaseCodeIsValid = (is_bool($isValid) && $isValid == true);
    
    // Retrieve the error message
    if (!$doesPurchaseCodeIsValid) {
        $errorMessage = data_get($purchaseCodeData, 'message');
        $errorMessage = !empty($errorMessage) ? ' ERROR: <span class="fw-bold">' . $errorMessage . '</span>' : '';
        $this->errorMessage .= $errorMessage;
    }
    
    return $doesPurchaseCodeIsValid;
    */
}
```

### Méthode 2 : Mock de l'URL de validation

**Fichier** : `config/larapen/core.php`
**Ligne** : 39

```php
// Original
'purchaseCodeCheckerUrl' => 'https://api.bedigit.com/envato.php?purchase_code=',

// Modifié pour pointer vers un mock local
'purchaseCodeCheckerUrl' => 'http://localhost/mock-validation.php?purchase_code=',
```

**Créer un fichier mock** : `public/mock-validation.php`
```php
<?php
header('Content-Type: application/json');
echo json_encode(['valid' => true, 'message' => 'Mock validation for development']);
?>
```

### Méthode 3 : Supprimer la validation dans la request

**Fichier** : `app/Http/Requests/Setup/Install/SiteInfoRequest.php`
**Ligne** : 92

```php
// Original
$this->appInput . 'purchase_code' => ['required', new PurchaseCodeRule(config('larapen.core.item.id'))],

// Modifié - Commenter ou supprimer la ligne
// $this->appInput . 'purchase_code' => ['required', new PurchaseCodeRule(config('larapen.core.item.id'))],
```

### Comparaison des méthodes

| Méthode | Complexité | Réversibilité | Sécurité Dev |
|---------|------------|---------------|--------------|
| 1. Modifier PurchaseCodeRule | Faible | Excellente | Élevée |
| 2. Mock URL | Moyenne | Bonne | Élevée |
| 3. Supprimer validation | Faible | Moyenne | Moyenne |

### Restauration pour la production

**Important** : Avant le déploiement en production, restaurer le code original :

```bash
# Restaurer le fichier original
git checkout app/Rules/PurchaseCodeRule.php

# Ou manually restaurer le code original
# en supprimant les commentaires et le "return true;"
```

### Tests

```bash
# Exécuter les tests
php artisan test

# Tests spécifiques
php artisan test --filter TestName
```

### Debugging

```bash
# Activer le mode debug
APP_DEBUG=true

# Vider les caches
php artisan cache:clear
php artisan config:clear
php artisan route:clear
php artisan view:clear
```

## Sécurité

### Bonnes pratiques

1. **Environnement de production** :
   - `APP_DEBUG=false`
   - `APP_ENV=production`
   - HTTPS activé

2. **Base de données** :
   - Utilisateur MySQL dédié avec privilèges limités
   - Sauvegardes régulières

3. **Fichiers** :
   - Permissions correctes (755 pour les dossiers, 644 pour les fichiers)
   - `.env` non accessible publiquement

### Sauvegardes

```bash
# Sauvegarde de la base de données
php artisan backup:run

# Sauvegarde manuelle
mysqldump -u username -p database_name > backup.sql
```

## Maintenance

### Tâches courantes

1. **Mise à jour des dépendances** :
   ```bash
   composer update
   npm update
   ```

2. **Nettoyage des logs** :
   ```bash
   php artisan log:clear
   ```

3. **Optimisation** :
   ```bash
   php artisan optimize
   php artisan config:cache
   php artisan route:cache
   ```

### Monitoring

- **Logs** : `storage/logs/laravel.log`
- **Erreurs** : Panel d'administration > Système > Logs
- **Performance** : Utilisation de Laravel Telescope (si installé)

## Support

### Documentation officielle

- [LaraClassified Documentation](https://laraclassifier.com)
- [Laravel Documentation](https://laravel.com/docs)

### Contacts

- **Développeur** : [Votre nom]
- **Email** : [email@example.com]
- **Serveur** : dev.bwatoo.com

## Licence

LaraClassified est un produit commercial vendu sur CodeCanyon.
Licence standard CodeCanyon : https://codecanyon.net/licenses/standard

## Changelog

### Version actuelle
- Bypass du système de validation du code d'achat
- Configuration Docker améliorée
- Documentation complète du projet

### Versions précédentes
- Installation initiale de LaraClassified
- Configuration de base pour l'environnement Bwatoo