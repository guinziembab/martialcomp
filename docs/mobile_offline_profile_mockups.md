# Maquettes du Profil Hors-ligne - MartialComp Mobile

## Vue d'ensemble

Ces spécifications détaillent les maquettes pour la fonctionnalité de profil hors-ligne de l'application mobile MartialComp, permettant aux utilisateurs de générer, afficher et partager un profil complet accessible sans connexion internet.

## Écrans du Profil Hors-ligne

### PROF-03: Profil Hors-ligne Principal

**Objectif**: Permettre à l'utilisateur de générer et gérer son profil hors-ligne

**Structure**:
- Barre de navigation avec titre "Profil Hors-ligne"
- Section d'état du profil hors-ligne
- QR code du profil (si généré)
- Informations sur la validité
- Boutons d'action
- Informations explicatives

**Section d'état**:
- **Non généré**: Badge gris "Non généré"
- **Généré & Valide**: Badge vert "Actif" avec date d'expiration
- **Expiré**: Badge rouge "Expiré" avec invitation à régénérer
- **En cours de génération**: Indicateur de chargement

**Informations de profil résumées**:
- Nom et prénom
- Club/Fédération
- Numéro de licence
- Discipline principale et grade
- Badge de validation fédération

**QR Code**:
- Taille importante (adaptée à l'écran mais minimum 250dp)
- Fond blanc avec marge claire
- Indicateur de densité de données (Haute/Moyenne/Basse)
- Bouton d'agrandissement pour plein écran

**Boutons d'action**:
- "Générer le profil hors-ligne" (si non généré)
- "Régénérer le profil" (si expiré ou proche de l'expiration)
- "Partager" (export image ou texte du token)
- "Afficher les détails" (voir le contenu exact du profil)

**Informations explicatives**:
- Explication sur l'utilité du profil hors-ligne
- Durée de validité
- Informations incluses dans le profil
- Conseils de sécurité

**États spéciaux**:
- Première génération (avec explications supplémentaires)
- Régénération récente
- Profil proche de l'expiration (avertissement)
- Problèmes de validation (licence expirée, etc.)

---

### PROF-03.1: Génération du Profil Hors-ligne

**Objectif**: Guider l'utilisateur dans le processus de génération du profil hors-ligne

**Structure**:
- Titre "Génération du profil hors-ligne"
- Étapes du processus (visuel)
- Formulaire de sélection des données à inclure
- Options de sécurité
- Bouton de génération
- Indications sur la taille et la validité

**Processus de génération visuel**:
- Étape 1: Sélection des données (en cours)
- Étape 2: Génération (à venir)
- Étape 3: Confirmation (à venir)

**Options de données à inclure**:
- Informations de base (toujours incluses, non désactivables)
- Informations sportives (grades, disciplines)
- Informations de contact (email, téléphone)
- Informations médicales (certificat, allergies)
- Licences et validations

**Options de sécurité**:
- Durée de validité (30, 60, 90 jours)
- Protection par mot de passe (optionnel)
- Mode de partage (public/privé)

**Bouton de génération**:
- Libellé clair "Générer mon profil hors-ligne"
- État désactivé si options obligatoires non sélectionnées
- Animation lors du clic

**Indicateurs**:
- Taille estimée du QR code
- Densité de données et lisibilité
- Date d'expiration prévue

**Animation de transition**:
- Transition fluide vers l'écran de génération en cours
- Barre de progression ou animation de chargement
- Feedback visuel et sonore lors de la complétion

---

### PROF-03.2: Affichage du Profil Hors-ligne

**Objectif**: Présenter le profil hors-ligne généré à l'utilisateur

**Structure**:
- En-tête avec nom du pratiquant et photo
- QR code central avec options
- Informations de validité
- Onglets pour catégories d'informations
- Boutons d'action en bas

**En-tête de profil**:
- Photo de profil (si disponible)
- Nom complet en grand
- Badge de statut (Actif/Expiré)
- Club et fédération

**QR Code**:
- Taille importante avec bordure claire
- Version haute résolution
- Options d'agrandissement et de partage directement sur le code

**Informations de validité**:
- Date de génération
- Date d'expiration
- Durée restante en jours
- ID unique du profil (discret)

**Onglets de catégories**:
- **Informations personnelles**: Nom, date de naissance, nationalité, etc.
- **Informations sportives**: Disciplines, grades, compétitions récentes
- **Validations**: Licences, certificats médicaux, affiliations
- **Données hors-ligne**: Détails techniques sur le contenu du token

**Boutons d'action**:
- "Partager le profil" (plusieurs options)
- "Imprimer" (génération PDF)
- "Régénérer" (avec confirmation)

**Indicateur de sécurité**:
- Sceau visuel de validation (logo MartialComp avec date)
- Informations sur les mécanismes de sécurité
- Conseils pour la vérification par des tiers

---

### PROF-03.3: Partage du Profil Hors-ligne

**Objectif**: Offrir différentes options pour partager le profil hors-ligne

**Structure**:
- Titre "Partager mon profil"
- Aperçu du contenu à partager
- Options de partage primaires
- Options avancées
- Paramètres de confidentialité

**Aperçu du contenu**:
- Miniature du QR code
- Résumé des informations incluses
- Taille approximative

**Options de partage primaires**:
- **Image du QR**: Partage de l'image seule
- **Carte de profil**: Image combinant QR et informations de base
- **Token texte**: Code alphanumérique pour saisie manuelle
- **Lien**: URL avec token intégré (si en ligne)

**Options avancées**:
- Exportation au format PDF
- Ajout aux contacts (vCard)
- Partage temporaire (durée limitée)
- Protection par mot de passe

**Méthodes de partage**:
- Applications de messagerie
- Email
- Bluetooth
- AirDrop (iOS)
- Nearby Share (Android)
- Réseaux sociaux
- Copier dans le presse-papier

**Paramètres de confidentialité**:
- Avertissements sur les données sensibles
- Options pour masquer certaines informations
- Journal de partage (qui, quand, comment)

---

### PROF-03.4: Vérification du Profil Hors-ligne

**Objectif**: Permettre la vérification d'un profil hors-ligne reçu

**Structure**:
- Barre de navigation avec titre "Vérifier un profil"
- Options d'entrée du profil (scanner/saisir)
- Résultat de la vérification
- Détails du profil vérifié
- Actions disponibles

**Options d'entrée**:
- Scanner un QR code (bouton caméra)
- Saisir un token manuellement (champ texte)
- Importer depuis un fichier

**Résultat de vérification**:
- **Valide**: Badge vert avec coche, informations de validité
- **Expiré**: Badge orange, date d'expiration dépassée
- **Invalide**: Badge rouge, raison de l'invalidité
- **Non reconnu**: Message d'erreur explicatif

**Affichage du profil vérifié**:
- Similaire à l'affichage du profil personnel mais en mode lecture seule
- Indication claire de l'origine et du statut de vérification
- Mise en évidence des informations critiques (validité, affiliation)

**Actions disponibles**:
- "Enregistrer le contact"
- "Vérifier en ligne" (si connexion disponible)
- "Partager la vérification"
- "Signaler un problème"

**Informations de sécurité**:
- Explication du processus de vérification
- Comment identifier un profil potentiellement falsifié
- Limitations de la vérification hors-ligne

---

### PROF-03.5: Profil Hors-ligne Plein Écran

**Objectif**: Afficher le QR code du profil en plein écran pour faciliter le scan

**Structure**:
- QR code occupant la majorité de l'écran
- Informations minimales sur l'identité
- Bouton de retour discret
- Contrôle de luminosité

**QR Code**:
- Taille maximale possible tout en restant lisible
- Fond blanc pur pour contraste optimal
- Bordure fine pour délimitation
- Auto-ajustement selon la taille de l'écran

**Informations minimales**:
- Nom du pratiquant (en bas)
- Badge de validité (petit, en coin)
- Date d'expiration (discrète)

**Contrôles**:
- Augmenter/diminuer la luminosité de l'écran
- Rotation automatique de l'écran supportée
- Empêcher la mise en veille automatique

**Comportement**:
- Tap n'importe où pour afficher/masquer les contrôles
- Pinch pour zoom si nécessaire
- Shake pour revenir à l'écran précédent

## Composants UI Spécifiques

### 1. ProfileQRCode
- Composant d'affichage du QR code avec bordure
- Support des différentes densités
- Optimisation pour l'affichage et le scan

### 2. ValidityBadge
- Badge indiquant le statut de validité du profil
- États multiples (valide, expiré, en attente)
- Design distinctif et clair

### 3. DataSelectionList
- Liste de sélection des données à inclure
- Cases à cocher avec descriptions
- Regroupement par catégories

### 4. ExpiryCountdown
- Affichage du temps restant avant expiration
- Formatage adaptatif (jours/heures)
- Changement de couleur selon l'urgence

### 5. SecuritySeal
- Indicateur visuel d'authenticité
- Animation subtile pour distinguer des images statiques
- Intégration des informations de validation

### 6. ShareOptionsGrid
- Grille d'options de partage
- Icônes distinctives et labels clairs
- Regroupement par type de partage

## Flux d'Utilisation

### 1. Première Génération du Profil
1. Utilisateur accède à la section profil hors-ligne
2. Consulte les informations explicatives
3. Initie le processus de génération
4. Sélectionne les données à inclure et options
5. Attend la génération
6. Reçoit confirmation et aperçu du profil généré

### 2. Utilisation Quotidienne
1. Utilisateur accède à son profil hors-ligne
2. Vérifie la validité
3. Présente le QR code à scanner ou utilise les options de partage
4. Peut passer en mode plein écran pour faciliter le scan

### 3. Régénération
1. Utilisateur est notifié de l'expiration proche
2. Accède à son profil hors-ligne
3. Utilise l'option de régénération
4. Peut modifier les options si souhaité
5. Confirme la régénération
6. Nouveau profil généré remplace l'ancien

### 4. Vérification d'un Profil Reçu
1. Utilisateur reçoit un profil à vérifier
2. Accède à la fonction de vérification
3. Scanne le QR code ou entre le token
4. Consulte le résultat de la vérification
5. Peut effectuer des actions supplémentaires

## Adaptations Techniques

### Performance
- Optimisation de la génération du QR code
- Gestion efficace de la mémoire pour les profils volumineux
- Compression des données sans perte d'informations critiques

### Accessibilité
- Support de VoiceOver/TalkBack pour la lecture des informations
- Options de contraste élevé pour le QR code
- Alternatives au QR code pour les personnes malvoyantes

### Sécurité
- Chiffrement des données sensibles
- Mécanismes anti-falsification
- Validation de l'intégrité des données

## Notes pour l'Implémentation

1. **Génération de QR Code**:
   - Utiliser des bibliothèques optimisées pour la densité
   - Tester sur différents scanners
   - Gérer les limitations de taille

2. **Stockage Local**:
   - Chiffrer les profils stockés
   - Gestion efficace de l'espace
   - Rotation des anciennes versions

3. **Validation**:
   - Algorithmes de validation robustes
   - Gestion des erreurs explicite
   - Vérification en plusieurs étapes

4. **Optimisations**:
   - Génération asynchrone pour les gros profils
   - Mise en cache des QR codes générés
   - Préchargement des données fréquemment utilisées