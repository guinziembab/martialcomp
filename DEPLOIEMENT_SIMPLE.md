# 🚀 Guide de Déploiement Simple - Onglet Résultats

## 📦 Package prêt
- **Fichier** : `/tmp/update_resultats_v2_20251014_233135.tar.gz`
- **Taille** : 28K
- **Contenu** : Nouvel onglet Résultats pour la gestion des compétitions

## 🔧 Étapes de déploiement

### 1️⃣ Transférer le package
```bash
scp /tmp/update_resultats_v2_20251014_233135.tar.gz martialcomp@serveur-prod:/home/martialcomp/
```

### 2️⃣ Se connecter au serveur
```bash
ssh martialcomp@serveur-prod
```

### 3️⃣ Déployer automatiquement
```bash
cd /home/martialcomp
tar -xzf update_resultats_v2_20251014_233135.tar.gz
cd update_resultats_v2_20251014_233135
./deploy_on_server.sh
```

## ✅ Vérification rapide

1. Ouvrir : `https://martialcomp.com/fr/competitions/club/competitions/8/manage/`
2. Vérifier la présence de l'onglet **"Résultats"** 🏆
3. Cliquer sur l'onglet et vérifier les 4 sections

## 🆘 En cas de problème

### Restauration rapide
```bash
# Le script crée automatiquement une sauvegarde
# Regarder le message affiché pour le chemin exact
cp -r /home/martialcomp/backups/[DATE]/* /home/martialcomp/public_html/apps/competitions/
touch /home/martialcomp/public_html/passenger_wsgi.py
```

### Logs à vérifier
```bash
tail -f /var/log/apache2/error.log
```

## 📝 Résultat attendu

L'onglet Résultats doit afficher :
- 2 cartes d'accès (Dashboard Juges, Gestion Notation)
- Liste des catégories avec boutons d'action
- Graphique circulaire de l'état de notation
- Tableau de suivi temps réel

## ⚠️ Notes
- Certains boutons affichent "en développement" (normal)
- Le graphique nécessite une connexion internet (Chart.js CDN)
- L'auto-refresh fonctionne uniquement quand l'onglet est actif