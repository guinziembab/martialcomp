#!/bin/bash

# Script pour bloquer définitivement le port 8001 et surveiller les processus gunicorn
echo "🔒 Blocage permanent du port 8001..."

# 1. Bloquer le port 8001 avec iptables
echo "📋 Application des règles iptables..."
iptables -C INPUT -p tcp --dport 8001 -j DROP 2>/dev/null || iptables -A INPUT -p tcp --dport 8001 -j DROP
iptables -C OUTPUT -p tcp --dport 8001 -j DROP 2>/dev/null || iptables -A OUTPUT -p tcp --dport 8001 -j DROP

# 2. Sauvegarder les règles iptables
iptables-save > /etc/iptables/rules.v4

# 3. Créer un script de surveillance
cat > /usr/local/bin/monitor_gunicorn.sh << 'EOF'
#!/bin/bash

# Script de surveillance pour empêcher gunicorn sur le port 8001
while true; do
    # Vérifier s'il y a des processus gunicorn sur le port 8001
    PIDS=$(ps aux | grep gunicorn | grep 8001 | grep -v grep | awk '{print $2}')
    
    if [ ! -z "$PIDS" ]; then
        echo "$(date): ALERTE - Processus gunicorn detecte sur le port 8001: $PIDS"
        echo "$(date): Suppression des processus..."
        kill -9 $PIDS
        echo "$(date): Processus supprimes."
    fi
    
    # Vérifier que le service systemd fonctionne
    if ! systemctl is-active --quiet martialcomp-gunicorn.service; then
        echo "$(date): Service martialcomp-gunicorn inactif, redemarrage..."
        systemctl restart martialcomp-gunicorn.service
    fi
    
    sleep 30
done
EOF

# 4. Rendre le script exécutable
chmod +x /usr/local/bin/monitor_gunicorn.sh

# 5. Créer un service systemd pour la surveillance
cat > /etc/systemd/system/gunicorn-monitor.service << 'EOF'
[Unit]
Description=Monitor Gunicorn processes to prevent port 8001 usage
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/monitor_gunicorn.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 6. Activer et démarrer le service de surveillance
systemctl daemon-reload
systemctl enable gunicorn-monitor.service
systemctl start gunicorn-monitor.service

echo "✅ Blocage permanent configure!"
echo "📊 Services actifs:"
echo "  - martialcomp-gunicorn.service: $(systemctl is-active martialcomp-gunicorn.service)"
echo "  - gunicorn-monitor.service: $(systemctl is-active gunicorn-monitor.service)"
echo ""
echo "🔍 Verification des processus gunicorn:"
ps aux | grep gunicorn | grep -v grep
echo ""
echo "📋 Regles iptables pour le port 8001:"
iptables -L | grep 8001 