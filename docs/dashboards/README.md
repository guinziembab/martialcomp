# Tableaux de Bord MartialComp

## Introduction

Ce répertoire contient la documentation complète des différents tableaux de bord (dashboards) disponibles dans l'application MartialComp. Chaque type d'utilisateur dispose d'un tableau de bord spécifique à son rôle, offrant des fonctionnalités adaptées à ses besoins.

## Types de Tableaux de Bord

MartialComp propose plusieurs tableaux de bord, chacun conçu pour un rôle spécifique :

1. [**Dashboard Participant**](./participants/README.md) - Pour les pratiquants d'arts martiaux qui participent aux compétitions
2. [**Dashboard Club**](./clubs/README.md) - Pour les gestionnaires de clubs et leurs administrateurs
3. [**Dashboard Fédération**](./federations/README.md) - Pour les administrateurs de fédérations
4. [**Dashboard Arbitre/Juge**](./referees/README.md) - Pour les arbitres et juges qui évaluent les compétitions
5. [**Dashboard Entraîneur Multidiscipline**](./coaches/README.md) - Pour les entraîneurs qui gèrent plusieurs disciplines
6. [**Dashboard Combat**](./combat/README.md) - Interface spécialisée pour la gestion des combats

## Accès aux Tableaux de Bord

Chaque utilisateur est automatiquement redirigé vers le tableau de bord correspondant à son rôle après la connexion. La redirection est gérée par la vue `dashboard` dans le fichier `competitions/views/dashboard/base.py`.

## Structure Commune des Tableaux de Bord

Tous les tableaux de bord partagent une structure commune :

- **En-tête** : Affiche le nom de l'utilisateur, le rôle, et donne accès aux paramètres et à la déconnexion
- **Barre latérale** : Navigation vers les différentes sections du tableau de bord
- **Contenu principal** : Affiche les informations et fonctionnalités spécifiques à chaque section
- **Pied de page** : Informations sur la version de l'application et liens utiles

## Personnalisation des Tableaux de Bord

Les utilisateurs peuvent personnaliser certains aspects de leur tableau de bord :
- Choix des widgets affichés sur la page d'accueil
- Ordre d'affichage des informations
- Préférences de notification

## Fonctionnalités Communes

Tous les tableaux de bord offrent ces fonctionnalités de base :
- Vue d'ensemble avec statistiques clés
- Notifications et alertes
- Gestion du profil utilisateur
- Calendrier des événements à venir
- Accès à la documentation

## Support Multilingue

Tous les tableaux de bord prennent en charge le multilinguisme et sont disponibles dans les langues suivantes :
- Français (fr) - Langue par défaut
- Anglais (en)
- Espagnol (es)
- Italien (it)
- Allemand (de)
- Norvégien (no)
- Japonais (ja)
- Chinois (zh)
- Hindi (hi)
- Arabe (ar)
- Swahili (sw)
- Amharique (am)
- Zoulou (zu)
- Yoruba (yo)
- Portugais (pt)
- Coréen (ko)

## Conception Technique

Les tableaux de bord sont implémentés en utilisant :
- Django pour le backend
- HTML/CSS/JavaScript pour le frontend
- Bootstrap pour la mise en page responsive
- Technologie AJAX pour les mises à jour dynamiques

## Documentation Détaillée

Pour plus de détails sur chaque tableau de bord, consultez les liens ci-dessus ou explorez les sous-dossiers de ce répertoire.