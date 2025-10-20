# 🚀 Patch Onboarding MartialComp - Production

## 📋 Description

Ce patch corrige l'erreur 500 lors de l'onboarding en ajoutant :
- ✅ Gestion d'erreurs robuste sur toutes les vues
- ✅ Création automatique du profil utilisateur si manquant
- ✅ Fallback sur disciplines par défaut
- ✅ Page d'erreur gracieuse
- ✅ Correction de la redirection vers le dashboard fédération

## 📁 Contenu du patch

```
apps/competitions/
├── management/commands/
│   └── init_disciplines.py          # Commande pour initialiser les disciplines
├── views/onboarding/
│   └── emergency_views.py           # Vues sécurisées avec gestion d'erreurs
├── templates/competitions/onboarding/
│   └── error.html                   # Page d'erreur user-friendly
└── urls/
    └── onboarding.py                # URLs modifiées avec routes sécurisées

scripts/
└── init_disciplines_direct.py       # Script direct d'initialisation (backup)
```

## 🔧 Installation

1. **Transférer le package sur le serveur**
```bash
scp -r onboarding_patch_production_* user@martialcomp-production:/home/martialc/
```

2. **Se connecter au serveur**
```bash
ssh user@martialcomp-production
```

3. **Extraire et exécuter**
```bash
cd /home/martialc
tar -xzf onboarding_patch_production_*.tar.gz
cd onboarding_patch_production_*
sudo ./deploy_patch.sh
```

## ✅ Corrections appliquées

### 1. Vue safe_club_creation()
- Try/except sur toute la logique
- Création automatique du UserProfile si manquant
- Gestion des disciplines manquantes

### 2. Vue safe_federation_creation()
- Correction de la redirection: `'dashboard:federation'` → `'competitions:dashboard:federations'`
- Gestion robuste des erreurs
- Logs détaillés pour debugging

### 3. URLs activées
- `/competitions/onboarding/club/creation/` → Vue sécurisée
- `/competitions/onboarding/federation/` → Vue sécurisée
- `/competitions/onboarding/error/` → Page d'erreur
- `/competitions/onboarding/complete/` → Finalisation

## 🔍 Vérification post-déploiement

1. **Tester la création de club**
   - https://app.martialcomp.com/competitions/onboarding/club/creation/
   
2. **Tester la création de fédération**
   - https://app.martialcomp.com/competitions/onboarding/federation/
   
3. **Vérifier les disciplines**
   ```bash
   python manage.py shell
   from apps.competitions.models import Discipline
   print(f"Disciplines actives: {Discipline.objects.filter(is_active=True).count()}")
   ```

## 🔄 Rollback si nécessaire

Les backups sont créés automatiquement dans `/home/martialc/backups/onboarding_*`

Pour restaurer :
```bash
cp /home/martialc/backups/onboarding_*/emergency_views.py /home/martialc/martialcomp/apps/competitions/views/onboarding/
cp /home/martialc/backups/onboarding_*/onboarding.py /home/martialc/martialcomp/apps/competitions/urls/
touch /home/martialc/martialcomp/tmp/restart.txt
```

## 📞 Support

En cas de problème :
- Logs Django : `/var/log/martialcomp/django.log`
- Logs Passenger : `/var/log/passenger/passenger.log`
- Contact : support@martialcomp.com
