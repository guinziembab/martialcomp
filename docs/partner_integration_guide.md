# Guide d'intégration partenaires - MartialComp

## 🤝 Programme partenaire

### Types de partenariats
1. **Intégrateur certifié** : Déploiement et support
2. **Développeur agréé** : Extensions et plugins
3. **Revendeur autorisé** : Distribution commerciale
4. **Partenaire technologique** : Intégrations tierces

## 🔧 API Reference

### Authentification
```bash
# Obtenir un token API
curl -X POST https://api.martialcomp.com/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET",
    "grant_type": "client_credentials"
  }'

# Réponse
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### Endpoints principaux

#### Tenants
```bash
# Lister les tenants (admin seulement)
GET /v1/tenants
Authorization: Bearer TOKEN

# Créer un tenant
POST /v1/tenants
{
  "name": "Nouveau Club",
  "domain": "nouveau-club",
  "plan": "essentials",
  "admin_email": "admin@club.com"
}

# Mettre à jour un tenant
PATCH /v1/tenants/{tenant_id}
{
  "plan": "masters",
  "metadata": {
    "custom_field": "value"
  }
}
```

#### Pratiquants
```bash
# Lister les pratiquants
GET /v1/practitioners
X-Tenant-ID: {tenant_id}

# Créer un pratiquant
POST /v1/practitioners
X-Tenant-ID: {tenant_id}
{
  "first_name": "Jean",
  "last_name": "Dupont",
  "email": "jean.dupont@email.com",
  "birth_date": "1990-05-15",
  "current_grade": "2e Dan"
}

# Mettre à jour un pratiquant
PATCH /v1/practitioners/{id}
{
  "current_grade": "3e Dan"
}
```

#### Compétitions
```bash
# Créer une compétition
POST /v1/competitions
X-Tenant-ID: {tenant_id}
{
  "name": "Championnat 2024",
  "date": "2024-06-15",
  "location": "Paris",
  "categories": ["kata", "combat"],
  "registration_deadline": "2024-05-31"
}

# Inscrire un pratiquant
POST /v1/competitions/{id}/registrations
{
  "practitioner_id": 123,
  "categories": ["kata"]
}

# Saisir des résultats
POST /v1/competitions/{id}/results
{
  "category": "kata",
  "results": [
    {"practitioner_id": 123, "rank": 1, "score": 8.5},
    {"practitioner_id": 456, "rank": 2, "score": 8.3}
  ]
}
```

### Webhooks

#### Configuration
```bash
POST /v1/webhooks
{
  "url": "https://your-app.com/webhooks/martialcomp",
  "events": [
    "practitioner.created",
    "practitioner.updated",
    "competition.created",
    "results.published"
  ],
  "secret": "your-webhook-secret"
}
```

#### Format des événements
```json
{
  "id": "evt_1234567890",
  "type": "practitioner.created",
  "created": "2024-01-15T10:30:00Z",
  "data": {
    "id": 123,
    "first_name": "Jean",
    "last_name": "Dupont",
    "email": "jean.dupont@email.com"
  },
  "previous_attributes": null
}
```

## 🔌 Intégrations courantes

### 1. Single Sign-On (SSO)

#### SAML 2.0
```xml
<!-- Configuration SAML -->
<EntityDescriptor entityID="https://your-idp.com">
  <IDPSSODescriptor>
    <SingleSignOnService 
      Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
      Location="https://your-idp.com/sso"/>
  </IDPSSODescriptor>
</EntityDescriptor>
```

#### OAuth 2.0
```javascript
// Configuration OAuth
const config = {
  clientId: 'YOUR_CLIENT_ID',
  clientSecret: 'YOUR_CLIENT_SECRET',
  redirectUri: 'https://your-app.com/callback',
  authorizationUrl: 'https://martialcomp.com/oauth/authorize',
  tokenUrl: 'https://martialcomp.com/oauth/token'
};
```

### 2. Synchronisation des données

#### Import en masse
```python
import requests
import csv

def bulk_import_practitioners(csv_file, tenant_id, api_token):
    """Import en masse des pratiquants"""
    
    url = "https://api.martialcomp.com/v1/bulk/practitioners"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "X-Tenant-ID": tenant_id
    }
    
    with open(csv_file, 'r') as f:
        data = list(csv.DictReader(f))
    
    response = requests.post(url, json={"practitioners": data}, headers=headers)
    
    if response.status_code == 202:
        job_id = response.json()["job_id"]
        return check_import_status(job_id)
    else:
        raise Exception(f"Import failed: {response.text}")

def check_import_status(job_id):
    """Vérifier le statut d'un import"""
    url = f"https://api.martialcomp.com/v1/jobs/{job_id}"
    
    while True:
        response = requests.get(url, headers=headers)
        status = response.json()
        
        if status["state"] == "completed":
            return status["result"]
        elif status["state"] == "failed":
            raise Exception(f"Import failed: {status['error']}")
        
        time.sleep(5)  # Attendre 5 secondes
```

#### Synchronisation temps réel
```javascript
// WebSocket pour sync temps réel
const ws = new WebSocket('wss://api.martialcomp.com/v1/sync');

ws.on('open', () => {
  ws.send(JSON.stringify({
    type: 'auth',
    token: 'YOUR_API_TOKEN',
    tenant_id: 'TENANT_ID'
  }));
});

ws.on('message', (data) => {
  const event = JSON.parse(data);
  
  switch(event.type) {
    case 'practitioner.updated':
      updateLocalPractitioner(event.data);
      break;
    case 'competition.created':
      addNewCompetition(event.data);
      break;
  }
});
```

### 3. Passerelles de paiement

#### Stripe
```javascript
// Configuration Stripe
const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);

async function createPaymentIntent(amount, tenantId) {
  const paymentIntent = await stripe.paymentIntents.create({
    amount: amount * 100, // En centimes
    currency: 'eur',
    metadata: {
      tenant_id: tenantId,
      platform: 'martialcomp'
    }
  });
  
  // Enregistrer dans MartialComp
  await axios.post('https://api.martialcomp.com/v1/payments', {
    external_id: paymentIntent.id,
    amount: amount,
    status: 'pending',
    provider: 'stripe'
  });
  
  return paymentIntent;
}
```

#### PayPal
```python
import paypalrestsdk

paypalrestsdk.configure({
  "mode": "live",
  "client_id": "YOUR_CLIENT_ID",
  "client_secret": "YOUR_CLIENT_SECRET"
})

def create_payment(amount, tenant_id):
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {"payment_method": "paypal"},
        "transactions": [{
            "amount": {
                "total": str(amount),
                "currency": "EUR"
            },
            "description": f"Cotisation MartialComp - {tenant_id}"
        }],
        "redirect_urls": {
            "return_url": "https://martialcomp.com/payment/success",
            "cancel_url": "https://martialcomp.com/payment/cancel"
        }
    })
    
    if payment.create():
        # Enregistrer dans MartialComp
        save_payment_to_martialcomp(payment.id, amount, tenant_id)
        return payment
    else:
        raise Exception(payment.error)
```

## 🛠️ SDK et bibliothèques

### SDK officiel
```bash
# JavaScript/Node.js
npm install @martialcomp/sdk

# Python
pip install martialcomp-sdk

# PHP
composer require martialcomp/sdk
```

### Exemple d'utilisation (Node.js)
```javascript
const MartialComp = require('@martialcomp/sdk');

const client = new MartialComp({
  apiKey: 'YOUR_API_KEY',
  tenantId: 'YOUR_TENANT_ID'
});

// Créer un pratiquant
const practitioner = await client.practitioners.create({
  firstName: 'Jean',
  lastName: 'Dupont',
  email: 'jean@example.com'
});

// Lister les compétitions
const competitions = await client.competitions.list({
  status: 'upcoming',
  limit: 10
});

// Inscription à une compétition
await client.registrations.create({
  competitionId: competitions[0].id,
  practitionerId: practitioner.id,
  categories: ['kata']
});
```

## 📋 Certification partenaire

### Niveaux de certification
1. **Bronze** : Connaissances de base
2. **Silver** : Intégration avancée
3. **Gold** : Expert certifié

### Process de certification
1. Formation en ligne (8h)
2. Projet pratique
3. Examen théorique
4. Certification valable 2 ans

### Avantages
- Badge officiel
- Listing annuaire partenaires
- Support prioritaire
- Commission préférentielle
- Accès beta features

## 🚀 Déploiement

### Architecture recommandée
```yaml
# docker-compose.yml
version: '3.8'

services:
  martialcomp-connector:
    image: martialcomp/connector:latest
    environment:
      - API_KEY=${MARTIALCOMP_API_KEY}
      - TENANT_ID=${MARTIALCOMP_TENANT_ID}
      - WEBHOOK_SECRET=${WEBHOOK_SECRET}
    ports:
      - "8080:8080"
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
```

### Configuration Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: martialcomp-integration
spec:
  replicas: 3
  selector:
    matchLabels:
      app: martialcomp
  template:
    metadata:
      labels:
        app: martialcomp
    spec:
      containers:
      - name: connector
        image: martialcomp/connector:latest
        env:
        - name: API_KEY
          valueFrom:
            secretKeyRef:
              name: martialcomp-secret
              key: api-key
```

## 📞 Support partenaires

### Ressources
- **Documentation technique** : docs.martialcomp.com
- **API Explorer** : api.martialcomp.com/explorer
- **Slack communauté** : martialcomp.slack.com

### Contact
- **Email** : partners@martialcomp.com
- **Hotline** : +33 1 23 45 67 88
- **Account manager** : Dédié selon niveau

### SLA
- **Bronze** : 48h
- **Silver** : 24h
- **Gold** : 4h

---

*Rejoignez l'écosystème MartialComp*

**Devenir partenaire** : partners.martialcomp.com