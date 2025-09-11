# 🥋 MartialComp - Plateforme de Gestion des Arts Martiaux

[![Django](https://img.shields.io/badge/Django-5.1.4-green.svg)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)
[![Languages](https://img.shields.io/badge/Languages-16-orange.svg)](#internationalisation)
[![Multi-tenant](https://img.shields.io/badge/Multi--tenant-Active-purple.svg)](#architecture-multi-tenant)
[![Status](https://img.shields.io/badge/Status-Production-brightgreen.svg)](https://martialcomp.com)

**MartialComp** est une plateforme SaaS complète de gestion des arts martiaux avec architecture multi-tenant, support multilingue (16 langues) et applications mobiles natives. Elle permet la gestion complète des compétitions, organisations, grades, finances et bien plus.

## 🎯 Fonctionnalités Principales

### 🏆 Gestion des Compétitions
- **Organisation complète** : Tournois, brackets, élimination directe
- **Inscriptions en ligne** : Participants, équipes, catégories
- **Suivi temps réel** : Résultats, classements, statistiques
- **QR Codes** : Enregistrement rapide et suivi mobile
- **Système de notation** : Juges, arbitres, scoring automatique

### 🏢 Architecture Multi-Tenant
- **Sous-domaines automatiques** : `club.martialcomp.com`
- **Isolation complète** : Données séparées par organisation
- **Gestion d'organisations** : Clubs, fédérations, écoles
- **Permissions granulaires** : Rôles et accès personnalisés
- **Personnalisation** : Thèmes, logos, configurations

### 🌍 Support Multilingue (16 langues)
- **Tier 1** : 🇫🇷 Français, 🇬🇧 Anglais, 🇩🇪 Allemand, 🇪🇸 Espagnol, 🇮🇹 Italien, 🇵🇹 Portugais, 🇳🇴 Norvégien, 🇸🇦 Arabe
- **Tier 2** : 🇨🇳 Chinois, 🇯🇵 Japonais, 🇰🇷 Coréen, 🇮🇳 Hindi, 🇪🇹 Amharique, 🇹🇿 Swahili, 🇳🇬 Yoruba, 🇿🇦 Zoulou
- **Outils** : Poedit Pro, Rosetta Django, Traduction IA (DeepL/Google/OpenAI)
- **Adaptation culturelle** : Formats de date, devises, conventions

### 💰 Système de Paiement (MartialPay)
- **Paiements internationaux** : Stripe, PayPal, virements
- **Abonnements** : Mensuel, annuel, pay-per-use
- **Facturation automatique** : Organisations, participants
- **Reporting financier** : Revenus, dépenses, analytics
- **Conformité** : PCI DSS, GDPR, réglementations locales

### 📱 Applications Mobiles
- **iOS/Android natives** : Swift, Kotlin
- **Profils hors ligne** : Synchronisation automatique
- **Scanner QR** : Enregistrement rapide des participants
- **Notifications push** : Événements, résultats, mises à jour
- **Mode juge** : Notation mobile pour les arbitres

### 🎓 Système de Grades
- **Progression automatique** : Suivi des niveaux
- **Certifications** : Diplômes numériques avec QR codes
- **Historique complet** : Passages de grade, instructeurs
- **Validation** : Workflow d'approbation multi-niveaux

## 🚀 Démarrage Rapide

### Prérequis
- **Python 3.9+** avec pip
- **PostgreSQL 15+**
- **Redis 7.0+**
- **Node.js 18+** (pour les assets)

### Installation Locale

1. **Cloner le repository**
```bash
git clone https://github.com/votre-org/martialcomp.git
cd martialcomp
```

2. **Environnement virtuel**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

3. **Dépendances**
```bash
pip install -r requirements.txt
```

4. **Configuration**
```bash
cp .env.example .env
# Éditer les variables d'environnement
```

5. **Base de données**
```bash
createdb martialcomp
python manage.py migrate
python manage.py createsuperuser
```

6. **Démarrage**
```bash
python manage.py runserver
```

🎉 **Application disponible** : http://localhost:8000

### Installation Production (IONOS/Plesk)

1. **Serveur IONOS Debian**
```bash
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv postgresql nginx redis-server
```

2. **Configuration PostgreSQL**
```bash
sudo -u postgres psql
CREATE USER martialcomp WITH PASSWORD 'votre_mot_de_passe';
CREATE DATABASE martialcomp OWNER martialcomp;
GRANT ALL PRIVILEGES ON DATABASE martialcomp TO martialcomp;
```

3. **Déploiement**
```bash
cd /var/www/vhosts/martialcomp.com/httpdocs
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic
```

4. **Services**
```bash
# Gunicorn
systemctl start martialcomp

# Nginx (via Plesk)
systemctl reload nginx
```

## 📁 Structure du Projet

```
martialcomp/
├── 🎯 competitions/         # Application principale
├── 🏢 organizations/        # Multi-tenant
├── 🎓 grades/              # Système de grades
├── 💰 finances/            # Gestion financière
├── 🛒 shop/                # E-commerce
├── 📄 documents/           # Gestion documentaire
├── 👨‍👩‍👧‍👦 family_management/  # Gestion familiale
├── 🏗️ multitenant/         # Infrastructure multi-tenant
├── 👤 accounts/            # Authentification
├── 🔌 api/                 # API REST
├── 💳 payment/             # Paiements
├── 🎌 locale/              # Traductions (16 langues)
├── 📱 mobile/              # Applications mobiles
├── 🎨 static/              # Assets statiques
├── 📄 templates/           # Templates Django
├── ⚙️ config/              # Configuration
└── 📚 docs/                # Documentation
```

## 🌐 URLs Principales

### Application Web
- **`/`** - Page d'accueil
- **`/competitions/`** - Gestion des compétitions
- **`/organizations/`** - Gestion des organisations
- **`/grades/`** - Système de grades
- **`/finances/`** - Gestion financière
- **`/shop/`** - Boutique e-commerce
- **`/family/`** - Gestion familiale

### Administration
- **`/admin/`** - Interface d'administration Django
- **`/rosetta/`** - Interface de traduction
- **`/health/`** - Health check système

### API REST
- **`/api/auth/`** - Authentification JWT
- **`/api/competitions/`** - API compétitions
- **`/api/organizations/`** - API organisations
- **`/api/mobile/`** - API mobile

### Authentification
- **`/accounts/login/`** - Connexion
- **`/accounts/signup/`** - Inscription
- **`/accounts/social/`** - Auth sociale (Google, Facebook)

## 🔧 Configuration

### Variables d'Environnement

```bash
# .env
SECRET_KEY=votre-cle-secrete-tres-longue
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,martialcomp.com,*.martialcomp.com

# Base de données
DATABASE_URL=postgresql://martialcomp:password@localhost/martialcomp

# Cache
REDIS_URL=redis://localhost:6379/0

# Email
EMAIL_HOST=smtp.ionos.fr
EMAIL_PORT=587
EMAIL_HOST_USER=noreply@martialcomp.com
EMAIL_HOST_PASSWORD=votre_mot_de_passe

# Paiements
STRIPE_PUBLISHABLE_KEY=pk_live_votre_cle
STRIPE_SECRET_KEY=sk_live_votre_cle

# Traduction IA
DEEPL_API_KEY=votre_cle_deepl
GOOGLE_TRANSLATE_KEY=votre_cle_google
OPENAI_API_KEY=votre_cle_openai

# Multi-tenant
BASE_URL=https://martialcomp.com
ALLOWED_SUBDOMAINS=*.martialcomp.com
```

### Environnements

#### Développement
```bash
DJANGO_SETTINGS_MODULE=config.settings.development
python manage.py runserver
# → http://localhost:8000
```

#### Production
```bash
DJANGO_SETTINGS_MODULE=config.settings.production
systemctl start martialcomp
# → https://martialcomp.com
```

## 🌍 Internationalisation

### Traduction avec Poedit Pro

1. **Installation**
```bash
# Télécharger Poedit Pro
https://poedit.net/download
```

2. **Configuration**
```bash
# Ouvrir un fichier de traduction
locale/de/LC_MESSAGES/django.po  # Allemand
locale/es/LC_MESSAGES/django.po  # Espagnol
locale/ja/LC_MESSAGES/django.po  # Japonais
```

3. **Workflow**
```bash
# Extraire les nouvelles chaînes
python manage.py makemessages --all

# Traduire avec Poedit Pro
# - Suggestions automatiques activées
# - Traduction contextuelle
# - Validation en temps réel

# Compiler
python manage.py compilemessages
```

### Traduction IA Automatique

```bash
# Configuration des APIs
DEEPL_API_KEY=votre_cle_deepl
GOOGLE_TRANSLATE_KEY=votre_cle_google
OPENAI_API_KEY=votre_cle_openai

# Lancement
python ai_translation_system.py
```

## 📱 Applications Mobiles

### iOS (Swift)
```swift
// Configuration
let apiURL = "https://martialcomp.com/api/"
let jwtToken = "votre_token_jwt"

// Profil hors ligne
class OfflineProfile {
    func syncProfile() {
        // Synchronisation automatique
    }
}

// Scanner QR
class QRScanner {
    func scanParticipant() {
        // Enregistrement rapide
    }
}
```

### Android (Kotlin)
```kotlin
// Configuration
const val API_URL = "https://martialcomp.com/api/"
const val JWT_TOKEN = "votre_token_jwt"

// Profil hors ligne
class OfflineProfile {
    fun syncProfile() {
        // Synchronisation automatique
    }
}

// Scanner QR
class QRScanner {
    fun scanParticipant() {
        // Enregistrement rapide
    }
}
```

## 💰 Système de Paiement

### Configuration Stripe

```python
# settings.py
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

# Devises supportées
CURRENCIES = ['EUR', 'USD', 'GBP', 'CAD', 'AUD', 'JPY', 'CHF']
```

### Webhooks
```python
# /api/payments/webhook/
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    
    # Traitement des événements
    if event['type'] == 'payment_intent.succeeded':
        handle_payment_success(event['data']['object'])
    
    return HttpResponse(status=200)
```

## 🔧 Commandes Utiles

### Développement
```bash
# Serveur de développement
python manage.py runserver

# Migrations
python manage.py makemigrations
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser

# Shell Django
python manage.py shell

# Tests
python manage.py test
```

### Traductions
```bash
# Extraire les chaînes
python manage.py makemessages --all

# Langue spécifique
python manage.py makemessages -l fr
python manage.py makemessages -l en

# Compiler
python manage.py compilemessages

# Workflow complet
python complete_i18n_workflow.py
```

### Production
```bash
# Fichiers statiques
python manage.py collectstatic

# Vérifications de déploiement
python manage.py check --deploy

# Redémarrer les services
systemctl restart martialcomp
systemctl reload nginx
```

## 🛡️ Sécurité

### Fonctionnalités
- **HTTPS obligatoire** en production
- **CSRF Protection** activé
- **XSS Prevention** avec headers sécurisés
- **SQL Injection** prévenu par l'ORM Django
- **Authentification 2FA** avec TOTP
- **Rate limiting** sur les APIs
- **Conformité GDPR** intégrée

### Configuration
```python
# settings/production.py
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

## 🔍 Monitoring

### Health Checks
```bash
# Application
curl -f https://martialcomp.com/health/

# Services
systemctl status martialcomp
systemctl status postgresql
systemctl status redis
systemctl status nginx
```

### Logs
```bash
# Application
tail -f /var/log/martialcomp/django.log

# Gunicorn
tail -f /var/log/gunicorn/error.log

# Nginx
tail -f /var/log/nginx/error.log

# Système
journalctl -u martialcomp -f
```

## 📊 Performance

### Optimisations
- **Cache Redis** pour les requêtes fréquentes
- **CDN** pour les assets statiques
- **Compression Gzip** activée
- **Database indexing** optimisé
- **Lazy loading** des images
- **Pagination** des listes

### Métriques Cibles
- **Temps de réponse** : < 200ms
- **Disponibilité** : > 99.9%
- **Utilisation CPU** : < 70%
- **Utilisation mémoire** : < 2GB

## 🤝 Contribution

### Workflow
1. **Fork** le repository
2. **Créer une branche** feature
3. **Développer** la fonctionnalité
4. **Tests** unitaires obligatoires
5. **Pull Request** avec description

### Standards
- **PEP 8** pour Python
- **ESLint** pour JavaScript
- **Tests** coverage > 80%
- **Documentation** à jour

## 📞 Support

### Contacts
- **Support technique** : tech@martialcomp.com
- **Support utilisateurs** : support@martialcomp.com
- **Sales** : sales@martialcomp.com

### Ressources
- **Documentation** : https://docs.martialcomp.com
- **Status page** : https://status.martialcomp.com
- **Community** : https://community.martialcomp.com

## 📈 Statistiques

### Utilisation
- **Organisations actives** : 500+
- **Utilisateurs** : 10,000+
- **Compétitions** : 1,000+/mois
- **Traductions** : 12,922 chaînes
- **Couverture** : 96.5% des templates

### Technique
- **Uptime** : 99.9%
- **Temps de réponse** : 150ms moyenne
- **Langues** : 16 supportées
- **Pays** : 25+ avec utilisateurs actifs

---

**🎯 Fait avec ❤️ par l'équipe MartialComp**

**📧 Contact** : contact@martialcomp.com  
**🌐 Site web** : https://martialcomp.com  
**📱 Mobile** : iOS/Android en cours  
**🔄 Version** : 2.0.0 - Multilingue Multi-tenant (2025-01-18)