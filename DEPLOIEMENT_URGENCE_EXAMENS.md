# 🚨 DÉPLOIEMENT D'URGENCE - Erreur 500 Examens

## 🎯 Problème à Résoudre

**URL affectée :** https://martialcomp.com/fr/competitions/federations/3/examens/  
**Erreur :** HTTP 500 Internal Server Error  
**Cause :** Corrections locales non déployées sur le serveur de production

## 📋 Fichiers à Déployer (OBLIGATOIRES)

### 1. 🔧 Vue Federations Corrigée
**Fichier :** `apps/competitions/views/federations.py`  
**Modifications :**
- ✅ Gestion d'erreurs améliorée dans `federation_examens()`
- ✅ Import timezone ajouté
- ✅ Gestion des exceptions ImportError et Exception séparées

### 2. 📄 Template Examens Fonctionnel
**Fichier :** `apps/competitions/templates/competitions/federations/examens/list.html`  
**Modifications :**
- ✅ Extension `"competitions/dashboard/base.html"` au lieu de `"base.html"`
- ✅ Block `dashboard_content` au lieu de `content`
- ✅ Sidebar intégrée supprimée (évite duplication)
- ✅ Interface moderne avec statistiques

### 3. 🔗 URLs Dashboard Complètes
**Fichier :** `apps/competitions/urls/dashboard.py`  
**Modifications :**
- ✅ URL pattern `dashboard_guide` ajouté
- ✅ Correction des erreurs NoReverseMatch

## 🚀 Méthodes de Déploiement

### Option 1: Script Automatique (RECOMMANDÉ)

```bash
# Depuis votre machine locale
./deploy_emergency_fix.sh
```

**Ce script fait :**
- ✅ Sauvegarde automatique des fichiers existants
- ✅ Transfert sécurisé des corrections
- ✅ Correction des migrations
- ✅ Redémarrage des services
- ✅ Test de validation automatique

### Option 2: Déploiement Manuel

```bash
# 1. Connexion au serveur
ssh root@martialcomp.com
cd /var/www/martialcomp

# 2. Sauvegarde de sécurité
mkdir -p backups
tar -czf backups/backup_examens_$(date +%Y%m%d_%H%M%S).tar.gz \
    apps/competitions/views/federations.py \
    apps/competitions/templates/competitions/federations/examens/ \
    apps/competitions/urls/dashboard.py

# 3. Transfert des fichiers (depuis votre machine locale)
scp apps/competitions/views/federations.py root@martialcomp.com:/var/www/martialcomp/apps/competitions/views/federations.py
scp apps/competitions/urls/dashboard.py root@martialcomp.com:/var/www/martialcomp/apps/competitions/urls/dashboard.py
scp apps/competitions/templates/competitions/federations/examens/list.html root@martialcomp.com:/var/www/martialcomp/apps/competitions/templates/competitions/federations/examens/list.html

# 4. Correction des migrations (sur le serveur)
python3 manage.py migrate --fake competitions 0007
rm -f apps/competitions/migrations/0008_remove_*
rm -f apps/competitions/migrations/0009_alter_*
python3 manage.py makemigrations
python3 manage.py migrate

# 5. Redémarrage
python3 manage.py collectstatic --noinput
systemctl restart nginx
systemctl restart gunicorn

# 6. Test
curl -I https://martialcomp.com/fr/competitions/federations/3/examens/
```

## 🧪 Tests de Validation

Après le déploiement, vérifier :

### ✅ URLs à Tester
- **Examens :** https://martialcomp.com/fr/competitions/federations/3/examens/
- **Documentation :** https://martialcomp.com/fr/competitions/dashboard/documentation/  
- **Dashboard :** https://martialcomp.com/fr/competitions/dashboard/

### ✅ Codes de Réponse Attendus
- **200 OK** - Page se charge correctement
- **302/301** - Redirection (probablement vers login) = Normal si pas connecté
- **❌ 500** - Erreur serveur = Problème persiste

## 🔍 Diagnostic en Cas de Problème

### Logs à Consulter
```bash
# Sur le serveur martialcomp.com
tail -f /var/log/django/martialcomp.log
tail -f /var/log/nginx/error.log
journalctl -u gunicorn -f
```

### Commandes de Debug
```bash
# Test Django
python3 manage.py check
python3 manage.py showmigrations competitions

# Test spécifique à la vue examens
python3 manage.py shell -c "
from apps.competitions.views.federations import federation_examens
from django.test import RequestFactory
from django.contrib.auth.models import User
print('Vue federation_examens importée avec succès')
"
```

## 🏥 Plan de Rollback

En cas de problème critique :

```bash
# Sur le serveur
cd /var/www/martialcomp

# Restaurer la dernière sauvegarde
tar -xzf backups/backup_examens_YYYYMMDD_HHMMSS.tar.gz

# Redémarrer les services
systemctl restart nginx
systemctl restart gunicorn
```

## 📊 Suivi du Déploiement

| Étape | Status | Vérification |
|-------|--------|-------------|
| 🔄 Transfert fichiers | ⏳ En attente | `ls -la apps/competitions/views/federations.py` |
| 🗄️ Migrations | ⏳ En attente | `python3 manage.py showmigrations` |
| 🔄 Redémarrage | ⏳ En attente | `systemctl status gunicorn` |
| 🧪 Test URL | ⏳ En attente | `curl -I https://martialcomp.com/fr/competitions/federations/3/examens/` |

---

**⚠️ IMPORTANT :** Ce déploiement corrige spécifiquement l'erreur 500 sur la page examens. Les corrections d'icônes et autres améliorations seront déployées séparément si nécessaire.

**📞 Support :** En cas de problème, restaurer la sauvegarde et contacter l'équipe technique.