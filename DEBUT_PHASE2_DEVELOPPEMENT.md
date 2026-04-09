# DÉBUT PHASE 2 - DÉVELOPPEMENT

**Date de démarrage :** 3 novembre 2025  
**Objectif :** Démarrer le développement de la Phase 2  
**Statut :** 🟡 En cours

---

## 📊 VUE D'ENSEMBLE

### Tâches à démarrer

| ID | Tâche | Priorité | Durée | Statut |
|----|-------|----------|-------|--------|
| `consolidation-3` | Système de scoring unifié | 🔴 Haute | 10-15 jours | 🟡 En cours |
| `notifications-1` | Système de notifications automatiques | 🔴 Haute | 5-7 jours | ⏸️ En attente |
| `notifications-2` | Emails avec liens directs | 🔴 Haute | 4-5 jours | ⏸️ En attente |

---

## 🎯 STRATÉGIE D'EXÉCUTION

**Approche :** Séquentiel avec priorité sur `consolidation-3`

1. **Démarrer `consolidation-3`** (Système unifié) - **EN COURS**
   - Base fondamentale pour tout le reste
   - Permet d'intégrer les notifications dans le système unifié
   - Commencer par les modèles (Étape 1)

2. **Puis démarrer `notifications-1`** (en partie en parallèle si possible)
   - Peut utiliser le système unifié pour intégration
   - Amélioration immédiate de l'UX
   - Durée plus courte (5-7 jours)

3. **Enfin `notifications-2`** (Emails)
   - Dépend de `notifications-1` pour la base
   - Complète le système de notifications

---

## 🔨 CONSOLIDATION-3 : SYSTÈME DE SCORING UNIFIÉ

### Étape 1 : Création des modèles unifiés (EN COURS)

**Objectif :** Créer les modèles de données unifiés qui intègrent toutes les fonctionnalités des 3 systèmes.

**Fonctionnalités à intégrer :**
- Types de systèmes multiples (STANDARD, POINT, DIRECT_ELIMINATION, CUSTOM) - **Depuis Standalone**
- Système de rounds (preliminary, semifinal, final) - **Depuis Standalone**
- Configuration par catégorie avec overrides - **Depuis Standalone**
- Critères avec ordre d'affichage (drag & drop) - **Depuis Management**
- Snapshots de classements - **Depuis Standalone**
- Isolation organisationnelle - **Depuis Standalone**

**Fichier à créer :** `apps/competitions/models/unified_scoring_v2.py`

---

## 📧 NOTIFICATIONS-1 : SYSTÈME DE NOTIFICATIONS (EN ATTENTE)

**Objectif :** Créer un système de notifications automatiques lors de l'assignation de juges.

**Prérequis :** Compréhension du modèle `JudgeAssignment` ✅ (fait)

**Fichiers à créer :**
- `apps/competitions/models/notifications.py` - Modèle JudgeAssignmentNotification
- `apps/competitions/signals.py` - Signal pour créer notification automatiquement
- `apps/competitions/services/notification_service.py` - Service de gestion

---

## 📨 NOTIFICATIONS-2 : EMAILS AVEC LIENS (EN ATTENTE)

**Objectif :** Implémenter l'envoi d'emails automatiques avec liens directs vers les templates.

**Prérequis :** `notifications-1` en cours ou terminé

**Fichiers à créer :**
- `apps/competitions/services/email_service.py` - Service d'envoi
- `apps/competitions/templates/emails/judge_assignment.html` - Template email

---

## 🚀 PROCHAINES ÉTAPES

1. **Maintenant :** Créer les modèles unifiés (`unified_scoring_v2.py`)
2. **Puis :** Créer les migrations
3. **Ensuite :** Créer le calculateur unifié
4. **Puis :** Créer les vues backend
5. **Enfin :** Créer les templates

---

**Dernière mise à jour :** 3 novembre 2025  
**Statut :** 🟡 Démarrage de `consolidation-3` - Étape 1 : Modèles
