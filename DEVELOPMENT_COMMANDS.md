# 🛠️ COMMANDES DE DÉVELOPPEMENT - MartialComp

## 📦 PHASE 1: Installation WebSocket

### 1. Installer les dépendances
```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Installer Django Channels et Redis
pip install channels[daphne]==4.0.0
pip install channels-redis==4.1.0
pip install redis==4.5.0
pip install daphne==4.0.0

# Mettre à jour requirements.txt
pip freeze > requirements.txt
```

### 2. Installer Redis (Ubuntu/Debian)
```bash
# Installation système
sudo apt update
sudo apt install redis-server

# Démarrer Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Vérifier que Redis fonctionne
redis-cli ping
# Devrait retourner: PONG
```

### 3. Configurer Django Channels
```bash
# Créer les fichiers nécessaires
touch config/routing.py
touch apps/competitions/consumers.py
touch apps/competitions/routing.py
```

### 4. Tester WebSocket
```bash
# Démarrer le serveur de développement avec Daphne
daphne -b 0.0.0.0 -p 8000 config.asgi:application

# Ou avec runserver (channels installé)
python manage.py runserver
```

---

## 🧪 PHASE 2: Tests

### 1. Configuration des tests
```bash
# Installer les dépendances de test
pip install pytest==7.4.0
pip install pytest-django==4.5.2
pip install pytest-cov==4.1.0
pip install factory-boy==3.3.0
pip install freezegun==1.2.2

# Pour les tests WebSocket
pip install pytest-asyncio==0.21.0
pip install channels[testing]
```

### 2. Exécuter les tests
```bash
# Tests unitaires
pytest apps/competitions/tests/unit/ -v

# Tests d'intégration
pytest apps/competitions/tests/integration/ -v

# Tests E2E
pytest apps/competitions/tests/e2e/ -v

# Tous les tests avec coverage
pytest --cov=apps --cov-report=html
open htmlcov/index.html  # Voir le rapport de couverture
```

### 3. Tests spécifiques
```bash
# Tester uniquement les modèles
pytest -k "test_models" -v

# Tester uniquement les WebSockets
pytest -k "test_websocket" -v

# Tester avec print statements
pytest -s -v
```

---

## 📚 PHASE 3: Documentation API

### 1. Installer Swagger
```bash
pip install drf-spectacular==0.26.0
```

### 2. Générer la documentation
```bash
# Générer le schema OpenAPI
python manage.py spectacular --file schema.yml

# Valider le schema
python manage.py spectacular --validate

# Servir la documentation
python manage.py runserver
# Accéder à: http://localhost:8000/api/docs/
```

---

## 🚀 PHASE 4: Optimisation

### 1. Analyser les performances
```bash
# Installer django-debug-toolbar
pip install django-debug-toolbar==4.2.0

# Profiler les requêtes SQL
python manage.py shell_plus --print-sql

# Identifier les requêtes N+1
python manage.py debugsqlshell
```

### 2. Optimiser la base de données
```bash
# Créer les indexes
python manage.py dbshell
CREATE INDEX idx_competition_discipline ON competitions_competition(discipline_id);
CREATE INDEX idx_competition_type_discipline ON competitions_competitiontype(discipline_id);
CREATE INDEX idx_registration_competition ON competitions_competitionregistration(competition_id);

# Analyser les requêtes lentes
python manage.py inspectdb > models_current.py
```

---

## 🔒 PHASE 5: Sécurité

### 1. Audit de sécurité
```bash
# Installer les outils de sécurité
pip install django-security==0.16.0
pip install bandit==1.7.5

# Scanner le code
bandit -r apps/

# Vérifier les dépendances vulnérables
pip install safety==2.3.0
safety check
```

### 2. Tests de sécurité
```bash
# OWASP ZAP scan (après installation)
docker run -t owasp/zap2docker-stable zap-baseline.py -t http://localhost:8000

# Test CSRF
curl -X POST http://localhost:8000/api/competitions/ -H "Content-Type: application/json" -d '{}'
```

---

## 📊 PHASE 6: Monitoring

### 1. Configurer Sentry
```bash
# Installer Sentry
pip install sentry-sdk==1.32.0

# Tester l'intégration
python manage.py shell
import sentry_sdk
sentry_sdk.capture_message("Test message")
```

### 2. Logs structurés
```bash
# Voir les logs en temps réel
tail -f logs/django.log | jq '.'

# Filtrer les erreurs
tail -f logs/django.log | grep ERROR

# Analyser les patterns
grep "WebSocket" logs/django.log | wc -l
```

---

## 🏗️ PHASE 7: CI/CD

### 1. Tests en local
```bash
# Simuler GitHub Actions en local
act -W .github/workflows/main.yml

# Ou manuellement
./scripts/run_tests.sh
./scripts/check_quality.sh
```

### 2. Build de production
```bash
# Collecter les fichiers statiques
python manage.py collectstatic --noinput

# Compiler les messages
python manage.py compilemessages

# Vérifier les migrations
python manage.py showmigrations
```

---

## 🌐 PHASE 8: Déploiement

### 1. Préparer l'environnement
```bash
# Créer le package de déploiement
./scripts/create_deployment_package.sh

# Vérifier la configuration
python manage.py check --deploy

# Tester avec les settings de production
python manage.py runserver --settings=config.settings.production
```

### 2. Déployer
```bash
# Transférer vers le serveur
rsync -avz --exclude='*.pyc' --exclude='venv' . user@server:/path/to/app/

# Sur le serveur
ssh user@server
cd /path/to/app
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

---

## 🔍 Commandes de Debug

### WebSocket Debug
```bash
# Console JavaScript (navigateur)
const ws = new WebSocket('ws://localhost:8000/ws/competition/1/');
ws.onmessage = (e) => console.log(e.data);
ws.send(JSON.stringify({type: 'ping'}));
```

### Django Shell Plus
```bash
python manage.py shell_plus

# Tester les requêtes
from apps.competitions.models import Competition, CompetitionType
Competition.objects.select_related('discipline').prefetch_related('competition_types')
```

### Monitoring en temps réel
```bash
# Surveiller les processus
htop -p $(pgrep -f "manage.py")

# Surveiller les connexions WebSocket
netstat -an | grep :8000

# Logs en temps réel avec couleur
tail -f logs/django.log | ccze -A
```

---

## 📱 Tests Mobile

### Tester l'API mobile
```bash
# Simuler une requête mobile
curl -H "X-Mobile-App: true" \
     -H "Authorization: Token your-token" \
     http://localhost:8000/api/competitions/

# Tester CORS
curl -H "Origin: http://mobile.app" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: X-Requested-With" \
     -X OPTIONS http://localhost:8000/api/competitions/
```

---

## 🆘 Dépannage

### Erreurs communes
```bash
# Redis connection refused
sudo systemctl status redis-server
sudo systemctl restart redis-server

# WebSocket connection failed
# Vérifier que Daphne est utilisé au lieu de runserver standard
daphne config.asgi:application

# Migrations échouées
python manage.py migrate --fake-initial
python manage.py migrate --run-syncdb

# Cache corrompu
python manage.py shell
from django.core.cache import cache
cache.clear()
```

---

## 📈 Suivi de progression

```bash
# Rapport quotidien
python daily_progress_tracker.py

# Mettre à jour une tâche
python daily_progress_tracker.py update websocket_infrastructure completed

# Générer rapport de conformité
python generate_compliance_report.py
```

---

**Dernière mise à jour:** 13 Octobre 2025