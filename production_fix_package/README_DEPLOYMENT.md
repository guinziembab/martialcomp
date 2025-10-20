# 🚨 GUIDE DE DÉPLOIEMENT - CORRECTIONS PRACTITIONER

## 📋 Résumé du Problème
- **Erreur** : `DoesNotExist: Discipline matching query does not exist.`
- **URL** : `https://martialcomp.com/fr/admin/competitions/practitioner/`
- **Impact** : Erreur serveur 500 empêchant l'accès à l'interface d'administration

## 📦 Contenu du Package

### Fichiers Principaux
- `production.py` - Settings Django modifiés avec middleware et corrections
- `admin_override.py` - Désinscription du modèle Practitioner de l'admin
- `install_production_fix.sh` - Script d'installation automatisé
- `test_practitioner_fix.py` - Script de test des corrections
- `.htaccess_production_fix` - Redirections Apache de backup

### Scripts de Support
- `deploy_urgent_fix.sh` - Script de déploiement original
- `README_DEPLOYMENT.md` - Ce guide

## 🚀 Instructions de Déploiement

### Étape 1: Transfert vers le Serveur

#### Option A: Transfert par SCP/SFTP
```bash
# Depuis votre machine locale
scp -r production_fix_package/ user@martialcomp.com:/tmp/

# Ou avec SFTP
sftp user@martialcomp.com
put -r production_fix_package/
```

#### Option B: Transfert par Plesk File Manager
1. Se connecter à Plesk
2. Aller dans "Fichiers" → "httpdocs"
3. Créer un dossier `production_fix_package`
4. Uploader tous les fichiers du package

#### Option C: Création directe sur le serveur
```bash
# Se connecter au serveur
ssh user@martialcomp.com

# Aller dans le répertoire de production
cd /var/www/vhosts/martialcomp.com/httpdocs

# Créer le dossier
mkdir -p production_fix_package
```

### Étape 2: Installation Automatisée

```bash
# Se connecter au serveur
ssh user@martialcomp.com

# Aller dans le répertoire de production
cd /var/www/vhosts/martialcomp.com/httpdocs

# Copier le package (si transféré dans /tmp)
cp -r /tmp/production_fix_package ./

# Aller dans le dossier du package
cd production_fix_package

# Exécuter l'installation
chmod +x install_production_fix.sh
./install_production_fix.sh
```

### Étape 3: Vérification

#### Tests Automatiques
Le script d'installation exécute automatiquement :
- ✅ Validation de la configuration Django
- ✅ Redémarrage d'Apache
- ✅ Tests des corrections

#### Tests Manuels
1. **Accès direct** : `https://martialcomp.com/fr/admin/competitions/practitioner/`
   - Doit rediriger vers `https://martialcomp.com/fr/admin/`
   - Status code : 301 ou 302

2. **Interface d'administration** : `https://martialcomp.com/fr/admin/`
   - Doit être accessible sans erreur
   - Practitioner ne doit pas apparaître dans la liste

## 🔧 Installation Manuelle (si nécessaire)

Si le script automatisé échoue, voici les étapes manuelles :

### 1. Sauvegarde
```bash
cd /var/www/vhosts/martialcomp.com/httpdocs
mkdir -p /var/backups/martialcomp_before_fix_$(date +%Y%m%d_%H%M%S)
cp config/settings/production.py /var/backups/martialcomp_before_fix_*/
cp .htaccess /var/backups/martialcomp_before_fix_*/
```

### 2. Installation des fichiers
```bash
# Settings Django
cp production.py config/settings/production.py

# Admin override
mkdir -p apps/competitions/
cp admin_override.py apps/competitions/admin_override.py

# Redirections Apache
cat .htaccess_production_fix >> .htaccess
```

### 3. Vérification et redémarrage
```bash
# Test configuration
python3 manage.py check --settings=config.settings.production

# Redémarrage Apache
systemctl restart apache2

# Test des corrections
python3 test_practitioner_fix.py
```

## 📊 Monitoring Post-Déploiement

### Logs à Surveiller
```bash
# Logs Apache
tail -f /var/log/apache2/error.log

# Logs Django
tail -f /var/log/django/martialcomp.log

# Statut Apache
systemctl status apache2
```

### Commandes de Vérification
```bash
# Test de la configuration Django
python3 manage.py check --settings=config.settings.production

# Test des corrections
python3 test_practitioner_fix.py

# Vérification des redirections
curl -I https://martialcomp.com/fr/admin/competitions/practitioner/
```

## 🆘 En Cas de Problème

### Restauration Rapide
```bash
# Restaurer depuis la sauvegarde
cp /var/backups/martialcomp_before_fix_*/production.py config/settings/production.py
cp /var/backups/martialcomp_before_fix_*/.htaccess .htaccess
systemctl restart apache2
```

### Diagnostic
```bash
# Vérifier les erreurs Apache
tail -n 50 /var/log/apache2/error.log

# Vérifier la configuration Django
python3 manage.py check --settings=config.settings.production

# Tester les URLs
curl -v https://martialcomp.com/fr/admin/competitions/practitioner/
```

### Contact Support
Si les problèmes persistent :
- Vérifier les permissions des fichiers
- Contacter l'équipe de développement
- Consulter les logs détaillés

## ✅ Checklist de Déploiement

- [ ] Package transféré sur le serveur
- [ ] Sauvegarde créée
- [ ] Script d'installation exécuté
- [ ] Configuration Django validée
- [ ] Apache redémarré
- [ ] Tests automatiques réussis
- [ ] Tests manuels effectués
- [ ] Logs vérifiés
- [ ] Site accessible sans erreur

---
**Date de création** : $(date)
**Statut** : ✅ Prêt pour le déploiement
**Prochaine étape** : Exécution du script d'installation