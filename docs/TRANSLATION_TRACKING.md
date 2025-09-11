
# SUIVI DES TRADUCTIONS MARTIALCOMP

## Delta de Traduction - État au $(date)

### Méthode de Calcul
- Analyse automatique de tous les templates HTML
- Détection des textes français avec accents/mots-clés
- Comparaison avec les balises {% trans %} existantes
- Calcul du pourcentage réel de couverture

### Commandes de Suivi

```bash
# Audit complet
python scripts/translation_audit.py

# Suivi continu
python manage.py translation_delta --language en

# Test de régression
python manage.py test_translations --all-languages
```

### Objectifs par Phase

#### Phase 1 (Semaine 1) - Objectif: 40%
- [ ] Traduction complète welcome.html
- [ ] Formulaires d'authentification
- [ ] Navigation principale

#### Phase 2 (Semaine 2) - Objectif: 70% 
- [ ] Dashboards coach/manager
- [ ] Menus et sidebars
- [ ] Messages d'erreur

#### Phase 3 (Semaine 3) - Objectif: 90%
- [ ] Templates secondaires
- [ ] Help text et tooltips
- [ ] Footer et pages légales

#### Phase 4 (Semaine 4) - Objectif: 95%+
- [ ] Contenu dynamique
- [ ] Meta descriptions
- [ ] Tests exhaustifs

### Suivi Automatisé

Le script `translation_audit.py` doit être exécuté quotidiennement pour suivre les progrès.
