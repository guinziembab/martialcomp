# Module de Planification d'Événements pour MartialComp

Ce module permet de créer et gérer des sondages pour la planification d'événements dans l'application MartialComp, inspiré du fonctionnement de Doodle.

## Fonctionnalités

1. **Création de sondages d'événements**
   - Proposer plusieurs options de dates et heures
   - Choisir le type de réponse (Oui/Non, Oui/Peut-être/Non)
   - Paramétrer la visibilité des participants et des votes
   - Définir une date d'expiration pour le sondage

2. **Participation aux sondages**
   - Répondre aux options proposées
   - Ajouter des commentaires (si activé)
   - Répondre de manière anonyme (si activé)

3. **Finalisation d'événements**
   - Sélectionner l'option la plus populaire
   - Création automatique d'un événement à la date choisie
   - Conservation des statistiques de participation

4. **Rappels d'événements**
   - Créer des rappels personnalisés
   - Définir quand envoyer les rappels (durée avant l'événement ou date précise)
   - Sélectionner les destinataires spécifiques

5. **Statistiques et analyses**
   - Visualiser les taux de participation
   - Analyser les préférences des participants
   - Comparer les différentes options proposées

## Architecture

### Modèles

- **EventPoll**: Sondage d'événement avec ses paramètres
- **PollOption**: Options de date/heure proposées dans un sondage
- **PollResponse**: Réponses des utilisateurs aux options
- **EventReminder**: Rappels configurés pour les événements
- **EventStatistics**: Statistiques sur les sondages et événements

### Intégration

Le module s'intègre avec les modèles existants:
- Utilise le modèle `Event` existant pour créer des événements
- Se connecte aux organisations (clubs, fédérations) via leur modèle
- S'appuie sur le modèle utilisateur de Django

## Installation et Configuration

1. Les modèles ont été ajoutés à l'application `competitions`
2. Une migration a été créée: `0022_add_event_planning_models.py`
3. Les URLs sont configurées dans `competitions/urls/event_planning.py`
4. Les templates sont dans `competitions/templates/competitions/event_planning/`

Pour activer le module:

```bash
# Appliquer les migrations
python manage.py migrate

# Compiler les traductions
python manage.py compilemessages
```

## Utilisation

### Accès au module

Le module est accessible via l'URL `/events/` qui mène à la liste des sondages disponibles.

### Création d'un sondage

1. Accéder à la page de création via `/events/polls/create/`
2. Remplir le formulaire avec les informations du sondage
3. Ajouter au moins une option de date/heure
4. Soumettre le formulaire

### Réponse à un sondage

1. Accéder au sondage via l'URL partagée ou depuis la liste des sondages
2. Indiquer sa disponibilité pour chaque option proposée
3. Ajouter des commentaires si nécessaire
4. Soumettre ses réponses

### Finalisation d'un sondage

1. En tant que créateur ou administrateur, accéder au sondage
2. Sélectionner l'option à finaliser
3. Confirmer la finalisation
4. Un événement sera automatiquement créé ou mis à jour

## Personnalisation

### Traductions

Les traductions françaises sont disponibles dans le fichier `locale/fr/LC_MESSAGES/event_planning.po`.
Pour ajouter d'autres langues, copiez et adaptez ce fichier.

### Styles

Les templates utilisent Bootstrap 5 et peuvent être personnalisés en ajoutant des classes CSS supplémentaires.

## Considérations pour le déploiement

- Assurez-vous que les migrations sont appliquées avant d'utiliser le module
- Les notifications par email nécessitent une configuration SMTP correcte
- Pour les rappels automatiques, un système de tâches comme Celery est recommandé

## Bonnes pratiques d'utilisation

1. **Pour les clubs et fédérations**:
   - Créez des sondages suffisamment à l'avance
   - Limitez le nombre d'options à 5-6 maximum
   - Définissez une date d'expiration raisonnable

2. **Pour les participants**:
   - Répondez rapidement aux sondages pour faciliter la planification
   - Utilisez les commentaires pour indiquer des contraintes spécifiques
   - Consultez régulièrement la liste des sondages actifs

## Support et dépannage

En cas de problème:
1. Vérifiez que toutes les migrations ont été appliquées
2. Assurez-vous que les traductions sont compilées
3. Consultez les logs Django pour identifier les erreurs

Pour toute question ou suggestion, veuillez contacter l'équipe MartialComp.