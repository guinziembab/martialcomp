# Package de mise à jour Production - Novembre 2024

## Vue d'ensemble

Ce package contient tous les fichiers essentiels de l'application "Compétitions" modifiés depuis le 1er novembre 2024. Il a été créé pour aligner la plateforme de production avec les dernières mises à jour du développement.

## Date de création

Package généré le: $(date +"%d/%m/%Y à %H:%M:%S")

## Fichiers inclus

### 1. Forms (Formulaires)

Les formulaires suivants ont été modifiés:

- **combat_forms.py**: Formulaires pour la gestion des combats (configurations, équipes, poules, combats, actions)
- **practitioners.py**: Formulaires pour la gestion des pratiquants (création, édition, recherche, import)
- **standalone_scoring.py**: Formulaires pour le système de notation autonome
- **competition_types.py**: Formulaires pour les types de compétition
- **competitions.py**: Formulaires pour les compétitions
- **grades.py**: Formulaires pour les grades
- **onboarding.py**: Formulaires pour l'onboarding
- Et autres formulaires modifiés

### 2. Models (Modèles)

Les modèles suivants ont été modifiés:

- **combat.py**: Modèles pour le système de gestion des combats (CombatConfiguration, Equipe, MembreEquipe, Poule, Combat, ActionCombat)
- **practitioners.py**: Modèles pour les pratiquants
- **standalone_scoring.py**: Modèles pour le système de notation autonome
- **competitions.py**: Modèles pour les compétitions
- **categories.py**: Modèles pour les catégories
- Et autres modèles modifiés

### 3. Views (Vues)

Les vues suivantes ont été modifiées:

#### Vues Club
- **club/competitions.py**: Gestion des compétitions du club
- **club/practitioners.py**: Gestion des pratiquants du club
- **club/registrations.py**: Gestion des inscriptions du club
- **club/import_export.py**: Import/export de données

#### Vues Dashboard
- **dashboard/base.py**: Vues de base du dashboard
- **dashboard/club.py**: Dashboard du club
- **dashboard/participant.py**: Dashboard du participant
- **dashboard/referee.py**: Dashboard de l'arbitre

#### Vues Combat
- **combat.py**: Vues pour la gestion des combats
- **combat_taekwondo.py**: Vues spécifiques au Taekwondo

#### Vues Management
- **management/dashboard.py**: Dashboard de gestion
- **management/judges.py**: Gestion des juges
- **management/participants.py**: Gestion des participants
- **management/results.py**: Gestion des résultats
- **management/schedule.py**: Gestion du planning
- **management/scoring.py**: Gestion de la notation

#### Autres vues
- **competitions.py**: Vues des compétitions
- **competition_management_pro.py**: Gestion avancée des compétitions
- **standalone_scoring.py**: Vues pour le système de notation autonome
- **notifications.py**: Vues pour les notifications

### 4. URLs (Routes)

Les routes suivantes ont été modifiées:

- **__init__.py**: Routes principales de l'application
- **club.py**: Routes pour les fonctionnalités club
- **combat.py**: Routes pour le module de combat
- **competitions.py**: Routes pour les compétitions
- **dashboard.py**: Routes pour les dashboards
- **notifications.py**: Routes pour les notifications
- Et autres routes modifiées

### 5. Templates (Templates HTML)

Les templates suivants ont été modifiés:

- Templates pour les comptes (login, logout, signup)
- Templates pour l'administration (batch_translate, deepl_status, smart_import, translation_dashboard)
- Templates pour les catégories (category_form, confirm_delete, form, list)
- Templates pour les clubs (assign_grade, assign_role_form, attendance_list, create_user_form, practitioner_form)
- Templates pour les dashboards (base.html)
- Et autres templates modifiés

### 6. Utils (Utilitaires)

Les utilitaires suivants ont été modifiés:

- **decorators.py**: Décorateurs personnalisés
- **permission_helpers.py**: Helpers pour les permissions
- **custom_filters.py**: Filtres de template personnalisés
- Et autres utilitaires modifiés

### 7. Templatetags (Tags de template)

Les tags de template suivants ont été modifiés:

- **competition_tags.py**: Tags pour les compétitions
- **feature_tags.py**: Tags pour les fonctionnalités
- **grade_tags.py**: Tags pour les grades
- **translation_helpers.py**: Helpers pour les traductions

## Fichiers exclus

Les fichiers suivants ont été **exclus** du package car ils ne sont pas essentiels:

- Fichiers de backup (*.backup, *_backup, Backup/)
- Fichiers de correction (*_fix.py, *_fixed.py)
- Fichiers d'urgence (*_emergency.py)
- Fichiers corrompus (*_corrupted.py)
- Fichiers de copie (* copy.py)
- Fichiers .py.py (doublons)
- Fichiers dans urls_bak/
- Scripts de correction (coach_forms_fix.py, etc.)

## Installation sur la production

### Prérequis

1. Accès SSH au serveur de production
2. Accès au répertoire de l'application Django
3. Permissions d'écriture sur les fichiers de l'application
4. Backup récent de la base de données

### Étapes d'installation

1. **Transférer le package sur le serveur de production**
   ```bash
   scp production_update_november_YYYYMMDD_HHMMSS.tar.gz user@production-server:/tmp/
   ```

2. **Se connecter au serveur de production**
   ```bash
   ssh user@production-server
   ```

3. **Extraire le package**
   ```bash
   cd /tmp
   tar -xzf production_update_november_YYYYMMDD_HHMMSS.tar.gz
   cd production_update_november_YYYYMMDD_HHMMSS
   ```

4. **Modifier le script de déploiement**
   Éditer `deploy_to_production.sh` et modifier la variable `PROJECT_ROOT` pour pointer vers le répertoire de production:
   ```bash
   PROJECT_ROOT="/path/to/production/martialcomp"  # MODIFIER ICI
   ```

5. **Exécuter le script de déploiement**
   ```bash
   ./deploy_to_production.sh
   ```

6. **Post-déploiement**
   ```bash
   # Activer l'environnement virtuel si nécessaire
   source /path/to/venv/bin/activate
   
   # Exécuter les migrations si nécessaire
   python manage.py migrate
   
   # Collecter les fichiers statiques
   python manage.py collectstatic --noinput
   
   # Redémarrer l'application
   sudo systemctl restart gunicorn  # ou uwsgi, ou autre
   ```

## Vérification post-déploiement

1. **Vérifier les logs**
   ```bash
   tail -f /var/log/gunicorn/error.log
   # ou
   tail -f /var/log/uwsgi/app.log
   ```

2. **Tester les fonctionnalités principales**
   - Connexion/Déconnexion
   - Dashboard club
   - Gestion des pratiquants
   - Gestion des compétitions
   - Interface de combat
   - Système de notation

3. **Vérifier les erreurs dans l'interface**
   - Ouvrir le site en production
   - Naviguer dans les différentes sections
   - Vérifier qu'il n'y a pas d'erreurs 500

## Rollback

En cas de problème, le backup est automatiquement créé dans le répertoire `backup_YYYYMMDD_HHMMSS` lors du déploiement.

Pour restaurer:

```bash
cd /path/to/production/martialcomp
cp -r ../backup_YYYYMMDD_HHMMSS/* .
```

Puis redémarrer l'application.

## Notes importantes

1. **Migrations de base de données**: Les migrations ne sont pas incluses dans ce package. Si de nouvelles migrations ont été créées depuis le 1er novembre, elles doivent être exécutées séparément.

2. **Fichiers statiques**: Les fichiers statiques (CSS, JS, images) ne sont pas inclus dans ce package. Utiliser `collectstatic` après le déploiement.

3. **Fichiers de configuration**: Les fichiers de configuration (settings.py, urls.py principal, etc.) ne sont pas inclus dans ce package.

4. **Dépendances**: Vérifier que toutes les dépendances Python sont installées et à jour.

5. **Tests**: Il est recommandé de tester le package sur un environnement de staging avant de le déployer en production.

## Support

En cas de problème lors du déploiement:

1. Vérifier les logs de l'application
2. Vérifier les permissions des fichiers
3. Vérifier que toutes les dépendances sont installées
4. Vérifier que les migrations sont à jour
5. Restaurer le backup si nécessaire

## Historique des modifications

Les modifications incluses dans ce package proviennent des commits Git depuis le 1er novembre 2024. Pour voir l'historique détaillé:

```bash
git log --since="2024-11-01" --oneline
```

## Statistiques

- **Nombre de fichiers inclus**: ~186 fichiers
- **Types de fichiers**: Python (.py), HTML (.html), Markdown (.md)
- **Taille approximative**: Variable selon les modifications

## Avertissements

⚠️ **IMPORTANT**: 
- Toujours faire un backup complet avant le déploiement
- Tester sur un environnement de staging si possible
- Vérifier les logs après le déploiement
- Avoir un plan de rollback prêt

## Conclusion

Ce package permet d'aligner la production avec les dernières mises à jour du développement depuis le 1er novembre 2024. Il contient uniquement les fichiers essentiels de l'application "Compétitions", en excluant les scripts de correction et les fichiers de backup.

Pour toute question ou problème, consulter les logs de l'application et vérifier que toutes les étapes d'installation ont été suivies correctement.
