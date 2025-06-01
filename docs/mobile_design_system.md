# Design System - MartialComp Mobile

## Introduction

Ce document définit le système de design pour l'application mobile MartialComp. Il sert de référence pour maintenir la cohérence visuelle et fonctionnelle à travers toute l'application, et de guide pour les designers et développeurs.

## 1. Fondations

### 1.1. Palette de Couleurs

#### Couleurs Primaires
| Nom | Valeur | Utilisation |
|-----|--------|------------|
| **Primary** | `#3F51B5` (Indigo) | Boutons principaux, en-têtes, éléments d'action |
| **Primary Dark** | `#303F9F` | États pressés, variations sombres |
| **Primary Light** | `#C5CAE9` | Arrière-plans légers, sélections |

#### Couleurs Secondaires
| Nom | Valeur | Utilisation |
|-----|--------|------------|
| **Secondary** | `#FF4081` (Rose) | Call-to-actions, accents, notifications |
| **Secondary Dark** | `#C2185B` | États pressés, variations sombres |
| **Secondary Light** | `#F8BBD0` | Arrière-plans légers, indicateurs |

#### Couleurs Fonctionnelles
| Nom | Valeur | Utilisation |
|-----|--------|------------|
| **Success** | `#4CAF50` (Vert) | Confirmations, validations, actions réussies |
| **Warning** | `#FFC107` (Ambre) | Avertissements, attention requise |
| **Error** | `#F44336` (Rouge) | Erreurs, actions destructives |
| **Info** | `#2196F3` (Bleu) | Informations, aide, conseils |

#### Gris Neutres
| Nom | Valeur | Utilisation |
|-----|--------|------------|
| **Gray100** | `#F5F5F5` | Arrière-plans, séparateurs légers |
| **Gray200** | `#EEEEEE` | Arrière-plans alternés, cartes |
| **Gray300** | `#E0E0E0` | Séparateurs, bordures |
| **Gray400** | `#BDBDBD` | Éléments désactivés |
| **Gray500** | `#9E9E9E` | Texte secondaire, icônes inactives |
| **Gray600** | `#757575` | Texte secondaire fort |
| **Gray700** | `#616161` | Texte par défaut |
| **Gray800** | `#424242` | Texte d'importance |
| **Gray900** | `#212121` | Titres, texte important |

#### Mode Sombre
| Nom | Valeur | Utilisation |
|-----|--------|------------|
| **Dark Background** | `#121212` | Arrière-plan principal |
| **Dark Surface** | `#1E1E1E` | Cartes, surfaces élevées |
| **Dark Text Primary** | `#FFFFFF` | Texte principal (100% opacité) |
| **Dark Text Secondary** | `rgba(255,255,255,0.7)` | Texte secondaire (70% opacité) |
| **Dark Text Disabled** | `rgba(255,255,255,0.5)` | Texte désactivé (50% opacité) |

### 1.2. Typographie

#### Familles de polices
- **Principal**: Roboto (Android) / San Francisco (iOS)
- **Alternative**: System default sans-serif

#### Échelle Typographique
| Nom | Taille | Poids | Utilisation |
|-----|--------|-------|------------|
| **Headline 1** | 28sp | Bold | Titres principaux, pages de bienvenue |
| **Headline 2** | 24sp | Bold | En-têtes de section principale |
| **Headline 3** | 20sp | Medium | Titres de cartes, sous-sections |
| **Headline 4** | 18sp | Medium | Titres mineurs, groupes d'éléments |
| **Body 1** | 16sp | Regular | Texte principal, labels principaux |
| **Body 2** | 14sp | Regular | Texte secondaire, descriptions |
| **Caption** | 12sp | Regular | Informations auxiliaires, légendes |
| **Button** | 16sp | Medium | Texte des boutons |
| **Overline** | 10sp | Regular | En-têtes très petits, libellés techniques |

#### Alignement
- Alignement à gauche par défaut pour les langues LTR
- Alignement à droite pour les langues RTL
- Justification évitée pour meilleure lisibilité sur petits écrans

### 1.3. Iconographie

#### Système d'icônes
- Utilisation de Material Icons pour la cohérence
- Taille standard: 24dp x 24dp
- Zone de touch: minimum 48dp x 48dp

#### Tailles d'icônes
| Contexte | Taille | Utilisation |
|----------|--------|------------|
| **Petite** | 16dp | Indicateurs, badges, compléments de texte |
| **Standard** | 24dp | Majorité des icônes d'interface |
| **Moyenne** | 32dp | Mises en évidence, boutons d'action primaires |
| **Grande** | 48dp | Illustrations fonctionnelles, points d'attention |

#### Style
- Style filled (rempli) pour actions principales
- Style outlined (contour) pour actions secondaires
- Couleur correspondant à la fonction (primaire, alerte, etc.)
- Utiliser les icônes standard du système quand approprié

### 1.4. Espacement et Grille

#### Système d'espacement
Base sur un incrément de 8dp:
- **2dp**: Espacement minimal (séparations fines)
- **4dp**: Espacement compact (entre éléments liés)
- **8dp**: Espacement standard (entre éléments distincts)
- **16dp**: Espacement moyen (séparation de groupes)
- **24dp**: Espacement large (séparation de sections)
- **32dp** et plus: Espacements majeurs (séparations de blocs)

#### Marges
- Marge standard: 16dp
- Marge sur petits écrans: 8dp
- Marge sur grands écrans: 24dp

#### Grille
- Grille fluide de 4 colonnes sur smartphones
- Grille fluide de 8 colonnes sur tablettes
- Gouttière: 16dp (adaptative selon taille)

### 1.5. Élévation et Ombres

#### Niveaux d'élévation
| Niveau | Élévation | Utilisation |
|--------|-----------|------------|
| **0dp** | Pas d'ombre | Éléments au niveau de base |
| **1dp** | Ombre légère | Cartes, surfaces légèrement surélevées |
| **2dp** | Ombre basse | Barres d'application, cartes actives |
| **4dp** | Ombre moyenne | Barres de navigation, menus flottants |
| **8dp** | Ombre haute | Boutons flottants (FAB), modals |
| **16dp** | Ombre maximale | Dialogs, menus contextuels |

#### Propriétés d'ombre
- Augmentation de la taille et flou avec l'élévation
- Opacité adaptée au mode clair/sombre
- Ombres désactivables pour performances

## 2. Composants

### 2.1. Boutons et Actions

#### Types de boutons
| Type | Apparence | Utilisation |
|------|-----------|------------|
| **Bouton Principal** | Fond plein couleur primaire, texte blanc | Actions principales, validations |
| **Bouton Secondaire** | Contour couleur primaire, texte primaire | Actions alternatives, annulations |
| **Bouton Texte** | Texte couleur primaire sans fond | Actions tertiaires, liens |
| **Bouton Critique** | Fond rouge, texte blanc | Actions destructives, suppressions |
| **FAB (Floating Action Button)** | Rond, couleur secondaire, icône blanche | Action principale de l'écran |

#### États des boutons
- **Normal**: Apparence standard
- **Hover/Focus**: Léger changement d'opacité/luminosité
- **Pressed**: Assombrissement de la couleur
- **Disabled**: Opacité réduite (40%), non cliquable

#### Dimensions
- Hauteur standard: 48dp
- Largeur: adaptative au contenu ou pleine largeur
- Padding horizontal: 16dp
- Rayon de coin: 4dp (8dp pour boutons arrondis)

### 2.2. Champs de formulaire

#### Types de champs
| Type | Description | Utilisation |
|------|-------------|------------|
| **Champ Texte** | Zone de saisie avec label flottant | Entrées textuelles |
| **Zone de Texte** | Champ texte multi-lignes | Textes longs, commentaires |
| **Sélecteur** | Menu déroulant ou roue | Choix parmi liste d'options |
| **Case à cocher** | Toggle carré | Options multiples |
| **Bouton Radio** | Toggle rond | Option unique parmi plusieurs |
| **Interrupteur** | Toggle coulissant | Activation/désactivation |
| **Curseur** | Barre avec poignée | Sélection de valeur dans une plage |
| **Sélecteur Date/Heure** | Champ spécial avec picker | Sélection temporelle |

#### États des champs
- **Repos**: Bordure fine grise
- **Focus**: Bordure accentuée couleur primaire
- **Rempli**: Texte visible, label réduit
- **Erreur**: Bordure rouge, message d'erreur
- **Désactivé**: Opacité réduite, non modifiable
- **Lecture seule**: Visuel standard mais non modifiable

#### Validation
- Validation en temps réel quand approprié
- Messages d'erreur explicites sous le champ
- Indicateurs visuels clairs (icônes, couleurs)

### 2.3. Cartes et Conteneurs

#### Types de cartes
| Type | Description | Utilisation |
|------|-------------|------------|
| **Carte Standard** | Container rectangulaire avec ombre | Groupement d'informations |
| **Carte Actionnable** | Carte standard + action de tap | Éléments de liste interactifs |
| **Carte Compacte** | Version réduite, moins de padding | Listes denses |
| **Carte Média** | Carte avec image/média proéminent | Contenu visuel important |
| **Carte État** | Carte avec indicateur visuel d'état | Éléments avec statut |

#### Anatomie d'une carte
- Padding interne: 16dp
- Marge entre cartes: 8dp
- Rayon des coins: 8dp
- Élévation: 1dp (repos), 2dp (active)

#### Variations
- Cartes à bord coloré pour catégorisation
- Badges d'état en coin supérieur
- Options d'expansion/collapse

### 2.4. Navigation

#### Barre inférieure
- 3-5 destinations principales
- Icônes + labels
- Indicateur de sélection
- Hauteur: 56dp

#### Barre supérieure
- Titre de l'écran actuel
- Bouton retour quand applicable
- Actions contextuelles
- Hauteur: 56dp (simple), 112dp (étendue)

#### Tiroir de navigation
- Pour applications à nombreuses sections
- Liste verticale d'options
- Groupement par catégories
- En-tête avec logo/profil

#### Onglets
- Navigation horizontale entre vues liées
- 2-5 onglets maximum visibles
- Indicateur de sélection animé
- Scrollable si plus de 5 onglets

### 2.5. Listes et Tableaux

#### Types de listes
| Type | Description | Utilisation |
|------|-------------|------------|
| **Liste Simple** | Lignes texte avec séparateurs légers | Menus, options simples |
| **Liste avec Avatar** | Avec image/icône à gauche | Contacts, utilisateurs |
| **Liste à Deux Lignes** | Titre + description | Informations détaillées |
| **Liste avec Actions** | Contrôles à droite | Options interactives |
| **Liste Expansible** | Éléments pouvant se déployer | Sections collapsibles |

#### Dimensions
- Hauteur ligne simple: 48dp
- Hauteur ligne double: 72dp
- Hauteur ligne triple: 88dp
- Padding horizontal: 16dp
- Séparateur: 1dp, couleur Gray300

#### Interactions
- Ripple effect sur tap (Android)
- Highlight sur tap (iOS)
- Swipe actions quand approprié
- Pull-to-refresh pour listes dynamiques

### 2.6. Alertes et Feedback

#### Types de feedback
| Type | Description | Utilisation |
|------|-------------|------------|
| **Toast** | Message bref en bas d'écran | Confirmations brèves |
| **Snackbar** | Message avec action possible | Notifications actionnables |
| **Bannière** | Notification en haut d'écran | Alertes importantes |
| **Dialog** | Fenêtre modale centrée | Décisions, confirmations |
| **Badge** | Petit indicateur sur icône | Compteurs, notifications |

#### Alertes contextuelles
- Couleur selon gravité (error, warning, info, success)
- Icônes correspondantes
- Temps d'affichage adapté à la longueur du message
- Options de fermeture explicites pour alertes persistantes

### 2.7. Loaders et États vides

#### Indicateurs de chargement
| Type | Description | Utilisation |
|------|-------------|------------|
| **Spinner Circulaire** | Animation de rotation | Chargement indéterminé |
| **Barre de Progression** | Barre horizontale | Chargement avec pourcentage |
| **Skeleton Screen** | Placeholder animé | Préchargement de contenu |
| **Pull Indicator** | Animation lors du pull-to-refresh | Rafraîchissement manuel |

#### États vides
- Illustration représentative
- Message explicatif clair
- Action suggérée si applicable
- Style cohérent avec l'application

## 3. Patterns d'interaction

### 3.1. Gestes et Contrôles Tactiles

#### Gestes standard
| Geste | Action |
|-------|--------|
| **Tap** | Sélection, activation |
| **Double tap** | Zoom, action secondaire |
| **Long press** | Menu contextuel, sélection multiple |
| **Swipe horizontal** | Navigation, actions contextuelles |
| **Swipe vertical** | Défilement |
| **Pinch** | Zoom in/out |
| **Pull down** | Rafraîchir |

#### Zones tactiles
- Taille minimale: 48dp x 48dp
- Espacement minimal: 8dp
- Feedback visuel sur toutes les zones interactives

### 3.2. Transitions et Animations

#### Types d'animations
| Type | Durée | Courbe | Utilisation |
|------|-------|--------|------------|
| **Standard** | 300ms | Ease-out | Transitions d'écran |
| **Rapide** | 150ms | Ease | Changements d'état, feedback |
| **Entrance** | 225ms | Ease-out | Apparition d'éléments |
| **Exit** | 195ms | Ease-in | Disparition d'éléments |
| **Emphase** | 450ms | Ease | Attirer l'attention |

#### Principes
- Animations subtiles, non intrusives
- Support de la réduction des animations (accessibilité)
- Cohérence dans les directions et motifs
- Animations significatives (pas uniquement décoratives)

### 3.3. Accessibilité

#### Contraste et Lisibilité
- Ratio de contraste minimum: 4.5:1 (AA)
- Ratio préféré: 7:1 (AAA)
- Pas de texte sur images sans contraste suffisant
- Taille de texte minimum: 14sp

#### Support de VoiceOver / TalkBack
- Tous les éléments interactifs avec labels accessibles
- Ordre de focus logique
- Descriptions alternatives pour images
- Feedback audio/haptique pour actions importantes

#### Personnalisation
- Support du texte agrandi
- Mode sombre complet
- Options de contraste élevé
- Pas d'information transmise uniquement par la couleur

### 3.4. Modes et Thèmes

#### Mode Clair / Sombre
- Transition fluide entre modes
- Respect des préférences système
- Cohérence dans les contrastes
- Préservation de la hiérarchie visuelle

#### Variations Thématiques
- Variations de couleur primaire/secondaire
- Adaptation aux couleurs de la fédération/club
- Cohérence des éléments fonctionnels
- Paramètres utilisateur pour personnalisation

## 4. Applications Spécifiques

### 4.1. Mode Hors-ligne

#### Indicateurs de Statut
- Badge persistant en header (vert/rouge)
- Bannière informative lors du changement d'état
- Icônes spécifiques pour fonctionnalités disponibles hors-ligne

#### Style des Éléments
- Démarcation claire des fonctionnalités disponibles/indisponibles
- Style spécifique pour les données mises en cache
- Indicateurs de fraîcheur des données (âge)

### 4.2. Scanner QR

#### Interface de Scan
- Fenêtre de preview plein écran
- Cadre de détection bien visible
- Contrôles minimaux et discrets
- Retour visuel instantané

#### Résultats
- Transition rapide vers écran de résultat
- Affichage clair du statut (succès/échec)
- Actions contextuelles évidentes
- Option de retour au scan

### 4.3. Compétitions et Événements

#### Affichage des Compétitions
- Cards avec image représentative
- Indicateurs de date/statut proéminents
- Catégorisation visuelle (discipline, type)
- Filtres et recherche accessibles

#### Interface de Notation
- Optimisée pour utilisation rapide
- Boutons de score larges et bien espacés
- Confirmation visuelle immédiate
- Mode paysage optimisé

### 4.4. Profil et Données Personnelles

#### Affichage du Profil
- Photo/avatar proéminent
- Informations hiérarchisées par importance
- Sections clairement délimitées
- Actions principales facilement accessibles

#### QR Code Personnel
- Taille maximale pour lisibilité
- Options de partage évidentes
- Informations d'expiration visibles
- Contrôles d'affichage optimisés

## 5. Guide d'Implémentation

### 5.1. Structure de composants React Native

```jsx
// Exemple de structure pour un bouton primaire
import React from 'react';
import { TouchableOpacity, Text, StyleSheet } from 'react-native';
import { colors, typography, spacing } from '../styles';

export const PrimaryButton = ({ label, onPress, disabled }) => (
  <TouchableOpacity 
    style={[
      styles.button, 
      disabled && styles.buttonDisabled
    ]} 
    onPress={onPress}
    disabled={disabled}
  >
    <Text style={[
      styles.buttonText, 
      disabled && styles.buttonTextDisabled
    ]}>
      {label}
    </Text>
  </TouchableOpacity>
);

const styles = StyleSheet.create({
  button: {
    backgroundColor: colors.primary,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.lg,
    borderRadius: 4,
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonDisabled: {
    backgroundColor: colors.gray400,
  },
  buttonText: {
    ...typography.button,
    color: colors.white,
  },
  buttonTextDisabled: {
    color: colors.gray600,
  },
});
```

### 5.2. Organisation des Styles

```jsx
// styles/colors.js
export default {
  primary: '#3F51B5',
  primaryDark: '#303F9F',
  primaryLight: '#C5CAE9',
  secondary: '#FF4081',
  // etc.
};

// styles/typography.js
export default {
  headline1: {
    fontSize: 28,
    fontWeight: 'bold',
    lineHeight: 34,
  },
  // etc.
};

// styles/spacing.js
export default {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

// styles/index.js
import colors from './colors';
import typography from './typography';
import spacing from './spacing';

export { colors, typography, spacing };
```

### 5.3. Gestion des Thèmes

```jsx
// context/ThemeContext.js
import React, { createContext, useState, useContext, useEffect } from 'react';
import { Appearance } from 'react-native';
import { lightTheme, darkTheme } from '../styles/themes';

const ThemeContext = createContext();

export const ThemeProvider = ({ children }) => {
  const [isDarkMode, setIsDarkMode] = useState(
    Appearance.getColorScheme() === 'dark'
  );
  
  useEffect(() => {
    const subscription = Appearance.addChangeListener(({ colorScheme }) => {
      setIsDarkMode(colorScheme === 'dark');
    });
    
    return () => subscription.remove();
  }, []);
  
  const theme = isDarkMode ? darkTheme : lightTheme;
  
  return (
    <ThemeContext.Provider value={{ theme, isDarkMode, setIsDarkMode }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => useContext(ThemeContext);
```

### 5.4. Responsive Design

```jsx
// utils/responsive.js
import { Dimensions } from 'react-native';

const { width, height } = Dimensions.get('window');

// Guideline sizes for standard 5" device
const guidelineBaseWidth = 350;
const guidelineBaseHeight = 680;

export const scale = (size) => width / guidelineBaseWidth * size;
export const verticalScale = (size) => height / guidelineBaseHeight * size;
export const moderateScale = (size, factor = 0.5) => size + (scale(size) - size) * factor;

export const isTablet = () => {
  const { width, height } = Dimensions.get('window');
  return (width > 600) || (height > 600);
};
```

## 6. Ressources

### 6.1. Exports d'Assets

#### Icônes
- Format SVG recommandé
- PNG en fallback (1x, 2x, 3x)
- Nommage cohérent: `icon_[nom]_[variante].svg`

#### Images
- Format PNG ou JPEG selon besoins
- Optimisation pour mobile
- Nommage: `img_[section]_[description].png`

### 6.2. Bibliothèques Recommandées

- **UI Components**: React Native Paper
- **Navigation**: React Navigation
- **Formulaires**: Formik + Yup
- **Animations**: React Native Reanimated
- **Gestion État**: Redux Toolkit ou Context API
- **QR Code**: react-native-qrcode-svg

### 6.3. Outils de Design

- **Design**: Figma
- **Prototypage**: Figma / Protopie
- **Collaboration**: Zeplin
- **Test d'accessibilité**: Stark