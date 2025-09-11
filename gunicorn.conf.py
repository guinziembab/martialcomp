# Configuration Gunicorn pour MartialComp Production
import multiprocessing
import os

# Liaison et réseau - PORT 8002
bind = "127.0.0.1:8002"
backlog = 2048

# Processus worker
workers = min(4, (multiprocessing.cpu_count() * 2) + 1)
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
preload_app = True

# Timeouts
timeout = 30
keepalive = 2
graceful_timeout = 30

# Utilisateur et groupe
user = "www-data"
group = "www-data"

# Logging
accesslog = "/var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_access.log"
errorlog = "/var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Nom du processus
proc_name = 'martialcomp'

# Dossier temporaire
tmp_upload_dir = "/tmp"

# Variables d'environnement
raw_env = [
  'DJANGO_SETTINGS_MODULE=config.settings.production',
  'PYTHONPATH=/var/www/vhosts/martialcomp.com/httpdocs']

# Callbacks
def on_starting(server):
  server.log.info("🚀 Démarrage du serveur MartialComp sur le port 8002")

def on_reload(server):
  server.log.info("🔄 Rechargement du serveur MartialComp")

def worker_int(worker):
  worker.log.info("🛑 Worker interrompu (PID: %s)", worker.pid)

def pre_fork(server, worker):
  server.log.info("🔧 Pré-fork worker (PID: %s)", worker.pid)

def post_fork(server, worker):
  server.log.info("✅ Worker créé (PID: %s)", worker.pid)

def worker_abort(worker):
  worker.log.info("💥 Worker avorté (PID: %s)", worker.pid) 
import multiprocessing
import os

# Liaison et réseau - PORT 8002
bind = "127.0.0.1:8002"
backlog = 2048

# Processus worker
workers = min(4, (multiprocessing.cpu_count() * 2) + 1)
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
preload_app = True

# Timeouts
timeout = 30
keepalive = 2
graceful_timeout = 30

# Utilisateur et groupe
user = "www-data"
group = "www-data"

# Logging
accesslog = "/var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_access.log"
errorlog = "/var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Nom du processus
proc_name = 'martialcomp'

# Dossier temporaire
tmp_upload_dir = "/tmp"

# Variables d'environnement
raw_env = [
  'DJANGO_SETTINGS_MODULE=config.settings.production',
  'PYTHONPATH=/var/www/vhosts/martialcomp.com/httpdocs']

# Callbacks
def on_starting(server):
  server.log.info("🚀 Démarrage du serveur MartialComp sur le port 8002")

def on_reload(server):
  server.log.info("🔄 Rechargement du serveur MartialComp")

def worker_int(worker):
  worker.log.info("🛑 Worker interrompu (PID: %s)", worker.pid)

def pre_fork(server, worker):
  server.log.info("🔧 Pré-fork worker (PID: %s)", worker.pid)

def post_fork(server, worker):
  server.log.info("✅ Worker créé (PID: %s)", worker.pid)

def worker_abort(worker):
  worker.log.info("💥 Worker avorté (PID: %s)", worker.pid) 