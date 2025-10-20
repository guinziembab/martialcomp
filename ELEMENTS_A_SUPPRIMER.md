# Éléments à supprimer avant transfert en production

## Archives et backups (~ 200+ MB)
- apps_complete_20250917.tar.gz (9.6 MB)
- apps_dev.zip (10.4 MB)
- deployment_complete_20250918_130614.zip (42.3 MB)
- martialcomp_production_transfer_8-5_221133.tar.gz (74.7 MB)
- martialcomp_update_20250826_204045.tar.gz (17.8 MB)
- mobile_backup_20250827_214456.tar.gz (11.8 MB)
- Tous les fichiers .tar.gz et .zip
- Dossiers: backup_*, mobile_backup_*, deployment_package_*, production_*

## Fichiers temporaires (5317 fichiers)
- Tous les *.pyc
- Tous les dossiers __pycache__
- Tous les *.log
- Tous les *.sqlite3 et *.db (sauf si nécessaire pour dev)

## Fichiers de documentation temporaires
- Tous les fichiers .md de statut/rapport (BACKUP_*.md, *_FIX_*.md, STATUS_*.md, etc.)
- Fichiers de diagnostic et test (diagnostic_*.js, test_*.js, debug_*.js)

## Dossiers probablement volumineux à vérifier
- media/ (si contient des uploads de dev)
- static/ (si non optimisé)
- node_modules/ (si présent)
- venv/ ou env/ (environnement virtuel)
- .git/ (historique Git peut être volumineux)