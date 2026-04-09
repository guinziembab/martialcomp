/**
 * MartialComp - Module Inscription en Masse
 * Version: 2.0.0
 * ✅ Encodage UTF-8 corrigé
 * ✅ Une seule définition de fonction
 */

(function() {
    'use strict';

    const BulkRegistration = {
        // ===== INITIALISATION =====
        init: function(urls, translations) {
            console.log('📋 Init Inscription en Masse');
            
            this.urls = urls || {};
            this.translations = translations || {};
            
            this.initButtons();
            this.initCheckboxes();
        },

        // ===== BOUTONS =====
        initButtons: function() {
            const bulkBtn = document.getElementById('bulk-registration-btn');
            if (!bulkBtn) return;

            // Éviter les double initialisations
            if (bulkBtn.getAttribute('data-initialized') === 'true') return;

            bulkBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.showModal();
            });

            bulkBtn.setAttribute('data-initialized', 'true');
            console.log('✅ Bouton inscription en masse initialisé');
        },

        // ===== CHECKBOXES =====
        initCheckboxes: function() {
            // Checkbox "Tout sélectionner"
            const selectAllCheckbox = document.getElementById('select-all-practitioners');
            if (selectAllCheckbox) {
                selectAllCheckbox.addEventListener('change', (e) => {
                    this.toggleAllPractitioners(e.target.checked);
                });
            }

            // Checkboxes individuelles
            document.querySelectorAll('.practitioner-checkbox').forEach(checkbox => {
                checkbox.addEventListener('change', () => {
                    this.updateButtonState();
                });
            });
        },

        // ===== TOGGLE ALL =====
        toggleAllPractitioners: function(checked) {
            document.querySelectorAll('.practitioner-checkbox').forEach(cb => {
                cb.checked = checked;
            });
            this.updateButtonState();
        },

        // ===== UPDATE BUTTON =====
        updateButtonState: function() {
            const selected = document.querySelectorAll('.practitioner-checkbox:checked');
            const bulkBtn = document.getElementById('bulk-registration-btn');
            
            if (!bulkBtn) return;

            if (selected.length > 0) {
                bulkBtn.innerHTML = `<i class="fas fa-trophy"></i> Inscrire (${selected.length})`;
                bulkBtn.classList.remove('btn-info');
                bulkBtn.classList.add('btn-success');
            } else {
                bulkBtn.innerHTML = '<i class="fas fa-trophy"></i> Inscription en masse';
                bulkBtn.classList.remove('btn-success');
                bulkBtn.classList.add('btn-info');
            }
        },

        // ===== SHOW MODAL =====
        showModal: function() {
            const allPractitioners = document.querySelectorAll('.practitioner-checkbox');
            const selectedPractitioners = document.querySelectorAll('.practitioner-checkbox:checked');

            // Validations
            if (allPractitioners.length === 0) {
                alert("Aucun pratiquant disponible. Ajoutez d'abord des membres.");
                return;
            }

            if (selectedPractitioners.length === 0) {
                alert("Veuillez sélectionner au moins un pratiquant.");
                return;
            }

            try {
                this.createModal(selectedPractitioners);
            } catch (error) {
                console.error('Erreur création modal:', error);
                alert('Une erreur est survenue lors de l\'ouverture du modal');
            }
        },

        // ===== CREATE MODAL =====
        createModal: function(selectedPractitioners) {
            // Créer le modal
            const modal = document.createElement('div');
            modal.className = 'modal fade';
            modal.id = 'bulkRegistrationModal';
            modal.setAttribute('tabindex', '-1');

            modal.innerHTML = `
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-trophy"></i> Inscription en masse
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h6>Pratiquants sélectionnés (${selectedPractitioners.length})</h6>
                                    <div id="selectedPractitionersList" class="list-group">
                                        ${this.renderPractitionersList(selectedPractitioners)}
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <h6>Choisir une compétition</h6>
                                    <select id="competitionSelect" class="form-select">
                                        <option value="">Chargement...</option>
                                    </select>
                                    <div id="competitionInfo" class="mt-3"></div>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Annuler</button>
                            <button type="button" class="btn btn-primary" id="confirmBulkRegistration">
                                <i class="fas fa-check"></i> Confirmer l'inscription
                            </button>
                        </div>
                    </div>
                </div>
            `;

            document.body.appendChild(modal);

            // Charger les compétitions
            this.loadAvailableCompetitions();

            // Afficher le modal
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();

            // Event listener pour la confirmation
            document.getElementById('confirmBulkRegistration').addEventListener('click', () => {
                this.processRegistration(selectedPractitioners);
            });

            // Nettoyer après fermeture
            modal.addEventListener('hidden.bs.modal', () => {
                modal.remove();
            });
        },

        // ===== RENDER LIST =====
        renderPractitionersList: function(practitioners) {
            let html = '';
            practitioners.forEach(checkbox => {
                const name = checkbox.getAttribute('data-name');
                html += `
                    <div class="list-group-item d-flex justify-content-between align-items-center">
                        <span><i class="fas fa-user me-2"></i>${name}</span>
                        <span class="badge bg-primary">Prêt</span>
                    </div>
                `;
            });
            return html;
        },

        // ===== LOAD COMPETITIONS =====
        loadAvailableCompetitions: function() {
            const select = document.getElementById('competitionSelect');
            
            fetch(this.urls.available_competitions, {
                method: 'GET',
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
            .then(response => response.json())
            .then(data => {
                if (data.competitions && data.competitions.length > 0) {
                    select.innerHTML = '<option value="">-- Sélectionner une compétition --</option>';
                    data.competitions.forEach(comp => {
                        const option = document.createElement('option');
                        option.value = comp.id;
                        option.textContent = `${comp.name} - ${comp.date}`;
                        option.setAttribute('data-location', comp.location || '');
                        option.setAttribute('data-deadline', comp.registration_deadline || '');
                        select.appendChild(option);
                    });
                    
                    // Event listener pour afficher les infos
                    select.addEventListener('change', (e) => {
                        const option = e.target.selectedOptions[0];
                        if (option.value) {
                            this.displayCompetitionInfo(option);
                        }
                    });
                } else {
                    select.innerHTML = '<option value="">Aucune compétition disponible</option>';
                }
            })
            .catch(error => {
                console.error('Erreur chargement compétitions:', error);
                select.innerHTML = '<option value="">Erreur de chargement</option>';
            });
        },

        // ===== DISPLAY INFO =====
        displayCompetitionInfo: function(option) {
            const infoDiv = document.getElementById('competitionInfo');
            infoDiv.innerHTML = `
                <div class="alert alert-info">
                    <h6>${option.textContent}</h6>
                    <p class="mb-0">
                        <i class="fas fa-map-marker-alt"></i> ${option.getAttribute('data-location') || 'Non défini'}<br>
                        <i class="fas fa-calendar"></i> Date limite: ${option.getAttribute('data-deadline') || 'Non définie'}
                    </p>
                </div>
            `;
        },

        // ===== PROCESS REGISTRATION =====
        processRegistration: function(selectedPractitioners) {
            const select = document.getElementById('competitionSelect');
            const competitionId = select.value;

            if (!competitionId) {
                alert('Veuillez sélectionner une compétition');
                return;
            }

            // Récupérer les IDs des pratiquants
            const practitionerIds = [];
            selectedPractitioners.forEach(checkbox => {
                practitionerIds.push(checkbox.value);
            });

            // Envoyer la requête
            fetch(this.urls.bulk_registration_process, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': window.ClubDashboard.getCookie('csrftoken'),
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    competition_id: competitionId,
                    practitioner_ids: practitionerIds
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.ClubDashboard.showAlert(
                        `${data.registered_count} pratiquants inscrits avec succès`,
                        'success'
                    );
                    // Fermer le modal
                    bootstrap.Modal.getInstance(document.getElementById('bulkRegistrationModal')).hide();
                    
                    // Recharger la page après 2 secondes
                    setTimeout(() => location.reload(), 2000);
                } else {
                    window.ClubDashboard.showAlert(data.message || 'Erreur lors de l\'inscription', 'danger');
                }
            })
            .catch(error => {
                console.error('Erreur inscription:', error);
                window.ClubDashboard.showAlert('Erreur lors de l\'inscription', 'danger');
            });
        }
    };

    // Exposition globale
    window.BulkRegistration = BulkRegistration;

    console.log('📦 Module BulkRegistration chargé');

})();