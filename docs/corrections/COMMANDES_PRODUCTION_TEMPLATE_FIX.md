# 🚀 COMMANDES POUR CORRIGER LE TEMPLATE EN PRODUCTION

## 📋 Instructions
Copiez et collez ces commandes **directement sur votre serveur de production** pour résoudre l'erreur TemplateSyntaxError.

---

## 🔧 1. Connexion au serveur et navigation
```bash
# Connectez-vous à votre serveur de production via SSH ou Plesk
cd /opt/martialcomp/app
```

---

## 💾 2. Sauvegarde du template actuel
```bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
cp competitions/templates/competitions/welcome.html competitions/templates/competitions/welcome.html.backup_$TIMESTAMP
echo "✅ Sauvegarde créée: welcome.html.backup_$TIMESTAMP"
```

---

## 🎨 3. Création du template corrigé
```bash
cat > competitions/templates/competitions/welcome.html << 'EOF'
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MartialComp - Plateforme Arts Martiaux</title>
    <meta name="description" content="MartialComp est la solution complète pour organiser, gérer et participer aux compétitions d'arts martiaux.">
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: #f5f5f5; 
        }
        .container { 
            max-width: 1000px; 
            margin: 0 auto; 
            background: white; 
            padding: 40px; 
            border-radius: 10px; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
        }
        .header { 
            text-align: center; 
            margin-bottom: 40px; 
        }
        .logo { 
            font-size: 2.5rem; 
            font-weight: bold; 
            color: #c41e3a; 
            margin-bottom: 10px; 
        }
        .tagline { 
            font-size: 1.2rem; 
            color: #666; 
        }
        .auth-section { 
            text-align: center; 
            margin: 40px 0; 
            padding: 30px; 
            background: #f8f9fa; 
            border-radius: 8px; 
        }
        .btn { 
            display: inline-block; 
            padding: 12px 24px; 
            margin: 10px; 
            text-decoration: none; 
            border-radius: 5px; 
            font-weight: bold; 
            transition: all 0.3s ease; 
        }
        .btn-primary { 
            background: #c41e3a; 
            color: white; 
        }
        .btn-google { 
            background: #4285f4; 
            color: white; 
        }
        .btn-facebook { 
            background: #1877f2; 
            color: white; 
        }
        .btn:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 4px 8px rgba(0,0,0,0.2); 
        }
        .footer { 
            text-align: center; 
            margin-top: 40px; 
            padding-top: 20px; 
            border-top: 1px solid #eee; 
            color: #666; 
        }
        .success { 
            background: #d4edda; 
            color: #155724; 
            padding: 15px; 
            border-radius: 5px; 
            margin: 20px 0; 
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🥋 MartialComp</div>
            <div class="tagline">Plateforme de Gestion des Arts Martiaux</div>
        </div>
        
        <div class="success">
            <h3>✅ Authentification Sociale Opérationnelle !</h3>
            <p>L'authentification Google et Facebook est maintenant entièrement fonctionnelle.</p>
        </div>
        
        <div class="auth-section">
            <h3>🔐 Connexion Sécurisée</h3>
            <p>Connectez-vous avec votre méthode préférée :</p>
            
            <a href="/accounts/login/" class="btn btn-primary">Connexion Classique</a>
            <a href="/accounts/google/login/" class="btn btn-google">✅ Connexion Google</a>
            <a href="/accounts/facebook/login/" class="btn btn-facebook">✅ Connexion Facebook</a>
        </div>
        
        <div class="footer">
            <p>© 2025 MartialComp - Authentification sociale déployée avec succès</p>
            <p>
                <a href="/privacy/">Politique de confidentialité</a> | 
                <a href="/terms/">Conditions d'utilisation</a>
            </p>
        </div>
    </div>
</body>
</html>
EOF

echo "✅ Template corrigé créé"
```

---

## 🔄 4. Redémarrage de Django
```bash
# Arrêter Django
pkill -f "runserver 127.0.0.1:8000" 2>/dev/null || true
sleep 5

# Activer l'environnement virtuel
source venv/bin/activate

# Vérifier la configuration Django
python manage.py check

# Si pas d'erreur, redémarrer Django
nohup python manage.py runserver 127.0.0.1:8000 > /tmp/django_template_fix.log 2>&1 &

echo "✅ Django redémarré"
```

---

## 🧪 5. Test de vérification
```bash
# Attendre le démarrage
sleep 15

# Tester la page localement sur le serveur
curl -s -o /dev/null -w "Code de réponse Django: %{http_code}\n" "http://127.0.0.1:8000/"

# Vérifier les logs si besoin
tail -10 /tmp/django_template_fix.log
```

---

## 🌍 6. Test des URLs publiques
Testez ces URLs dans votre navigateur :

- ✅ **Page d'accueil** : https://martialcomp.com/
- ✅ **Page française** : https://martialcomp.com/fr/
- ✅ **Google OAuth** : https://martialcomp.com/accounts/google/login/
- ✅ **Facebook OAuth** : https://martialcomp.com/accounts/facebook/login/
- ✅ **Politique de confidentialité** : https://martialcomp.com/privacy/
- ✅ **Conditions d'utilisation** : https://martialcomp.com/terms/

---

## 📋 Résultat attendu
- ❌ **Avant** : `TemplateSyntaxError at /fr/`
- ✅ **Après** : Page d'accueil professionnelle avec authentification sociale fonctionnelle

---

## 🆘 En cas de problème
```bash
# Restaurer l'ancien template
cp competitions/templates/competitions/welcome.html.backup_$TIMESTAMP competitions/templates/competitions/welcome.html

# Redémarrer Django
pkill -f "runserver 127.0.0.1:8000" && sleep 5
source venv/bin/activate
nohup python manage.py runserver 127.0.0.1:8000 > /tmp/django_restore.log 2>&1 &
```

---

## 🎯 Prochaine étape après correction
Une fois cette correction appliquée, il faudra configurer les **URLs de callback** dans :
1. **Google Cloud Console** : `https://martialcomp.com/accounts/google/login/callback/`
2. **Facebook Developer Console** : `https://martialcomp.com/accounts/facebook/login/callback/`