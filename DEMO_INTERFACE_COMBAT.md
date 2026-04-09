# Démonstration Interface de Combat V2

## Combat de test créé ✅

Un combat de test a été créé avec les données suivantes :
- **ID du combat** : 1
- **Combattant Rouge** : Pratiquant Alpha (AkomanT Club)
- **Combattant Blanc** : Nom non défini (Bach Hac)
- **Configuration** : Taekwondo Standard
- **Statut** : Planifié

## Accès à l'interface

### URL principale avec mode simulation
```
http://127.0.0.1:8888/en/competitions/combat/combats/1/interface-v2/?simulation=1
```

### URL sans simulation (combat réel)
```
http://127.0.0.1:8888/en/competitions/combat/combats/1/interface-v2/
```

## Fonctionnalités de la nouvelle interface

### 1. **Affichage Double Écran**
L'interface simule parfaitement un système professionnel à 2 écrans :

- **Colonne Rouge (Gauche)** 
  - Fond rouge gradient (#dc3545 → #a02530)
  - Score géant blanc
  - 6 boutons de scoring (Poing +1, Pied Corps +2, Pied Tête +3, etc.)
  - Indicateurs de pénalités (Kyong-go, Gam-jeom)
  - Statistiques en temps réel

- **Colonne Blanche (Droite)**
  - Fond blanc gradient (#f8f9fa → #e9ecef)
  - Score géant noir
  - Même configuration de boutons
  - Mêmes indicateurs et statistiques

### 2. **Zone Centrale de Contrôle**
- **Timer principal** : Chronomètre géant (format MM:SS)
- **Indicateur de round** : Round actuel / Total
- **Boutons de contrôle** :
  - Pause/Reprise
  - Réinitialiser Timer
  - Fin du Round
  - Arrêt Médical
  - Terminer Combat
- **Historique** : 10 dernières actions avec horodatage

### 3. **Mode Simulation**
En ajoutant `?simulation=1` à l'URL :
- Bannière "SIMULATION" en filigrane
- Tous les boutons sont actifs même si le combat n'est pas "en cours"
- Actions automatiques simulées toutes les 7 secondes
- Données d'exemple pré-remplies (scores 12-8)

### 4. **Raccourcis Clavier**

#### Combattant Rouge
- `Q` → Poing (+1 point)
- `W` → Pied Corps (+2 points)
- `E` → Pied Tête (+3 points)
- `R` → Retourné Corps (+4 points)
- `T` → Retourné Tête (+5 points)
- `A` → Kyong-go (-0.5 point)

#### Combattant Blanc
- `U` → Poing (+1 point)
- `I` → Pied Corps (+2 points)
- `O` → Pied Tête (+3 points)
- `P` → Retourné Corps (+4 points)
- `[` → Retourné Tête (+5 points)
- `J` → Kyong-go (-0.5 point)

#### Contrôles Généraux
- `ESPACE` → Pause/Reprise
- `ÉCHAP` → Réinitialiser Timer
- `ENTRÉE` → Fin du Round

### 5. **Animations et Effets**
- **Flash du score** : Animation d'échelle lors de l'attribution de points
- **Couleurs d'actions** : 
  - Vert pour les points positifs
  - Rouge pour les pénalités
- **Mode plein écran** : Bouton pour passer en présentation

### 6. **Règles Automatiques Implémentées**
- **Victoire par écart** : Si différence ≥ 20 points
- **Disqualification automatique** :
  - 10 Kyong-go (avertissements)
  - 5 Gam-jeom (déductions)
- **Animation de victoire** : Pulsation dorée du gagnant

## Test de l'interface

1. Ouvrez l'URL dans votre navigateur
2. Vous verrez l'interface avec les scores 12-8 en mode simulation
3. Testez les raccourcis clavier (Q, W, E pour Rouge / U, I, O pour Blanc)
4. Observez les animations de score et l'historique des actions
5. Utilisez ESPACE pour mettre en pause le chronomètre
6. Cliquez sur "Plein écran" pour une expérience immersive

## Comparaison avec l'ancienne interface

| Aspect | Ancienne Interface | Nouvelle Interface V2 |
|--------|-------------------|---------------------|
| **Design** | Une seule colonne | Double écran professionnel |
| **Scores** | Taille normale | Scores géants (15rem) |
| **Boutons** | Petits badges | Grands boutons avec descriptions |
| **Animations** | Basiques | Flash, pulsations, gradients |
| **Raccourcis** | Non | Complets (Q-T, U-[) |
| **Statistiques** | Non | Précision, actions, touches tête |
| **Mode simulation** | Non | Oui avec données d'exemple |

## Prochaines étapes

Pour utiliser cette interface en production :

1. **Démarrer un combat réel** depuis l'interface de gestion
2. **Configurer 2 écrans physiques** (ou 2 fenêtres de navigateur)
3. **Former les arbitres** aux raccourcis clavier
4. **Tester le son** (à implémenter)
5. **Configurer les WebSockets** pour un temps réel parfait