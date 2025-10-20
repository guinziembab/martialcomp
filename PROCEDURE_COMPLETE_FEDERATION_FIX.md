# 🚀 Procédure Complète - Correction Disciplines Fédération

## 📋 Résumé du Problème
Les cases à cocher des disciplines ne s'affichent pas lors de la création d'une fédération car le champ `disciplines` n'est pas inclus dans `Meta.fields` du formulaire `FederationCreationForm`.

## 🔧 Étapes de Correction

### 1️⃣ Préparation des Fichiers

#### A. Créer l'archive de correction
```bash
# Depuis votre machine locale (WSL)
cd /mnt/c/martial_hub_django/martialcomp

# Créer un dossier pour le package
mkdir -p federation_disciplines_fix
cp diagnose_federation_disciplines_issue.sh federation_disciplines_fix/
cp fix_federation_disciplines_production_final.sh federation_disciplines_fix/

# Créer l'archive
tar -czf federation_disciplines_fix.tar.gz federation_disciplines_fix/
```

### 2️⃣ Transfert vers le Serveur de Production

#### A. Transfert par SCP
```bash
# Transférer l'archive
scp federation_disciplines_fix.tar.gz martialcomp-production:/home/martialc/

# OU si vous avez des problèmes avec le transfert, copiez directement le script
scp fix_federation_disciplines_production_final.sh martialcomp-production:/home/martialc/
```

### 3️⃣ Connexion au Serveur de Production

```bash
# Se connecter au serveur
ssh martialcomp-production
```

### 4️⃣ Exécution du Diagnostic (Optionnel mais Recommandé)

```bash
# Une fois connecté au serveur
cd /home/martialc

# Si vous avez transféré l'archive
tar -xzf federation_disciplines_fix.tar.gz
cd federation_disciplines_fix

# Rendre les scripts exécutables
chmod +x *.sh

# Exécuter le diagnostic pour voir l'état actuel
./diagnose_federation_disciplines_issue.sh > diagnostic_avant.log 2>&1

# Voir le résultat
cat diagnostic_avant.log
```

### 5️⃣ Exécution de la Correction

```bash
# Se positionner dans le bon répertoire
cd /home/martialc

# Si le script n'est pas encore là, le créer directement
cat > fix_federation_disciplines_production_final.sh << 'EOF'
[COLLER ICI LE CONTENU DU SCRIPT fix_federation_disciplines_production_final.sh]
EOF

# Rendre le script exécutable
chmod +x fix_federation_disciplines_production_final.sh

# IMPORTANT: Exécuter avec sudo pour les redémarrages de services
sudo ./fix_federation_disciplines_production_final.sh
```

### 6️⃣ Vérification Post-Correction

#### A. Vérifier les logs de correction
```bash
# Le script affiche un résumé à la fin
# Vérifier que tout est ✅

# Optionnel: Relancer le diagnostic
./diagnose_federation_disciplines_issue.sh > diagnostic_apres.log 2>&1
diff diagnostic_avant.log diagnostic_apres.log
```

#### B. Test Manuel Rapide
```bash
# Vérifier que le champ disciplines est maintenant dans Meta.fields
cd /home/martialc/martialcomp
grep -A 5 "class Meta:" apps/competitions/forms/onboarding.py | grep -A 3 "model = Federation" | grep "fields ="
# Devrait montrer 'disciplines' dans la liste
```

### 7️⃣ Test en Production

1. Ouvrir le navigateur
2. Aller sur https://app.martialcomp.com
3. Se connecter avec un compte test ou créer un nouveau compte
4. Aller sur https://app.martialcomp.com/competitions/onboarding/
5. Choisir "Administrateur de fédération"
6. Sur la page de création de fédération, vérifier que :
   - Les cases à cocher des disciplines s'affichent ✅
   - Vous pouvez en sélectionner plusieurs ✅
   - Le formulaire se soumet correctement ✅

### 8️⃣ En Cas de Problème

#### A. Consulter les logs
```bash
# Logs Django
tail -f /var/log/django/martialcomp.log

# Logs Apache
tail -f /var/log/apache2/error.log

# Logs du script (si disponibles)
ls -la /home/martialc/backups/federation_disciplines_*/
```

#### B. Restaurer depuis le backup
```bash
# Le script crée automatiquement un backup
# Trouver le dernier backup
BACKUP_DIR=$(ls -td /home/martialc/backups/federation_disciplines_* | head -1)
echo "Backup trouvé: $BACKUP_DIR"

# Restaurer si nécessaire
cd /home/martialc/martialcomp
cp $BACKUP_DIR/onboarding.py.backup apps/competitions/forms/onboarding.py
cp $BACKUP_DIR/federation_creation.html.backup apps/competitions/templates/competitions/onboarding/federation_creation.html
cp $BACKUP_DIR/federations.py.backup apps/competitions/views/onboarding/federations.py

# Redémarrer
sudo touch tmp/restart.txt
sudo systemctl restart gunicorn
sudo systemctl reload apache2
```

## 📝 Script Tout-en-Un (Alternative)

Si vous préférez tout faire en une seule commande depuis votre machine locale :

```bash
# Créer un script local qui fait tout
cat > deploy_federation_fix.sh << 'EOF'
#!/bin/bash
echo "🚀 Déploiement de la correction disciplines fédération..."

# Transférer le script
scp fix_federation_disciplines_production_final.sh martialcomp-production:/home/martialc/

# Exécuter sur le serveur
ssh martialcomp-production << 'REMOTE'
cd /home/martialc
chmod +x fix_federation_disciplines_production_final.sh
sudo ./fix_federation_disciplines_production_final.sh
REMOTE

echo "✅ Déploiement terminé!"
echo "🎯 Testez maintenant sur https://app.martialcomp.com/competitions/onboarding/federation/"
EOF

chmod +x deploy_federation_fix.sh
./deploy_federation_fix.sh
```

## ✅ Checklist Finale

- [ ] Script transféré sur le serveur
- [ ] Script exécuté avec sudo
- [ ] Pas d'erreur dans l'exécution
- [ ] 'disciplines' ajouté dans Meta.fields
- [ ] Services redémarrés
- [ ] Cases à cocher visibles sur la page
- [ ] Création de fédération fonctionne
- [ ] Disciplines sauvegardées correctement

## 🎯 Résultat Attendu

Après cette correction, lors de la création d'une fédération :
1. Les cases à cocher des disciplines s'affichent correctement
2. L'utilisateur peut sélectionner plusieurs disciplines
3. Les disciplines sont sauvegardées avec la fédération
4. L'utilisateur est redirigé vers le dashboard fédération

## 📞 Support

Si le problème persiste après cette correction :
1. Vérifier les logs : `tail -100 /var/log/django/martialcomp.log | grep -i "federation\|discipline"`
2. Envoyer le diagnostic : `./diagnose_federation_disciplines_issue.sh > diagnostic.log`
3. Contacter avec les détails du problème et le fichier diagnostic.log