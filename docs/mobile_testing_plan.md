# Plan de Tests pour l'Application Mobile MartialComp

## 1. Introduction

Ce plan de tests définit l'approche, les ressources et le calendrier des tests pour l'application mobile MartialComp. Il couvre les tests fonctionnels, d'interface utilisateur, de performance et de compatibilité.

## 2. Objectifs

- Vérifier que toutes les fonctionnalités implémentées fonctionnent comme prévu
- Assurer que l'application fonctionne correctement en mode hors-ligne
- Valider que l'interface utilisateur est adaptée aux différentes tailles d'écran
- Confirmer que l'application a des performances acceptables
- Vérifier la compatibilité avec différentes versions d'OS et appareils

## 3. Composants à tester

### 3.1 Authentification

| ID | Description | Priorité | Statut |
|----|-------------|----------|--------|
| AU-01 | Connexion avec identifiants valides | Haute | À faire |
| AU-02 | Connexion avec identifiants invalides | Haute | À faire |
| AU-03 | Inscription d'un nouvel utilisateur | Moyenne | À faire |
| AU-04 | Fonctionnement du refresh token | Haute | À faire |
| AU-05 | Déconnexion | Moyenne | À faire |
| AU-06 | Persistance de la session après redémarrage | Moyenne | À faire |
| AU-07 | Implémentation PKCE | Haute | À faire |

### 3.2 Profil Hors-ligne

| ID | Description | Priorité | Statut |
|----|-------------|----------|--------|
| PO-01 | Génération du profil hors-ligne | Haute | À faire |
| PO-02 | Validation du profil hors-ligne | Haute | À faire |
| PO-03 | Scan et décodage du QR code de profil | Haute | À faire |
| PO-04 | Affichage des informations du profil | Moyenne | À faire |
| PO-05 | Vérification de la validité du token | Haute | À faire |
| PO-06 | Gestion des tokens expirés | Moyenne | À faire |
| PO-07 | Vérification de la signature | Haute | À faire |

### 3.3 Scanner QR Code

| ID | Description | Priorité | Statut |
|----|-------------|----------|--------|
| QR-01 | Scan d'un QR code valide | Haute | À faire |
| QR-02 | Scan d'un QR code invalide | Moyenne | À faire |
| QR-03 | Traitement en mode hors-ligne | Haute | À faire |
| QR-04 | Stockage local des scans | Haute | À faire |
| QR-05 | Synchronisation des scans | Haute | À faire |
| QR-06 | Utilisation du flash | Basse | À faire |
| QR-07 | Vérification des permissions caméra | Moyenne | À faire |

### 3.4 Fonctionnalités spécifiques

| ID | Description | Priorité | Statut |
|----|-------------|----------|--------|
| FS-01 | Notation en temps réel pour les juges | Haute | À faire |
| FS-02 | Affichage des compétitions | Moyenne | À faire |
| FS-03 | Affichage des résultats | Moyenne | À faire |
| FS-04 | Navigation géolocalisée | Basse | À faire |
| FS-05 | Partage sur réseaux sociaux | Basse | À faire |

### 3.5 Synchronisation et Connectivité

| ID | Description | Priorité | Statut |
|----|-------------|----------|--------|
| SC-01 | Détection de connectivité réseau | Haute | À faire |
| SC-02 | Bascule automatique en mode hors-ligne | Haute | À faire |
| SC-03 | File d'attente des opérations hors-ligne | Haute | À faire |
| SC-04 | Synchronisation des données au retour de connexion | Haute | À faire |
| SC-05 | Résolution des conflits de synchronisation | Moyenne | À faire |

### 3.6 Interface Utilisateur

| ID | Description | Priorité | Statut |
|----|-------------|----------|--------|
| UI-01 | Adaptation aux différentes tailles d'écran | Haute | À faire |
| UI-02 | Support du mode portrait/paysage | Moyenne | À faire |
| UI-03 | Support des thèmes clair/sombre | Basse | À faire |
| UI-04 | Accessibilité (taille de texte, contraste) | Moyenne | À faire |
| UI-05 | Feedback tactile et visuel | Moyenne | À faire |
| UI-06 | Performance de la navigation | Haute | À faire |

## 4. Environnements de test

### 4.1 Android
- Versions d'OS: Android 7.0+
- Tailles d'écran: 5" à 10"
- Appareils principaux: 
  - Google Pixel (dernière génération)
  - Samsung Galaxy S
  - Samsung Galaxy Tab

### 4.2 iOS
- Versions d'OS: iOS 13+
- Tailles d'écran: 4.7" à 12.9"
- Appareils principaux:
  - iPhone (dernière génération)
  - iPhone SE (pour tester les petits écrans)
  - iPad

### 4.3 Conditions de connectivité
- Wi-Fi rapide (>50 Mbps)
- Wi-Fi lent (<5 Mbps)
- Données mobiles 4G
- Données mobiles 3G lent
- Mode avion (hors-ligne complet)
- Connectivité intermittente

## 5. Types de tests

### 5.1 Tests unitaires
Tests automatisés qui vérifient le comportement des composants individuels.

```javascript
// Exemple de test unitaire pour la validation de token
test('should validate a correct offline token', () => {
  const token = "eyJhbGciOiJIUzI1..."; // Token de test valide
  const result = verifyOfflineProfile(token);
  expect(result.valid).toBe(true);
});
```

### 5.2 Tests d'intégration
Tests qui vérifient l'interaction entre plusieurs composants.

```javascript
// Exemple de test d'intégration pour le processus d'authentification
test('should complete the full authentication flow', async () => {
  const authManager = new AuthManager();
  const result = await authManager.login('testuser', 'password');
  expect(result.success).toBe(true);
  
  const userProfile = await authManager.getUserProfile();
  expect(userProfile).not.toBeNull();
  
  const logoutResult = await authManager.logout();
  expect(logoutResult.success).toBe(true);
});
```

### 5.3 Tests d'interface utilisateur
Tests qui vérifient l'apparence et le comportement de l'interface utilisateur.

```javascript
// Exemple de test UI pour le scanner QR
test('QR scanner displays correct UI elements', async () => {
  const { getByTestId } = render(<QRScanner />);
  expect(getByTestId('scanner-overlay')).toBeVisible();
  expect(getByTestId('flash-button')).toBeVisible();
  expect(getByTestId('scan-type-selector')).toBeVisible();
});
```

### 5.4 Tests de performance
Tests qui mesurent les performances de l'application.

- Temps de démarrage de l'application
- Temps de réponse des opérations principales
- Utilisation de la mémoire
- Consommation de batterie
- Utilisation du réseau

### 5.5 Tests de compatibilité
Tests sur différents appareils et versions d'OS.

## 6. Procédure de test

### 6.1 Tests automatisés
1. Exécuter les tests unitaires pendant le développement
2. Exécuter les tests d'intégration avant chaque version
3. Exécuter les tests UI automatisés pour les parcours critiques

### 6.2 Tests manuels
1. Suivre les scénarios de test définis
2. Documenter les résultats avec captures d'écran
3. Vérifier les cas particuliers et les conditions limites

### 6.3 Tests utilisateurs
1. Sélectionner un groupe d'utilisateurs représentatifs
2. Définir les tâches à accomplir
3. Observer et noter les problèmes rencontrés
4. Recueillir les retours sur l'expérience

## 7. Calendrier des tests

| Phase | Durée | Description |
|-------|-------|-------------|
| Tests unitaires | En continu | Pendant le développement |
| Tests d'intégration | 1 semaine | Après chaque sprint |
| Tests UI | 1 semaine | Avant la release candidate |
| Tests de performance | 3 jours | Avant la release candidate |
| Tests de compatibilité | 2 jours | Avant la release candidate |
| Tests utilisateurs | 1 semaine | Sur la release candidate |
| Tests de régression | 2 jours | Avant la release finale |

## 8. Ressources nécessaires

- 1 testeur iOS
- 1 testeur Android
- 1 développeur pour corriger les bugs identifiés
- Appareils de test (voir section 4)
- Environnements de test (dev, staging, prod)
- Outils de test (Jest, Detox, etc.)

## 9. Critères de sortie

- Tous les tests prioritaires passent à 100%
- Pas de bug critique ou majeur
- Performance acceptable sur tous les appareils cibles
- Validation par les utilisateurs de test

## 10. Gestion des risques

| Risque | Impact | Probabilité | Atténuation |
|--------|--------|-------------|-------------|
| Problèmes de compatibilité sur certains appareils | Moyen | Moyenne | Tests sur un large éventail d'appareils |
| Problèmes de performance sur les appareils anciens | Haut | Moyenne | Optimisation du code, tests spécifiques |
| Problèmes de synchronisation des données | Haut | Haute | Tests exhaustifs des scénarios hors-ligne |
| Problèmes de sécurité dans l'authentification | Très haut | Basse | Audit de sécurité, tests de pénétration |
| Problèmes d'ergonomie sur petits écrans | Moyen | Moyenne | Tests sur différentes tailles d'écran |

## 11. Outils de test recommandés

- **Jest**: Tests unitaires et d'intégration
- **React Native Testing Library**: Tests de composants
- **Detox**: Tests end-to-end
- **Appium**: Tests sur appareils réels
- **Firebase Test Lab**: Tests sur une variété d'appareils virtuels
- **XCTest**: Tests natifs iOS
- **Espresso**: Tests natifs Android
- **Crashlytics**: Monitoring des crashes en production

## Annexe: Scripts de test

### Script de test pour l'authentification

```javascript
// Test d'authentification

// 1. Tentative de connexion avec identifiants invalides
// 2. Vérifier message d'erreur approprié
// 3. Connexion avec identifiants valides
// 4. Vérifier redirection vers dashboard
// 5. Vérifier que le token est stocké
// 6. Fermer puis rouvrir l'application
// 7. Vérifier que la session est maintenue
// 8. Déconnexion
// 9. Vérifier redirection vers login
```

### Script de test pour le profil hors-ligne

```javascript
// Test de profil hors-ligne

// 1. Activer le mode avion
// 2. Ouvrir l'application
// 3. Scanner un QR code de profil
// 4. Vérifier que les informations sont correctement affichées
// 5. Vérifier la validité du profil
// 6. Désactiver le mode avion
// 7. Vérifier que l'application revient en mode connecté
```

## Rapport de tests

Un rapport de tests sera généré à chaque cycle, incluant:
- Nombre de tests exécutés, réussis, échoués
- Couverture de code
- Liste des bugs identifiés
- Métriques de performance
- Recommandations pour les corrections