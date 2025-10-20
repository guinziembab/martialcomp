# 🚀 Guide de Déploiement Rapide - Patch Onboarding Production

## 📦 Package créé : `onboarding_patch_production_20251017_000929.tar.gz`

## 🔧 Étapes de déploiement

### 1. Transfert du package
```bash
# Depuis votre machine locale (WSL)
scp onboarding_patch_production_20251017_000929.tar.gz martialcomp-production:/home/martialc/
```

### 2. Connexion au serveur
```bash
ssh martialcomp-production
```

### 3. Extraction et déploiement
```bash
cd /home/martialc
tar -xzf onboarding_patch_production_20251017_000929.tar.gz
cd onboarding_patch_production_20251017_000929
sudo ./deploy_patch.sh
```

## ✅ Ce que fait le patch

1. **Corrige l'erreur 500** lors de la création de club/fédération
2. **Ajoute une gestion d'erreurs robuste** avec try/except
3. **Crée automatiquement le profil utilisateur** si manquant
4. **Initialise les disciplines par défaut** (15 disciplines)
5. **Corrige la redirection dashboard** : `'dashboard:federation'` → `'competitions:dashboard:federations'`
6. **Ajoute une page d'erreur gracieuse** avec code unique

## 📁 Fichiers modifiés

- `apps/competitions/management/commands/init_disciplines.py` - Nouvelle commande
- `apps/competitions/views/onboarding/emergency_views.py` - Vues sécurisées
- `apps/competitions/templates/competitions/onboarding/error.html` - Page d'erreur
- `apps/competitions/urls/onboarding.py` - URLs modifiées

## 🔍 Vérification après déploiement

### Test rapide
```bash
# Vérifier les disciplines
cd /home/martialc/martialcomp
python manage.py shell
```

```python
from apps.competitions.models import Discipline
print(f"Disciplines actives: {Discipline.objects.filter(is_active=True).count()}")
exit()
```

### URLs à tester
- https://app.martialcomp.com/competitions/onboarding/
- https://app.martialcomp.com/competitions/onboarding/club/creation/
- https://app.martialcomp.com/competitions/onboarding/federation/

## 🔄 Rollback si nécessaire

Les backups sont créés automatiquement. Pour restaurer :
```bash
# Les backups sont dans /home/martialc/backups/onboarding_*
ls -la /home/martialc/backups/onboarding_*

# Restaurer si besoin
cp /home/martialc/backups/onboarding_*/emergency_views.py /home/martialc/martialcomp/apps/competitions/views/onboarding/
cp /home/martialc/backups/onboarding_*/onboarding.py /home/martialc/martialcomp/apps/competitions/urls/
touch /home/martialc/martialcomp/tmp/restart.txt
```

## 📊 Logs à surveiller

```bash
# Logs Django
tail -f /var/log/martialcomp/django.log

# Logs Passenger
tail -f /var/log/passenger/passenger.log
```

## ⚡ Commandes utiles

```bash
# Redémarrer Passenger
touch /home/martialc/martialcomp/tmp/restart.txt

# Vérifier le statut
ps aux | grep passenger
```

## 🎯 Résultat attendu

Après le déploiement :
- ✅ Plus d'erreur 500 sur l'onboarding
- ✅ Création de club/fédération fonctionnelle
- ✅ Redirection correcte vers le dashboard
- ✅ Messages d'erreur user-friendly
- ✅ Logs détaillés pour debugging