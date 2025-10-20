# Guide de Déploiement Étape par Étape

## 🎯 Objectif
Corriger l'erreur 500 sur le dashboard fédération et vérifier l'état des utilisateurs

## 📋 Pré-requis
- Accès SSH au serveur martialcomp.com
- Les fichiers suivants sont prêts dans votre répertoire local :
  - ✅ `apps/competitions/views/dashboard/federations.py` (46K)
  - ✅ `check_users_production.sh` (3.7K)
  - ✅ `fix_federation_500_error.sh` (4.2K)
  - ✅ `recreate_fedetest1.sh` (4.9K)

---

## 📦 ÉTAPE 1 : Transférer les fichiers vers le serveur

### Option A : Utiliser le script automatique

```bash
bash TRANSFERT_PRODUCTION_URGENT.sh
```

**Si cela fonctionne**, passez directement à l'ÉTAPE 3.

### Option B : Transfert manuel (si l'option A échoue)

Dans votre terminal local (WSL), exécutez :

```bash
# 1. Transfert du fichier corrigé
scp /mnt/c/martial_hub_django/martialcomp/apps/competitions/views/dashboard/federations.py \
    martialcomp.com:~/federations_nouveau.py

# 2. Transfert des scripts
scp /mnt/c/martial_hub_django/martialcomp/check_users_production.sh \
    martialcomp.com:~/check_users.sh

scp /mnt/c/martial_hub_django/martialcomp/recreate_fedetest1.sh \
    martialcomp.com:~/recreate_fedetest1.sh
```

**Résultat attendu** : Les fichiers sont copiés sans erreur

---

## 🔍 ÉTAPE 2 : Se connecter au serveur

```bash
ssh martialcomp.com
```

**Résultat attendu** : Vous êtes connecté au serveur

---

## 👥 ÉTAPE 3 : Vérifier l'état des utilisateurs

```bash
cd ~/
chmod +x check_users.sh
bash check_users.sh
```

**Lisez attentivement la sortie** et notez :
- Nombre total d'utilisateurs : _______
- Utilisateur FEDETEST1 trouvé ? ☐ OUI  ☐ NON
- Si OUI, est-il actif ? ☐ OUI  ☐ NON

**Sauvegardez la sortie** :
```bash
bash check_users.sh > ~/users_report_$(date +%Y%m%d_%H%M%S).txt
```

---

## 🔧 ÉTAPE 4 : Appliquer la correction

### 4.1 Sauvegarder l'ancien fichier

```bash
cd ~/martialcomp
cp apps/competitions/views/dashboard/federations.py \
   apps/competitions/views/dashboard/federations.py.backup_$(date +%Y%m%d_%H%M%S)
```

**Vérifier la sauvegarde** :
```bash
ls -lh apps/competitions/views/dashboard/federations.py.backup_*
```

### 4.2 Copier le nouveau fichier

```bash
cp ~/federations_nouveau.py \
   ~/martialcomp/apps/competitions/views/dashboard/federations.py
```

### 4.3 Vérifier que le fichier est valide

```bash
cd ~/martialcomp
source venv/bin/activate
python -m py_compile apps/competitions/views/dashboard/federations.py
```

**Résultat attendu** : Aucune erreur

### 4.4 Vérifier qu'il n'y a plus l'erreur

```bash
grep -n "self\.request\.user" apps/competitions/views/dashboard/federations.py
```

**Résultat attendu** : Aucune ligne trouvée (exit code 1, normal)

---

## 🔄 ÉTAPE 5 : Redémarrer l'application

```bash
touch ~/martialcomp/passenger_wsgi.py
echo "Application redémarrée à $(date)"
```

**Attendez 5-10 secondes** pour que Passenger redémarre.

---

## 🧪 ÉTAPE 6 : Tester la correction

### 6.1 Tester la page d'accueil

Ouvrez dans votre navigateur : https://martialcomp.com/

**Résultat attendu** : La page s'affiche normalement

### 6.2 Tester le dashboard (sans connexion)

Ouvrez : https://martialcomp.com/fr/competitions/federations/6/dashboard/

**Résultat attendu** : Redirection vers la page de connexion (pas d'erreur 500)

---

## 👤 ÉTAPE 7 : Vérifier/Recréer FEDETEST1

### Si FEDETEST1 existe (vu à l'ÉTAPE 3)

Passez à l'ÉTAPE 8.

### Si FEDETEST1 n'existe PAS

```bash
cd ~/
chmod +x recreate_fedetest1.sh
bash recreate_fedetest1.sh
```

**Notez les informations** :
- Username : `FEDETEST1`
- Email : `fedetest1@martialcomp.com`
- Password : `TestFede2025!`

---

## ✅ ÉTAPE 8 : Test de connexion final

### 8.1 Se connecter avec FEDETEST1

1. Allez sur : https://martialcomp.com/fr/account/login/
2. Entrez :
   - Username : `FEDETEST1`
   - Password : (votre mot de passe ou `TestFede2025!` si recréé)
3. Cliquez sur "Se connecter"

**Résultat attendu** : Connexion réussie

### 8.2 Accéder au dashboard

Après connexion, allez sur : https://martialcomp.com/fr/competitions/federations/6/dashboard/

**Résultat attendu** : Le dashboard s'affiche avec :
- Statistiques de la fédération
- Liste des clubs
- Compétitions à venir
- Etc.

**✨ PAS D'ERREUR 500 !**

---

## 📊 ÉTAPE 9 : Vérifier les logs

```bash
tail -50 ~/logs/error_log
```

**Cherchez des erreurs récentes**. Il ne devrait plus y avoir de :
- `AttributeError: 'WSGIRequest' object has no attribute 'request'`
- Erreurs liées à `self.request.user`

---

## ✅ Checklist de Vérification Finale

Cochez chaque élément une fois vérifié :

- [ ] Les fichiers sont transférés
- [ ] L'état des utilisateurs est vérifié
- [ ] L'ancien fichier est sauvegardé
- [ ] Le nouveau fichier est en place
- [ ] Le fichier Python est valide (py_compile OK)
- [ ] Aucune occurrence de `self.request.user`
- [ ] L'application est redémarrée
- [ ] La page d'accueil fonctionne
- [ ] FEDETEST1 existe et est actif
- [ ] Connexion avec FEDETEST1 réussie
- [ ] Le dashboard fédération s'affiche correctement
- [ ] Pas d'erreurs dans les logs

---

## 🚨 En Cas de Problème

### Problème : Erreur 500 persiste

```bash
# Restaurer le backup
cd ~/martialcomp
ls -t apps/competitions/views/dashboard/federations.py.backup_* | head -1
# Notez le nom du fichier le plus récent, puis :
cp apps/competitions/views/dashboard/federations.py.backup_XXXXXXXX \
   apps/competitions/views/dashboard/federations.py
touch passenger_wsgi.py
```

### Problème : FEDETEST1 ne peut pas se connecter

```bash
cd ~/martialcomp
source venv/bin/activate
python manage.py shell
```

Puis dans le shell Python :
```python
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.get(username='FEDETEST1')
print(f"Email: {user.email}")
print(f"Actif: {user.is_active}")
user.set_password('TestFede2025!')
user.is_active = True
user.save()
print("Password réinitialisé et utilisateur activé")
exit()
```

### Problème : Aucun utilisateur dans la base

**C'est un problème majeur**. Contactez l'administrateur système.

Pour diagnostiquer :
```bash
cd ~/martialcomp
source venv/bin/activate
python manage.py shell -c "from django.contrib.auth import get_user_model; print(get_user_model().objects.count())"
```

---

## 📝 Notes de Déploiement

**Date du déploiement** : _____________  
**Heure du déploiement** : _____________  
**Nombre d'utilisateurs en production** : _____________  
**FEDETEST1 recréé ?** : ☐ OUI  ☐ NON  
**Tests réussis ?** : ☐ OUI  ☐ NON  
**Commentaires** :
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

---

## 📞 Contact

En cas de problème non résolu, consultez :
- `RAPPORT_CORRECTION_ERREUR_500_20251007.md` pour plus de détails
- Les logs : `tail -100 ~/logs/error_log`

**FIN DU GUIDE**
