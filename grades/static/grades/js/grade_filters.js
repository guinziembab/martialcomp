// Créer ce fichier dans: grades/static/grades/js/grade_filters.js

(function($) {
    $(document).ready(function() {
        var disciplineSelect = $('#id_discipline');
        var categorySelect = $('#id_category');
        
        // Fonction pour mettre à jour les catégories en fonction de la discipline
        function updateCategories() {
            var disciplineId = disciplineSelect.val();
            
            if (disciplineId) {
                // Sauvegarde de la valeur actuelle
                var currentCategory = categorySelect.val();
                
                // Désactive les catégories pendant le chargement
                categorySelect.prop('disabled', true);
                
                // Requête AJAX pour obtenir les catégories
                $.ajax({
                    url: '/grades/api/categories-by-discipline/',
                    data: {
                        'discipline_id': disciplineId
                    },
                    dataType: 'json',
                    success: function(data) {
                        // Vider les options existantes
                        categorySelect.empty();
                        
                        // Ajouter les nouvelles options
                        categorySelect.append($('<option value="">---------</option>'));
                        
                        $.each(data.categories, function(index, category) {
                            var option = $('<option></option>')
                                .attr('value', category.id)
                                .text(category.name);
                                
                            // Sélectionner l'option si elle était sélectionnée avant
                            if (category.id == currentCategory) {
                                option.prop('selected', true);
                            }
                            
                            categorySelect.append(option);
                        });
                        
                        // Réactive le select
                        categorySelect.prop('disabled', false);
                    }
                });
            } else {
                // Si aucune discipline n'est sélectionnée, vider les catégories
                categorySelect.empty();
                categorySelect.append($('<option value="">---------</option>'));
            }
        }
        
        // Observer les changements sur le select de discipline
        disciplineSelect.change(updateCategories);
        
        // Initialiser au chargement
        updateCategories();
    });
})(django.jQuery);