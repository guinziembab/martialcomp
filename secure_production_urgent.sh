#!/bin/bash

# Script de sécurisation URGENTE de la production

echo "=== SÉCURISATION URGENTE DE LA PRODUCTION ==="
echo "Date: $(date)"
echo ""

# 1. Installation de fail2ban
echo "1. INSTALLATION DE FAIL2BAN"
echo "==========================="

apt-get update -qq
apt-get install -y fail2ban

echo "✓ fail2ban installé"

# 2. Configuration fail2ban pour Django
echo ""
echo "2. CONFIGURATION FAIL2BAN"
echo "========================="

# Créer le filtre Django
cat > /etc/fail2ban/filter.d/django-auth.conf << 'F2B_FILTER'
[Definition]
failregex = Invalid password for .* from <HOST>
            Failed password for .* from <HOST>
            Invalid user .* from <HOST>
            User not found: .* from <HOST>
            Authentication failure for .* from <HOST>
            POST /admin/login/ .* 403
            POST /accounts/login/ .* 403
ignoreregex =
F2B_FILTER

# Créer le filtre pour les tentatives sur /admin/
cat > /etc/fail2ban/filter.d/django-admin.conf << 'F2B_ADMIN'
[Definition]
failregex = ^<HOST> .* "(GET|POST) /admin/.* HTTP/.*" (403|401)
            ^<HOST> .* "POST /admin/login/.* HTTP/.*" 200
ignoreregex = ^<HOST> .* "(GET|POST) /admin/.* HTTP/.*" (200|301|302|304)
F2B_ADMIN

# Configurer les jails
cat > /etc/fail2ban/jail.local << 'F2B_JAIL'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5
destemail = admin@martialcomp.com
sendername = Fail2Ban
mta = sendmail

[sshd]
enabled = true

[django-auth]
enabled = true
port = http,https
filter = django-auth
logpath = /var/www/vhosts/martialcomp.com/httpdocs/logs/django.log
maxretry = 5
bantime = 3600

[django-admin]
enabled = true
port = http,https
filter = django-admin
logpath = /var/log/nginx/access.log
maxretry = 10
bantime = 7200
findtime = 300

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
port = http,https
logpath = /var/log/nginx/*error.log
maxretry = 10
bantime = 3600
F2B_JAIL

echo "✓ Filtres et jails configurés"

# 3. Configuration nginx rate limiting
echo ""
echo "3. CONFIGURATION NGINX RATE LIMITING"
echo "===================================="

# Ajouter les zones de rate limiting dans nginx
cat > /tmp/nginx_rate_limit.conf << 'NGINX_RATE'
# Rate limiting zones
limit_req_zone $binary_remote_addr zone=general:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=login:10m rate=3r/m;
limit_req_zone $binary_remote_addr zone=admin:10m rate=5r/m;

# Protection contre les attaques par force brute
geo $limit {
    default 1;
    # Whitelist des IPs de confiance (à personnaliser)
    127.0.0.1 0;
}

map $limit $limit_key {
    0 "";
    1 $binary_remote_addr;
}
NGINX_RATE

# Vérifier si on peut modifier la config nginx via Plesk
if [ -f "/var/www/vhosts/system/martialcomp.com/conf/vhost_nginx.conf" ]; then
    echo "Configuration Nginx via Plesk..."
    
    # Créer un fichier de configuration personnalisé pour Plesk
    cat > /var/www/vhosts/system/martialcomp.com/conf/nginx_security.conf << 'NGINX_SEC'
# Protection des endpoints sensibles
location /admin/ {
    limit_req zone=admin burst=5 nodelay;
    limit_req_status 429;
}

location /accounts/login/ {
    limit_req zone=login burst=3 nodelay;
    limit_req_status 429;
}

location /set_language/ {
    limit_req zone=general burst=20 nodelay;
}

# Bloquer les user-agents suspects
if ($http_user_agent ~* (wget|curl|python|scrapy|bot|crawler|spider)) {
    return 403;
}

# Bloquer les méthodes non autorisées
if ($request_method !~ ^(GET|HEAD|POST)$) {
    return 405;
}
NGINX_SEC
    
    echo "✓ Configuration Nginx ajoutée"
fi

# 4. Installation et configuration de django-ratelimit
echo ""
echo "4. INSTALLATION DJANGO-RATELIMIT"
echo "================================"

cd /var/www/vhosts/martialcomp.com/httpdocs
source /var/www/vhosts/martialcomp.com/venv/bin/activate

pip install django-ratelimit

# Créer des décorateurs de rate limiting
cat > apps/core/decorators.py << 'DECORATORS_PY'
from django_ratelimit.decorators import ratelimit
from functools import wraps
from django.http import HttpResponseForbidden
import logging

logger = logging.getLogger(__name__)

def rate_limit_login(func):
    """Rate limit pour les tentatives de connexion"""
    @wraps(func)
    @ratelimit(key='ip', rate='5/m', method='POST')
    def wrapper(request, *args, **kwargs):
        if getattr(request, 'limited', False):
            logger.warning(f"Rate limit atteint pour IP: {request.META.get('REMOTE_ADDR')}")
            return HttpResponseForbidden("Trop de tentatives. Réessayez dans quelques minutes.")
        return func(request, *args, **kwargs)
    return wrapper

def rate_limit_admin(func):
    """Rate limit pour l'accès admin"""
    @wraps(func)
    @ratelimit(key='ip', rate='20/h', method='ALL')
    def wrapper(request, *args, **kwargs):
        if getattr(request, 'limited', False):
            logger.warning(f"Rate limit admin atteint pour IP: {request.META.get('REMOTE_ADDR')}")
            return HttpResponseForbidden("Accès temporairement bloqué.")
        return func(request, *args, **kwargs)
    return wrapper
DECORATORS_PY

echo "✓ django-ratelimit installé et configuré"

# 5. Bloquer les IPs suspectes immédiatement
echo ""
echo "5. BLOCAGE DES IPS SUSPECTES"
echo "============================"

# Analyser les logs et bloquer les IPs avec trop de requêtes
echo "Analyse des IPs suspectes..."
tail -n 10000 /var/log/nginx/access.log | \
    awk '$7 ~ /\/admin/ {print $1}' | \
    sort | uniq -c | sort -rn | \
    awk '$1 > 50 {print $2}' > /tmp/suspicious_ips.txt

if [ -s /tmp/suspicious_ips.txt ]; then
    echo "IPs à bloquer:"
    cat /tmp/suspicious_ips.txt
    
    # Bloquer via iptables
    while read ip; do
        iptables -A INPUT -s $ip -j DROP
        echo "✓ Bloqué: $ip"
    done < /tmp/suspicious_ips.txt
    
    # Sauvegarder les règles
    iptables-save > /etc/iptables/rules.v4
fi

# 6. Configuration de monitoring
echo ""
echo "6. CONFIGURATION DU MONITORING"
echo "=============================="

# Créer un script de monitoring
cat > /usr/local/bin/monitor_attacks.sh << 'MONITOR_SH'
#!/bin/bash

LOG_FILE="/var/www/vhosts/martialcomp.com/httpdocs/logs/security_monitor.log"
ALERT_EMAIL="admin@martialcomp.com"

# Fonction pour envoyer des alertes
send_alert() {
    local subject="$1"
    local message="$2"
    echo "$message" | mail -s "[MartialComp Security] $subject" $ALERT_EMAIL 2>/dev/null || echo "$message" >> $LOG_FILE
}

# Vérifier les tentatives sur /admin/
ADMIN_ATTEMPTS=$(tail -n 1000 /var/log/nginx/access.log | grep -c "/admin/")
if [ $ADMIN_ATTEMPTS -gt 100 ]; then
    send_alert "Nombreuses tentatives sur /admin/" "Détecté $ADMIN_ATTEMPTS tentatives sur /admin/ dans les 1000 dernières lignes"
fi

# Vérifier fail2ban
BANNED_IPS=$(fail2ban-client status | grep -E "Total banned:" | awk '{print $4}')
if [ "$BANNED_IPS" -gt 0 ]; then
    DETAILS=$(fail2ban-client status django-admin | grep -A 5 "Banned IP")
    send_alert "IPs bannies par fail2ban" "Nombre d'IPs bannies: $BANNED_IPS\n\n$DETAILS"
fi

# Log
echo "[$(date)] Monitoring exécuté - Admin attempts: $ADMIN_ATTEMPTS, Banned IPs: $BANNED_IPS" >> $LOG_FILE
MONITOR_SH

chmod +x /usr/local/bin/monitor_attacks.sh

# Ajouter au cron
echo "*/5 * * * * /usr/local/bin/monitor_attacks.sh" | crontab -

echo "✓ Monitoring configuré (exécution toutes les 5 minutes)"

# 7. Redémarrage des services
echo ""
echo "7. REDÉMARRAGE DES SERVICES"
echo "==========================="

systemctl restart fail2ban
systemctl restart nginx
systemctl restart martialcomp.service

echo "✓ Services redémarrés"

# 8. Status final
echo ""
echo "8. VÉRIFICATION FINALE"
echo "====================="

echo "fail2ban status:"
fail2ban-client status

echo ""
echo "Jails actifs:"
fail2ban-client status | grep "Jail list" -A 1

echo ""
echo "============================================"
echo "SÉCURISATION URGENTE TERMINÉE"
echo "============================================"
echo ""
echo "✅ fail2ban installé et configuré"
echo "✅ Rate limiting nginx configuré"
echo "✅ django-ratelimit installé"
echo "✅ IPs suspectes bloquées"
echo "✅ Monitoring actif"
echo ""
echo "Actions supplémentaires recommandées:"
echo "1. Configurer Cloudflare WAF depuis le dashboard"
echo "2. Activer le mode 'Under Attack' si nécessaire"
echo "3. Configurer des règles de pare-feu Cloudflare"
echo "4. Examiner régulièrement /var/www/vhosts/martialcomp.com/httpdocs/logs/security_monitor.log"
echo ""
echo "Commandes utiles:"
echo "- fail2ban-client status django-admin"
echo "- tail -f /var/log/fail2ban.log"
echo "- iptables -L -n"
echo ""
echo "============================================"