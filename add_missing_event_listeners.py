#!/usr/bin/env python3
"""
Script pour ajouter les event listeners manquants pour les boutons pratiquants
"""
import os
import re
from datetime import datetime

def add_event_listeners():
    filepath = "apps/competitions/templates/competitions/dashboard/club.html"
    
    # Créer une sauvegarde
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{filepath}.backup_event_{timestamp}"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✓ Sauvegarde créée: {backup_path}")
    
    # Code à insérer juste avant le cache buster
    event_listeners_code = '''

// ============== EVENT LISTENERS POUR BOUTONS PRATIQUANTS ==============
// Ajoutés automatiquement le ''' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '''

// Event listener global pour les boutons de suppression
document.addEventListener('click', function(e) {
    // Bouton de suppression
    if (e.target.closest('.delete-practitioner-btn')) {
        e.preventDefault();
        const button = e.target.closest('.delete-practitioner-btn');
        const practitionerId = button.getAttribute('data-practitioner-id');
        const practitionerName = button.getAttribute('data-practitioner-name');
        
        if (confirm(`Êtes-vous sûr de vouloir supprimer ${practitionerName} ?`)) {
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            
            // Utiliser l'URL Django template tag
            const deleteUrl = "{% url 'competitions:club:practitioner_delete' practitioner_id=0 %}".replace('0', practitionerId);
            
            fetch(deleteUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // Supprimer la ligne du tableau
                    const row = button.closest('tr');
                    if (row) {
                        row.style.transition = 'opacity 0.3s';
                        row.style.opacity = '0';
                        setTimeout(() => row.remove(), 300);
                    }
                    
                    // Afficher le message de succès
                    if (data.message) {
                        showAlert('success', data.message);
                    }
                } else {
                    alert('Erreur: ' + (data.error || 'Erreur inconnue'));
                    button.disabled = false;
                    button.innerHTML = '<i class="fas fa-trash"></i>';
                }
            })
            .catch(error => {
                console.error('Erreur:', error);
                alert('Erreur lors de la suppression');
                button.disabled = false;
                button.innerHTML = '<i class="fas fa-trash"></i>';
            });
        }
    }
    
    // Bouton toggle status
    if (e.target.closest('.toggle-status-btn')) {
        e.preventDefault();
        const button = e.target.closest('.toggle-status-btn');
        const practitionerId = button.getAttribute('data-practitioner-id');
        const currentStatus = button.getAttribute('data-current-status') === 'true';
        
        button.disabled = true;
        const originalHTML = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        
        // Utiliser l'URL Django template tag
        const toggleUrl = "{% url 'competitions:club:practitioner_toggle_status' pk=0 %}".replace('0', practitionerId);
        
        fetch(toggleUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                is_active: !currentStatus
            }),
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                const newStatus = data.is_active;
                button.setAttribute('data-current-status', newStatus.toString());
                
                // Mettre à jour l'apparence du bouton
                if (newStatus) {
                    button.classList.remove('btn-outline-warning');
                    button.classList.add('btn-outline-success');
                    button.innerHTML = '<i class="fas fa-toggle-on"></i>';
                    button.title = "{% trans 'Désactiver' %}";
                } else {
                    button.classList.remove('btn-outline-success');
                    button.classList.add('btn-outline-warning');
                    button.innerHTML = '<i class="fas fa-toggle-off"></i>';
                    button.title = "{% trans 'Activer' %}";
                }
                
                // Mettre à jour le badge de statut
                const row = button.closest('tr');
                if (row) {
                    const statusCell = row.querySelector('td:nth-child(5)');
                    if (statusCell) {
                        if (newStatus) {
                            statusCell.innerHTML = '<span class="badge bg-success">{% trans "Actif" %}</span>';
                        } else {
                            statusCell.innerHTML = '<span class="badge bg-secondary">{% trans "Inactif" %}</span>';
                        }
                    }
                }
                
                button.disabled = false;
                
                // Afficher le message de succès
                if (data.message) {
                    showAlert('success', data.message);
                }
            } else {
                alert('Erreur: ' + (data.error || 'Erreur inconnue'));
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

// Fonction pour afficher des alertes
function showAlert(type, message) {
    const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
    const icon = type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle';
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert ${alertClass} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
    alertDiv.style.zIndex = '9999';
    alertDiv.style.minWidth = '300px';
    alertDiv.innerHTML = `
        <i class="fas ${icon} me-2"></i>${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-fermer après 5 secondes
    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => alertDiv.remove(), 300);
    }, 5000);
}

// Corriger le bouton Import CSV au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔧 Initialisation des corrections de boutons...');
    
    // Fix Import CSV button
    const importBtn = document.getElementById('importCsvBtn');
    if (importBtn) {
        console.log('✓ Bouton Import CSV trouvé');
        importBtn.removeAttribute('onclick');
        importBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Import CSV cliqué - redirection...');
            window.location.href = "{% url 'competitions:club:import_export' %}";
        });
    }
    
    // Fix Bulk Registration button
    const bulkBtn = document.getElementById('bulkRegistrationBtn');
    if (bulkBtn) {
        console.log('✓ Bouton Inscription en masse trouvé');
        // Le bouton devrait déjà avoir son event listener via showBulkRegistrationModal
        // Vérifier qu'il est configuré correctement
        if (!bulkBtn.onclick && typeof showBulkRegistrationModal === 'function') {
            bulkBtn.onclick = showBulkRegistrationModal;
        }
    }
    
    console.log('✅ Event listeners des boutons pratiquants initialisés');
});
'''

    # Remplacer la ligne du cache buster avec notre code + cache buster
    new_content = content.replace(
        '// Cache buster: 20251103101111',
        event_listeners_code + '\n\n// Cache buster: ' + datetime.now().strftime('%Y%m%d%H%M%S')
    )
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✓ Event listeners ajoutés avec succès")

if __name__ == "__main__":
    print("=== Ajout des event listeners manquants ===")
    print(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 50)
    
    if not os.path.exists('manage.py'):
        print("ERREUR: Ce script doit être exécuté depuis la racine du projet")
        exit(1)
    
    add_event_listeners()
    
    print("\n✅ Terminé! Redémarrez le serveur Django et testez les boutons.")