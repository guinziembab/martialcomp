# Guide de Déploiement Production - Correction Catégories de Compétition

## 📋 Résumé des corrections
1. **Affichage JSON brut** → Interface utilisateur avec messages
2. **Sélection des grades** → Dropdowns dynamiques avec API

## 🚀 Instructions de déploiement étape par étape

### Étape 1: Connexion au serveur de production
```bash
ssh martialcomp-production
```

### Étape 2: Naviguer vers le répertoire du projet
```bash
cd /var/www/vhosts/martialcomp.com/httpdocs
```

### Étape 3: Créer des backups de sécurité
```bash
# Créer le dossier de backup
mkdir -p backups/$(date +%Y%m%d)

# Sauvegarder les fichiers actuels
cp apps/competitions/views/categories.py backups/$(date +%Y%m%d)/categories.py.backup
cp apps/competitions/urls/competitions.py backups/$(date +%Y%m%d)/competitions_urls.py.backup
cp apps/competitions/templates/competitions/club/competition_management_detail.html backups/$(date +%Y%m%d)/competition_management_detail.html.backup
```

### Étape 4: Appliquer les modifications

#### 4.1 Mettre à jour categories.py
```bash
# Ouvrir le fichier pour édition
nano apps/competitions/views/categories.py
```

**Modifications à faire:**
1. Ligne 14: Ajouter l'import
```python
from apps.grades.models import Grade
```

2. Lignes 98-100: S'assurer que ces lignes existent dans add_category()
```python
# Récupérer les grades (AJOUT DES VARIABLES MANQUANTES)
min_grade = request.POST.get('min_grade', '').strip()
max_grade = request.POST.get('max_grade', '').strip()
```

3. À la fin du fichier, ajouter la nouvelle fonction:
```python
@login_required
def get_discipline_grades(request, competition_id):
    """Récupérer les grades disponibles pour la discipline d'une compétition"""
    competition = get_object_or_404(Competition, id=competition_id)
    
    try:
        # Récupérer les grades pour la discipline
        grades = Grade.objects.filter(discipline=competition.discipline).order_by('order_field')
        
        # Formatter les grades pour le JSON
        grades_data = []
        for grade in grades:
            grades_data.append({
                'id': grade.id,
                'name': grade.name,
                'color': grade.color if hasattr(grade, 'color') else None,
                'order': grade.order_field
            })
        
        return JsonResponse({
            'success': True,
            'grades': grades_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })
```

#### 4.2 Mettre à jour competitions.py (urls)
```bash
nano apps/competitions/urls/competitions.py
```

**Modifications:**
1. Ligne 11: Ajouter get_discipline_grades à l'import
```python
from apps.competitions.views.categories import (
    competition_categories, add_category, delete_category, get_discipline_grades
)
```

2. Après la ligne 56, ajouter la nouvelle route:
```python
path('<int:competition_id>/api/grades/', get_discipline_grades, name='get_discipline_grades'),
```

#### 4.3 Mettre à jour le template
```bash
nano apps/competitions/templates/competitions/club/competition_management_detail.html
```

**Modifications:**
1. Remplacer les inputs de grades (chercher "Grade minimum") par:
```html
<div class="mb-3">
    <label for="categoryMinGrade" class="form-label">{% trans "Grade minimum" %}</label>
    <select class="form-select" id="categoryMinGrade" name="min_grade">
        <option value="">{% trans "Aucun grade minimum" %}</option>
    </select>
</div>

<div class="mb-3">
    <label for="categoryMaxGrade" class="form-label">{% trans "Grade maximum" %}</label>
    <select class="form-select" id="categoryMaxGrade" name="max_grade">
        <option value="">{% trans "Aucun grade maximum" %}</option>
    </select>
</div>
```

2. Avant la fermeture `</script>` à la fin du fichier, ajouter le JavaScript pour la gestion des catégories (voir le code complet ci-dessous)

### Étape 5: Vérifier la syntaxe Python
```bash
# Activer l'environnement virtuel
source /var/www/vhosts/martialcomp.com/venv/bin/activate

# Vérifier la syntaxe
python -m py_compile apps/competitions/views/categories.py
python -m py_compile apps/competitions/urls/competitions.py
```

### Étape 6: Collecter les fichiers statiques
```bash
python manage.py collectstatic --noinput --settings=config.settings.production
```

### Étape 7: Redémarrer le service
```bash
sudo systemctl restart martialcomp.service
```

### Étape 8: Vérifier le statut
```bash
# Vérifier que le service est actif
sudo systemctl status martialcomp.service

# Suivre les logs en temps réel
sudo journalctl -u martialcomp.service -f
```

## 📝 Code JavaScript complet à ajouter

Ajouter ce code avant `</script>` à la fin du template:

```javascript
// Gérer la soumission du formulaire de catégorie
document.addEventListener('DOMContentLoaded', function() {
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
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // Fermer le modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('categoryModal'));
                    modal.hide();
                    
                    // Réinitialiser le formulaire
                    this.reset();
                    
                    // Afficher un message de succès
                    showMessage(data.message || 'Catégorie créée avec succès', 'success');
                    
                    // Recharger la page pour afficher la nouvelle catégorie
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    // Afficher l'erreur dans le modal
                    showModalMessage(data.message || 'Erreur lors de la création de la catégorie', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showModalMessage('Erreur de connexion au serveur', 'error');
            })
            .finally(() => {
                submitButton.innerHTML = originalText;
                submitButton.disabled = false;
            });
        });
    }
    
    // Fonction pour afficher les messages dans le modal
    function showModalMessage(message, type) {
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
            // Supprimer les alertes existantes
            modalBody.querySelectorAll('.alert').forEach(alert => alert.remove());
            
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
    
    // Réinitialiser le formulaire quand le modal se ferme
    const categoryModal = document.getElementById('categoryModal');
    if (categoryModal) {
        categoryModal.addEventListener('hidden.bs.modal', function() {
            const form = this.querySelector('form');
            if (form) {
                form.reset();
            }
            // Supprimer les messages d'alerte
            this.querySelectorAll('.alert').forEach(alert => alert.remove());
        });
        
        // Charger les grades quand le modal s'ouvre
        categoryModal.addEventListener('show.bs.modal', function() {
            loadDisciplineGrades();
        });
    }
    
    // Fonction pour charger les grades de la discipline
    function loadDisciplineGrades() {
        const competitionId = {{ competition.id }};
        const minGradeSelect = document.getElementById('categoryMinGrade');
        const maxGradeSelect = document.getElementById('categoryMaxGrade');
        
        // Afficher un message de chargement
        minGradeSelect.innerHTML = '<option value="">Chargement des grades...</option>';
        maxGradeSelect.innerHTML = '<option value="">Chargement des grades...</option>';
        
        fetch(`/fr/competitions/competitions/${competitionId}/api/grades/`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Réinitialiser les options
                    minGradeSelect.innerHTML = '<option value="">Aucun grade minimum</option>';
                    maxGradeSelect.innerHTML = '<option value="">Aucun grade maximum</option>';
                    
                    // Ajouter les grades
                    data.grades.forEach(grade => {
                        const optionHtml = `<option value="${grade.name}">${grade.name}</option>`;
                        minGradeSelect.innerHTML += optionHtml;
                        maxGradeSelect.innerHTML += optionHtml;
                    });
                } else {
                    // En cas d'erreur, afficher un message
                    minGradeSelect.innerHTML = '<option value="">Aucun grade disponible</option>';
                    maxGradeSelect.innerHTML = '<option value="">Aucun grade disponible</option>';
                }
            })
            .catch(error => {
                console.error('Erreur lors du chargement des grades:', error);
                minGradeSelect.innerHTML = '<option value="">Erreur de chargement</option>';
                maxGradeSelect.innerHTML = '<option value="">Erreur de chargement</option>';
            });
    }
});
```

## 🧪 Tests de validation

### Test 1: Création de catégorie
1. Aller sur https://martialcomp.com/fr/competitions/club/competitions/[ID]/manage/
2. Cliquer sur "Ajouter une catégorie"
3. Vérifier que les grades se chargent
4. Remplir le formulaire et créer
5. ✅ Message de succès dans l'interface (pas de JSON)
6. ✅ Page rechargée avec la nouvelle catégorie

### Test 2: Sélection des grades
1. Ouvrir le modal de création
2. ✅ Les dropdowns de grades doivent se remplir automatiquement
3. ✅ Pouvoir sélectionner un grade min/max

### Test 3: Gestion d'erreurs
1. Essayer de créer une catégorie sans nom
2. ✅ Message d'erreur dans le modal

## 🔧 En cas de problème

### Si le service ne démarre pas:
```bash
# Vérifier les erreurs
sudo journalctl -u martialcomp.service -n 100

# Vérifier la syntaxe Python
python manage.py check --settings=config.settings.production
```

### Pour revenir en arrière:
```bash
# Restaurer les backups
cp backups/$(date +%Y%m%d)/categories.py.backup apps/competitions/views/categories.py
cp backups/$(date +%Y%m%d)/competitions_urls.py.backup apps/competitions/urls/competitions.py
cp backups/$(date +%Y%m%d)/competition_management_detail.html.backup apps/competitions/templates/competitions/club/competition_management_detail.html

# Redémarrer
sudo systemctl restart martialcomp.service
```

## ✅ Checklist finale

- [ ] Backups créés
- [ ] categories.py modifié (import Grade + fonction API)
- [ ] URLs mises à jour
- [ ] Template modifié (selects + JavaScript)
- [ ] Syntaxe Python vérifiée
- [ ] Statiques collectés
- [ ] Service redémarré
- [ ] Tests effectués
- [ ] Logs vérifiés

## 📞 Support

En cas de problème, vérifier:
1. Les logs: `sudo journalctl -u martialcomp.service -f`
2. La console du navigateur pour les erreurs JavaScript
3. L'onglet Network pour vérifier les appels API