# 🚀 DÉPLOIEMENT APPLICATION MOBILE MARTIALCOMP

## 📱 **Configuration Production**

### **1. Configurer l'API pour la production**

```bash
# Dans le dossier mobile/
cd mobile

# Créer le fichier .env de production
cat > .env << 'EOF'
# Production Configuration
EXPO_PUBLIC_API_URL=https://martialcomp.com/api/v1
API_URL=https://martialcomp.com/api/v1
NODE_ENV=production
EOF

# Vérifier la configuration actuelle
cat src/config/api.ts
```

### **2. Modifier la configuration API**

Éditez `src/config/api.ts` :

```typescript
// Configuration pour production
export const API_URL = (process.env.EXPO_PUBLIC_API_URL as string) || 'https://martialcomp.com/api/v1';

// Mode production activé
export const isProduction = () => API_URL.includes('martialcomp.com');
```

### **3. Vérifier les dépendances**

```bash
# Installation des dépendances
npm install

# Vérification de la configuration
npm run build:check || npx expo doctor
```

## 🔗 **Tests de connexion API**

### **Test 1: Vérification des endpoints**

```bash
# Test des endpoints depuis le mobile
cd mobile
npm start

# Dans un autre terminal - Test API
node test-site-connectivity.js
```

### **Test 2: Test d'authentification**

```bash
# Test de l'authentification mobile
node -e "
const axios = require('axios');
const API_URL = 'https://martialcomp.com/api/v1';

async function testAuth() {
  try {
    // Test health
    const health = await axios.get('https://martialcomp.com/api/health/');
    console.log('✅ Health check:', health.status);
    
    // Test profile endpoint
    const profile = await axios.get(\`\${API_URL}/auth/profile/\`);
    console.log('✅ Profile endpoint accessible');
  } catch (error) {
    console.log('❌ Erreur:', error.response?.status, error.response?.data);
  }
}
testAuth();
"
```

## 📱 **Démarrage de l'application mobile**

### **Mode développement avec backend production :**

```bash
cd mobile

# Démarrer l'app avec configuration production
npm start

# Ou avec Expo CLI
npx expo start
```

### **Instructions pour les tests :**

1. **Scanner le QR code** avec votre téléphone (Expo Go app)
2. **L'app se connectera** à `https://martialcomp.com/api/v1`
3. **Tester la connexion** avec un utilisateur existant

## 🧪 **Tests de fonctionnalités**

### **Test 1: Connexion utilisateur**

```
Utilisateur de test : BGA_TESTUSER1
Mot de passe : TestPassword123!
```

### **Test 2: Scanner QR Code**

- Tester le scanner QR avec les codes d'organisations existantes
- Vérifier la navigation contextuelle

### **Test 3: Fonctionnalités hors-ligne**

- Tester le stockage local des profils
- Vérifier la synchronisation

### **Test 4: API Endpoints**

Vérifiez ces endpoints principaux :
- ✅ `/api/health/` - Santé de l'API
- ✅ `/api/v1/auth/profile/` - Profil utilisateur enrichi
- ✅ `/api/v1/mobile/dashboard/` - Dashboard mobile
- ✅ `/api/organizations/` - Organisations
- ✅ `/api/competitions/` - Compétitions

## 🚀 **Build Production (optionnel)**

### **Expo Build Service (EAS)**

```bash
# Installation EAS CLI
npm install -g @expo/eas-cli

# Connexion
eas login

# Configuration du build
eas build:configure

# Build Android
eas build --platform android --profile production

# Build iOS
eas build --platform ios --profile production
```

### **Configuration build dans eas.json :**

```json
{
  "cli": {
    "version": ">= 3.0.0"
  },
  "build": {
    "production": {
      "env": {
        "EXPO_PUBLIC_API_URL": "https://martialcomp.com/api/v1"
      }
    }
  }
}
```

## ✅ **Checklist de déploiement**

### **Configuration :**
- [ ] .env créé avec URL de production
- [ ] api.ts configuré pour production
- [ ] Dépendances installées

### **Tests :**
- [ ] Connexion API backend
- [ ] Authentification utilisateur
- [ ] Scanner QR codes
- [ ] Navigation entre écrans
- [ ] Synchronisation hors-ligne

### **Déploiement :**
- [ ] App fonctionne en mode développement
- [ ] Tests sur téléphone physique
- [ ] Build production (optionnel)

## 🎯 **Résultat attendu**

L'application mobile React Native sera :
- ✅ **Connectée** à `https://martialcomp.com`
- ✅ **Synchronisée** avec tous les utilisateurs et données
- ✅ **Fonctionnelle** avec scanner QR, authentification, hors-ligne
- ✅ **Prête** pour distribution

**L'écosystème complet sera opérationnel : Backend Django + Frontend Web + Application Mobile !**