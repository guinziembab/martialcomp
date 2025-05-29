#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour ajouter un champ de texte libre pour le lieu d'enseignement
"""
import os

# Modifier le modèle CoachProfile
coach_model_file = "competitions/models/coach_profile.py"

if not os.path.exists(coach_model_file):
    print(f"Le fichier {coach_model_file} n'existe pas.")
    exit(1)

# Lire le contenu du fichier
with open(coach_model_file, "r", encoding="utf-8") as f:
    coach_model_content = f.read()

# Créer une sauvegarde
with open(f"{coach_model_file}.teachingplace.bak", "w", encoding="utf-8") as f:
    f.write(coach_model_content)

print(f"Sauvegarde créée dans {coach_model_file}.teachingplace.bak")

# Ajouter le nouveau champ teaching_place avant primary_teaching_place
if "primary_teaching_place = models.ForeignKey" in coach_model_content:
    # Texte du nouveau champ à ajouter
    new_field = """    teaching_place = models.CharField(
        _("Lieu d'enseignement principal"),
        max_length=200,
        blank=True,
        help_text=_("Nom de votre club, dojo ou lieu d'enseignement principal")
    )
    
"""

    # Trouver où insérer le nouveau champ
    primary_teaching_index = coach_model_content.find("    primary_teaching_place = models.ForeignKey")
    
    if primary_teaching_index != -1:
        # Insérer le nouveau champ avant primary_teaching_place
        modified_content = (
            coach_model_content[:primary_teaching_index] + 
            new_field + 
            coach_model_content[primary_teaching_index:]
        )
        
        # Écrire le contenu modifié
        with open(coach_model_file, "w", encoding="utf-8") as f:
            f.write(modified_content)
        
        print("✓ Champ teaching_place ajouté au modèle CoachProfile")
    else:
        print("Position d'insertion non trouvée pour le nouveau champ")
else:
    print("Le champ primary_teaching_place n'a pas été trouvé dans le modèle")

# Mettre à jour le formulaire pour inclure le nouveau champ
forms_file = "competitions/forms/onboarding.py"

if os.path.exists(forms_file):
    # Lire le contenu du fichier
    with open(forms_file, "r", encoding="utf-8") as f:
        forms_content = f.read()
    
    # Créer une sauvegarde
    with open(f"{forms_file}.teachingplace.bak", "w", encoding="utf-8") as f:
        f.write(forms_content)
    
    print(f"Sauvegarde créée dans {forms_file}.teachingplace.bak")
    
    # Vérifier si "CoachProfileForm" existe dans le fichier
    if "class CoachProfileForm" in forms_content:
        # Chercher la liste des champs dans Meta
        if "fields = [" in forms_content:
            # Si "primary_teaching_place" est dans la liste des champs
            if "'primary_teaching_place'" in forms_content or '"primary_teaching_place"' in forms_content:
                # Ajouter "teaching_place" après "primary_teaching_place"
                modified_forms = forms_content.replace(
                    "'primary_teaching_place'", 
                    "'teaching_place', 'primary_teaching_place'"
                ).replace(
                    '"primary_teaching_place"', 
                    '"teaching_place", "primary_teaching_place"'
                )
                
                # Écrire le contenu modifié
                with open(forms_file, "w", encoding="utf-8") as f:
                    f.write(modified_forms)
                
                print("✓ Champ teaching_place ajouté au formulaire CoachProfileForm")
            else:
                print("Le champ primary_teaching_place n'a pas été trouvé dans la liste des champs")
        else:
            print("Liste des champs 'fields = [' non trouvée dans le formulaire")
    else:
        print("Classe CoachProfileForm non trouvée dans le fichier")
else:
    print(f"Le fichier {forms_file} n'existe pas")

# Mettre à jour le template
template_file = "competitions/templates/onboarding/coach/profile.html"

if os.path.exists(template_file):
    # Lire le contenu du template
    with open(template_file, "r", encoding="utf-8") as f:
        template_content = f.read()
    
    # Créer une sauvegarde
    with open(f"{template_file}.teachingplace.bak", "w", encoding="utf-8") as f:
        f.write(template_content)
    
    print(f"Sauvegarde créée dans {template_file}.teachingplace.bak")
    
    # Vérifier si primary_teaching_place est dans le template
    if "profile_form.primary_teaching_place|as_crispy_field" in template_content:
        # Remplacer primary_teaching_place par teaching_place
        modified_template = template_content.replace(
            "profile_form.primary_teaching_place|as_crispy_field",
            "profile_form.teaching_place|as_crispy_field"
        )
        
        # Écrire le contenu modifié
        with open(template_file, "w", encoding="utf-8") as f:
            f.write(modified_template)
        
        print("✓ Template mis à jour pour utiliser le champ teaching_place")
    else:
        print("Référence à primary_teaching_place non trouvée dans le template")
else:
    print(f"Le fichier {template_file} n'existe pas")

print("\nModifications terminées.")
print("Veuillez exécuter les commandes suivantes:")
print("1. python manage.py makemigrations")
print("2. python manage.py migrate")
print("3. Redémarrez votre serveur Django")