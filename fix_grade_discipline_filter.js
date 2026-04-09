// JavaScript pour améliorer le filtrage par discipline dans les pages de grades

document.addEventListener('DOMContentLoaded', function() {
    const disciplineSelect = document.getElementById('discipline-filter');
    const categorySelect = document.getElementById('category-filter');
    
    if (disciplineSelect && categorySelect) {
        // Sauvegarder toutes les options de catégorie
        const allCategoryOptions = Array.from(categorySelect.options).map(option => ({
            value: option.value,
            text: option.text,
            disciplineId: option.dataset.disciplineId || extractDisciplineId(option.text)
        }));
        
        // Fonction pour extraire l'ID de discipline du texte de l'option
        function extractDisciplineId(text) {
            // Pour les options au format "Nom catégorie (Nom discipline)"
            // On devrait avoir un data-discipline-id mais on peut essayer de parser
            return null; // Par défaut
        }
        
        // Fonction pour filtrer les catégories en fonction de la discipline
        function filterCategories(disciplineId) {
            // Vider le select des catégories
            categorySelect.innerHTML = '';
            
            // Ajouter l'option par défaut
            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.text = categorySelect.dataset.defaultText || 'Toutes les catégories';
            categorySelect.appendChild(defaultOption);
            
            // Si aucune discipline sélectionnée, montrer toutes les catégories
            if (!disciplineId) {
                allCategoryOptions.forEach(opt => {
                    if (opt.value) { // Ignorer l'option vide
                        const option = new Option(opt.text, opt.value);
                        categorySelect.appendChild(option);
                    }
                });
            } else {
                // Filtrer les catégories pour la discipline sélectionnée
                // Pour cela, il faudrait que les options aient un attribut data-discipline-id
                // ou faire une requête AJAX pour récupérer les catégories de la discipline
                fetchCategoriesForDiscipline(disciplineId);
            }
        }
        
        // Fonction pour récupérer les catégories d'une discipline via AJAX
        function fetchCategoriesForDiscipline(disciplineId) {
            // Construction de l'URL avec les paramètres existants
            const currentUrl = new URL(window.location);
            const baseUrl = window.location.origin + '/grades/api/categories-by-discipline/';
            
            fetch(`${baseUrl}?discipline=${disciplineId}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.categories) {
                    data.categories.forEach(cat => {
                        const option = new Option(cat.name, cat.id);
                        option.dataset.disciplineId = disciplineId;
                        categorySelect.appendChild(option);
                    });
                }
                
                // Restaurer la sélection si elle existe dans l'URL
                const selectedCategory = currentUrl.searchParams.get('category');
                if (selectedCategory) {
                    categorySelect.value = selectedCategory;
                }
            })
            .catch(error => {
                console.error('Erreur lors du chargement des catégories:', error);
                // En cas d'erreur, afficher toutes les catégories
                allCategoryOptions.forEach(opt => {
                    if (opt.value) {
                        const option = new Option(opt.text, opt.value);
                        categorySelect.appendChild(option);
                    }
                });
            });
        }
        
        // Gérer le changement de discipline
        disciplineSelect.addEventListener('change', function() {
            const selectedDisciplineId = this.value;
            
            // Filtrer les catégories
            filterCategories(selectedDisciplineId);
            
            // Réinitialiser la sélection de catégorie
            categorySelect.value = '';
            
            // Mettre à jour l'URL
            const url = new URL(window.location);
            if (selectedDisciplineId) {
                url.searchParams.set('discipline', selectedDisciplineId);
            } else {
                url.searchParams.delete('discipline');
            }
            url.searchParams.delete('category'); // Réinitialiser la catégorie
            
            // Rediriger
            window.location = url.toString();
        });
        
        // Au chargement, filtrer les catégories si une discipline est sélectionnée
        const currentDiscipline = disciplineSelect.value;
        if (currentDiscipline) {
            filterCategories(currentDiscipline);
        }
    }
});