# Maquettes du Scanner QR - MartialComp Mobile

## Vue d'ensemble

Ces spécifications détaillent les maquettes pour la fonctionnalité de scanner QR de l'application mobile MartialComp, incluant le scan en mode connecté et hors-ligne, ainsi que l'affichage des résultats.

## Écrans du Scanner QR

### SCAN-01: Scanner QR Principal

**Objectif**: Permettre à l'utilisateur de scanner un QR code à l'aide de la caméra

**Structure**:
- Barre supérieure avec:
  - Titre "Scanner QR"
  - Indicateur de statut connexion (icône en ligne/hors-ligne)
  - Bouton d'historique (icône d'horloge)
- Vue caméra plein écran
- Cadre de scan au centre (rectangulaire avec coins spéciaux)
- Texte d'instruction au-dessus du cadre
- Options de scan en bas

**Options de scan**:
- Sélecteur de type de scan (pills ou segments horizontaux)
- Bouton de flash (toggle)
- Bouton d'options avancées (optionnel)

**États de connexion**:
- **En ligne**: Icône verte, pas de bannière
- **Hors-ligne**: Icône rouge + bannière jaune en haut indiquant "Mode hors-ligne - Les scans seront synchronisés plus tard"

**Types de scan disponibles**:
- Présence
- Compétition
- Événement
- Entraînement
- Profil

**Comportement de la caméra**:
- Prévisualisation en temps réel
- Détection automatique des QR codes
- Retour visuel lors de la détection (cadre qui devient vert)
- Vibration/son lors de la détection réussie

**Animations et interactions**:
- Animation de balayage dans le cadre de scan
- Effet de flash lors d'un scan réussi
- Transition fluide vers l'écran de résultat

**Adaptations**:
- Mode paysage: caméra plein écran avec contrôles sur le côté
- Support des différentes proportions de caméra

---

### SCAN-02: Sélection du Type de Scan

**Objectif**: Permettre à l'utilisateur de choisir le type de scan à effectuer

**Design**:
- Intégré dans l'écran principal du scanner (SCAN-01)
- Affichage horizontal sous forme de pills ou segments
- Type actif clairement indiqué (fond coloré, texte en gras)

**Types de scan et icônes**:
- **Présence**: Icône de coche/check-in
- **Compétition**: Icône de médaille/trophée
- **Événement**: Icône de calendrier/événement
- **Entraînement**: Icône d'haltère/arts martiaux
- **Profil**: Icône de personne/carte d'identité

**Comportement**:
- Tap sur un type pour le sélectionner
- Sauvegarde de la préférence pour la prochaine utilisation
- Animation douce lors du changement
- Adaptation des instructions de scan selon le type sélectionné

**États spéciaux**:
- En mode hors-ligne, certains types peuvent être désactivés (grisés)
- Types contextuels: si ouvert depuis une compétition, pré-sélection du type "Compétition"

---

### SCAN-03: Résultat du Scan

**Objectif**: Afficher le résultat d'un scan QR et les actions possibles

**Structure**:
- Header avec titre "Résultat du scan"
- Bannière de statut (succès/échec)
- Carte de résultat principale
- Informations du scan
- Boutons d'action
- Bouton "Scanner à nouveau" en bas

**Bannière de statut**:
- **Succès**: Fond vert, icône de coche, texte "Scan réussi"
- **Échec**: Fond rouge, icône d'erreur, texte décrivant l'erreur
- **Hors-ligne**: Badge "Vérifié hors-ligne" sur fond orange

**Carte de résultat pour un pratiquant**:
- Photo du pratiquant (si disponible)
- Nom complet en gras
- Club/Fédération
- Numéro de licence
- Badge de validation fédération (vert si validé, rouge si non validé)
- Discipline principale

**Informations du scan**:
- Type de scan effectué
- Date et heure du scan
- Lieu (si disponible)
- ID unique du scan (petit texte)

**Boutons d'action contextuels**:
- **Présence**: "Enregistrer présence", "Voir détails"
- **Compétition**: "Valider passage", "Voir catégorie"
- **Profil**: "Voir profil complet", "Contacter"

**États spéciaux**:
- Mode hors-ligne: notification claire que le scan sera synchronisé plus tard
- Scan invalide: message d'erreur explicite et option pour réessayer
- Scan déjà effectué: notification et option pour voir le scan précédent

**Animations**:
- Entrée avec animation de scale-up depuis le centre
- Indicateurs de validation animés
- Feedback visuel sur les boutons d'action

---

### SCAN-04: Historique des Scans

**Objectif**: Afficher l'historique des QR codes scannés

**Structure**:
- Barre de navigation standard avec titre "Historique des scans"
- Filtres en haut (tous, en attente de sync, par type)
- Liste des scans avec indicateurs de statut
- Pull-to-refresh
- FAB (Floating Action Button) pour nouveau scan

**Éléments de la liste**:
- Chaque scan représenté par une carte contenant:
  - Petite photo ou icône du type de scan
  - Nom de la personne/élément scanné
  - Date et heure du scan
  - Type de scan (icône + texte)
  - Indicateur de statut (synchronisé, en attente, erreur)
  - Chevron pour voir les détails

**Regroupement**:
- Regroupement par date (Aujourd'hui, Hier, Cette semaine, Ce mois)
- Séparateurs visuels entre les groupes
- Compteur pour chaque groupe

**États des scans**:
- **Synchronisé**: Icône de coche verte
- **En attente**: Icône d'horloge orange
- **Erreur**: Icône d'erreur rouge avec option de réessayer

**Fonctionnalités**:
- Recherche par nom ou identifiant
- Filtrage par type de scan
- Tri par date (plus récent/plus ancien)
- Suppression par swipe ou sélection multiple
- Synchronisation manuelle des scans en attente

**Actions contextuelles**:
- Tap sur un scan pour voir les détails complets
- Tap long pour sélection multiple
- Swipe pour actions rapides (supprimer, marquer, etc.)

---

### SCAN-05: Scans Hors-ligne

**Objectif**: Gérer les scans effectués en mode hors-ligne et leur synchronisation

**Structure**:
- Onglet dédié dans l'historique ou écran accessible depuis le menu
- Bannière d'information sur le statut de la synchronisation
- Liste des scans en attente de synchronisation
- Bouton de synchronisation manuelle
- Statistiques de synchronisation

**Éléments de la liste**:
- Similaire à l'historique mais focalisé sur les scans non synchronisés
- Chaque élément comprend:
  - Informations principales du scan
  - Horodatage du scan
  - Statut (en attente, tentative échouée, etc.)
  - Bouton de réessai individuel

**Bannière de statut**:
- **Hors-ligne**: "Mode hors-ligne actif - x scans en attente"
- **Synchronisation en cours**: Indicateur de progression
- **Erreur de synchronisation**: Message d'erreur avec option de réessai
- **Synchronisé**: Confirmation temporaire "Tous les scans sont synchronisés"

**Fonctionnalités**:
- Synchronisation de tous les scans en un clic
- Suppression sélective des scans en attente
- Détails sur les erreurs de synchronisation
- Paramètres de synchronisation automatique

**États spéciaux**:
- Première connexion après période hors-ligne
- Conflits de synchronisation (doublons)
- Échecs répétés de synchronisation

---

### SCAN-06: Mon QR Code

**Objectif**: Afficher le QR code personnel du pratiquant pour être scanné par d'autres

**Structure**:
- Barre de navigation avec titre "Mon QR Code"
- Informations d'identification simplifiées
- QR code large et bien visible au centre
- Options de partage et renouvellement
- Informations sur la validité

**Informations d'identification**:
- Nom et prénom
- Photo de profil (petite)
- Club/Fédération
- Badge de validation

**QR Code**:
- Taille importante (adaptée à l'écran mais minimum 250dp)
- Fond blanc avec marge claire
- Possibilité de zoom
- Animation subtile pour attirer l'attention

**Options**:
- Onglets pour différents types de QR code:
  - Standard (identification)
  - Hors-ligne (profil complet)
  - Compétition (spécifique à un événement)
- Bouton de partage (image ou lien)
- Bouton de renouvellement (avec confirmation)

**Informations de validité**:
- Date de génération
- Date d'expiration
- Informations sur le contenu (selon le type)

**États spéciaux**:
- QR code expiré ou proche de l'expiration
- Mode hors-ligne (génération spéciale)
- Problèmes de validation (licence expirée, etc.)

## Composants UI Spécifiques

### 1. CameraView
- Vue plein écran avec support de la caméra
- Gestion des permissions
- Support du flash et de la mise au point
- Traitement des QR codes en temps réel

### 2. ScanFrame
- Cadre de guidage pour le scan
- Animation de balayage
- Feedback visuel lors de la détection

### 3. ScanTypePicker
- Sélecteur horizontal des types de scan
- Support des icônes et labels
- États actifs/inactifs/désactivés

### 4. ResultCard
- Carte de résultat avec mise en page adaptative
- Support de différents types de contenu
- États de succès/échec

### 5. SyncStatusBanner
- Bannière informative sur le statut de synchronisation
- États multiples avec indicateurs visuels
- Actions contextuelles

### 6. QRCodeDisplay
- Affichage optimisé du QR code personnel
- Contrôles de partage et options
- Support des différents types de codes

## Flux d'Utilisation

### 1. Scan Standard (Mode Connecté)
1. Utilisateur ouvre le scanner
2. Sélectionne le type de scan
3. Scanne un QR code
4. Visualise le résultat
5. Effectue l'action appropriée ou retourne au scan

### 2. Scan Hors-ligne
1. Utilisateur en mode hors-ligne ouvre le scanner
2. Est informé du mode hors-ligne
3. Scanne un QR code compatible hors-ligne
4. Visualise le résultat avec indication "Hors-ligne"
5. Scan stocké localement pour synchronisation ultérieure

### 3. Synchronisation
1. Utilisateur retrouve la connexion
2. Notification suggérant la synchronisation
3. Accès à l'écran des scans hors-ligne
4. Synchronisation automatique ou manuelle
5. Confirmation des résultats

### 4. Partage de QR Code Personnel
1. Utilisateur accède à "Mon QR Code"
2. Sélectionne le type approprié
3. Présente à scanner ou utilise options de partage
4. Peut renouveler le code si nécessaire

## Adaptations Techniques

### Performance
- Optimisation de la caméra pour réduire la consommation de batterie
- Traitement efficace des images pour la détection des QR codes
- Stockage optimisé des scans hors-ligne

### Accessibilité
- Instructions vocales pour le scan
- Retour haptique lors de la détection
- Options de luminosité et contraste ajustables

### Sécurité
- Validation des QR codes scannés
- Vérification des signatures pour les codes hors-ligne
- Protection contre les codes malveillants

## Notes pour l'Implémentation

1. **Permissions**:
   - Demander l'accès à la caméra de manière contextuelle
   - Gérer les refus et les demandes ultérieures
   - Supporter les restrictions iOS et Android

2. **Stockage Local**:
   - Chiffrer les données sensibles
   - Limiter la taille de l'historique
   - Gérer la persistance entre sessions

3. **Synchronisation**:
   - Stratégie de retry avec backoff exponentiel
   - Gestion des conflits de données
   - Indicateurs de progression clairs

4. **Optimisations**:
   - Scanner des QR codes de différentes tailles et densités
   - Ajuster dynamiquement la résolution de la caméra
   - Supporter les appareils avec performances variées