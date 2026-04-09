# SOLUTION : Purger le Cache Cloudflare

## Problème Identifié
Le template `liste_poules.html` est **correctement déployé sur le serveur** (MD5 vérifié), mais Cloudflare continue de servir l'ancienne version HTML cachée.

## Solution : Purger le Cache Cloudflare

### Option 1 : Via le Dashboard Cloudflare (Recommandé)

1. **Connectez-vous à Cloudflare** : https://dash.cloudflare.com/
2. **Sélectionnez le domaine** : `martialcomp.com`
3. **Allez dans Caching** → **Configuration**
4. **Cliquez sur "Purge Everything"** (Purger tout)
5. **Confirmez** la purge

### Option 2 : Purge sélective d'une URL spécifique

1. Dans Cloudflare Dashboard → Caching → Configuration
2. Cliquez sur "Custom Purge"
3. Entrez l'URL exacte de la page des poules, par exemple :
   ```
   https://martialcomp.com/combat/poules/competition/*/
   ```
   Ou l'URL exacte que vous visitez.

### Option 3 : Via l'API Cloudflare (si vous avez les clés API)

```bash
# Purge tout le cache
curl -X POST "https://api.cloudflare.com/client/v4/zones/ZONE_ID/purge_cache" \
     -H "Authorization: Bearer YOUR_API_TOKEN" \
     -H "Content-Type: application/json" \
     --data '{"purge_everything":true}'
```

---

## Après la Purge

1. **Ouvrez un navigateur en mode Incognito/Privé** (Ctrl+Shift+N sur Chrome)
2. **Videz le cache du navigateur** : Ctrl+Shift+Delete
3. **Accédez à la page des poules**
4. **Vérifiez** :
   - Le bouton "Générer automatiquement" doit avoir une icône baguette magique (fa-magic)
   - Un clic doit ouvrir un **MODAL** (pas un alert/confirm JavaScript)
   - Chaque catégorie doit avoir un bouton poubelle rouge pour la supprimer

---

## Configuration Cloudflare Recommandée (Optionnel)

Pour éviter ce problème à l'avenir, vous pouvez configurer des règles de cache pour exclure les pages HTML dynamiques :

### Page Rules (Règles de page)

1. Cloudflare Dashboard → Rules → Page Rules
2. Créer une règle :
   - **URL Pattern** : `*martialcomp.com/combat/*`
   - **Setting** : Cache Level → Bypass

Cela empêchera Cloudflare de cacher les pages de l'interface combat.

### Cache-Control Headers

Alternativement, configurez Django pour envoyer des headers de cache appropriés :

```python
# Dans views/combat.py, ajoutez à la vue liste_poules :
from django.views.decorators.cache import never_cache

@never_cache
@login_required
def liste_poules(request, competition_id):
    # ... code existant
```

---

## Vérification Finale

Après la purge, exécutez cette commande pour vérifier que Cloudflare sert la nouvelle version :

```bash
curl -s -I "https://martialcomp.com/combat/poules/competition/YOUR_COMPETITION_ID/" | grep -E "(cf-cache-status|age|cache-control)"
```

Le `cf-cache-status` devrait être `MISS` (première requête après purge) ou `DYNAMIC`.
