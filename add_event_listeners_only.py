#!/usr/bin/env python3
"""
Script pour ajouter uniquement les event listeners manquants au template
"""
import os
import re
from datetime import datetime

def add_event_listeners_to_template():
    """Ajouter les event listeners pour les boutons pratiquants"""
    print("\n=== Ajout des event listeners pour les boutons pratiquants ===")
    
    filepath = "apps/competitions/templates/competitions/dashboard/club.html"
    if not os.path.exists(filepath):
        print("✗ Fichier template non trouvé")
        return False
    
    # Créer une sauvegarde
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{filepath}.backup_listeners_{timestamp}"
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✓ Sauvegarde créée: {backup_path}")
    
    # Vérifier si les event listeners existent déjà
    if 'delete-practitioner-btn' in content and 'toggle-status-btn' in content:
        print("⚠ Les event listeners semblent déjà présents")
        return True
    
    # Event listeners à ajouter
    event_listeners_code = '''

// ============== EVENT LISTENERS POUR BOUTONS PRATIQUANTS ==============
// Ajout automatique le ''' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '''
(function() {
    'use strict';
    
    console.log('🔧 Initialisation des event listeners pour les boutons pratiquants...');
    
    // Gestion des boutons de suppression
    document.addEventListener('click', function(e) {
        if (e.target.closest('.delete-practitioner-btn')) {
            e.preventDefault();
            const button = e.target.closest('.delete-practitioner-btn');
            const practitionerId = button.getAttribute('data-practitioner-id');
            const practitionerName = button.getAttribute('data-practitioner-name');
            
            if (confirm(`Êtes-vous sûr de vouloir supprimer ${practitionerName} ?`)) {
                button.disabled = true;
                button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
                
                // Construction dynamique de l'URL
                const baseUrl = window.location.origin;
                const deleteUrl = `${baseUrl}/fr/competitions/club/practitioners/${practitionerId}/delete/`;
                
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
                        const row = button.closest('tr');
                        if (row) {
                            row.style.transition = 'opacity 0.3s';
                            row.style.opacity = '0';
                            setTimeout(() => row.remove(), 300);
                        }
                        
                        // Afficher un message de succès
                        if (data.message) {
                            showSuccessMessage(data.message);
                        }
                    } else {
                        alert('Erreur: ' + (data.error || 'Erreur inconnue'));
                        button.disabled = false;
                        button.innerHTML = '<i class="fas fa-trash"></i>';
                    }
                })
                .catch(error => {
                    console.error('Erreur:', error);
                    alert('Erreur lors de la suppression: ' + error.message);
                    button.disabled = false;
                    button.innerHTML = '<i class="fas fa-trash"></i>';
                });
            }
        }
    });
    
    // Gestion des boutons toggle status (activer/désactiver)
    document.addEventListener('click', function(e) {
        if (e.target.closest('.toggle-status-btn')) {
            e.preventDefault();
            const button = e.target.closest('.toggle-status-btn');
            const practitionerId = button.getAttribute('data-practitioner-id');
            
            button.disabled = true;
            const originalHTML = button.innerHTML;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            
            // Construction dynamique de l'URL
            const baseUrl = window.location.origin;
            const toggleUrl = `${baseUrl}/fr/competitions/club/practitioners/${practitionerId}/toggle-status/`;
            
            fetch(toggleUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({}),
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
                        button.title = "Désactiver";
                    } else {
                        button.classList.remove('btn-outline-success');
                        button.classList.add('btn-outline-warning');
                        button.innerHTML = '<i class="fas fa-toggle-off"></i>';
                        button.title = "Activer";
                    }
                    
                    // Mettre à jour le badge de statut dans le tableau
                    const row = button.closest('tr');
                    if (row) {
                        const statusCell = row.querySelector('td:nth-child(5)'); // Colonne du statut
                        if (statusCell) {
                            if (newStatus) {
                                statusCell.innerHTML = '<span class="badge bg-success">Actif</span>';
                            } else {
                                statusCell.innerHTML = '<span class="badge bg-secondary">Inactif</span>';
                            }
                        }
                    }
                    
                    // Afficher un message de succès
                    if (data.message) {
                        showSuccessMessage(data.message);
                    }
                    
                    button.disabled = false;
                } else {
                    alert('Erreur: ' + (data.error || 'Erreur inconnue'));
                    button.disabled = false;
                    button.innerHTML = originalHTML;
                }
            })
            .catch(error => {
                console.error('Erreur:', error);
                alert('Erreur lors du changement de statut: ' + error.message);
                button.disabled = false;
                button.innerHTML = originalHTML;
            });
        }
    });
    
    // Corriger le bouton Import CSV
    document.addEventListener('DOMContentLoaded', function() {
        const importBtn = document.querySelector('button[onclick*="goToImportExport"]');
        if (importBtn && !importBtn.hasAttribute('data-fixed')) {
            importBtn.setAttribute('data-fixed', 'true');
            const originalOnclick = importBtn.getAttribute('onclick');
            importBtn.removeAttribute('onclick');
            
            importBtn.addEventListener('click', function(e) {
                e.preventDefault();
                // Utiliser l'URL complète
                window.location.href = '/fr/competitions/club/import-export/';
            });
            
            console.log('✅ Bouton Import CSV corrigé');
        }
    });
    
    // Fonction pour afficher les messages de succès
    function showSuccessMessage(message) {
        const container = document.querySelector('.tab-content') || document.querySelector('.container-fluid');
        if (container) {
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-success alert-dismissible fade show mt-3';
            alertDiv.innerHTML = `
                <i class="fas fa-check-circle me-2"></i>${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            
            // Insérer au début du container
            if (container.firstChild) {
                container.insertBefore(alertDiv, container.firstChild);
            } else {
                container.appendChild(alertDiv);
            }
            
            // Auto-fermer après 5 secondes
            setTimeout(() => {
                alertDiv.classList.remove('show');
                setTimeout(() => alertDiv.remove(), 300);
            }, 5000);
        }
    }
    
    console.log('✅ Event listeners des boutons pratiquants initialisés avec succès');
})();
'''

    # Chercher où insérer le code
    # Chercher juste avant la fermeture du script principal
    if '// Cache buster:' in content:
        # Insérer juste avant le cache buster
        parts = content.split('// Cache buster:')
        new_content = parts[0] + event_listeners_code + '\n\n// Cache buster:' + parts[1]
        print("✓ Event listeners ajoutés avant le cache buster")
    elif '</script>' in content and '{% endblock %}' in content:
        # Chercher le dernier </script> avant {% endblock %}
        match = re.search(r'(</script>)\s*({% endblock %})', content, re.DOTALL)
        if match:
            new_content = content[:match.start()] + event_listeners_code + '\n\n' + match.group(0)
            print("✓ Event listeners ajoutés à la fin du script")
        else:
            print("✗ Impossible de trouver où insérer les event listeners")
            return False
    else:
        print("✗ Structure du template non reconnue")
        return False
    
    # Sauvegarder le fichier modifié
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✓ Template mis à jour avec succès")
    return True

def main():
    print("=== AJOUT DES EVENT LISTENERS MANQUANTS ===")
    print(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 50)
    
    # Vérifier qu'on est dans le bon répertoire
    if not os.path.exists('manage.py'):
        print("ERREUR: Ce script doit être exécuté depuis la racine du projet Django")
        return
    
    # Ajouter les event listeners
    success = add_event_listeners_to_template()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ EVENT LISTENERS AJOUTÉS AVEC SUCCÈS !")
        print("\nPour tester:")
        print("1. Redémarrez le serveur Django : python manage.py runserver 8888")
        print("2. Allez sur : http://127.0.0.1:8888/fr/competitions/dashboard/club/")
        print("3. Cliquez sur l'onglet 'Pratiquants'")
        print("4. Testez les boutons :")
        print("   - Supprimer (🗑️) - avec confirmation")
        print("   - Toggle status (⚡) - activer/désactiver")
        print("   - Import CSV - redirection vers import/export")
    else:
        print("⚠ L'ajout des event listeners a échoué")

if __name__ == "__main__":
    main()