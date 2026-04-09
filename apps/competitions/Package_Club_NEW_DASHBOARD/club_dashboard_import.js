/**
 * MartialComp - Module Import CSV
 * Version: 2.0.0
 * ✅ Encodage UTF-8 corrigé
 * ✅ Gestion d'erreurs robuste
 */

(function() {
    'use strict';

    const CSVImport = {
        // ===== INITIALISATION =====
        init: function(urls, translations) {
            console.log('📥 Init Import CSV');
            
            this.urls = urls || {};
            this.translations = translations || {};
            
            this.initButton();
        },

        // ===== BOUTON =====
        initButton: function() {
            const importBtn = document.getElementById('import-csv-btn');
            if (!importBtn) return;

            // Éviter les double initialisations
            if (importBtn.getAttribute('data-initialized') === 'true') return;

            importBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.openFileDialog();
            });

            importBtn.setAttribute('data-initialized', 'true');
            console.log('✅ Bouton import CSV initialisé');
        },

        // ===== OPEN FILE DIALOG =====
        openFileDialog: function() {
            // Vérifier qu'un upload n'est pas déjà en cours
            if (window.ClubDashboard.state.uploadInProgress) {
                console.log('⚠️ Upload déjà en cours');
                return;
            }

            // Créer un input file temporaire
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.csv,.xlsx,.xls';
            input.style.display = 'none';

            input.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (file) {
                    this.handleFileSelect(file);
                }
            });

            document.body.appendChild(input);
            input.click();
            document.body.removeChild(input);
        },

        // ===== HANDLE FILE SELECT =====
        handleFileSelect: function(file) {
            console.log('📄 Fichier sélectionné:', file.name, 'Taille:', file.size);

            // Validation du format
            const validExtensions = ['.csv', '.xlsx', '.xls'];
            const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();

            if (!validExtensions.includes(fileExtension)) {
                alert('Format non supporté. Utilisez CSV ou Excel (.csv, .xlsx, .xls)');
                return;
            }

            // Validation de la taille (max 10MB)
            const maxSize = 10 * 1024 * 1024; // 10MB
            if (file.size > maxSize) {
                alert('Le fichier est trop volumineux (max 10MB)');
                return;
            }

            // Traiter le fichier
            this.uploadFile(file);
        },

        // ===== UPLOAD FILE =====
        uploadFile: function(file) {
            window.ClubDashboard.state.uploadInProgress = true;

            // Créer le FormData
            const formData = new FormData();
            formData.append('csv_file', file);
            formData.append('csrfmiddlewaretoken', window.ClubDashboard.getCookie('csrftoken'));

            // Afficher un indicateur de chargement
            window.ClubDashboard.showAlert('Import en cours...', 'info');

            // Envoyer la requête
            fetch(this.urls.import_export_ajax, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                window.ClubDashboard.state.uploadInProgress = false;

                if (data.success) {
                    window.ClubDashboard.showAlert(
                        `Import réussi: ${data.created || 0} pratiquants ajoutés, ${data.updated || 0} mis à jour`,
                        'success'
                    );
                    
                    // Recharger la page après 2 secondes
                    setTimeout(() => location.reload(), 2000);
                } else {
                    window.ClubDashboard.showAlert(
                        data.message || 'Erreur lors de l\'import',
                        'danger'
                    );
                    
                    // Afficher les erreurs détaillées si disponibles
                    if (data.errors && data.errors.length > 0) {
                        console.error('Erreurs d\'import:', data.errors);
                        this.showErrorDetails(data.errors);
                    }
                }
            })
            .catch(error => {
                console.error('Erreur upload:', error);
                window.ClubDashboard.state.uploadInProgress = false;
                window.ClubDashboard.showAlert(
                    'Erreur lors de l\'envoi du fichier',
                    'danger'
                );
            });
        },

        // ===== SHOW ERROR DETAILS =====
        showErrorDetails: function(errors) {
            // Créer un modal pour afficher les erreurs
            const modal = document.createElement('div');
            modal.className = 'modal fade';
            modal.id = 'importErrorsModal';

            let errorsList = '';
            errors.forEach((error, index) => {
                errorsList += `<li class="mb-2">Ligne ${error.row || index + 1}: ${error.message}</li>`;
            });

            modal.innerHTML = `
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header bg-danger text-white">
                            <h5 class="modal-title">
                                <i class="fas fa-exclamation-triangle"></i> Erreurs d'import
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p>Les erreurs suivantes ont été détectées:</p>
                            <ul class="list-unstyled">
                                ${errorsList}
                            </ul>
                            <div class="alert alert-info mt-3">
                                <i class="fas fa-info-circle"></i> 
                                Corrigez ces erreurs dans votre fichier et réessayez l'import.
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fermer</button>
                        </div>
                    </div>
                </div>
            `;

            document.body.appendChild(modal);

            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();

            // Nettoyer après fermeture
            modal.addEventListener('hidden.bs.modal', () => {
                modal.remove();
            });
        }
    };

    // Exposition globale
    window.CSVImport = CSVImport;

    console.log('📦 Module CSVImport chargé');

})();