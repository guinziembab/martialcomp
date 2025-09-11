#!/bin/bash

# setup_python_env_and_passenger.sh
# Ce script prépare un environnement Python propre pour Passenger/Django
# et ajuste la configuration pour une exécution fiable en production.

set -e

PROJECT_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
VENV_DIR="$PROJECT_DIR/.venv"
VHOST_CONF="/var/www/vhosts/system/martialcomp.com/conf/vhost.conf"
REQUIREMENTS="$PROJECT_DIR/requirements.txt"
PYTHON_BIN="/usr/bin/python3"

step() {
    echo -e "\n\033[1;34m[ETAPE]\033[0m $1"
}

error() {
    echo -e "\033[1;31m[ERREUR]\033[0m $1"
}

success() {
    echo -e "\033[1;32m[SUCCES]\033[0m $1"
}

step "Création de l'environnement virtuel Python..."
if [ ! -d "$VENV_DIR" ]; then
    $PYTHON_BIN -m venv "$VENV_DIR"
    success "Environnement virtuel créé."
else
    success "Environnement virtuel déjà présent."
fi

step "Activation de l'environnement virtuel et mise à jour de pip..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip

step "Installation des dépendances du projet..."
if [ -f "$REQUIREMENTS" ]; then
    pip install -r "$REQUIREMENTS"
    success "Dépendances installées."
else
    error "Fichier requirements.txt introuvable !"
    exit 1
fi

deactivate

step "Modification de la configuration Passenger pour utiliser le bon Python..."
# On remplace (ou ajoute) la ligne PassengerPython dans vhost.conf
if grep -q "PassengerPython" "$VHOST_CONF"; then
    sed -i "s|PassengerPython .*|PassengerPython $VENV_DIR/bin/python|" "$VHOST_CONF"
else
    sed -i "/<IfModule mod_passenger.c>/a \\    PassengerPython $VENV_DIR/bin/python" "$VHOST_CONF"
fi
success "PassengerPython configuré dans vhost.conf."

step "Vérification de la syntaxe Apache..."
sudo apache2ctl configtest

step "Redémarrage d'Apache..."
sudo systemctl restart apache2 && success "Apache redémarré."

step "Test de la route /debug-host/ ..."
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" "http://martialcomp.com/debug-host/" || true)
CODE=$(echo "$RESPONSE" | grep HTTP_CODE | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE:/d')

if [[ "$CODE" == "200" ]]; then
    success "La route /debug-host/ est accessible."
    echo -e "\nRéponse :\n$BODY"
else
    error "La route /debug-host/ n'est pas accessible (code HTTP $CODE)."
    echo -e "\nRéponse brute :\n$RESPONSE"
    step "Affichage des 20 dernières lignes du log Apache :"
    sudo tail -n 20 /var/www/vhosts/martialcomp.com/logs/error.log
    exit 2
fi

step "Fin du script. Plateforme Python et Passenger configurée." 

# setup_python_env_and_passenger.sh
# Ce script prépare un environnement Python propre pour Passenger/Django
# et ajuste la configuration pour une exécution fiable en production.

set -e

PROJECT_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
VENV_DIR="$PROJECT_DIR/.venv"
VHOST_CONF="/var/www/vhosts/system/martialcomp.com/conf/vhost.conf"
REQUIREMENTS="$PROJECT_DIR/requirements.txt"
PYTHON_BIN="/usr/bin/python3"

step() {
    echo -e "\n\033[1;34m[ETAPE]\033[0m $1"
}

error() {
    echo -e "\033[1;31m[ERREUR]\033[0m $1"
}

success() {
    echo -e "\033[1;32m[SUCCES]\033[0m $1"
}

step "Création de l'environnement virtuel Python..."
if [ ! -d "$VENV_DIR" ]; then
    $PYTHON_BIN -m venv "$VENV_DIR"
    success "Environnement virtuel créé."
else
    success "Environnement virtuel déjà présent."
fi

step "Activation de l'environnement virtuel et mise à jour de pip..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip

step "Installation des dépendances du projet..."
if [ -f "$REQUIREMENTS" ]; then
    pip install -r "$REQUIREMENTS"
    success "Dépendances installées."
else
    error "Fichier requirements.txt introuvable !"
    exit 1
fi

deactivate

step "Modification de la configuration Passenger pour utiliser le bon Python..."
# On remplace (ou ajoute) la ligne PassengerPython dans vhost.conf
if grep -q "PassengerPython" "$VHOST_CONF"; then
    sed -i "s|PassengerPython .*|PassengerPython $VENV_DIR/bin/python|" "$VHOST_CONF"
else
    sed -i "/<IfModule mod_passenger.c>/a \\    PassengerPython $VENV_DIR/bin/python" "$VHOST_CONF"
fi
success "PassengerPython configuré dans vhost.conf."

step "Vérification de la syntaxe Apache..."
sudo apache2ctl configtest

step "Redémarrage d'Apache..."
sudo systemctl restart apache2 && success "Apache redémarré."

step "Test de la route /debug-host/ ..."
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" "http://martialcomp.com/debug-host/" || true)
CODE=$(echo "$RESPONSE" | grep HTTP_CODE | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE:/d')

if [[ "$CODE" == "200" ]]; then
    success "La route /debug-host/ est accessible."
    echo -e "\nRéponse :\n$BODY"
else
    error "La route /debug-host/ n'est pas accessible (code HTTP $CODE)."
    echo -e "\nRéponse brute :\n$RESPONSE"
    step "Affichage des 20 dernières lignes du log Apache :"
    sudo tail -n 20 /var/www/vhosts/martialcomp.com/logs/error.log
    exit 2
fi

step "Fin du script. Plateforme Python et Passenger configurée." 