# 🌍 Package de Traductions MartialComp - Production

## 📦 Contenu du Package

Ce package contient les traductions complètes pour 10 langues :

| Langue | Code | Messages | Statut |
|--------|------|----------|--------|
| Français | fr | 13,454 | ✅ 100% |
| Anglais | en | 13,454 | ✅ 100% |
| Espagnol | es | 13,454 | ✅ 100% |
| Italien | it | 13,454 | ✅ 100% |
| Allemand | de | 13,454 | ✅ 100% |
| Japonais | ja | 13,452 | ⚠️ 99.98% |
| Chinois | zh | 13,453 | ⚠️ 99.99% |
| Arabe | ar | 13,454 | ✅ 100% |
| Swahili | sw | 13,454 | ✅ 100% |
| Portugais | pt | 13,454 | ✅ 100% |

**Total**: 134,540+ messages traduits

## 🚀 Installation sur le Serveur de Production

### Méthode 1 : Script Automatique (Recommandé)

```bash
# 1. Transférer le package vers le serveur
scp -r translations_production_XXXXXXXX_XXXXXX root@vigilant-swartz:/tmp/

# 2. Se connecter au serveur
ssh root@vigilant-swartz

# 3. Exécuter le script d'installation
cd /tmp/translations_production_XXXXXXXX_XXXXXX
chmod +x INSTALL.sh
./INSTALL.sh
```

Le script va :
- ✅ Sauvegarder les traductions actuelles
- ✅ Installer les nouvelles traductions
- ✅ Appliquer les permissions correctes
- ✅ Redémarrer le service
- ✅ Afficher les statistiques

### Méthode 2 : Installation Manuelle

```bash
# 1. Backup des traductions actuelles
cd /var/www/vhosts/martialcomp.com/httpdocs
tar -czf locale_backup_$(date +%Y%m%d_%H%M%S).tar.gz locale/

# 2. Copier les nouvelles traductions
for lang in fr en es it de ja zh ar sw pt; do
    cp -f /tmp/translations_production_*/locale/$lang/LC_MESSAGES/django.* \
          locale/$lang/LC_MESSAGES/
done

# 3. Permissions
chown -R martialco:psacln locale/
find locale/ -type f -exec chmod 644 {} \;
find locale/ -type d -exec chmod 755 {} \;

# 4. Redémarrer le service
systemctl restart martialcomp.service

# 5. Vérifier
systemctl status martialcomp.service
```

## ✅ Vérification Post-Installation

### 1. Vérifier le service
```bash
systemctl status martialcomp.service
journalctl -u martialcomp.service -n 50
```

### 2. Tester le changement de langue
Accédez à : https://martialcomp.com/fr/
Changez la langue dans le sélecteur et vérifiez que tout est traduit.

### 3. Vérifier les statistiques
```bash
cd /var/www/vhosts/martialcomp.com/httpdocs
for lang in fr en es it de ja zh ar sw pt; do
    echo "=== $lang ==="
    msgfmt --statistics locale/$lang/LC_MESSAGES/django.po 2>&1
done
```

## 📋 Notes Importantes

- **Backup automatique** : Le script crée automatiquement un backup avant l'installation
- **Temps d'arrêt** : ~2-3 secondes pendant le redémarrage du service
- **Rollback** : En cas de problème, restaurez depuis locale_backup_*
- **Permissions** : Le script applique automatiquement les bonnes permissions

## ⚠️ Problèmes Connus (Mineurs)

- **Japonais** : 2 messages manquants (99.98% complet)
- **Chinois** : 1 message manquant (99.99% complet)
- **Espagnol** : Quelques erreurs de format (non bloquantes)

Ces problèmes n'affectent pas le fonctionnement du site.

## 📞 Support

En cas de problème :
1. Vérifier les logs : `journalctl -u martialcomp.service -f`
2. Restaurer le backup : `cp -r locale_backup_*/locale /var/www/vhosts/martialcomp.com/httpdocs/`
3. Redémarrer : `systemctl restart martialcomp.service`

---

**Date de création** : $(date +%Y-%m-%d)
**Version** : 1.0
