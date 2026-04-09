/**
 * MartialComp - Dashboard Club - Module Principal
 * Version: 2.0.0 - Optimisée
 * ✅ Encodage UTF-8 corrigé
 * ✅ IDs des boutons unifiés
 * ✅ Event listeners optimisés
 */

(function() {
    'use strict';

    const ClubDashboard = {
        config: {
            localStorageKey: 'clubDashboardActiveTab',
            defaultTab: 'overview',
            alertDuration: 5000
        },

        urls: {},
        translations: {},
        state: { uploadInProgress: false, initialized: false },

        // ===== INITIALISATION =====
        init: function(urls, translations) {
            if (this.state.initialized) {
                console.warn('⚠️ Dashboard déjà initialisé');
                return;
            }

            console.log('🚀 Init Dashboard Club v2.0.0');
            this.urls = urls || {};
            this.translations = translations || {};

            this.initTabs();
            this.initAnimations();
            this.initTooltips();
            this.initEventListeners();

            this.state.initialized = true;
            console.log('✅ Dashboard initialisé');
        },

        // ===== GESTION DES ONGLETS =====
        initTabs: function() {
            const tabs = document.querySelectorAll('[data-bs-toggle="tab"]');
            const activeTabId = localStorage.getItem(this.config.localStorageKey) || this.config.defaultTab;

            // Restaurer l'onglet actif
            const activeTabElement = document.querySelector(`#${activeTabId}-tab`);
            if (activeTabElement && typeof bootstrap !== 'undefined') {
                new bootstrap.Tab(activeTabElement).show();
            }

            // Sauvegarder l'onglet sélectionné
            tabs.forEach(tab => {
                tab.addEventListener('shown.bs.tab', (event) => {
                    const targetId = event.target.getAttribute('data-bs-target').substring(1);
                    localStorage.setItem(this.config.localStorageKey, targetId);
                    
                    // Calcul des âges si onglet pratiquants
                    if (targetId === 'members') {
                        setTimeout(() => this.calculateAges(), 100);
                    }
                });
            });
        },

        // ===== ANIMATIONS =====
        initAnimations: function() {
            document.querySelectorAll('.card, .action-card, .stat-card').forEach(card => {
                card.addEventListener('mouseenter', function() {
                    this.style.transform = 'translateY(-2px)';
                    this.style.transition = 'transform 0.3s ease';
                });
                card.addEventListener('mouseleave', function() {
                    this.style.transform = '';
                });
            });
        },

        // ===== TOOLTIPS =====
        initTooltips: function() {
            if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
                [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
                   .map(el => new bootstrap.Tooltip(el));
            }
        },

        // ===== EVENT LISTENERS =====
        initEventListeners: function() {
            this.initDeleteButtons();
            this.initToggleStatusButtons();
            this.initQRCodeButtons();
        },

        initDeleteButtons: function() {
            document.querySelectorAll('.delete-practitioner-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    const id = btn.getAttribute('data-practitioner-id');
                    const name = btn.getAttribute('data-practitioner-name');

                    if (confirm(`Êtes-vous sûr de vouloir supprimer ${name} ?`)) {
                        this.deletePractitioner(id);
                    }
                });
            });
        },

        initToggleStatusButtons: function() {
            document.querySelectorAll('.toggle-status-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.togglePractitionerStatus(btn.getAttribute('data-practitioner-id'));
                });
            });
        },

        initQRCodeButtons: function() {
            document.addEventListener('click', (e) => {
                const qrBtn = e.target.closest('.download-qr-btn');
                if (qrBtn) {
                    e.preventDefault();
                    this.downloadQRCode(
                        qrBtn.getAttribute('data-qr-url'),
                        qrBtn.getAttribute('data-filename')
                    );
                }
            });
        },

        // ===== ACTIONS AJAX =====
        deletePractitioner: function(id) {
            fetch(this.urls.practitioner_delete.replace('0', id), {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken'),
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    this.showAlert(data.message, 'success');
                    document.querySelector(`tr[data-practitioner-id="${id}"]`)?.remove();
                } else {
                    this.showAlert(data.message, 'danger');
                }
            })
            .catch(err => {
                console.error('Erreur suppression:', err);
                this.showAlert('Erreur lors de la suppression', 'danger');
            });
        },

        togglePractitionerStatus: function(id) {
            fetch(this.urls.practitioner_toggle_status.replace('0', id), {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                }
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    this.showAlert(data.message, 'success');
                    const badge = document.querySelector(`[data-status-badge="${id}"]`);
                    if (badge) {
                        badge.className = data.is_active ? 'badge bg-success' : 'badge bg-secondary';
                        badge.textContent = data.is_active ? 'Actif' : 'Inactif';
                    }
                } else {
                    this.showAlert(data.message, 'danger');
                }
            })
            .catch(err => {
                console.error('Erreur toggle:', err);
                this.showAlert('Erreur lors du changement de statut', 'danger');
            });
        },

        downloadQRCode: function(url, filename) {
            const link = document.createElement('a');
            link.href = url;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        },

        // ===== UTILITAIRES =====
        getCookie: function(name) {
            let cookieValue = null;
            if (document.cookie) {
                const cookies = document.cookie.split(';');
                for (let cookie of cookies) {
                    cookie = cookie.trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        },

        showAlert: function(message, type = 'info') {
            const alertClass = {
                'success': 'alert-success',
                'danger': 'alert-danger',
                'warning': 'alert-warning',
                'info': 'alert-info'
            }[type] || 'alert-info';
            
            const icon = {
                'success': 'fa-check-circle',
                'danger': 'fa-exclamation-circle',
                'warning': 'fa-exclamation-triangle',
                'info': 'fa-info-circle'
            }[type] || 'fa-info-circle';

            const alert = document.createElement('div');
            alert.className = `alert ${alertClass} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
            alert.style.zIndex = '9999';
            alert.style.minWidth = '300px';
            alert.innerHTML = `
                <i class="fas ${icon} me-2"></i>${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;

            document.body.appendChild(alert);

            setTimeout(() => {
                alert.classList.remove('show');
                setTimeout(() => alert.remove(), 300);
            }, this.config.alertDuration);
        },

        // ===== CALCUL DES ÂGES =====
        calculateAges: function() {
            document.querySelectorAll('.age-display').forEach(el => {
                if (el.getAttribute('data-calculated') === 'true') return;

                const birthDateStr = el.getAttribute('data-birth-date');
                
                if (birthDateStr) {
                    try {
                        const birthDate = new Date(birthDateStr);
                        const today = new Date();
                        
                        let age = today.getFullYear() - birthDate.getFullYear();
                        const monthDiff = today.getMonth() - birthDate.getMonth();
                        
                        if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
                            age--;
                        }
                        
                        if (age >= 0 && age <= 120) {
                            el.innerHTML = `<span class="text-info fw-bold">${age} ans</span>`;
                        } else {
                            el.innerHTML = '<span class="text-muted">-</span>';
                        }
                        
                        el.setAttribute('data-calculated', 'true');
                    } catch (error) {
                        console.error('Erreur calcul âge:', error);
                        el.innerHTML = '<span class="text-muted">-</span>';
                        el.setAttribute('data-calculated', 'true');
                    }
                } else {
                    el.innerHTML = '<span class="text-muted">-</span>';
                    el.setAttribute('data-calculated', 'true');
                }
            });
        }
    };

    // Exposition globale
    window.ClubDashboard = ClubDashboard;

    document.addEventListener('DOMContentLoaded', () => {
        console.log('📦 Module ClubDashboard chargé');
    });

})();