# Kinovea - Integration avec MartialComp

## Contexte

Chaque aire de combat lors d'une competition dispose de cameras.
L'objectif est de pouvoir :
- Suivre les mouvements des pratiquants en temps reel
- Diffuser en direct sur les ecrans / le Cockpit
- Capturer des images cles (techniques, scores)
- Faire des ralentis pour l'arbitrage ou l'analyse technique

## Qu'est-ce que Kinovea ?

**Kinovea** est un logiciel open-source d'analyse video sportive.
- Site : https://www.kinovea.org/
- Licence : GPLv2 (gratuit)
- Plateforme : Windows
- Utilise par : clubs d'arts martiaux, federations de taekwondo, judo, karate

### Fonctionnalites cles

| Fonctionnalite | Description |
|---|---|
| Ralenti | Lecture a vitesse variable (0.1x a 8x) |
| Capture live | Connexion directe aux cameras (USB, IP, HDMI via capture card) |
| Dual video | Affichage cote a cote de 2 flux (2 angles ou comparaison) |
| Mesure d'angles | Overlay pour mesurer les angles des articulations |
| Chronometrage | Mesure du temps entre 2 instants (duree d'une technique) |
| Dessin sur video | Annotations en direct (fleches, cercles, texte) |
| Export | Capture d'images, export de sequences video |
| Trajectoires | Suivi automatique de points (tracking) |

## Architecture proposee par aire de combat

```
[Camera IP/USB]
      |
      v
[PC Aire de combat]
   - Kinovea (analyse video locale)
   - OBS Studio (optionnel, pour streaming)
      |
      v
[Reseau local competition]
      |
      +---> Ecran geant de l'aire (retransmission directe)
      +---> Serveur MartialComp (clips, captures)
      +---> Cockpit web (streaming live via WebRTC)
```

## Materiel requis par aire

| Element | Specification minimale | Cout estime |
|---|---|---|
| Camera | Camera IP 1080p ou webcam HD | 50-150 EUR |
| Capture card (si HDMI) | Elgato Cam Link ou equivalent | 100 EUR |
| PC | Windows 10/11, i5+, 8Go RAM | existant ou 400 EUR |
| Ecran | TV/moniteur pour affichage public | existant |
| Cable Ethernet | Cat5e/Cat6 pour reseau local | 10 EUR |

**Cout minimal par aire : ~60 EUR** (camera USB + logiciel gratuit)

## Cas d'utilisation concrets

### 1. Arbitrage assiste par video
- L'arbitre demande un replay
- L'operateur Kinovea fait un ralenti de la sequence
- Affichage sur l'ecran de l'aire
- Decision arbitrale confirmee

### 2. Analyse technique post-competition
- Enregistrement de tous les passages
- Les entraineurs recuperent les videos
- Analyse des angles, positions, timing avec Kinovea

### 3. Scoring technique (Quyen/Formes)
- Capture d'images aux moments cles (positions finales)
- Mesure des angles pour evaluation objective
- Comparaison cote a cote avec la technique de reference

### 4. Streaming vers le Cockpit MartialComp
- Kinovea capture le flux camera
- OBS Studio encode et streame via RTMP/WebRTC
- Le Cockpit MartialComp affiche le flux live de chaque aire

## Integration future avec MartialComp

### Phase 1 - Standalone (zero developpement)
- Installer Kinovea sur chaque PC d'aire
- Utilisation independante par les operateurs
- Pas de lien avec MartialComp

### Phase 2 - Export vers MartialComp
- Les clips/captures sont enregistres localement
- Apres la competition, upload dans MartialComp
- Association clip <-> combat/categorie/pratiquant
- Endpoint API : `POST /api/v1/competitions/{id}/media/`

### Phase 3 - Integration temps reel
- Streaming live integre dans le Cockpit
- Bouton "Replay" dans l'interface du juge
- Ralenti accessible depuis le navigateur
- Technologies : LiveKit (WebRTC) + Video.js (player)

### Phase 4 - Analyse automatique (ML)
- MediaPipe pour detection de pose
- Scoring automatique base sur les positions
- Detection automatique des techniques (coups de pied, blocages)
- Necessite GPU et entrainement de modele

## Cameras IP recommandees

### Budget reduit
- Logitech C920/C922 (USB, 1080p, ~70 EUR)
- TP-Link Tapo C200 (WiFi, 1080p, ~30 EUR)

### Qualite professionnelle
- Hikvision DS-2CD2143G2 (IP PoE, 4MP, ~150 EUR)
- Axis M3075-V (IP PoE, 1080p, grand angle, ~300 EUR)

### Conseil
- Privilegier les cameras IP PoE pour la fiabilite (pas de WiFi)
- Angle large (120°+) pour couvrir toute l'aire
- 2 cameras par aire idealement (face + profil)

## Liens utiles

- Kinovea - Site officiel : https://www.kinovea.org/
- Kinovea - Code source : https://github.com/Kinovea/Kinovea
- Kinovea - Manuel : https://www.kinovea.org/help/en/
- LiveKit (streaming) : https://livekit.io/
- MediaPipe (pose) : https://mediapipe.dev/
- OBS Studio (streaming) : https://obsproject.com/

## Notes

- Cette reflexion date de mars 2026
- Aucune implementation n'est prevue pour le moment
- La priorite est d'abord de finaliser le Cockpit et la gestion des competitions
- L'integration video sera envisagee apres la stabilisation de la plateforme
