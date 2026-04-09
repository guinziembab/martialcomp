# 🥋 Déploiement Interface Combat V3 - DEV

## ✅ Modifications Appliquées en DEV

### 1. Template V3 Adapté
- ✅ Template copié : `apps/competitions/templates/competitions/combat/interface_combat_v3.html`
- ✅ Adapté aux modèles réels :
  - `combattant_rouge` → `pratiquant_rouge`
  - `combattant_blanc` → `pratiquant_blanc`
  - `.nom` → `.full_name`
  - `.club.nom` → `.club.name`
  - `.pays.code` → `.club.country`
  - `competition.nom` → `competition.title`
  - `discipline.nom` → `discipline.name`

### 2. Vues API Créées
- ✅ `apps/competitions/combat_api_views.py` - Vues API adaptées aux modèles réels
- ✅ `apps/competitions/combat_api_urls.py` - URLs API

### 3. Intégration URLs
- ✅ URLs API ajoutées dans `config/urls.py` : `/api/combat/<id>/update/` et `/api/combat/<id>/status/`

### 4. Répertoire Drapeaux
- ✅ Répertoire créé : `static/images/flags/`

### 5. Vue Mise à Jour
- ✅ `apps/competitions/views/combat.py` : `interface_combat_v2` utilise maintenant `interface_combat_v3.html`

### 6. Backup
- ✅ Backup créé : `apps/competitions/templates/competitions/combat/interface_combat_v2_backup_*.html`

---

## 📋 Fichiers Modifiés/Créés

### Nouveaux Fichiers
1. `apps/competitions/templates/competitions/combat/interface_combat_v3.html`
2. `apps/competitions/combat_api_views.py`
3. `apps/competitions/combat_api_urls.py`

### Fichiers Modifiés
1. `config/urls.py` - Ajout des URLs API
2. `apps/competitions/views/combat.py` - Utilisation du template V3

---

## 🚀 Prochaines Étapes pour PROD

### 1. Télécharger les Drapeaux
```bash
cd /mnt/c/martial_hub_django/martialcomp
mkdir -p static/images/flags

# Télécharger les drapeaux principaux
wget -q https://flagcdn.com/256x192/fr.png -O static/images/flags/FR.png
wget -q https://flagcdn.com/256x192/be.png -O static/images/flags/BE.png
wget -q https://flagcdn.com/256x192/de.png -O static/images/flags/DE.png
wget -q https://flagcdn.com/256x192/it.png -O static/images/flags/IT.png
wget -q https://flagcdn.com/256x192/es.png -O static/images/flags/ES.png
wget -q https://flagcdn.com/256x192/gb.png -O static/images/flags/GB.png
# ... ajouter d'autres pays selon besoin
```

### 2. Collecter les Statiques
```bash
python manage.py collectstatic --noinput
```

### 3. Tester en DEV
- Accéder à un combat : `/fr/competitions/combat/combats/<id>/interface-v2/`
- Vérifier :
  - ✅ Logos des clubs dans l'en-tête
  - ✅ Drapeaux affichés
  - ✅ Logo central visible
  - ✅ Bouton "Gestion Poule" fonctionne
  - ✅ Bouton "Refresh" fonctionne (test API)

---

## 🔧 Commandes pour Transfert PROD

### Via SSH
```bash
ssh martialcomp-production

# Aller dans le répertoire
cd C:\martial_hub_django\martialcomp\apps\competitions

# Copier les fichiers depuis Packages-CombatV3
cp Packages-CombatV3/interface_combat_v3_improved.html templates/competitions/combat/interface_combat_v3.html
cp Packages-CombatV3/combat_api_views.py .
cp Packages-CombatV3/combat_api_urls.py .

# Adapter le template (remplacements similaires à DEV)
# ... (utiliser sed ou éditeur)

# Créer répertoire drapeaux
mkdir -p ../../static/images/flags

# Télécharger drapeaux
cd ../../static/images/flags
wget https://flagcdn.com/256x192/fr.png -O FR.png
# ... autres pays

# Collecter statiques
cd ../../..
python manage.py collectstatic --noinput

# Redémarrer services
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

---

## ⚠️ Notes Importantes

1. **Modèles** : Les avertissements/pénalités sont stockés dans `ActionCombat`, pas directement dans `Combat`
2. **Pays** : Le pays vient du `Club.country` (code ISO à 2 caractères)
3. **Template** : Le template V3 remplace V2 dans la vue `interface_combat_v2`
4. **API** : Les endpoints nécessitent une authentification (`@login_required`)

---

## 🐛 Dépannage

### Les drapeaux ne s'affichent pas
- Vérifier que les fichiers sont dans `static/images/flags/`
- Vérifier que `collectstatic` a été exécuté
- Vérifier que `STATIC_URL` est bien configuré

### Le bouton Refresh ne fonctionne pas
- Vérifier la console navigateur (F12) pour les erreurs
- Vérifier que l'URL API est accessible : `/api/combat/<id>/status/`
- Vérifier les permissions utilisateur

### Erreur CSRF
- Vérifier que le middleware CSRF est actif
- Vérifier que le token CSRF est bien récupéré dans le JavaScript

---

**Date de déploiement DEV** : $(date)
**Statut** : ✅ Prêt pour tests en DEV
