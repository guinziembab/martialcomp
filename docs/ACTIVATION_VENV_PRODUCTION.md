# ACTIVATION ENVIRONNEMENT VIRTUEL - PRODUCTION

## 🔍 Problème identifié
```
ModuleNotFoundError: No module named 'django'
```

Django n'est pas installé dans l'environnement Python 3 global. Il faut activer l'environnement virtuel.

## 🔍 LOCALISER L'ENVIRONNEMENT VIRTUEL

### Méthode 1: Rechercher les environnements virtuels courants

```bash
# Chercher dans les emplacements courants
ls -la venv/
ls -la env/
ls -la .venv/
ls -la virtualenv/
ls -la python-env/

# Ou rechercher dans tout le système
find /var/www -name "activate" 2>/dev/null
find /opt -name "activate" 2>/dev/null
find /home -name "activate" 2>/dev/null
```

### Méthode 2: Vérifier les processus Gunicorn

```bash
# Voir comment Gunicorn est actuellement lancé
ps aux | grep gunicorn

# Vérifier les logs pour voir le chemin Python utilisé
tail -50 gunicorn.log
```

### Méthode 3: Chercher les installations Django

```bash
# Chercher où Django est installé
find /var/www -name "django" -type d 2>/dev/null
find /opt -name "django" -type d 2>/dev/null

# Vérifier pip pour Python 3
python3 -m pip list | grep -i django
```

## ⚡ SOLUTIONS SELON LE CAS

### Cas 1: Environnement virtuel trouvé

```bash
# Si vous trouvez venv/bin/activate
source venv/bin/activate

# Puis tester
python manage.py --version
python manage.py shell
```

### Cas 2: Pas d'environnement virtuel

```bash
# Installer Django directement (temporaire)
python3 -m pip install django

# Ou créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate
pip install django
```

### Cas 3: Gunicorn utilise un autre chemin

```bash
# Vérifier le chemin Python de Gunicorn
ps aux | grep gunicorn

# Si Gunicorn utilise un chemin spécifique, l'utiliser:
# Exemple: /opt/python3.9/bin/python
/opt/python3.9/bin/python manage.py --version
```

## 🧪 COMMANDES DE DIAGNOSTIC

```bash
# 1. Chercher l'environnement virtuel
echo "=== Recherche environnement virtuel ==="
find /var/www/vhosts/martialcomp.com -name "activate" 2>/dev/null
ls -la | grep -E "(venv|env|virtualenv)"

# 2. Vérifier les processus Gunicorn
echo "=== Processus Gunicorn actuel ==="
ps aux | grep gunicorn

# 3. Vérifier les installations Python
echo "=== Installations Python ==="
which python
which python3
python3 -m pip list | head -10

# 4. Chercher Django
echo "=== Recherche Django ==="
find /var/www/vhosts/martialcomp.com -name "django" -type d 2>/dev/null | head -5
```

## 🚀 SOLUTION RAPIDE (après avoir trouvé l'env)

```bash
# Une fois l'environnement activé:
source venv/bin/activate  # ou le bon chemin

# Vérifier Django
python manage.py --version

# Continuer avec les corrections
python manage.py shell
```

## 📋 COMMANDE COMPLÈTE DE DIAGNOSTIC

```bash
cd /var/www/vhosts/martialcomp.com/httpdocs && find . -name "activate" 2>/dev/null && ps aux | grep gunicorn
```

---

**🔍 Exécutez d'abord les commandes de diagnostic pour localiser l'environnement virtuel !**