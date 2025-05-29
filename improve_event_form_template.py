#!/usr/bin/env python3
"""
Script pour améliorer le template event_form.html en ajoutant le JavaScript manquant
pour les cartes de type d'événement et autres améliorations.
"""

import os
from datetime import datetime

def main():
    print(f"[{datetime.now()}] Amélioration du template event_form.html...")
    
    template_path = 'competitions/templates/competitions/events/event_form.html'
    
    # Lire le template actuel
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # JavaScript à ajouter pour les cartes de type d'événement
    type_cards_js = '''
    // Gestion des cartes de type d'événement
    document.querySelectorAll('.type-card').forEach(card => {
      card.addEventListener('click', function() {
        // Désélectionner toutes les cartes
        document.querySelectorAll('.type-card').forEach(c => c.classList.remove('selected'));
        
        // Sélectionner cette carte
        this.classList.add('selected');
        
        // Mettre à jour le champ caché
        const eventType = this.dataset.type;
        const eventTypeField = document.getElementById('{{ form.event_type.id_for_label }}');
        if (eventTypeField) {
          eventTypeField.value = eventType;
          
          // Déclencher l'événement change pour mettre à jour la prévisualisation
          eventTypeField.dispatchEvent(new Event('change'));
        }
        
        // Afficher un feedback visuel
        this.style.transform = 'scale(0.98)';
        setTimeout(() => {
          this.style.transform = 'scale(1)';
        }, 150);
      });
    });

    // Améliorer l'interface "Ajouter Option"
    const addOptionButtons = document.querySelectorAll('[data-action="add-option"]');
    addOptionButtons.forEach(button => {
      button.addEventListener('click', function(e) {
        e.preventDefault();
        
        const targetSelector = this.dataset.target;
        const targetElement = document.querySelector(targetSelector);
        
        if (targetElement) {
          // Animation d'ouverture
          if (targetElement.style.display === 'none' || !targetElement.style.display) {
            targetElement.style.display = 'block';
            targetElement.style.opacity = '0';
            targetElement.style.transform = 'translateY(-10px)';
            
            // Animation fluide
            requestAnimationFrame(() => {
              targetElement.style.transition = 'all 0.3s ease';
              targetElement.style.opacity = '1';
              targetElement.style.transform = 'translateY(0)';
            });
            
            this.innerHTML = '<i class="fas fa-minus me-1"></i> {% trans "Masquer les options" %}';
            this.classList.remove('btn-outline-primary');
            this.classList.add('btn-outline-secondary');
          } else {
            // Animation de fermeture
            targetElement.style.transition = 'all 0.3s ease';
            targetElement.style.opacity = '0';
            targetElement.style.transform = 'translateY(-10px)';
            
            setTimeout(() => {
              targetElement.style.display = 'none';
            }, 300);
            
            this.innerHTML = '<i class="fas fa-plus me-1"></i> {% trans "Ajouter des options" %}';
            this.classList.remove('btn-outline-secondary');
            this.classList.add('btn-outline-primary');
          }
        }
      });
    });

    // Validation en temps réel
    const requiredFields = document.querySelectorAll('input[required], textarea[required], select[required]');
    requiredFields.forEach(field => {
      field.addEventListener('blur', function() {
        validateField(this);
      });
      
      field.addEventListener('input', function() {
        if (this.classList.contains('is-invalid')) {
          validateField(this);
        }
      });
    });
    
    function validateField(field) {
      const isValid = field.checkValidity();
      
      if (isValid) {
        field.classList.remove('is-invalid');
        field.classList.add('is-valid');
        
        // Masquer le message d'erreur s'il existe
        const errorElement = field.parentElement.querySelector('.invalid-feedback');
        if (errorElement) {
          errorElement.style.display = 'none';
        }
      } else {
        field.classList.remove('is-valid');
        field.classList.add('is-invalid');
        
        // Afficher ou créer un message d'erreur
        let errorElement = field.parentElement.querySelector('.invalid-feedback');
        if (!errorElement) {
          errorElement = document.createElement('div');
          errorElement.className = 'invalid-feedback';
          field.parentElement.appendChild(errorElement);
        }
        
        errorElement.textContent = field.validationMessage;
        errorElement.style.display = 'block';
      }
    }

    // Auto-sauvegarde (optionnel)
    let autoSaveTimeout;
    const formFields = document.querySelectorAll('#eventForm input, #eventForm textarea, #eventForm select');
    
    formFields.forEach(field => {
      field.addEventListener('input', function() {
        clearTimeout(autoSaveTimeout);
        autoSaveTimeout = setTimeout(() => {
          saveFormData();
        }, 2000); // Sauvegarder après 2 secondes d'inactivité
      });
    });
    
    function saveFormData() {
      const formData = new FormData(document.getElementById('eventForm'));
      const data = Object.fromEntries(formData.entries());
      
      // Sauvegarder dans localStorage
      localStorage.setItem('eventFormDraft', JSON.stringify(data));
      
      // Afficher un indicateur de sauvegarde
      showSaveIndicator();
    }
    
    function showSaveIndicator() {
      const indicator = document.createElement('div');
      indicator.className = 'alert alert-success position-fixed';
      indicator.style.cssText = 'top: 20px; right: 20px; z-index: 1060; opacity: 0.9;';
      indicator.innerHTML = '<i class="fas fa-check me-1"></i> {% trans "Brouillon sauvegardé" %}';
      
      document.body.appendChild(indicator);
      
      setTimeout(() => {
        indicator.remove();
      }, 2000);
    }
    
    // Restaurer les données sauvegardées au chargement
    function restoreFormData() {
      const savedData = localStorage.getItem('eventFormDraft');
      if (savedData) {
        try {
          const data = JSON.parse(savedData);
          
          // Demander à l'utilisateur s'il veut restaurer
          if (confirm('{% trans "Un brouillon a été trouvé. Voulez-vous le restaurer ?" %}')) {
            Object.entries(data).forEach(([name, value]) => {
              const field = document.querySelector(`[name="${name}"]`);
              if (field) {
                field.value = value;
                
                // Déclencher les événements pour mettre à jour l'interface
                field.dispatchEvent(new Event('change'));
                field.dispatchEvent(new Event('input'));
              }
            });
          }
        } catch (e) {
          console.error('Erreur lors de la restauration du brouillon:', e);
        }
      }
    }
    
    // Restaurer au chargement de la page
    if (!document.getElementById('eventForm').dataset.editing) {
      restoreFormData();
    }
    
    // Nettoyer le brouillon après soumission réussie
    document.getElementById('eventForm').addEventListener('submit', function() {
      localStorage.removeItem('eventFormDraft');
    });'''
    
    # Chercher l'endroit où insérer le JavaScript (avant la fermeture de document.addEventListener)
    insert_point = content.find("document.addEventListener('DOMContentLoaded', function() {")
    
    if insert_point != -1:
        # Trouver la fin de la fonction DOMContentLoaded
        end_point = content.find("});", insert_point)
        
        if end_point != -1:
            # Insérer le nouveau JavaScript avant la fermeture
            new_content = (content[:end_point] + 
                          "\n    " + type_cards_js.replace('\n', '\n    ') + 
                          "\n  " + content[end_point:])
        else:
            print("⚠️ Point de fermeture DOMContentLoaded non trouvé")
            new_content = content
    else:
        print("⚠️ DOMContentLoaded non trouvé, ajout du JavaScript à la fin")
        # Ajouter le JavaScript à la fin du fichier
        script_section = f'''
<script>
document.addEventListener('DOMContentLoaded', function() {{
{type_cards_js}
}});
</script>
{% endblock %}'''
        
        # Remplacer la fin du fichier
        if "{% endblock %}" in content:
            new_content = content.replace("{% endblock %}", script_section)
        else:
            new_content = content + script_section
    
    # CSS amélioré pour les cartes de type
    improved_css = '''
    .type-card {
      cursor: pointer;
      transition: all 0.3s ease;
      border: 2px solid #e9ecef;
      position: relative;
      overflow: hidden;
    }
    
    .type-card:hover {
      transform: translateY(-5px);
      box-shadow: 0 8px 25px rgba(0,0,0,0.15);
      border-color: #007bff;
    }
    
    .type-card.selected {
      border-color: #007bff;
      background: linear-gradient(135deg, #f8f9ff 0%, #e3f2fd 100%);
      transform: translateY(-2px);
    }
    
    .type-card.selected::before {
      content: '✓';
      position: absolute;
      top: 10px;
      right: 10px;
      color: #007bff;
      font-weight: bold;
      font-size: 18px;
    }
    
    .type-card .type-icon {
      transition: transform 0.3s ease;
    }
    
    .type-card:hover .type-icon,
    .type-card.selected .type-icon {
      transform: scale(1.1);
    }
    
    /* Amélioration des boutons "Ajouter Option" */
    .btn-add-option {
      transition: all 0.3s ease;
    }
    
    .btn-add-option:hover {
      transform: translateY(-1px);
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* Validation en temps réel */
    .is-valid {
      border-color: #28a745;
    }
    
    .is-invalid {
      border-color: #dc3545;
    }
    
    /* Animations pour les sections extensibles */
    .collapsible-section {
      overflow: hidden;
    }
    
    /* Indicateur de sauvegarde */
    .save-indicator {
      animation: slideInRight 0.3s ease;
    }
    
    @keyframes slideInRight {
      from { transform: translateX(100%); }
      to { transform: translateX(0); }
    }
    '''
    
    # Injecter le CSS amélioré
    css_insert_point = new_content.find("{% block extra_css %}")
    if css_insert_point != -1:
        css_end_point = new_content.find("{% endblock %}", css_insert_point)
        if css_end_point != -1:
            new_content = (new_content[:css_end_point] + 
                          improved_css + 
                          "\n" + new_content[css_end_point:])
    
    # Sauvegarder le template amélioré
    backup_path = template_path + f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    
    # Créer une sauvegarde
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Écrire le nouveau contenu
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ Template amélioré !")
    print(f"📁 Sauvegarde créée: {backup_path}")
    print("\nAméliorations ajoutées:")
    print("- ✅ JavaScript pour les cartes de type d'événement")
    print("- ✅ Animation des boutons 'Ajouter Option'")
    print("- ✅ Validation en temps réel des champs")
    print("- ✅ Auto-sauvegarde dans localStorage")
    print("- ✅ CSS amélioré avec animations")
    print("- ✅ Indicateurs visuels améliorés")

if __name__ == "__main__":
    main()