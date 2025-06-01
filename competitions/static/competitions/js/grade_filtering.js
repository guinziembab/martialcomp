/**
 * Script pour le filtrage dynamique des grades par discipline
 */

class GradeFilter {
    constructor(disciplineSelector, gradeSelector, apiUrl = '/api/grades/disciplines/') {
        this.disciplineSelect = document.querySelector(disciplineSelector);
        this.gradeSelect = document.querySelector(gradeSelector);
        this.apiUrl = apiUrl;
        
        if (this.disciplineSelect && this.gradeSelect) {
            this.init();
        }
    }
    
    init() {
        // Attacher l'événement sur le select de disciplines
        this.disciplineSelect.addEventListener('change', () => this.updateGrades());
        
        // Déclencher le chargement initial si une discipline est déjà sélectionnée
        if (this.disciplineSelect.value) {
            this.updateGrades();
        }
    }
    
    async updateGrades() {
        const selectedDisciplines = this.getSelectedDisciplines();
        
        if (selectedDisciplines.length === 0) {
            this.setEmptyState();
            return;
        }
        
        this.setLoadingState();
        
        try {
            const grades = await this.fetchGrades(selectedDisciplines);
            this.populateGrades(grades);
        } catch (error) {
            console.error('Erreur lors du chargement des grades:', error);
            this.setErrorState();
        }
    }
    
    getSelectedDisciplines() {
        if (this.disciplineSelect.multiple) {
            return Array.from(this.disciplineSelect.selectedOptions).map(option => option.value);
        } else {
            return this.disciplineSelect.value ? [this.disciplineSelect.value] : [];
        }
    }
    
    async fetchGrades(disciplineIds) {
        const params = new URLSearchParams();
        disciplineIds.forEach(disciplineId => {
            params.append('disciplines[]', disciplineId);
        });
        
        const response = await fetch(`${this.apiUrl}?${params.toString()}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        // L'API retourne un objet avec une propriété 'grades'
        return data.grades || [];
    }
    
    populateGrades(grades) {
        // Effacer les options actuelles
        this.gradeSelect.innerHTML = '<option value="">Sélectionnez un grade</option>';
        
        if (grades.length === 0) {
            this.gradeSelect.innerHTML = '<option value="">Aucun grade trouvé</option>';
            this.gradeSelect.disabled = true;
            return;
        }
        
        // Grouper les grades par discipline
        const gradesByDiscipline = this.groupGradesByDiscipline(grades);
        
        // Ajouter les grades groupés par discipline
        Object.keys(gradesByDiscipline).forEach(disciplineName => {
            const optgroup = document.createElement('optgroup');
            optgroup.label = disciplineName;
            
            gradesByDiscipline[disciplineName]
                .sort((a, b) => a.level - b.level)
                .forEach(grade => {
                    const option = document.createElement('option');
                    option.value = grade.id;
                    option.textContent = `${grade.name}${grade.color ? ' (' + grade.color + ')' : ''}`;
                    optgroup.appendChild(option);
                });
            
            this.gradeSelect.appendChild(optgroup);
        });
        
        this.gradeSelect.disabled = false;
    }
    
    groupGradesByDiscipline(grades) {
        const grouped = {};
        grades.forEach(grade => {
            if (!grouped[grade.discipline_name]) {
                grouped[grade.discipline_name] = [];
            }
            grouped[grade.discipline_name].push(grade);
        });
        return grouped;
    }
    
    setEmptyState() {
        this.gradeSelect.innerHTML = '<option value="">Sélectionnez d\'abord une discipline</option>';
        this.gradeSelect.disabled = true;
    }
    
    setLoadingState() {
        this.gradeSelect.innerHTML = '<option value="">Chargement des grades...</option>';
        this.gradeSelect.disabled = true;
    }
    
    setErrorState() {
        this.gradeSelect.innerHTML = '<option value="">Erreur lors du chargement</option>';
        this.gradeSelect.disabled = true;
    }
}

// Fonction utilitaire pour initialiser le filtre automatiquement
function initGradeFilter(disciplineSelector, gradeSelector) {
    document.addEventListener('DOMContentLoaded', function() {
        new GradeFilter(disciplineSelector, gradeSelector);
    });
}

// Export pour utilisation en module
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { GradeFilter, initGradeFilter };
}