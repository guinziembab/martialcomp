#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour remplacer le champ Club par un champ texte libre
"""
import os

# Chemin du fichier modèle
coach_model_file = "competitions/models/coach_profile.py"

if not os.path.exists(coach_model_file):
    print(f"Le fichier {coach_model_file} n'existe pas.")
    exit(1)

# Lire le contenu du fichier
with open(coach_model_file, "r", encoding="utf-8") as f:
    content = f.read()

# Créer une sauvegarde
with open(f"{coach_model_file}.place.bak", "w", encoding="utf-8") as f:
    f.write(content)

print(f"Sauvegarde créée dans {coach_model_file}.place.bak")

# Texte de l'ancien champ primary_teaching_place
old_field = """    primary_teaching_place = models.ForeignKey(
        Club,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='primary_coaches',
        verbose_name=_("Club d'enseignement principal")
    )"""

# Texte du nouveau champ
new_field = """    teaching_place_name = models.CharField(
        _("Lieu ou club d'enseignement"),
        max_length=200,
        blank=True,
        help_text=_("Nom de votre club, dojo ou lieu d'enseignement principal")
    )
    
    # Champ maintenu pour compatibilité mais non affiché dans le formulaire
    primary_teaching_place = models.ForeignKey(
        Club,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='primary_coaches',
        verbose_name=_("Club référencé (interne)")
    )"""

# Remplacer le champ
if old_field in content:
    modified_content = content.replace(old_field, new_field)
    
    # Écrire le contenu modifié
    with open(coach_model_file, "w", encoding="utf-8") as f:
        f.write(modified_content)
    
    print("✓ Modèle mis à jour avec le champ teaching_place_name")
else:
    print("Champ primary_teaching_place non trouvé dans le format attendu")

# Mettre à jour le template
template_file = "competitions/templates/onboarding/coach/profile.html"

if not os.path.exists(template_file):
    print(f"Le fichier {template_file} n'existe pas.")
    exit(1)

# Lire le contenu du template
with open(template_file, "r", encoding="utf-8") as f:
    template_content = f.read()

# Créer une sauvegarde
with open(f"{template_file}.place.bak", "w", encoding="utf-8") as f:
    f.write(template_content)

print(f"Sauvegarde créée dans {template_file}.place.bak")

# Rechercher le bloc contenant primary_teaching_place
old_block = """                            <div class="col-md-6">
                                {{ profile_form.primary_teaching_place|as_crispy_field }}
                            </div>"""

# Nouveau bloc avec teaching_place_name
new_block = """                            <div class="col-md-6">
                                {{ profile_form.teaching_place_name|as_crispy_field }}
                            </div>"""

# Remplacer le bloc dans le template
if old_block in template_content:
    modified_template = template_content.replace(old_block, new_block)
    
    # Écrire le contenu modifié
    with open(template_file, "w", encoding="utf-8") as f:
        f.write(modified_template)
    
    print("✓ Template mis à jour pour utiliser teaching_place_name")
else:
    print("Bloc contenant primary_teaching_place non trouvé dans le template")

# Mettre à jour le formulaire
forms_file = "competitions/forms/onboarding.py"

if not os.path.exists(forms_file):
    print(f"Le fichier {forms_file} n'existe pas.")
    exit(1)

# Lire le contenu du fichier
with open(forms_file, "r", encoding="utf-8") as f:
    forms_content = f.read()

# Créer une sauvegarde
with open(f"{forms_file}.place.bak", "w", encoding="utf-8") as f:
    f.write(forms_content)

print(f"Sauvegarde créée dans {forms_file}.place.bak")

# Rechercher la classe CoachProfileForm
if "class CoachProfileForm" in forms_content:
    # Rechercher les champs du formulaire
    if "'primary_teaching_place'" in forms_content or '"primary_teaching_place"' in forms_content:
        # Remplacer primary_teaching_place par teaching_place_name
        modified_forms = forms_content.replace(
            "'primary_teaching_place'", 
            "'teaching_place_name'"
        ).replace(
            '"primary_teaching_place"', 
            '"teaching_place_name"'
        )
        
        # Écrire le contenu modifié
        with open(forms_file, "w", encoding="utf-8") as f:
            f.write(modified_forms)
        
        print("✓ Formulaire mis à jour pour utiliser teaching_place_name")
    else:
        print("Aucune référence à primary_teaching_place trouvée dans le formulaire")
else:
    print("Classe CoachProfileForm non trouvée dans le fichier de formulaires")

print("\nModifications terminées.")
print("Veuillez exécuter les commandes suivantes:")
print("1. python manage.py makemigrations  # Pour créer une migration pour le nouveau champ")
print("2. python manage.py migrate  # Pour appliquer la migration")