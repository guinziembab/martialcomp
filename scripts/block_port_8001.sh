#!/bin/bash

# Script pour bloquer définitivement le port 8001
echo "🔒 Blocage du port 8001..."

# Bloquer le port 8001 avec iptables
iptables -A INPUT -p tcp --dport 8001 -j DROP
iptables -A OUTPUT -p tcp --dport 8001 -j DROP

# Sauvegarder les règles iptables
iptables-save > /etc/iptables/rules.v4

echo "✅ Port 8001 bloqué définitivement"
echo "📋 Règles iptables appliquées :"
iptables -L | grep 8001 