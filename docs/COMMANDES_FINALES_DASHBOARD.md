# Commandes finales pour corriger le dashboard

## 🎯 Objectif
Corriger le routage dashboard pour utiliser **UNIQUEMENT les templates existants**.
**AUCUN nouveau template ne sera créé** - respecte la directive utilisateur.

## 📋 Commandes à exécuter

### 1. Transférer le script final
```bash
scp final_dashboard_fix.py root@martialcomp.com:/tmp/
```

### 2. Se connecter au serveur
```bash
ssh root@martialcomp.com
```

### 3. Exécuter la correction finale
```bash
cd /var/www/vhosts/martialcomp.com/httpdocs
python3 /tmp/final_dashboard_fix.py
```

## 🧪 Test après correction

### 4. Tester le site
1. Aller sur: https://martialcomp.com/
2. Cliquer sur "Rejoindre la phase de test"
3. Se connecter avec: `dojo_sakura_manager` / `demo2025`
4. Vérifier que le **dashboard club existant** s'affiche

## ✅ Résultat attendu

- **Utilisateur demo**: `dojo_sakura_manager` → `/dashboard/club/`
- **Template utilisé**: `competitions/dashboard/club.html` (EXISTANT)
- **Nouveaux templates**: AUCUN (respecte directive utilisateur)

## 🔧 Ce que fait le script

1. ✅ Vérifie les templates dashboard existants
2. ✅ Crée un router minimal utilisant UNIQUEMENT templates existants  
3. ✅ Corrige competitions/urls.py
4. ✅ Corrige les redirections dans settings.py
5. ✅ Redémarre le serveur
6. ✅ Teste le routage avec le compte demo

## 📊 Conformité à la directive

> "Pourquoi créer les templates alors qu'ils existent et fonctionnent, il faut pointer vers les dashboards existants et pas créer de nouveau"

✅ **RESPECTÉ**: Le script utilise exclusivement les templates existants dans `competitions/templates/competitions/dashboard/`