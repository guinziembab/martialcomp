# DIRECTIVE DE MISE À JOUR - MARTIALCOMP.COM

## CONTEXTE
En nous basant sur les retours utilisateurs de Théophile Akoman, Maxence, ainsi que le dernier retour concernant les problèmes de profil et l'ajout de disciplines, nous avons identifié plusieurs problèmes et améliorations nécessaires pour optimiser l'expérience utilisateur sur la plateforme MartialComp.

## CORRECTIFS PRIORITAIRES

### 1. GESTION DES PROFILS UTILISATEURS
- **Correction des profils utilisateurs**: Résoudre de toute urgence le problème empêchant les utilisateurs de modifier leurs profils après inscription
  - Implémenter une interface claire et accessible pour la modification des informations personnelles
  - Permettre la modification du mot de passe via cette interface
  - S'assurer que l'interface utilisateur reste accessible et visible après l'inscription
- **Navigation vers le profil**: Ajouter un lien visible et permanent vers la page de profil dans la barre de navigation principale

### 2. EXPANSION DES DISCIPLINES D'ARTS MARTIAUX
- **Ajout de nouvelles disciplines**: Intégrer de nouvelles disciplines d'arts martiaux actuellement manquantes:
  - Nihon Tai Jitsu
  - Viet Vu Dao
  - Et autres disciplines demandées par les utilisateurs
- **Paramètres multi-styles**: Améliorer le système pour permettre aux utilisateurs pratiquant plusieurs styles d'arts martiaux de les gérer efficacement
  - Permettre l'affiliation à plusieurs disciplines simultanément
  - Adapter les interfaces pour afficher et gérer ces multiples affiliations

### 3. SYSTÈME DE GESTION DES CLUBS
- **Modification des informations club**: Créer une interface permettant aux responsables de club de modifier les informations de leur club après la création initiale
- **Interface de mise à jour**: Ajouter un bouton "Modifier" visible dans le profil du club avec accès à tous les champs modifiables

### 4. SYSTÈME DE QR CODES ET PRÉSENCE
- **Alternative manuelle**: Implémenter une interface permettant aux responsables de club de cocher manuellement la présence des élèves sans nécessiter un scan de QR code
  - Créer une liste des pratiquants avec cases à cocher
  - Ajouter un bouton "Marquer présent" pour chaque pratiquant
  - Permettre la sélection multiple pour marquer plusieurs présences simultanément
- **Correction redirection QR code**: S'assurer que le QR code d'une organisation redirige correctement vers la page d'inscription du club concerné

### 5. GESTION DES GRADES
- **Correction des prérequis**: Corriger l'incohérence où le système exige un 6e dang pour passer le 3e cap bleu
- **Filtrage des grades**: Supprimer les grades non liés au QKD dans les options de création de passage de grade
- **Ajout des grades Co Vo Dao**: Implémenter la gestion des grades Co Vo Dao comme demandé par l'utilisateur

### 6. NAVIGATION ET INTERFACE UTILISATEUR
- **Dashboard Shop**: Ajouter dans la barre latérale gauche du dashboard Shop un bouton explicite de retour au tableau de bord principal
- **Cohérence de la barre latérale**: 
  - Maintenir l'affichage de la barre latérale de manière cohérente dans toute l'application
  - Uniformiser le comportement d'affichage/masquage de la barre latérale
  - S'assurer que l'icône à trois barres (hamburger) ouvre systématiquement la barre latérale
- **Ergonomie des formulaires**: 
  - Revoir l'interface de création de pratique pour avoir soit un bouton "Suivant" en bas de page, soit regrouper tous les champs sur une seule page

## AMÉLIORATIONS FONCTIONNELLES

### 1. SÉCURITÉ ET AUTHENTIFICATION
- **Récupération de mot de passe**: Implémenter la fonction "mot de passe oublié"

### 2. GESTION DES PRATIQUANTS
- **Attribution des qualificatifs**: Permettre aux responsables de club d'ajouter des qualificatifs à leurs pratiquants
- **Gestion des rôles**: Corriger le problème d'attribution du rôle requis pour accéder à la rubrique "compétition"
- **Gestion documentaire**: Ajouter la possibilité de lier des documents annexes lors de l'inscription d'un pratiquant (ex: droit à l'image, fiche d'assurance)

### 3. GESTION DES ÉVÉNEMENTS
- **Intégration dashboard**: S'assurer que tous les événements créés apparaissent correctement dans le dashboard
- **Simplification du formulaire**: Retirer le champ "organisation" du formulaire de création d'événement et utiliser par défaut l'organisation courante
- **Notifications**: 
  - Éliminer le problème de doubles notifications
  - Implémenter un système de filtre permettant aux utilisateurs de sélectionner les types d'événements qui les intéressent
  - Offrir des options de personnalisation plus granulaires pour les rappels

### 4. PHOTOS ET MÉDIAS
- **Aperçu photos**: Corriger le dysfonctionnement de l'aperçu de la photo de profil lors de la création d'un pratiquant

### 5. IMPORTATION EN MASSE
- **Amélioration du système**: Corriger le système d'importation en masse actuel
- **Exploration IA**: Étudier l'utilisation d'IA pour améliorer l'importation en masse en détectant automatiquement les structures de fichiers et en suggérant des mappages de colonnes

### 6. LIENS DÉFECTUEUX
- **Section Coach**: Réparer le lien mort dans la section Coach
- **Clubs affiliés**: Corriger l'affichage NOK des clubs affiliés dans la section fédération

## PLAN D'IMPLÉMENTATION RÉVISÉ

### PHASE URGENTE - CORRECTIFS CRITIQUES (Délai: 1 semaine)
1. Correction des problèmes de modification de profil utilisateur
2. Correction de l'édition des informations de club
3. Implémentation du contrôle de présence manuel

### PHASE 1 - CORRECTIFS ESSENTIELS (Délai: 2 semaines)
1. Ajout des disciplines manquantes (Nihon Tai Jitsu, Viet Vu Dao, etc.)
2. Mise en place de la gestion multi-styles pour les utilisateurs
3. Correction de la redirection des QR codes
4. Correction des problèmes de grades (prérequis et filtrage)
5. Ajout du bouton de retour au dashboard principal depuis Shop
6. Correction du lien mort dans la section Coach

### PHASE 2 - AMÉLIORATIONS ESSENTIELLES (Délai: 3 semaines)
1. Implémentation de la fonction "mot de passe oublié"
2. Correction des problèmes de notifications (doublons)
3. Ajout de la gestion des grades Co Vo Dao
4. Correction de l'aperçu des photos de profil
5. Amélioration de l'ergonomie des formulaires multi-onglets
6. Correction de l'affichage des événements dans le dashboard

### PHASE 3 - OPTIMISATIONS (Délai: 4 semaines)
1. Implémentation de la gestion documentaire pour les pratiquants
2. Correction des problèmes d'attribution de rôles et qualificatifs
3. Amélioration de la cohérence de la barre latérale
4. Simplification du formulaire d'événement
5. Personnalisation avancée des notifications d'événements

### PHASE 4 - INNOVATIONS (Délai: 6 semaines)
1. Exploration et intégration d'IA pour l'importation en masse
2. Amélioration des rapprochements bancaires avec IA
3. Optimisation globale des performances

## SPÉCIFICATIONS TECHNIQUES

### 1. PROFILS UTILISATEURS
- Corriger la vue `UserProfileUpdateView` pour assurer son accessibilité après l'inscription
- Vérifier les redirections post-inscription qui doivent mener à une page où l'interface reste accessible
- Ajouter un lien permanent "Mon profil" dans le menu principal de l'application

### 2. DISCIPLINES D'ARTS MARTIAUX
- Mettre à jour le modèle `Discipline` dans l'application `competitions` pour inclure les nouvelles disciplines
- Assurer que les relations ManyToMany entre utilisateurs et disciplines fonctionnent correctement
- Adapter l'interface utilisateur pour permettre la sélection et l'affichage de plusieurs disciplines

### 3. IMPLÉMENTATION MULTI-STYLES
- Créer un formulaire dédié permettant aux utilisateurs d'ajouter/supprimer des styles
- Adapter les tableaux de bord pour visualiser et gérer les informations relatives à chaque style
- Modifier le modèle de données pour supporter efficacement la gestion multi-styles

## MÉTHODOLOGIE DE DÉVELOPPEMENT
1. Chaque correction doit être testée dans un environnement de développement avant déploiement
2. Implémenter des tests automatisés pour chaque fonctionnalité corrigée
3. Documenter toutes les modifications apportées
4. Recueillir des retours utilisateurs après chaque déploiement majeur

## TESTS ET VALIDATION
1. Créer un groupe de beta-testeurs incluant Théophile Akoman, Maxence et l'utilisateur ayant signalé les problèmes de profil
2. Mettre en place un système de suivi des bugs et suggestions
3. Effectuer des tests de régression après chaque mise à jour
4. Tester spécifiquement la gestion multi-styles avec des utilisateurs pratiquant plusieurs disciplines

## CONCLUSION
Les corrections et améliorations proposées visent à résoudre les problèmes signalés par les utilisateurs et à améliorer l'expérience globale sur la plateforme MartialComp. Cette directive de mise à jour révisée met l'accent sur les problèmes critiques de gestion de profil et l'expansion des disciplines, tout en maintenant le plan d'action pour les autres améliorations identifiées précédemment.

La priorité immédiate est de corriger les problèmes empêchant les utilisateurs de modifier leurs profils et d'ajouter les disciplines manquantes, car ces éléments impactent directement l'expérience utilisateur dès l'inscription.
