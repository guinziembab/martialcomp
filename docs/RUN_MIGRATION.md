# 🚀 Lancer la Migration Production

## 📋 Commande à exécuter

```bash
./migrate_production_complete.sh
```

## 🔑 Informations SSH requises

Le script vous demandera :

### 1. Adresse du serveur
```
Adresse du serveur (ex: user@server.com): 
```
**Exemples de réponses :**
- `root@votre-serveur.com`
- `ubuntu@192.168.1.100`
- `martialcomp@production.example.com`

### 2. Chemin du projet
```
Chemin du projet sur le serveur (ex: /home/user/martialcomp):
```
**Exemples de réponses :**
- `/home/ubuntu/martialcomp`
- `/var/www/martialcomp`
- `/opt/martialcomp`
- `/root/projets/martialcomp`

## 🔧 Configuration SSH préalable

### Si vous n'avez pas encore configuré SSH :

#### Option 1 : Avec mot de passe
```bash
ssh-copy-id user@votre-serveur.com
```

#### Option 2 : Avec clé privée
```bash
ssh -i /chemin/vers/votre/cle.pem user@serveur.com
```

#### Option 3 : Test de connexion
```bash
ssh user@votre-serveur.com "echo 'Test connexion réussi'"
```

## 📊 Ce qui sera récupéré

Le script va rapatrier **TOUT** :

### 🗂️ Configuration & Code
- ✅ Settings Django complets
- ✅ URLs complètes  
- ✅ Tous les modèles
- ✅ Toutes les vues
- ✅ Tous les formulaires
- ✅ Tous les templates
- ✅ Toutes les migrations
- ✅ Signaux et Apps

### 🗄️ Données
- ✅ Base de données complète
- ✅ Utilisateurs de production
- ✅ Fédérations réelles
- ✅ Clubs réels
- ✅ Toutes les données métier

### 📦 Environnement
- ✅ Requirements Python
- ✅ Configuration serveur
- ✅ État des migrations
- ✅ Versions installées

## ⏱️ Temps estimé

- **Connexion SSH** : 5-10 secondes
- **Récupération code** : 1-2 minutes
- **Récupération données** : 2-5 minutes (selon la taille)
- **Total** : 5-10 minutes

## 📋 Après récupération

Le script créera automatiquement :

1. **Dossier de migration** : `production_complete_YYYYMMDD_HHMMSS/`
2. **Script d'application** : `apply_complete_production.sh`
3. **Résumé détaillé** : `MIGRATION_SUMMARY_*.md`

## 🚀 Application automatique

Après récupération :

```bash
cd production_complete_YYYYMMDD_HHMMSS/
./apply_complete_production.sh
```

## 🛡️ Sécurité

- ✅ **Sauvegarde locale créée** avant toute modification
- ✅ **Script de restauration** disponible
- ✅ **Aucune modification** sur le serveur de production
- ✅ **Nettoyage automatique** des fichiers temporaires

## 🔙 Restauration

En cas de problème :

```bash
./restore_dev_backup.sh
```

## 📞 Support

Si problème de connexion SSH :

1. **Tester la connexion** :
   ```bash
   ssh user@serveur.com "pwd"
   ```

2. **Vérifier le chemin du projet** :
   ```bash
   ssh user@serveur.com "ls -la /chemin/vers/projet"
   ```

3. **Vérifier manage.py** :
   ```bash
   ssh user@serveur.com "ls -la /chemin/vers/projet/manage.py"
   ```

---

## ▶️ DÉMARRER MAINTENANT

```bash
./migrate_production_complete.sh
```

Puis suivez les instructions à l'écran !