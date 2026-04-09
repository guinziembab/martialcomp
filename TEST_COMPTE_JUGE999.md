# Test du compte Juge999 - Guide complet

## 🔐 Informations de connexion

- **Username** : `Juge999` (avec J majuscule)
- **Mot de passe** : `AQW123ok;`

## ✅ Configuration actuelle

Le compte Juge999 a maintenant :

1. **UserProfile** avec `role='judge'`
2. **Profil Practitioner** (créé automatiquement)
3. **Profil Judge** avec :
   - Niveau : Régional
   - Juge technique : ✅
   - Arbitre combat : ✅
   - Organisation : AkomanT Club

## 🚀 Test de connexion

### 1. Accès initial
1. Allez sur : `http://127.0.0.1:8888/fr/competitions/dashboard/`
2. Connectez-vous avec les identifiants ci-dessus
3. **Résultat attendu** : Redirection automatique vers le dashboard juge/arbitre

### 2. Dashboard Juge
Vous devriez voir :
- Interface spécifique aux juges/arbitres
- Accès aux compétitions assignées
- Outils de notation

### 3. Bascule vers le mode Pratiquant
Comme le Juge999 a aussi un profil Practitioner, il peut basculer :
- Cherchez le bouton "Mode Pratiquant" dans la sidebar
- Cliquez pour accéder au dashboard pratiquant

## 🔍 Diagnostic en cas de problème

### Si vous tombez encore sur le dashboard pratiquant

1. **Vérifiez la session** : Le système pourrait avoir mémorisé le mode pratiquant
   - Déconnectez-vous complètement
   - Effacez les cookies du navigateur pour localhost:8888
   - Reconnectez-vous

2. **Forcer le mode juge** :
   - Une fois connecté, allez directement sur : `http://127.0.0.1:8888/fr/competitions/dashboard/referee/`

3. **Vérifier le profil** :
   ```bash
   python3 check_juge111_profile.py
   ```

## 📊 Architecture du système

```
User (Juge999)
├── UserProfile (role='judge')
├── Practitioner (profil pratiquant)
└── Judge (profil juge)
    ├── Juge technique ✅
    └── Arbitre combat ✅
```

## 🎯 URLs importantes

- **Dashboard général** : `/competitions/dashboard/` (redirection automatique)
- **Dashboard juge direct** : `/competitions/dashboard/referee/`
- **Dashboard pratiquant** : `/competitions/dashboard/participant/`
- **Notation technique** : `/technical-scoring/judge/dashboard/`
- **Interface combat** : `/combat/dashboard/`

## 🔄 Système de bascule

Le système permet de basculer entre les modes :

1. **Mode Juge** → **Mode Pratiquant**
   - Bouton dans la sidebar du dashboard juge
   - URL : `/dashboard/switch-to-participant/`

2. **Mode Pratiquant** → **Mode Juge**
   - Bouton dans la sidebar du dashboard pratiquant
   - URL : `/dashboard/switch-to-judge/`

## 🛠️ En cas de problème persistant

1. **Vérifiez les logs** :
   ```bash
   tail -f /tmp/server.log | grep Juge999
   ```

2. **Testez la redirection manuelle** :
   ```bash
   curl -I -L http://127.0.0.1:8888/fr/competitions/dashboard/ \
     -H "Cookie: sessionid=VOTRE_SESSION_ID"
   ```

3. **Réinitialisez le profil** :
   ```bash
   python3 fix_juge999_profile.py
   ```

## ✨ Fonctionnalités disponibles pour le Juge999

### En mode Juge :
- Accès aux compétitions assignées
- Interface de notation technique
- Interface d'arbitrage combat
- Gestion des évaluations
- Historique des notations

### En mode Pratiquant :
- Inscription aux compétitions
- Suivi des résultats
- Gestion des paiements
- Accès aux documents

---

**Note** : Le système détecte automatiquement les multiples profils et permet une navigation fluide entre les différents rôles.