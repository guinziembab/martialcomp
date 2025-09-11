# CORRECTION ONBOARDING - DÉPLOIEMENT PRODUCTION

## Problème identifié
Le processus signup/onboarding ne fonctionne pas car les URLs de redirection utilisent des namespaces incorrects.

## Solution
Modifier le fichier `competitions/views/auth.py` pour corriger les URLs d'onboarding.

## COMMANDES DE DÉPLOIEMENT

### Méthode 1: Correction directe sur le serveur

```bash
# 1. Se connecter au serveur de production
cd /var/www/vhosts/martialcomp.com/httpdocs

# 2. Faire une sauvegarde du fichier actuel
cp competitions/views/auth.py competitions/views/auth.py.backup_$(date +%s)

# 3. Éditer le fichier avec nano
nano competitions/views/auth.py

# 4. Localiser les lignes 100-108 et remplacer:

# ANCIEN CODE (lignes 100-108):
                try:
                    return redirect('competitions:onboarding:start')  # Utiliser le namespace complet
                except Resolver404:
                    # Fallback si la première URL n'est pas trouvée
                    try:
                        return redirect('onboarding:start')
                    except Resolver404:
                        # Second fallback
                        return redirect('competitions:onboarding:role_selection')

# NOUVEAU CODE (lignes 100-116):
                try:
                    return redirect('onboarding:start')  # Utiliser le namespace correct
                except Resolver404 as e:
                    # Log l'erreur et essayer le fallback
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"URL onboarding:start non trouvée: {str(e)}")
                    
                    try:
                        return redirect('onboarding:role_selection')
                    except Resolver404 as e2:
                        # Log l'erreur du fallback
                        logger.error(f"URL onboarding:role_selection non trouvée: {str(e2)}")
                        
                        # Second fallback vers le dashboard
                        messages.warning(request, _("Veuillez compléter votre profil."))
                        return redirect('dashboard:index')

# 5. Sauvegarder et quitter (Ctrl+X, Y, Enter)

# 6. Redémarrer Gunicorn
pkill -f gunicorn
source venv/bin/activate
nohup gunicorn --bind 127.0.0.1:8000 --workers 3 --timeout 120 --max-requests 1000 --max-requests-jitter 100 --preload --chdir /var/www/vhosts/martialcomp.com/httpdocs config.wsgi:application > gunicorn.log 2>&1 &

# 7. Vérifier que le processus fonctionne
ps aux | grep gunicorn
```

### Méthode 2: Remplacement complet du fichier

```bash
# 1. Se connecter au serveur de production
cd /var/www/vhosts/martialcomp.com/httpdocs

# 2. Faire une sauvegarde
cp competitions/views/auth.py competitions/views/auth.py.backup_$(date +%s)

# 3. Créer le fichier corrigé
cat > competitions/views/auth.py << 'EOF'
[Contenu du fichier auth_py_corrected.py]
EOF

# 4. Vérifier les permissions
chmod 644 competitions/views/auth.py

# 5. Redémarrer Gunicorn
pkill -f gunicorn
source venv/bin/activate
nohup gunicorn --bind 127.0.0.1:8000 --workers 3 --timeout 120 --max-requests 1000 --max-requests-jitter 100 --preload --chdir /var/www/vhosts/martialcomp.com/httpdocs config.wsgi:application > gunicorn.log 2>&1 &
```

### Méthode 3: Script de transfert via SCP (si accès local)

```bash
# Sur la machine locale
scp auth_py_corrected.py user@martialcomp.com:/var/www/vhosts/martialcomp.com/httpdocs/competitions/views/auth.py

# Puis sur le serveur
ssh user@martialcomp.com
cd /var/www/vhosts/martialcomp.com/httpdocs
chmod 644 competitions/views/auth.py
pkill -f gunicorn
source venv/bin/activate
nohup gunicorn --bind 127.0.0.1:8000 --workers 3 --timeout 120 --max-requests 1000 --max-requests-jitter 100 --preload --chdir /var/www/vhosts/martialcomp.com/httpdocs config.wsgi:application > gunicorn.log 2>&1 &
```

## VÉRIFICATION

Après avoir appliqué la correction:

```bash
# Vérifier que Gunicorn fonctionne
ps aux | grep gunicorn
curl -I http://127.0.0.1:8000/

# Vérifier les logs
tail -f gunicorn.log

# Tester le site
curl -I https://martialcomp.com/signup/
```

## RÉSULTAT ATTENDU

✅ L'inscription d'un utilisateur se déroule normalement
✅ Après l'inscription, l'utilisateur est redirigé vers l'onboarding  
✅ Le message "Une erreur inattendue est survenue" ne s'affiche plus
✅ Le processus d'onboarding se lance correctement pour déterminer le rôle

## TEST FINAL

🌐 **URL de test**: https://martialcomp.com/signup/

1. Créer un nouveau compte
2. Vérifier que la redirection vers l'onboarding fonctionne
3. Confirmer que l'utilisateur peut sélectionner son rôle

**La correction devrait résoudre définitivement le problème d'onboarding !**