/**
 * JavaScript pour la planification d'événements
 * Améliore l'expérience utilisateur pour les sondages et les rappels
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialisation pour les sondages de planification d'événements
    initPollVoting();
    initPollCharts();
    initPollActions();
    
    // Initialisation pour les rappels
    initReminderForms();
    
    // Initialisation des tooltips et popovers Bootstrap
    initBootstrapComponents();
});

/**
 * Initialise les interactions de vote pour les sondages
 */
function initPollVoting() {
    const pollResponses = document.querySelectorAll('.poll-response-option');
    
    // Gestion des clics sur les options de réponse
    pollResponses.forEach(option => {
        option.addEventListener('click', function(e) {
            e.preventDefault();
            
            const optionId = this.dataset.optionId;
            const response = this.dataset.response;
            const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
            
            // Mettre à jour visuellement l'option sélectionnée
            updateSelectedOption(this);
            
            // Envoyer la réponse via AJAX
            fetch(`/competitions/events/planning/poll-options/${optionId}/respond/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    response: response,
                    comment: ''  // Commentaire vide par défaut
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Mettre à jour les compteurs de votes
                    updateVoteCounts(optionId, data.stats);
                    // Afficher un message de succès
                    showNotification('Votre réponse a été enregistrée.', 'success');
                } else {
                    // Afficher un message d'erreur
                    showNotification(data.message || 'Une erreur est survenue lors de l\'enregistrement de votre réponse.', 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Une erreur de communication est survenue. Veuillez réessayer.', 'danger');
            });
        });
    });
    
    // Commentaires sur les options
    const commentButtons = document.querySelectorAll('.poll-option-comment-btn');
    commentButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const optionId = this.dataset.optionId;
            const commentForm = document.getElementById(`comment-form-${optionId}`);
            
            // Afficher/masquer le formulaire de commentaire
            if (commentForm.classList.contains('d-none')) {
                commentForm.classList.remove('d-none');
                this.innerHTML = '<i class="fas fa-times"></i> Annuler';
                this.classList.replace('btn-outline-secondary', 'btn-outline-danger');
            } else {
                commentForm.classList.add('d-none');
                this.innerHTML = '<i class="fas fa-comment"></i> Commenter';
                this.classList.replace('btn-outline-danger', 'btn-outline-secondary');
            }
        });
    });
    
    // Soumission des commentaires
    const commentForms = document.querySelectorAll('.poll-option-comment-form');
    commentForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const optionId = this.dataset.optionId;
            const commentInput = this.querySelector('textarea');
            const comment = commentInput.value.trim();
            const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
            
            // Récupérer la réponse actuelle
            const selectedOption = document.querySelector(`.poll-response-option[data-option-id="${optionId}"].selected`);
            const response = selectedOption ? selectedOption.dataset.response : 'yes';  // Par défaut 'yes' si rien n'est sélectionné
            
            // Envoyer la réponse avec le commentaire via AJAX
            fetch(`/competitions/events/planning/poll-options/${optionId}/respond/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    response: response,
                    comment: comment
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Vider le champ de commentaire et masquer le formulaire
                    commentInput.value = '';
                    form.classList.add('d-none');
                    
                    // Mettre à jour le bouton de commentaire
                    const commentButton = document.querySelector(`.poll-option-comment-btn[data-option-id="${optionId}"]`);
                    commentButton.innerHTML = '<i class="fas fa-comment"></i> Commenter';
                    commentButton.classList.replace('btn-outline-danger', 'btn-outline-secondary');
                    
                    // Afficher un message de succès
                    showNotification('Votre commentaire a été enregistré.', 'success');
                    
                    // Ajouter le commentaire à la liste des commentaires
                    updateCommentsList(optionId, comment);
                } else {
                    // Afficher un message d'erreur
                    showNotification(data.message || 'Une erreur est survenue lors de l\'enregistrement de votre commentaire.', 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Une erreur de communication est survenue. Veuillez réessayer.', 'danger');
            });
        });
    });
}

/**
 * Met à jour visuellement l'option sélectionnée
 */
function updateSelectedOption(selectedOption) {
    const optionId = selectedOption.dataset.optionId;
    const optionGroup = document.querySelectorAll(`.poll-response-option[data-option-id="${optionId}"]`);
    
    // Désélectionner toutes les options de ce groupe
    optionGroup.forEach(option => {
        option.classList.remove('selected');
    });
    
    // Sélectionner l'option cliquée
    selectedOption.classList.add('selected');
}

/**
 * Met à jour les compteurs de votes pour une option
 */
function updateVoteCounts(optionId, stats) {
    const yesCounter = document.getElementById(`yes-count-${optionId}`);
    const maybeCounter = document.getElementById(`maybe-count-${optionId}`);
    const noCounter = document.getElementById(`no-count-${optionId}`);
    const totalCounter = document.getElementById(`total-count-${optionId}`);
    
    if (yesCounter) yesCounter.textContent = stats.yes_votes;
    if (maybeCounter) maybeCounter.textContent = stats.maybe_votes;
    if (noCounter) noCounter.textContent = stats.no_votes;
    if (totalCounter) totalCounter.textContent = stats.total_votes;
    
    // Mettre à jour les barres de progression si elles existent
    updateProgressBars(optionId, stats);
}

/**
 * Met à jour les barres de progression pour une option
 */
function updateProgressBars(optionId, stats) {
    const yesBar = document.getElementById(`yes-bar-${optionId}`);
    const maybeBar = document.getElementById(`maybe-bar-${optionId}`);
    const noBar = document.getElementById(`no-bar-${optionId}`);
    
    const total = stats.total_votes || 1;  // Éviter la division par zéro
    
    if (yesBar) {
        const yesPercent = (stats.yes_votes / total * 100).toFixed(0);
        yesBar.style.width = `${yesPercent}%`;
        yesBar.setAttribute('aria-valuenow', yesPercent);
        yesBar.textContent = `${yesPercent}%`;
    }
    
    if (maybeBar) {
        const maybePercent = (stats.maybe_votes / total * 100).toFixed(0);
        maybeBar.style.width = `${maybePercent}%`;
        maybeBar.setAttribute('aria-valuenow', maybePercent);
        maybeBar.textContent = `${maybePercent}%`;
    }
    
    if (noBar) {
        const noPercent = (stats.no_votes / total * 100).toFixed(0);
        noBar.style.width = `${noPercent}%`;
        noBar.setAttribute('aria-valuenow', noPercent);
        noBar.textContent = `${noPercent}%`;
    }
}

/**
 * Ajoute un commentaire à la liste des commentaires
 */
function updateCommentsList(optionId, comment) {
    const commentsList = document.getElementById(`comments-list-${optionId}`);
    if (!commentsList) return;
    
    const currentUser = document.getElementById('current-user-name').value || 'Vous';
    const commentItem = document.createElement('div');
    commentItem.className = 'comment-item mb-2 border-bottom pb-2';
    commentItem.innerHTML = `
        <div class="d-flex justify-content-between">
            <strong>${currentUser}</strong>
            <small class="text-muted">à l'instant</small>
        </div>
        <p class="mb-1">${comment}</p>
    `;
    
    commentsList.appendChild(commentItem);
    
    // Si la liste était vide, supprimer le message "aucun commentaire"
    const noCommentsMessage = commentsList.querySelector('.no-comments');
    if (noCommentsMessage) {
        noCommentsMessage.remove();
    }
}

/**
 * Initialise les graphiques pour les résultats des sondages
 */
function initPollCharts() {
    // Vérifier si Chart.js est disponible
    if (typeof Chart === 'undefined') return;
    
    // Graphique de répartition des votes par option
    const votesChartCanvas = document.getElementById('votes-chart');
    if (votesChartCanvas) {
        // Récupérer les données du sondage
        const optionsData = JSON.parse(document.getElementById('poll-options-data').textContent);
        const labels = optionsData.map(option => option.date);
        const yesData = optionsData.map(option => option.yes_count);
        const maybeData = optionsData.map(option => option.maybe_count);
        const noData = optionsData.map(option => option.no_count);
        
        new Chart(votesChartCanvas, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Oui',
                        data: yesData,
                        backgroundColor: 'rgba(40, 167, 69, 0.7)',
                        borderColor: 'rgba(40, 167, 69, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'Peut-être',
                        data: maybeData,
                        backgroundColor: 'rgba(255, 193, 7, 0.7)',
                        borderColor: 'rgba(255, 193, 7, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'Non',
                        data: noData,
                        backgroundColor: 'rgba(220, 53, 69, 0.7)',
                        borderColor: 'rgba(220, 53, 69, 1)',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        stacked: true,
                        title: {
                            display: true,
                            text: 'Options de date'
                        }
                    },
                    y: {
                        stacked: true,
                        title: {
                            display: true,
                            text: 'Nombre de votes'
                        },
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    // Graphique de popularité des options (score)
    const scoreChartCanvas = document.getElementById('score-chart');
    if (scoreChartCanvas) {
        // Récupérer les données du sondage
        const optionsData = JSON.parse(document.getElementById('poll-options-data').textContent);
        const labels = optionsData.map(option => option.date);
        const scores = optionsData.map(option => option.score);
        
        new Chart(scoreChartCanvas, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Score',
                        data: scores,
                        backgroundColor: 'rgba(0, 123, 255, 0.7)',
                        borderColor: 'rgba(0, 123, 255, 1)',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Score (2 points par "Oui", 1 point par "Peut-être")'
                        }
                    }
                }
            }
        });
    }
}

/**
 * Initialise les actions pour les sondages (finalisation, annulation)
 */
function initPollActions() {
    // Finalisation d'un sondage
    const finalizeButtons = document.querySelectorAll('.finalize-poll-btn');
    finalizeButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const pollId = this.dataset.pollId;
            const optionId = this.dataset.optionId;
            const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
            
            // Confirmation
            if (!confirm('Êtes-vous sûr de vouloir finaliser ce sondage avec cette option ? Cette action est irréversible.')) {
                return;
            }
            
            // Envoyer la demande de finalisation via AJAX
            fetch(`/competitions/events/planning/polls/${pollId}/finalize/${optionId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification('Le sondage a été finalisé avec succès.', 'success');
                    
                    // Rediriger vers la page de l'événement créé ou du sondage
                    setTimeout(() => {
                        window.location.href = data.redirect_url;
                    }, 1500);
                } else {
                    showNotification(data.message || 'Une erreur est survenue lors de la finalisation du sondage.', 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Une erreur de communication est survenue. Veuillez réessayer.', 'danger');
            });
        });
    });
    
    // Annulation d'un sondage
    const cancelButtons = document.querySelectorAll('.cancel-poll-btn');
    cancelButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const pollId = this.dataset.pollId;
            const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
            
            // Confirmation
            if (!confirm('Êtes-vous sûr de vouloir annuler ce sondage ? Cette action est irréversible.')) {
                return;
            }
            
            // Envoyer la demande d'annulation via AJAX
            fetch(`/competitions/events/planning/polls/${pollId}/cancel/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification('Le sondage a été annulé avec succès.', 'success');
                    
                    // Actualiser la page
                    setTimeout(() => {
                        window.location.reload();
                    }, 1500);
                } else {
                    showNotification(data.message || 'Une erreur est survenue lors de l\'annulation du sondage.', 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Une erreur de communication est survenue. Veuillez réessayer.', 'danger');
            });
        });
    });
}

/**
 * Initialise les formulaires de rappels
 */
function initReminderForms() {
    // Champ de type de rappel
    const reminderTypeSelect = document.getElementById('id_reminder_type');
    if (reminderTypeSelect) {
        // Afficher/masquer les champs spécifiques selon le type de rappel
        reminderTypeSelect.addEventListener('change', function() {
            toggleReminderFields();
        });
        
        // Initialiser l'état des champs
        toggleReminderFields();
    }
    
    // Champ de méthode de planification
    const schedulingMethodRadios = document.querySelectorAll('input[name="scheduling_method"]');
    if (schedulingMethodRadios.length > 0) {
        schedulingMethodRadios.forEach(radio => {
            radio.addEventListener('change', function() {
                toggleSchedulingFields();
            });
        });
        
        // Initialiser l'état des champs
        toggleSchedulingFields();
    }
    
    // Champ de destinataires
    const sendToSelect = document.getElementById('id_send_to');
    if (sendToSelect) {
        // Afficher/masquer le sélecteur de destinataires personnalisés
        sendToSelect.addEventListener('change', function() {
            toggleRecipientsField();
        });
        
        // Initialiser l'état du champ
        toggleRecipientsField();
    }
}

/**
 * Affiche/masque les champs spécifiques selon le type de rappel
 */
function toggleReminderFields() {
    const reminderType = document.getElementById('id_reminder_type').value;
    
    // Champs spécifiques aux emails
    const emailFields = document.getElementById('email-specific-fields');
    if (emailFields) {
        emailFields.style.display = (reminderType === 'email' || reminderType === 'all') ? 'block' : 'none';
    }
    
    // Champs spécifiques aux SMS
    const smsFields = document.getElementById('sms-specific-fields');
    if (smsFields) {
        smsFields.style.display = (reminderType === 'sms' || reminderType === 'all') ? 'block' : 'none';
    }
    
    // Champs spécifiques aux notifications
    const notificationFields = document.getElementById('notification-specific-fields');
    if (notificationFields) {
        notificationFields.style.display = (reminderType === 'notification' || reminderType === 'all') ? 'block' : 'none';
    }
}

/**
 * Affiche/masque les champs de planification selon la méthode choisie
 */
function toggleSchedulingFields() {
    const schedulingMethod = document.querySelector('input[name="scheduling_method"]:checked').value;
    
    // Champ de date/heure spécifique
    const specificDateField = document.getElementById('specific-date-field');
    if (specificDateField) {
        specificDateField.style.display = (schedulingMethod === 'specific') ? 'block' : 'none';
    }
    
    // Champ de délai avant l'événement
    const timeBeforeField = document.getElementById('time-before-field');
    if (timeBeforeField) {
        timeBeforeField.style.display = (schedulingMethod === 'before_event') ? 'block' : 'none';
    }
}

/**
 * Affiche/masque le sélecteur de destinataires personnalisés
 */
function toggleRecipientsField() {
    const sendTo = document.getElementById('id_send_to').value;
    
    // Champ de sélection des destinataires personnalisés
    const customRecipientsField = document.getElementById('custom-recipients-field');
    if (customRecipientsField) {
        customRecipientsField.style.display = (sendTo === 'custom') ? 'block' : 'none';
    }
}

/**
 * Initialise les composants Bootstrap
 */
function initBootstrapComponents() {
    // Initialiser les tooltips
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(tooltip => {
        new bootstrap.Tooltip(tooltip);
    });
    
    // Initialiser les popovers
    const popovers = document.querySelectorAll('[data-bs-toggle="popover"]');
    popovers.forEach(popover => {
        new bootstrap.Popover(popover);
    });
}

/**
 * Affiche une notification à l'utilisateur
 */
function showNotification(message, type = 'info') {
    // Vérifier si l'élément de notification existe, sinon le créer
    let notificationArea = document.getElementById('notification-area');
    if (!notificationArea) {
        notificationArea = document.createElement('div');
        notificationArea.id = 'notification-area';
        notificationArea.className = 'position-fixed top-0 end-0 p-3';
        notificationArea.style.zIndex = '1050';
        document.body.appendChild(notificationArea);
    }
    
    // Créer l'élément de toast
    const toastId = 'toast-' + Date.now();
    const toastEl = document.createElement('div');
    toastEl.className = `toast bg-${type} text-white`;
    toastEl.id = toastId;
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    
    toastEl.innerHTML = `
        <div class="toast-header bg-${type} text-white">
            <strong class="me-auto">Notification</strong>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    notificationArea.appendChild(toastEl);
    
    // Initialiser et afficher le toast
    const toast = new bootstrap.Toast(toastEl, {
        autohide: true,
        delay: 5000
    });
    toast.show();
    
    // Supprimer le toast après qu'il soit caché
    toastEl.addEventListener('hidden.bs.toast', function() {
        toastEl.remove();
    });
}