# 🥋 Interface de Combat MartialComp V3 - Installation Rapide

## 📦 Fichiers Fournis

1. **interface_combat_v3_improved.html** - Le nouveau template HTML/CSS/JS
2. **combat_api_views.py** - Les vues API Django pour le refresh en temps réel
3. **combat_api_urls.py** - Configuration des URLs API
4. **deploy_combat_interface_v3.sh** - Script de déploiement automatique (Linux)
5. **GUIDE_INTERFACE_COMBAT_V3.md** - Documentation complète
6. **README.md** - Ce fichier

---

## 🚀 Installation Express (5 minutes)

### Option 1 : Script Automatique (Recommandé pour Linux)

```bash
# 1. Rendre le script exécutable
chmod +x deploy_combat_interface_v3.sh

# 2. Exécuter le déploiement en staging
./deploy_combat_interface_v3.sh --staging

# 3. Une fois validé, déployer en production
./deploy_combat_interface_v3.sh --production
```

### Option 2 : Installation Manuelle

#### Étape 1 : Backup

```bash
# Sauvegarder l'ancien template
cp apps/competitions/templates/competitions/interface_combat_v2.html \
   apps/competitions/templates/competitions/interface_combat_v2_backup.html

# Sauvegarder la base de données
python manage.py dumpdata competitions > backup_combat.json
```

#### Étape 2 : Copier les fichiers

```bash
# Template
cp interface_combat_v3_improved.html \
   apps/competitions/templates/competitions/interface_combat_v3.html

# API Views
cp combat_api_views.py apps/competitions/

# API URLs
cp combat_api_urls.py apps/competitions/
```

#### Étape 3 : Configurer les URLs

Dans votre `urls.py` principal (ex: `martialcomp/urls.py`), ajoutez :

```python
urlpatterns = [
    # ... autres URLs ...
    
    # API Combat
    path('api/', include('apps.competitions.combat_api_urls')),
]
```

#### Étape 4 : Préparer les drapeaux

```bash
# Créer le répertoire
mkdir -p static/images/flags

# Télécharger les drapeaux (exemple pour la France)
wget https://flagcdn.com/256x192/fr.png -O static/images/flags/FR.png
wget https://flagcdn.com/256x192/be.png -O static/images/flags/BE.png
wget https://flagcdn.com/256x192/de.png -O static/images/flags/DE.png
# ... etc pour tous les pays
```

#### Étape 5 : Migrations et collecte des statiques

```bash
# Migrations (si nécessaire)
python manage.py makemigrations
python manage.py migrate

# Collecte des statiques
python manage.py collectstatic --noinput
```

#### Étape 6 : Redémarrer

```bash
# En développement
# Ctrl+C puis relancer le serveur

# En production
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

---

## 🎯 Nouveautés de la V3

### ✨ Principales Améliorations

1. **Logos repositionnés** ✅
   - Logos de clubs dans les coins supérieurs de l'en-tête
   - Plus d'espace dans les colonnes des combattants

2. **Drapeaux des pays** 🌍
   - Affichés dans le bandeau supérieur
   - À côté des logos de clubs

3. **Logo central** 🏆
   - Logo de compétition/discipline bien visible au centre
   - Animation pulse pour attirer l'attention

4. **Bouton "Gestion Poule"** 📊
   - Navigation rapide vers la gestion de la poule
   - Toujours accessible en haut à droite

5. **Bouton "Refresh"** 🔄
   - Actualisation en temps réel des scores
   - Sans rechargement de page (AJAX)

---

## 🔧 Configuration Requise

### Modèles Django

Assurez-vous que votre modèle `Combat` contient les champs suivants :

```python
class Combat(models.Model):
    # Combattants
    combattant_rouge = models.ForeignKey(Practitioner, ...)
    combattant_blanc = models.ForeignKey(Practitioner, ...)
    
    # Scores
    score_rouge = models.FloatField(default=0)
    score_blanc = models.FloatField(default=0)
    
    # Pénalités
    avertissements_rouge = models.IntegerField(default=0)
    avertissements_blanc = models.IntegerField(default=0)
    penalites_rouge = models.IntegerField(default=0)
    penalites_blanc = models.IntegerField(default=0)
    sorties_rouge = models.IntegerField(default=0)
    sorties_blanc = models.IntegerField(default=0)
    
    # Timer
    duree_combat = models.IntegerField(default=120)
    temps_restant = models.IntegerField(default=120)
    est_en_cours = models.BooleanField(default=False)
    
    # Relations
    pool = models.ForeignKey(Pool, ...)
    competition = models.ForeignKey(Competition, ...)
    discipline = models.ForeignKey(Discipline, ...)
```

### Modèle Practitioner

```python
class Practitioner(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    club = models.ForeignKey(Club, ...)
    pays = models.ForeignKey(Country, ...)  # nullable
    
    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"
```

### Modèle Club

```python
class Club(models.Model):
    nom = models.CharField(max_length=200)
    logo = models.ImageField(upload_to='clubs/logos/', blank=True, null=True)
```

### Modèle Country

```python
class Country(models.Model):
    nom = models.CharField(max_length=100)
    code = models.CharField(max_length=2)  # ISO code (FR, BE, etc.)
```

---

## 🧪 Test de l'Installation

### 1. Test du Template

Accédez à un combat existant :
```
http://localhost:8000/competitions/combat/123/
```

Vérifiez :
- ✅ Logos des clubs visibles en haut
- ✅ Drapeaux affichés correctement
- ✅ Logo central bien visible
- ✅ Boutons de navigation présents

### 2. Test de l'API

Test avec curl :

```bash
# Test de mise à jour
curl -X POST http://localhost:8000/api/combat/123/update/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: YOUR_TOKEN" \
  -d '{"score_rouge": 2.5, "score_blanc": 1.0}'

# Test de récupération du status
curl http://localhost:8000/api/combat/123/status/
```

### 3. Test du Refresh

1. Ouvrir l'interface de combat
2. Cliquer sur le bouton "Refresh"
3. Vérifier qu'une notification apparaît
4. Vérifier dans les logs Django que la requête est reçue

---

## 🐛 Dépannage

### Problème : Les drapeaux ne s'affichent pas

**Solution 1 :** Vérifier le chemin des images
```bash
ls -la static/images/flags/
```

**Solution 2 :** Vérifier que `STATIC_URL` est bien configuré dans `settings.py`
```python
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
```

### Problème : Le bouton Refresh ne fonctionne pas

**Solution 1 :** Vérifier que l'URL API est bien configurée
```bash
python manage.py show_urls | grep combat
```

**Solution 2 :** Vérifier les logs Django
```bash
tail -f /var/log/martialcomp/debug.log
```

**Solution 3 :** Ouvrir la console du navigateur (F12) et vérifier les erreurs JavaScript

### Problème : Erreur CSRF Token

**Solution :** Vérifier que le middleware CSRF est actif dans `settings.py`
```python
MIDDLEWARE = [
    ...
    'django.middleware.csrf.CsrfViewMiddleware',
    ...
]
```

### Problème : Permission refusée sur l'API

**Solution :** Vérifier que l'utilisateur est bien authentifié et a les permissions nécessaires

---

## 📊 Structure des Fichiers après Installation

```
martialcomp/
├── apps/
│   └── competitions/
│       ├── templates/
│       │   └── competitions/
│       │       ├── interface_combat_v2.html (backup)
│       │       └── interface_combat_v3.html (nouveau)
│       ├── combat_api_views.py (nouveau)
│       ├── combat_api_urls.py (nouveau)
│       ├── views.py
│       └── models.py
├── static/
│   └── images/
│       └── flags/
│           ├── FR.png
│           ├── BE.png
│           ├── DE.png
│           └── ...
├── manage.py
└── requirements.txt
```

---

## 🔄 Rollback (Retour en arrière)

Si vous rencontrez des problèmes :

### Option 1 : Script automatique
```bash
./deploy_combat_interface_v3.sh --rollback
```

### Option 2 : Manuelle
```bash
# Restaurer l'ancien template
cp apps/competitions/templates/competitions/interface_combat_v2_backup.html \
   apps/competitions/templates/competitions/interface_combat_v2.html

# Restaurer la base de données
python manage.py loaddata backup_combat.json

# Redémarrer
sudo systemctl restart gunicorn
```

---

## 📞 Support

Pour toute question :
1. Consultez le **GUIDE_INTERFACE_COMBAT_V3.md** pour la documentation complète
2. Vérifiez les logs Django : `tail -f /var/log/martialcomp/debug.log`
3. Consultez la console navigateur (F12) pour les erreurs JavaScript

---

## ✅ Checklist Post-Installation

- [ ] Template v3 déployé
- [ ] API views installées
- [ ] API URLs configurées
- [ ] Drapeaux téléchargés
- [ ] Migrations appliquées
- [ ] Statiques collectés
- [ ] Services redémarrés
- [ ] Interface testée en navigation
- [ ] Bouton Refresh testé
- [ ] Bouton Gestion Poule testé
- [ ] Logos visibles
- [ ] Drapeaux visibles
- [ ] Logo central visible
- [ ] Mode plein écran testé

---

**Bon combat ! 🥋**
