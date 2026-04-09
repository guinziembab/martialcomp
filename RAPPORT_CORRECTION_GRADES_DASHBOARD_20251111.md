# Rapport de Correction - Erreur 500 sur /grades/dashboard/
Date: 11 novembre 2024

## Problème Identifié
L'erreur 500 sur `/grades/dashboard/` était causée par deux problèmes :

1. **discipline_filtering.py** : Le code tentait d'accéder à `club.federation` sans vérifier si l'attribut existe
2. **utils_module.py** : La fonction `get_user_club` ne gérait pas le cas où l'utilisateur a une Organization au lieu d'un Club

## Corrections Appliquées

### 1. apps/competitions/utils/discipline_filtering.py

**Ligne 46** - Protection contre l'absence de l'attribut federation :
```python
# AVANT
federation = club.federation

# APRÈS  
federation = getattr(club, 'federation', None)
```

**Lignes 39-43** - Gestion du cas où club est une Organization :
```python
# AVANT
club_disciplines = club.disciplines.all()

# APRÈS
if hasattr(club, 'disciplines'):
    club_disciplines = club.disciplines.all()
else:
    # Si c'est une Organization, pas de disciplines directes
    club_disciplines = Discipline.objects.none()
```

### 2. apps/grades/utils_module.py

Refonte complète de la fonction `get_user_club` pour aligner avec la logique du middleware :
- Vérifie d'abord si `request.user_organization` existe (défini par le middleware)
- Vérifie UserProfile.organization
- Vérifie MembershipSubscription actif
- Utilise les anciennes méthodes en fallback

## Fichiers Modifiés
1. `apps/competitions/utils/discipline_filtering.py`
2. `apps/grades/utils_module.py`

## Scripts Créés
- `deploy_grades_dashboard_fix.sh` : Script de déploiement automatique

## État Final
Les corrections ont été appliquées localement et sont prêtes à être déployées en production.

## Commandes de Déploiement Manuel
```bash
# Copier les fichiers
scp apps/competitions/utils/discipline_filtering.py pierrep99@martialcomp.com:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/utils/
scp apps/grades/utils_module.py pierrep99@martialcomp.com:/var/www/vhosts/martialcomp.com/httpdocs/apps/grades/

# Redémarrer Gunicorn
ssh pierrep99@martialcomp.com "sudo systemctl reload gunicorn"
```

## Vérification
Après déploiement, vérifier que https://martialcomp.com/fr/grades/dashboard/ fonctionne correctement.