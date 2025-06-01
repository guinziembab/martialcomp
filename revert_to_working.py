#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour revenir à un état fonctionnel en utilisant primary_teaching_place
"""
import os

# Chemin du template
template_file = "competitions/templates/onboarding/coach/profile.html"

# Le template est déjà dans un état fonctionnel avec primary_teaching_place, pas besoin de le changer

# Vérifier si le modèle a été modifié
model_file = "competitions/models/coach_profile.py"
if os.path.exists(model_file):
    # Lire le contenu du modèle
    with open(model_file, "r", encoding="utf-8") as f:
        model_content = f.read()
    
    # Vérifier si teaching_place_name existe dans le modèle
    if "teaching_place_name" in model_content:
        # Créer une sauvegarde
        with open(f"{model_file}.revert.bak", "w", encoding="utf-8") as f:
            f.write(model_content)
        
        print(f"Sauvegarde créée dans {model_file}.revert.bak")
        
        # Supprimer le bloc teaching_place_name
        import re
        pattern = r"""    teaching_place_name = models\.CharField\(
        _\("Lieu ou club d'enseignement"\),
        max_length=200,
        blank=True,
        help_text=_\("Nom de votre club, dojo ou lieu d'enseignement principal"\)
    \)
    
"""
        
        if re.search(pattern, model_content):
            modified_content = re.sub(pattern, "", model_content)
            
            # Écrire le contenu modifié
            with open(model_file, "w", encoding="utf-8") as f:
                f.write(modified_content)
            
            print("✓ Modèle corrigé: champ teaching_place_name supprimé")
        else:
            print("Motif teaching_place_name non trouvé dans le format attendu")
    else:
        print("Le champ teaching_place_name n'existe pas dans le modèle")
else:
    print(f"Fichier {model_file} non trouvé")

# Vérifie le formulaire
forms_file = "competitions/forms/onboarding.py"
if os.path.exists(forms_file):
    # Lire le contenu du formulaire
    with open(forms_file, "r", encoding="utf-8") as f:
        forms_content = f.read()
    
    # Vérifier si teaching_place_name existe dans le formulaire
    if "'teaching_place_name'" in forms_content or '"teaching_place_name"' in forms_content:
        # Créer une sauvegarde
        with open(f"{forms_file}.revert.bak", "w", encoding="utf-8") as f:
            f.write(forms_content)
        
        print(f"Sauvegarde créée dans {forms_file}.revert.bak")
        
        # Remplacer teaching_place_name par primary_teaching_place
        modified_forms = forms_content.replace(
            "'teaching_place_name'", 
            "'primary_teaching_place'"
        ).replace(
            '"teaching_place_name"', 
            '"primary_teaching_place"'
        )
        
        # Écrire le contenu modifié
        with open(forms_file, "w", encoding="utf-8") as f:
            f.write(modified_forms)
        
        print("✓ Formulaire corrigé: teaching_place_name remplacé par primary_teaching_place")
    else:
        print("Aucune référence à teaching_place_name trouvée dans le formulaire")
else:
    print(f"Fichier {forms_file} non trouvé")

print("\nLes fichiers ont été restaurés à un état fonctionnel.")
print("Vous pouvez maintenant accéder à la page /onboarding/coach/profile/")