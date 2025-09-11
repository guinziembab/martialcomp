# 🚨 GUIDE DE RÉCUPÉRATION SSH - Connection Timeout

## 🔍 DIAGNOSTIC SITUATION CRITIQUE

**❌ Problème majeur identifié :**
- SSH connection timeout sur port 22 
- Serveur non accessible après reboot
- Aucune réponse sur 212.227.78.104:22

## 🎯 CAUSES POSSIBLES

### 1. **Service SSH non démarré**
Le service SSH ne s'est pas relancé automatiquement après reboot.

### 2. **Firewall/iptables activé**
Les règles de firewall bloquent le port 22.

### 3. **Configuration réseau corrompue**
L'interface réseau n'est pas configurée correctement.

### 4. **Serveur bloqué au boot**
Le serveur est resté sur un écran de boot/erreur.

### 5. **Problème hébergeur**
L'hébergeur a un problème technique.

## 🔧 SOLUTIONS PAR ORDRE DE PRIORITÉ

### Solution 1: Console d'Administration Hébergeur

**🎯 ACCÈS VIA PANEL HÉBERGEUR**

1. **Se connecter au panel de contrôle** de l'hébergeur
2. **Accéder à la console VNC/KVM** du serveur
3. **Vérifier l'état du serveur** (boot, erreurs)
4. **Redémarrer les services** si nécessaire

**Commandes à exécuter via console :**
```bash
# Vérifier si le système a démarré
systemctl status
systemctl status ssh
systemctl status nginx

# Redémarrer SSH si nécessaire
systemctl restart ssh
systemctl enable ssh

# Vérifier réseau
ip addr show
ping 8.8.8.8

# Vérifier firewall
iptables -L
ufw status
```

### Solution 2: Réinitialisation Réseau

**Via console hébergeur :**
```bash
# Redémarrer networking
systemctl restart networking
systemctl restart systemd-networkd

# Recharger configuration SSH
systemctl restart ssh

# Test local
ss -tlnp | grep :22
```

### Solution 3: Recovery Mode

**Si le serveur est bloqué au boot :**
1. **Redémarrer en mode recovery** via panel hébergeur
2. **Monter le système de fichiers** en lecture/écriture
3. **Corriger les configurations** problématiques
4. **Redémarrer normalement**

### Solution 4: Restauration de Sauvegarde

**En dernier recours :**
1. **Restaurer une sauvegarde** antérieure au reboot
2. **Récupérer la configuration** i18n depuis les backups
3. **Appliquer les corrections** manuellement

## 🌐 TESTS ALTERNATIFS

### Test Ping
```bash
ping 212.227.78.104
ping martialcomp.com
```

### Test Autres Ports
```bash
nmap -p 22,80,443 212.227.78.104
telnet 212.227.78.104 22
telnet 212.227.78.104 80
```

### Test DNS
```bash
nslookup martialcomp.com
dig martialcomp.com
```

## 📞 CONTACT HÉBERGEUR

**Si aucune solution ne fonctionne :**

1. **Contacter le support** de l'hébergeur immédiatement
2. **Signaler le problème** : "Serveur inaccessible après reboot"
3. **Demander accès console** VNC/KVM
4. **Demander vérification** infrastructure réseau

**Informations à fournir :**
- IP serveur : 212.227.78.104
- Domaine : martialcomp.com
- Problème : SSH timeout après reboot système
- Heure du reboot : 2025-06-24 21:01:43

## 🔧 RÉCUPÉRATION DJANGO POST-SSH

**Une fois SSH restauré :**

```bash
# Connexion et diagnostic
ssh root@212.227.78.104
cd /var/www/vhosts/martialcomp.com/httpdocs

# Vérifier logs post-reboot
cat /tmp/martialcomp_reboot.log
cat /tmp/django_post_reboot.log

# Démarrage manuel Django
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings
python3 manage.py check
python3 manage.py runserver 0.0.0.0:8000 &

# Test URLs i18n
curl -I http://localhost:8000/
curl -I http://localhost:8000/fr/
curl -I http://localhost:8000/en/
```

## 🎯 OBJECTIF FINAL

**Après récupération SSH :**
- ✅ Accès SSH restauré
- ✅ Django démarré manuellement  
- ✅ URLs i18n fonctionnelles
- ✅ Site MartialComp opérationnel

## ⏰ URGENCE

**🚨 PRIORITÉ MAXIMALE :**
1. **Accès console hébergeur** (solution la plus rapide)
2. **Contact support technique** si console indisponible
3. **Restauration service SSH** 
4. **Récupération Django** avec configuration i18n

La configuration i18n est sauvegardée et prête à être réactivée dès que l'accès SSH sera restauré.