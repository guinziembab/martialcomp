# 🚀 DÉPLOIEMENT EN COURS - Competition Management Fix

**Date:** 14 novembre 2025  
**Heure de début:** En cours...

## 📋 Commandes à Exécuter

### 1️⃣ Connexion au serveur
```bash
ssh martialcomp-production
```

### 2️⃣ Navigation vers le projet
```bash
cd /home/martialcomp/martialcomp
```

### 3️⃣ Vérification de l'état actuel
```bash
# Vérifier la branche
git branch --show-current

# Vérifier l'état
git status
```

### 4️⃣ Activation de l'environnement virtuel
```bash
source venv/bin/activate
```

### 5️⃣ Récupération des modifications
```bash
# Récupérer les dernières modifications
git fetch origin

# Basculer sur la bonne branche si nécessaire
git checkout fix/federation-dashboard

# Mettre à jour
git pull origin fix/federation-dashboard
```

### 6️⃣ Vérification des fichiers modifiés
```bash
# Voir les dernières modifications
git log -1 --name-only --oneline

# Vérifier que les fichiers clés sont présents
ls -la apps/competitions/views/competition_management_pro.py
ls -la apps/competitions/urls/club.py
ls -la apps/competitions/templates/competitions/club/competition_management_detail.html
```

### 7️⃣ Vérification de la syntaxe Python
```bash
python -m py_compile apps/competitions/views/competition_management_pro.py
echo "✓ Syntaxe Python vérifiée"
```

### 8️⃣ Collecte des fichiers statiques
```bash
python manage.py collectstatic --noinput
```

### 9️⃣ Vérification des URLs (optionnel)
```bash
python manage.py show_urls | grep -E "api_get_competition"
```

### 🔟 Redémarrage de Gunicorn
```bash
sudo systemctl restart gunicorn
```

### 1️⃣1️⃣ Attendre et vérifier
```bash
# Attendre 3 secondes
sleep 3

# Vérifier que Gunicorn est actif
sudo systemctl status gunicorn
```

### 1️⃣2️⃣ Rechargement de Nginx
```bash
sudo systemctl reload nginx
```

### 1️⃣3️⃣ Vérification des logs
```bash
# Voir les dernières lignes des logs
sudo journalctl -u gunicorn -n 50 --no-pager
```

### 1️⃣4️⃣ Test des APIs
```bash
# Test API Types
curl -I https://martialcomp.com/en/competitions/club/api/competitions/4/types/list/

# Test API Catégories
curl -I https://martialcomp.com/en/competitions/club/api/competitions/4/categories/list/
```

---

## ✅ Checklist de Validation

- [ ] Connexion au serveur réussie
- [ ] Navigation vers le projet OK
- [ ] Branche correcte (fix/federation-dashboard)
- [ ] Environnement virtuel activé
- [ ] Code récupéré depuis Git
- [ ] Fichiers modifiés présents
- [ ] Syntaxe Python valide
- [ ] Fichiers statiques collectés
- [ ] Gunicorn redémarré avec succès
- [ ] Nginx rechargé
- [ ] Aucune erreur dans les logs
- [ ] APIs répondent correctement (HTTP 200 ou 302)

---

## 🧪 Tests Post-Déploiement

### Test 1: Interface Web
1. Ouvrir: https://martialcomp.com/en/competitions/club/competitions/4/manage/
2. Aller sur l'onglet "Types of competition"
3. Vérifier: Pas de "Undefined", catégories visibles
4. Aller sur l'onglet "Catégories"
5. Cliquer sur une catégorie
6. Vérifier: Liste des inscrits s'affiche

### Test 2: Console JavaScript
1. Ouvrir la console (F12)
2. Vérifier: Aucune erreur JavaScript
3. Vérifier: Les requêtes API réussissent

---

## 🆘 En Cas de Problème

### Erreur lors du redémarrage de Gunicorn
```bash
# Voir les erreurs détaillées
sudo journalctl -u gunicorn -n 100 --no-pager

# Forcer le redémarrage
sudo systemctl stop gunicorn
sleep 2
sudo systemctl start gunicorn
```

### Les changements ne s'appliquent pas
```bash
# Vérifier que les fichiers sont à jour
git log -1 apps/competitions/views/competition_management_pro.py

# Forcer la collecte des statiques
python manage.py collectstatic --noinput --clear

# Redémarrer à nouveau
sudo systemctl restart gunicorn
```

### Rollback si nécessaire
```bash
# Revenir à la version précédente
git log --oneline -5
git checkout <commit-hash-precedent>
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
```

---

## 📊 Résultat Attendu

✅ **Types of competition:** Affichage correct avec catégories  
✅ **Catégories:** Inscrits visibles au clic  
✅ **Performance:** Chargement < 2 secondes  
✅ **Logs:** Aucune erreur  

---

**Bonne chance pour le déploiement !** 🚀
