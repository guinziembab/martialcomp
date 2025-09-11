# 🥋 Architecture Backend → Mobile MartialComp

## 📊 Mapping Complet des 14 Applications Django

| **App Backend** | **Modèles Clés** | **Fonctionnalités Web** | **API Actuelle** | **Priorité Mobile** | **Écrans Mobile Requis** |
|---|---|---|---|---|---|
| **🔐 api_auth** | User, JWT | Authentification | ✅ `/api/v1/auth/login/` | **P0 - CRITIQUE** | LoginScreen, ProfileScreen |
| **🏛️ organizations** | Organization, Member, Affiliation | CRUD Orga, Membres | ✅ `/api/organizations/` | **P1 - ESSENTIEL** | OrganizationScreen, MembersScreen |
| **🏆 competitions** | Competition, Registration, Event, QR, Scoring | Dashboards, QR, Scoring, Events | ✅ `/api/competitions/upcoming/` | **P1 - ESSENTIEL** | CompetitionsScreen, QRScannerScreen |
| **💳 competitions/payment** | Transaction, Payment, Webhook | Paiements compétitions | ❌ Pas d'API | **P2 - IMPORTANT** | PaymentScreen |
| **📄 documents** | DocumentMetadata, GoogleDrive | Gestion documents | ✅ ViewSets complets | **P3 - UTILE** | DocumentsScreen |
| **💰 finances** | Invoice, Transaction, Account | Dashboard, Rapports, Comptes | ✅ `/api/finances/dashboard/`, `/api/finances/payments/` | **P2 - IMPORTANT** | FinancesScreen |
| **🎖️ grades** | Grade, GradeExam, Requirement | CRUD grades, examens | ✅ `/api/grades/` (alias `/api/v1/grades/`) | **P1 - ESSENTIEL** | GradesScreen, ExamScreen |
| **📋 task_management** | Board, Task, Column | Kanban, Tasks | ✅ ViewSets complets | **P3 - UTILE** | TasksScreen |
| **🛒 shop** | Product, Order, Cart | Catalogue, Checkout | ⚠️ Minimal `/api/shop/` | **P2 - IMPORTANT** | ShopScreen, CartScreen |
| **⚙️ permissions_manager** | Permission, Role | Gestion permissions | ❌ Pas d'API | **P4 - ADMIN** | AdminScreen |
| **👨‍👩‍👧‍👦 family_management** | Family, FamilyMember | Gestion familles | ❌ Pas d'API | **P3 - UTILE** | FamilyScreen |
| **💳 payment** | SubscriptionPlan, Payment | Abonnements génériques | ❌ Pas d'API | **P2 - IMPORTANT** | SubscriptionScreen |
| **👤 accounts** | OrganisateurNonMembre | Admin utilisateurs | ❌ Pas d'API | **P4 - ADMIN** | UsersAdminScreen |
| **🏢 multitenant** | Tenant, Domain | Multi-tenant (DÉSACTIVÉ) | ❌ Désactivé | **P5 - FUTUR** | — |

---

## 🚨 GAPS CRITIQUES IDENTIFIÉS

### **APIs critiques (État actualisé)**
```python
# Déjà disponibles côté backend :
✅ GET /api/v1/auth/profile/           # Profil utilisateur (api_auth)
✅ GET /api/grades/                    # Système de grades (alias: /api/v1/grades/)
✅ GET /api/finances/dashboard/        # Dashboard financier
✅ GET /api/finances/payments/         # Liste paiements (pagination + filtres)
✅ GET /api/organizations/             # Organisations
✅ GET /api/competitions/upcoming/     # Compétitions à venir
✅ ViewSets documents & task_management

# À compléter :
⚠️ GET /api/shop/products/             # Shop: API minimale existante, à étendre
❌ API REST abonnements (apps/payment)
❌ API REST family_management
```

### **Endpoints Existants (À utiliser)**
```python
✅ GET /api/v1/auth/profile/
✅ GET /api/grades/
✅ GET /api/finances/dashboard/
✅ GET /api/finances/payments/
✅ GET /api/organizations/
✅ GET /api/competitions/upcoming/
✅ ViewSets documents & task_management
```

---

## 🎯 PLAN D'IMPLÉMENTATION REVISÉ

### **Phase 0 - Correction API Critiques (1 semaine)**

#### **Backend - Endpoints (état)**
```python
# Déjà en place :
- api_auth.views.UserProfileView  -> GET /api/v1/auth/profile/
- apps.grades.api                 -> GET /api/grades/ (alias /api/v1/grades/)
- apps.finances.rest_api          -> GET /api/finances/dashboard/
- apps.finances.rest_api          -> GET /api/finances/payments/

# À planifier :
- Shop: enrichir /api/shop/ (catalogue + panier + commandes)
- apps/payment (abonnements): exposer API REST
- family_management: exposer API REST
```

#### **Mobile - Services (alignement)**
```typescript
// ProfileService: utilise déjà GET /api/v1/auth/profile/
// GradeService:   utilise déjà GET /api/grades/
// FinanceService: utilise déjà GET /api/finances/dashboard/ et /api/finances/payments/
```

### **Phase 1 - Apps Prioritaires (2 semaines)**

#### **P0 - CRITIQUE : Authentification + Profil**
- [x] ✅ Login/Auth (FAIT)
- [ ] ❌ UserProfile complet avec vraies données
- [ ] ❌ OrganizationProfile (RACH.HAAC)

#### **P1 - ESSENTIEL : Fonctionnalités Core**
```typescript
// Organizations (API existante)
const OrganizationScreen = () => {
  // Utiliser GET /api/organizations/dashboard/
  // Afficher : 4 practitioners, 1 competition, etc.
}

// Competitions (API existante) 
const CompetitionsScreen = () => {
  // Utiliser GET /api/competitions/upcoming/
  // Afficher compétitions à venir + inscriptions
}

// Grades (API à créer)
const GradesScreen = () => {
  // Nouveau : GET /api/grades/
  // Système de grades complet
}
```

### **Phase 2 - Apps Importantes (3 semaines)**

#### **P2 - IMPORTANT : Fonctionnalités Business**
```typescript
// Finances (API existante)
const FinancesScreen = () => {
  // GET /api/finances/dashboard/ + /api/finances/payments/
}

// Shop (API à créer)
const ShopScreen = () => {
  // Nouveau : GET /api/shop/products/
  // Catalogue + panier + commandes
}

// Payments (abonnements – API à créer)
const PaymentsScreen = () => {
  // À exposer: endpoints abonnements (apps/payment)
}
```

### **Phase 3 - Apps Utiles (2 semaines)**

#### **P3 - UTILE : Fonctionnalités Avancées**
```typescript
// Documents (API existante)
const DocumentsScreen = () => {
  // Utiliser ViewSets existants
  // Gestion documents + Google Drive
}

// Tasks (API existante)
const TasksScreen = () => {
  // Utiliser ViewSets existants  
  // Kanban + gestion tâches
}

// Family Management (API à créer)
const FamilyScreen = () => {
  // Nouveau : GET /api/family/
  // Gestion membres famille
}
```

---

## 📱 ARCHITECTURE MOBILE FINALE

### **Navigation Principale (Sidebar)**
```typescript
const mainNavigation = [
  // Dashboard
  { icon: '📊', title: 'Dashboard', route: 'Dashboard' },
  
  // Core Features (P1)
  { icon: '🏛️', title: 'Organizations', route: 'Organizations' },
  { icon: '🏆', title: 'Competitions', route: 'Competitions' },
  { icon: '🎖️', title: 'Grades', route: 'Grades' },
  
  // Business Features (P2)  
  { icon: '💰', title: 'Finances', route: 'Finances' },
  { icon: '🛒', title: 'Shop', route: 'Shop', badge: 'New' },
  { icon: '💳', title: 'Payments', route: 'Payments' },
  
  // Advanced Features (P3)
  { icon: '📄', title: 'Documents', route: 'Documents' },
  { icon: '📋', title: 'Tasks', route: 'Tasks' },
  { icon: '👨‍👩‍👧‍👦', title: 'Family', route: 'Family' },
  
  // Utils
  { icon: '📱', title: 'QR Scanner', route: 'QRScanner' },
  { icon: '⚙️', title: 'Settings', route: 'Settings' },
];
```

### **Dashboard Stats (Exactes du Backend)**
```typescript
interface DashboardStats {
  practitioners: 4;           // De organizations
  competitions: 1;           // De competitions  
  registrations: 1;          // De competitions
  judges: 0;                 // De competitions
  balance: '0€';             // De finances
  revenue: '0€';             // De finances
  orders: 0;                 // De shop
  tasks: 0;                  // De task_management
}
```

---

## 🚀 ACTION IMMÉDIATE

**Vu l'architecture complète, je recommande :**

### **🔧 Priorité #1 : Endpoints API Manquants**

**Créer immédiatement ces 3 endpoints critiques :**

1. **`GET /api/v1/auth/profile/`** → Profil utilisateur complet
2. **`GET /api/v1/grades/`** → Système de grades  
3. **`GET /api/v1/finances/dashboard/`** → Dashboard financier

### **📱 Priorité #2 : Mobile Dashboard**

**Remplacer l'interface mobile actuelle par :**
- Vraies données utilisateur (ClaudiuG)
- Statistiques exactes (4 practitioners, 1 competition)
- Navigation 12+ modules comme backend

### **🎨 Priorité #3 : Thème MartialComp**

**Couleurs rouge/noir + logo + branding cohérent**

## 🤔 Question Stratégique

**Avec cette vision complète, par quoi voulez-vous commencer ?**

**A)** Créer les 3 endpoints API manquants dans Django  
**B)** Refactorer complètement l'interface mobile  
**C)** Focus sur 1 module spécifique (Organizations par exemple)

**Cette architecture révèle l'ampleur du projet - mais c'est gérable étape par étape !** 🥋