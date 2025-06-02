# 🎯 Prochaines Étapes - Déploiement MartialComp

## ✅ Statut Actuel
- **Connexion SSH** : ✅ Confirmée (root@212.227.78.104)
- **Mot de passe** : ✅ Vérifié (AQWZSX123ok,)
- **Environnement local** : ✅ Préparé
- **Guides de déploiement** : ✅ Créés

## 🚀 Actions Immédiates à Effectuer

### 1. Finaliser la Configuration Locale (15 min)

#### A. Compléter le fichier .env.production
```bash
# Éditer le fichier .env.production
nano .env.production

# OBLIGATOIRE : Remplacer ces valeurs
EMAIL_HOST_PASSWORD=CHANGEZ_MOT_DE_PASSE_EMAIL_ICI
STRIPE_PUBLIC_KEY=pk_live_your_stripe_public_key
STRIPE_SECRET_KEY=sk_live_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
```

#### B. Créer un Repository Git Privé
```bash
# 1. Aller sur GitHub/GitLab
# 2. Créer un repository privé : martialcomp-production
# 3. Cloner et pousser le code :

git init
git add .
git commit -m "MartialComp - Production ready"
git remote add origin https://github.com/VOTRE-USERNAME/martialcomp-production.git
git push -u origin main
```

### 2. Première Connexion Serveur (10 min)

#### Vérifications Essentielles
```bash
# Se connecter au serveur
ssh root@212.227.78.104

# Vérifier l'environnement
cd /var/www/vhosts/martialcomp.com/
ls -la

# Vérifier Python
python3 --version
pip3 --version

# Vérifier PostgreSQL
systemctl status postgresql

# Vérifier la base de données
sudo -u postgres psql -c "\l" | grep martial
```

### 3. Configuration Préliminaire (20 min)

#### A. Créer l'Environnement Virtuel
```bash
cd /var/www/vhosts/martialcomp.com/
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

#### B. Créer la Structure de Répertoires
```bash
mkdir -p /var/www/vhosts/martialcomp.com/{logs,backups,media,staticfiles}
chown -R martialcomp:psacln /var/www/vhosts/martialcomp.com/
chmod 755 /var/www/vhosts/martialcomp.com/{logs,backups,media,staticfiles}
```

#### C. Configurer la Base de Données
```bash
# Se connecter à PostgreSQL
sudo -u postgres psql

# Créer la base et l'utilisateur (si pas déjà fait)
CREATE DATABASE martialcomp_db;
CREATE USER martialcomp_user WITH PASSWORD 'AQWZSX123ok,';
GRANT ALL PRIVILEGES ON DATABASE martialcomp_db TO martialcomp_user;
\q
```

### 4. Configuration Email Ionos (25 min)

#### A. Créer les Adresses Email dans Plesk
```bash
# 1. Aller sur https://212.227.78.104:8443
# 2. Connectez-vous à Plesk
# 3. Aller dans : Mail > Adresses Email
# 4. Créer ces adresses :

noreply@martialcomp.com (mot de passe fort)
admin@martialcomp.com (mot de passe fort)
support@martialcomp.com (mot de passe fort)
```

#### B. Tester l'Email SMTP
```bash
# Test basique avec telnet
telnet smtp.ionos.fr 587

# Ou utiliser un script Python pour tester
```

### 5. Configuration Stripe (30 min)

#### A. Compte Stripe
```bash
# 1. Aller sur https://stripe.com
# 2. Créer un compte business
# 3. Compléter la vérification KYC
# 4. Activer le mode Live
```

#### B. Récupérer les Clés API
```bash
# Dans Stripe Dashboard > Developers > API keys
# Noter :
# - Publishable key (pk_live_...)
# - Secret key (sk_live_...)
```

#### C. Configurer les Webhooks
```bash
# Créer un endpoint webhook :
# URL: https://martialcomp.com/stripe/webhook/
# Événements: payment_intent.succeeded, customer.subscription.*
```

## 📋 Ordre d'Exécution Recommandé

### Phase 1 : Préparation (45 min)
1. Finaliser .env.production avec tous les secrets
2. Créer repository Git et pousser le code
3. Configurer Stripe (compte + clés API)
4. Créer adresses email dans Plesk

### Phase 2 : Déploiement Initial (90 min)
1. Suivre le `DEPLOYMENT_EXECUTION_GUIDE.md`
2. Exécuter phases 2-4 (serveur + application + DB)
3. Configurer Plesk Python application
4. Tester l'accès de base

### Phase 3 : Configuration Avancée (45 min)
1. Configurer SSL avec Let's Encrypt
2. Tester les emails
3. Tester les paiements Stripe
4. Exécuter la checklist sécurité

## 🔧 Outils et Ressources

### Guides Créés
- `DEPLOYMENT_EXECUTION_GUIDE.md` - Guide principal
- `STRIPE_CONFIGURATION_GUIDE.md` - Configuration paiements
- `EMAIL_SMTP_CONFIGURATION.md` - Configuration email
- `SECURITY_PRODUCTION_CHECKLIST.md` - Sécurité

### Scripts Utiles
- `deploy_production.sh` - Script de déploiement automatisé
- `.env.production` - Configuration environnement

### URLs Importantes
- **Plesk** : https://212.227.78.104:8443
- **Site futur** : https://martialcomp.com
- **Admin Django** : https://martialcomp.com/admin/

## 🆘 Support

### En Cas de Problème
1. Vérifier les logs : `/var/www/vhosts/martialcomp.com/logs/`
2. Consulter les guides de dépannage
3. Tester les connexions (DB, email, etc.)

### Contacts
- **Support Ionos** : 24/7 disponible
- **Documentation Django** : https://docs.djangoproject.com/

## 🎯 Objectif Final

**Site accessible** : https://martialcomp.com
**Admin fonctionnel** : https://martialcomp.com/admin/
**Paiements actifs** : Via Stripe
**Emails opérationnels** : Via SMTP Ionos

---

**💡 CONSEIL** : Procéder étape par étape et tester chaque phase avant de passer à la suivante.

**⏱️ TEMPS TOTAL ESTIMÉ** : 3-4 heures pour un déploiement complet.