#!/bin/bash

echo "=== DIAGNOSTIC POSTGRESQL MARTIALCOMP ==="
echo "Date: $(date)"
echo ""

# 1. Vérifier les services PostgreSQL disponibles
echo "1. SERVICES POSTGRESQL DISPONIBLES:"
systemctl list-units --type=service | grep postgresql
echo ""

# 2. Statut des services PostgreSQL
echo "2. STATUT DES SERVICES:"
systemctl status postgresql --no-pager
echo ""
systemctl status postgresql@13-main --no-pager 2>/dev/null || echo "Service postgresql@13-main non trouvé"
echo ""

# 3. Vérifier les processus PostgreSQL
echo "3. PROCESSUS POSTGRESQL:"
ps aux | grep postgres | grep -v grep
echo ""

# 4. Vérifier les ports en écoute
echo "4. PORTS EN ÉCOUTE:"
netstat -tlnp | grep 5432 || echo "Port 5432 non en écoute"
echo ""

# 5. Vérifier les permissions des dossiers
echo "5. PERMISSIONS DES DOSSIERS:"
ls -la /var/lib/postgresql/13/main/ | head -5
echo ""

# 6. Vérifier la configuration
echo "6. CONFIGURATION POSTGRESQL:"
echo "Fichier de config principal:"
ls -la /etc/postgresql/13/main/postgresql.conf
echo ""

# 7. Tester la connexion
echo "7. TEST DE CONNEXION:"
PGPASSWORD='martialcomp123' psql -h localhost -U martialcomp_user -d martialcomp_db -c 'SELECT version();' 2>/dev/null || echo "Échec de connexion PostgreSQL"
echo ""

# 8. Logs récents
echo "8. LOGS RÉCENTS:"
journalctl -u postgresql --no-pager -n 10
echo ""

echo "=== FIN DU DIAGNOSTIC ===" 

echo "=== DIAGNOSTIC POSTGRESQL MARTIALCOMP ==="
echo "Date: $(date)"
echo ""

# 1. Vérifier les services PostgreSQL disponibles
echo "1. SERVICES POSTGRESQL DISPONIBLES:"
systemctl list-units --type=service | grep postgresql
echo ""

# 2. Statut des services PostgreSQL
echo "2. STATUT DES SERVICES:"
systemctl status postgresql --no-pager
echo ""
systemctl status postgresql@13-main --no-pager 2>/dev/null || echo "Service postgresql@13-main non trouvé"
echo ""

# 3. Vérifier les processus PostgreSQL
echo "3. PROCESSUS POSTGRESQL:"
ps aux | grep postgres | grep -v grep
echo ""

# 4. Vérifier les ports en écoute
echo "4. PORTS EN ÉCOUTE:"
netstat -tlnp | grep 5432 || echo "Port 5432 non en écoute"
echo ""

# 5. Vérifier les permissions des dossiers
echo "5. PERMISSIONS DES DOSSIERS:"
ls -la /var/lib/postgresql/13/main/ | head -5
echo ""

# 6. Vérifier la configuration
echo "6. CONFIGURATION POSTGRESQL:"
echo "Fichier de config principal:"
ls -la /etc/postgresql/13/main/postgresql.conf
echo ""

# 7. Tester la connexion
echo "7. TEST DE CONNEXION:"
PGPASSWORD='martialcomp123' psql -h localhost -U martialcomp_user -d martialcomp_db -c 'SELECT version();' 2>/dev/null || echo "Échec de connexion PostgreSQL"
echo ""

# 8. Logs récents
echo "8. LOGS RÉCENTS:"
journalctl -u postgresql --no-pager -n 10
echo ""

echo "=== FIN DU DIAGNOSTIC ===" 