# Guide d'utilisation des profils hors-ligne

## Introduction

La fonctionnalité de profil hors-ligne permet aux pratiquants de présenter leur profil et leurs informations d'identification sans nécessiter une connexion internet active. Cela est particulièrement utile lors d'événements, de compétitions ou d'entraînements dans des lieux où la connexion internet est limitée ou absente.

## Table des matières

1. [Pour les pratiquants](#pour-les-pratiquants)
2. [Pour les administrateurs de club](#pour-les-administrateurs-de-club)
3. [Pour les organisateurs d'événements](#pour-les-organisateurs-dévénements)
4. [Questions fréquentes](#questions-fréquentes)
5. [Résolution des problèmes](#résolution-des-problèmes)

## Pour les pratiquants

### Générer votre QR code de profil hors-ligne

1. Connectez-vous à votre compte sur l'application MartialComp
2. Accédez à votre profil
3. Cliquez sur l'option "QR Code" 
4. Sur la page QR Code, vous verrez une nouvelle option "Profil hors-ligne"
5. Cliquez sur ce bouton pour générer votre QR code de profil hors-ligne

### Utiliser votre QR code

Votre QR code de profil hors-ligne peut être utilisé de plusieurs façons :

- **Impression** : Vous pouvez imprimer le QR code et l'emporter avec vous aux événements
- **Téléchargement** : Vous pouvez télécharger l'image et la conserver sur votre téléphone
- **Partage** : Vous pouvez partager le token de profil via email ou messagerie

### Validité du profil hors-ligne

- Votre profil hors-ligne est valable pendant **30 jours** après sa génération
- Après cette période, vous devrez générer un nouveau QR code de profil
- La date d'expiration est clairement indiquée sur la page de génération du QR code

## Pour les administrateurs de club

### Générer des QR codes pour vos pratiquants

En tant qu'administrateur de club, vous pouvez générer des QR codes de profil hors-ligne pour les pratiquants de votre club :

1. Accédez à la section "Pratiquants" dans le tableau de bord de votre club
2. Sélectionnez le pratiquant pour lequel vous souhaitez générer un QR code
3. Cliquez sur "QR Code" puis sur "Profil hors-ligne"
4. Imprimez ou partagez ce QR code avec le pratiquant

### Vérification des profils

Pour vérifier un profil hors-ligne :

1. Accédez à la section "Scanner" dans le menu principal
2. Sélectionnez "Vérifier un profil hors-ligne"
3. Scannez le QR code du pratiquant ou saisissez manuellement le token
4. Le système vérifiera l'authenticité du profil et affichera les informations du pratiquant

## Pour les organisateurs d'événements

### Préparation avant l'événement

1. Assurez-vous que tous les participants ont généré leur QR code de profil hors-ligne
2. Téléchargez l'application mobile MartialComp pour la vérification hors-ligne
3. Testez le système de vérification avant l'événement

### Pendant l'événement

1. Utilisez l'application mobile en mode hors-ligne pour scanner les QR codes
2. Vérifiez les informations affichées, notamment :
   - Identité du pratiquant
   - Club d'appartenance
   - Grade actuel
   - Licence et validité du certificat médical
3. Marquez les présences directement dans l'application, qui se synchronisera lorsque la connexion internet sera rétablie

## Questions fréquentes

**Q: Combien de temps mon profil hors-ligne reste-t-il valide ?**  
R: Le profil hors-ligne est valable pendant 30 jours après sa génération.

**Q: Que faire si mon QR code ne fonctionne pas ?**  
R: Vérifiez que le QR code n'est pas endommagé et qu'il n'a pas expiré. Si le problème persiste, générez un nouveau QR code.

**Q: Les informations sont-elles sécurisées ?**  
R: Oui, toutes les informations de profil sont cryptées avec une signature numérique sécurisée qui garantit leur authenticité.

**Q: Puis-je utiliser un ancien QR code ?**  
R: Non, après la date d'expiration, le QR code ne sera plus reconnu comme valide par le système.

**Q: Que se passe-t-il si mes informations changent après avoir généré le QR code ?**  
R: Le QR code contient les informations au moment de sa génération. Si vos informations changent significativement (grade, club, etc.), il est recommandé de générer un nouveau QR code.

## Résolution des problèmes

### Le QR code ne peut pas être scanné

- Assurez-vous que l'éclairage est suffisant
- Vérifiez que le QR code n'est pas endommagé ou plié
- Essayez de scanner à une distance optimale (15-20 cm)

### Message "Token expiré"

- Le profil a dépassé sa période de validité de 30 jours
- Générez un nouveau QR code de profil hors-ligne

### Message "Signature invalide"

- Le QR code ou le token a peut-être été altéré
- Régénérez un nouveau QR code de profil

### Impossible de générer un QR code

- Vérifiez votre connexion internet au moment de la génération
- Assurez-vous que votre profil est complet avec toutes les informations requises
- Contactez l'administrateur de votre club si le problème persiste

---

## Informations techniques (pour les développeurs)

### Structure du token de profil

Le token de profil hors-ligne est structuré comme suit :

```json
{
  "prac_id": 123,                           // ID du pratiquant
  "first_name": "John",                     // Prénom
  "last_name": "Doe",                       // Nom
  "birth_date": "1990-01-01",               // Date de naissance
  "nationality": "French",                  // Nationalité
  "license_number": "ABC123",               // Numéro de licence
  "club": {                                 // Informations du club
    "id": 456,
    "name": "Club Name"
  },
  "grade": "Ceinture Noire 1er Dan",        // Grade actuel
  "disciplines": [                          // Disciplines pratiquées
    {"id": 1, "name": "Karate"},
    {"id": 2, "name": "Judo"}
  ],
  "primary_discipline": {                   // Discipline principale
    "id": 1,
    "name": "Karate"
  },
  "is_coach": false,                        // Si le pratiquant est coach
  "medical_certificate_date": "2023-02-15", // Date du certificat médical
  "membership_end_date": "2024-12-31",      // Date de fin d'adhésion
  "iat": 1620000000,                        // Date d'émission (timestamp)
  "exp": 1622000000,                        // Date d'expiration (timestamp)
  "jti": "uuid-token-id",                   // Identifiant unique du token
  "sig": "hash-signature"                   // Signature de sécurité
}
```

### Processus de vérification

1. Le token est décodé depuis le QR code
2. La signature est vérifiée pour garantir l'authenticité
3. La date d'expiration est vérifiée pour s'assurer que le profil est toujours valide
4. Les informations sont affichées à l'utilisateur

Pour plus d'informations techniques, consultez la documentation du code source dans `competitions/utils/qr_offline.py`.