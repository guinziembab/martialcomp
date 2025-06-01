/**
 * JavaScript pour les sondages d'événements (surveys)
 * Améliore l'expérience utilisateur pour la création et la participation aux sondages
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialisation pour les formulaires de sondage
    initSurveyForm();
    
    // Initialisation pour les formulaires de réponse
    initSurveyResponseForm();
    
    // Initialisation pour les visualisations de résultats
    initSurveyResults();
    
    // Initialisation des actions de sondage (activation/désactivation, suppression)
    initSurveyActions();
});

/**
 * Initialise le formulaire de création/édition de sondage
 */
function initSurveyForm() {
    const formElement = document.getElementById('surveyForm');
    if (!formElement) return;
    
    // Gestion des questions
    initQuestionForms();
    
    // Validation avancée du formulaire
    formElement.addEventListener('submit', function(e) {
        const isValid = validateSurveyForm();
        if (!isValid) {
            e.preventDefault();
            showNotification('Veuillez corriger les erreurs dans le formulaire avant de soumettre.', 'danger');
        }
    });
}

/**
 * Initialise la gestion des questions dans le formulaire de sondage
 */
function initQuestionForms() {
    // Bouton d'ajout de question
    const addQuestionBtn = document.getElementById('addQuestion');
    if (addQuestionBtn) {
        addQuestionBtn.addEventListener('click', addNewQuestion);
    }
    
    // Initialiser les gestionnaires pour les questions existantes
    const questions = document.querySelectorAll('.question-formset');
    questions.forEach(initQuestionFormset);
    
    // Rendre les questions triables
    initSortableQuestions();
}

/**
 * Ajoute une nouvelle question au formulaire
 */
function addNewQuestion() {
    const container = document.getElementById('questions-container');
    const totalFormsInput = document.getElementById('id_questions-TOTAL_FORMS');
    const emptyForm = document.getElementById('empty-form-template').innerHTML;
    
    // Récupérer l'index actuel
    const formCount = parseInt(totalFormsInput.value);
    
    // Incrémenter le compteur de formulaires
    totalFormsInput.value = formCount + 1;
    
    // Créer un nouvel élément de question en remplaçant les indices
    const newForm = emptyForm.replace(/__prefix__/g, formCount);
    
    // Ajouter la nouvelle question au conteneur
    container.insertAdjacentHTML('beforeend', newForm);
    
    // Initialiser la nouvelle question
    const newQuestion = container.lastElementChild;
    initQuestionFormset(newQuestion);
    
    // Mettre à jour les numéros de questions
    updateQuestionNumbers();
    
    // Masquer le message "aucune question"
    const noQuestionsMessage = document.getElementById('noQuestionsMessage');
    if (noQuestionsMessage) {
        noQuestionsMessage.style.display = 'none';
    }
}

/**
 * Initialise une question individuelle
 */
function initQuestionFormset(question) {
    // Gestionnaire de type de question
    const typeSelect = question.querySelector('[id$="-question_type"]');
    if (typeSelect) {
        typeSelect.addEventListener('change', function() {
            updateQuestionTypeFields(question, this.value);
        });
        
        // Initialiser l'affichage des champs spécifiques
        updateQuestionTypeFields(question, typeSelect.value);
    }
    
    // Gestionnaire de suppression
    const deleteBtn = question.querySelector('.delete-question');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', function() {
            deleteQuestion(question);
        });
    }
}

/**
 * Met à jour les champs spécifiques au type de question
 */
function updateQuestionTypeFields(question, questionType) {
    // Masquer tous les champs spécifiques
    const specificFields = question.querySelectorAll('.question-type-specific');
    specificFields.forEach(field => {
        field.classList.remove('active');
    });
    
    // Afficher les champs correspondant au type sélectionné
    if (questionType === 'single_choice' || questionType === 'multiple_choice') {
        const choiceFields = question.querySelector('.question-type-choice');
        if (choiceFields) choiceFields.classList.add('active');
    } else if (questionType === 'rating' || questionType === 'scale') {
        const ratingFields = question.querySelector('.question-type-rating');
        if (ratingFields) ratingFields.classList.add('active');
    }
}

/**
 * Supprime une question du formulaire
 */
function deleteQuestion(question) {
    // Confirmation
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette question ?')) {
        return;
    }
    
    // Marquer comme supprimé plutôt que de réellement supprimer (pour la gestion de formset Django)
    const deleteInput = question.querySelector('[id$="-DELETE"]');
    if (deleteInput) {
        deleteInput.checked = true;
        question.classList.add('deleted');
        question.style.display = 'none';
    } else {
        // Si pas de champ DELETE (nouvelle question), supprimer l'élément DOM
        question.remove();
    }
    
    // Mettre à jour les numéros de questions
    updateQuestionNumbers();
    
    // Afficher le message "aucune question" si toutes les questions sont supprimées
    checkNoQuestions();
}

/**
 * Met à jour les numéros de questions affichés
 */
function updateQuestionNumbers() {
    const questions = document.querySelectorAll('.question-formset:not(.deleted)');
    questions.forEach((question, index) => {
        const numberSpan = question.querySelector('.question-number');
        if (numberSpan) {
            numberSpan.textContent = index + 1;
        }
    });
}

/**
 * Vérifie s'il reste des questions et affiche un message si nécessaire
 */
function checkNoQuestions() {
    const questions = document.querySelectorAll('.question-formset:not(.deleted)');
    const noQuestionsMessage = document.getElementById('noQuestionsMessage');
    
    if (noQuestionsMessage) {
        noQuestionsMessage.style.display = questions.length === 0 ? 'block' : 'none';
    }
}

/**
 * Initialise le tri des questions par glisser-déposer
 */
function initSortableQuestions() {
    // Vérifier si la bibliothèque Sortable.js est disponible
    if (typeof Sortable === 'undefined') return;
    
    const container = document.getElementById('questions-container');
    if (!container) return;
    
    // Créer l'instance Sortable
    new Sortable(container, {
        handle: '.drag-handle',
        animation: 150,
        onEnd: function() {
            // Mettre à jour les numéros et l'ordre des questions
            updateQuestionNumbers();
            updateQuestionOrder();
        }
    });
}

/**
 * Met à jour les champs d'ordre des questions
 */
function updateQuestionOrder() {
    const questions = document.querySelectorAll('.question-formset:not(.deleted)');
    questions.forEach((question, index) => {
        const orderInput = question.querySelector('[id$="-order"]');
        if (orderInput) {
            orderInput.value = index;
        }
    });
}

/**
 * Valide le formulaire de sondage avant soumission
 */
function validateSurveyForm() {
    let isValid = true;
    
    // Vérifier les champs obligatoires du sondage
    const title = document.getElementById('id_title');
    if (!title || !title.value.trim()) {
        markFieldAsInvalid(title, 'Le titre est obligatoire');
        isValid = false;
    } else {
        markFieldAsValid(title);
    }
    
    // Vérifier qu'il y a au moins une question visible
    const visibleQuestions = document.querySelectorAll('.question-formset:not(.deleted)');
    if (visibleQuestions.length === 0) {
        showNotification('Vous devez ajouter au moins une question au sondage.', 'warning');
        isValid = false;
    }
    
    // Vérifier chaque question
    visibleQuestions.forEach((question, index) => {
        // Vérifier le texte de la question
        const questionText = question.querySelector('[id$="-question_text"]');
        if (!questionText || !questionText.value.trim()) {
            markFieldAsInvalid(questionText, 'Le texte de la question est obligatoire');
            isValid = false;
        } else {
            markFieldAsValid(questionText);
        }
        
        // Vérifier les champs spécifiques selon le type
        const questionType = question.querySelector('[id$="-question_type"]').value;
        
        if (questionType === 'single_choice' || questionType === 'multiple_choice') {
            const choices = question.querySelector('[id$="-choices_text"]');
            if (!choices || !choices.value.trim()) {
                markFieldAsInvalid(choices, 'Vous devez spécifier au moins une option de réponse');
                isValid = false;
            } else {
                markFieldAsValid(choices);
            }
        } else if (questionType === 'rating' || questionType === 'scale') {
            const minValue = question.querySelector('[id$="-min_value"]');
            const maxValue = question.querySelector('[id$="-max_value"]');
            
            if (!minValue || minValue.value === '' || isNaN(parseInt(minValue.value))) {
                markFieldAsInvalid(minValue, 'La valeur minimale est obligatoire');
                isValid = false;
            } else {
                markFieldAsValid(minValue);
            }
            
            if (!maxValue || maxValue.value === '' || isNaN(parseInt(maxValue.value))) {
                markFieldAsInvalid(maxValue, 'La valeur maximale est obligatoire');
                isValid = false;
            } else if (parseInt(maxValue.value) <= parseInt(minValue.value)) {
                markFieldAsInvalid(maxValue, 'La valeur maximale doit être supérieure à la valeur minimale');
                isValid = false;
            } else {
                markFieldAsValid(maxValue);
            }
        }
    });
    
    return isValid;
}

/**
 * Marque un champ comme invalide et affiche un message d'erreur
 */
function markFieldAsInvalid(field, message) {
    if (!field) return;
    
    field.classList.add('is-invalid');
    
    // Créer ou mettre à jour le message d'erreur
    let errorDiv = field.nextElementSibling;
    if (!errorDiv || !errorDiv.classList.contains('invalid-feedback')) {
        errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        field.parentNode.insertBefore(errorDiv, field.nextSibling);
    }
    
    errorDiv.textContent = message;
}

/**
 * Marque un champ comme valide
 */
function markFieldAsValid(field) {
    if (!field) return;
    
    field.classList.remove('is-invalid');
    field.classList.add('is-valid');
    
    // Supprimer le message d'erreur s'il existe
    const errorDiv = field.nextElementSibling;
    if (errorDiv && errorDiv.classList.contains('invalid-feedback')) {
        errorDiv.remove();
    }
}

/**
 * Initialise le formulaire de réponse à un sondage
 */
function initSurveyResponseForm() {
    const form = document.getElementById('survey-response-form');
    if (!form) return;
    
    // Gestion des questions de notation
    initRatingQuestions();
    
    // Gestion des questions à échelle
    initScaleQuestions();
    
    // Gestion de l'anonymat
    initAnonymousToggle();
    
    // Validation du formulaire avant soumission
    form.addEventListener('submit', function(e) {
        const isValid = validateResponseForm();
        if (!isValid) {
            e.preventDefault();
            showNotification('Veuillez répondre à toutes les questions obligatoires.', 'warning');
            
            // Mettre en évidence les questions requises non répondues
            highlightRequiredQuestions();
        }
    });
}

/**
 * Initialise les questions de notation
 */
function initRatingQuestions() {
    const ratingOptions = document.querySelectorAll('.rating-option');
    ratingOptions.forEach(option => {
        option.addEventListener('click', function() {
            // Récupérer l'identifiant du champ et la valeur
            const fieldName = this.getAttribute('data-field');
            const value = this.getAttribute('data-value');
            
            // Mettre à jour le champ caché
            const hiddenInput = document.getElementById(fieldName);
            if (hiddenInput) {
                hiddenInput.value = value;
                
                // Marquer le champ comme valide si requis
                if (hiddenInput.hasAttribute('required')) {
                    hiddenInput.classList.remove('is-invalid');
                }
            }
            
            // Mettre à jour l'interface
            const optionsGroup = document.querySelectorAll(`.rating-option[data-field="${fieldName}"]`);
            optionsGroup.forEach(opt => {
                opt.classList.remove('selected');
            });
            
            this.classList.add('selected');
        });
    });
}

/**
 * Initialise les questions à échelle
 */
function initScaleQuestions() {
    const scaleInputs = document.querySelectorAll('input[type="range"]');
    scaleInputs.forEach(input => {
        // Créer un élément pour afficher la valeur
        const valueDisplay = document.createElement('div');
        valueDisplay.className = 'range-value';
        valueDisplay.textContent = input.value;
        input.parentNode.appendChild(valueDisplay);
        
        // Mettre à jour l'affichage de la valeur lors du déplacement du curseur
        input.addEventListener('input', function() {
            valueDisplay.textContent = this.value;
        });
    });
}

/**
 * Initialise la gestion de l'anonymat
 */
function initAnonymousToggle() {
    const anonymousCheckbox = document.getElementById('id_is_anonymous');
    if (!anonymousCheckbox) return;
    
    const nameField = document.getElementById('id_respondent_name');
    const emailField = document.getElementById('id_respondent_email');
    
    anonymousCheckbox.addEventListener('change', function() {
        if (this.checked) {
            // Masquer et désactiver les champs d'identification
            if (nameField) {
                nameField.disabled = true;
                nameField.parentNode.style.display = 'none';
            }
            
            if (emailField) {
                emailField.disabled = true;
                emailField.parentNode.style.display = 'none';
            }
        } else {
            // Afficher et activer les champs d'identification
            if (nameField) {
                nameField.disabled = false;
                nameField.parentNode.style.display = 'block';
            }
            
            if (emailField) {
                emailField.disabled = false;
                emailField.parentNode.style.display = 'block';
            }
        }
    });
    
    // Initialiser l'état des champs
    anonymousCheckbox.dispatchEvent(new Event('change'));
}

/**
 * Valide le formulaire de réponse avant soumission
 */
function validateResponseForm() {
    let isValid = true;
    
    // Vérifier les champs d'identification si non anonyme
    const anonymousCheckbox = document.getElementById('id_is_anonymous');
    if (anonymousCheckbox && !anonymousCheckbox.checked) {
        const nameField = document.getElementById('id_respondent_name');
        const emailField = document.getElementById('id_respondent_email');
        
        if (nameField && !nameField.value.trim()) {
            nameField.classList.add('is-invalid');
            isValid = false;
        }
        
        if (emailField && !emailField.value.trim()) {
            emailField.classList.add('is-invalid');
            isValid = false;
        }
    }
    
    // Vérifier les questions obligatoires
    const requiredFields = document.querySelectorAll('.question-input [required]');
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        }
    });
    
    return isValid;
}

/**
 * Met en évidence les questions requises non répondues
 */
function highlightRequiredQuestions() {
    const requiredQuestions = document.querySelectorAll('.question-card:has(.is-invalid)');
    requiredQuestions.forEach(question => {
        question.scrollIntoView({ behavior: 'smooth', block: 'center' });
        question.classList.add('border-danger');
        
        // Animation pour attirer l'attention
        setTimeout(() => {
            question.classList.remove('border-danger');
        }, 2000);
    });
}

/**
 * Initialise les visualisations de résultats de sondage
 */
function initSurveyResults() {
    // Vérifier si Chart.js est disponible
    if (typeof Chart === 'undefined') return;
    
    // Initialiser les graphiques pour chaque question
    initQuestionCharts();
    
    // Initialiser le graphique de progression des réponses
    initResponseProgressChart();
}

/**
 * Initialise les graphiques pour chaque question
 */
function initQuestionCharts() {
    // Graphiques pour les questions à choix
    document.querySelectorAll('[id^="chart-choice-question-"]').forEach(canvas => {
        const questionId = canvas.id.replace('chart-choice-question-', '');
        const dataElement = document.getElementById(`chart-data-${questionId}`);
        
        if (!dataElement) return;
        
        const chartData = JSON.parse(dataElement.textContent);
        
        new Chart(canvas, {
            type: 'bar',
            data: {
                labels: chartData.labels,
                datasets: [{
                    label: 'Réponses',
                    data: chartData.values,
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Nombre de réponses'
                        }
                    }
                }
            }
        });
    });
    
    // Graphiques pour les questions de notation
    document.querySelectorAll('[id^="chart-rating-question-"]').forEach(canvas => {
        const questionId = canvas.id.replace('chart-rating-question-', '');
        const dataElement = document.getElementById(`chart-data-${questionId}`);
        
        if (!dataElement) return;
        
        const chartData = JSON.parse(dataElement.textContent);
        
        new Chart(canvas, {
            type: 'bar',
            data: {
                labels: chartData.labels,
                datasets: [{
                    label: 'Réponses',
                    data: chartData.values,
                    backgroundColor: 'rgba(75, 192, 192, 0.5)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Nombre de réponses'
                        }
                    }
                }
            }
        });
    });
}

/**
 * Initialise le graphique de progression des réponses
 */
function initResponseProgressChart() {
    const canvas = document.getElementById('response-progress-chart');
    if (!canvas) return;
    
    const dataElement = document.getElementById('response-progress-data');
    if (!dataElement) return;
    
    const chartData = JSON.parse(dataElement.textContent);
    
    new Chart(canvas, {
        type: 'line',
        data: {
            labels: chartData.dates,
            datasets: [{
                label: 'Réponses cumulées',
                data: chartData.cumulative,
                borderColor: 'rgba(54, 162, 235, 1)',
                backgroundColor: 'rgba(54, 162, 235, 0.1)',
                tension: 0.1,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Nombre de réponses'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                }
            }
        }
    });
}

/**
 * Initialise les actions de sondage (activation/désactivation, suppression)
 */
function initSurveyActions() {
    // Activation/désactivation d'un sondage
    const toggleStatusBtn = document.querySelector('.toggle-status');
    if (toggleStatusBtn) {
        toggleStatusBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            const surveyId = this.dataset.surveyId;
            const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
            
            // Envoyer la demande via AJAX
            fetch(`/competitions/events/surveys/${surveyId}/toggle/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Mettre à jour l'interface
                    if (data.is_active) {
                        this.innerHTML = '<i class="fas fa-toggle-off"></i> Désactiver le sondage';
                        document.getElementById('survey-status-badge').className = 'badge bg-success';
                        document.getElementById('survey-status-badge').textContent = 'Actif';
                    } else {
                        this.innerHTML = '<i class="fas fa-toggle-on"></i> Activer le sondage';
                        document.getElementById('survey-status-badge').className = 'badge bg-secondary';
                        document.getElementById('survey-status-badge').textContent = 'Inactif';
                    }
                    
                    showNotification(data.message, 'success');
                } else {
                    showNotification(data.message || 'Une erreur est survenue lors du changement de statut du sondage.', 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Une erreur de communication est survenue. Veuillez réessayer.', 'danger');
            });
        });
    }
    
    // Suppression d'un sondage
    const confirmDeleteBtn = document.getElementById('confirmDelete');
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', function() {
            const surveyId = this.dataset.surveyId;
            const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
            
            // Envoyer la demande via AJAX
            fetch(`/competitions/events/surveys/${surveyId}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification('Le sondage a été supprimé avec succès.', 'success');
                    
                    // Rediriger vers la page appropriée
                    setTimeout(() => {
                        window.location.href = data.redirect_url;
                    }, 1500);
                } else {
                    showNotification(data.message || 'Une erreur est survenue lors de la suppression du sondage.', 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Une erreur de communication est survenue. Veuillez réessayer.', 'danger');
            });
        });
    }
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