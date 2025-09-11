# 🔌 Test de Connexion SSH - Serveur Ionos

## 📋 Informations de Connexion
- **IP Serveur** : 212.227.78.104
- **Utilisateur** : root
- **Mot de passe** : 68_02M@et@
- **OS** : Debian 11.11

## 🧪 Tests à Effectuer

### Test 1 : Connexion SSH Basique
```bash
# Depuis votre terminal local (Windows/Linux/Mac)
ssh root@212.227.78.104

# Si demandé, accepter la clé d'hôte : yes
# Entrer le mot de passe : 68_02M@et@
```

### Test 2 : Vérification Système
```bash
# Une fois connecté, exécuter ces commandes :

# Vérifier l'OS
cat /etc/os-release

# Vérifier l'espace disque
df -h

# Vérifier la mémoire
free -h

# Vérifier les services
systemctl status apache2
systemctl status postgresql
```

### Test 3 : Vérification Structure Ionos
```bash
# Vérifier la structure Plesk/Ionos
ls -la /var/www/vhosts/

# Vérifier le domaine martialcomp.com
ls -la /var/www/vhosts/martialcomp.com/

# Vérifier les permissions
whoami
id
```

### Test 4 : Vérification Python
```bash
# Vérifier Python
python3 --version
which python3

# Vérifier pip
pip3 --version

# Vérifier virtualenv
python3 -m venv --help
```

### Test 5 : Vérification Base de Données
```bash
# Vérifier PostgreSQL
sudo -u postgres psql -c "\l"

# Tester la connexion avec les identifiants MartialComp
psql -h localhost -U martialcomp_user -d martialcomp_db -c "\dt"
# Mot de passe : AQWZSX123ok,
```

## 📋 Checklist de Vérification

### Connexion SSH
- [ ] Connexion SSH réussie
- [ ] Accès root confirmé
- [ ] Terminal interactif fonctionnel

### Système
- [ ] OS Debian 11.11 confirmé
- [ ] Espace disque suffisant (>5GB libre)
- [ ] Mémoire RAM suffisante (>1GB libre)

### Services
- [ ] Apache2 actif
- [ ] PostgreSQL actif
- [ ] Plesk fonctionnel

### Structure Fichiers
- [ ] Répertoire /var/www/vhosts/ existe
- [ ] Dossier martialcomp.com présent
- [ ] Permissions correctes

### Outils Développement
- [ ] Python 3.9+ disponible
- [ ] pip3 installé
- [ ] virtualenv fonctionnel
- [ ] git installé

### Base de Données
- [ ] PostgreSQL accessible
- [ ] Base martialcomp_db existe
- [ ] Utilisateur martialcomp_user configuré

## 🚨 Problèmes Possibles

### Connexion SSH Refuse
```bash
# Vérifier que SSH est accessible depuis votre IP
# Tester avec telnet
telnet 212.227.78.104 22

# Si timeout, vérifier :
# 1. Firewall local
# 2. Restrictions IP chez Ionos
# 3. Service SSH actif sur le serveur
```

### Mot de Passe Incorrect
```bash
# Si le mot de passe ne fonctionne pas :
# 1. Vérifier les caractères spéciaux
# 2. Essayer de copier-coller le mot de passe
# 3. Contacter le support Ionos
```

### Permissions Insuffisantes
```bash
# Si accès limité :
# 1. Vérifier que vous êtes bien en root
# 2. Utiliser sudo si nécessaire
# 3. Vérifier les restrictions Plesk
```

## 📞 Support en Cas de Problème

### Support Ionos
- **Téléphone** : Support technique 24/7
- **Panel** : https://212.227.78.104:8443
- **Documentation** : Centre d'aide Ionos

### Commandes de Diagnostic
```bash
# Vérifier la connectivité réseau
ping google.com

# Vérifier les logs système
tail -f /var/log/auth.log

# Vérifier les processus
ps aux | grep ssh
```

## 🔄 Étapes Suivantes

### Si Connexion OK
1. Passer à la Phase 2 du `DEPLOYMENT_EXECUTION_GUIDE.md`
2. Créer l'environnement virtuel Python
3. Configurer la base de données

### Si Connexion KO
1. Vérifier les informations de connexion
2. Contacter le support Ionos
3. Vérifier les restrictions firewall

---

**⚠️ IMPORTANT** : Gardez les identifiants de connexion en sécurité et ne les partagez jamais.

**💡 CONSEIL** : Une fois connecté, créer un utilisateur non-root pour plus de sécurité.