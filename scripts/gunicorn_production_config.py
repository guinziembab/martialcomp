# Configuration Gunicorn pour MartialComp Production
# Serveur: 212.227.78.104
# Configuration optimisée pour multi-tenant avec sous-domaines

import multiprocessing
import os

# Socket Unix pour communication avec Nginx
bind = "unix:/opt/martialcomp/run/gunicorn.sock"

# Nombre de workers optimisé pour la production
# Formule: (2 x CPU cores) + 1
workers = multiprocessing.cpu_count() * 2 + 1
max_workers = 8  # Limite maximum pour éviter la surcharge

# Type de worker - sync pour Django standard
worker_class = "sync"

# Connexions par worker
worker_connections = 1000

# Timeouts optimisés pour MartialComp
timeout = 120  # 2 minutes pour les requêtes longues (QR generation, etc.)
keepalive = 5  # Keep-alive plus long pour les connexions fréquentes
graceful_timeout = 30

# Configuration mémoire
max_requests = 1000  # Restart worker après 1000 requêtes (évite memory leaks)
max_requests_jitter = 100  # Variation aléatoire pour éviter restart simultané

# Permissions et sécurité
umask = 0o002
user = "martialcomp"
group = "www-data"

# Répertoire de travail
chdir = "/opt/martialcomp/app"

# PID file
pidfile = "/opt/martialcomp/run/gunicorn.pid"

# Logging production
loglevel = "info"
accesslog = "/opt/martialcomp/logs/gunicorn_access.log"
errorlog = "/opt/martialcomp/logs/gunicorn_error.log"
capture_output = True

# Format des logs d'accès détaillé
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming pour monitoring
proc_name = "martialcomp_gunicorn"

# Préchargement de l'application (améliore les performances)
preload_app = True

# Rechargement automatique désactivé en production
reload = False

# Configuration SSL/TLS si needed (pas nécessaire avec Nginx)
# keyfile = None
# certfile = None

# Variables d'environnement pour Django
raw_env = [
    "DJANGO_SETTINGS_MODULE=config.settings_production_final",
]

# Configuration pour multi-threading (si worker_class = "gthread")
# threads = 2

# Hooks pour monitoring et debugging
def when_ready(server):
    """Hook appelé quand Gunicorn est prêt"""
    server.log.info("MartialComp Gunicorn server is ready. Listening on: %s", server.address)

def worker_int(worker):
    """Hook appelé quand un worker reçoit SIGINT/SIGQUIT"""
    worker.log.info("Worker received SIGINT/SIGQUIT. Shutting down gracefully.")

def on_exit(server):
    """Hook appelé à l'arrêt du serveur"""
    server.log.info("MartialComp Gunicorn server is shutting down.")

def on_reload(server):
    """Hook appelé lors d'un reload"""
    server.log.info("MartialComp Gunicorn server is reloading.")

# Hooks pour gestion des workers
def worker_abort(worker):
    """Hook appelé quand un worker est tué par timeout"""
    worker.log.error("Worker timeout. Killing worker process.")

def pre_fork(server, worker):
    """Hook appelé avant de fork un nouveau worker"""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    """Hook appelé après avoir forké un nouveau worker"""
    server.log.info("Worker spawned successfully (pid: %s)", worker.pid)

def post_worker_init(worker):
    """Hook appelé après l'initialisation d'un worker"""
    worker.log.info("Worker initialized (pid: %s)", worker.pid)

def worker_exit(server, worker):
    """Hook appelé quand un worker se termine"""
    server.log.info("Worker exited (pid: %s)", worker.pid)

# Configuration SSL (si Gunicorn gère SSL directement)
# ssl_version = 3  # TLS
# ciphers = "ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS"
# ca_certs = None
# suppress_ragged_eofs = True

# Configuration pour débogage (désactivé en production)
spew = False
check_config = False

# Configuration système
enable_stdio_inheritance = False
pythonpath = "/opt/martialcomp/app"

# Configuration pour Docker (si utilisé)
# forwarded_allow_ips = "127.0.0.1"
# secure_scheme_headers = {
#     'X-FORWARDED-PROTOCOL': 'ssl',
#     'X-FORWARDED-PROTO': 'https',
#     'X-FORWARDED-SSL': 'on'
# }