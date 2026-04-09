# Instructions pour résoudre le problème de cache

## Problème
L'URL `/en/competitions/competitions/3/schedule/overview/` est toujours utilisée malgré la correction du template.

## Solution : Nettoyer le cache

### 1. Redémarrer le serveur Django (OBLIGATOIRE)

```bash
# Arrêter le serveur (Ctrl+C dans le terminal)
# Puis redémarrer :
python3 manage.py runserver 0.0.0.0:8888
```

### 2. Vider le cache du navigateur

**Chrome/Edge :**
- Appuyer sur `Ctrl+Shift+Delete`
- Cocher "Images et fichiers en cache"
- Cliquer sur "Effacer les données"

**Firefox :**
- Appuyer sur `Ctrl+Shift+Delete`
- Cocher "Cache"
- Cliquer sur "Effacer maintenant"

**Ou Hard Refresh :**
- Windows : `Ctrl+F5` ou `Ctrl+Shift+R`
- Mac : `Cmd+Shift+R`

### 3. Vider le cache Django (si activé)

```bash
python3 manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
>>> exit()
```

### 4. Supprimer les fichiers .pyc

```bash
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
```

### 5. Vérifier que le template est correct

```bash
grep -n "schedule_overview" apps/competitions/templates/competitions/dashboard/club.html
```

La ligne 1136 devrait afficher :
```
{% url 'competitions:management:schedule_overview' competition_id=competition.id %}
```

### 6. Tester l'URL générée

```bash
python3 manage.py shell -c "from django.urls import reverse; print(reverse('competitions:management:schedule_overview', kwargs={'competition_id': 3}))"
```

Devrait afficher : `/en/competitions/management/schedule/3/overview/`

---

**Note :** Si le problème persiste après ces étapes, il se peut qu'un autre template ou du JavaScript génère cette URL incorrecte.
