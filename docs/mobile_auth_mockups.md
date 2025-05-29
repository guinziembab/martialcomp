# Maquettes des Écrans d'Authentification - MartialComp Mobile

## Vue d'ensemble

Ces spécifications détaillent les maquettes pour les écrans d'authentification de l'application mobile MartialComp. Elles sont destinées aux designers UI/UX pour créer les maquettes visuelles et aux développeurs pour l'implémentation.

## Palette de Couleurs (Provisoire)

- **Primaire**: `#3F51B5` (Indigo)
- **Secondaire**: `#FF4081` (Rose)
- **Fond**: `#FFFFFF` (Blanc)
- **Fond Sombre**: `#121212` (Pour mode sombre)
- **Texte Principal**: `#212121` (Gris très foncé)
- **Texte Secondaire**: `#757575` (Gris moyen)
- **Succès**: `#4CAF50` (Vert)
- **Erreur**: `#F44336` (Rouge)
- **Avertissement**: `#FFC107` (Ambre)
- **Info**: `#2196F3` (Bleu)

## Typographie

- **Famille de police**: Roboto (Android) / San Francisco (iOS)
- **Titres**: Bold, 24sp
- **Sous-titres**: Medium, 18sp
- **Corps de texte**: Regular, 16sp
- **Petits textes**: Regular, 14sp
- **Très petits textes**: Regular, 12sp

## Écrans d'Authentification

### AUTH-01: Splash Screen

**Objectif**: Afficher le logo de l'application pendant le chargement initial

**Contenu**:
- Logo MartialComp centré (200dp x 200dp)
- Nom de l'application sous le logo (typographie: 28sp, Bold)
- Indicateur de chargement circulaire sous le nom
- Fond uni de couleur primaire ou dégradé (du primaire vers une teinte plus claire)

**Comportement**:
- Affichage pendant 2-3 secondes
- Transition fluide vers l'écran de connexion ou tableau de bord si déjà connecté
- Pas d'interaction utilisateur requise

**Variantes**:
- Mode Portrait (priorité)
- Mode Paysage (optionnel)

---

### AUTH-02: Écran de Connexion

**Objectif**: Permettre à l'utilisateur de se connecter à l'application

**Structure**:
- Logo MartialComp en haut (plus petit que sur le splash screen, 120dp x 120dp)
- Titre "Connexion" sous le logo
- Formulaire de connexion au centre
- Options supplémentaires en bas

**Formulaire**:
- Champ Email/Nom d'utilisateur (avec icône et validation)
- Champ Mot de passe (avec icône, masquage et option afficher)
- Case à cocher "Se souvenir de moi"
- Bouton "Connexion" sur toute la largeur, couleur primaire
- Indicateur de chargement pendant la connexion

**Options supplémentaires**:
- Lien "Mot de passe oublié ?" centré sous le bouton
- Séparateur avec texte "OU"
- Texte "Pas encore de compte ?" suivi d'un bouton/lien "S'inscrire"

**États**:
- État initial (formulaire vide)
- État d'erreur de validation (ex: email invalide)
- État d'erreur d'authentification (ex: mauvais mot de passe)
- État de chargement (pendant la connexion)

**Comportement**:
- Validation des champs à la soumission
- Masquage/affichage du mot de passe
- Animation de transition vers l'écran suivant

---

### AUTH-03: Écran d'Inscription

**Objectif**: Permettre à un nouvel utilisateur de créer un compte

**Structure**:
- Logo MartialComp en haut (plus petit que sur le splash screen, 100dp x 100dp)
- Titre "Créer un compte" sous le logo
- Formulaire d'inscription multi-étapes
- Options supplémentaires en bas

**Formulaire (Étape 1 - Informations de base)**:
- Champ Prénom (avec validation)
- Champ Nom (avec validation)
- Champ Email (avec validation)
- Champ Mot de passe (avec exigences de complexité)
- Champ Confirmation du mot de passe
- Bouton "Continuer" sur toute la largeur, couleur primaire

**Formulaire (Étape 2 - Informations spécifiques)**:
- Sélecteur de date de naissance
- Menu déroulant pour le club/fédération
- Champ Numéro de licence (optionnel)
- Sélecteur de discipline principale
- Bouton "S'inscrire" sur toute la largeur, couleur primaire

**Options supplémentaires**:
- Indicateurs d'étape (1/2, 2/2)
- Bouton Retour pour revenir à l'étape précédente
- Texte "Déjà un compte ?" suivi d'un bouton/lien "Se connecter"
- Cases à cocher pour accepter les conditions d'utilisation et la politique de confidentialité

**États**:
- États pour chaque étape du formulaire
- États d'erreur de validation pour chaque champ
- État de chargement pendant l'inscription
- État de succès après inscription

**Comportement**:
- Validation des champs à chaque étape
- Navigation entre les étapes
- Soumission finale du formulaire
- Redirection vers l'écran de confirmation ou d'activation

---

### AUTH-04: Récupération de Mot de Passe

**Objectif**: Permettre à l'utilisateur de réinitialiser son mot de passe

**Structure**:
- Logo MartialComp en haut (plus petit, 80dp x 80dp)
- Titre "Récupération de mot de passe"
- Texte explicatif
- Formulaire de récupération
- Bouton de retour en haut à gauche

**Formulaire (Étape 1 - Demande)**:
- Champ Email (avec validation)
- Bouton "Envoyer le lien de réinitialisation"
- Animation de chargement pendant l'envoi

**Formulaire (Étape 2 - Confirmation)**:
- Message de confirmation
- Illustration d'email envoyé
- Instructions pour vérifier la boîte de réception
- Bouton "Retour à la connexion"
- Lien "Renvoyer l'email"

**États**:
- État initial (formulaire vide)
- État d'erreur (email non trouvé)
- État de chargement
- État de confirmation (email envoyé)

**Comportement**:
- Validation de l'email
- Envoi de la demande de réinitialisation
- Affichage du message de confirmation
- Option pour renvoyer l'email

---

### AUTH-05: Sélection de Tenant

**Objectif**: Permettre à l'utilisateur de choisir son organisation (pour multi-tenant)

**Structure**:
- Logo MartialComp en haut (petit, 60dp x 60dp)
- Titre "Sélectionnez votre organisation"
- Texte explicatif
- Liste des organisations disponibles
- Barre de recherche en haut de la liste

**Liste des organisations**:
- Cartes pour chaque organisation avec:
  - Logo de l'organisation (si disponible)
  - Nom de l'organisation en gras
  - Type d'organisation (fédération, club, etc.)
  - Localisation (ville/pays)
- Pagination ou chargement à la demande si nombreuses

**États**:
- État initial (liste complète)
- État de recherche (résultats filtrés)
- État de chargement
- État vide (aucun résultat)

**Comportement**:
- Filtrage en temps réel lors de la recherche
- Sélection d'une organisation par tap
- Sauvegarde de la sélection et redirection vers le tableau de bord
- Option "Se souvenir de ce choix" pour éviter la sélection future

---

### AUTH-06: Activation du Compte

**Objectif**: Confirmer l'activation du compte après inscription

**Structure**:
- Logo MartialComp en haut (petit, 60dp x 60dp)
- Titre "Activation du compte"
- Illustration de validation/activation
- Message de statut
- Options suivantes

**Contenu pour compte activé**:
- Icône de succès (coche verte)
- Message "Votre compte a été activé avec succès"
- Bouton "Continuer vers l'application"

**Contenu pour activation en attente**:
- Icône d'attente (horloge ou sablier)
- Message "Vérifiez votre email pour activer votre compte"
- Instructions détaillées
- Bouton "J'ai déjà activé mon compte"
- Lien "Renvoyer l'email d'activation"

**États**:
- État de succès (compte activé)
- État d'attente (activation en cours)
- État d'erreur (problème d'activation)

**Comportement**:
- Vérification du statut d'activation
- Redirection vers le tableau de bord après activation
- Option pour renvoyer l'email d'activation

## Spécifications Techniques

### Composants Réutilisables

1. **InputField**
   - Label flottant
   - Icône à gauche
   - Message d'erreur en dessous
   - Animation de focus

2. **ActionButton**
   - Bouton principal sur toute la largeur
   - États: normal, désactivé, chargement
   - Animation de pression
   - Élévation légère

3. **LinkText**
   - Texte cliquable
   - Couleur primaire
   - Sans soulignement
   - Animation de pression

4. **FormContainer**
   - Conteneur avec padding
   - Fond blanc légèrement élevé
   - Coins arrondis
   - Ombre légère

5. **ProgressIndicator**
   - Spinner circulaire
   - Couleur primaire
   - Taille adaptable

### Adaptations Responsives

**Smartphones (5"-7")**:
- Éléments empilés verticalement
- Formulaires sur toute la largeur
- Padding horizontal: 24dp
- Espacement vertical: 16dp

**Tablettes (7"-10")**:
- Formulaires centrés avec largeur maximale de 400dp
- Padding horizontal: 32dp
- Espacement vertical: 24dp

**Grands écrans (>10")**:
- Layout en deux colonnes possible
- Formulaires centrés avec largeur maximale de 500dp
- Padding horizontal: 48dp
- Espacement vertical: 32dp

### Animations et Transitions

1. **Transition entre écrans**:
   - Fade + slide pour la navigation avant
   - Slide inverse pour retour en arrière
   - Durée: 300ms

2. **Feedback d'interaction**:
   - Ripple effect sur les boutons (Android)
   - Highlight sur les boutons (iOS)
   - Scale légère sur les cartes sélectionnables

3. **Animations d'état**:
   - Fade pour afficher/masquer les messages d'erreur
   - Slide pour les changements d'étape dans les formulaires
   - Pulse pour les indicateurs d'attention

## Consignes pour l'Implémentation

1. **Accessibilité**:
   - Tous les champs doivent avoir des labels accessibles
   - Contraste suffisant pour tous les textes
   - Support du mode texte agrandi
   - Ordre de tabulation logique

2. **Internationalisation**:
   - Prévoir l'espace pour les textes plus longs dans d'autres langues
   - Supporter le RTL pour l'arabe
   - Utiliser des chaînes localisables pour tous les textes

3. **Performance**:
   - Optimiser les assets graphiques
   - Minimiser les reflows pendant les animations
   - Gérer efficacement le cycle de vie des écrans

4. **Tests**:
   - Tester sur différentes tailles d'écran
   - Vérifier le comportement avec différentes langues
   - Valider les cas d'erreur et les états de chargement