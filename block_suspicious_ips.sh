#!/bin/bash

# Script pour bloquer les IPs suspectes immédiatement

echo "=== BLOCAGE IMMÉDIAT DES IPS SUSPECTES ==="
echo ""

# IPs à bloquer (basé sur l'analyse)
SUSPICIOUS_IPS=(
    "54.232.15.12"      # Brésil - 60+ requêtes
    "216.180.246.12"    # USA - tentatives répétées
    "47.251.13.59"      # Chine - comportement suspect
    "159.223.53.103"    # Digital Ocean - bot probable
    "143.198.32.92"     # Digital Ocean - scanner
    "143.110.182.33"    # Digital Ocean - scanner
)

echo "Blocage via iptables..."
echo ""

for ip in "${SUSPICIOUS_IPS[@]}"; do
    # Vérifier si l'IP est déjà bloquée
    if iptables -L INPUT -n | grep -q "$ip"; then
        echo "✓ $ip - déjà bloquée"
    else
        # Bloquer l'IP
        iptables -A INPUT -s "$ip" -j DROP
        echo "✅ $ip - BLOQUÉE"
    fi
done

# Sauvegarder les règles
echo ""
echo "Sauvegarde des règles iptables..."

# Pour Debian/Ubuntu
if command -v iptables-save &> /dev/null; then
    iptables-save > /etc/iptables/rules.v4
    echo "✅ Règles sauvegardées"
fi

# Afficher le résumé
echo ""
echo "Résumé des IPs bloquées:"
iptables -L INPUT -n | grep DROP | awk '{print $4}' | sort | uniq

echo ""
echo "============================================"
echo "BLOCAGE TERMINÉ"
echo "============================================"
echo ""
echo "Pour débloquer une IP:"
echo "iptables -D INPUT -s IP_ADDRESS -j DROP"
echo ""
echo "Pour voir toutes les règles:"
echo "iptables -L -n"
echo ""
echo "============================================"