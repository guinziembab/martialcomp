# 🚀 Déploiement Template Poule Professionnel - Production

## 📦 Package Prêt pour Production

Le package est disponible dans :
```
apps/competitions/Packages-CombatV3/Production-Poule-Template/
```

## 📋 Contenu du Package

```
Production-Poule-Template/
├── README.md                          # Documentation complète
├── DEPLOY.sh                          # Script de déploiement automatique
├── CHANGELOG.md                       # Historique des modifications
├── templates/
│   └── competitions/
│       └── combat/
│           ├── detail_poule.html     # Template amélioré
│           └── base.html              # Template de base
└── views/
    └── detail_poule_function.py      # Fonction améliorée à intégrer
```

## 🚀 Déploiement en Production

### Option 1 : Script Automatique (Recommandé)

```bash
# Se connecter au serveur de production
ssh martialcomp-production

# Aller dans le répertoire du projet
cd /mnt/c/martial_hub_django/martialcomp

# Exécuter le script de déploiement
bash apps/competitions/Packages-CombatV3/Production-Poule-Template/DEPLOY.sh
```

Le script va :
- ✅ Créer automatiquement des backups
- ✅ Copier les nouveaux fichiers
- ✅ Mettre à jour la fonction `detail_poule`
- ✅ Vérifier les permissions
- ✅ Vérifier la syntaxe Python

### Option 2 : Déploiement Manuel

#### Étape 1 : Sauvegarder les fichiers existants

```bash
cd /mnt/c/martial_hub_django/martialcomp

# Créer un répertoire de backup
mkdir -p backups/$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"

# Sauvegarder les fichiers
cp apps/competitions/templates/competitions/combat/detail_poule.html $BACKUP_DIR/
cp apps/competitions/templates/competitions/combat/base.html $BACKUP_DIR/
cp apps/competitions/views/combat.py $BACKUP_DIR/
```

#### Étape 2 : Copier les nouveaux fichiers

```bash
PACKAGE_DIR="apps/competitions/Packages-CombatV3/Production-Poule-Template"

# Copier les templates
cp $PACKAGE_DIR/templates/competitions/combat/detail_poule.html \
   apps/competitions/templates/competitions/combat/detail_poule.html

cp $PACKAGE_DIR/templates/competitions/combat/base.html \
   apps/competitions/templates/competitions/combat/base.html
```

#### Étape 3 : Mettre à jour la fonction detail_poule

Ouvrir `apps/competitions/views/combat.py` et remplacer la fonction `detail_poule` par celle du fichier :
`$PACKAGE_DIR/views/detail_poule_function.py`

#### Étape 4 : Vérifier les permissions

```bash
chmod 644 apps/competitions/templates/competitions/combat/detail_poule.html
chmod 644 apps/competitions/templates/competitions/combat/base.html
chmod 644 apps/competitions/views/combat.py
```

#### Étape 5 : Redémarrer le serveur

```bash
# Si Gunicorn
sudo systemctl restart gunicorn
# ou
sudo supervisorctl restart gunicorn

# Si uWSGI
sudo systemctl restart uwsgi
```

## ✅ Vérification Post-Déploiement

1. **Accéder à une page de poule** :
   ```
   https://votre-domaine.com/en/competitions/combat/poules/1/
   ```

2. **Vérifier** :
   - ✅ Header avec dégradé violet s'affiche
   - ✅ 4 cartes de statistiques visibles
   - ✅ Barre de progression affichée
   - ✅ Participants et combats visibles
   - ✅ Pas d'erreurs dans la console du navigateur

3. **Tester la responsivité** :
   - Réduire la fenêtre du navigateur
   - Vérifier que le layout s'adapte

4. **Vérifier les fonctionnalités** :
   - Cliquer sur les boutons d'action
   - Vérifier les liens vers les détails
   - Tester l'interface de combat

## 🔄 Rollback en Cas de Problème

Si vous devez restaurer les anciens fichiers :

```bash
# Trouver le dernier backup
BACKUP_DIR=$(ls -td backups/*/ | head -1)

# Restaurer les fichiers
cp $BACKUP_DIR/detail_poule.html \
   apps/competitions/templates/competitions/combat/detail_poule.html

cp $BACKUP_DIR/base.html \
   apps/competitions/templates/competitions/combat/base.html

cp $BACKUP_DIR/combat.py \
   apps/competitions/views/combat.py

# Redémarrer le serveur
sudo systemctl restart gunicorn
```

## 📝 Checklist de Déploiement

- [ ] Sauvegarder les fichiers existants
- [ ] Copier les nouveaux templates
- [ ] Mettre à jour la fonction `detail_poule`
- [ ] Vérifier les permissions (644)
- [ ] Vérifier la syntaxe Python
- [ ] Redémarrer le serveur web/WSGI
- [ ] Tester l'accès à une page de poule
- [ ] Vérifier les statistiques
- [ ] Tester la responsivité
- [ ] Vérifier les fonctionnalités
- [ ] Vérifier les logs pour les erreurs

## 🐛 Dépannage

### Erreur : Template not found
- Vérifier que les fichiers sont bien copiés
- Vérifier les permissions (644)
- Vérifier le chemin dans les settings Django

### Erreur : SyntaxError dans combat.py
- Vérifier que la fonction `detail_poule` est correctement intégrée
- Vérifier l'indentation Python
- Vérifier les imports nécessaires

### Les statistiques ne s'affichent pas
- Vérifier que la fonction `detail_poule` a été mise à jour
- Vérifier que les variables sont passées au template
- Vérifier les logs Django pour les erreurs

### Le design ne s'affiche pas correctement
- Vérifier que Bootstrap 5 est chargé
- Vérifier que Font Awesome est chargé
- Vérifier la console du navigateur pour les erreurs CSS

## 📞 Support

En cas de problème :
1. Vérifier les logs Django : `tail -f /var/log/django/error.log`
2. Vérifier les logs du serveur web
3. Vérifier les permissions des fichiers
4. Vérifier que les templates sont bien chargés

## 📅 Informations

- **Date de création** : 2024-11-17
- **Version** : 1.0.0
- **Auteur** : MartialComp Development Team
