(function($) {
    $(document).ready(function() {
        // Récupérer les éléments du formulaire
        var $disciplineSelect = $('select[name="discipline"]');
        var $systemSelect = $('select[name="grade_system"]');
        var $categorySelect = $('select[name="category"]');
        
        // Fonction pour mettre à jour le système en fonction de la discipline
        function updateSystems() {
            var disciplineId = $disciplineSelect.val();
            if (disciplineId) {
                // Désactiver le sélecteur de systèmes pendant le chargement
                $systemSelect.prop('disabled', true);
                $categorySelect.prop('disabled', true);
                
                // Vider les sélecteurs
                $systemSelect.empty().append('<option value="">---------</option>');
                $categorySelect.empty().append('<option value="">---------</option>');
                
                // Requête AJAX pour obtenir les systèmes de grade pour cette discipline
                $.getJSON('/admin/competitions/grade-systems-by-discipline/', {
                    'discipline_id': disciplineId
                }, function(data) {
                    // Ajouter les options au sélecteur de systèmes
                    $.each(data, function(i, system) {
                        $systemSelect.append('<option value="' + system.id + '">' + system.name + '</option>');
                    });
                    
                    // Réactiver le sélecteur de systèmes
                    $systemSelect.prop('disabled', false);
                });
            } else {
                // Désactiver et vider les sélecteurs
                $systemSelect.prop('disabled', true).empty().append('<option value="">---------</option>');
                $categorySelect.prop('disabled', true).empty().append('<option value="">---------</option>');
            }
        }
        
        // Fonction pour mettre à jour les catégories en fonction du système
        function updateCategories() {
            var systemId = $systemSelect.val();
            if (systemId) {
                // Désactiver le sélecteur de catégories pendant le chargement
                $categorySelect.prop('disabled', true);
                
                // Vider le sélecteur de catégories
                $categorySelect.empty().append('<option value="">---------</option>');
                
                // Requête AJAX pour obtenir les catégories pour ce système
                $.getJSON('/admin/competitions/grade-categories-by-system/', {
                    'system_id': systemId
                }, function(data) {
                    // Ajouter les options au sélecteur de catégories
                    $.each(data, function(i, category) {
                        $categorySelect.append('<option value="' + category.id + '">' + category.name + '</option>');
                    });
                    
                    // Réactiver le sélecteur de catégories
                    $categorySelect.prop('disabled', false);
                });
            } else {
                // Désactiver et vider le sélecteur de catégories
                $categorySelect.prop('disabled', true).empty().append('<option value="">---------</option>');
            }
        }
        
        // Associer les événements aux sélecteurs
        $disciplineSelect.on('change', updateSystems);
        $systemSelect.on('change', updateCategories);
        
        // Initialiser les sélecteurs au chargement de la page
        if ($disciplineSelect.val()) {
            updateSystems();
        }
    });
})(django.jQuery);