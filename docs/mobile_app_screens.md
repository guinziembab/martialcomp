# Définition des Écrans de l'Application Mobile MartialComp

## 1. Introduction

Ce document définit l'ensemble des écrans nécessaires pour l'application mobile MartialComp. Chaque écran est décrit avec son objectif, ses composants principaux et ses interactions.

## 2. Architecture de Navigation

L'application sera structurée autour de 5 sections principales accessibles via une barre de navigation en bas:

1. **Accueil** - Tableau de bord principal adapté au rôle de l'utilisateur
2. **Scanner** - Outil de scan de QR codes pour diverses fonctionnalités
3. **Compétitions** - Liste et détails des compétitions
4. **Profil** - Informations personnelles et options
5. **Plus** - Fonctionnalités supplémentaires et paramètres

## 3. Écrans par Section

### 3.1 Section Authentification

| ID | Nom | Description | Priorité |
|----|-----|-------------|----------|
| AUTH-01 | Splash Screen | Écran de démarrage avec logo MartialComp | Haute |
| AUTH-02 | Connexion | Formulaire de connexion avec email/mot de passe | Haute |
| AUTH-03 | Inscription | Formulaire d'inscription pour nouveaux utilisateurs | Haute |
| AUTH-04 | Récupération Mot de Passe | Processus de récupération de mot de passe | Moyenne |
| AUTH-05 | Sélection Tenant | Choix de l'organisation (pour multi-tenant) | Haute |
| AUTH-06 | Activation Compte | Activation après inscription par email | Basse |

### 3.2 Section Accueil

| ID | Nom | Description | Priorité |
|----|-----|-------------|----------|
| HOME-01 | Tableau de Bord (Pratiquant) | Vue personnalisée pour pratiquant avec prochains événements | Haute |
| HOME-02 | Tableau de Bord (Juge) | Vue personnalisée pour juge avec événements à juger | Haute |
| HOME-03 | Tableau de Bord (Coach) | Vue personnalisée pour coach avec liste d'élèves | Haute |
| HOME-04 | Tableau de Bord (Admin) | Vue administrateur avec statistiques | Moyenne |
| HOME-05 | Notifications | Liste des notifications avec marquage lu/non-lu | Moyenne |
| HOME-06 | Calendrier | Vue calendrier des événements à venir | Basse |

### 3.3 Section Scanner

| ID | Nom | Description | Priorité |
|----|-----|-------------|----------|
| SCAN-01 | Scanner QR | Écran principal de scan avec caméra | Haute |
| SCAN-02 | Type de Scan | Sélection du type de scan (présence, compétition, etc.) | Haute |
| SCAN-03 | Résultat Scan | Affichage du résultat après scan | Haute |
| SCAN-04 | Historique Scans | Liste des scans effectués | Moyenne |
| SCAN-05 | Scans Hors-ligne | Liste des scans en attente de synchronisation | Haute |
| SCAN-06 | Mon QR Code | Affichage du QR code personnel du pratiquant | Haute |

### 3.4 Section Compétitions

| ID | Nom | Description | Priorité |
|----|-----|-------------|----------|
| COMP-01 | Liste Compétitions | Liste des compétitions disponibles | Haute |
| COMP-02 | Détail Compétition | Informations détaillées sur une compétition | Haute |
| COMP-03 | Inscription Compétition | Formulaire d'inscription à une compétition | Haute |
| COMP-04 | Résultats | Affichage des résultats d'une compétition | Haute |
| COMP-05 | Catégories | Liste des catégories d'une compétition | Moyenne |
| COMP-06 | Planning | Planning des passages | Haute |
| COMP-07 | Notation (Juge) | Interface de notation pour les juges | Très Haute |
| COMP-08 | Carte Lieu | Carte avec localisation de l'événement | Basse |

### 3.5 Section Profil

| ID | Nom | Description | Priorité |
|----|-----|-------------|----------|
| PROF-01 | Mon Profil | Informations personnelles de l'utilisateur | Haute |
| PROF-02 | Édition Profil | Modification des informations personnelles | Haute |
| PROF-03 | Profil Hors-ligne | Génération/affichage du profil hors-ligne | Haute |
| PROF-04 | Grades | Affichage des grades et progression | Moyenne |
| PROF-05 | Licences | Gestion des licences | Moyenne |
| PROF-06 | Historique | Historique des compétitions et résultats | Basse |
| PROF-07 | Documents | Certificats médicaux et autres documents | Moyenne |

### 3.6 Section Plus

| ID | Nom | Description | Priorité |
|----|-----|-------------|----------|
| MORE-01 | Menu Plus | Menu principal des options supplémentaires | Haute |
| MORE-02 | Paramètres | Paramètres de l'application | Haute |
| MORE-03 | Mode Hors-ligne | Configuration du mode hors-ligne | Haute |
| MORE-04 | Aide | Documentation et aide | Moyenne |
| MORE-05 | À Propos | Informations sur l'application | Basse |
| MORE-06 | Déconnexion | Option de déconnexion | Haute |
| MORE-07 | Langue | Sélection de la langue | Moyenne |
| MORE-08 | Thème | Sélection du thème (clair/sombre) | Basse |

## 4. Flux de Navigation Principaux

### 4.1 Flux d'Authentification
1. Splash Screen
2. Connexion/Inscription
3. (Optionnel) Sélection Tenant
4. Tableau de Bord correspondant au rôle

### 4.2 Flux de Scan QR
1. Sélection Type de Scan
2. Scanner QR
3. Résultat Scan
4. (Optionnel) Historique Scans

### 4.3 Flux de Compétition
1. Liste Compétitions
2. Détail Compétition
3. Inscription Compétition / Résultats / Planning

### 4.4 Flux de Notation (Juge)
1. Tableau de Bord Juge
2. Sélection Compétition
3. Interface de Notation

### 4.5 Flux de Profil Hors-ligne
1. Mon Profil
2. Profil Hors-ligne
3. Génération QR Code

## 5. Composants UI Réutilisables

| Composant | Description | Utilisation |
|-----------|-------------|-------------|
| Header | En-tête avec titre et boutons de navigation | Tous les écrans |
| BottomNav | Barre de navigation principale | Tous les écrans (post-auth) |
| Card | Carte d'information | Tableaux de bord, listes |
| Button | Bouton d'action | Tous les écrans |
| SearchBar | Barre de recherche | Écrans de liste |
| Avatar | Avatar utilisateur | Profil, tableaux de bord |
| QRScanner | Composant de scan QR | Écrans de scan |
| StatusBadge | Badge de statut (en ligne/hors-ligne) | Tous les écrans |
| TabBar | Barre d'onglets | Écrans avec sous-sections |
| ModalPopup | Fenêtre modale | Diverses confirmations |

## 6. États Spéciaux

### 6.1 État Hors-ligne
- Indicateur visuel clair (badge, bannière)
- Accès limité aux fonctionnalités disponibles hors-ligne
- File d'attente visible pour les opérations en attente de synchronisation

### 6.2 État Chargement
- Indicateurs de chargement (spinners, barres de progression)
- Squelettes de chargement pour les listes et cartes

### 6.3 État Erreur
- Messages d'erreur clairs
- Options de réessai
- Journalisation des erreurs pour débogage

## 7. Adaptations d'Affichage

### 7.1 Orientation
- La plupart des écrans en mode portrait
- Notation des juges et certains tableaux optimisés pour le mode paysage

### 7.2 Taille d'Écran
- Conception adaptative pour smartphones (5" - 7")
- Optimisations pour tablettes (7" - 12")

### 7.3 Accessibilité
- Support des tailles de texte dynamiques
- Contraste suffisant pour lisibilité
- Zones tactiles suffisamment grandes

## 8. Priorités de Développement

1. **MVP (Phase 1)**
   - Authentification complète
   - Tableau de bord basique
   - Scanner QR avec support hors-ligne
   - Profil hors-ligne
   - Menu Plus minimal

2. **Phase 2**
   - Compétitions (liste et détails)
   - Améliorations du tableau de bord
   - Historique des scans
   - Édition de profil

3. **Phase 3**
   - Interface de notation pour juges
   - Planning des compétitions
   - Gestion des licences et documents
   - Fonctionnalités avancées

## 9. Annexes

### 9.1 Stockage Local
- Profil utilisateur
- Tokens d'authentification
- Scans hors-ligne
- Données de base des compétitions récentes

### 9.2 Permissions Requises
- Caméra (scan QR)
- Stockage (documents et QR codes)
- Notifications
- (Optionnel) Localisation pour carte des lieux