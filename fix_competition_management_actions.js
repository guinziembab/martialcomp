// JavaScript à ajouter au template competition_management_detail.html
// Pour gérer la soumission AJAX du formulaire de création de catégorie

document.addEventListener('DOMContentLoaded', function() {
    // Gérer la soumission du formulaire de catégorie
    const categoryForm = document.getElementById('categoryForm');
    if (categoryForm) {
        categoryForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const submitButton = this.querySelector('button[type="submit"]');
            const originalText = submitButton.innerHTML;
            
            // Afficher un spinner
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Création...';
            submitButton.disabled = true;
            
            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Fermer le modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('categoryModal'));
                    modal.hide();
                    
                    // Réinitialiser le formulaire
                    this.reset();
                    
                    // Afficher un message de succès
                    showMessage(data.message, 'success');
                    
                    // Recharger la page pour afficher la nouvelle catégorie
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    showMessage(data.message || 'Erreur lors de la création de la catégorie', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showMessage('Erreur de connexion au serveur', 'error');
            })
            .finally(() => {
                submitButton.innerHTML = originalText;
                submitButton.disabled = false;
            });
        });
    }

    // Fonction pour afficher les messages
    function showMessage(message, type) {
        const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
        const icon = type === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-triangle';
        
        const alertHtml = `
            <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                <i class="${icon} me-2"></i>${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        // Insérer l'alerte en haut du modal body
        const modalBody = document.querySelector('#categoryModal .modal-body');
        if (modalBody) {
            modalBody.insertAdjacentHTML('afterbegin', alertHtml);
            
            // Auto-supprimer après 5 secondes
            setTimeout(() => {
                const alert = modalBody.querySelector('.alert');
                if (alert) {
                    alert.remove();
                }
            }, 5000);
        }
    }

    // Gérer les boutons d'actions rapides
    const quickActionButtons = document.querySelectorAll('[data-action]');
    quickActionButtons.forEach(button => {
        button.addEventListener('click', function() {
            const action = this.dataset.action;
            handleQuickAction(action);
        });
    });

    // Fonction pour gérer les actions rapides
    function handleQuickAction(action) {
        switch(action) {
            case 'edit-details':
                // Ouvrir modal d'édition
                const editModal = document.getElementById('editDetailsModal');
                if (editModal) {
                    const modal = new bootstrap.Modal(editModal);
                    modal.show();
                } else {
                    alert('Fonctionnalité en cours de développement');
                }
                break;
            
            case 'add-category':
                // Ouvrir modal de catégorie
                const categoryModal = document.getElementById('categoryModal');
                if (categoryModal) {
                    const modal = new bootstrap.Modal(categoryModal);
                    modal.show();
                }
                break;
            
            case 'schedule':
                // Ouvrir modal de planification
                const scheduleModal = document.getElementById('scheduleModal');
                if (scheduleModal) {
                    const modal = new bootstrap.Modal(scheduleModal);
                    modal.show();
                } else {
                    alert('Fonctionnalité de planification en cours de développement');
                }
                break;
            
            case 'share':
                // Ouvrir modal de partage
                const shareModal = document.getElementById('shareModal');
                if (shareModal) {
                    const modal = new bootstrap.Modal(shareModal);
                    modal.show();
                } else {
                    alert('Fonctionnalité de partage en cours de développement');
                }
                break;
            
            default:
                console.warn('Action non reconnue:', action);
        }
    }

    // Ajouter data-action aux boutons d'actions rapides s'ils n'en ont pas
    const editButton = document.querySelector('button[data-bs-target="#editDetailsModal"]');
    if (editButton && !editButton.dataset.action) {
        editButton.dataset.action = 'edit-details';
    }

    const categoryButton = document.querySelector('button[data-bs-target="#categoryModal"]');
    if (categoryButton && !categoryButton.dataset.action) {
        categoryButton.dataset.action = 'add-category';
    }

    const scheduleButton = document.querySelector('button[data-bs-target="#scheduleModal"]');
    if (scheduleButton && !scheduleButton.dataset.action) {
        scheduleButton.dataset.action = 'schedule';
    }

    const shareButton = document.querySelector('button[data-bs-target="#shareModal"]');
    if (shareButton && !shareButton.dataset.action) {
        shareButton.dataset.action = 'share';
    }
});