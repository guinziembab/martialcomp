# Instructions de Déploiement - Correction Club Dashboard

## Méthode 1 : Exécuter le script directement sur le serveur

### Étape 1 : Transférer le script vers le serveur
```bash
scp apply_fix_on_production.sh pierrep99@martialcomp.com:/tmp/
```

### Étape 2 : Se connecter au serveur et exécuter
```bash
ssh pierrep99@martialcomp.com
chmod +x /tmp/apply_fix_on_production.sh
/tmp/apply_fix_on_production.sh
```

## Méthode 2 : Exécuter le script via SSH en une commande

```bash
ssh pierrep99@martialcomp.com 'bash -s' < apply_fix_on_production.sh
```

## Méthode 3 : Copier le fichier corrigé directement

### Étape 1 : Copier le fichier local vers la production
```bash
scp apps/competitions/views/dashboard/club.py pierrep99@martialcomp.com:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/dashboard/club.py
```

### Étape 2 : Redémarrer Gunicorn
```bash
ssh pierrep99@martialcomp.com "cd /var/www/vhosts/martialcomp.com/httpdocs && sudo systemctl reload gunicorn"
```

## Méthode 4 : Appliquer les corrections manuellement

### Se connecter au serveur
```bash
ssh pierrep99@martialcomp.com
cd /var/www/vhosts/martialcomp.com/httpdocs
```

### Sauvegarder le fichier
```bash
cp apps/competitions/views/dashboard/club.py apps/competitions/views/dashboard/club.py.backup_$(date +%Y%m%d_%H%M%S)
```

### Éditer le fichier
```bash
nano apps/competitions/views/dashboard/club.py
```

### Appliquer les corrections

1. **Trouver la ligne avec le log du club** (environ ligne 155) :
   ```python
   logger.info(f"Club: {club}, trouvé via: {club_found_via}")
   ```

2. **Ajouter après cette ligne** (ligne 158) :
   ```python
   # Date actuelle pour les calculs - DÉPLACÉ ICI POUR ÉVITER L'ERREUR
   now = timezone.now().date()
   ```

3. **Ajouter après** (ligne 161) :
   ```python
   # Initialiser club_organization
   club_organization = None
   ```

4. **Supprimer toute autre définition de `now`** qui pourrait exister plus bas dans le fichier (autour de la ligne 296)

### Redémarrer Gunicorn
```bash
sudo systemctl reload gunicorn
```

## Vérification

Après le déploiement, vérifier que la page fonctionne :
- https://martialcomp.com/fr/competitions/dashboard/club/

## Corrections appliquées

1. ✓ `now` défini à la ligne 158 (après le log du club)
2. ✓ `club_organization` initialisé à `None` à la ligne 161
3. ✓ Suppression de la définition dupliquée de `now`
