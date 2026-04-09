# DÉPLOIEMENT URGENT - Correction Template Poules

## Problème
Le template `liste_poules.html` sur le serveur de production affiche toujours l'ancien code (bouton avec icône crayon et `confirm()` au lieu du modal Bootstrap).

## Fichiers modifiés localement

1. **Template** : `apps/competitions/templates/competitions/combat/liste_poules.html`
   - Modal de sélection du type de compétition et mode de génération
   - Bouton avec icône `fa-magic` (baguette magique)
   - **NOUVEAU** : Bouton de suppression par catégorie

2. **Vue** : `apps/competitions/views/combat.py`
   - `combat_competition_types` passé au contexte
   - **NOUVEAU** : Fonction `supprimer_poules_categorie()` ajoutée

3. **URLs** : `apps/competitions/urls/combat.py`
   - **NOUVEAU** : Route `supprimer_poules_categorie`

---

## Commandes de déploiement MANUELLES

Exécutez ces commandes **une par une** depuis le terminal:

### 1. Copier les fichiers vers le serveur

```bash
# Template
scp apps/competitions/templates/competitions/combat/liste_poules.html martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/combat/

# Vue
scp apps/competitions/views/combat.py martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/

# URLs
scp apps/competitions/urls/combat.py martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/urls/
```

### 2. Nettoyer les caches sur le serveur

```bash
ssh martialcomp-production "cd /var/www/vhosts/martialcomp.com/httpdocs && find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null; find . -name '*.pyc' -delete 2>/dev/null; echo 'Cache Python supprimé'"
```

### 3. Vider le cache Django

```bash
ssh martialcomp-production "cd /var/www/vhosts/martialcomp.com/httpdocs && source /var/www/vhosts/martialcomp.com/venv/bin/activate && python manage.py shell -c 'from django.core.cache import cache; cache.clear(); print(\"Cache Django vidé\")'"
```

### 4. Redémarrer Apache

```bash
ssh martialcomp-production "touch /var/www/vhosts/martialcomp.com/httpdocs/config/wsgi.py && sudo systemctl restart apache2"
```

### 5. Vérification

```bash
# Vérifier que le nouveau fichier est bien présent
ssh martialcomp-production "grep -c 'fa-magic' /var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/combat/liste_poules.html && echo 'OK: fa-magic trouvé' || echo 'ERREUR: fa-magic absent'"

ssh martialcomp-production "grep -c 'generatePoolsModal' /var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/combat/liste_poules.html && echo 'OK: Modal trouvé' || echo 'ERREUR: Modal absent'"

ssh martialcomp-production "grep -c 'supprimer_poules_categorie' /var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/combat.py && echo 'OK: Vue trouvée' || echo 'ERREUR: Vue absente'"
```

---

## Nouvelles fonctionnalités ajoutées

### 1. Modal de génération des poules
- **Étape 1** : Sélection des types de compétition (combat/mixed uniquement)
- **Étape 2** : Choix du mode de génération :
  - **Mode Standard** : Round-robin complet (toutes les équipes contre toutes)
  - **Mode Qualificatif** : 2 combats min par équipe puis demi/finale

### 2. Suppression par catégorie
- Chaque catégorie dans la liste des poules a maintenant un bouton poubelle rouge
- Un clic ouvre une confirmation avec le nombre de poules et combats qui seront supprimés
- Permet de gérer plus finement les catégories sans tout réinitialiser

---

## Si le problème persiste

1. **Vérifier qu'il n'y a qu'UN seul fichier** :
```bash
ssh martialcomp-production "find /var/www/vhosts/martialcomp.com -name 'liste_poules.html' -type f"
```

2. **Vérifier les logs Apache** :
```bash
ssh martialcomp-production "tail -50 /var/log/apache2/error.log"
```

3. **Forcer le rechargement mod_wsgi** :
```bash
ssh martialcomp-production "sudo /etc/init.d/apache2 force-reload"
```

4. **Vérifier s'il y a un CDN/Cloudflare** :
   - Si oui, purger le cache CDN
