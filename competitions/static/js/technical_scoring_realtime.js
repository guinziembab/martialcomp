/**
 * Script pour la mise à jour en temps réel des données de notation technique
 * Ce script utilise des appels AJAX pour récupérer les informations sur les performances en cours
 */

class TechnicalScoringRealtime {
    constructor(options) {
        this.options = Object.assign({
            refreshInterval: 5000, // Intervalle de rafraîchissement en ms
            performanceStatusUrl: null,
            categoryPerformancesUrl: null,
            csrfToken: null
        }, options);
        
        this.intervalId = null;
    }
    
    /**
     * Démarre la mise à jour automatique de l'état d'une performance
     * @param {number} performanceId - ID de la performance à surveiller
     * @param {function} callback - Fonction de rappel avec les données reçues
     */
    startPerformanceMonitoring(performanceId, callback) {
        if (!this.options.performanceStatusUrl) {
            console.error('URL de statut de performance non définie');
            return;
        }
        
        // Construire l'URL avec l'ID de la performance
        const url = this.options.performanceStatusUrl.replace('__ID__', performanceId);
        
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
     * Démarre la mise à jour automatique des performances d'une catégorie
     * @param {number} categoryId - ID de la catégorie à surveiller
     * @param {function} callback - Fonction de rappel avec les données reçues
     */
    startCategoryMonitoring(categoryId, callback) {
        if (!this.options.categoryPerformancesUrl) {
            console.error('URL des performances de catégorie non définie');
            return;
        }
        
        // Construire l'URL avec l'ID de la catégorie
        const url = this.options.categoryPerformancesUrl.replace('__ID__', categoryId);
        
        // Arrêter tout intervalle existant
        this.stopMonitoring();
        
        // Fonction de requête
        const fetchPerformances = () => {
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
                console.error('Erreur lors de la récupération des performances:', error);
            });
        };
        
        // Exécuter immédiatement une première fois
        fetchPerformances();
        
        // Puis démarrer l'intervalle
        this.intervalId = setInterval(fetchPerformances, this.options.refreshInterval);
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
const scoringRealtime = new TechnicalScoringRealtime({
    // Les options seront définies dans le HTML
});

// Fonctions d'aide pour mettre à jour l'interface

/**
 * Met à jour l'affichage du statut d'un juge
 * @param {object} judgeData - Données du juge
 * @param {string} elementSelector - Sélecteur CSS de l'élément à mettre à jour
 */
function updateJudgeStatus(judgeData, elementSelector) {
    const element = document.querySelector(elementSelector);
    if (!element) return;
    
    // Mise à jour de la classe CSS
    if (judgeData.has_submitted) {
        element.classList.add('submitted');
        element.classList.remove('pending');
    } else {
        element.classList.add('pending');
        element.classList.remove('submitted');
    }
    
    // Mise à jour du texte de statut si l'élément existe
    const statusText = element.querySelector('.status-text');
    if (statusText) {
        statusText.textContent = judgeData.has_submitted ? 'Soumis' : 'En attente';
    }
}

/**
 * Met à jour l'affichage du statut d'une performance
 * @param {object} performanceData - Données de la performance
 * @param {string} elementSelector - Sélecteur CSS de l'élément à mettre à jour
 */
function updatePerformanceStatus(performanceData, elementSelector) {
    const element = document.querySelector(elementSelector);
    if (!element) return;
    
    // Mise à jour de la classe CSS
    element.classList.remove('pending', 'in-progress', 'completed');
    element.classList.add(performanceData.status === 'pending' ? 'pending' : 
                          performanceData.status === 'in_progress' ? 'in-progress' : 'completed');
    
    // Mise à jour du texte de statut si l'élément existe
    const statusText = element.querySelector('.status-text');
    if (statusText) {
        statusText.textContent = performanceData.status === 'pending' ? 'En attente' : 
                               performanceData.status === 'in_progress' ? 'En cours' : 'Terminé';
    }
    
    // Si la performance est terminée, proposer de voir les résultats
    if (performanceData.is_completed) {
        const actionsContainer = element.querySelector('.actions-container');
        if (actionsContainer) {
            const existingLink = actionsContainer.querySelector('.results-link');
            if (!existingLink) {
                const resultsLink = document.createElement('a');
                resultsLink.href = `/technical-scoring/performance/${performanceData.id}/results/`;
                resultsLink.className = 'btn btn-primary results-link';
                resultsLink.innerHTML = '<i class="fas fa-chart-bar me-2"></i>Voir les résultats';
                actionsContainer.appendChild(resultsLink);
            }
        }
    }
}