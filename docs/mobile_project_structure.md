# Structure du Projet React Native - MartialComp Mobile

## Vue d'ensemble

Ce document définit la structure de base du projet React Native pour l'application mobile MartialComp. Il couvre l'organisation des fichiers, les dépendances principales et les conventions de codage à suivre.

## 1. Structure des Répertoires

```
martialcomp-mobile/
├── android/               # Configuration native Android
├── ios/                   # Configuration native iOS
├── src/                   # Code source principal
│   ├── api/               # Services d'API et intégrations backend
│   ├── assets/            # Ressources statiques (images, fonts, etc.)
│   ├── components/        # Composants réutilisables
│   ├── config/            # Configuration de l'application
│   ├── contexts/          # Context API pour la gestion d'état
│   ├── hooks/             # Hooks personnalisés
│   ├── navigation/        # Configuration de la navigation
│   ├── screens/           # Écrans de l'application
│   ├── services/          # Services (stockage local, permissions, etc.)
│   ├── store/             # État global (Redux/MobX si utilisé)
│   ├── styles/            # Styles partagés et thèmes
│   ├── types/             # Types TypeScript
│   └── utils/             # Fonctions utilitaires
├── __tests__/             # Tests
├── .env                   # Variables d'environnement (dev)
├── .env.production        # Variables d'environnement (prod)
├── App.tsx                # Point d'entrée de l'application
├── index.js               # Point d'entrée React Native
├── app.json               # Configuration de l'application
├── package.json           # Dépendances et scripts
└── tsconfig.json          # Configuration TypeScript
```

## 2. Structure Détaillée

### 2.1. `/src/api`

Gestion des appels API et intégration avec le backend.

```
api/
├── client.ts              # Configuration Axios/Fetch
├── auth.ts                # Endpoints d'authentification
├── competition.ts         # Endpoints de compétitions
├── profile.ts             # Endpoints de profil
├── qrcode.ts              # Endpoints de QR codes
├── types.ts               # Types d'API
└── utils.ts               # Utilitaires pour les requêtes
```

### 2.2. `/src/components`

Composants réutilisables organisés par catégorie.

```
components/
├── auth/                  # Composants d'authentification
├── common/                # Composants génériques
│   ├── Button.tsx
│   ├── Card.tsx
│   ├── Input.tsx
│   ├── Loading.tsx
│   └── ...
├── forms/                 # Composants de formulaire
├── layout/                # Composants de mise en page
├── modals/                # Fenêtres modales
├── navigation/            # Éléments de navigation
├── qrcode/                # Composants liés aux QR codes
│   ├── Scanner.tsx
│   ├── Generator.tsx
│   ├── ResultCard.tsx
│   └── ...
├── profile/               # Composants de profil
├── competition/           # Composants de compétition
└── ui/                    # Elements UI de base
```

### 2.3. `/src/screens`

Écrans organisés par section fonctionnelle.

```
screens/
├── auth/                  # Écrans d'authentification
│   ├── LoginScreen.tsx
│   ├── RegisterScreen.tsx
│   ├── ForgotPasswordScreen.tsx
│   └── ...
├── home/                  # Écrans d'accueil
│   ├── DashboardScreen.tsx
│   ├── NotificationsScreen.tsx
│   └── ...
├── scanner/               # Écrans du scanner
│   ├── ScannerScreen.tsx
│   ├── ScanResultScreen.tsx
│   ├── HistoryScreen.tsx
│   └── ...
├── competition/           # Écrans de compétition
│   ├── CompetitionListScreen.tsx
│   ├── CompetitionDetailScreen.tsx
│   ├── JudgeScreen.tsx
│   └── ...
├── profile/               # Écrans de profil
│   ├── ProfileScreen.tsx
│   ├── EditProfileScreen.tsx
│   ├── OfflineProfileScreen.tsx
│   └── ...
└── more/                  # Écrans divers
    ├── SettingsScreen.tsx
    ├── HelpScreen.tsx
    └── ...
```

### 2.4. `/src/navigation`

Configuration de la navigation de l'application.

```
navigation/
├── AppNavigator.tsx       # Navigateur principal
├── AuthNavigator.tsx      # Navigation d'authentification
├── HomeNavigator.tsx      # Navigation du tableau de bord
├── ScannerNavigator.tsx   # Navigation du scanner
├── ProfileNavigator.tsx   # Navigation du profil
├── CompetitionNavigator.tsx # Navigation des compétitions
├── MoreNavigator.tsx      # Navigation divers
└── navigationUtils.ts     # Utilitaires de navigation
```

### 2.5. `/src/services`

Services pour les fonctionnalités internes.

```
services/
├── auth/                  # Service d'authentification
│   ├── authService.ts
│   ├── tokenStorage.ts
│   └── ...
├── storage/               # Stockage local
│   ├── asyncStorage.ts
│   ├── secureStorage.ts
│   └── ...
├── offline/               # Gestion du mode hors-ligne
│   ├── syncService.ts
│   ├── offlineQueue.ts
│   └── ...
├── qrcode/                # Services QR code
│   ├── scannerService.ts
│   ├── generatorService.ts
│   ├── verificationService.ts
│   └── ...
└── notifications/         # Service de notifications
    ├── pushNotifications.ts
    ├── localNotifications.ts
    └── ...
```

### 2.6. `/src/styles`

Styles partagés et système de design.

```
styles/
├── colors.ts             # Palette de couleurs
├── typography.ts         # Styles de texte
├── spacing.ts            # Système d'espacement
├── themes/               # Thèmes (clair/sombre)
│   ├── light.ts
│   ├── dark.ts
│   └── index.ts
├── components/           # Styles spécifiques aux composants
└── globalStyles.ts       # Styles globaux
```

## 3. Configuration et Dépendances

### 3.1. Dépendances Principales

```json
{
  "dependencies": {
    "@react-navigation/native": "^6.1.9",
    "@react-navigation/native-stack": "^6.9.17",
    "@react-navigation/bottom-tabs": "^6.5.11",
    "react-native-safe-area-context": "^4.7.4",
    "react-native-screens": "^3.27.0",
    "react-native-paper": "^5.11.3",
    "react-native-vector-icons": "^10.0.2",
    "react-native-svg": "^14.0.0",
    "@react-native-async-storage/async-storage": "^1.21.0",
    "react-native-reanimated": "^3.5.4",
    "react-native-gesture-handler": "^2.14.0",
    "react-native-device-info": "^10.11.0",
    "axios": "^1.6.2",
    "formik": "^2.4.5",
    "yup": "^1.3.2",
    "date-fns": "^2.30.0",
    "react-native-camera": "^4.2.1",
    "react-native-qrcode-scanner": "^1.5.5",
    "react-native-qrcode-svg": "^6.2.0",
    "i18next": "^23.7.6",
    "react-i18next": "^13.5.0",
    "@react-native-community/netinfo": "^11.1.0",
    "react-native-permissions": "^3.10.1"
  },
  "devDependencies": {
    "@types/react": "^18.2.38",
    "@types/react-native": "^0.72.7",
    "typescript": "^5.3.2",
    "jest": "^29.7.0",
    "@testing-library/react-native": "^12.4.0",
    "eslint": "^8.54.0",
    "prettier": "^3.1.0"
  }
}
```

### 3.2. Configuration TypeScript

```json
{
  "compilerOptions": {
    "target": "esnext",
    "module": "commonjs",
    "lib": ["es2019"],
    "jsx": "react-native",
    "strict": true,
    "moduleResolution": "node",
    "baseUrl": "./",
    "paths": {
      "@/*": ["src/*"]
    },
    "allowSyntheticDefaultImports": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "resolveJsonModule": true
  },
  "exclude": [
    "node_modules",
    "babel.config.js",
    "metro.config.js",
    "jest.config.js"
  ]
}
```

### 3.3. Configuration ESLint

```json
{
  "extends": [
    "eslint:recommended",
    "plugin:react/recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:react-hooks/recommended",
    "prettier"
  ],
  "parser": "@typescript-eslint/parser",
  "plugins": ["react", "react-native", "@typescript-eslint", "prettier"],
  "rules": {
    "prettier/prettier": "error",
    "react/prop-types": "off",
    "react/react-in-jsx-scope": "off",
    "no-console": ["warn", { "allow": ["warn", "error"] }]
  }
}
```

## 4. Conventions de Codage

### 4.1. Nommage

- **Fichiers de composants**: PascalCase (ex: `Button.tsx`)
- **Fichiers utilitaires**: camelCase (ex: `authUtils.ts`)
- **Constantes**: UPPER_SNAKE_CASE (ex: `API_URL`)
- **Interfaces/Types**: PascalCase préfixé par I/T (ex: `IUser`, `TAuthState`)
- **Composants**: PascalCase (ex: `LoginScreen`)
- **Fonctions/Méthodes**: camelCase (ex: `fetchUserData`)

### 4.2. Imports

Organiser les imports dans cet ordre:
1. Imports de bibliothèques externes
2. Imports de composants/fonctions internes
3. Imports de types
4. Imports de styles/assets

```typescript
// Bibliothèques externes
import React, { useState, useEffect } from 'react';
import { View, Text } from 'react-native';

// Imports internes
import { Button } from '@/components/common';
import { useAuth } from '@/hooks';
import { fetchUserProfile } from '@/api/profile';

// Types
import { IUser } from '@/types';

// Styles
import { colors } from '@/styles';
import userIcon from '@/assets/icons/user.png';
```

### 4.3. Structure des Composants

Préférer les composants fonctionnels avec hooks.

```typescript
import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Button } from '@/components/common';
import { colors, typography, spacing } from '@/styles';

interface ProfileCardProps {
  userName: string;
  role: string;
  onPress: () => void;
}

export const ProfileCard: React.FC<ProfileCardProps> = ({ 
  userName, 
  role, 
  onPress 
}) => {
  const [isActive, setIsActive] = useState(false);

  useEffect(() => {
    // Effet si nécessaire
  }, []);

  return (
    <View style={styles.container}>
      <Text style={styles.userName}>{userName}</Text>
      <Text style={styles.role}>{role}</Text>
      <Button 
        label="Voir profil" 
        onPress={onPress}
        variant="primary"
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: spacing.md,
    backgroundColor: colors.white,
    borderRadius: 8,
    elevation: 2,
  },
  userName: {
    ...typography.headline3,
    color: colors.gray900,
    marginBottom: spacing.xs,
  },
  role: {
    ...typography.body2,
    color: colors.gray600,
    marginBottom: spacing.md,
  },
});
```

### 4.4. Gestion d'État

Utiliser Context API pour l'état partagé entre quelques composants et Redux pour l'état global complexe.

```typescript
// src/contexts/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { IUser } from '@/types';
import { loginUser, logoutUser, refreshToken } from '@/services/auth/authService';

interface AuthContextProps {
  user: IUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshSession: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextProps | undefined>(undefined);

export const AuthProvider: React.FC = ({ children }) => {
  const [user, setUser] = useState<IUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Implémentation...

  return (
    <AuthContext.Provider value={{
      user,
      isLoading,
      isAuthenticated: !!user,
      login,
      logout,
      refreshSession,
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
```

### 4.5. API et Services

Séparer la logique d'API de la logique de composant.

```typescript
// src/api/auth.ts
import { apiClient } from './client';
import { ILoginRequest, ILoginResponse, IRefreshTokenRequest } from '@/types';

export const login = async (data: ILoginRequest): Promise<ILoginResponse> => {
  try {
    const response = await apiClient.post('/auth/login/', data);
    return response.data;
  } catch (error) {
    throw new Error('Failed to login');
  }
};

export const refreshToken = async (data: IRefreshTokenRequest): Promise<ILoginResponse> => {
  try {
    const response = await apiClient.post('/auth/refresh/', data);
    return response.data;
  } catch (error) {
    throw new Error('Failed to refresh token');
  }
};

// src/services/auth/authService.ts
import * as authApi from '@/api/auth';
import { tokenStorage } from './tokenStorage';
import { IUser } from '@/types';

export const loginUser = async (email: string, password: string): Promise<IUser> => {
  const response = await authApi.login({ email, password });
  await tokenStorage.storeTokens(response.access, response.refresh);
  return response.user;
};
```

## 5. Structure des Écrans

### 5.1. Exemple d'Écran de Connexion

```typescript
// src/screens/auth/LoginScreen.tsx
import React, { useState } from 'react';
import { View, Text, StyleSheet, KeyboardAvoidingView, Platform } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { Formik } from 'formik';
import * as Yup from 'yup';

import { Button, Input, Logo, ErrorMessage } from '@/components/common';
import { useAuth } from '@/contexts/AuthContext';
import { colors, typography, spacing } from '@/styles';

const loginSchema = Yup.object().shape({
  email: Yup.string().email('Email invalide').required('Email requis'),
  password: Yup.string().required('Mot de passe requis'),
});

const LoginScreen: React.FC = () => {
  const navigation = useNavigation();
  const { login } = useAuth();
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (values: { email: string; password: string }) => {
    try {
      setError(null);
      await login(values.email, values.password);
      // Navigation handled by auth state change
    } catch (err) {
      setError('Identifiants incorrects. Veuillez réessayer.');
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.container}
    >
      <View style={styles.logoContainer}>
        <Logo size="large" />
        <Text style={styles.title}>MartialComp</Text>
      </View>

      <Formik
        initialValues={{ email: '', password: '' }}
        validationSchema={loginSchema}
        onSubmit={handleLogin}
      >
        {({ handleChange, handleBlur, handleSubmit, values, errors, touched }) => (
          <View style={styles.formContainer}>
            <Input
              label="Email"
              value={values.email}
              onChangeText={handleChange('email')}
              onBlur={handleBlur('email')}
              error={touched.email && errors.email}
              keyboardType="email-address"
              autoCapitalize="none"
            />

            <Input
              label="Mot de passe"
              value={values.password}
              onChangeText={handleChange('password')}
              onBlur={handleBlur('password')}
              error={touched.password && errors.password}
              secureTextEntry
            />

            {error && <ErrorMessage message={error} />}

            <Button 
              label="Se connecter" 
              onPress={handleSubmit} 
              variant="primary"
              style={styles.loginButton}
            />

            <View style={styles.linkContainer}>
              <Button
                label="Mot de passe oublié ?"
                onPress={() => navigation.navigate('ForgotPassword')}
                variant="text"
              />
              <Button
                label="Créer un compte"
                onPress={() => navigation.navigate('Register')}
                variant="text"
              />
            </View>
          </View>
        )}
      </Formik>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.white,
    padding: spacing.lg,
  },
  logoContainer: {
    alignItems: 'center',
    marginTop: spacing.xxl,
    marginBottom: spacing.xl,
  },
  title: {
    ...typography.headline1,
    color: colors.primary,
    marginTop: spacing.sm,
  },
  formContainer: {
    width: '100%',
  },
  loginButton: {
    marginTop: spacing.lg,
  },
  linkContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: spacing.lg,
  },
});

export default LoginScreen;
```

### 5.2. Exemple d'Écran de Scanner

```typescript
// src/screens/scanner/ScannerScreen.tsx
import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { BarCodeScanner } from 'expo-barcode-scanner';
import { useNetInfo } from '@react-native-community/netinfo';
import { Ionicons } from '@expo/vector-icons';

import { ScanFrame, ScanTypePicker, StatusBanner } from '@/components/qrcode';
import { processScan } from '@/services/qrcode/scannerService';
import { ScanType } from '@/types';
import { colors, spacing } from '@/styles';

const ScannerScreen: React.FC = () => {
  const navigation = useNavigation();
  const netInfo = useNetInfo();
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [scanned, setScanned] = useState(false);
  const [scanType, setScanType] = useState<ScanType>('attendance');
  const [flashMode, setFlashMode] = useState(BarCodeScanner.Constants.FlashMode.off);
  
  const isOffline = !netInfo.isConnected;

  useEffect(() => {
    (async () => {
      const { status } = await BarCodeScanner.requestPermissionsAsync();
      setHasPermission(status === 'granted');
    })();
  }, []);

  const handleBarCodeScanned = async ({ type, data }: { type: string; data: string }) => {
    if (scanned) return;
    
    setScanned(true);
    
    try {
      const result = await processScan(data, scanType, isOffline);
      navigation.navigate('ScanResult', { result });
    } catch (error) {
      navigation.navigate('ScanResult', { 
        error: true, 
        message: error.message 
      });
    }
  };

  if (hasPermission === null) {
    return <Text>Demande d'autorisation de caméra...</Text>;
  }
  
  if (hasPermission === false) {
    return <Text>Pas d'accès à la caméra</Text>;
  }

  return (
    <View style={styles.container}>
      {isOffline && (
        <StatusBanner 
          message="Mode hors-ligne actif. Les scans seront synchronisés plus tard."
          type="warning"
        />
      )}
      
      <ScanTypePicker 
        selected={scanType}
        onChange={setScanType}
        disabled={isOffline ? ['competition'] : []}
      />
      
      <View style={styles.cameraContainer}>
        <BarCodeScanner
          onBarCodeScanned={scanned ? undefined : handleBarCodeScanned}
          style={StyleSheet.absoluteFillObject}
          flashMode={flashMode}
          barCodeTypes={[BarCodeScanner.Constants.BarCodeType.qr]}
        />
        
        <ScanFrame />
        
        <View style={styles.controls}>
          <TouchableOpacity
            style={styles.flashButton}
            onPress={() => setFlashMode(
              flashMode === BarCodeScanner.Constants.FlashMode.torch
                ? BarCodeScanner.Constants.FlashMode.off
                : BarCodeScanner.Constants.FlashMode.torch
            )}
          >
            <Ionicons 
              name={flashMode === BarCodeScanner.Constants.FlashMode.torch 
                ? "flash" : "flash-outline"} 
              size={24} 
              color={colors.white}
            />
          </TouchableOpacity>
          
          <TouchableOpacity
            style={styles.historyButton}
            onPress={() => navigation.navigate('ScanHistory')}
          >
            <Ionicons name="time-outline" size={24} color={colors.white} />
          </TouchableOpacity>
        </View>
      </View>
      
      {scanned && (
        <TouchableOpacity 
          style={styles.scanAgainButton}
          onPress={() => setScanned(false)}
        >
          <Text style={styles.scanAgainText}>Scanner à nouveau</Text>
        </TouchableOpacity>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.gray900,
  },
  cameraContainer: {
    flex: 1,
    position: 'relative',
  },
  controls: {
    position: 'absolute',
    bottom: spacing.xl,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  flashButton: {
    backgroundColor: 'rgba(0,0,0,0.6)',
    width: 56,
    height: 56,
    borderRadius: 28,
    justifyContent: 'center',
    alignItems: 'center',
  },
  historyButton: {
    backgroundColor: 'rgba(0,0,0,0.6)',
    width: 56,
    height: 56,
    borderRadius: 28,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scanAgainButton: {
    backgroundColor: colors.primary,
    padding: spacing.md,
    margin: spacing.lg,
    borderRadius: 8,
    alignItems: 'center',
  },
  scanAgainText: {
    color: colors.white,
    fontWeight: 'bold',
  },
});

export default ScannerScreen;
```

## 6. Scripts et Commandes

### 6.1. Scripts package.json

```json
{
  "scripts": {
    "android": "react-native run-android",
    "ios": "react-native run-ios",
    "start": "react-native start",
    "test": "jest",
    "lint": "eslint . --ext .js,.jsx,.ts,.tsx",
    "format": "prettier --write \"src/**/*.{ts,tsx}\"",
    "typecheck": "tsc --noEmit",
    "build:android": "cd android && ./gradlew assembleRelease",
    "build:ios": "cd ios && xcodebuild -workspace MartialComp.xcworkspace -scheme MartialComp -configuration Release",
    "clean": "react-native-clean-project",
    "postinstall": "patch-package"
  }
}
```

### 6.2. Commandes de Développement

```bash
# Installation des dépendances
npm install

# Lancement en développement
npm run ios     # Pour iOS
npm run android # Pour Android

# Vérification du code
npm run lint    # Analyse statique
npm run typecheck # Vérification des types
npm run test    # Exécution des tests

# Construction des builds de production
npm run build:android
npm run build:ios
```

## 7. Guides de Développement

### 7.1. Ajout d'un Nouvel Écran

1. Créer le fichier dans `src/screens/[section]/NewScreen.tsx`
2. Ajouter la route dans le navigateur approprié dans `src/navigation/`
3. Implémenter l'écran en utilisant les composants existants
4. Ajouter les tests dans `__tests__/screens/[section]/NewScreen.test.tsx`

### 7.2. Ajout d'un Nouveau Composant

1. Créer le fichier dans `src/components/[category]/NewComponent.tsx`
2. Implémenter l'interface props avec TypeScript
3. Créer les styles en utilisant les valeurs du design system
4. Exporter depuis le fichier index.ts de la catégorie
5. Ajouter les tests dans `__tests__/components/[category]/NewComponent.test.tsx`

### 7.3. Intégration d'une Nouvelle API

1. Ajouter les types d'API dans `src/api/types.ts`
2. Créer les fonctions d'API dans `src/api/[domain].ts`
3. Créer ou mettre à jour le service dans `src/services/[domain]/`
4. Intégrer avec les composants ou hooks

### 7.4. Ajout d'une Nouvelle Langue

1. Ajouter le fichier de traduction dans `src/assets/translations/[lang].json`
2. Mettre à jour `src/i18n/index.ts` pour inclure la nouvelle langue
3. Ajouter l'option dans le sélecteur de langue

## 8. Bonnes Pratiques

### 8.1. Performance

- Utiliser `React.memo()` pour les composants qui reçoivent souvent les mêmes props
- Éviter les re-renders inutiles avec `useCallback` et `useMemo`
- Optimiser les listes avec `FlatList` et la propriété `keyExtractor`
- Minimiser le state global et préférer le state local quand possible
- Utiliser `InteractionManager` pour les opérations lourdes après les animations

### 8.2. Sécurité

- Ne jamais stocker les secrets en clair dans le code
- Utiliser Secure Storage pour les données sensibles (tokens, etc.)
- Valider toutes les entrées utilisateur
- Implémenter le PKCE pour l'authentification OAuth
- Chiffrer les données stockées localement

### 8.3. Accessibilité

- Utiliser les props d'accessibilité (`accessibilityLabel`, etc.)
- Tester avec VoiceOver/TalkBack
- Supporter le mode texte agrandi
- Assurer un contraste suffisant
- Fournir des alternatives aux informations visuelles

### 8.4. Internationalisation

- Extraire tous les textes dans les fichiers de traduction
- Utiliser des formats adaptés pour dates, nombres, monnaies
- Supporter les directions RTL pour langues comme l'arabe
- Prévoir de l'espace pour les textes plus longs dans certaines langues

## 9. Déploiement

### 9.1. Préparation Android

1. Générer une clé de signature:
```bash
keytool -genkeypair -v -keystore martialcomp.keystore -alias martialcomp -keyalg RSA -keysize 2048 -validity 10000
```

2. Configurer `android/app/build.gradle` pour la version de production:
```gradle
signingConfigs {
    release {
        storeFile file('martialcomp.keystore')
        storePassword System.getenv("KEYSTORE_PASSWORD")
        keyAlias 'martialcomp'
        keyPassword System.getenv("KEY_PASSWORD")
    }
}
```

3. Construire l'APK ou le bundle:
```bash
npm run build:android
```

### 9.2. Préparation iOS

1. Configurer les certificats dans Apple Developer Portal
2. Configurer le provisioning profile dans Xcode
3. Définir le numéro de version et build
4. Construire l'archive:
```bash
npm run build:ios
```

### 9.3. CI/CD

Exemple de configuration GitHub Actions:

```yaml
name: Build and Deploy

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Node.js
        uses: actions/setup-node@v2
        with:
          node-version: '14'
      - name: Install dependencies
        run: npm ci
      - name: Run linter
        run: npm run lint
      - name: Run type checker
        run: npm run typecheck
      - name: Run tests
        run: npm test

  build-android:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      # ... steps to build Android app
      
  build-ios:
    needs: test
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v2
      # ... steps to build iOS app
```

## 10. Conclusion

Cette structure de projet est conçue pour maximiser la maintenabilité, la lisibilité et la performance de l'application mobile MartialComp. Elle suit les meilleures pratiques de développement React Native et s'adapte aux besoins spécifiques de l'application.

Les développeurs sont encouragés à suivre ces conventions pour assurer une cohérence dans la base de code et faciliter la collaboration.