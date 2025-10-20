# 🔗 Liens de Test - Onboarding MartialComp

## 🚀 Pour démarrer le serveur

```bash
python3 manage.py runserver 0.0.0.0:8888
```

## 📍 URLs de test (remplacez le port si nécessaire)

### 1. **Page d'accueil Onboarding**
   - http://localhost:8888/competitions/onboarding/
   - Point d'entrée principal du processus

### 2. **Création de Club** (Vue sécurisée avec patch)
   - http://localhost:8888/competitions/onboarding/club/creation/
   - Formulaire de création de club avec gestion d'erreurs robuste

### 3. **Création de Fédération** (Vue sécurisée avec patch)
   - http://localhost:8888/competitions/onboarding/federation/
   - Formulaire de création de fédération avec gestion d'erreurs robuste

### 4. **Page d'erreur gracieuse**
   - http://localhost:8888/competitions/onboarding/error/
   - Page affichée en cas de problème technique

### 5. **Page de finalisation**
   - http://localhost:8888/competitions/onboarding/complete/
   - Confirmation de fin d'onboarding

### 6. **Sélection du rôle**
   - http://localhost:8888/competitions/onboarding/role/
   - Choix entre : Club, Fédération, Juge, Participant

## 🧪 Scénarios de test

### Test 1 : Création de Club
1. Aller sur http://localhost:8888/competitions/onboarding/role/
2. Sélectionner "Club"
3. Remplir le formulaire de création
4. Vérifier la redirection vers la finalisation

### Test 2 : Création de Fédération
1. Aller sur http://localhost:8888/competitions/onboarding/role/
2. Sélectionner "Fédération"
3. Remplir le formulaire
4. Vérifier la création et redirection

### Test 3 : Gestion d'erreur
1. Aller directement sur http://localhost:8888/competitions/onboarding/error/
2. Vérifier l'affichage de la page d'erreur
3. Tester les boutons d'action

## 📝 Notes importantes

- **Authentification requise** : Vous devez être connecté pour accéder à ces pages
- **Page de connexion** : http://localhost:8888/accounts/login/
- **Créer un compte test** : http://localhost:8888/accounts/signup/

## 🔍 Vérifications après test

1. Les disciplines s'affichent correctement dans les formulaires
2. Pas d'erreur 500 lors de la soumission
3. Les redirections fonctionnent
4. Les messages de succès/erreur s'affichent

## 🛠️ En cas de problème

Si le serveur ne démarre pas à cause de channels :
```bash
# Installer channels temporairement
pip install channels

# Ou utiliser un environnement virtuel
python3 -m venv venv_test
source venv_test/bin/activate
pip install -r requirements.txt
python manage.py runserver 8888
```