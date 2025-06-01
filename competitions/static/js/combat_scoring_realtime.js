/**
 * Script pour la mise à jour en temps réel des données de scoring combat
 * Ce script utilise des appels AJAX pour récupérer les informations sur les combats en cours
 */

class CombatScoringRealtime {
    constructor(options) {
        this.options = Object.assign({
            refreshInterval: 2000, // Intervalle de rafraîchissement en ms
            matchStatusUrl: null,
            poolMatchesUrl: null,
            csrfToken: null,
            actionUrl: null
        }, options);
        
        this.intervalId = null;
        this.matchData = null;
    }
    
    /**
     * Démarre la mise à jour automatique de l'état d'un combat
     * @param {number} matchId - ID du combat à surveiller
     * @param {function} callback - Fonction de rappel avec les données reçues
     */
    startMatchMonitoring(matchId, callback) {
        if (!this.options.matchStatusUrl) {
            console.error('URL de statut de combat non définie');
            return;
        }
        
        // Construire l'URL avec l'ID du combat
        const url = this.options.matchStatusUrl.replace('__ID__', matchId);
        
        // Arrêter tout intervalle existant
        this.stopMonitoring();
        
        // Fonction de requête
        const fetchStatus = () => {
            fetch(url, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': this.options.csrfToken,
                    'Content-Type': 'application/json'
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Erreur réseau');
                }
                return response.json();
            })
            .then(data => {
                this.matchData = data;
                if (typeof callback === 'function') {
                    callback(data);
                }
            })
            .catch(error => {
                console.error('Erreur lors de la récupération du statut:', error);
            });
        };
        
        // Exécuter immédiatement une première fois
        fetchStatus();
        
        // Puis démarrer l'intervalle
        this.intervalId = setInterval(fetchStatus, this.options.refreshInterval);
    }
    
    /**
     * Démarre la mise à jour automatique des combats d'une poule
     * @param {number} poolId - ID de la poule à surveiller
     * @param {function} callback - Fonction de rappel avec les données reçues
     */
    startPoolMonitoring(poolId, callback) {
        if (!this.options.poolMatchesUrl) {
            console.error('URL des combats de poule non définie');
            return;
        }
        
        // Construire l'URL avec l'ID de la poule
        const url = this.options.poolMatchesUrl.replace('__ID__', poolId);
        
        // Arrêter tout intervalle existant
        this.stopMonitoring();
        
        // Fonction de requête
        const fetchMatches = () => {
            fetch(url, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': this.options.csrfToken,
                    'Content-Type': 'application/json'
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Erreur réseau');
                }
                return response.json();
            })
            .then(data => {
                if (typeof callback === 'function') {
                    callback(data);
                }
            })
            .catch(error => {
                console.error('Erreur lors de la récupération des combats:', error);
            });
        };
        
        // Exécuter immédiatement une première fois
        fetchMatches();
        
        // Puis démarrer l'intervalle
        this.intervalId = setInterval(fetchMatches, this.options.refreshInterval);
    }
    
    /**
     * Envoie une action pour un combat
     * @param {number} matchId - ID du combat
     * @param {string} actionType - Type d'action (point, warning, penalty, etc.)
     * @param {string} team - Équipe concernée (red, blue)
     * @param {number} points - Nombre de points (peut être négatif pour les pénalités)
     * @param {function} callback - Fonction de rappel avec les données reçues
     */
    sendAction(matchId, actionType, team, points, callback) {
        if (!this.options.actionUrl) {
            console.error('URL d\'action non définie');
            return;
        }
        
        const url = this.options.actionUrl.replace('__ID__', matchId);
        
        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.options.csrfToken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action_type: actionType,
                team: team,
                points: points
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Erreur réseau');
            }
            return response.json();
        })
        .then(data => {
            if (typeof callback === 'function') {
                callback(data);
            }
        })
        .catch(error => {
            console.error('Erreur lors de l\'envoi de l\'action:', error);
        });
    }
    
    /**
     * Arrête toute surveillance en cours
     */
    stopMonitoring() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }
}

// Singleton pour utilisation globale
const combatRealtime = new CombatScoringRealtime({
    // Les options seront définies dans le HTML
});

// Fonctions d'aide pour mettre à jour l'interface

/**
 * Met à jour l'affichage du score d'un combat
 * @param {object} matchData - Données du combat
 */
function updateMatchScore(matchData) {
    // Mettre à jour le score rouge
    const redScoreElement = document.getElementById('score-red');
    if (redScoreElement) {
        redScoreElement.textContent = matchData.score_red;
    }
    
    // Mettre à jour le score bleu
    const blueScoreElement = document.getElementById('score-blue');
    if (blueScoreElement) {
        blueScoreElement.textContent = matchData.score_blue;
    }
    
    // Mettre à jour le temps écoulé
    const timeElement = document.getElementById('match-time');
    if (timeElement && matchData.elapsed_time) {
        timeElement.textContent = formatTime(matchData.elapsed_time);
    }
    
    // Mettre à jour l'état du combat
    const statusElement = document.getElementById('match-status');
    if (statusElement) {
        statusElement.textContent = getStatusText(matchData.status);
        
        // Mettre à jour les classes CSS
        statusElement.classList.remove('status-pending', 'status-in-progress', 'status-completed', 'status-cancelled');
        statusElement.classList.add(`status-${matchData.status}`);
    }
    
    // Mettre à jour la liste des actions
    updateActionsList(matchData.actions);
}

/**
 * Met à jour la liste des actions d'un combat
 * @param {Array} actions - Liste des actions du combat
 */
function updateActionsList(actions) {
    const actionsContainer = document.getElementById('actions-list');
    if (!actionsContainer) return;
    
    // Vider le conteneur
    actionsContainer.innerHTML = '';
    
    // Trier les actions par date (la plus récente en premier)
    const sortedActions = actions.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    
    // Ajouter chaque action
    sortedActions.forEach(action => {
        const actionItem = document.createElement('div');
        actionItem.className = `action-item action-${action.action_type} team-${action.team}`;
        
        const actionTime = new Date(action.timestamp);
        const timeStr = `${actionTime.getHours().toString().padStart(2, '0')}:${actionTime.getMinutes().toString().padStart(2, '0')}:${actionTime.getSeconds().toString().padStart(2, '0')}`;
        
        actionItem.innerHTML = `
            <span class="action-time">${timeStr}</span>
            <span class="action-type">${getActionTypeText(action.action_type)}</span>
            <span class="action-team">${action.team === 'red' ? 'Rouge' : 'Bleu'}</span>
            <span class="action-points">${action.points > 0 ? '+' : ''}${action.points}</span>
        `;
        
        actionsContainer.appendChild(actionItem);
    });
}

/**
 * Formate le temps en mm:ss
 * @param {number} seconds - Temps en secondes
 * @returns {string} - Temps formaté
 */
function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Retourne le texte correspondant à un statut
 * @param {string} status - Statut du combat
 * @returns {string} - Texte du statut
 */
function getStatusText(status) {
    switch (status) {
        case 'pending': return 'En attente';
        case 'in_progress': return 'En cours';
        case 'completed': return 'Terminé';
        case 'cancelled': return 'Annulé';
        default: return status;
    }
}

/**
 * Retourne le texte correspondant à un type d'action
 * @param {string} actionType - Type d'action
 * @returns {string} - Texte du type d'action
 */
function getActionTypeText(actionType) {
    switch (actionType) {
        case 'point': return 'Point';
        case 'warning': return 'Avertissement';
        case 'penalty': return 'Pénalité';
        case 'disqualification': return 'Disqualification';
        default: return actionType;
    }
}