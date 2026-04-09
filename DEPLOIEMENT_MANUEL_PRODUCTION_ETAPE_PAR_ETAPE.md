# 🚀 DÉPLOIEMENT MANUEL EN PRODUCTION - ÉTAPE PAR ÉTAPE

**Date:** 2025-11-16  
**Problème:** Le nouveau template n'a pas été déployé en production  
**Preuve:** Erreur "Unexpected token '<'" à la ligne 2216 (ancien template = 1379+ lignes)

---

## ⚠️ CONSTAT

### En local (WSL) :
- ✅ Nouveau template installé : **849 lignes**
- ✅ Boutons onclick présents
- ✅ Pas de termes coréens
- ✅ Bouton DÉMARRER présent

### En production :
- ❌ Ancien template encore actif : **1379+ lignes**
- ❌ Erreur JavaScript ligne 2216
- ❌ Boutons ne fonctionnent pas
- ❌ Termes coréens encore présents

---

## 🎯 SOLUTION : DÉPLOIEMENT MANUEL

### ÉTAPE 1 : Connexion au serveur de production

```bash
ssh votre_utilisateur@votre_serveur
# OU via votre interface d'hébergement
```

---

### ÉTAPE 2 : Aller dans le répertoire de l'application

```bash
cd /var/www/martialcomp
# OU le chemin où se trouve votre application Django
```

---

### ÉTAPE 3 : Vérifier le template actuel

```bash
# Compter les lignes (devrait être 1379+ si ancien template)
wc -l apps/competitions/templates/competitions/combat/interface_combat_v2.html

# Vérifier si les termes coréens sont présents
grep -c "Kyong-go" apps/competitions/templates/competitions/combat/interface_combat_v2.html

# Si résultat > 0, c'est l'ancien template
```

---

### ÉTAPE 4 : Créer un backup de l'ancien template

```bash
cp apps/competitions/templates/competitions/combat/interface_combat_v2.html \
   apps/competitions/templates/competitions/combat/interface_combat_v2.html.backup_$(date +%Y%m%d_%H%M%S)

# Vérifier que le backup a été créé
ls -lh apps/competitions/templates/competitions/combat/interface_combat_v2.html.backup*
```

---

### ÉTAPE 5 : Transférer le nouveau template sur le serveur

**Option A : Via SCP (depuis votre machine locale)**

```bash
# Depuis votre machine locale (WSL)
cd /mnt/c/martial_hub_django/martialcomp

scp apps/competitions/templates/competitions/combat/interface_combat_v2.html \
    votre_utilisateur@votre_serveur:/var/www/martialcomp/apps/competitions/templates/competitions/combat/interface_combat_v2.html
```

**Option B : Via FTP/SFTP**

1. Ouvrir FileZilla ou votre client FTP
2. Se connecter au serveur
3. Naviguer vers : `/var/www/martialcomp/apps/competitions/templates/competitions/combat/`
4. Uploader le fichier `interface_combat_v2.html` depuis votre machine locale

**Option C : Copier-coller le contenu**

1. Sur votre machine locale, ouvrir le fichier :
   ```bash
   cat /mnt/c/martial_hub_django/martialcomp/apps/competitions/templates/competitions/combat/interface_combat_v2.html
   ```

2. Copier tout le contenu

3. Sur le serveur, éditer le fichier :
   ```bash
   nano apps/competitions/templates/competitions/combat/interface_combat_v2.html
   # OU
   vi apps/competitions/templates/competitions/combat/interface_combat_v2.html
   ```

4. Supprimer tout le contenu (dans nano : Ctrl+K plusieurs fois)

5. Coller le nouveau contenu

6. Sauvegarder (dans nano : Ctrl+O, Enter, Ctrl+X)

---

### ÉTAPE 6 : Vérifier que le nouveau template est bien en place

```bash
# Compter les lignes (devrait être 849)
wc -l apps/competitions/templates/competitions/combat/interface_combat_v2.html

# Vérifier que les boutons onclick sont présents
grep -c "onclick=\"addPoints" apps/competitions/templates/competitions/combat/interface_combat_v2.html
# Devrait afficher : 12

# Vérifier que les termes coréens ont disparu
grep -c "Kyong-go" apps/competitions/templates/competitions/combat/interface_combat_v2.html
# Devrait afficher : 0

# Vérifier que le bouton DÉMARRER est présent
grep -c "id=\"startBtn\"" apps/competitions/templates/competitions/combat/interface_combat_v2.html
# Devrait afficher : 1
```

---

### ÉTAPE 7 : Collecter les fichiers statiques

```bash
python3 manage.py collectstatic --noinput --clear
```

---

### ÉTAPE 8 : Redémarrer Gunicorn

```bash
sudo systemctl restart gunicorn

# Attendre 3 secondes
sleep 3

# Vérifier le statut
sudo systemctl status gunicorn
```

**Si Gunicorn n'est pas trouvé, essayez :**

```bash
# Chercher le service
sudo systemctl list-units --type=service | grep -i gunicorn

# OU redémarrer via supervisord
sudo supervisorctl restart all

# OU redémarrer Apache/Nginx
sudo systemctl restart apache2
# OU
sudo systemctl restart nginx
```

---

### ÉTAPE 9 : Vider le cache du navigateur

**Sur votre navigateur :**

1. Aller sur : https://martialcomp.com/fr/competitions/combat/combats/9/interface-v2/

2. Appuyer sur :
   - **Windows/Linux :** `Ctrl + Shift + R`
   - **Mac :** `Cmd + Shift + R`

3. **OU** ouvrir en navigation privée :
   - **Chrome :** `Ctrl + Shift + N`
   - **Firefox :** `Ctrl + Shift + P`

---

### ÉTAPE 10 : Vérifier que le nouveau template est actif

**Ouvrir la Console (F12) :**

1. Aller sur la page du combat
2. Appuyer sur `F12`
3. Aller dans l'onglet "Console"
4. Vérifier qu'il n'y a **pas** d'erreur "Unexpected token '<'" à la ligne 2216

**Vérifier visuellement :**

1. ✅ Bouton **DÉMARRER** visible avec animation verte
2. ✅ Termes : "Avertissements" et "Pénalités" (pas "Kyong-go" ni "Gam-jeom")
3. ✅ Clic sur ¼ pt → Score = 0.25
4. ✅ Console affiche : "🎯 Bouton cliqué:"

---

## 🔍 DIAGNOSTIC SI ÇA NE FONCTIONNE TOUJOURS PAS

### Problème 1 : Le template n'a pas été remplacé

**Vérifier sur le serveur :**

```bash
# Date de modification du fichier
ls -lh apps/competitions/templates/competitions/combat/interface_combat_v2.html

# Afficher les 10 premières lignes
head -20 apps/competitions/templates/competitions/combat/interface_combat_v2.html

# Chercher le bouton DÉMARRER
grep -n "startBtn" apps/competitions/templates/competitions/combat/interface_combat_v2.html
```

**Si le bouton DÉMARRER n'est pas trouvé :**
→ Le fichier n'a pas été remplacé, recommencer l'ÉTAPE 5

---

### Problème 2 : Les fichiers statiques n'ont pas été collectés

**Vérifier :**

```bash
# Voir si les fichiers statiques ont été collectés récemment
ls -lht staticfiles/ | head -10

# Forcer la collecte
python3 manage.py collectstatic --noinput --clear
```

---

### Problème 3 : Gunicorn n'a pas redémarré

**Vérifier :**

```bash
# Statut de Gunicorn
sudo systemctl status gunicorn

# Si inactif, redémarrer
sudo systemctl restart gunicorn

# Voir les logs
sudo journalctl -u gunicorn -n 50 --no-pager
```

---

### Problème 4 : Le cache du navigateur n'a pas été vidé

**Solutions :**

1. Faire `Ctrl + Shift + R` **plusieurs fois** (3-5 fois)

2. Vider complètement le cache :
   - Chrome : `F12` → Clic droit sur refresh → "Vider le cache et actualiser"

3. Ouvrir en navigation privée

4. Tester avec un autre navigateur

---

### Problème 5 : Le serveur utilise un cache (Redis, Memcached)

**Vider le cache Django :**

```bash
python3 manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
>>> exit()
```

---

## 📋 CHECKLIST COMPLÈTE

### Sur le serveur :
- [ ] Connexion au serveur réussie
- [ ] Backup de l'ancien template créé
- [ ] Nouveau template transféré
- [ ] Vérification : 849 lignes
- [ ] Vérification : 12 boutons onclick
- [ ] Vérification : 0 occurrence "Kyong-go"
- [ ] Vérification : 1 bouton startBtn
- [ ] Fichiers statiques collectés
- [ ] Gunicorn redémarré
- [ ] Gunicorn actif

### Sur le navigateur :
- [ ] Cache vidé (Ctrl + Shift + R)
- [ ] Page rechargée
- [ ] Pas d'erreur "Unexpected token '<'" dans la console
- [ ] Bouton DÉMARRER visible
- [ ] Termes neutres visibles (Avertissements, Pénalités)
- [ ] Clic sur ¼ pt → Score = 0.25
- [ ] Console affiche "🎯 Bouton cliqué:"

---

## 🆘 SI RIEN NE FONCTIONNE

**Envoyez-moi ces informations :**

1. **Sur le serveur :**
   ```bash
   # Nombre de lignes du template
   wc -l apps/competitions/templates/competitions/combat/interface_combat_v2.html
   
   # Recherche du bouton DÉMARRER
   grep -n "startBtn" apps/competitions/templates/competitions/combat/interface_combat_v2.html
   
   # Recherche des termes coréens
   grep -n "Kyong-go" apps/competitions/templates/competitions/combat/interface_combat_v2.html
   
   # Date de modification
   ls -lh apps/competitions/templates/competitions/combat/interface_combat_v2.html
   ```

2. **Dans la console du navigateur (F12) :**
   - Copier toutes les erreurs en rouge
   - Copier les logs affichés

3. **Capture d'écran de l'interface**

---

## 🎯 RÉSUMÉ

Le problème actuel est que **le serveur de production n'a pas été mis à jour**.

**Solution :**
1. Transférer le nouveau template sur le serveur (ÉTAPE 5)
2. Vérifier qu'il est bien en place (ÉTAPE 6)
3. Collecter les fichiers statiques (ÉTAPE 7)
4. Redémarrer Gunicorn (ÉTAPE 8)
5. Vider le cache du navigateur (ÉTAPE 9)

**Une fois ces étapes effectuées, tout devrait fonctionner !** ✅

---

**Document créé le:** 2025-11-16  
**Auteur:** Assistant IA  
**Statut:** Guide de déploiement manuel
