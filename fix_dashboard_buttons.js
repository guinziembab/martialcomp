// Corrections pour les boutons du dashboard club
// Ce fichier doit être ajouté au template dashboard/club.html

// Fonction getCookie pour obtenir le CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Initialisation des event listeners au chargement du DOM
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔧 Initialisation des boutons du dashboard club...');
    
    // 1. Gestion des boutons de suppression
    document.addEventListener('click', function(e) {
        if (e.target.closest('.delete-practitioner-btn')) {
            e.preventDefault();
            const button = e.target.closest('.delete-practitioner-btn');
            const practitionerId = button.getAttribute('data-practitioner-id');
            const practitionerName = button.getAttribute('data-practitioner-name');
            
            if (confirm(`Êtes-vous sûr de vouloir supprimer ${practitionerName} ?`)) {
                // Désactiver le bouton
                button.disabled = true;
                button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
                
                fetch(`/fr/competitions/club/practitioners/${practitionerId}/delete/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    credentials: 'same-origin'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Supprimer la ligne du tableau
                        const row = button.closest('tr');
                        if (row) {
                            row.remove();
                        }
                        alert('Pratiquant supprimé avec succès');
                    } else {
                        alert('Erreur lors de la suppression: ' + (data.error || 'Erreur inconnue'));
                        // Réactiver le bouton
                        button.disabled = false;
                        button.innerHTML = '<i class="fas fa-trash"></i>';
                    }
                })
                .catch(error => {
                    console.error('Erreur:', error);
                    alert('Erreur lors de la suppression');
                    // Réactiver le bouton
                    button.disabled = false;
                    button.innerHTML = '<i class="fas fa-trash"></i>';
                });
            }
        }
    });
    
    // 2. Gestion des boutons toggle status (activer/désactiver)
    document.addEventListener('click', function(e) {
        if (e.target.closest('.toggle-status-btn')) {
            e.preventDefault();
            const button = e.target.closest('.toggle-status-btn');
            const practitionerId = button.getAttribute('data-practitioner-id');
            const currentStatus = button.getAttribute('data-current-status');
            
            // Désactiver le bouton
            button.disabled = true;
            const originalHTML = button.innerHTML;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            
            fetch(`/fr/competitions/club/practitioners/${practitionerId}/toggle-status/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({}),
                credentials: 'same-origin'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Mettre à jour le bouton
                    const newStatus = data.is_active;
                    button.setAttribute('data-current-status', newStatus.toString());
                    
                    // Changer la classe et l'icône
                    if (newStatus) {
                        button.classList.remove('btn-outline-warning');
                        button.classList.add('btn-outline-success');
                        button.innerHTML = '<i class="fas fa-toggle-on"></i>';
                        button.title = 'Désactiver';
                    } else {
                        button.classList.remove('btn-outline-success');
                        button.classList.add('btn-outline-warning');
                        button.innerHTML = '<i class="fas fa-toggle-off"></i>';
                        button.title = 'Activer';
                    }
                    
                    // Mettre à jour le badge de statut si présent
                    const row = button.closest('tr');
                    const statusCell = row.querySelector('td:nth-child(5)'); // Colonne statut
                    if (statusCell) {
                        if (newStatus) {
                            statusCell.innerHTML = '<span class="badge bg-success">Actif</span>';
                        } else {
                            statusCell.innerHTML = '<span class="badge bg-secondary">Inactif</span>';
                        }
                    }
                    
                    button.disabled = false;
                } else {
                    alert('Erreur lors du changement de statut: ' + (data.error || 'Erreur inconnue'));
                    button.disabled = false;
                    button.innerHTML = originalHTML;
                }
            })
            .catch(error => {
                console.error('Erreur:', error);
                alert('Erreur lors du changement de statut');
                button.disabled = false;
                button.innerHTML = originalHTML;
            });
        }
    });
    
    // 3. Bouton Import CSV
    const importCsvBtn = document.getElementById('importCsvBtn');
    if (importCsvBtn) {
        importCsvBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Import CSV clicked');
            window.location.href = '/fr/competitions/club/import-export/';
        });
    }
    
    // 4. Inscription en masse - vérifier si le bouton existe
    const bulkRegBtn = document.getElementById('bulkRegistrationBtn');
    if (bulkRegBtn && !bulkRegBtn.hasAttribute('data-initialized')) {
        bulkRegBtn.setAttribute('data-initialized', 'true');
        bulkRegBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Bulk registration clicked');
            
            const selectedPractitioners = document.querySelectorAll('.practitioner-checkbox:checked');
            if (selectedPractitioners.length === 0) {
                alert('Veuillez sélectionner au moins un pratiquant');
                return;
            }
            
            // Ouvrir le modal d'inscription en masse
            if (typeof showBulkRegistrationModal === 'function') {
                showBulkRegistrationModal();
            } else {
                console.error('showBulkRegistrationModal function not found');
                alert('Fonction d\'inscription en masse non disponible');
            }
        });
    }
    
    console.log('✅ Boutons du dashboard initialisés avec succès');
});

// Ajouter ce script pour déboguer
console.log('Dashboard buttons fix script loaded');