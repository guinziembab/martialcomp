
# Guide de déploiement pour la correction JavaScript

## Problème
Le code JavaScript s'affiche comme du texte au lieu d'être exécuté sur https://martialcomp.com

## Solution
1. **Sauvegarder le template actuel**:
   ```bash
   cp /path/to/production/apps/competitions/templates/competitions/dashboard/club.html /path/to/backup/club_template_backup_$(date +%Y%m%d_%H%M%S).html
   ```

2. **Copier le template corrigé**:
   ```bash
   cp /path/to/corrected/club.html /path/to/production/apps/competitions/templates/competitions/dashboard/club.html
   ```

3. **Vérifier la correction**:
   ```bash
   grep -q "function calculateAges()" /path/to/production/apps/competitions/templates/competitions/dashboard/club.html
   ```

4. **Redémarrer le serveur web**:
   ```bash
   systemctl restart nginx
   systemctl restart gunicorn
   ```

5. **Tester sur https://martialcomp.com/fr/competitions/dashboard/club/**

## Vérifications
- ✅ Le JavaScript ne s'affiche plus comme du texte
- ✅ Les fonctions JavaScript s'exécutent correctement
- ✅ L'interface utilisateur fonctionne normalement
