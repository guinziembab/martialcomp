# Améliorations de la lisibilité de l'interface de combat

## 🎨 Changements appliqués

### 1. **Colonne Rouge**
- Tout le texte est maintenant en blanc (#ffffff) pour un contraste optimal
- Les scores ont une ombre portée pour améliorer la lisibilité
- Les boutons conservent leurs couleurs (vert/jaune) avec des ombres pour mieux ressortir
- Les indicateurs de pénalité ont un fond semi-transparent blanc

### 2. **Colonne Blanc**
- Le texte reste en noir (#212529) pour un bon contraste
- Les boutons ont une bordure légère pour mieux se distinguer
- Les indicateurs de pénalité ont un fond gris clair

### 3. **Styles globaux améliorés**
- Taille de police ajustée pour les labels des boutons
- Espacement optimisé entre le label et la valeur
- Animations conservées pour le feedback visuel

## 📝 CSS ajouté

```css
/* Force le texte blanc dans la colonne rouge */
.fighter-column.rouge {
    color: #ffffff;
}

.fighter-column.rouge * {
    color: #ffffff;
}

/* Styles spécifiques pour améliorer la lisibilité */
.fighter-column.rouge .score-button div {
    color: #ffffff !important;
}

.fighter-column.rouge .score-number {
    color: #ffffff !important;
    text-shadow: 0 0 30px rgba(0,0,0,0.3);
}

/* Boutons avec meilleur contraste */
.fighter-column.rouge .score-button {
    box-shadow: 0 2px 10px rgba(0,0,0,0.3);
}
```

## ✅ Résultat

- Les labels des points et pénalités sont maintenant parfaitement lisibles sur le fond rouge
- L'interface conserve son aspect professionnel avec un meilleur contraste
- Les animations et interactions restent fluides

## 🔧 Si d'autres ajustements sont nécessaires

Pour modifier les couleurs ou le contraste :
1. Éditer le fichier `interface_combat_v2.html`
2. Ajuster les valeurs de couleur dans la section CSS
3. Rafraîchir la page pour voir les changements

Les points critiques pour la lisibilité sont :
- `.fighter-column.rouge` : couleur du texte principal
- `.score-button` : style des boutons de score
- `.penalty-indicator` : affichage des pénalités
- `.stat-value` et `.stat-label` : statistiques en bas