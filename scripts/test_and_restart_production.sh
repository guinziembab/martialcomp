#!/bin/bash

# test_and_restart_production.sh
# Script intelligent pour redémarrer Apache, tester la plateforme Django, et guider l'exploitation

set -e

LOGFILE="/var/www/vhosts/martialcomp.com/logs/error.log"
SITE_URL="http://martialcomp.com/debug-host/"

step() {
    echo -e "\n\033[1;34m[ETAPE]\033[0m $1"
}

error() {
    echo -e "\033[1;31m[ERREUR]\033[0m $1"
}

success() {
    echo -e "\033[1;32m[SUCCES]\033[0m $1"
}

step "Redémarrage d'Apache..."
if sudo systemctl restart apache2 2>/tmp/apache_restart_err; then
    success "Apache redémarré avec succès."
else
    error "Echec du redémarrage Apache :"
    cat /tmp/apache_restart_err
    exit 1
fi

step "Vérification de l'accessibilité de la plateforme ($SITE_URL) ..."
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$SITE_URL" || true)
CODE=$(echo "$RESPONSE" | grep HTTP_CODE | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE:/d')

if [[ "$CODE" == "200" ]]; then
    success "La route /debug-host/ est accessible."
    echo -e "\nRéponse :\n$BODY"
else
    error "La route /debug-host/ n'est pas accessible (code HTTP $CODE)."
    echo -e "\nRéponse brute :\n$RESPONSE"
    step "Affichage des 20 dernières lignes du log Apache :"
    sudo tail -n 20 "$LOGFILE"
    exit 2
fi

step "Fin du test. Plateforme opérationnelle."

# Génération du guide d'exploitation
cat <<'EOF' > GUIDE_EXPLOITATION_MARTIALCOMP.md
# Guide d'exploitation rapide - Plateforme martialcomp.com

## 1. Redémarrer Apache

```bash
sudo systemctl restart apache2
```

## 2. Vérifier l'état de la plateforme

- Accéder à : http://martialcomp.com/debug-host/
- Si la page affiche les infos Django, la plateforme fonctionne.

## 3. Surveiller les logs Apache

```bash
sudo tail -f /var/www/vhosts/martialcomp.com/logs/error.log
```

## 4. En cas d'erreur 503 ou 500

- Vérifier la configuration Passenger dans /var/www/vhosts/system/martialcomp.com/conf/vhost.conf
- Vérifier le fichier passenger_wsgi.py à la racine du projet
- Redémarrer Apache
- Consulter les logs pour plus de détails

## 5. Commande de test automatique

```bash
sudo bash /var/www/vhosts/martialcomp.com/httpdocs/test_and_restart_production.sh
```

EOF

success "Guide d'exploitation généré : GUIDE_EXPLOITATION_MARTIALCOMP.md" 

# test_and_restart_production.sh
# Script intelligent pour redémarrer Apache, tester la plateforme Django, et guider l'exploitation

set -e

LOGFILE="/var/www/vhosts/martialcomp.com/logs/error.log"
SITE_URL="http://martialcomp.com/debug-host/"

step() {
    echo -e "\n\033[1;34m[ETAPE]\033[0m $1"
}

error() {
    echo -e "\033[1;31m[ERREUR]\033[0m $1"
}

success() {
    echo -e "\033[1;32m[SUCCES]\033[0m $1"
}

step "Redémarrage d'Apache..."
if sudo systemctl restart apache2 2>/tmp/apache_restart_err; then
    success "Apache redémarré avec succès."
else
    error "Echec du redémarrage Apache :"
    cat /tmp/apache_restart_err
    exit 1
fi

step "Vérification de l'accessibilité de la plateforme ($SITE_URL) ..."
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$SITE_URL" || true)
CODE=$(echo "$RESPONSE" | grep HTTP_CODE | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE:/d')

if [[ "$CODE" == "200" ]]; then
    success "La route /debug-host/ est accessible."
    echo -e "\nRéponse :\n$BODY"
else
    error "La route /debug-host/ n'est pas accessible (code HTTP $CODE)."
    echo -e "\nRéponse brute :\n$RESPONSE"
    step "Affichage des 20 dernières lignes du log Apache :"
    sudo tail -n 20 "$LOGFILE"
    exit 2
fi

step "Fin du test. Plateforme opérationnelle."

# Génération du guide d'exploitation
cat <<'EOF' > GUIDE_EXPLOITATION_MARTIALCOMP.md
# Guide d'exploitation rapide - Plateforme martialcomp.com

## 1. Redémarrer Apache

```bash
sudo systemctl restart apache2
```

## 2. Vérifier l'état de la plateforme

- Accéder à : http://martialcomp.com/debug-host/
- Si la page affiche les infos Django, la plateforme fonctionne.

## 3. Surveiller les logs Apache

```bash
sudo tail -f /var/www/vhosts/martialcomp.com/logs/error.log
```

## 4. En cas d'erreur 503 ou 500

- Vérifier la configuration Passenger dans /var/www/vhosts/system/martialcomp.com/conf/vhost.conf
- Vérifier le fichier passenger_wsgi.py à la racine du projet
- Redémarrer Apache
- Consulter les logs pour plus de détails

## 5. Commande de test automatique

```bash
sudo bash /var/www/vhosts/martialcomp.com/httpdocs/test_and_restart_production.sh
```

EOF

success "Guide d'exploitation généré : GUIDE_EXPLOITATION_MARTIALCOMP.md" 