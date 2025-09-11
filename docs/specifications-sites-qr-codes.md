# Spécification : Système de sites en sous-domaine et QR codes pour les organisations

## Contexte et objectifs

Dans le cadre de la plateforme MartialComp, nous souhaitons permettre à chaque organisation enregistrée (fédérations, clubs, coachs sportifs) de disposer automatiquement d'un site web dédié en sous-domaine. Cette fonctionnalité vise à :

1. Offrir une présence en ligne immédiate à toutes les organisations d'arts martiaux
2. Faciliter la communication de leurs activités vers leurs membres et le public
3. Simplifier le processus d'inscription aux événements, compétitions et cours
4. Intégrer un système de QR codes pour fluidifier l'expérience des pratiquants
5. Renforcer l'écosystème MartialComp en créant un réseau de sites interconnectés

## Description détaillée du besoin

### 1. Création automatique de sous-domaines

Dès l'enregistrement d'une organisation dans le système MartialComp, un site web en sous-domaine doit être automatiquement provisionné selon le format :
- `[identifiant-organisation].martialcomp.com`

Où l'identifiant de l'organisation sera généré à partir de son nom, avec les caractères spéciaux et espaces remplacés par des tirets, en minuscules.

### 2. Types d'organisations supportés

Le système doit prendre en compte les types d'organisations suivants, chacun avec ses spécificités :

1. **Fédérations** - Organisations nationales ou internationales gérant une ou plusieurs disciplines
2. **Clubs** - Structures locales proposant la pratique d'une ou plusieurs disciplines
3. **Coachs sportifs** - Professionnels indépendants proposant des cours particuliers ou en petit groupe

### 3. Templates de site disponibles

Le système doit proposer 4 templates de site distincts, adaptés aux différents types d'organisations :

1. **Template Fédération** - Axé sur la présentation institutionnelle, les actualités officielles et le calendrier des compétitions nationales/internationales
   
2. **Template Club** - Centré sur la présentation des cours, des instructeurs et des activités locales
   
3. **Template Coach** - Focalisé sur la présentation du coach, ses qualifications, ses services et ses disponibilités
   
4. **Template Événementiel** - Dédié principalement à la promotion d'une compétition ou événement majeur

### 4. Personnalisation

Chaque organisation pourra personnaliser son site à travers :

- **Identité visuelle** :
  - Logo de l'organisation (obligatoire)
  - Couleurs principales (2-3 couleurs)
  - Bannière d'en-tête (optionnelle)
  - Images de fond/ambiance (optionnelles)

- **Contenu structuré** :
  - Présentation de l'organisation
  - Coordonnées et informations de contact
  - Disciplines pratiquées
  - Horaires (pour les clubs et coachs)
  - Équipe dirigeante/instructeurs (photos, noms, fonctions)

- **Modules activables** :
  - Actualités
  - Calendrier d'événements
  - Galerie photos
  - Témoignages/palmarès
  - Inscription en ligne
  - QR codes d'accès rapide

### 5. Système de QR codes

#### 5.1 QR codes pour les organisations

Chaque organisation dispose automatiquement de QR codes générés par le système :

- **QR code principal** : Redirige vers la page d'accueil du site de l'organisation
- **QR codes d'inscription** : Spécifiques à chaque activité, cours ou événement
- **QR codes temporaires** : Pour des promotions ou événements limités dans le temps

Ces QR codes peuvent être :
- Téléchargés depuis l'interface d'administration
- Imprimés directement depuis le site
- Intégrés aux supports de communication (affiches, flyers, cartes de visite)

#### 5.2 QR codes pour les adhérents/pratiquants

Chaque pratiquant enregistré dans le système reçoit un QR code personnel qui :

- Contient son identifiant unique dans le système
- Permet une identification rapide lors des événements et compétitions
- Facilite le pointage aux cours et entraînements
- Donne accès à son espace personnel sur le site de son organisation

Fonctionnalités associées :
- **Check-in rapide** : Scan du QR code à l'entrée des cours ou événements
- **Inscription accélérée** aux compétitions
- **Vérification des licences et assurances** en temps réel
- **Suivi de présence** automatisé pour les clubs et coachs

### 6. Fonctionnalités d'inscription

Le site doit permettre :

1. **Inscription aux activités** :
   - Via formulaire en ligne intégré au site
   - Via scan du QR code de l'activité
   - Avec possibilité d'identification rapide pour les pratiquants existants via leur QR code personnel

2. **Gestion des adhérents** :
   - Tableau de bord pour l'administration des inscriptions
   - Suivi des paiements (si applicable)
   - Gestion des renouvellements
   - Génération et envoi automatiques des QR codes personnels

3. **Inscription aux compétitions** :
   - Lien direct avec le système central MartialComp
   - Affichage des compétitions pertinentes pour l'organisation
   - Procédure d'inscription simplifiée pour les membres
   - Vérification automatique des critères d'éligibilité

4. **Réservation de cours** (spécifique aux coachs) :
   - Affichage des disponibilités
   - Système de réservation en ligne
   - Rappels automatiques par email/SMS
   - Gestion des annulations et reports

### 7. Flux d'utilisation des QR codes

#### 7.1 Flux d'inscription via QR code organisation

1. Un nouveau pratiquant découvre l'organisation (club, coach)
2. Il scanne le QR code affiché sur un support de communication
3. Il est dirigé vers la page d'inscription du site
4. Il complète le formulaire avec ses informations
5. Il reçoit une confirmation par email avec son QR code personnel

#### 7.2 Flux d'utilisation du QR code pratiquant

1. Le pratiquant arrive à un cours/entraînement/compétition
2. L'administrateur ou coach scanne son QR code personnel
3. Le système identifie instantanément le pratiquant
4. Le système vérifie automatiquement son statut (licence, cotisation, inscription)
5. Le pratiquant est enregistré comme présent
6. Le système met à jour son historique de participation

#### 7.3 Flux d'inscription à une compétition

1. L'organisation publie une compétition sur son site
2. Le pratiquant scanne le QR code de la compétition
3. Il s'identifie via son QR code personnel
4. Le système pré-remplit le formulaire avec ses informations
5. Le pratiquant confirme sa participation
6. Il reçoit un QR code spécifique pour cette compétition

## Spécifications techniques

### 1. Architecture

1. **Système multi-tenant** :
   - Chaque organisation disposera d'un tenant spécifique dans l'application
   - Les données seront isolées tout en partageant l'infrastructure commune

2. **Gestion des sous-domaines** :
   - Configuration DNS automatisée
   - Certificats SSL générés et renouvelés automatiquement

3. **Stockage des données** :
   - Stockage isolé par organisation pour le contenu spécifique
   - Référence au système central pour les données partagées (compétitions, disciplines, pratiquants)

### 2. Système de QR codes

1. **Génération des QR codes** :
   - Utilisation de la bibliothèque qrcode pour Python
   - Format SVG pour une qualité optimale à l'impression
   - Intégration du logo de l'organisation au centre (optionnel)

2. **Structure des données QR** :
   - URL avec paramètres encodés pour les QR codes organisation
   - Identifiant unique chiffré pour les QR codes pratiquants
   - Paramètres additionnels pour les QR codes événements/cours

3. **Sécurité** :
   - Rotation périodique des QR codes pratiquants
   - Vérification de validité temporelle
   - Protection contre la duplication (QR codes à usage unique pour certains événements)

### 3. Scanner de QR codes

1. **Interface web responsive** :
   - Accès à la caméra via WebRTC
   - Traitement en temps réel

2. **Application mobile complémentaire** (optionnelle) :
   - Scanner natif pour iOS et Android
   - Fonctionnement hors-ligne avec synchronisation ultérieure

### 4. Contraintes de sécurité

1. **Isolation des données** :
   - Chaque organisation ne doit avoir accès qu'à ses propres données
   - Respect strict des règles de filtrage par discipline et affiliation

2. **Protection des données personnelles** :
   - Conformité RGPD
   - Formulaires de consentement intégrés
   - Politique de confidentialité personnalisable

### 5. Interface d'administration

1. **Panneau d'administration dédié** :
   - Interface spécifique pour la gestion du site par les administrateurs de l'organisation
   - Outils de génération et gestion des QR codes
   - Suivi des statistiques d'utilisation des QR codes

2. **Tableau de bord de présence** :
   - Visualisation en temps réel des check-ins
   - Historique de participation
   - Exportation des données de présence

## Considérations spécifiques par type d'organisation

### 1. Pour les fédérations

- QR codes d'affiliation pour les clubs
- QR codes d'accréditation pour les événements officiels
- Système de vérification des licences via QR code
- Statistiques de participation agrégées par disciplines et régions

### 2. Pour les clubs

- QR codes d'accès aux cours par niveau/discipline
- Système de cartes de membre virtuelles
- Suivi de progression des pratiquants
- Gestion des présences aux entraînements
- Check-in rapide aux séances d'entraînement

### 3. Pour les coachs sportifs

- QR codes de réservation de séances
- Système de planification avec QR codes temporaires
- Suivi personnalisé des clients
- Gestion des forfaits et séances restantes
- Attestations de participation générées automatiquement

## Plan de mise en œuvre

### Phase 1 : Conception et prototypage

1. **Conception des templates** :
   - Design des 4 templates principaux
   - Définition des options de personnalisation
   - Création des maquettes interactives

2. **Architecture technique** :
   - Spécification détaillée de l'architecture multi-tenant
   - Conception du système de sous-domaines
   - Prototypage du système de QR codes

### Phase 2 : Développement

1. **Système de provisionnement** :
   - Développement du mécanisme automatique de création de sites
   - Mise en place de la génération de sous-domaines
   - Développement du générateur de QR codes

2. **Interface d'administration** :
   - Développement du panneau d'administration des sites
   - Création des outils de personnalisation
   - Développement du scanner de QR codes

3. **Fonctionnalités d'inscription** :
   - Développement des formulaires d'inscription
   - Système de génération des QR codes personnels
   - Intégration avec le système central MartialComp

### Phase 3 : Test et déploiement

1. **Tests utilisateurs** :
   - Tests avec un panel d'organisations pilotes
   - Tests du système de QR codes dans des conditions réelles
   - Recueil des retours et ajustements

2. **Déploiement progressif** :
   - Déploiement pour les nouvelles organisations
   - Migration progressive des organisations existantes
   - Formation des administrateurs à l'utilisation des QR codes

## Conclusion

Cette spécification établit les bases d'un système complet de sites en sous-domaine pour les organisations enregistrées sur MartialComp, intégrant un système innovant de QR codes pour les organisations et les pratiquants.

Ce système permettra de :
- Offrir une présence en ligne professionnelle à chaque organisation
- Simplifier drastiquement le processus d'inscription et de participation
- Améliorer l'expérience utilisateur des pratiquants
- Faciliter la gestion administrative des organisations
- Renforcer l'écosystème MartialComp en créant une expérience fluide et interconnectée

L'approche progressive et modulaire proposée permettra un déploiement contrôlé et une adoption optimale par les utilisateurs, tout en maintenant la cohérence et l'intégrité du système central.
