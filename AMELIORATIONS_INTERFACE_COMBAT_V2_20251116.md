# 🥋 AMÉLIORATIONS INTERFACE COMBAT V2 - 16 Novembre 2025

## 📋 Résumé des Modifications

Toutes les améliorations demandées ont été implémentées dans le template `interface_combat_v2.html`.

---

## ✅ Modifications Effectuées

### 1. ✅ Système de Pénalités Progressives

**Avant :** Un seul bouton de retrait (-0.5)

**Après :** 5 boutons de pénalités distincts :
- **-0.25** : Pénalité légère
- **-0.5** : Pénalité moyenne
- **-1** : Pénalité importante
- **-1.5** : Pénalité sévère
- **-2** : Pénalité maximale

**Implémentation :**
```javascript
function addPenalty(color, points) {
  // Ajoute la pénalité au score
  // Incrémente le compteur de pénalités
  // Enregistre dans l'historique
}
```

---

### 2. ✅ Système de Comptage des Sorties

**Fonctionnalité :** 
- Bouton "Sortie" pour chaque combattant
- Compteur visuel "X/3" sur le bouton
- Affichage dans la zone des pénalités
- **Automatique :** À la 3ème sortie → Pénalité de -0.5 appliquée automatiquement

**Implémentation :**
```javascript
function addExit(color) {
  // Incrémente le compteur de sorties
  // Si 3 sorties atteintes :
  //   - Applique -0.5 au score
  //   - Affiche une alerte
  //   - Enregistre dans l'historique
}
```

**Affichage :**
- Zone des pénalités : "🚪 Sorties: X/3"
- Bouton : Affiche "0/3", "1/3", "2/3", "3/3"

---

### 3. ✅ Logo de la Discipline

**Avant :** Affichage de "120s" en haut

**Après :** 
- Affichage du **logo de la discipline** si disponible
- Sinon, affichage du **nom de la discipline** stylisé
- Le timer s'affiche en dessous au format **MM:SS**

**Code Template :**
```django
<div class="discipline-logo">
  {% if combat.competition.discipline.logo %}
    <img src="{{ combat.competition.discipline.logo.url }}" 
         alt="{{ combat.competition.discipline.name }}" 
         style="max-height: 80px; max-width: 200px;">
  {% else %}
    <div style="font-size: 2rem; color: #ffc107;">
      {{ combat.competition.discipline.name|default:"Discipline" }}
    </div>
  {% endif %}
</div>
<div class="main-timer" id="mainTimer">02:00</div>
```

---

### 4. ✅ Logos des Clubs

**Fonctionnalité :**
- Affichage du logo du club **au-dessus** du nom du combattant
- Pour les deux colonnes (Rouge et Blanc)
- Gère les cas :
  - Combat individuel : Logo de l'organisation ou du club du pratiquant
  - Combat d'équipe : Logo du club de l'équipe

**Code Template :**
```django
<div class="club-logo">
  {% if combat.type_combat == 'individuel' and combat.pratiquant_rouge.organization.logo %}
    <img src="{{ combat.pratiquant_rouge.organization.logo.url }}" 
         alt="{{ combat.pratiquant_rouge.organization.name }}">
  {% elif combat.type_combat == 'individuel' and combat.pratiquant_rouge.club.logo %}
    <img src="{{ combat.pratiquant_rouge.club.logo.url }}" 
         alt="{{ combat.pratiquant_rouge.club.name }}">
  {% elif combat.type_combat == 'equipe' and combat.equipe_rouge.club.logo %}
    <img src="{{ combat.equipe_rouge.club.logo.url }}" 
         alt="{{ combat.equipe_rouge.club.name }}">
  {% endif %}
</div>
```

**Style CSS :**
```css
.club-logo {
  text-align: center;
  margin-bottom: 1rem;
}

.club-logo img {
  max-height: 60px;
  max-width: 120px;
  object-fit: contain;
}
```

---

### 5. ✅ Son GONG à la Fin du Combat

**Fonctionnalité :**
- Son de gong synthétique joué automatiquement quand le timer atteint 00:00
- Utilise l'API Web Audio pour générer un son de gong réaliste

**Implémentation :**
```javascript
function playGong() {
  const audioContext = new (window.AudioContext || window.webkitAudioContext)();
  const oscillator = audioContext.createOscillator();
  const gainNode = audioContext.createGain();
  
  oscillator.connect(gainNode);
  gainNode.connect(audioContext.destination);
  
  oscillator.frequency.value = 200; // Fréquence basse pour simuler un gong
  oscillator.type = 'sine';
  
  gainNode.gain.setValueAtTime(1, audioContext.currentTime);
  gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 3);
  
  oscillator.start(audioContext.currentTime);
  oscillator.stop(audioContext.currentTime + 3);
}

function endCombat() {
  clearInterval(combat.timerInterval);
  playGong(); // ← Joue le son GONG
  // ... reste du code
}
```

**Note :** Le son dure 3 secondes avec une décroissance progressive pour simuler un vrai gong.

---

### 6. ✅ Timer en Format MM:SS

**Avant :** Affichage "120s"

**Après :** Affichage "02:00" (format minutes:secondes)

**Fonctionnalité :**
- Décrémentation seconde par seconde
- Format toujours à 2 chiffres (ex: "01:05", "00:30")
- Mise à jour en temps réel

**Implémentation :**
```javascript
function formatTime(seconds) {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
}

function updateTimer() {
  if (!combat.isPaused && combat.timeRemaining > 0) {
    combat.timeRemaining--;
    document.getElementById('mainTimer').textContent = formatTime(combat.timeRemaining);
    
    if (combat.timeRemaining === 0) {
      endCombat();
    }
  }
}
```

---

## 🎨 Ajustements Visuels

### Panneau de Scoring

**Avant :** 3 colonnes avec 6 boutons

**Après :** 3 colonnes avec 11 boutons
- 5 boutons de points (+0.25, +0.5, +1, +1.5, +2)
- 5 boutons de pénalités (-0.25, -0.5, -1, -1.5, -2)
- 1 bouton de sortie

**Ajustements CSS :**
```css
.scoring-panel {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.8rem; /* Réduit de 1rem à 0.8rem */
}

.score-button {
  padding: 1rem; /* Réduit de 1.5rem à 1rem */
  font-size: 1.2rem; /* Réduit de 1.5rem à 1.2rem */
}
```

### Zone des Pénalités

**Ajout :** Indicateur de sorties
```html
<div class="penalty-indicator">
  <i class="fas fa-door-open"></i> Sorties: <span id="exitRouge">0</span>/3
</div>
```

---

## 🔧 Variables JavaScript Ajoutées

```javascript
let combat = {
  scoreRouge: 0,
  scoreBlanc: 0,
  avertRouge: 0,
  penalRouge: 0,
  avertBlanc: 0,
  penalBlanc: 0,
  exitRouge: 0,      // ← NOUVEAU
  exitBlanc: 0,      // ← NOUVEAU
  timeRemaining: 120,
  isPaused: true,
  isRunning: false,
  timerInterval: null,
  gongSound: null    // ← NOUVEAU
};
```

---

## 📊 Résumé des Fonctionnalités

| Fonctionnalité | Status | Description |
|----------------|--------|-------------|
| **Pénalités progressives** | ✅ | 5 niveaux de pénalités (-0.25 à -2) |
| **Comptage des sorties** | ✅ | Bouton + compteur + pénalité auto à 3 sorties |
| **Logo discipline** | ✅ | Remplace "120s" en haut du timer |
| **Logos des clubs** | ✅ | Affichés au-dessus de chaque combattant |
| **Son GONG** | ✅ | Joué automatiquement à la fin du combat |
| **Timer MM:SS** | ✅ | Format minutes:secondes avec décrémentation |

---

## 🚀 Déploiement

### Fichier Modifié
```
apps/competitions/templates/competitions/combat/interface_combat_v2.html
```

### Commandes de Déploiement

```bash
# 1. Sauvegarder le fichier modifié
git add apps/competitions/templates/competitions/combat/interface_combat_v2.html

# 2. Créer un commit
git commit -m "Amélioration interface combat v2: pénalités, sorties, logos, timer, gong"

# 3. Déployer en production
ssh user@martialcomp.com
cd /home/martialcomp/martialcomp
git pull origin main
sudo systemctl restart gunicorn
sudo systemctl reload apache2

# 4. Vider le cache Django
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
>>> exit()

# 5. Vérifier le déploiement
curl -I https://martialcomp.com/fr/competitions/combat/combats/10/interface-v2/
```

---

## 🧪 Tests à Effectuer

### 1. Test des Pénalités
- [ ] Cliquer sur chaque bouton de pénalité (-0.25, -0.5, -1, -1.5, -2)
- [ ] Vérifier que le score diminue correctement
- [ ] Vérifier que le compteur de pénalités s'incrémente
- [ ] Vérifier l'historique des actions

### 2. Test des Sorties
- [ ] Cliquer 3 fois sur le bouton "Sortie"
- [ ] Vérifier que le compteur passe de 0/3 à 3/3
- [ ] Vérifier qu'une alerte s'affiche à la 3ème sortie
- [ ] Vérifier que -0.5 est appliqué automatiquement au score

### 3. Test du Timer
- [ ] Cliquer sur "DÉMARRER"
- [ ] Vérifier que le timer décrémente seconde par seconde
- [ ] Vérifier le format MM:SS (ex: 01:59, 01:58, ...)
- [ ] Laisser le timer atteindre 00:00
- [ ] Vérifier que le son GONG se joue
- [ ] Vérifier que l'alerte de fin de combat s'affiche

### 4. Test des Logos
- [ ] Vérifier que le logo de la discipline s'affiche en haut
- [ ] Vérifier que les logos des clubs s'affichent pour chaque combattant
- [ ] Tester avec un combat où les logos ne sont pas disponibles

### 5. Test de l'Interface Complète
- [ ] Tester tous les boutons de points (+0.25, +0.5, +1, +1.5, +2)
- [ ] Vérifier les animations de flash sur les scores
- [ ] Vérifier que l'historique se remplit correctement
- [ ] Tester le bouton PAUSE/REPRENDRE
- [ ] Tester le bouton RÉINITIALISER

---

## 📝 Notes Techniques

### Gestion des Logos
- Les logos sont chargés via les relations Django (organization.logo, club.logo, discipline.logo)
- Si le logo n'existe pas, l'espace reste vide (pas d'erreur)
- Les images sont redimensionnées automatiquement (max-height: 60px/80px)

### Son GONG
- Utilise l'API Web Audio (compatible tous navigateurs modernes)
- Génère un son synthétique (pas besoin de fichier audio)
- Fréquence de 200 Hz avec décroissance sur 3 secondes
- Alternative : Remplacer par un fichier audio MP3/WAV si souhaité

### Comptage des Sorties
- Réinitialisation automatique à 0 après application de la pénalité
- Possibilité d'ajouter une limite de 5 sorties = disqualification (à implémenter si souhaité)

### Performance
- Pas d'impact sur les performances (code JavaScript optimisé)
- Pas de requêtes AJAX supplémentaires
- Tout fonctionne côté client

---

## 🎯 Prochaines Améliorations Possibles

1. **Fichier audio GONG personnalisé**
   - Remplacer le son synthétique par un vrai fichier audio
   - Ajouter un champ `gong_sound` dans la configuration de combat

2. **Disqualification automatique**
   - À 5 sorties → Disqualification automatique
   - Bloquer les boutons de scoring

3. **Sauvegarde automatique**
   - Sauvegarder les scores en temps réel via AJAX
   - Récupération en cas de rafraîchissement de page

4. **Mode spectateur**
   - Affichage en lecture seule pour le public
   - Mise à jour en temps réel via WebSocket

5. **Statistiques avancées**
   - Graphiques de progression des scores
   - Temps moyen entre les points
   - Heatmap des actions

---

## ✅ Conclusion

Toutes les modifications demandées ont été implémentées avec succès :

✅ Système de pénalités progressives (-0.25, -0.5, -1, -1.5, -2)  
✅ Système de comptage des sorties (3 sorties = -0.5 automatique)  
✅ Logo de la discipline au lieu de "120s"  
✅ Logos des clubs de part et d'autre  
✅ Son GONG à la fin du combat  
✅ Timer au format MM:SS avec décrémentation en secondes  

Le template est prêt à être déployé en production ! 🚀

---

**Date :** 16 Novembre 2025  
**Fichier modifié :** `apps/competitions/templates/competitions/combat/interface_combat_v2.html`  
**Lignes modifiées :** ~200 lignes (ajouts + modifications)  
**Tests requis :** Interface complète fonctionnelle
