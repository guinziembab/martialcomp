# 🔍 DIAGNOSTIC TEMPLATE PRODUCTION

## 🎯 PROBLÈME
Le template professionnel est déployé sur le serveur, mais Django affiche le template simple.

## 📋 COMMANDES DE DIAGNOSTIC À EXÉCUTER SUR LE SERVEUR

### 1️⃣ Vérifier quel template Django utilise
```bash
cd /opt/martialcomp/app

# Voir tous les templates welcome.html
find . -name "welcome.html" -type f

# Vérifier le contenu du template principal
head -10 competitions/templates/competitions/welcome.html

# Chercher s'il y a d'autres templates welcome
find . -path "*/templates/*" -name "*.html" | grep -i welcome
```

### 2️⃣ Vérifier la configuration Django des templates
```bash
# Voir l'ordre de résolution des templates
python manage.py shell -c "from django.conf import settings; print('TEMPLATES:', settings.TEMPLATES[0]['DIRS']); print('APP_DIRS:', settings.TEMPLATES[0]['APP_DIRS'])"

# Vérifier s'il y a un cache template
find . -name "__pycache__" -type d | head -3
```

### 3️⃣ Vérifier les vues Django
```bash
# Voir quelle vue gère la page d'accueil
grep -n "welcome" config/urls.py

# Voir le contenu de la vue welcome
cat competitions/views/welcome.py
```

### 4️⃣ Forcer le rechargement
```bash
# Supprimer le cache Django
find . -name "*.pyc" -delete
find . -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Redémarrer Django
pkill -f "runserver 127.0.0.1:8000" 2>/dev/null || true
sleep 5
source venv/bin/activate
python manage.py check
nohup python manage.py runserver 127.0.0.1:8000 > /tmp/django_production_$(date +%H%M).log 2>&1 &

# Attendre et tester
sleep 10
curl -s "http://127.0.0.1:8000/" | head -20
```

### 5️⃣ Vérifier s'il y a un problème de permissions
```bash
# Vérifier les permissions du template
ls -la competitions/templates/competitions/welcome.html

# Vérifier le propriétaire
stat competitions/templates/competitions/welcome.html
```

---

## 🎯 SOLUTIONS POSSIBLES

### Solution A : Forcer le remplacement du template
```bash
cd /opt/martialcomp/app

# Sauvegarder l'actuel
cp competitions/templates/competitions/welcome.html competitions/templates/competitions/welcome.html.backup_$(date +%H%M)

# Copier le bon template (s'il existe ailleurs)
# Localiser d'abord le bon template professionnel
find . -name "*.html" -exec grep -l "auth-section" {} \; 2>/dev/null
```

### Solution B : Vérifier s'il y a un template qui override
```bash
# Chercher tous les templates qui pourraient interférer
find . -name "base.html" -o -name "index.html" -o -name "home.html" | head -5

# Vérifier les apps installées qui pourraient avoir des templates
grep -A 20 "INSTALLED_APPS" config/settings.py
```

### Solution C : Debug mode temporaire
```bash
# Activer le debug temporairement pour voir les erreurs
grep "DEBUG" config/settings.py
```

---

## 🔧 COMMANDES RAPIDES DE RÉSOLUTION

### Option 1 : Redémarrage complet
```bash
cd /opt/martialcomp/app
pkill -f python
sleep 5
source venv/bin/activate
python manage.py check
python manage.py runserver 127.0.0.1:8000 &
```

### Option 2 : Vérification des URLs
```bash
# Voir toutes les URLs configurées
python manage.py shell -c "from django.urls import get_resolver; print([str(p.pattern) for p in get_resolver().url_patterns])"
```

---

## ⚡ ACTIONS À FAIRE

1. **Exécuter le diagnostic complet** avec les commandes ci-dessus
2. **Identifier** où se trouve le bon template professionnel
3. **Forcer Django** à utiliser le bon template
4. **Redémarrer** l'application
5. **Tester** le résultat

**L'objectif** : Faire afficher le template professionnel avec les boutons Google/Facebook au lieu du template simple.